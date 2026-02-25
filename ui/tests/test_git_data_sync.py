"""Unit tests for app.git_data_sync."""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio

import pytest

from app.git_data_sync import ensure_repo_cloned, pull_latest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_process(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
    """Create a mock asyncio subprocess."""
    proc = AsyncMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    return proc


# ---------------------------------------------------------------------------
# ensure_repo_cloned
# ---------------------------------------------------------------------------


class TestEnsureRepoCloned:
    @pytest.mark.asyncio
    async def test_clones_when_not_exists(self, tmp_path):
        local_path = tmp_path / "repo"  # does not exist yet

        with patch("app.git_data_sync._git_clone", new_callable=AsyncMock) as mock_clone, \
             patch("app.git_data_sync._git_pull", new_callable=AsyncMock) as mock_pull:
            await ensure_repo_cloned("https://example.com/repo.git", "main", local_path)

        mock_clone.assert_called_once_with("https://example.com/repo.git", "main", local_path)
        mock_pull.assert_not_called()

    @pytest.mark.asyncio
    async def test_pulls_when_exists(self, tmp_path):
        local_path = tmp_path / "repo"
        local_path.mkdir()
        (local_path / ".git").mkdir()

        with patch("app.git_data_sync._git_clone", new_callable=AsyncMock) as mock_clone, \
             patch("app.git_data_sync._git_pull", new_callable=AsyncMock) as mock_pull:
            await ensure_repo_cloned("https://example.com/repo.git", "main", local_path)

        mock_pull.assert_called_once_with(local_path, "main")
        mock_clone.assert_not_called()

    @pytest.mark.asyncio
    async def test_clones_when_dir_exists_but_no_git(self, tmp_path):
        local_path = tmp_path / "repo"
        local_path.mkdir()  # exists but no .git subdir

        with patch("app.git_data_sync._git_clone", new_callable=AsyncMock) as mock_clone, \
             patch("app.git_data_sync._git_pull", new_callable=AsyncMock) as mock_pull:
            await ensure_repo_cloned("https://example.com/repo.git", "main", local_path)

        mock_clone.assert_called_once()
        mock_pull.assert_not_called()


# ---------------------------------------------------------------------------
# pull_latest
# ---------------------------------------------------------------------------


class TestPullLatest:
    @pytest.mark.asyncio
    async def test_delegates_to_git_pull(self, tmp_path):
        local_path = tmp_path / "repo"

        with patch("app.git_data_sync._git_pull", new_callable=AsyncMock) as mock_pull:
            await pull_latest(local_path, "data-cache")

        mock_pull.assert_called_once_with(local_path, "data-cache")


# ---------------------------------------------------------------------------
# _git_clone
# ---------------------------------------------------------------------------


class TestGitClone:
    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        from app.git_data_sync import _git_clone

        local_path = tmp_path / "repo"
        success_proc = _make_process(returncode=0)

        with patch("asyncio.create_subprocess_exec", return_value=success_proc):
            await _git_clone("https://example.com/repo.git", "main", local_path)

        # Parent directory should have been created
        assert local_path.parent.exists()

    @pytest.mark.asyncio
    async def test_raises_on_failure(self, tmp_path):
        from app.git_data_sync import _git_clone

        local_path = tmp_path / "repo"
        fail_proc = _make_process(returncode=1, stderr=b"fatal: repo not found")

        with patch("asyncio.create_subprocess_exec", return_value=fail_proc):
            with pytest.raises(subprocess.CalledProcessError):
                await _git_clone("https://example.com/bad.git", "main", local_path)

    @pytest.mark.asyncio
    async def test_uses_shallow_clone_flags(self, tmp_path):
        from app.git_data_sync import _git_clone

        local_path = tmp_path / "repo"
        success_proc = _make_process(returncode=0)

        with patch("asyncio.create_subprocess_exec", return_value=success_proc) as mock_exec:
            await _git_clone("https://example.com/repo.git", "main", local_path)

        args = mock_exec.call_args[0]
        assert "--depth" in args
        assert "1" in args
        assert "--single-branch" in args
        assert "--branch" in args
        assert "main" in args


# ---------------------------------------------------------------------------
# _git_pull
# ---------------------------------------------------------------------------


class TestGitPull:
    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        from app.git_data_sync import _git_pull

        local_path = tmp_path / "repo"
        success_proc = _make_process(returncode=0)

        with patch("asyncio.create_subprocess_exec", return_value=success_proc):
            await _git_pull(local_path, "main")

    @pytest.mark.asyncio
    async def test_raises_on_pull_failure(self, tmp_path):
        from app.git_data_sync import _git_pull

        local_path = tmp_path / "repo"
        # First call (reset) succeeds, second call (pull) fails
        success_proc = _make_process(returncode=0)
        fail_proc = _make_process(returncode=1, stderr=b"error: pull failed")

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return success_proc if call_count == 1 else fail_proc

        with patch("asyncio.create_subprocess_exec", side_effect=side_effect):
            with pytest.raises(subprocess.CalledProcessError):
                await _git_pull(local_path, "main")

    @pytest.mark.asyncio
    async def test_resets_before_pull(self, tmp_path):
        from app.git_data_sync import _git_pull

        local_path = tmp_path / "repo"
        success_proc = _make_process(returncode=0)
        calls = []

        async def capture(*args, **kwargs):
            calls.append(args)
            return success_proc

        with patch("asyncio.create_subprocess_exec", side_effect=capture):
            await _git_pull(local_path, "main")

        # Should have been called twice: reset + pull
        assert len(calls) == 2
        # First call should be a reset
        first_cmd = calls[0]
        assert "reset" in first_cmd
        assert "--hard" in first_cmd
        # Second call should be a pull
        second_cmd = calls[1]
        assert "pull" in second_cmd
