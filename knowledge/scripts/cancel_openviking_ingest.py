#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
# ]
# ///
"""Cancel pending OpenViking ingest work and clear locks.

OpenViking has no `cancel`/`drain` API, so cancelling means stopping the server
and removing the on-disk queue (and optionally the entire workspace).

Usage:
    cancel_openviking_ingest.py                  # stop server, drop queue.db, purge temp uploads
    cancel_openviking_ingest.py --purge-workspace  # also delete the whole workspace + state manifest
    cancel_openviking_ingest.py --yes            # skip the confirmation prompt
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OV_CONF = REPO_ROOT / "knowledge" / "openviking" / "ov.conf"
DEFAULT_MANIFEST = REPO_ROOT / "knowledge" / "state" / "context_manifest.json"
SERVER_PROCESS_PATTERN = "openviking-server"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ov-conf",
        type=Path,
        default=DEFAULT_OV_CONF,
        help=f"Path to ov.conf (default: {DEFAULT_OV_CONF.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--purge-workspace",
        action="store_true",
        help="Delete the entire workspace dir AND the ingest state manifest (destructive — wipes all ingested data).",
    )
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    return parser


def _workspace_path(ov_conf: Path) -> Path:
    config = json.loads(ov_conf.read_text(encoding="utf-8"))
    workspace = Path(config["storage"]["workspace"])
    return workspace if workspace.is_absolute() else (REPO_ROOT / workspace).resolve()


def _stop_server(console: Console) -> None:
    pids = _find_server_pids()
    if not pids:
        console.print("[dim]No openviking-server process running.[/dim]")
        return
    console.print(f"Stopping openviking-server (PIDs: {', '.join(str(p) for p in pids)})…")
    for pid in pids:
        os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        time.sleep(0.25)
        if not _find_server_pids():
            console.print("[green]Server stopped.[/green]")
            return
    for pid in _find_server_pids():
        console.print(f"[yellow]PID {pid} still alive — sending SIGKILL.[/yellow]")
        os.kill(pid, signal.SIGKILL)


def _find_server_pids() -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", SERVER_PROCESS_PATTERN], capture_output=True, text=True, check=False
    )
    return [int(line) for line in result.stdout.split() if line.strip().isdigit()]


def _clear_queue(workspace: Path, console: Console) -> None:
    queue_dir = workspace / "_system" / "queue"
    removed = 0
    for db_file in queue_dir.glob("queue.db*"):
        db_file.unlink()
        removed += 1
    console.print(f"Removed {removed} queue file(s) from {queue_dir.relative_to(REPO_ROOT)}.")


def _clear_temp_uploads(workspace: Path, console: Console) -> None:
    upload_dir = workspace / "temp" / "upload"
    if not upload_dir.is_dir():
        return
    count = sum(1 for _ in upload_dir.iterdir())
    if count == 0:
        return
    shutil.rmtree(upload_dir)
    upload_dir.mkdir(parents=True)
    console.print(f"Cleared {count} orphan upload(s) from {upload_dir.relative_to(REPO_ROOT)}.")


def _purge_workspace(workspace: Path, console: Console) -> None:
    if workspace.is_dir():
        shutil.rmtree(workspace)
        console.print(f"[red]Deleted workspace {workspace.relative_to(REPO_ROOT)}.[/red]")
    if DEFAULT_MANIFEST.is_file():
        DEFAULT_MANIFEST.unlink()
        console.print(f"[red]Deleted manifest {DEFAULT_MANIFEST.relative_to(REPO_ROOT)}.[/red]")


def _confirm(console: Console, message: str) -> bool:
    console.print(f"[yellow]{message}[/yellow]")
    reply = input("Type 'yes' to continue: ").strip().lower()
    return reply == "yes"


def main() -> int:
    args = build_parser().parse_args()
    console = Console()
    workspace = _workspace_path(args.ov_conf)

    if args.purge_workspace:
        action = f"DELETE the workspace at {workspace} and clear the state manifest"
    else:
        action = "stop the server and clear the queue + temp uploads (resources in viking/ and vectordb/ are preserved)"

    console.print(Panel.fit(f"About to {action}.", title="cancel_openviking_ingest", border_style="yellow"))
    if not args.yes and not _confirm(console, "This will stop in-flight OpenViking work."):
        console.print("[dim]Aborted.[/dim]")
        return 1

    _stop_server(console)
    if args.purge_workspace:
        _purge_workspace(workspace, console)
    else:
        _clear_queue(workspace, console)
        _clear_temp_uploads(workspace, console)

    console.print(
        Panel.fit(
            "Restart the server with:\n"
            "  uv run --group knowledge openviking-server --config knowledge/openviking/ov.conf",
            title="Next step",
            border_style="green",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
