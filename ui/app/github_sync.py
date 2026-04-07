"""GitHub repository sync for user projects.

Pulls files from a linked GitHub repo into local project storage and upserts
ProjectFile records in the database.
"""

import logging
import mimetypes
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import create_project_file, delete_project_file, get_github_files_for_project
from app.db.models import ProjectFile, UserProject
from app.git_data_sync import _git_clone, _git_lock, _git_pull
from app.storage import LocalFileStorage

logger = logging.getLogger(__name__)

# Files and directories to skip when syncing from a repo
_SKIP_NAMES = {".git", ".github", "__pycache__", ".DS_Store"}

# stderr substrings that indicate a missing branch (as opposed to a transient error)
_BRANCH_NOT_FOUND_HINTS = (
    "couldn't find remote ref",
    "remote ref does not exist",
    "pathspec",
    "invalid reference",
    "error: branch",
)


def _is_branch_error(exc: BaseException) -> bool:
    """Return True if *exc* looks like a 'branch not found' git error."""
    if not isinstance(exc, subprocess.CalledProcessError):
        return False
    stderr = (exc.stderr or b"").decode().lower()
    return any(hint in stderr for hint in _BRANCH_NOT_FOUND_HINTS)


# Only these two branches have an automatic fallback; any other branch name
# must fail explicitly so the caller is not silently served the wrong content.
_FALLBACK_PAIRS: dict[str, str] = {"main": "master", "master": "main"}


def _fallback_branch(branch: str) -> str | None:
    """Return the fallback branch for *branch*, or None if no fallback applies."""
    return _FALLBACK_PAIRS.get(branch)


async def sync_github_repo(
    repo_url: str,
    project: UserProject,
    storage: LocalFileStorage,
    db: AsyncSession,
    branch: str = "main",
) -> tuple[list[ProjectFile], str]:
    """Pull files from a GitHub repo into project storage and sync DB records.

    Shallow-clones or pulls `repo_url` into a cache directory under the
    project's storage path, then copies non-hidden files into the project
    storage area and upserts `ProjectFile` records.

    Args:
        repo_url: HTTPS or SSH GitHub repo URL.
        project: The owning UserProject (needs owner_id and slug).
        storage: LocalFileStorage rooted at user_projects_root.
        db: Async database session.
        branch: Branch to sync. Tries "main", falls back to "master" if clone fails.

    Returns:
        Tuple of (upserted ProjectFile records, actual branch checked out).
        The actual branch may differ from `branch` when the main↔master fallback fires.
    """
    owner_id, slug = project.filesystem_path_parts
    cache_rel = f"{owner_id}/{slug}/.git_cache"
    cache_path = storage.root / cache_rel

    # Clone or pull into the cache directory; may fall back to master/main
    actual_branch = await _ensure_repo(repo_url, branch, cache_path)

    # Only consider files previously synced from GitHub; manually uploaded files
    # are untouched even if they share the same project.
    existing = {f.filename: f for f in await get_github_files_for_project(db, project.id)}
    repo_filenames: set[str] = set()

    synced: list[ProjectFile] = []
    for src in _iter_files(cache_path):
        # Preserve subdirectory structure relative to the repo root.
        # e.g. notebooks/analysis.ipynb → filename "notebooks/analysis.ipynb"
        rel_path = src.relative_to(cache_path)
        filename = str(rel_path)  # used as the stable key in DB
        repo_filenames.add(filename)
        # Store under a "github/" namespace so GitHub blobs never collide with
        # manually uploaded files in the same project storage area.
        dest_rel = f"{owner_id}/{slug}/github/{filename}"

        data = src.read_bytes()
        size = await storage.save(data, dest_rel)

        content_type, _ = mimetypes.guess_type(src.name)
        file_type = _infer_file_type(src.name)

        if filename in existing:
            record = existing[filename]
            record.storage_path = dest_rel
            record.size_bytes = size
            record.content_type = content_type
            await db.commit()
            await db.refresh(record)
        else:
            try:
                record = await create_project_file(
                    db,
                    project_id=project.id,
                    file_type=file_type,
                    filename=filename,
                    storage_path=dest_rel,
                    size_bytes=size,
                    content_type=content_type,
                    source="github",
                )
            except IntegrityError:
                # Concurrent sync beat us — roll back and update the winner's row.
                await db.rollback()
                refreshed = await get_github_files_for_project(db, project.id)
                existing = {f.filename: f for f in refreshed}
                record = existing[filename]
                record.storage_path = dest_rel
                record.size_bytes = size
                record.content_type = content_type
                await db.commit()
                await db.refresh(record)

        synced.append(record)
        logger.debug("Synced %s → %s", filename, dest_rel)

    # Remove DB records and storage blobs for files deleted from the repo
    for filename, record in existing.items():
        if filename not in repo_filenames:
            await storage.delete(record.storage_path)
            await delete_project_file(db, record.id)
            logger.debug("Removed deleted file %s", filename)

    logger.info("Synced %d file(s) from %s for project %s", len(synced), repo_url, project.id)
    return synced, actual_branch


async def _ensure_repo(repo_url: str, branch: str, local_path: Path) -> str:
    """Clone the repo if it doesn't exist, otherwise pull. Falls back main→master.

    Holds _git_lock for the duration to prevent concurrent operations on the
    same cache directory.

    Returns the branch that was actually checked out (may differ from `branch`
    if the automatic main↔master fallback was used).
    """
    async with _git_lock:
        if local_path.exists() and (local_path / ".git").exists():
            try:
                await _git_pull(local_path, branch)
                return branch
            except Exception as exc:
                if not _is_branch_error(exc):
                    # Transient error (network, auth, disk) — do not silently switch
                    # branches; re-raise so the caller can handle or retry.
                    raise
                fallback = _fallback_branch(branch)
                if fallback is None:
                    # Non-main/master branch with no automatic fallback — re-raise.
                    raise
                # The branch is missing from the single-branch cache; delete and
                # reclone on the fallback branch.
                logger.warning(
                    "Pull on branch %r failed (branch not found), recloning on %r",
                    branch,
                    fallback,
                )
                shutil.rmtree(local_path)
                await _git_clone(repo_url, fallback, local_path)
                return fallback

        # Clean up any stale/partial directory before cloning
        if local_path.exists():
            shutil.rmtree(local_path)

        try:
            await _git_clone(repo_url, branch, local_path)
            return branch
        except Exception as exc:
            # Only fall back if the branch genuinely doesn't exist; re-raise
            # for transient errors so the caller sees the real failure.
            if not _is_branch_error(exc):
                raise
            fallback = _fallback_branch(branch)
            if fallback is None:
                # Non-main/master branch — no automatic fallback, re-raise.
                raise
            if local_path.exists():
                shutil.rmtree(local_path)
            logger.warning("Clone of branch %r failed (branch not found), trying %r", branch, fallback)
            await _git_clone(repo_url, fallback, local_path)
            return fallback


def _iter_files(repo_path: Path):
    """Yield all non-hidden, non-skipped regular files recursively under repo_path.

    Symlinks are always skipped — a malicious repo could point a symlink at
    an arbitrary host path (e.g. /etc/passwd), so we never follow them.
    """
    for entry in repo_path.iterdir():
        if entry.name in _SKIP_NAMES or entry.name.startswith("."):
            continue
        if entry.is_symlink():
            logger.warning("Skipping symlink in repo: %s", entry)
            continue
        if entry.is_dir():
            yield from _iter_files(entry)
        elif entry.is_file():
            yield entry


def _infer_file_type(filename: str) -> str:
    """Map a filename to a ProjectFile file_type enum value."""
    ext = Path(filename).suffix.lower()
    if ext == ".ipynb":
        return "notebook"
    if ext in {".md", ".rst", ".txt"} and "readme" in filename.lower():
        return "readme"
    if ext in {".html", ".png", ".jpg", ".jpeg", ".svg", ".pdf"}:
        return "visualization"
    return "data"
