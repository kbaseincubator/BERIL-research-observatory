"""Git-based data synchronization module.

Handles cloning and pulling data from a Git repository.
"""

import asyncio
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Global lock to prevent concurrent git operations
_git_lock = asyncio.Lock()


async def ensure_repo_cloned(repo_url: str, branch: str, local_path: Path) -> None:
    """
    Ensure the git repository is cloned and up to date.

    Args:
        repo_url: Git repository URL
        branch: Branch to checkout
        local_path: Local path where repo should be cloned

    Raises:
        subprocess.CalledProcessError: If git operations fail
    """
    async with _git_lock:
        if local_path.exists() and (local_path / ".git").exists():
            logger.info(f"Repository exists at {local_path}, pulling latest changes")
            await _git_pull(local_path, branch)
        else:
            logger.info(f"Cloning repository from {repo_url} to {local_path}")
            await _git_clone(repo_url, branch, local_path)


async def pull_latest(local_path: Path, branch: str) -> None:
    """
    Pull the latest changes from the remote repository.

    Args:
        local_path: Local path to the repository
        branch: Branch to pull

    Raises:
        subprocess.CalledProcessError: If git pull fails
    """
    async with _git_lock:
        logger.info(f"Pulling latest changes for branch {branch}")
        await _git_pull(local_path, branch)


async def _git_clone(repo_url: str, branch: str, local_path: Path) -> None:
    """Shallow clone a single branch."""
    # Create parent directory if it doesn't exist
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Shallow clone with single branch
    cmd = [
        "git",
        "clone",
        "--depth", "1",
        "--single-branch",
        "--branch", branch,
        repo_url,
        str(local_path),
    ]

    logger.debug(f"Running: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        logger.error(f"Git clone failed: {error_msg}")
        raise subprocess.CalledProcessError(
            process.returncode, cmd, stdout, stderr
        )

    logger.info(f"Repository cloned successfully to {local_path}")


async def _git_pull(local_path: Path, branch: str) -> None:
    """Pull latest changes from remote."""
    # Reset any local changes
    reset_cmd = ["git", "-C", str(local_path), "reset", "--hard", f"origin/{branch}"]
    logger.debug(f"Running: {' '.join(reset_cmd)}")

    process = await asyncio.create_subprocess_exec(
        *reset_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()

    # Pull latest changes
    pull_cmd = ["git", "-C", str(local_path), "pull", "origin", branch]
    logger.debug(f"Running: {' '.join(pull_cmd)}")

    process = await asyncio.create_subprocess_exec(
        *pull_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        logger.error(f"Git pull failed: {error_msg}")
        raise subprocess.CalledProcessError(
            process.returncode, pull_cmd, stdout, stderr
        )

    logger.info("Repository updated successfully")