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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from observatory_context.config import ContextConfig
from observatory_context.ingest import ingest_projects
from observatory_context.openviking_client import create_client
from observatory_context.progress import RichIngestObserver
from observatory_context.query import _field, _resources
from observatory_context.selection import project_target_uri
from observatory_context.smoke import latest_project_dirs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and query the latest BERIL projects")
    parser.add_argument("--count", type=int, default=5, help="Number of latest projects to ingest")
    parser.add_argument("--limit", type=int, default=3, help="Maximum query results per project")
    return parser


def render_results(console: Console, project: str, result: object, limit: int) -> None:
    resources = _resources(result)
    console.print(Rule(f"[bold]{project}[/bold]"))
    if not resources:
        console.print("[dim]no results[/dim]")
        return
    table = Table(show_lines=False, expand=True)
    table.add_column("Score", justify="right", width=7, style="cyan")
    table.add_column("Resource", overflow="fold")
    table.add_column("Abstract", overflow="fold")
    for resource in resources[:limit]:
        score = float(_field(resource, "score", 0.0))
        uri = str(_field(resource, "uri", ""))
        abstract = str(_field(resource, "abstract", "")).strip().replace("\n", " ")
        if len(abstract) > 240:
            abstract = abstract[:237] + "..."
        table.add_row(f"{score:.3f}", uri, abstract)
    console.print(table)


def main() -> None:
    args = build_parser().parse_args()
    console = Console()
    config = ContextConfig.from_env()
    project_dirs = latest_project_dirs(config.projects_dir, args.count)
    if not project_dirs:
        raise SystemExit("No projects found")

    console.print(Rule("[bold]Smoke test projects[/bold]"))
    for project_dir in project_dirs:
        console.print(f"  • {project_dir.name}")

    client = create_client(config)
    try:
        with RichIngestObserver(console=console) as observer:
            ingest_projects(
                config,
                client,
                [project_dir.name for project_dir in project_dirs],
                observer=observer,
            )

        console.print()
        console.print(Rule("[bold green]Query results[/bold green]"))
        for project_dir in project_dirs:
            result = client.find(
                query=project_dir.name.replace("_", " "),
                target_uri=project_target_uri(project_dir.name),
                limit=args.limit,
            )
            render_results(console, project_dir.name, result, args.limit)
    finally:
        client.close()


if __name__ == "__main__":
    main()
