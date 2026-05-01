from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from observatory_context.config import ContextConfig
from observatory_context.ingest import ingest_project
from observatory_context.openviking_client import create_client
from observatory_context.query import format_find_text
from observatory_context.selection import iter_project_dirs, project_target_uri


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and query the latest BERIL projects")
    parser.add_argument("--count", type=int, default=5, help="Number of latest projects to ingest")
    parser.add_argument("--limit", type=int, default=3, help="Maximum query results per project")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ContextConfig.from_env()
    project_dirs = latest_project_dirs(config.projects_dir, args.count)
    if not project_dirs:
        raise SystemExit("No projects found")

    print("Smoke test projects:")
    for project_dir in project_dirs:
        print(f"- {project_dir.name}")

    client = create_client(config)
    try:
        for project_dir in project_dirs:
            ingest_project(config, client, project_dir.name)

        for project_dir in project_dirs:
            print()
            print(f"## {project_dir.name}")
            result = client.find(
                query=project_dir.name.replace("_", " "),
                target_uri=project_target_uri(project_dir.name),
                limit=args.limit,
            )
            print(format_find_text(result))
    finally:
        client.close()


def latest_project_dirs(projects_dir: Path, count: int) -> list[Path]:
    return sorted(
        iter_project_dirs(projects_dir),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )[:count]


if __name__ == "__main__":
    main()
