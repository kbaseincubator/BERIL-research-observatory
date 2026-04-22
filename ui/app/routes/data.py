"""User data management routes.

Browser routes (session auth):
  GET  /user/data                            — project list page
  GET  /user/data/new                        — create new project form
  POST /user/projects/create                 — create project, redirect to /user/projects/{id}
  GET  /user/projects/{id}                   — file management page for an existing project
  POST /user/data/upload-to-project          — upload files to existing project
  DELETE /user/data/{file_id}                — delete a file
  POST /user/projects/{id}/github-sync       — link repo and sync

API routes (session or Bearer token):
  GET  /api/data/{file_id}              — download/view file bytes
  GET  /api/user/projects/{id}/files    — list files for a project (JSON)
  POST /api/user/token                  — generate/rotate API token
"""

import logging
import re
import uuid
from pathlib import Path
from urllib.parse import quote as _quote, urlparse

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.context as ctx
from app.auth import get_beril_user_id, get_current_user_session_or_token
from app.config import get_settings
from app.context import get_base_context
from app.db.crud import (
    create_project_file,
    create_user_project,
    delete_project_file,
    get_file_by_id,
    get_files_for_project,
    get_or_create_api_token,
    get_project_by_id,
    get_projects_for_user,
    get_upload_file_by_filename,
    update_project_github_url,
)
from app.db.models import BerilUser, UserProject
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


def _slugify(title: str) -> str:
    """Convert a project title to a URL/filesystem-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug or "project"


def _safe_relative_path(raw_name: str) -> str | None:
    """Return a sanitized relative path from an uploaded filename.

    Browsers send a flat basename for regular file picks, and a relative path
    like ``mydir/subdir/file.csv`` when the user picks a directory via
    webkitdirectory.  We sanitize every segment individually to prevent path
    traversal while preserving the directory structure.
    """
    # Normalize separators (Windows paths use backslash)
    normalized = raw_name.replace("\\", "/")
    segments = normalized.split("/")
    safe_segments = []
    for seg in segments:
        # Strip leading dots to prevent hidden-file tricks; reject empty or dot-only segments
        seg = seg.strip()
        if not seg or seg in {".", ".."}:
            continue
        safe_segments.append(seg)
    if not safe_segments:
        return None
    return "/".join(safe_segments)


async def _save_upload(
    db: AsyncSession,
    storage: LocalFileStorage,
    file: UploadFile,
    project_id: str,
    owner_id: str,
    slug: str,
    file_type: str,
    is_public: bool,
) -> None:
    """Save one uploaded file to storage and upsert a ProjectFile record.

    Preserves relative paths from directory uploads (webkitdirectory) so that
    ``mydir/subdir/file.csv`` is stored under ``uploads/mydir/subdir/file.csv``
    rather than being flattened to ``uploads/file.csv``.
    """
    relative_path = _safe_relative_path(file.filename or "upload")
    if relative_path is None:
        return
    storage_path = f"{owner_id}/{slug}/uploads/{relative_path}"
    # filename stored in DB is the relative path — preserves directory structure
    # and keeps the upsert uniqueness check meaningful for nested files.
    existing = await get_upload_file_by_filename(db, project_id, relative_path)
    data = await file.read()
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
                filename=relative_path,
                storage_path=storage_path,
                size_bytes=size,
                content_type=file.content_type,
                is_public=is_public,
                source="upload",
            )
        except IntegrityError:
            await db.rollback()
            existing = await get_upload_file_by_filename(db, project_id, relative_path)
            if existing is not None:
                existing.storage_path = storage_path
                existing.size_bytes = size
                existing.content_type = file.content_type
                existing.file_type = file_type
                existing.is_public = is_public
                await db.commit()


# ---------------------------------------------------------------------------
# Browser routes
# ---------------------------------------------------------------------------


@ROUTER_USER_DATA.get("/user/data", response_class=HTMLResponse)
async def user_data(
    request: Request,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Project list page."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url="/auth/login?next=/user/data", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    projects = await get_projects_for_user(db, beril_user_id)
    context["projects"] = projects
    return ctx.templates.TemplateResponse(request, "user/data_management.html", context)


@ROUTER_USER_DATA.get("/debug/me")
async def debug_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Dump the caller's session identity and project ownership counts.

    Helps diagnose cases where /user/data shows no projects despite rows
    existing in user_project — usually a mismatch between the session's
    beril_user_id and the owner_id on imported projects.
    """
    session_user_id = request.session.get("beril_user_id")
    session_orcid = request.session.get("orcid_id")

    db_user = None
    if session_user_id is not None:
        db_user = await db.get(BerilUser, session_user_id)

    owned_count = 0
    if session_user_id is not None:
        owned_count = (
            await db.execute(
                select(func.count()).select_from(UserProject).where(
                    UserProject.owner_id == session_user_id
                )
            )
        ).scalar_one()

    total_count = (
        await db.execute(select(func.count()).select_from(UserProject))
    ).scalar_one()

    by_origin_rows = (
        await db.execute(
            select(UserProject.origin, func.count())
            .group_by(UserProject.origin)
        )
    ).all()

    distinct_owners_rows = (
        await db.execute(
            select(UserProject.owner_id, func.count())
            .group_by(UserProject.owner_id)
            .order_by(func.count().desc())
        )
    ).all()

    return JSONResponse({
        "session": {
            "beril_user_id": session_user_id,
            "orcid_id": session_orcid,
        },
        "db_user": (
            {
                "id": db_user.id,
                "orcid_id": db_user.orcid_id,
                "display_name": db_user.display_name,
            }
            if db_user is not None
            else None
        ),
        "projects": {
            "owned_by_session_user": owned_count,
            "total_in_db": total_count,
            "by_origin": {origin: count for origin, count in by_origin_rows},
            "by_owner_id": [
                {"owner_id": owner_id, "count": count}
                for owner_id, count in distinct_owners_rows
            ],
        },
    })


@ROUTER_USER_DATA.get("/user/data/new", response_class=HTMLResponse)
async def user_data_new(
    request: Request,
    context: dict = Depends(get_base_context),
):
    """New project creation form."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url="/auth/login?next=/user/data/new", status_code=302)
    return ctx.templates.TemplateResponse(request, "user/new_project.html", context)


@ROUTER_USER_DATA.post("/user/projects/create")
async def user_create_project(
    request: Request,
    title: str = Form(...),
    research_question: str = Form(""),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project and redirect to its file management page."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    slug = _slugify(title)
    try:
        project = await create_user_project(
            db,
            beril_user_id,
            title=title,
            research_question=research_question or None,
            slug=slug,
        )
    except IntegrityError:
        await db.rollback()
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        project = await create_user_project(
            db,
            beril_user_id,
            title=title,
            research_question=research_question or None,
            slug=slug,
        )

    return RedirectResponse(url=f"/user/projects/{project.id}", status_code=302)


@ROUTER_USER_DATA.get("/user/projects/{project_id}", response_class=HTMLResponse)
async def user_project_files(
    request: Request,
    project_id: str,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """File management page for an existing project."""
    user = context.get("current_user")
    if user is None:
        return RedirectResponse(url=f"/auth/login?next=/user/projects/{project_id}", status_code=302)

    beril_user_id = get_beril_user_id(request)
    if beril_user_id is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    project = await get_project_by_id(db, project_id)
    if project is None or project.owner_id != beril_user_id:
        return Response(status_code=403)

    files = await get_files_for_project(db, project_id)
    context["project"] = project
    context["files"] = files
    return ctx.templates.TemplateResponse(request, "user/project_files.html", context)


@ROUTER_USER_DATA.post("/user/data/upload-to-project")
async def user_upload_to_project(
    request: Request,
    project_id: str = Form(...),
    file_type: str = Form("data"),
    is_public: bool = Form(False),
    files: list[UploadFile] = File(default=[]),
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
):
    """Upload one or more files to an existing project."""
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

    # Validate all filenames before writing anything to storage
    for file in files:
        if not file.filename:
            continue
        if _safe_relative_path(file.filename) is None:
            return Response(status_code=422, content=f"Invalid filename: {file.filename!r}")

    storage = _storage()
    for file in files:
        if not file.filename:
            continue
        await _save_upload(
            db, storage, file, project.id, beril_user_id, project.slug, file_type, is_public
        )

    return RedirectResponse(url=f"/user/projects/{project.id}", status_code=302)


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

    return RedirectResponse(url=f"/user/projects/{project_id}", status_code=302)


# ---------------------------------------------------------------------------
# API routes (session or Bearer token)
# ---------------------------------------------------------------------------


@ROUTER_USER_DATA.get("/api/user/projects/{project_id}/files")
async def api_list_project_files(
    request: Request,
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return JSON list of files for a project. Owner-only."""
    user = await get_current_user_session_or_token(request, db)
    if user is None:
        return Response(status_code=401)

    project = await get_project_by_id(db, project_id)
    if project is None or project.owner_id != user.id:
        return Response(status_code=403)

    files = await get_files_for_project(db, project_id)
    return JSONResponse([
        {
            "id": f.id,
            "filename": f.filename,
            "file_type": f.file_type,
            "size_bytes": f.size_bytes,
            "uploaded_at": f.uploaded_at.isoformat(),
        }
        for f in files
    ])


@ROUTER_USER_DATA.get("/api/data/{file_id}")
async def api_get_file(
    request: Request,
    file_id: str,
    view: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Return file bytes. Accessible to the owner or if the file is public.

    Pass ?view=1 to get an inline Content-Disposition (browser display)
    instead of the default attachment (download).
    """
    file = await get_file_by_id(db, file_id)
    if file is None:
        return Response(status_code=404)

    project = await get_project_by_id(db, file.project_id)
    if project is None:
        return Response(status_code=404)

    if not file.is_public:
        user = await get_current_user_session_or_token(request, db)
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
    disposition = "inline" if view else "attachment"
    return Response(
        content=data,
        media_type=file.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded}"},
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
