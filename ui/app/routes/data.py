"""User data management routes.

Browser routes (session auth):
  GET  /user/data                       — data management page
  GET  /user/data/upload                — upload form
  POST /user/data/upload                — handle file upload
  DELETE /user/data/{file_id}          — delete a file
  POST /user/projects/{id}/github-sync  — link repo and sync

API routes (session or Bearer token):
  GET  /api/data/{file_id}   — download file bytes
  POST /api/user/token       — generate/rotate API token
"""

import logging
from pathlib import Path
from urllib.parse import quote as _quote, urlparse

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.context as ctx
from app.auth import get_beril_user_id, get_current_user_or_token
from app.config import get_settings
from app.context import get_base_context
from app.db.crud import (
    create_project_file,
    delete_project_file,
    get_file_by_id,
    get_files_for_project,
    get_or_create_api_token,
    get_project_by_id,
    get_projects_for_user,
    get_upload_file_by_filename,
    update_project_github_url,
)
from app.db.session import get_db
from app.github_sync import sync_github_repo
from app.storage import LocalFileStorage

logger = logging.getLogger(__name__)

# Allowed file_type enum values (mirrors ProjectFile.file_type DB enum)
_ALLOWED_FILE_TYPES = {
    "notebook", "data", "visualization", "readme",
    "research_plan", "report", "other",
}

# GitHub sync only accepts HTTPS URLs pointing at github.com to prevent SSRF
_ALLOWED_GITHUB_HOSTS = {"github.com", "www.github.com"}


def _is_valid_github_url(url: str) -> bool:
    """Return True only for plain https://github.com/{owner}/{repo} URLs.

    Requires exactly two path segments so that bare org pages, settings pages,
    issue listings, and other non-clonable GitHub paths are rejected.
    Rejects credential-bearing URLs to prevent secret persistence/leakage.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    # Reject credential-bearing URLs like https://token:x@github.com/org/repo
    if parsed.username or parsed.password:
        return False
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_GITHUB_HOSTS:
        return False
    # Reject browser URLs with query strings or fragments — git clone cannot use them
    if parsed.query or parsed.fragment:
        return False
    # Path must have exactly two non-empty segments: /{owner}/{repo}
    # (strip an optional trailing .git suffix before counting)
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    segments = [s for s in path.split("/") if s]
    return len(segments) == 2


ROUTER_USER_DATA = APIRouter(tags=["User Data"])


def _storage() -> LocalFileStorage:
    return LocalFileStorage(get_settings().user_projects_root)


# ---------------------------------------------------------------------------
# Browser routes
# ---------------------------------------------------------------------------


@ROUTER_USER_DATA.get("/user/data", response_class=HTMLResponse)
async def user_data(
    request: Request,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Data management page — lists all files across the user's projects."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url=f"/auth/login?next=/user/data", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    projects = await get_projects_for_user(db, beril_user_id)
    projects_with_files = []
    for project in projects:
        files = await get_files_for_project(db, project.id)
        projects_with_files.append({"project": project, "files": files})

    context["projects_with_files"] = projects_with_files
    return ctx.templates.TemplateResponse(request, "user/data_management.html", context)


@ROUTER_USER_DATA.get("/user/data/upload", response_class=HTMLResponse)
async def user_data_upload_form(
    request: Request,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """File upload form."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url="/auth/login?next=/user/data/upload", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    projects = await get_projects_for_user(db, beril_user_id)
    context["projects"] = projects
    return ctx.templates.TemplateResponse(request, "user/data_upload.html", context)


@ROUTER_USER_DATA.post("/user/data/upload")
async def user_data_upload(
    request: Request,
    project_id: str = Form(...),
    file_type: str = Form("data"),
    is_public: bool = Form(False),
    file: UploadFile = File(...),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Handle multipart file upload, store blob, upsert ProjectFile record."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    if file_type not in _ALLOWED_FILE_TYPES:
        return Response(status_code=422, content=f"Invalid file_type: {file_type!r}")

    project = await get_project_by_id(db, project_id)
    if project is None or project.owner_id != beril_user_id:
        return Response(status_code=403)

    owner_id, slug = project.filesystem_path_parts
    # Strip any directory components from the uploaded filename, including both
    # forward-slash and backslash separators so Windows-style paths like
    # "..\evil.csv" don't bypass the basename extraction on Unix hosts.
    raw_name = (file.filename or "upload").replace("\\", "/")
    safe_name = Path(raw_name).name
    if not safe_name or safe_name in {".", ".."}:
        return Response(status_code=422, content="Invalid filename")
    storage_path = f"{owner_id}/{slug}/uploads/{safe_name}"

    # Check for an existing record before writing to storage so we can skip
    # creating a blob if the upsert will fail (avoids orphaned files on 422).
    # A unique-constraint violation from a rare concurrent upload is handled
    # by re-fetching the row and updating it in a second pass.
    existing = await get_upload_file_by_filename(db, project_id, safe_name)

    data = await file.read()
    storage = _storage()
    size = await storage.save(data, storage_path)

    if existing is not None:
        existing.storage_path = storage_path
        existing.size_bytes = size
        existing.content_type = file.content_type
        existing.file_type = file_type
        existing.is_public = is_public
        await db.commit()
    else:
        try:
            await create_project_file(
                db,
                project_id=project_id,
                file_type=file_type,
                filename=safe_name,
                storage_path=storage_path,
                size_bytes=size,
                content_type=file.content_type,
                is_public=is_public,
                source="upload",
            )
        except IntegrityError:
            # Concurrent upload beat us — roll back and update the winner's row.
            await db.rollback()
            existing = await get_upload_file_by_filename(db, project_id, safe_name)
            if existing is not None:
                existing.storage_path = storage_path
                existing.size_bytes = size
                existing.content_type = file.content_type
                existing.file_type = file_type
                existing.is_public = is_public
                await db.commit()

    return RedirectResponse(url="/user/data", status_code=302)


@ROUTER_USER_DATA.delete("/user/data/{file_id}")
async def user_data_delete(
    request: Request,
    file_id: str,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file — removes the storage blob and the DB record."""
    user = context.get("current_user")
    if user is None:
        return Response(status_code=401)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return Response(status_code=401)

    file = await get_file_by_id(db, file_id)
    if file is None:
        return Response(status_code=404)

    project = await get_project_by_id(db, file.project_id)
    if project is None or project.owner_id != beril_user_id:
        return Response(status_code=403)

    storage = _storage()
    await storage.delete(file.storage_path)
    await delete_project_file(db, file_id)

    return Response(status_code=204)


@ROUTER_USER_DATA.post("/user/projects/{project_id}/github-sync")
async def user_github_sync(
    request: Request,
    project_id: str,
    github_repo_url: str = Form(...),
    branch: str = Form("main"),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Store the GitHub repo URL on the project and trigger a sync."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    if not _is_valid_github_url(github_repo_url):
        return Response(status_code=422, content="github_repo_url must be an https://github.com/... URL")

    project = await get_project_by_id(db, project_id)
    if project is None or project.owner_id != beril_user_id:
        return Response(status_code=403)

    await update_project_github_url(db, project_id, github_repo_url, github_branch=branch)
    # Re-fetch to get the updated record
    project = await get_project_by_id(db, project_id)

    storage = _storage()
    try:
        _, actual_branch = await sync_github_repo(github_repo_url, project, storage, db, branch=branch)
        # Persist the branch that was actually used (may differ if main→master fallback fired)
        if actual_branch != branch:
            await update_project_github_url(db, project_id, github_repo_url, github_branch=actual_branch)
    except Exception:
        logger.exception("GitHub sync failed for project %s url %s", project_id, github_repo_url)

    return RedirectResponse(url="/user/data", status_code=302)


# ---------------------------------------------------------------------------
# API routes (session or Bearer token)
# ---------------------------------------------------------------------------


@ROUTER_USER_DATA.get("/api/data/{file_id}")
async def api_get_file(
    request: Request,
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return file bytes. Accessible to the owner or if the file is public."""
    file = await get_file_by_id(db, file_id)
    if file is None:
        return Response(status_code=404)

    project = await get_project_by_id(db, file.project_id)
    if project is None:
        return Response(status_code=404)

    if not file.is_public:
        user = await get_current_user_or_token(request, db)
        if user is None or user.id != project.owner_id:
            return Response(status_code=403)

    storage = _storage()
    try:
        data = await storage.load(file.storage_path)
    except FileNotFoundError:
        logger.warning("Storage blob missing for file %s at %s", file_id, file.storage_path)
        return Response(status_code=404)
    basename = Path(file.filename).name
    encoded = _quote(basename, safe="")
    return Response(
        content=data,
        media_type=file.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@ROUTER_USER_DATA.post("/api/user/token")
async def api_create_token(
    request: Request,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Generate or rotate the caller's API token. Session auth only."""
    user = context.get("current_user")
    if user is None:
        return Response(status_code=401)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return Response(status_code=401)

    raw_token, record = await get_or_create_api_token(db, beril_user_id)
    return JSONResponse(
        {"token": raw_token, "created_at": record.created_at.isoformat()}
    )
