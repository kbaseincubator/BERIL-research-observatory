"""beril start — launch a coding agent."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from beril_cli.config import get_default_agent, get_vertex_config
from beril_cli.detect import print_jupyterhub_path_hint

GITHUB_API_TIMEOUT_SECONDS = 10


def _sync_auth_token(env_path: Path) -> None:
    """Sync KBASE_AUTH_TOKEN from live environment into .env if available."""
    token = os.environ.get("KBASE_AUTH_TOKEN", "")
    if not token or not env_path.exists():
        return
    lines = env_path.read_text().splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith("KBASE_AUTH_TOKEN="):
            if line.strip() != f"KBASE_AUTH_TOKEN={token}":
                lines[i] = f"KBASE_AUTH_TOKEN={token}"
                updated = True
            break
    else:
        lines.append(f"KBASE_AUTH_TOKEN={token}")
        updated = True
    if updated:
        env_path.write_text("\n".join(lines) + "\n")
        print("Refreshed KBASE_AUTH_TOKEN in .env")


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md (repo marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def _github_repo_slug(repo_root: Path) -> str | None:
    """Return 'owner/repo' parsed from origin's URL, or None if it isn't a GitHub remote."""
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    url = result.stdout.strip()
    # Handles https://github.com/owner/repo(.git) and git@github.com:owner/repo(.git)
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"


def _latest_release_tag(repo_root: Path) -> str | None:
    """Return the tag of the latest published GitHub release, or None.

    Uses the public Releases API, which excludes drafts and prereleases. Raw git tags
    that were never published as a release (e.g. internal version bumps) are ignored.
    """
    slug = _github_repo_slug(repo_root)
    if not slug:
        return None
    url = f"https://api.github.com/repos/{slug}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=GITHUB_API_TIMEOUT_SECONDS) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Warning: could not query GitHub releases: {exc}", file=sys.stderr)
        return None
    tag = payload.get("tag_name")
    return tag if isinstance(tag, str) and tag else None


def _checkout_release(repo_root: Path, requested_version: str | None) -> int:
    """Fetch tags and check out the requested release (or the latest if unspecified).

    Returns 0 on success, non-zero on failure.
    """
    fetch = subprocess.run(
        ["git", "fetch", "--tags", "--quiet"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    if fetch.returncode != 0:
        print(
            f"Warning: git fetch --tags failed: {fetch.stderr.strip()}",
            file=sys.stderr,
        )

    if requested_version:
        tag = requested_version if requested_version.startswith("v") else f"v{requested_version}"
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
            cwd=repo_root, capture_output=True, text=True, check=False,
        )
        if verify.returncode != 0:
            print(f"Error: release '{tag}' not found.", file=sys.stderr)
            return 1
    else:
        tag = _latest_release_tag(repo_root)
        if not tag:
            print("Error: no release tags found in repository.", file=sys.stderr)
            return 1

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    target = subprocess.run(
        ["git", "rev-parse", f"{tag}^{{commit}}"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    if (
        head.returncode == 0
        and target.returncode == 0
        and head.stdout.strip() == target.stdout.strip()
    ):
        print(f"Already on release {tag}")
        return 0

    checkout = subprocess.run(
        ["git", "checkout", "--quiet", tag],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    if checkout.returncode != 0:
        print(
            f"Error: failed to check out release {tag}: {checkout.stderr.strip()}",
            file=sys.stderr,
        )
        print(
            "You may have local changes. Commit or stash them and try again.",
            file=sys.stderr,
        )
        return checkout.returncode
    print(f"Checked out release {tag}")
    return 0


def run_start(
    agent: str | None = None,
    extra_args: list[str] | None = None,
    skip_onboard: bool = False,
    version: str | None = None,
) -> int:
    """Launch the selected coding agent from the repo root."""
    agent = agent or get_default_agent()
    extra_args = extra_args or []

    binary = shutil.which(agent)
    if not binary:
        print(f"Error: '{agent}' is not installed or not on PATH.", file=sys.stderr)
        print("Install it and try again, or choose a different agent with --agent.", file=sys.stderr)
        return 1

    # Ensure we launch from the repo root so agent workflows have correct paths
    repo_root = _find_repo_root()
    if repo_root:
        os.chdir(repo_root)
    else:
        print("Error: BERIL repository not found. Run 'beril setup' first.", file=sys.stderr)
        return 1

    # Check out the requested release (or the latest published tag by default).
    rc = _checkout_release(repo_root, version)
    if rc != 0:
        return rc

    # Refresh KBASE_AUTH_TOKEN in .env from live environment (tokens expire)
    _sync_auth_token(repo_root / ".env")

    # Auto-run the onboarding skill unless skipped or the user already passed a prompt
    if not skip_onboard and not extra_args:
        extra_args = ["/berdl_start"]

    # Configure Google Vertex if enabled (shared BERIL Anthropic key)
    if agent == "claude":
        vertex = get_vertex_config()
        if vertex.get("enabled"):
            creds = vertex.get("credentials_file", "")
            if creds and Path(creds).exists():
                os.environ["CLAUDE_CODE_USE_VERTEX"] = "1"
                os.environ["CLOUD_ML_REGION"] = vertex.get("region", "global")
                os.environ["ANTHROPIC_VERTEX_PROJECT_ID"] = vertex.get("project_id", "")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds
                os.environ["VERTEX_REGION_CLAUDE_HAIKU_4_5"] = "us-east5"
                os.environ["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = "claude-haiku-4-5@20251001"
                print("Using BERIL Anthropic key (Google Vertex)")
            else:
                print(
                    "Warning: Vertex enabled but credentials file not found. "
                    "Falling back to personal API key.",
                    file=sys.stderr,
                )

    # Default to Opus model for Claude
    if agent == "claude" and "--model" not in extra_args:
        extra_args = ["--model", "opus", *extra_args]

    print(f"Launching {agent}...")
    print_jupyterhub_path_hint(repo_root)
    # Replace the current process with the agent
    os.execvp(binary, [agent, *extra_args])

    # execvp doesn't return on success; this is only reached on failure
    return 1  # pragma: no cover
