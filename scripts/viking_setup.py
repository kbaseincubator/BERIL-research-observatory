"""Validate and prepare the local OpenViking setup for this repository."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the local OpenViking setup for this repository.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument("--write-config", action="store_true", help="Copy the example config into config/openviking/ov.conf if missing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    example_path = repo_root / "config" / "openviking" / "ov.conf.example"
    config_path = repo_root / "config" / "openviking" / "ov.conf"

    if not example_path.exists():
        print(f"FAIL: example config not found at {example_path}")
        return 1
    if args.write_config and not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example_path, config_path)
    if not config_path.exists():
        print(f"FAIL: config not found at {config_path}")
        print("Run `uv run scripts/viking_setup.py --write-config` first.")
        return 1

    server_binary = shutil.which("openviking-server")
    if server_binary is None:
        print("FAIL: `openviking-server` is not installed in the current environment.")
        return 1

    expected_env = os.environ.get("OPENVIKING_CONFIG_FILE")
    print("PASS: local OpenViking prerequisites look valid.")
    print(f"Config: {config_path}")
    print(f"Server binary: {server_binary}")
    if expected_env == str(config_path):
        print("OPENVIKING_CONFIG_FILE is already set correctly.")
    else:
        print(f"Export: OPENVIKING_CONFIG_FILE={config_path}")
    print(f"Start: openviking-server --config {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
