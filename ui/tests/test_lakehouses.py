"""Tests for the lakehouse source abstraction.

The PR-1 surface is small: a protocol, a registry that picks the active source
by name, and a single ``GitLegacyLakehouse`` adapter that wraps the existing
git+pickle flow. These tests pin down

  - the registry picks the right implementation and rejects unknown names,
  - the legacy adapter dispatches into its three branches correctly
    (force_local_data, git-configured, neither),
  - the legacy adapter falls back to local parsing on git failure (preserving
    the previous behavior of ``initialize_data``),
  - ``sync()`` re-uses pull instead of clone on subsequent calls within the
    same process — needed so the webhook path stays cheap.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.lakehouses import LakehouseSource, SyncResult, get_lakehouse_source
from app.lakehouses.git_legacy import GitLegacyLakehouse


def _stub_repo_data(last_updated: datetime | None = None) -> MagicMock:
    repo_data = MagicMock()
    repo_data.last_updated = last_updated or datetime(2026, 1, 1)
    return repo_data


def _settings(**overrides) -> Settings:
    """Build a Settings instance with overrides applied as attributes.

    Settings is a pydantic BaseSettings model — we instantiate it (picking up
    .env defaults) and then patch attributes for the test, mirroring how the
    existing test_main.py fixtures handle Settings.

    Defaults the data-source-related flags to a "clean" state so tests are
    insulated from whatever lives in the developer's local .env (which
    typically sets ``BERIL_FORCE_LOCAL_DATA=True`` and a placeholder
    ``BERIL_DATA_REPO_URL``).
    """
    defaults = {
        "force_local_data": False,
        "data_repo_url": None,
        "lakehouse_source": "git",
    }
    defaults.update(overrides)
    s = Settings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_default_source_is_git_legacy(self):
        """An unconfigured deployment gets the legacy adapter — preserves
        existing behavior when this PR lands. Asserts on the pydantic field
        default directly so a developer .env can't mask a regression here."""
        assert Settings.model_fields["lakehouse_source"].default == "git"
        source = get_lakehouse_source(_settings())
        assert isinstance(source, GitLegacyLakehouse)
        assert source.name == "git"

    def test_explicit_git_selection(self):
        source = get_lakehouse_source(_settings(lakehouse_source="git"))
        assert isinstance(source, GitLegacyLakehouse)

    def test_unknown_source_raises(self):
        """A typo in the env var should fail loud, not silently downgrade."""
        with pytest.raises(ValueError, match="Unknown lakehouse source"):
            get_lakehouse_source(_settings(lakehouse_source="not-a-real-source"))

    def test_source_implements_protocol(self):
        """LakehouseSource is a Protocol with name/sync/is_available — the
        legacy adapter should satisfy isinstance via duck typing at runtime
        (Protocol with @runtime_checkable would be needed for isinstance, so
        we just spot-check the surface here)."""
        source: LakehouseSource = GitLegacyLakehouse(_settings())
        assert hasattr(source, "name")
        assert hasattr(source, "sync")
        assert hasattr(source, "is_available")


# ---------------------------------------------------------------------------
# GitLegacyLakehouse dispatch
# ---------------------------------------------------------------------------


class TestGitLegacyForceLocal:
    """force_local_data=True should bypass git entirely and parse repo_dir."""

    @pytest.mark.asyncio
    async def test_skips_git_and_parses_local(self):
        repo_data = _stub_repo_data()
        with (
            patch("app.lakehouses.git_legacy.load_repository_data", return_value=repo_data) as load_mock,
            patch("app.lakehouses.git_legacy.ensure_repo_cloned",
                  side_effect=AssertionError("must not clone when force_local_data")),
            patch("app.lakehouses.git_legacy.pull_latest",
                  side_effect=AssertionError("must not pull when force_local_data")),
        ):
            source = GitLegacyLakehouse(_settings(
                force_local_data=True,
                data_repo_url="https://example.com/repo.git",  # set, but ignored
            ))
            result = await source.sync()
        load_mock.assert_called_once_with(None)
        assert result.repo_data is repo_data
        assert result.source_name == "git"
        assert result.projects_dir.name == "projects"


class TestGitLegacyGitConfigured:
    """data_repo_url is set, force_local_data is False — clone, load pickle,
    return projects_dir under data_repo_path."""

    @pytest.mark.asyncio
    async def test_first_sync_clones(self, tmp_path: Path):
        repo_data = _stub_repo_data()
        with (
            patch("app.lakehouses.git_legacy.ensure_repo_cloned", new_callable=AsyncMock) as clone_mock,
            patch("app.lakehouses.git_legacy.pull_latest", new_callable=AsyncMock) as pull_mock,
            patch("app.lakehouses.git_legacy.load_repository_data", return_value=repo_data) as load_mock,
        ):
            source = GitLegacyLakehouse(_settings(
                data_repo_url="https://example.com/repo.git",
                data_repo_branch="data-cache",
                data_repo_path=tmp_path / "cache",
            ))
            result = await source.sync()

        clone_mock.assert_awaited_once_with(
            "https://example.com/repo.git", "data-cache", tmp_path / "cache",
        )
        pull_mock.assert_not_awaited()
        load_mock.assert_called_once_with(tmp_path / "cache" / "data_cache" / "data.pkl.gz")
        assert result.repo_data is repo_data
        assert result.projects_dir == tmp_path / "cache" / "projects"
        assert result.source_name == "git"

    @pytest.mark.asyncio
    async def test_subsequent_sync_pulls(self, tmp_path: Path):
        """The webhook path calls sync() repeatedly — after the first clone we
        should pull, not re-clone."""
        with (
            patch("app.lakehouses.git_legacy.ensure_repo_cloned", new_callable=AsyncMock) as clone_mock,
            patch("app.lakehouses.git_legacy.pull_latest", new_callable=AsyncMock) as pull_mock,
            patch("app.lakehouses.git_legacy.load_repository_data", return_value=_stub_repo_data()),
        ):
            source = GitLegacyLakehouse(_settings(
                data_repo_url="https://example.com/repo.git",
                data_repo_branch="data-cache",
                data_repo_path=tmp_path / "cache",
            ))
            await source.sync()  # clone
            await source.sync()  # pull
            await source.sync()  # pull

        assert clone_mock.await_count == 1
        assert pull_mock.await_count == 2
        pull_mock.assert_awaited_with(tmp_path / "cache", "data-cache")

    @pytest.mark.asyncio
    async def test_git_failure_falls_back_to_local(self, tmp_path: Path):
        """If git fails (network down, branch missing, etc.) the adapter must
        fall back to parsing repo_dir — matches the prior ``initialize_data``
        behavior. This is the resilience contract the rest of the app relies on."""
        repo_data = _stub_repo_data()
        with (
            patch("app.lakehouses.git_legacy.ensure_repo_cloned",
                  new_callable=AsyncMock, side_effect=RuntimeError("network down")),
            patch("app.lakehouses.git_legacy.load_repository_data", return_value=repo_data) as load_mock,
        ):
            source = GitLegacyLakehouse(_settings(
                data_repo_url="https://example.com/repo.git",
                data_repo_path=tmp_path / "cache",
            ))
            result = await source.sync()

        # Local fallback calls load_repository_data(None), not with the pickle path.
        load_mock.assert_called_once_with(None)
        assert result.repo_data is repo_data
        # projects_dir on the fallback path points at repo_dir/projects, not data_repo_path/projects.
        assert result.projects_dir.name == "projects"
        assert result.projects_dir != tmp_path / "cache" / "projects"


class TestGitLegacyUnconfigured:
    """No data_repo_url and not force_local_data — parse repo_dir directly."""

    @pytest.mark.asyncio
    async def test_parses_local_when_unconfigured(self):
        repo_data = _stub_repo_data()
        with (
            patch("app.lakehouses.git_legacy.load_repository_data", return_value=repo_data) as load_mock,
            patch("app.lakehouses.git_legacy.ensure_repo_cloned",
                  side_effect=AssertionError("must not clone when no url configured")),
        ):
            source = GitLegacyLakehouse(_settings(
                data_repo_url=None,
                force_local_data=False,
            ))
            result = await source.sync()
        load_mock.assert_called_once_with(None)
        assert result.repo_data is repo_data


# ---------------------------------------------------------------------------
# SyncResult shape
# ---------------------------------------------------------------------------


class TestSyncResultShape:
    @pytest.mark.asyncio
    async def test_last_updated_echoes_repo_data(self):
        repo_data = _stub_repo_data(last_updated=datetime(2026, 5, 1, 12, 0, 0))
        with patch("app.lakehouses.git_legacy.load_repository_data", return_value=repo_data):
            source = GitLegacyLakehouse(_settings(force_local_data=True))
            result = await source.sync()
        assert result.last_updated == datetime(2026, 5, 1, 12, 0, 0)

    @pytest.mark.asyncio
    async def test_is_available_returns_true(self):
        """The legacy adapter falls back to local parsing on any failure, so
        there is no meaningful unavailable state."""
        source = GitLegacyLakehouse(_settings())
        assert await source.is_available() is True


# ---------------------------------------------------------------------------
# Sync result is what initialize_data unpacks
# ---------------------------------------------------------------------------


class TestInitializeDataIntegration:
    """The startup hook (app.context.initialize_data) consumes ``SyncResult``
    and returns ``repo_data``. Pin the integration point so future protocol
    changes don't silently break startup."""

    @pytest.mark.asyncio
    async def test_initialize_data_uses_source_sync(self):
        from app.context import initialize_data

        repo_data = _stub_repo_data()
        stub_source = MagicMock()
        stub_source.sync = AsyncMock(return_value=SyncResult(
            repo_data=repo_data,
            projects_dir=Path("/tmp/x"),
            source_name="stub",
            last_updated=repo_data.last_updated,
        ))

        with patch("app.context.get_lakehouse_source", return_value=stub_source):
            result = await initialize_data(_settings())

        assert result is repo_data
        stub_source.sync.assert_awaited_once()
