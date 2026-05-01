#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openviking",
#     "pyyaml",
#     "rich",
# ]
# ///
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rich.console import Console
from rich.panel import Panel

from observatory_context.config import ContextConfig
from observatory_context.ingest import (
    ingest_all,
    ingest_changed,
    ingest_docs,
    ingest_project,
    resolve_project_dir,
)
from observatory_context.openviking_client import create_client
from observatory_context.progress import RichIngestObserver


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest BERIL context into OpenViking")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="Ingest all selected projects and docs")
    mode.add_argument("--changed", action="store_true", help="Ingest changed selected sources")
    mode.add_argument("--project", help="Ingest one project ID")
    mode.add_argument("--docs", action="store_true", help="Ingest selected central docs")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = ContextConfig.from_env()
    if args.project:
        try:
            resolve_project_dir(config, args.project)
        except (FileNotFoundError, ValueError) as exc:
            parser.error(str(exc))

    console = Console()
    started = time.monotonic()
    client = create_client(config)
    try:
        with RichIngestObserver(console=console) as observer:
            if args.all:
                ingest_all(config, client, observer=observer)
            elif args.changed:
                ingest_changed(config, client, observer=observer)
            elif args.project:
                ingest_project(config, client, args.project, observer=observer)
            elif args.docs:
                ingest_docs(config, client, observer=observer)
        elapsed = time.monotonic() - started
        is_healthy = bool(client.is_healthy()) if hasattr(client, "is_healthy") else True
        summary_style = "green" if is_healthy else "red"
        console.print(
            Panel.fit(
                f"Ingest finished in {elapsed:0.1f}s — server healthy: {is_healthy}",
                title="Done",
                border_style=summary_style,
            )
        )
    finally:
        close = getattr(client, "close", None)
        if close:
            close()


if __name__ == "__main__":
    main()
