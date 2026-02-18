#!/usr/bin/env python3
"""Resolve BERDL MinIO credentials from local env or BERDL remote context."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Get BERDL MinIO credentials.")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional dotenv file to load before reading environment variables.",
    )
    parser.add_argument(
        "--bootstrap-remote",
        action="store_true",
        help="Run berdl-remote login and spawn before reading remote env vars.",
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        help="Print output as shell exports instead of JSON.",
    )
    return parser.parse_args()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def parse_remote_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def resolve_from_local_env() -> dict[str, str] | None:
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    endpoint_url = os.getenv("MINIO_ENDPOINT_URL", "https://minio.berdl.kbase.us")
    if access_key and secret_key:
        return {
            "MINIO_ACCESS_KEY": access_key,
            "MINIO_SECRET_KEY": secret_key,
            "MINIO_ENDPOINT_URL": endpoint_url,
            "source": "local-env",
        }
    return None


def resolve_from_berdl_remote(bootstrap_remote: bool) -> dict[str, str] | None:
    if shutil.which("berdl-remote") is None:
        return None

    if bootstrap_remote:
        login_result = run(["berdl-remote", "login"])
        if login_result.returncode != 0:
            print(login_result.stderr.strip(), file=sys.stderr)
            return None
        spawn_result = run(["berdl-remote", "spawn"])
        if spawn_result.returncode != 0:
            print(spawn_result.stderr.strip(), file=sys.stderr)
            return None

    code = (
        "import json, os; "
        "print(json.dumps({"
        "'MINIO_ACCESS_KEY': os.getenv('MINIO_ACCESS_KEY'), "
        "'MINIO_SECRET_KEY': os.getenv('MINIO_SECRET_KEY'), "
        "'MINIO_ENDPOINT_URL': os.getenv('MINIO_ENDPOINT_URL', 'https://minio.berdl.kbase.us')"
        "}))"
    )
    result = run(["berdl-remote", "python", code])
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return None

    payload = parse_remote_json(result.stdout)
    if not payload:
        return None

    access_key = payload.get("MINIO_ACCESS_KEY")
    secret_key = payload.get("MINIO_SECRET_KEY")
    endpoint_url = payload.get("MINIO_ENDPOINT_URL") or "https://minio.berdl.kbase.us"
    if not access_key or not secret_key:
        return None

    return {
        "MINIO_ACCESS_KEY": access_key,
        "MINIO_SECRET_KEY": secret_key,
        "MINIO_ENDPOINT_URL": endpoint_url,
        "source": "berdl-remote",
    }


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))

    creds = resolve_from_local_env()
    if creds is None:
        creds = resolve_from_berdl_remote(args.bootstrap_remote)

    if creds is None:
        print(
            "Could not resolve MinIO credentials from local env or berdl-remote.",
            file=sys.stderr,
        )
        return 1

    if args.shell:
        print(f"export MINIO_ACCESS_KEY='{creds['MINIO_ACCESS_KEY']}'")
        print(f"export MINIO_SECRET_KEY='{creds['MINIO_SECRET_KEY']}'")
        print(f"export MINIO_ENDPOINT_URL='{creds['MINIO_ENDPOINT_URL']}'")
        print(f"# source={creds['source']}")
    else:
        print(json.dumps(creds, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
