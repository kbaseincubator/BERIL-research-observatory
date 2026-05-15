"""Git synchronization helpers for the BERIL repository."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_API = "https://api.github.com"


class GitSyncError(RuntimeError):
    """Raised when the repository cannot be synchronized."""


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command in the repository and raise on failure."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GitSyncError(f"git {' '.join(args)} failed: {detail}")
    return result


def _github_repo_from_remote(repo_root: Path, remote: str) -> tuple[str, str]:
    """Return GitHub owner/repo from a git remote URL."""
    result = _run_git(repo_root, ["remote", "get-url", remote])
    remote_url = result.stdout.strip()
    match = re.match(
        r"(?:git@github\.com:|ssh://git@github\.com/|https://github\.com/)([^/]+)/(.+?)(?:\.git)?$",
        remote_url,
    )
    if not match:
        raise GitSyncError(f"{remote} is not a supported GitHub remote: {remote_url}")
    return match.group(1), match.group(2)


def _latest_release_tag(owner: str, repo: str) -> str | None:
    """Return the latest published GitHub release tag, or None if no release exists."""
    request = urllib.request.Request(
        f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "beril-cli",
        },
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise GitSyncError(f"GitHub release lookup failed: HTTP {exc.code}") from exc
    except (OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise GitSyncError(f"GitHub release lookup failed: {exc}") from exc

    tag_name = (payload.get("tag_name") or "").strip()
    if not tag_name:
        raise GitSyncError("GitHub latest release response did not include tag_name")
    return tag_name


def _checkout_remote_head_commit(repo_root: Path, remote: str) -> str:
    """Fetch and check out the remote HEAD commit."""
    _run_git(repo_root, ["fetch", remote])
    commit = _run_git(repo_root, ["rev-parse", "--verify", f"{remote}/HEAD"]).stdout.strip()
    _run_git(repo_root, ["checkout", "--detach", commit])
    return f"Checked out remote HEAD commit {commit[:12]}"


def sync_repo_to_latest_ref(repo_root: Path, remote: str = "origin") -> str:
    """Check out the latest GitHub release tag, or remote HEAD if no release exists.

    Parameters
    ----------
    repo_root
        Path to the BERIL git repository.
    remote
        Git remote to fetch refs from.

    Returns
    -------
    str
        Human-readable description of the checked out ref.
    """
    owner, repo = _github_repo_from_remote(repo_root, remote)
    release_tag = _latest_release_tag(owner, repo)
    if not release_tag:
        return _checkout_remote_head_commit(repo_root, remote)

    _run_git(repo_root, ["fetch", "--force", remote, f"refs/tags/{release_tag}:refs/tags/{release_tag}"])
    _run_git(repo_root, ["checkout", "--detach", release_tag])
    return f"Checked out release {release_tag}"
