#!/usr/bin/env python3
"""Detect BERDL environment and check prerequisites.

Determines if running on-cluster (BERDL JupyterHub) or off-cluster (local machine).
Checks proxy status, KBASE_AUTH_TOKEN, venv setup, and provides actionable next steps.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


def test_connectivity(host: str, port: int, timeout: float = 2.0) -> bool:
    """Test if a host:port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error, OSError):
        return False


def check_port_listening(port: int) -> bool:
    """Check if a local port has something listening."""
    result = subprocess.run(
        ["lsof", "-i", f":{port}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return "LISTEN" in result.stdout


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load .env file and return key-value pairs."""
    env_vars = {}
    if not env_path.exists():
        return env_vars
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            env_vars[key] = value
    return env_vars


def save_to_env(env_path: Path, key: str, value: str) -> None:
    """Append or update a key in .env file."""
    existing = load_env_file(env_path)
    existing[key] = value

    with env_path.open("w") as f:
        for k, v in existing.items():
            # Quote values that might have special characters
            if any(c in v for c in [" ", "#", "$", "!", "&"]):
                f.write(f'{k}="{v}"\n')
            else:
                f.write(f"{k}={v}\n")


def detect_environment() -> dict[str, Any]:
    """Detect environment and return status report."""
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    venv_path = repo_root / ".venv-berdl"

    result: dict[str, Any] = {
        "location": "unknown",
        "ready": False,
        "checks": {},
        "next_steps": [],
    }

    # Test connectivity to BERDL Spark endpoint
    spark_reachable = test_connectivity("spark.berdl.kbase.us", 443, timeout=2.0)

    if spark_reachable:
        # On-cluster (BERDL JupyterHub)
        result["location"] = "on-cluster"
        result["checks"]["spark_direct"] = True

        # Check for KBASE_AUTH_TOKEN in environment
        token = os.getenv("KBASE_AUTH_TOKEN")
        if token:
            result["checks"]["kbase_token_env"] = True
            # Write to .env if not already there
            env_vars = load_env_file(env_file)
            if "KBASE_AUTH_TOKEN" not in env_vars:
                save_to_env(env_file, "KBASE_AUTH_TOKEN", token)
                result["next_steps"].append(
                    f"✅ Saved KBASE_AUTH_TOKEN to {env_file.relative_to(repo_root)}"
                )
            else:
                result["checks"]["kbase_token_env_file"] = True
            result["ready"] = True
            result["next_steps"].append(
                "✅ On BERDL cluster with direct access. Use scripts without --berdl-proxy."
            )
        else:
            result["checks"]["kbase_token_env"] = False
            result["next_steps"].append(
                "⚠️ KBASE_AUTH_TOKEN not found in environment. "
                "Get your token from https://narrative.kbase.us/#auth2/account "
                "and add it to .env"
            )
    else:
        # Off-cluster (local machine)
        result["location"] = "off-cluster"
        result["checks"]["spark_direct"] = False

        # Check .env for KBASE_AUTH_TOKEN
        env_vars = load_env_file(env_file)
        token_in_env = "KBASE_AUTH_TOKEN" in env_vars and bool(env_vars["KBASE_AUTH_TOKEN"])
        result["checks"]["kbase_token_env_file"] = token_in_env

        if not token_in_env:
            result["next_steps"].append(
                "❌ KBASE_AUTH_TOKEN missing from .env. "
                "Get your token from https://narrative.kbase.us/#auth2/account "
                "and add: KBASE_AUTH_TOKEN=\"your-token-here\""
            )

        # Check .venv-berdl
        venv_exists = venv_path.exists()
        result["checks"]["venv_berdl"] = venv_exists

        if not venv_exists:
            result["next_steps"].append(
                "❌ .venv-berdl not found. Run: bash scripts/bootstrap_client.sh"
            )

        # Check SSH tunnels
        tunnel_1337 = check_port_listening(1337)
        tunnel_1338 = check_port_listening(1338)
        result["checks"]["ssh_tunnel_1337"] = tunnel_1337
        result["checks"]["ssh_tunnel_1338"] = tunnel_1338

        if not tunnel_1337 or not tunnel_1338:
            missing = []
            if not tunnel_1337:
                missing.append("1337")
            if not tunnel_1338:
                missing.append("1338")
            result["next_steps"].append(
                f"❌ SSH tunnel(s) on port(s) {', '.join(missing)} not running. "
                "Start with: ssh -f -N -o ServerAliveInterval=60 -D <port> ac.<username>@login1.berkeley.kbase.us"
            )

        # Check pproxy
        pproxy_running = check_port_listening(8123)
        result["checks"]["pproxy_8123"] = pproxy_running

        if not pproxy_running:
            result["next_steps"].append(
                "❌ pproxy not running on port 8123. "
                "See .claude/skills/berdl-query/references/proxy-setup.md for startup instructions."
            )

        # Overall readiness
        result["ready"] = all([
            token_in_env,
            venv_exists,
            tunnel_1337,
            tunnel_1338,
            pproxy_running,
        ])

        if result["ready"]:
            result["next_steps"] = [
                "✅ Off-cluster environment fully configured. "
                "Use --berdl-proxy with all scripts."
            ]
        else:
            result["next_steps"].append(
                "\nFull setup guide: .claude/skills/berdl-query/references/proxy-setup.md"
            )

    return result


def main() -> int:
    """Run detection and print results."""
    result = detect_environment()
    print(json.dumps(result, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
