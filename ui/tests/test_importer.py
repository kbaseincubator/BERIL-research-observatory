"""Tests for app.importer — idempotent repo-to-DB project migration."""

import pytest

from app.db.models import BerilUser, ProjectFile, ProjectImportRecord, UserProject
from app.importer import (
    SENTINEL_ORCID,
    _get_import_record,
    _is_stale,
    _source_mtime,
    _upsert_import_record,
    import_project,
    resolve_owner,
    run_full_migration,
)
from app.storage import LocalFileStorage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def projects_root(tmp_path):
    """Minimal fake repo root with a projects/ directory."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "projects").mkdir()
    return root


@pytest.fixture
def storage(tmp_path):
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    return LocalFileStorage(storage_root)


def _make_project_dir(projects_root, slug, *, readme=None, plan=None, report=None):
    """Create a project directory with the given markdown files."""
    d = projects_root / "projects" / slug
    d.mkdir(parents=True, exist_ok=True)
    if readme is not None:
        (d / "README.md").write_text(readme, encoding="utf-8")
    if plan is not None:
        (d / "RESEARCH_PLAN.md").write_text(plan, encoding="utf-8")
    if report is not None:
        (d / "REPORT.md").write_text(report, encoding="utf-8")
    return d


# ---------------------------------------------------------------------------
# _source_mtime
# ---------------------------------------------------------------------------


class TestSourceMtime:
    def test_returns_epoch_when_no_files(self, tmp_path):
        from datetime import datetime, timezone
        result = _source_mtime(tmp_path)
        assert result == datetime.fromtimestamp(0, tz=timezone.utc)

    def test_returns_most_recent_mtime(self, tmp_path):
        import time
        from datetime import datetime, timezone
        (tmp_path / "README.md").write_text("x")
        time.sleep(0.01)
        (tmp_path / "RESEARCH_PLAN.md").write_text("y")
        mtime = _source_mtime(tmp_path)
        plan_mtime = datetime.fromtimestamp(
            (tmp_path / "RESEARCH_PLAN.md").stat().st_mtime, tz=timezone.utc
        )
        assert abs((mtime - plan_mtime).total_seconds()) < 0.01

    def test_detects_non_markdown_file_changes(self, tmp_path):
        import time
        from datetime import datetime, timezone
        (tmp_path / "README.md").write_text("x")
        time.sleep(0.01)
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")
        mtime = _source_mtime(tmp_path)
        csv_mtime = datetime.fromtimestamp(
            (tmp_path / "data.csv").stat().st_mtime, tz=timezone.utc
        )
        assert abs((mtime - csv_mtime).total_seconds()) < 0.01


# ---------------------------------------------------------------------------
# _is_stale
# ---------------------------------------------------------------------------


class TestIsStale:
    def test_stale_when_no_last_synced(self, tmp_path):
        record = ProjectImportRecord(
            repo_path="projects/test",
            status="imported",
            last_synced_at=None,
        )
        (tmp_path / "README.md").write_text("x")
        assert _is_stale(record, tmp_path) is True

    def test_not_stale_when_recently_synced(self, tmp_path):
        from datetime import datetime, timezone
        (tmp_path / "README.md").write_text("x")
        # Set last_synced_at to far in the future
        future = datetime(2099, 1, 1, tzinfo=timezone.utc)
        record = ProjectImportRecord(
            repo_path="projects/test",
            status="imported",
            last_synced_at=future,
        )
        assert _is_stale(record, tmp_path) is False


# ---------------------------------------------------------------------------
# _upsert_import_record
# ---------------------------------------------------------------------------


class TestUpsertImportRecord:
    async def test_creates_new_record(self, db_session):
        record = await _upsert_import_record(
            db_session, "projects/alpha",
            project_id="abc-123",
            status="imported",
        )
        assert record.repo_path == "projects/alpha"
        assert record.status == "imported"
        assert record.project_id == "abc-123"

    async def test_updates_existing_record(self, db_session):
        await _upsert_import_record(
            db_session, "projects/alpha",
            project_id=None,
            status="failed",
            error_message="oops",
        )
        record = await _upsert_import_record(
            db_session, "projects/alpha",
            project_id="abc-123",
            status="imported",
        )
        assert record.status == "imported"
        assert record.project_id == "abc-123"
        assert record.error_message is None

    async def test_sets_last_synced_at_on_import(self, db_session):
        record = await _upsert_import_record(
            db_session, "projects/alpha",
            project_id="abc",
            status="imported",
        )
        assert record.last_synced_at is not None

    async def test_does_not_set_last_synced_at_on_failure(self, db_session):
        record = await _upsert_import_record(
            db_session, "projects/alpha",
            project_id=None,
            status="failed",
            error_message="boom",
        )
        assert record.last_synced_at is None


# ---------------------------------------------------------------------------
# resolve_owner
# ---------------------------------------------------------------------------


class TestResolveOwner:
    async def test_returns_sentinel_when_no_orcid(self, db_session):
        from app.content_parser import ParsedProjectFields
        parsed = ParsedProjectFields(contributors=[])
        owner = await resolve_owner(db_session, parsed)
        assert owner.orcid_id == SENTINEL_ORCID

    async def test_returns_existing_user_when_orcid_matches(self, db_session):
        from app.content_parser import ParsedContributor, ParsedProjectFields
        user = BerilUser(orcid_id="0000-0001-2345-6789", display_name="Alice")
        db_session.add(user)
        await db_session.commit()

        parsed = ParsedProjectFields(
            contributors=[ParsedContributor(name="Alice", orcid="0000-0001-2345-6789")]
        )
        owner = await resolve_owner(db_session, parsed)
        assert owner.id == user.id

    async def test_creates_user_for_new_orcid(self, db_session):
        from app.content_parser import ParsedContributor, ParsedProjectFields
        parsed = ParsedProjectFields(
            contributors=[ParsedContributor(name="Bob", orcid="0000-0002-9999-0000")]
        )
        owner = await resolve_owner(db_session, parsed)
        assert owner.orcid_id == "0000-0002-9999-0000"
        assert owner.display_name == "Bob"


# ---------------------------------------------------------------------------
# import_project — single project
# ---------------------------------------------------------------------------


class TestImportProject:
    async def test_skips_directory_without_readme(self, db_session, storage, projects_root):
        d = _make_project_dir(projects_root, "no_readme")
        result = await import_project(db_session, storage, d, projects_root)
        assert result.status == "skipped"
        assert "README" in result.message

    async def test_imports_minimal_project(self, db_session, storage, projects_root):
        d = _make_project_dir(
            projects_root, "alpha",
            readme="# Alpha Project\n\n## Research Question\nQ?\n",
        )
        result = await import_project(db_session, storage, d, projects_root)
        assert result.status == "imported"
        assert result.project_id is not None

    async def test_creates_userproject_row(self, db_session, storage, projects_root):
        d = _make_project_dir(
            projects_root, "beta",
            readme="# Beta\n\n## Research Question\nQ?\n",
        )
        result = await import_project(db_session, storage, d, projects_root)
        row = await db_session.get(UserProject, result.project_id)
        assert row is not None
        assert row.title == "Beta"
        assert row.origin == "repo"

    async def test_copies_files_to_storage(self, db_session, storage, projects_root):
        d = _make_project_dir(
            projects_root, "gamma",
            readme="# Gamma\n",
        )
        (d / "data.csv").write_text("x,y\n1,2\n")
        await import_project(db_session, storage, d, projects_root)

        # At least README.md and data.csv should be stored
        from sqlalchemy import select
        result = await db_session.execute(
            select(ProjectFile).where(ProjectFile.source == "repo_import")
        )
        files = result.scalars().all()
        filenames = {f.filename for f in files}
        assert "README.md" in filenames
        assert "data.csv" in filenames

    async def test_skips_unchanged_project_on_reimport(self, db_session, storage, projects_root):
        d = _make_project_dir(
            projects_root, "delta",
            readme="# Delta\n",
        )
        r1 = await import_project(db_session, storage, d, projects_root)
        assert r1.status == "imported"

        r2 = await import_project(db_session, storage, d, projects_root)
        assert r2.status == "skipped"
        assert r2.message == "Up to date"

    async def test_reimports_when_readme_updated(self, db_session, storage, projects_root):
        import time
        d = _make_project_dir(
            projects_root, "epsilon",
            readme="# Epsilon\n",
        )
        r1 = await import_project(db_session, storage, d, projects_root)
        assert r1.status == "imported"

        # Touch the README to make it newer than last_synced_at
        time.sleep(0.02)
        (d / "README.md").write_text("# Epsilon Updated\n")
        r2 = await import_project(db_session, storage, d, projects_root)
        assert r2.status == "imported"

    async def test_deletes_removed_files_on_resync(self, db_session, storage, projects_root):
        """Files removed from the repo directory should be deleted from DB and storage on resync."""
        import time
        from sqlalchemy import select as sa_select

        d = _make_project_dir(projects_root, "file_del", readme="# File Del\n")
        (d / "data.csv").write_text("a,b\n1,2\n")
        r1 = await import_project(db_session, storage, d, projects_root)
        assert r1.status == "imported"

        result = await db_session.execute(
            sa_select(ProjectFile).where(
                ProjectFile.project_id == r1.project_id,
                ProjectFile.source == "repo_import",
            )
        )
        filenames = {f.filename for f in result.scalars().all()}
        assert "data.csv" in filenames

        # Remove data.csv and resync
        time.sleep(0.02)
        (d / "data.csv").unlink()
        (d / "README.md").write_text("# File Del Updated\n")
        r2 = await import_project(db_session, storage, d, projects_root)
        assert r2.status == "imported"

        result = await db_session.execute(
            sa_select(ProjectFile).where(
                ProjectFile.project_id == r2.project_id,
                ProjectFile.source == "repo_import",
            )
        )
        remaining = {f.filename for f in result.scalars().all()}
        assert "data.csv" not in remaining
        assert "README.md" in remaining

    async def test_reimports_when_non_markdown_file_changes(self, db_session, storage, projects_root):
        """Updating a CSV without touching markdown should still trigger a re-import."""
        import time

        d = _make_project_dir(projects_root, "nonmd", readme="# NonMD\n")
        (d / "data.csv").write_text("a\n1\n")
        r1 = await import_project(db_session, storage, d, projects_root)
        assert r1.status == "imported"

        r2 = await import_project(db_session, storage, d, projects_root)
        assert r2.status == "skipped"

        # Update only the CSV
        time.sleep(0.02)
        (d / "data.csv").write_text("a\n1\n2\n")
        r3 = await import_project(db_session, storage, d, projects_root)
        assert r3.status == "imported"

    async def test_removes_stale_contributors_on_resync(self, db_session, storage, projects_root):
        """Contributors removed from README should be deleted on resync."""
        import time
        from sqlalchemy import select as sa_select
        from app.db.models import ProjectContributor

        readme_with_two = (
            "# Zeta\n\n## Authors\n"
            "- **Alice** (LBNL) | ORCID: 0000-0001-2345-6789\n"
            "- **Bob** (ORNL) | ORCID: 0000-0002-9999-0000\n"
        )
        d = _make_project_dir(projects_root, "zeta", readme=readme_with_two)
        r1 = await import_project(db_session, storage, d, projects_root)
        assert r1.status == "imported"

        result = await db_session.execute(
            sa_select(ProjectContributor).where(ProjectContributor.project_id == r1.project_id)
        )
        assert len(result.scalars().all()) == 2

        # Remove Bob
        time.sleep(0.02)
        readme_with_one = (
            "# Zeta\n\n## Authors\n"
            "- **Alice** (LBNL) | ORCID: 0000-0001-2345-6789\n"
        )
        (d / "README.md").write_text(readme_with_one)
        r2 = await import_project(db_session, storage, d, projects_root)
        assert r2.status == "imported"

        result = await db_session.execute(
            sa_select(ProjectContributor).where(ProjectContributor.project_id == r2.project_id)
        )
        remaining = result.scalars().all()
        assert len(remaining) == 1
        assert remaining[0].name == "Alice"

    async def test_removes_stale_collection_refs_on_resync(self, db_session, storage, projects_root):
        """Collection references removed from README should be deleted on resync."""
        import time
        from sqlalchemy import select as sa_select
        from app.db.models import ProjectCollection

        readme_with_coll = "# Eta\n\nWe used kbase_ke_pangenome and kbase_genomes.\n"
        d = _make_project_dir(projects_root, "eta", readme=readme_with_coll)
        r1 = await import_project(db_session, storage, d, projects_root)
        assert r1.status == "imported"

        result = await db_session.execute(
            sa_select(ProjectCollection).where(ProjectCollection.project_id == r1.project_id)
        )
        assert len(result.scalars().all()) == 2

        # Remove kbase_genomes reference
        time.sleep(0.02)
        (d / "README.md").write_text("# Eta\n\nWe used kbase_ke_pangenome only.\n")
        r2 = await import_project(db_session, storage, d, projects_root)
        assert r2.status == "imported"

        result = await db_session.execute(
            sa_select(ProjectCollection).where(ProjectCollection.project_id == r2.project_id)
        )
        remaining = result.scalars().all()
        assert len(remaining) == 1
        assert remaining[0].collection_id == "kbase_ke_pangenome"

    async def test_records_failure_on_exception(self, db_session, storage, projects_root):
        """If parsing raises, import_project returns status=failed and records error."""
        d = _make_project_dir(projects_root, "broken", readme="")
        # Empty README leads to a no-title parse but should not crash — write a
        # real README but mock the parse to raise
        from unittest.mock import patch
        (d / "README.md").write_text("# OK\n")
        with patch("app.importer.parse_project_fields", side_effect=RuntimeError("boom")):
            result = await import_project(db_session, storage, d, projects_root)
        assert result.status == "failed"
        assert "boom" in result.message

        record = await _get_import_record(db_session, "projects/broken")
        assert record is not None
        assert record.status == "failed"


# ---------------------------------------------------------------------------
# run_full_migration
# ---------------------------------------------------------------------------


class TestRunFullMigration:
    async def test_returns_empty_summary_for_missing_root(self, db_session, storage, tmp_path):
        missing = tmp_path / "no_such_dir"
        summary = await run_full_migration(db_session, storage, missing)
        assert summary.total == 0
        assert summary.imported == 0

    async def test_imports_all_projects(self, db_session, storage, projects_root):
        projects_dir = projects_root / "projects"
        for slug in ("proj_a", "proj_b", "proj_c"):
            d = projects_dir / slug
            d.mkdir()
            (d / "README.md").write_text(f"# {slug}\n")

        summary = await run_full_migration(db_session, storage, projects_dir)
        assert summary.total == 3
        assert summary.imported == 3
        assert summary.failed == 0

    async def test_skips_already_imported(self, db_session, storage, projects_root):
        projects_dir = projects_root / "projects"
        d = projects_dir / "solo"
        d.mkdir()
        (d / "README.md").write_text("# Solo\n")

        s1 = await run_full_migration(db_session, storage, projects_dir)
        assert s1.imported == 1

        s2 = await run_full_migration(db_session, storage, projects_dir)
        assert s2.skipped == 1
        assert s2.imported == 0
