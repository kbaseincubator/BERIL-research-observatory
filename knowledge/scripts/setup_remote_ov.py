#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "openviking",
# ]
# ///
"""One-time setup for the remote OpenViking knowledge server.

Exchanges your BERIL login (the ``beril_session`` browser cookie) for an
OpenViking API key and writes ``OPENVIKING_URL`` + ``OPENVIKING_API_KEY`` into
``.env``, so ``knowledge_query.py`` can talk to the remote server.

Usage:
    uv run knowledge/scripts/setup_remote_ov.py --cookie '<beril_session value>'
    uv run knowledge/scripts/setup_remote_ov.py --cookie '...' --server https://host
    uv run knowledge/scripts/setup_remote_ov.py --cookie '...' --regenerate
    uv run knowledge/scripts/setup_remote_ov.py --cookie '...' --print-only

The cookie may also come from ``$BERIL_SESSION`` or an interactive prompt.
See docs/remote-openviking-setup.md for how to copy the cookie.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from observatory_context.config import ContextConfig
from observatory_context.openviking_client import diagnose, format_diagnosis

# beril-dev is the current (temporary) dev host. When the OV server moves to
# production, change this one line or pass --server.
DEFAULT_SERVER = "https://beril-dev.kbase.us"
_TIMEOUT = httpx.Timeout(15.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a remote OpenViking API key and write it into .env.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cookie", help="Your 'beril_session' cookie value (or set $BERIL_SESSION)."
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"BERIL server base URL (default: {DEFAULT_SERVER}).",
    )
    parser.add_argument(
        "--env-file", default=None, help="Path to .env (default: repo-root .env)."
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Mint a fresh key (invalidates the old one).",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the env lines instead of writing .env.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the post-write connectivity check.",
    )
    return parser


def _resolve_cookie(arg: str | None) -> str:
    cookie = arg or os.environ.get("BERIL_SESSION")
    if not cookie and sys.stdin.isatty():
        cookie = input("Paste your beril_session cookie value: ").strip()
    cookie = (cookie or "").strip()
    # tolerate a pasted "beril_session=..." / "beril_session: ..." prefix
    cookie = re.sub(r"^\s*beril_session\s*[=:]\s*", "", cookie)
    if not cookie:
        raise SystemExit(
            "No cookie provided. Pass --cookie '<value>', set $BERIL_SESSION, or "
            "run interactively.\nSee docs/remote-openviking-setup.md for how to "
            "copy the beril_session cookie."
        )
    return cookie


def _headers(cookie: str) -> dict[str, str]:
    return {"Cookie": f"beril_session={cookie}", "Accept": "application/json"}


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text.strip()[:200] or f"HTTP {response.status_code}"
    if isinstance(body, dict) and body.get("detail"):
        return str(body["detail"])
    return f"HTTP {response.status_code}"


def _guard(response: httpx.Response, *, action: str) -> None:
    if response.is_success:
        return
    if response.status_code == 401:
        raise SystemExit(
            "Your beril_session cookie is missing, invalid, or expired (HTTP 401).\n"
            f"Log in again, re-copy the cookie, and retry. (while trying to {action})"
        )
    raise SystemExit(f"Failed to {action}: {_detail(response)}")


def _fetch_user_key(server: str, cookie: str, regenerate: bool) -> str:
    base = server.rstrip("/")
    with httpx.Client(timeout=_TIMEOUT, headers=_headers(cookie)) as client:
        if regenerate:
            resp = client.post(f"{base}/api/ov/user/regenerate")
            _guard(resp, action="regenerate your OpenViking key")
        else:
            resp = client.post(f"{base}/api/ov/user")
            if resp.status_code == 409:
                raise SystemExit(
                    "OpenViking already has a user for your ORCiD, but BERIL holds "
                    "no key for it. Re-run with --regenerate to mint a fresh key:\n"
                    "  uv run knowledge/scripts/setup_remote_ov.py "
                    "--cookie '<cookie>' --regenerate"
                )
            _guard(resp, action="create your OpenViking account")
        creds = client.get(f"{base}/api/ov/credentials")
        _guard(creds, action="fetch your OpenViking credentials")
        body = creds.json()
    key = (body or {}).get("user_key")
    if not key:
        raise SystemExit(
            "BERIL did not return a user_key. Try --regenerate, or contact an admin."
        )
    return key


def render_env(existing: str, updates: dict[str, str]) -> str:
    """Upsert ``KEY=value`` lines: replace in place, preserve everything else,
    append keys not already present. Idempotent."""
    seen: set[str] = set()
    out: list[str] = []
    for line in existing.splitlines():
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        key = match.group(1) if match else None
        if key in updates:
            if key not in seen:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
            continue  # drop stale/duplicate assignments
        out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    return "\n".join(out).rstrip("\n") + "\n"


def _resolve_env_path(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    return Path(__file__).resolve().parents[2] / ".env"


def _mask(key: str) -> str:
    return f"…{key[-4:]}" if len(key) > 4 else "set"


def main() -> int:
    args = build_parser().parse_args()
    cookie = _resolve_cookie(args.cookie)
    server = args.server.rstrip("/")
    ov_url = f"{server}/ov"

    key = _fetch_user_key(server, cookie, args.regenerate)
    updates = {"OPENVIKING_URL": ov_url, "OPENVIKING_API_KEY": key}

    if args.print_only:
        print("# Add these to your .env:")
        for name, value in updates.items():
            print(f"{name}={value}")
        return 0

    env_path = _resolve_env_path(args.env_file)
    existing = env_path.read_text() if env_path.exists() else ""
    env_path.write_text(render_env(existing, updates))
    print(
        f"Wrote OPENVIKING_URL={ov_url} and OPENVIKING_API_KEY ({_mask(key)}) "
        f"to {env_path}"
    )

    if not args.no_verify:
        repo_root = Path(__file__).resolve().parents[2]
        config = ContextConfig(
            repo_root=repo_root, openviking_url=ov_url, openviking_api_key=key
        )
        print()
        print(format_diagnosis(diagnose(config)))

    print()
    print(
        'Next: uv run --env-file .env knowledge/scripts/knowledge_query.py '
        'find "your query"'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
