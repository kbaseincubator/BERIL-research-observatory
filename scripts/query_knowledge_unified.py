#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "pydantic>=2.0",
#   "pydantic-settings>=2.0",
#   "httpx>=0.27",
#   "openviking>=0.2.9",
# ]
# ///
"""Unified query backend for BERIL knowledge — delegates all queries via ContextDelivery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from observatory_context._text import split_frontmatter
from observatory_context.delivery import ContextDelivery
from observatory_context.models import (
    ContextItem,
    GraphResult,
    SearchResults,
    Scope,
    Tier,
)
from observatory_context.uris import (
    build_knowledge_graph_uri,
    build_knowledge_resource_uri,
    build_project_workspace_uri,
)

DELIVERY: ContextDelivery


def _build_delivery() -> ContextDelivery:
    """Build a ContextDelivery instance with a live OpenViking connection or exit."""
    from observatory_context.runtime import build_delivery

    try:
        delivery = build_delivery(require_live=True)
    except Exception as exc:
        print(f"Error: OpenViking server is not reachable: {exc}", file=sys.stderr)
        print("Start the server first. See docs/openviking_tutorial.md.", file=sys.stderr)
        raise SystemExit(1)
    return delivery


def _read_knowledge_yaml(relative_path: str) -> dict | list:
    """Read a knowledge YAML file from OpenViking and return parsed data."""
    uri = build_knowledge_resource_uri(relative_path)
    content = DELIVERY.client.read_resource(uri)
    _, body = split_frontmatter(content, {})
    return yaml.safe_load(body) or {}


# ------------------------------------------------------------------
# Output helpers
# ------------------------------------------------------------------


def _print_context_item(item: ContextItem, index: int | None = None) -> None:
    prefix = f"## {index}. " if index else "## "
    print(f"{prefix}{item.title}")
    print(f"- uri: {item.uri}")
    print(f"- kind: {item.kind}")
    print(f"- tier: {item.tier}")
    if item.project_ids:
        print(f"- projects: {', '.join(item.project_ids)}")
    if item.tags:
        print(f"- tags: {', '.join(item.tags)}")
    if item.source_type == "memory":
        print("- source: memory")
    print()
    print(item.content)
    print()


def _print_search_results(results: SearchResults) -> None:
    print(f'Results for "{results.query}" ({results.total_count} total)')
    print("=" * 60)
    print()
    if not results.items:
        print("No matching resources found.")
    for i, item in enumerate(results.items, 1):
        _print_context_item(item, index=i)


def _print_graph_result(result: GraphResult) -> None:
    print(f"## Root: {result.root.title}")
    print(f"- uri: {result.root.uri}")
    print()
    if result.relations:
        print("### Relations")
        for edge in result.relations:
            print(f"  {edge.predicate} → {edge.object_uri}")
            print(f"    evidence: {edge.evidence} (confidence: {edge.confidence})")
        print()
    if result.connected:
        print(f"### Connected Entities ({len(result.connected)})")
        for item in result.connected:
            _print_context_item(item)


def _print_items(items: list[ContextItem], heading: str) -> None:
    """Print a list of context items with a heading."""
    print(f"### {heading} ({len(items)} total)")
    print()
    if not items:
        print("No items found.")
    for i, item in enumerate(items, 1):
        _print_context_item(item, index=i)


# ------------------------------------------------------------------
# Subcommand handlers
# ------------------------------------------------------------------


def _handle_search(args) -> int:
    tier = Tier(args.tier)
    scope = Scope(args.scope) if args.scope else Scope.all
    results = DELIVERY.search(
        args.topic,
        tier=tier,
        scope=scope,
        kind=getattr(args, "kind", None),
        project=args.project,
        with_memory=args.with_memory,
        limit=args.limit,
    )
    _print_search_results(results)
    return 0


def _handle_figures(args) -> int:
    tier = Tier(args.tier)
    results = DELIVERY.search(args.topic, kind="figure", tier=tier, limit=20)
    _print_search_results(results)
    return 0


def _handle_data(args) -> int:
    tier = Tier(args.tier)
    results = DELIVERY.search(args.topic, kind="project_document", tier=tier, limit=30)
    _print_search_results(results)
    return 0


def _handle_project(args) -> int:
    uri = build_project_workspace_uri(args.project_id)
    item = DELIVERY.get(uri, tier=Tier.L2)
    _print_context_item(item)
    return 0


def _handle_landscape(args) -> int:
    uri = build_knowledge_graph_uri()
    items = DELIVERY.browse(uri, tier=Tier.L1)
    _print_items(items, "Research Landscape")
    return 0


def _handle_entities(args) -> int:
    tier = Tier(args.tier)
    items = DELIVERY.entities(args.entity_type, tier=tier)
    _print_items(items, f"{args.entity_type.title()} Entities")
    return 0


def _handle_connections(args) -> int:
    tier = Tier(args.tier)
    result = DELIVERY.traverse(args.entity, hops=1, tier=tier)
    _print_graph_result(result)
    return 0


def _handle_hypotheses(args) -> int:
    items = DELIVERY.hypotheses(args.status)
    label = args.status or "all"
    _print_items(items, f"Hypotheses ({label})")
    return 0


def _handle_gaps(args) -> int:
    proposed = DELIVERY.hypotheses(status="proposed")
    testing = DELIVERY.hypotheses(status="testing")
    combined = proposed + testing
    _print_items(combined, "Research Gaps (proposed/testing hypotheses)")
    return 0


def _handle_timeline(args) -> int:
    items = DELIVERY.timeline(project=args.project)
    suffix = f" for {args.project}" if args.project else ""
    _print_items(items, f"Research Timeline{suffix}")
    return 0


def _handle_backfill(_args) -> int:
    print("DEPRECATED: `backfill` has been removed.")
    print("Use `viking_ingest.py --graph-only` instead.")
    return 1


def _handle_related(args) -> int:
    result = DELIVERY.traverse(args.id_or_uri, hops=1)
    _print_graph_result(result)
    return 0


def _handle_grep(args) -> int:
    from observatory_context.uris import build_observatory_root_uri

    target = args.uri or build_observatory_root_uri()
    result = DELIVERY.client.grep(target, args.pattern, case_insensitive=args.ignore_case)
    matches = result.get("matches", [])
    if not matches:
        print(f'No content matches for "{args.pattern}"')
        return 0
    print(f'### Content matches for "{args.pattern}"')
    print()
    for entry in matches:
        print(f"**{entry.get('uri', 'unknown')}**")
        for line in entry.get("lines", []):
            print(f"  L{line.get('number', '?')}: {line.get('content', '')}")
        print()
    return 0


def _handle_glob(args) -> int:
    from observatory_context.uris import build_observatory_root_uri

    result = DELIVERY.client.glob(args.pattern, uri=build_observatory_root_uri())
    matches = result.get("matches", [])
    if not matches:
        print(f'No resources matching "{args.pattern}"')
        return 0
    print(f'### Resources matching "{args.pattern}"')
    print()
    for entry in matches:
        print(f"- {entry.get('uri', 'unknown')}")
    print(f"\n({len(matches)} total)")
    return 0


# -- New subcommands --


def _handle_browse(args) -> int:
    # Use browse-specific tier (default L1) unless global --tier was set
    tier = Tier(args.browse_tier) if args.tier == "L2" else Tier(args.tier)
    items = DELIVERY.browse(args.uri, tier=tier)
    _print_items(items, f"Browse: {args.uri}")
    return 0


def _handle_traverse(args) -> int:
    tier = Tier(args.tier)
    result = DELIVERY.traverse(
        args.entity_uri,
        hops=args.hops,
        relation_filter=args.relation_filter,
        tier=tier,
    )
    _print_graph_result(result)
    return 0


def _handle_recall(args) -> int:
    items = DELIVERY.recall(args.query, store=args.store, limit=args.limit)
    _print_items(items, f'Memory recall: "{args.query}"')
    return 0


def _handle_remember(args) -> int:
    entities = [e.strip() for e in args.entities.split(",")] if args.entities else None
    projects = [p.strip() for p in args.projects.split(",")] if args.projects else None
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None

    uri = DELIVERY.remember(
        args.store,
        args.title,
        args.body,
        entities=entities,
        projects=projects,
        tags=tags,
    )
    print(f"Memory created: {uri}")
    return 0


def _handle_ingest_entity(args) -> int:
    profile = json.loads(args.profile_json)
    relations = json.loads(args.relations_json) if args.relations_json else None

    uri = DELIVERY.ingest_entity(
        args.type,
        args.id,
        profile,
        relations=relations,
    )
    print(f"Entity created: {uri}")
    return 0


_HANDLERS = {
    "search": _handle_search,
    "figures": _handle_figures,
    "data": _handle_data,
    "project": _handle_project,
    "landscape": _handle_landscape,
    "entities": _handle_entities,
    "connections": _handle_connections,
    "hypotheses": _handle_hypotheses,
    "gaps": _handle_gaps,
    "timeline": _handle_timeline,
    "backfill": _handle_backfill,
    "related": _handle_related,
    "grep": _handle_grep,
    "glob": _handle_glob,
    "browse": _handle_browse,
    "traverse": _handle_traverse,
    "recall": _handle_recall,
    "remember": _handle_remember,
    "ingest-entity": _handle_ingest_entity,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BERIL knowledge query — delegates all queries via ContextDelivery."
    )
    parser.add_argument(
        "--tier",
        choices=["L0", "L1", "L2"],
        default="L2",
        help="Detail tier (default: L2)",
    )
    parser.add_argument(
        "--with-memory",
        action="store_true",
        default=False,
        help="Blend memory results into search",
    )
    parser.add_argument(
        "--scope",
        choices=["all", "resources", "memory", "graph"],
        default=None,
        help="Search scope (default: all)",
    )

    sub = parser.add_subparsers(dest="command")

    # -- Existing subcommands (rewired) --

    p_search = sub.add_parser("search", help="Search projects/findings by topic")
    p_search.add_argument("topic")
    p_search.add_argument("--project", default=None)
    p_search.add_argument("--kind", default=None, help="Filter by resource kind")
    p_search.add_argument("--limit", type=int, default=10)

    p_fig = sub.add_parser("figures", help="Search figure catalog")
    p_fig.add_argument("topic")

    p_data = sub.add_parser("data", help="Search reusable data artifacts")
    p_data.add_argument("topic")

    p_project = sub.add_parser("project", help="Show project summary")
    p_project.add_argument("project_id")

    sub.add_parser("landscape", help="Browse knowledge graph at L1")

    p_entities = sub.add_parser("entities", help="List entities by type")
    p_entities.add_argument(
        "entity_type",
        choices=["organism", "gene", "pathway", "method", "concept"],
    )

    p_conn = sub.add_parser("connections", help="Show relations for an entity")
    p_conn.add_argument("entity", help="Entity URI")

    p_hyp = sub.add_parser("hypotheses", help="List hypotheses")
    p_hyp.add_argument("status", nargs="?")

    sub.add_parser("gaps", help="Show proposed/testing hypotheses as research gaps")

    p_timeline = sub.add_parser("timeline", help="Show timeline events")
    p_timeline.add_argument("--project", default=None)

    p_backfill = sub.add_parser(
        "backfill", help="DEPRECATED — use viking_ingest.py --graph-only"
    )

    p_related = sub.add_parser("related", help="Show related resources (graph traverse)")
    p_related.add_argument("id_or_uri")

    p_grep = sub.add_parser("grep", help="Content search across resources")
    p_grep.add_argument("pattern")
    p_grep.add_argument("--uri", default=None, help="Scope search to a URI subtree")
    p_grep.add_argument("--ignore-case", action="store_true")

    p_glob = sub.add_parser("glob", help="File pattern matching")
    p_glob.add_argument("pattern")

    # -- New subcommands --

    p_browse = sub.add_parser("browse", help="Directory listing via ContextDelivery")
    p_browse.add_argument("uri", help="Directory URI to browse")
    p_browse.add_argument(
        "--browse-tier",
        choices=["L0", "L1", "L2"],
        default="L1",
        help="Detail tier for browse (default: L1)",
    )

    p_traverse = sub.add_parser("traverse", help="Graph walk from an entity")
    p_traverse.add_argument("entity_uri", help="Starting entity URI")
    p_traverse.add_argument("--hops", type=int, default=1, help="Number of hops")
    p_traverse.add_argument(
        "--relation-filter", default=None, help="Filter by predicate name"
    )

    p_recall = sub.add_parser("recall", help="Search memories")
    p_recall.add_argument("query")
    p_recall.add_argument(
        "--store",
        choices=["journal", "patterns", "conversations"],
        default=None,
        help="Restrict to a memory store",
    )
    p_recall.add_argument("--limit", type=int, default=5)

    p_remember = sub.add_parser("remember", help="Write a memory entry")
    p_remember.add_argument(
        "store", choices=["journal", "patterns", "conversations"]
    )
    p_remember.add_argument("title")
    p_remember.add_argument("body")
    p_remember.add_argument("--entities", default=None, help="Comma-separated entity refs")
    p_remember.add_argument("--projects", default=None, help="Comma-separated project IDs")
    p_remember.add_argument("--tags", default=None, help="Comma-separated tags")

    p_ingest = sub.add_parser("ingest-entity", help="Create entity with profile")
    p_ingest.add_argument("type", choices=["organism", "gene", "pathway", "method", "concept"])
    p_ingest.add_argument("id", help="Entity identifier slug")
    p_ingest.add_argument("--profile-json", required=True, help="Profile data as JSON string")
    p_ingest.add_argument("--relations-json", default=None, help="Relations as JSON array string")

    return parser


def main(argv: list[str] | None = None) -> int:
    global DELIVERY
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        if argv is None and len(sys.argv) == 2:
            # Bare argument treated as search topic for backward compat
            args.command = "search"
            args.topic = sys.argv[1]
            args.project = None
            args.kind = None
            args.limit = 10
        else:
            parser.print_help()
            return 1

    DELIVERY = _build_delivery()

    handler = _HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
