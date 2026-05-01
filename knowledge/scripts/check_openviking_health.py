#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openviking",
#     "pyyaml",
#     "rich",
# ]
# ///
"""Inspect OpenViking server health: queues, locks, models, errors.

Usage:
    check_openviking_health.py                # one-shot dashboard, exit 0/1
    check_openviking_health.py --watch 2      # refresh every 2s until Ctrl+C
    check_openviking_health.py --json         # raw JSON dump
    check_openviking_health.py --url http://host:1933
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rich.console import Console, Group
from rich.live import Live
from rich.rule import Rule
from rich.text import Text

from observatory_context.config import ContextConfig
from observatory_context.openviking_client import create_client
from observatory_context.progress import render_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", type=float, metavar="SECONDS", help="Refresh interval; omit for one-shot")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Print raw status as JSON and exit")
    parser.add_argument("--url", help="Override OPENVIKING_URL")
    return parser


def _config_for(args: argparse.Namespace) -> ContextConfig:
    config = ContextConfig.from_env()
    if args.url:
        return ContextConfig(
            repo_root=config.repo_root,
            openviking_url=args.url,
            openviking_api_key=config.openviking_api_key,
        )
    return config


def _status_is_healthy(status: dict[str, Any]) -> bool:
    if not status.get("is_healthy"):
        return False
    if status.get("errors"):
        return False
    for component in (status.get("components") or {}).values():
        if isinstance(component, dict) and component.get("has_errors"):
            return False
    return True


def _dashboard(url: str, status: dict[str, Any]) -> Group:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = Rule(Text(f"OpenViking @ {url}    {timestamp}", style="bold"))
    return Group(header, render_status(status))


def _run_oneshot(console: Console, client: Any, url: str) -> int:
    status = client.get_status()
    console.print(_dashboard(url, status))
    return 0 if _status_is_healthy(status) else 1


def _run_watch(console: Console, client: Any, url: str, interval: float) -> int:
    last_status: dict[str, Any] = {}
    try:
        with Live(console=console, refresh_per_second=max(1.0, 1.0 / interval), screen=False) as live:
            while True:
                last_status = client.get_status()
                live.update(_dashboard(url, last_status))
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[dim]Stopped.[/dim]")
    return 0 if _status_is_healthy(last_status) else 1


def main() -> int:
    args = build_parser().parse_args()
    if args.watch is not None and args.as_json:
        raise SystemExit("--watch and --json are mutually exclusive")

    config = _config_for(args)
    console = Console()
    client = create_client(config)
    try:
        if args.as_json:
            print(json.dumps(client.get_status(), indent=2, default=str))
            return 0
        if args.watch is not None and args.watch > 0:
            return _run_watch(console, client, config.openviking_url, args.watch)
        return _run_oneshot(console, client, config.openviking_url)
    finally:
        close = getattr(client, "close", None)
        if close:
            close()


if __name__ == "__main__":
    raise SystemExit(main())
