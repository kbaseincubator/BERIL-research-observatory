#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openviking",
#     "pyyaml",
# ]
# ///
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from observatory_context.config import ContextConfig
from observatory_context.openviking_client import create_client
from observatory_context.query import (
    format_find_text,
    parse_filter_arg,
    result_to_json,
    run_find,
    target_uri_for_find,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query BERIL context in OpenViking")
    commands = parser.add_subparsers(dest="command", required=True)

    find = commands.add_parser("find", help="Semantic search")
    find.add_argument("query", help="Search query")
    scope = find.add_mutually_exclusive_group()
    scope.add_argument("--project", help="Search one project ID")
    scope.add_argument("--docs", action="store_true", help="Search central docs")
    scope.add_argument("--target-uri", help="Search a raw OpenViking target URI")
    find.add_argument("--limit", type=int, default=10, help="Maximum results")
    find.add_argument("--filter", help="Raw JSON metadata filter (OV filter tree)")
    find.add_argument("--score-threshold", type=float, help="Minimum score")
    find.add_argument("--since", help="Lower time bound (ISO date or 7d/2w)")
    find.add_argument("--until", help="Upper time bound (ISO date or 7d/2w)")
    find.add_argument(
        "--time-field",
        choices=["updated_at", "created_at"],
        help="Time field for since/until",
    )
    find.add_argument("--json", action="store_true", help="Print JSON")

    grep = commands.add_parser("grep", help="Exact pattern search across resources")
    grep.add_argument("pattern", help="Pattern to match")
    grep.add_argument(
        "--uri",
        default="viking://resources/",
        help="URI subtree to search (default: viking://resources/)",
    )
    grep.add_argument("-i", "--case-insensitive", action="store_true")
    grep.add_argument("--exclude-uri", help="URI subtree to exclude")
    grep.add_argument("--node-limit", type=int, help="Max matching nodes")

    glob = commands.add_parser("glob", help="URI pattern enumeration")
    glob.add_argument("pattern", help="Glob pattern (e.g. viking://resources/projects/*/)")
    glob.add_argument("--uri", default="viking://", help="Root URI")

    ls = commands.add_parser("ls", help="List directory contents")
    ls.add_argument("uri", help="Directory URI")
    ls.add_argument("--simple", action="store_true", help="Path list only")
    ls.add_argument("-r", "--recursive", action="store_true")

    tree = commands.add_parser("tree", help="Print resource hierarchy")
    tree.add_argument("uri", help="Root URI")
    tree.add_argument("--node-limit", type=int, default=1000)

    stat = commands.add_parser("stat", help="Resource metadata")
    stat.add_argument("uri", help="Resource URI")

    relations = commands.add_parser("relations", help="List relations for a resource")
    relations.add_argument("uri", help="Resource URI")

    link = commands.add_parser("link", help="Create relation(s) between resources")
    link.add_argument("from_uri", help="Source URI")
    link.add_argument("to_uris", nargs="+", help="Target URI(s)")
    link.add_argument("--reason", default="", help="Optional reason for the relation")

    unlink = commands.add_parser("unlink", help="Remove a relation")
    unlink.add_argument("from_uri", help="Source URI")
    unlink.add_argument("to_uri", help="Target URI")

    overview = commands.add_parser("overview", help="Print a resource overview")
    overview.add_argument("uri", help="Resource URI")

    read = commands.add_parser("read", help="Print a resource")
    read.add_argument("uri", help="Resource URI")

    return parser


def _print_json(value) -> None:
    print(json.dumps(value, indent=2, default=str))


def main() -> None:
    args = build_parser().parse_args()
    config = ContextConfig.from_env()
    client = create_client(config)
    try:
        if args.command == "find":
            target_uri = target_uri_for_find(
                project=args.project,
                docs=args.docs,
                target_uri=args.target_uri,
            )
            result = run_find(
                client,
                args.query,
                target_uri,
                args.limit,
                filter=parse_filter_arg(args.filter),
                score_threshold=args.score_threshold,
                since=args.since,
                until=args.until,
                time_field=args.time_field,
            )
            print(result_to_json(result) if args.json else format_find_text(result))
        elif args.command == "grep":
            kwargs = {"case_insensitive": args.case_insensitive}
            if args.node_limit is not None:
                kwargs["node_limit"] = args.node_limit
            if args.exclude_uri:
                kwargs["exclude_uri"] = args.exclude_uri
            _print_json(client.grep(args.uri, args.pattern, **kwargs))
        elif args.command == "glob":
            _print_json(client.glob(args.pattern, uri=args.uri))
        elif args.command == "ls":
            _print_json(
                client.ls(args.uri, simple=args.simple, recursive=args.recursive)
            )
        elif args.command == "tree":
            _print_json(client.tree(args.uri, node_limit=args.node_limit))
        elif args.command == "stat":
            _print_json(client.stat(args.uri))
        elif args.command == "relations":
            _print_json(client.relations(args.uri))
        elif args.command == "link":
            client.link(args.from_uri, args.to_uris, reason=args.reason)
        elif args.command == "unlink":
            client.unlink(args.from_uri, args.to_uri)
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
