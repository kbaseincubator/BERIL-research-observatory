"""beril start — launch a coding agent."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from beril_cli.config import get_default_agent


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


def run_start(
    agent: str | None = None,
    extra_args: list[str] | None = None,
    skip_onboard: bool = False,
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

    # Pull latest changes (repo is under active development)
    result = subprocess.run(
        ["git", "pull", "--ff-only"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0 and "Already up to date" not in result.stdout:
        print(f"Updated: {result.stdout.strip()}")
    elif result.returncode != 0:
        print("Warning: git pull failed (you may have local changes). Continuing anyway.", file=sys.stderr)

    # Refresh KBASE_AUTH_TOKEN in .env from live environment (tokens expire)
    _sync_auth_token(repo_root / ".env")

    # Auto-run the onboarding skill unless skipped or the user already passed a prompt
    if not skip_onboard and not extra_args:
        extra_args = ["/berdl_start"]

    print(f"Launching {agent}...")
    # Replace the current process with the agent
    os.execvp(binary, [agent, *extra_args])

    # execvp doesn't return on success; this is only reached on failure
    return 1  # pragma: no cover
