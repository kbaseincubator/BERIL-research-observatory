"""Admin routes for import management."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.context as ctx
from app.auth import get_current_user_session_or_token
from app.config import get_settings
from app.context import get_base_context
from app.db.models import BerilUser, ProjectImportRecord
from app.db.session import get_db
from app.importer import ImportResult, run_full_migration, import_project
from app.storage import LocalFileStorage

logger = logging.getLogger(__name__)

ROUTER_ADMIN = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BerilUser:
    """FastAPI dependency: resolve current user and verify admin role.

    Accepts both session cookie and Bearer token (via get_current_user_session_or_token).
    Raises 401 if not authenticated, 403 if authenticated but not admin.
    """
    user = await get_current_user_session_or_token(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Refresh roles relationship
    await db.refresh(user, ["roles"])
    role_names = {r.role for r in user.roles}
    if "admin" not in role_names:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _storage_from_settings() -> LocalFileStorage:
    settings = get_settings()
    return LocalFileStorage(Path(settings.user_projects_root))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@ROUTER_ADMIN.get("/import/status", response_class=HTMLResponse)
async def import_status_page(
    request: Request,
    context: dict = Depends(get_base_context),
    db: AsyncSession = Depends(get_db),
    _admin: BerilUser = Depends(require_admin),
):
    """Admin page: show import status for all known repo projects."""
    result = await db.execute(
        select(ProjectImportRecord).order_by(ProjectImportRecord.repo_path)
    )
    records = list(result.scalars().all())

    settings = get_settings()
    projects_root = Path(settings.projects_dir)
    # Count how many directories exist that could be imported
    untracked: list[str] = []
    if projects_root.exists():
        tracked_paths = {r.repo_path for r in records}
        for d in sorted(projects_root.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                repo_path = str(d.relative_to(projects_root.parent))
                if repo_path not in tracked_paths:
                    untracked.append(repo_path)

    context["import_records"] = records
    context["untracked_dirs"] = untracked
    return ctx.templates.TemplateResponse(request, "admin/import_status.html", context)


@ROUTER_ADMIN.post("/import/run")
async def run_import(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: BerilUser = Depends(require_admin),
):
    """Trigger a full migration of all project directories into the DB."""
    settings = get_settings()
    projects_root = Path(settings.projects_dir)
    storage = _storage_from_settings()

    summary = await run_full_migration(db, storage, projects_root)

    return JSONResponse({
        "status": "ok",
        "total": summary.total,
        "imported": summary.imported,
        "skipped": summary.skipped,
        "failed": summary.failed,
        "results": [
            {
                "repo_path": r.repo_path,
                "status": r.status,
                "project_id": r.project_id,
                "message": r.message,
            }
            for r in summary.results
        ],
    })


@ROUTER_ADMIN.post("/import/{slug}/resync")
async def resync_project(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: BerilUser = Depends(require_admin),
):
    """Force re-import of a single project by its slug."""
    settings = get_settings()
    projects_root = Path(settings.projects_dir)
    project_dir = projects_root / slug

    if not project_dir.exists() or not project_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Project directory not found: {slug!r}")

    storage = _storage_from_settings()
    result: ImportResult = await import_project(db, storage, project_dir, projects_root.parent)

    return JSONResponse({
        "repo_path": result.repo_path,
        "status": result.status,
        "project_id": result.project_id,
        "message": result.message,
    })
