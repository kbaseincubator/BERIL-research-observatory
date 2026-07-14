"""Repo-to-database project importer.

Handles the one-time (and ongoing transition-period) migration of projects
from the git repository filesystem into the database and managed filestore.

Key design points:
- Idempotent: safe to run repeatedly; uses ProjectImportRecord to track state.
- Sentinel user (SENTINEL_ORCID) owns projects with no linked ORCiD.
- Known ORCiD IDs get a real BerilUser row created on first import.
- Files are physically copied into the managed volume under the same
  {owner_id}/{slug}/uploads/ structure used by user-uploaded files.
- Re-imports a project if its README/PLAN/REPORT mtime is newer than
  last_synced_at on the import record.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_parser import (
    ParsedProjectFields,
    parse_notebook_metadata,
    parse_project_fields,
    scan_project_files,
)
from app.db.models import (
    BerilUser,
    ProjectCollection,
    ProjectContributor,
    ProjectFile,
    ProjectImportRecord,
    UserProject,
)
from app.storage import LocalFileStorage

logger = logging.getLogger(__name__)

SENTINEL_ORCID = "9999-9999-9999-9999"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class ImportResult:
    repo_path: str
    status: str  # imported | skipped | failed
    project_id: str | None = None
    message: str = ""


@dataclass
class MigrationSummary:
    total: int = 0
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    results: list[ImportResult] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.results is None:
            self.results = []


# ---------------------------------------------------------------------------
# User resolution
# ---------------------------------------------------------------------------


async def _get_or_create_sentinel(db: AsyncSession) -> BerilUser:
    """Return (creating if needed) the sentinel BerilUser for unowned projects."""
    result = await db.execute(
        select(BerilUser).where(BerilUser.orcid_id == SENTINEL_ORCID)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = BerilUser(
            orcid_id=SENTINEL_ORCID,
            display_name="BERIL Repository (unowned)",
            is_active=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Created sentinel user %s", SENTINEL_ORCID)
    return user


async def resolve_owner(
    db: AsyncSession,
    parsed: ParsedProjectFields,
) -> BerilUser:
    """Return the BerilUser who should own this project.

    - If any contributor has an ORCiD, use the first one found.
      Create a new BerilUser if that ORCiD isn't registered yet.
    - Otherwise fall back to the sentinel user.
    """
    for contrib in parsed.contributors:
        if not contrib.orcid:
            continue
        result = await db.execute(
            select(BerilUser).where(BerilUser.orcid_id == contrib.orcid)
        )
        user = result.scalar_one_or_none()
        if user is not None:
            return user
        # Create a stub account for this ORCiD
        user = BerilUser(
            orcid_id=contrib.orcid,
            display_name=contrib.name,
            affiliation=contrib.affiliation,
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            logger.info("Created user for ORCiD %s (%s)", contrib.orcid, contrib.name)
            return user
        except IntegrityError:
            await db.rollback()
            # Another concurrent import beat us — fetch the now-existing row
            result = await db.execute(
                select(BerilUser).where(BerilUser.orcid_id == contrib.orcid)
            )
            user = result.scalar_one_or_none()
            if user is not None:
                return user

    return await _get_or_create_sentinel(db)


# ---------------------------------------------------------------------------
# Import record helpers
# ---------------------------------------------------------------------------


async def _get_import_record(db: AsyncSession, repo_path: str) -> ProjectImportRecord | None:
    result = await db.execute(
        select(ProjectImportRecord).where(ProjectImportRecord.repo_path == repo_path)
    )
    return result.scalar_one_or_none()


async def _upsert_import_record(
    db: AsyncSession,
    repo_path: str,
    *,
    project_id: str | None,
    status: str,
    error_message: str | None = None,
) -> ProjectImportRecord:
    record = await _get_import_record(db, repo_path)
    now = datetime.now(timezone.utc)
    if record is None:
        record = ProjectImportRecord(
            repo_path=repo_path,
            project_id=project_id,
            status=status,
            error_message=error_message,
            imported_at=now,
            last_synced_at=now if status == "imported" else None,
        )
        db.add(record)
    else:
        record.project_id = project_id
        record.status = status
        record.error_message = error_message
        if status == "imported":
            record.last_synced_at = now
    await db.commit()
    await db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Staleness check
# ---------------------------------------------------------------------------


def _source_mtime(project_dir: Path) -> datetime:
    """Return the most recent mtime of any importable file in the project directory."""
    scanned = scan_project_files(project_dir)
    if not scanned:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return max(pf.mtime for pf in scanned)


def _is_stale(record: ProjectImportRecord, project_dir: Path) -> bool:
    """True if any source file is newer than last_synced_at."""
    if record.last_synced_at is None:
        return True
    synced = record.last_synced_at
    if synced.tzinfo is None:
        synced = synced.replace(tzinfo=timezone.utc)
    return _source_mtime(project_dir) > synced


# ---------------------------------------------------------------------------
# File copy
# ---------------------------------------------------------------------------


async def _copy_project_files(
    project_dir: Path,
    storage: LocalFileStorage,
    owner_id: str,
    slug: str,
    project_id: str,
    db: AsyncSession,
) -> int:
    """Copy all files from project_dir into the managed volume and create DB records.

    Returns the number of files copied.
    """
    copied = 0
    scanned = scan_project_files(project_dir)

    for pf in scanned:
        src = project_dir / pf.relative_path
        storage_path = f"{owner_id}/{slug}/uploads/{pf.relative_path}"

        # Determine title for notebooks
        title: str | None = None
        description: str | None = None
        if pf.file_type == "notebook":
            nb_meta = parse_notebook_metadata(src)
            title = nb_meta.title
            description = nb_meta.description

        data = src.read_bytes()
        size = await storage.save(data, storage_path)

        # Upsert the DB record (unique on project_id + filename + source)
        result = await db.execute(
            select(ProjectFile).where(
                ProjectFile.project_id == project_id,
                ProjectFile.filename == pf.relative_path,
                ProjectFile.source == "repo_import",
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.storage_path = storage_path
            existing.size_bytes = size
            existing.content_type = pf.content_type
            existing.last_updated_at = pf.mtime
            existing.title = title or existing.title
            existing.description = description or existing.description
        else:
            db.add(ProjectFile(
                project_id=project_id,
                file_type=pf.file_type,
                filename=pf.relative_path,
                storage_path=storage_path,
                size_bytes=size,
                content_type=pf.content_type,
                title=title,
                description=description,
                is_public=True,  # repo projects are public by default
                source="repo_import",
                last_updated_at=pf.mtime,
            ))
        copied += 1

    # Delete ProjectFile rows (and storage blobs) for files no longer in the source tree
    scanned_paths = {pf.relative_path for pf in scanned}
    existing_result = await db.execute(
        select(ProjectFile).where(
            ProjectFile.project_id == project_id,
            ProjectFile.source == "repo_import",
        )
    )
    for row in existing_result.scalars().all():
        if row.filename not in scanned_paths:
            await storage.delete(row.storage_path)
            await db.delete(row)

    await db.commit()
    return copied


# ---------------------------------------------------------------------------
# Single-project import
# ---------------------------------------------------------------------------


async def import_project(
    db: AsyncSession,
    storage: LocalFileStorage,
    project_dir: Path,
    repo_root: Path,
) -> ImportResult:
    """Idempotently import one project directory into the DB and filestore.

    - Skips if already imported and source files haven't changed.
    - Re-imports (upserts) if source files are newer than last_synced_at.
    """
    repo_path = str(project_dir.relative_to(repo_root))  # e.g. "projects/my_project"
    slug = project_dir.name

    readme_path = project_dir / "README.md"
    if not readme_path.exists():
        return ImportResult(repo_path=repo_path, status="skipped", message="No README.md")

    # Check import record
    record = await _get_import_record(db, repo_path)
    if record is not None and record.status == "imported" and not _is_stale(record, project_dir):
        return ImportResult(
            repo_path=repo_path,
            status="skipped",
            project_id=record.project_id,
            message="Up to date",
        )

    try:
        # Parse content
        readme = readme_path.read_text(encoding="utf-8")
        plan_path = project_dir / "RESEARCH_PLAN.md"
        report_path = project_dir / "REPORT.md"
        plan = plan_path.read_text(encoding="utf-8") if plan_path.exists() else None
        report = report_path.read_text(encoding="utf-8") if report_path.exists() else None

        parsed = parse_project_fields(readme, plan, report, project_id=slug)

        # Resolve owner
        owner = await resolve_owner(db, parsed)

        # Upsert UserProject — match on repo_path slug
        result = await db.execute(
            select(UserProject).where(UserProject.repo_path == repo_path)
        )
        project = result.scalar_one_or_none()

        other_sections_json = json.dumps(parsed.other_sections) if parsed.other_sections else None

        if project is None:
            project = UserProject(
                owner_id=owner.id,
                slug=slug,
                title=parsed.title,
                research_question=parsed.research_question,
                status=parsed.status,
                hypothesis=parsed.hypothesis,
                approach=parsed.approach,
                findings=parsed.findings,
                overview=parsed.overview,
                results=parsed.results,
                interpretation=parsed.interpretation,
                limitations=parsed.limitations,
                future_directions=parsed.future_directions,
                data_section=parsed.data_section,
                references_text=parsed.references_text,
                revision_history=parsed.revision_history,
                other_sections=other_sections_json,
                raw_readme=parsed.raw_readme,
                research_plan_raw=parsed.research_plan_raw,
                report_raw=parsed.report_raw,
                origin="repo",
                repo_path=repo_path,
                is_public=True,
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)
        else:
            # Update all parsed fields
            project.owner_id = owner.id
            project.title = parsed.title
            project.research_question = parsed.research_question
            project.status = parsed.status
            project.hypothesis = parsed.hypothesis
            project.approach = parsed.approach
            project.findings = parsed.findings
            project.overview = parsed.overview
            project.results = parsed.results
            project.interpretation = parsed.interpretation
            project.limitations = parsed.limitations
            project.future_directions = parsed.future_directions
            project.data_section = parsed.data_section
            project.references_text = parsed.references_text
            project.revision_history = parsed.revision_history
            project.other_sections = other_sections_json
            project.raw_readme = parsed.raw_readme
            project.research_plan_raw = parsed.research_plan_raw
            project.report_raw = parsed.report_raw
            await db.commit()
            await db.refresh(project)

        # Sync contributors: update/insert parsed names, delete names no longer present
        existing_contribs = await db.execute(
            select(ProjectContributor).where(ProjectContributor.project_id == project.id)
        )
        existing_by_name = {c.name: c for c in existing_contribs.scalars().all()}
        parsed_names = {c.name for c in parsed.contributors}

        for name, ec in existing_by_name.items():
            if name not in parsed_names:
                await db.delete(ec)

        for contrib in parsed.contributors:
            if contrib.name in existing_by_name:
                ec = existing_by_name[contrib.name]
                ec.orcid_id = contrib.orcid or ec.orcid_id
                ec.role = ", ".join(contrib.roles) if contrib.roles else ec.role
            else:
                db.add(ProjectContributor(
                    project_id=project.id,
                    name=contrib.name,
                    orcid_id=contrib.orcid,
                    role=", ".join(contrib.roles) if contrib.roles else "Author",
                ))
        await db.commit()

        # Sync collection references: add new, remove stale
        existing_colls = await db.execute(
            select(ProjectCollection).where(ProjectCollection.project_id == project.id)
        )
        existing_coll_rows = {c.collection_id: c for c in existing_colls.scalars().all()}
        parsed_coll_ids = set(parsed.related_collections)

        for coll_id, row in existing_coll_rows.items():
            if coll_id not in parsed_coll_ids:
                await db.delete(row)

        for coll_id in parsed_coll_ids:
            if coll_id not in existing_coll_rows:
                db.add(ProjectCollection(project_id=project.id, collection_id=coll_id))
        await db.commit()

        # Copy files
        n_files = await _copy_project_files(
            project_dir, storage, owner.id, slug, project.id, db
        )

        await _upsert_import_record(
            db, repo_path, project_id=project.id, status="imported"
        )

        logger.info(
            "Imported project %r → %s (%d files, owner=%s)",
            slug, project.id, n_files, owner.orcid_id,
        )
        return ImportResult(
            repo_path=repo_path,
            status="imported",
            project_id=project.id,
            message=f"{n_files} files copied",
        )

    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to import project %r", repo_path)
        await _upsert_import_record(
            db, repo_path, project_id=None, status="failed",
            error_message=str(exc)[:1000],
        )
        return ImportResult(
            repo_path=repo_path,
            status="failed",
            message=str(exc),
        )


# ---------------------------------------------------------------------------
# Full migration runner
# ---------------------------------------------------------------------------


async def run_full_migration(
    db: AsyncSession,
    storage: LocalFileStorage,
    projects_root: Path,
) -> MigrationSummary:
    """Import all project directories under projects_root.

    Safe to call repeatedly — already-imported, unchanged projects are skipped.
    """
    summary = MigrationSummary()

    if not projects_root.exists():
        logger.warning("projects_root does not exist: %s", projects_root)
        return summary

    project_dirs = sorted(
        d for d in projects_root.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    summary.total = len(project_dirs)

    for project_dir in project_dirs:
        result = await import_project(db, storage, project_dir, projects_root.parent)
        summary.results.append(result)
        if result.status == "imported":
            summary.imported += 1
        elif result.status == "skipped":
            summary.skipped += 1
        else:
            summary.failed += 1

    logger.info(
        "Migration complete: %d imported, %d skipped, %d failed (total %d)",
        summary.imported, summary.skipped, summary.failed, summary.total,
    )
    return summary
