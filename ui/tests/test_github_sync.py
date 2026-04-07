"""Tests for GitHub repo sync (app.github_sync)."""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.db.models import BerilUser, UserProject
from app.github_sync import _infer_file_type, _iter_files, sync_github_repo
from app.storage import LocalFileStorage


def _branch_error(branch: str = "main") -> subprocess.CalledProcessError:
    """Return a CalledProcessError that looks like 'branch not found'."""
    stderr = f"error: couldn't find remote ref {branch}".encode()
    return subprocess.CalledProcessError(128, ["git"], b"", stderr)


def _transient_error() -> subprocess.CalledProcessError:
    """Return a CalledProcessError that looks like a network/auth failure."""
    stderr = b"fatal: unable to access 'https://github.com/': Could not resolve host"
    return subprocess.CalledProcessError(128, ["git"], b"", stderr)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def user(db_session):
    u = BerilUser(orcid_id="0000-0001-2345-6789")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def project(db_session, user):
    p = UserProject(owner_id=user.id, slug="my-project", title="T", research_question="Q?")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def storage(tmp_path):
    return LocalFileStorage(tmp_path)


# ---------------------------------------------------------------------------
# _infer_file_type
# ---------------------------------------------------------------------------


class TestInferFileType:
    def test_notebook(self):
        assert _infer_file_type("analysis.ipynb") == "notebook"

    def test_readme_md(self):
        assert _infer_file_type("README.md") == "readme"

    def test_readme_rst(self):
        assert _infer_file_type("README.rst") == "readme"

    def test_visualization_png(self):
        assert _infer_file_type("figure.png") == "visualization"

    def test_visualization_html(self):
        assert _infer_file_type("plot.html") == "visualization"

    def test_default_is_data(self):
        assert _infer_file_type("data.csv") == "data"
        assert _infer_file_type("results.tsv") == "data"
        assert _infer_file_type("unknown.xyz") == "data"


# ---------------------------------------------------------------------------
# _iter_files
# ---------------------------------------------------------------------------


class TestIterFiles:
    def test_yields_regular_files(self, tmp_path):
        (tmp_path / "file_a.csv").write_text("a")
        (tmp_path / "file_b.txt").write_text("b")
        names = {f.name for f in _iter_files(tmp_path)}
        assert names == {"file_a.csv", "file_b.txt"}

    def test_skips_git_directory(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / "data.csv").write_text("x")
        names = {f.name for f in _iter_files(tmp_path)}
        assert ".git" not in names
        assert "data.csv" in names

    def test_skips_hidden_files(self, tmp_path):
        (tmp_path / ".hidden").write_text("x")
        (tmp_path / "visible.csv").write_text("y")
        names = {f.name for f in _iter_files(tmp_path)}
        assert ".hidden" not in names
        assert "visible.csv" in names

    def test_recurses_into_subdirectories(self, tmp_path):
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested.csv").write_text("n")
        (tmp_path / "top.csv").write_text("t")
        paths = list(_iter_files(tmp_path))
        names = {f.name for f in paths}
        assert "nested.csv" in names
        assert "top.csv" in names

    def test_skips_hidden_subdirectory(self, tmp_path):
        (tmp_path / ".hidden_dir").mkdir()
        (tmp_path / ".hidden_dir" / "secret.csv").write_text("s")
        (tmp_path / "visible.csv").write_text("v")
        names = {f.name for f in _iter_files(tmp_path)}
        assert "secret.csv" not in names
        assert "visible.csv" in names

    def test_skips_symlinks(self, tmp_path):
        """Symlinks are never followed to prevent host path traversal."""
        target = tmp_path / "real_file.txt"
        target.write_text("real")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        (tmp_path / "normal.csv").write_text("n")
        names = {f.name for f in _iter_files(tmp_path)}
        assert "link.txt" not in names
        assert "normal.csv" in names

    def test_empty_repo(self, tmp_path):
        assert list(_iter_files(tmp_path)) == []


# ---------------------------------------------------------------------------
# sync_github_repo
# ---------------------------------------------------------------------------


class TestSyncGithubRepo:
    def _fake_repo(self, path: Path, files: dict[str, bytes]) -> None:
        """Write files into a fake cloned repo directory.

        Keys in *files* may include subdirectory components, e.g.
        ``"notebooks/analysis.ipynb"``.
        """
        path.mkdir(parents=True, exist_ok=True)
        (path / ".git").mkdir(exist_ok=True)
        for name, data in files.items():
            dest = path / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

    async def test_sync_creates_project_files(self, db_session, project, storage, tmp_path):
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"data.csv": b"a,b\n1,2", "notebook.ipynb": b"{}"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        assert len(synced) == 2
        filenames = {f.filename for f in synced}
        assert "data.csv" in filenames
        assert "notebook.ipynb" in filenames

    async def test_sync_writes_files_to_storage(self, db_session, project, storage):
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"results.csv": b"x,y\n1,2"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock):
            await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        dest = f"{project.owner_id}/{project.slug}/github/results.csv"
        assert storage.exists(dest)
        assert await storage.load(dest) == b"x,y\n1,2"

    async def test_sync_upserts_existing_file(self, db_session, project, storage):
        from app.db.crud import create_project_file, get_file_by_id

        # Pre-create a GitHub-synced ProjectFile record for the same filename
        existing = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="data",
            filename="data.csv",
            storage_path=f"{project.owner_id}/{project.slug}/github/data.csv",
            size_bytes=0,
            source="github",
        )

        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"data.csv": b"new,content\n"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        assert len(synced) == 1
        assert synced[0].id == existing.id
        refreshed = await get_file_by_id(db_session, existing.id)
        assert refreshed.size_bytes == len(b"new,content\n")

    async def test_sync_infers_file_type(self, db_session, project, storage):
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"analysis.ipynb": b"{}"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        assert synced[0].file_type == "notebook"

    async def test_sync_marks_files_as_github_source(self, db_session, project, storage):
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"data.csv": b"a,b"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        assert synced[0].source == "github"

    async def test_sync_empty_repo_returns_empty(self, db_session, project, storage):
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        assert synced == []

    async def test_sync_recurses_into_subdirectories(self, db_session, project, storage):
        """Files in subdirectories are synced with their relative path as filename."""
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(
            cache_path,
            {
                "root.csv": b"root",
                "notebooks/analysis.ipynb": b"{}",
                "data/raw/results.csv": b"a,b",
            },
        )

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        assert len(synced) == 3
        filenames = {f.filename for f in synced}
        assert "root.csv" in filenames
        assert "notebooks/analysis.ipynb" in filenames
        assert "data/raw/results.csv" in filenames

        # Storage paths should mirror the relative structure under the github/ namespace
        nb_dest = f"{project.owner_id}/{project.slug}/github/notebooks/analysis.ipynb"
        assert storage.exists(nb_dest)

    async def test_sync_deletes_removed_files(self, db_session, project, storage):
        """GitHub-synced files removed from the repo should be deleted from DB and storage."""
        from app.db.crud import create_project_file, get_file_by_id

        # Pre-create a github-sourced file that no longer exists in the repo
        old_path = f"{project.owner_id}/{project.slug}/github/old.csv"
        await storage.save(b"old data", old_path)
        old_record = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="data",
            filename="old.csv",
            storage_path=old_path,
            source="github",
        )

        # Repo now only has new.csv
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"new.csv": b"new,data"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        # Only new.csv should be returned
        assert len(synced) == 1
        assert synced[0].filename == "new.csv"
        # old.csv should be gone from DB and storage
        assert await get_file_by_id(db_session, old_record.id) is None
        assert not storage.exists(old_path)

    async def test_sync_preserves_manually_uploaded_files(self, db_session, project, storage):
        """Manually uploaded files (source='upload') must not be deleted during GitHub sync."""
        from app.db.crud import create_project_file, get_file_by_id

        # Pre-create a manually uploaded file (not from GitHub)
        upload_path = f"{project.owner_id}/{project.slug}/manual.csv"
        await storage.save(b"user data", upload_path)
        upload_record = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="data",
            filename="manual.csv",
            storage_path=upload_path,
            source="upload",  # manually uploaded, not from GitHub
        )

        # GitHub repo has only repo.csv — manual.csv is absent
        cache_path = storage.root / project.owner_id / project.slug / ".git_cache"
        self._fake_repo(cache_path, {"repo.csv": b"repo,data"})

        with patch("app.github_sync._ensure_repo", new_callable=AsyncMock, return_value="main"):
            synced, _ = await sync_github_repo(
                "https://github.com/org/repo", project, storage, db_session
            )

        # Only repo.csv should be in the sync result
        assert len(synced) == 1
        assert synced[0].filename == "repo.csv"
        # manual.csv must still exist in DB and storage
        assert await get_file_by_id(db_session, upload_record.id) is not None
        assert storage.exists(upload_path)


# ---------------------------------------------------------------------------
# _ensure_repo branch fallback
# ---------------------------------------------------------------------------


class TestEnsureRepo:
    async def test_clones_on_main_branch(self, tmp_path):
        from app.github_sync import _ensure_repo

        with patch("app.github_sync._git_clone", new_callable=AsyncMock) as mock_clone:
            await _ensure_repo("https://github.com/org/repo", "main", tmp_path / "cache")
        mock_clone.assert_called_once_with(
            "https://github.com/org/repo", "main", tmp_path / "cache"
        )

    async def test_falls_back_to_master_on_clone_failure(self, tmp_path):
        from app.github_sync import _ensure_repo

        calls = []
        cache = tmp_path / "cache"

        async def clone_side_effect(url, branch, path):
            calls.append(branch)
            if branch == "main":
                # Simulate git clone leaving a partial directory behind
                path.mkdir(parents=True, exist_ok=True)
                raise _branch_error("main")

        with patch("app.github_sync._git_clone", side_effect=clone_side_effect):
            await _ensure_repo("https://github.com/org/repo", "main", cache)

        assert calls == ["main", "master"]
        # The partial directory must have been cleaned up before the retry
        # (if it still existed, the second clone would have failed too)

    async def test_clone_transient_error_is_not_silently_retried(self, tmp_path):
        """A network/auth failure during clone must propagate, not trigger branch fallback."""
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"

        async def clone_side_effect(url, branch, path):
            raise _transient_error()

        with patch("app.github_sync._git_clone", side_effect=clone_side_effect):
            with pytest.raises(subprocess.CalledProcessError):
                await _ensure_repo("https://github.com/org/repo", "main", cache)

    async def test_non_default_branch_does_not_fall_back(self, tmp_path):
        """Branches other than main/master must not silently fall back to another branch."""
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"

        async def clone_side_effect(url, branch, path):
            raise _branch_error(branch)

        with patch("app.github_sync._git_clone", side_effect=clone_side_effect):
            with pytest.raises(subprocess.CalledProcessError):
                # 'develop' has no automatic fallback pair
                await _ensure_repo("https://github.com/org/repo", "develop", cache)

    async def test_stale_clone_dir_cleaned_before_fallback(self, tmp_path):
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"

        async def clone_side_effect(url, branch, path):
            if branch == "main":
                path.mkdir(parents=True, exist_ok=True)
                (path / "stale_file").write_text("leftover")
                raise _branch_error("main")
            # fallback succeeds — verify the stale dir was removed first
            assert not path.exists() or not (path / "stale_file").exists()

        with patch("app.github_sync._git_clone", side_effect=clone_side_effect):
            await _ensure_repo("https://github.com/org/repo", "main", cache)

    async def test_stale_dir_without_git_is_cleaned_before_clone(self, tmp_path):
        """A partial dir with no .git should be removed and the same branch retried."""
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "leftover").write_text("stale")

        calls = []

        async def clone_side_effect(url, branch, path):
            calls.append(branch)
            # verify dir was cleaned before this call
            assert not path.exists()

        with patch("app.github_sync._git_clone", side_effect=clone_side_effect):
            await _ensure_repo("https://github.com/org/repo", "main", cache)

        assert calls == ["main"]  # no fallback needed — same branch retried cleanly

    async def test_pulls_when_repo_exists(self, tmp_path):
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / ".git").mkdir()

        with patch("app.github_sync._git_pull", new_callable=AsyncMock) as mock_pull:
            await _ensure_repo("https://github.com/org/repo", "main", cache)

        mock_pull.assert_called_once_with(cache, "main")

    async def test_reclones_on_fallback_branch_when_pull_fails(self, tmp_path):
        """When pull fails with branch-not-found on an existing cache, delete the cache
        and reclone on the fallback branch.

        A single-branch clone only has the original branch; pulling a different
        branch would fail.  The fix is to wipe the cache and reclone fresh.
        """
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / ".git").mkdir()
        (cache / "old_file").write_text("stale")

        clone_calls = []

        async def pull_side_effect(path, branch):
            raise _branch_error(branch)

        async def clone_side_effect(url, branch, path):
            clone_calls.append(branch)
            # The stale cache must have been removed before this call
            assert not (path / "old_file").exists()

        with (
            patch("app.github_sync._git_pull", side_effect=pull_side_effect),
            patch("app.github_sync._git_clone", side_effect=clone_side_effect),
        ):
            await _ensure_repo("https://github.com/org/repo", "main", cache)

        assert clone_calls == ["master"]  # recloned on the fallback branch

    async def test_pull_transient_error_is_not_silently_retried(self, tmp_path):
        """A network/auth failure during pull on an existing cache must propagate."""
        from app.github_sync import _ensure_repo

        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / ".git").mkdir()

        async def pull_side_effect(path, branch):
            raise _transient_error()

        with patch("app.github_sync._git_pull", side_effect=pull_side_effect):
            with pytest.raises(subprocess.CalledProcessError):
                await _ensure_repo("https://github.com/org/repo", "main", cache)
