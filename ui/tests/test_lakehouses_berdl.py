"""Unit tests for BERDLLakehouse.

We don't talk to a real MinIO. ``aioboto3.Session().client(...)`` is mocked
at the class boundary: we replace ``BERDLLakehouse._session`` with a stub
whose ``.client()`` returns an async-context-managed mock S3 client whose
behaviour each test prescribes. ``RepositoryParser`` is also mocked so we
exercise the sync plumbing without needing a real project tree on disk.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.lakehouses import get_lakehouse_source
from app.lakehouses.base import SyncResult
from app.lakehouses.berdl import BERDLLakehouse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(tmp_path: Path, **overrides) -> Settings:
    """Build Settings pinned to a tmp cache root with placeholder creds."""
    defaults = {
        "lakehouse_source": "berdl",
        "lakehouse_cache_dir": tmp_path / "cache",
        "force_local_data": False,
        "data_repo_url": None,
        "berdl_minio_endpoint": "https://minio.example.invalid",
        "berdl_minio_access_key": "test-access",
        "berdl_minio_secret_key": "test-secret",
        "berdl_minio_bucket": "cdm-lake",
        "berdl_projects_prefix": "tenant-general-warehouse/microbialdiscoveryforge/projects/",
        "berdl_https_proxy": None,
        # Pin repo_dir to a tmp tree with the local subdirs the parser needs;
        # individual tests can override or pre-create as needed.
        "repo_dir": tmp_path / "repo",
    }
    defaults.update(overrides)
    s = Settings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_repo_dir(tmp_path: Path) -> Path:
    """Create the local subdirs BERDLLakehouse symlinks into the cache root."""
    repo = tmp_path / "repo"
    for name in ("docs", "atlas", "ui", ".claude"):
        (repo / name).mkdir(parents=True, exist_ok=True)
    return repo


def _mock_s3_client(
    pages: list[list[dict]] | None = None,
    download_side_effect=None,
) -> tuple[MagicMock, MagicMock]:
    """Build a stand-in for the aioboto3 S3 client.

    ``pages`` mirrors what ``list_objects_v2`` paginator yields — each page is
    a list of {"Key": "..."} dicts. Returns (s3_client_mock, paginator_mock)
    so callers can inspect calls.
    """
    pages = pages if pages is not None else [[]]

    paginator = MagicMock()

    async def _paginate(**_kwargs):
        for page in pages:
            yield {"Contents": page}

    paginator.paginate = _paginate

    client = MagicMock()
    client.get_paginator = MagicMock(return_value=paginator)

    async def _download_file(bucket: str, key: str, dest: str) -> None:
        # Write a minimal file so callers can assert it appeared on disk.
        Path(dest).write_text(f"content of {key}")
        if download_side_effect is not None:
            await download_side_effect(bucket, key, dest)

    client.download_file = AsyncMock(side_effect=_download_file)

    return client, paginator


def _patch_session(s3_client: MagicMock) -> MagicMock:
    """Build an aioboto3.Session stub whose .client() returns ``s3_client``
    as an async context manager. Use ``provider._session = result`` to apply."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=s3_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.client = MagicMock(return_value=ctx)
    return session


def _patch_parser(repo_data: MagicMock | None = None) -> patch:
    """Patch RepositoryParser at the import site inside berdl.py."""
    parser_instance = MagicMock()
    parser_instance.parse_all = MagicMock(return_value=repo_data or MagicMock(last_updated=None))
    parser_class = MagicMock(return_value=parser_instance)
    return patch("app.lakehouses.berdl.RepositoryParser", parser_class)


# ---------------------------------------------------------------------------
# Construction & registry
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_registry_resolves_berdl(self, tmp_path: Path):
        source = get_lakehouse_source(_settings(tmp_path))
        assert isinstance(source, BERDLLakehouse)
        assert source.name == "berdl"

    def test_raises_without_access_key(self, tmp_path: Path):
        with pytest.raises(ValueError, match="berdl_minio_access_key"):
            BERDLLakehouse(_settings(tmp_path, berdl_minio_access_key=None))

    def test_raises_without_secret_key(self, tmp_path: Path):
        with pytest.raises(ValueError, match="berdl_minio_secret_key"):
            BERDLLakehouse(_settings(tmp_path, berdl_minio_secret_key=None))


# ---------------------------------------------------------------------------
# sync() — happy path
# ---------------------------------------------------------------------------


class TestSyncHappyPath:
    @pytest.mark.asyncio
    async def test_downloads_and_parses(self, tmp_path: Path):
        _make_repo_dir(tmp_path)
        prefix = "tenant-general-warehouse/microbialdiscoveryforge/projects/"
        s3, _ = _mock_s3_client(pages=[[
            {"Key": prefix + "alpha/README.md"},
            {"Key": prefix + "alpha/notebooks/x.ipynb"},
            {"Key": prefix + "beta/REPORT.md"},
        ]])

        repo_data = MagicMock(last_updated="2026-05-22T00:00:00")
        with _patch_parser(repo_data=repo_data):
            provider = BERDLLakehouse(_settings(tmp_path))
            provider._session = _patch_session(s3)
            result = await provider.sync()

        # Sync result.
        assert isinstance(result, SyncResult)
        assert result.source_name == "berdl"
        assert result.repo_data is repo_data
        assert result.last_updated == "2026-05-22T00:00:00"
        assert result.projects_dir == tmp_path / "cache" / "projects"

        # Files staged correctly into the live cache.
        assert (tmp_path / "cache" / "projects" / "alpha" / "README.md").read_text() \
            == f"content of {prefix}alpha/README.md"
        assert (tmp_path / "cache" / "projects" / "alpha" / "notebooks" / "x.ipynb").exists()
        assert (tmp_path / "cache" / "projects" / "beta" / "REPORT.md").exists()

        # Local subdirs symlinked into the cache root.
        for name in ("docs", "atlas", "ui", ".claude"):
            link = tmp_path / "cache" / name
            assert link.is_symlink()
            assert link.resolve() == (tmp_path / "repo" / name).resolve()

        # Staging dir cleaned up.
        staging_dirs = list((tmp_path / "cache").glob(".staging-*"))
        assert staging_dirs == []

    @pytest.mark.asyncio
    async def test_paginated_list(self, tmp_path: Path):
        """list_objects_v2 caps at 1000 per page; we must walk every page."""
        _make_repo_dir(tmp_path)
        prefix = "tenant-general-warehouse/microbialdiscoveryforge/projects/"
        page1 = [{"Key": prefix + f"p1/file{i:04d}.txt"} for i in range(3)]
        page2 = [{"Key": prefix + f"p2/file{i:04d}.txt"} for i in range(2)]
        s3, _ = _mock_s3_client(pages=[page1, page2])

        with _patch_parser():
            provider = BERDLLakehouse(_settings(tmp_path))
            provider._session = _patch_session(s3)
            await provider.sync()

        assert s3.download_file.await_count == 5

    @pytest.mark.asyncio
    async def test_skips_directory_markers(self, tmp_path: Path):
        """Keys ending in '/' are MinIO directory markers (zero-byte). Don't
        try to download them — they'd create a file at a folder path."""
        _make_repo_dir(tmp_path)
        prefix = "tenant-general-warehouse/microbialdiscoveryforge/projects/"
        s3, _ = _mock_s3_client(pages=[[
            {"Key": prefix + "alpha/"},
            {"Key": prefix + "alpha/data/"},
            {"Key": prefix + "alpha/README.md"},
        ]])

        with _patch_parser():
            provider = BERDLLakehouse(_settings(tmp_path))
            provider._session = _patch_session(s3)
            await provider.sync()

        assert s3.download_file.await_count == 1


# ---------------------------------------------------------------------------
# sync() — atomic swap
# ---------------------------------------------------------------------------


class TestAtomicSwap:
    @pytest.mark.asyncio
    async def test_replaces_existing_projects_dir(self, tmp_path: Path):
        """A second sync must wipe the previous projects/ contents."""
        _make_repo_dir(tmp_path)
        # Pre-populate a stale projects/ tree.
        (tmp_path / "cache" / "projects" / "stale_project").mkdir(parents=True)
        (tmp_path / "cache" / "projects" / "stale_project" / "old.txt").write_text("stale")

        prefix = "tenant-general-warehouse/microbialdiscoveryforge/projects/"
        s3, _ = _mock_s3_client(pages=[[{"Key": prefix + "fresh/README.md"}]])

        with _patch_parser():
            provider = BERDLLakehouse(_settings(tmp_path))
            provider._session = _patch_session(s3)
            await provider.sync()

        # Old project is gone.
        assert not (tmp_path / "cache" / "projects" / "stale_project").exists()
        # New project is present.
        assert (tmp_path / "cache" / "projects" / "fresh" / "README.md").exists()


# ---------------------------------------------------------------------------
# sync() — failure modes
# ---------------------------------------------------------------------------


class TestFailures:
    @pytest.mark.asyncio
    async def test_download_failure_cleans_up_staging(self, tmp_path: Path):
        """A failed download must not leave the cache half-updated or strewn
        with .staging-* directories."""
        _make_repo_dir(tmp_path)
        prefix = "tenant-general-warehouse/microbialdiscoveryforge/projects/"

        async def _boom(bucket, key, dest):
            raise RuntimeError("simulated network failure")

        s3, _ = _mock_s3_client(
            pages=[[{"Key": prefix + "alpha/x.txt"}]],
            download_side_effect=_boom,
        )

        # Pre-populate a previous successful sync so we can verify it survives.
        (tmp_path / "cache" / "projects" / "previous").mkdir(parents=True)
        (tmp_path / "cache" / "projects" / "previous" / "ok.txt").write_text("ok")

        with _patch_parser():
            provider = BERDLLakehouse(_settings(tmp_path))
            provider._session = _patch_session(s3)
            with pytest.raises(RuntimeError, match="simulated network failure"):
                await provider.sync()

        # Previous good state is intact.
        assert (tmp_path / "cache" / "projects" / "previous" / "ok.txt").read_text() == "ok"
        # No staging detritus left behind.
        assert list((tmp_path / "cache").glob(".staging-*")) == []


# ---------------------------------------------------------------------------
# Proxy configuration
# ---------------------------------------------------------------------------


class TestProxy:
    @pytest.mark.asyncio
    async def test_proxy_passed_to_client(self, tmp_path: Path):
        """When berdl_https_proxy is set, it must be threaded into the
        aioboto3 client config — dev MinIO access goes through pproxy."""
        _make_repo_dir(tmp_path)
        prefix = "tenant-general-warehouse/microbialdiscoveryforge/projects/"
        s3, _ = _mock_s3_client(pages=[[]])

        provider = BERDLLakehouse(_settings(
            tmp_path,
            berdl_https_proxy="http://127.0.0.1:8123",
        ))
        provider._session = _patch_session(s3)
        with _patch_parser():
            await provider.sync()

        # Inspect the kwargs passed to session.client to confirm config carried
        # the proxy. The session is a MagicMock so .client is a MagicMock too.
        provider._session.client.assert_called_once()
        kwargs = provider._session.client.call_args.kwargs
        assert kwargs["aws_access_key_id"] == "test-access"
        assert kwargs["aws_secret_access_key"] == "test-secret"
        assert kwargs["endpoint_url"] == "https://minio.example.invalid"
        # The config object is internal to aiobotocore; just verify one was
        # passed (the no-proxy case passes None).
        assert kwargs["config"] is not None

    @pytest.mark.asyncio
    async def test_no_proxy_passes_none_config(self, tmp_path: Path):
        _make_repo_dir(tmp_path)
        s3, _ = _mock_s3_client(pages=[[]])

        provider = BERDLLakehouse(_settings(tmp_path, berdl_https_proxy=None))
        provider._session = _patch_session(s3)
        with _patch_parser():
            await provider.sync()

        kwargs = provider._session.client.call_args.kwargs
        assert kwargs["config"] is None


# ---------------------------------------------------------------------------
# is_available — current placeholder behavior
# ---------------------------------------------------------------------------


class TestIsAvailable:
    @pytest.mark.asyncio
    async def test_returns_true(self, tmp_path: Path):
        """Today is_available is a placeholder; sync() failure is the real
        signal. When a real probe lands this test should be replaced."""
        provider = BERDLLakehouse(_settings(tmp_path))
        assert await provider.is_available() is True
