"""beril start — launch a coding agent."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from beril_cli.config import get_default_agent


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md (repo marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def run_start(agent: str | None = None, extra_args: list[str] | None = None) -> int:
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
        print("Warning: could not find repo root (PROJECT.md). Launching from current directory.", file=sys.stderr)

    print(f"Launching {agent}...")
    # Replace the current process with the agent
    os.execvp(binary, [agent, *extra_args])

    # execvp doesn't return on success; this is only reached on failure
    return 1  # pragma: no cover
