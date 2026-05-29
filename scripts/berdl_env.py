#!/usr/bin/env python3
"""BERDL environment-check entrypoint.

Single canonical helper that every BERDL skill calls as Step 0. Wraps the
underlying detect_berdl_environment.py with auto-recovery (start pproxy when
tunnels are up but pproxy isn't) and a structured Python API.

CLI:
    python scripts/berdl_env.py --check   # exit 0 if ready, 1 otherwise
    python scripts/berdl_env.py --json    # emit detection JSON to stdout

Python:
    from scripts.berdl_env import require_environment, BerdlEnvironmentError
    env = require_environment()  # raises if not ready
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import the underlying detector. The repo root must be on sys.path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.detect_berdl_environment import detect_environment  # noqa: E402


PPROXY_WAIT_SECONDS = 5
PPROXY_POLL_INTERVAL = 0.5


@dataclass
class BerdlEnvironment:
    location: str
    ready: bool
    checks: dict[str, Any]
    next_steps: list[str]


class BerdlEnvironmentError(RuntimeError):
    def __init__(self, message: str, next_steps: list[str] | None = None) -> None:
        super().__init__(message)
        self.next_steps = next_steps or []


def start_pproxy() -> bool:
    """Start pproxy via scripts/start_pproxy.sh. Returns True if it ends up listening."""
    script = _REPO_ROOT / "scripts" / "start_pproxy.sh"
    if not script.exists():
        return False
    try:
        subprocess.run(["bash", str(script)], check=False, timeout=10)
    except subprocess.TimeoutExpired:
        return False
    deadline = time.time() + PPROXY_WAIT_SECONDS
    while time.time() < deadline:
        result = subprocess.run(
            ["lsof", "-i", ":8123"], capture_output=True, text=True, check=False
        )
        if "LISTEN" in result.stdout:
            return True
        time.sleep(PPROXY_POLL_INTERVAL)
    return False


def _attempt_pproxy_recovery(result: dict[str, Any]) -> dict[str, Any]:
    """If pproxy is the only missing piece, try to start it and re-detect."""
    checks = result.get("checks", {})
    if (
        result.get("location") == "off-cluster"
        and not result.get("ready")
        and checks.get("ssh_tunnel_1337")
        and checks.get("ssh_tunnel_1338")
        and not checks.get("pproxy_8123")
    ):
        if start_pproxy():
            return detect_environment()
    return result


def check_cli() -> int:
    """`--check` mode: exit 0 if ready, 1 otherwise. Auto-recovers pproxy."""
    result = detect_environment()
    result = _attempt_pproxy_recovery(result)
    print(f"Location: {result['location']}")
    for step in result.get("next_steps", []):
        print(f"  {step}")
    return 0 if result.get("ready") else 1


def json_cli() -> int:
    """`--json` mode: emit detection result as JSON, exit 0 always."""
    result = detect_environment()
    result = _attempt_pproxy_recovery(result)
    print(json.dumps(result, indent=2))
    return 0


def require_environment() -> BerdlEnvironment:
    """Python API. Raises BerdlEnvironmentError if not ready."""
    result = detect_environment()
    result = _attempt_pproxy_recovery(result)
    env = BerdlEnvironment(
        location=result.get("location", "unknown"),
        ready=bool(result.get("ready")),
        checks=dict(result.get("checks", {})),
        next_steps=list(result.get("next_steps", [])),
    )
    if not env.ready:
        message = "BERDL environment is not ready: " + "; ".join(env.next_steps)
        raise BerdlEnvironmentError(message, next_steps=env.next_steps)
    return env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Exit 0 if ready, 1 otherwise.")
    group.add_argument("--json", action="store_true", help="Emit detection JSON.")
    args = parser.parse_args(argv)
    if args.json:
        return json_cli()
    return check_cli()


if __name__ == "__main__":
    raise SystemExit(main())
