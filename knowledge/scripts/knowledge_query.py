from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from observatory_context.config import ContextConfig
from observatory_context.openviking_client import create_client
from observatory_context.query import (
    format_find_text,
    result_to_json,
    run_find,
    target_uri_for_find,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query BERIL context in OpenViking")
    commands = parser.add_subparsers(dest="command", required=True)

    find = commands.add_parser("find", help="Find context resources")
    find.add_argument("query", help="Search query")
    scope = find.add_mutually_exclusive_group()
    scope.add_argument("--project", help="Search one project ID")
    scope.add_argument("--docs", action="store_true", help="Search central docs")
    scope.add_argument("--metadata", action="store_true", help="Search project metadata")
    scope.add_argument("--target-uri", help="Search a raw OpenViking target URI")
    find.add_argument("--limit", type=int, default=10, help="Maximum results")
    find.add_argument("--json", action="store_true", help="Print JSON")

    overview = commands.add_parser("overview", help="Print a resource overview")
    overview.add_argument("uri", help="Resource URI")

    read = commands.add_parser("read", help="Print a resource")
    read.add_argument("uri", help="Resource URI")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ContextConfig.from_env()
    client = create_client(config)
    try:
        if args.command == "find":
            target_uri = target_uri_for_find(
                project=args.project,
                docs=args.docs,
                metadata=args.metadata,
                target_uri=args.target_uri,
            )
            result = run_find(client, args.query, target_uri, args.limit)
            print(result_to_json(result) if args.json else format_find_text(result))
        elif args.command == "overview":
            print(client.overview(args.uri))
        elif args.command == "read":
            print(client.read(args.uri))
    finally:
        close = getattr(client, "close", None)
        if close:
            close()


if __name__ == "__main__":
    main()
