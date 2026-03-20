"""Query OpenViking-backed BERIL knowledge from the command line."""

from __future__ import annotations

import argparse
from pathlib import Path

from observatory_context import runtime
from observatory_context.render import RenderLevel


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query BERIL knowledge through OpenViking.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Semantic search across OpenViking resources.")
    search.add_argument("query", help="Search query text.")
    search.add_argument("--project", default=None, help="Optional project ID scope.")
    search.add_argument("--kind", default=None, help="Optional resource kind filter.")
    search.add_argument(
        "--detail-level",
        choices=[level.value for level in RenderLevel],
        default=RenderLevel.L1.value,
        help="Rendered detail level.",
    )
    search.add_argument("--limit", type=int, default=5, help="Maximum number of results to print.")

    project = subparsers.add_parser("project", help="Show a project workspace summary.")
    project.add_argument("project_id", help="Project ID.")
    project.add_argument(
        "--detail-level",
        choices=[level.value for level in RenderLevel],
        default=RenderLevel.L1.value,
        help="Rendered detail level for the project resource.",
    )

    resource = subparsers.add_parser("resource", help="Show one resource by ID or URI.")
    resource.add_argument("id_or_uri", help="Resource ID or full URI.")
    resource.add_argument(
        "--detail-level",
        choices=[level.value for level in RenderLevel],
        default=RenderLevel.L2.value,
        help="Rendered detail level.",
    )

    related = subparsers.add_parser("related", help="Show related resources.")
    related.add_argument("id_or_uri", help="Resource ID or full URI.")
    related.add_argument("--limit", type=int, default=5, help="Maximum number of results to print.")

    return parser


def _service():
    return runtime.build_service(REPO_ROOT, offline=False, require_live=True)


def _level(value: str) -> RenderLevel:
    return RenderLevel(value)


def _print_result(index: int, response) -> None:
    print(f"## {index}. {response.resource.title}")
    print(f"- uri: {response.resource.uri}")
    print(f"- kind: {response.resource.kind}")
    if response.resource.project_ids:
        print(f"- projects: {', '.join(response.resource.project_ids)}")
    print()
    print(response.rendered)
    print()


def _print_resource(resource) -> None:
    print(f"- {resource.title} [{resource.kind}]")
    print(f"  {resource.uri}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = _service()

    if args.command == "search":
        results = service.search_context(
            args.query,
            kind=args.kind,
            project=args.project,
            detail_level=_level(args.detail_level),
        )
        print(f'Results for "{args.query}"')
        print("=" * (len(args.query) + 13))
        print()
        if not results:
            print("No OpenViking matches found.")
            return 0
        for index, response in enumerate(results[: args.limit], start=1):
            _print_result(index, response)
        return 0

    if args.command == "project":
        workspace = service.get_project_workspace(
            args.project_id,
            detail_level=_level(args.detail_level),
        )
        print(f"Project workspace: {workspace.project_id}")
        print(f"URI: {workspace.workspace_uri}")
        print()
        print(workspace.project_resource.title)
        print()
        for resource in workspace.resources:
            _print_resource(resource)
        return 0

    if args.command == "resource":
        response = service.get_resource(args.id_or_uri, detail_level=_level(args.detail_level))
        _print_result(1, response)
        return 0

    if args.command != "related":
        return 1

    related = service.related_resources(args.id_or_uri, limit=args.limit)
    print(f"Related resources for {args.id_or_uri}")
    print("=" * (len(args.id_or_uri) + 22))
    print()
    if not related:
        print("No related OpenViking resources found.")
        return 0
    for resource in related:
        _print_resource(resource)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
