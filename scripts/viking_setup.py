"""Validate and prepare the local OpenViking setup for this repository."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVER_CONFIG = {
    "host": "127.0.0.1",
    "port": 1933,
    "workers": 1,
    "cors_origins": ["*"],
}


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def _get_setting(env: dict[str, str], dotenv: dict[str, str], key: str) -> str | None:
    return env.get(key) or dotenv.get(key)


def _load_server_config(config_path: Path, example_path: Path) -> dict[str, Any]:
    for path in (config_path, example_path):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        server = payload.get("server")
        if isinstance(server, dict):
            return server
    return DEFAULT_SERVER_CONFIG.copy()


def _build_openviking_config(repo_root: Path, config_path: Path, example_path: Path) -> dict[str, Any]:
    env = dict(os.environ)
    dotenv = _read_dotenv(repo_root / ".env")

    provider = _get_setting(env, dotenv, "OPENVIKING_PROVIDER") or "openai"
    if provider != "openai":
        raise RuntimeError(
            "Only OPENVIKING_PROVIDER=openai is supported by this repo bootstrap. "
            "Set OPENAI_API_KEY in your shell or .env."
        )

    api_key = _get_setting(env, dotenv, "OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Set it in your shell or add it to .env, "
            "then rerun `uv run scripts/viking_setup.py --write-config`."
        )

    api_base = _get_setting(env, dotenv, "OPENAI_BASE_URL") or "https://api.openai.com/v1"
    embedding_model = (
        _get_setting(env, dotenv, "OPENVIKING_EMBEDDING_MODEL") or "text-embedding-3-large"
    )
    embedding_dimension = int(
        _get_setting(env, dotenv, "OPENVIKING_EMBEDDING_DIMENSION") or "3072"
    )
    vlm_model = _get_setting(env, dotenv, "OPENVIKING_VLM_MODEL") or "gpt-4o-mini"

    return {
        "server": _load_server_config(config_path, example_path),
        "embedding": {
            "dense": {
                "api_base": api_base,
                "api_key": api_key,
                "provider": provider,
                "dimension": embedding_dimension,
                "model": embedding_model,
            }
        },
        "vlm": {
            "api_base": api_base,
            "api_key": api_key,
            "provider": provider,
            "model": vlm_model,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the local OpenViking setup for this repository.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Write a runnable config/openviking/ov.conf using shell env or .env values.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    example_path = repo_root / "config" / "openviking" / "ov.conf.example"
    config_path = repo_root / "config" / "openviking" / "ov.conf"

    if not example_path.exists():
        print(f"FAIL: example config not found at {example_path}")
        return 1
    if args.write_config:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = _build_openviking_config(repo_root, config_path, example_path)
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
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
