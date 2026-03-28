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
"""Unified query backend for BERIL knowledge — delegates all queries to OpenViking."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from observatory_context._text import split_frontmatter
from observatory_context.render import RenderLevel
from observatory_context.service.context_service import ObservatoryContextService
from observatory_context.uris import build_knowledge_resource_uri


def _build_service() -> ObservatoryContextService:
    """Build service with a live OpenViking connection or exit."""
    from observatory_context import runtime

    try:
        service = runtime.build_service(REPO_ROOT, require_live=True)
    except Exception as exc:
        print(f"Error: OpenViking server is not reachable: {exc}", file=sys.stderr)
        print("Start the server first. See docs/openviking_tutorial.md.", file=sys.stderr)
        raise SystemExit(1)
    return service


def _read_knowledge_yaml(service: ObservatoryContextService, relative_path: str) -> dict | list:
    """Read a knowledge YAML file from OpenViking and return parsed data."""
    uri = build_knowledge_resource_uri(relative_path)
    content = service.client.read_resource(uri)
    _, body = split_frontmatter(content, {})
    return yaml.safe_load(body) or {}


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


SERVICE: ObservatoryContextService

def _handle_search(args) -> int:
    results = SERVICE.search_context(
        args.topic, project=args.project, detail_level=RenderLevel.L1, limit=args.limit,
    )
    print(f'Results for "{args.topic}"')
    print("=" * (len(args.topic) + 13))
    print()
    if not results:
        print("No matching resources found.")
    for i, r in enumerate(results, 1):
        _print_result(i, r)
    return 0


def _handle_figures(args) -> int:
    results = SERVICE.search_context(args.topic, kind="figure", detail_level=RenderLevel.L1)
    print(f'Figures matching "{args.topic}"')
    print()
    if not results:
        print("No matching figures found.")
    for i, r in enumerate(results[:20], 1):
        _print_result(i, r)
    return 0


def _handle_data(args) -> int:
    results = SERVICE.search_context(args.topic, detail_level=RenderLevel.L1)
    data_results = [r for r in results if r.resource.kind in {"project_document", "knowledge_document"}]
    print(f'Data artifacts matching "{args.topic}"')
    print()
    if not data_results:
        print("No matching data artifacts found.")
    for i, r in enumerate(data_results[:30], 1):
        _print_result(i, r)
    return 0


def _handle_project(args) -> int:
    workspace = SERVICE.get_project_workspace(args.project_id, detail_level=RenderLevel.L1)
    print(f"Project workspace: {workspace.project_id}")
    print(f"URI: {workspace.workspace_uri}")
    print()
    print(workspace.project_resource.title)
    print()
    for resource in workspace.resources:
        _print_resource(resource)
    return 0


def _handle_landscape(args) -> int:
    all_resources = SERVICE.all_resources()
    kinds: dict[str, int] = {}
    projects: set[str] = set()
    for r in all_resources.values():
        kinds[r.kind] = kinds.get(r.kind, 0) + 1
        projects.update(r.project_ids)
    print("## Research Landscape")
    print()
    print(f"**Total resources**: {len(all_resources)}")
    print(f"**Projects**: {len(projects)}")
    print()
    print("### Resources by kind")
    print("| Kind | Count |")
    print("|---|---|")
    for kind in sorted(kinds):
        print(f"| {kind} | {kinds[kind]} |")
    return 0


def _handle_entities(args) -> int:
    data = _read_knowledge_yaml(SERVICE, f"entities/{args.entity_type}s.yaml")
    rows = data.get(f"{args.entity_type}s", []) if isinstance(data, dict) else []
    if args.query:
        ql = args.query.lower()
        rows = [r for r in rows if ql in " ".join(str(v) for v in r.values()).lower()]
    print(f"### {args.entity_type.title()} Entities ({len(rows)} total)")
    print()
    print("| ID | Name | Projects | Description |")
    print("|---|---|---|---|")
    for row in rows[:100]:
        rid = row.get("id", "")
        name = row.get("name", "")
        proj_n = len(row.get("projects", []))
        desc = str(row.get("description") or row.get("definition") or row.get("role") or "")
        desc = " ".join(desc.split())[:90]
        print(f"| {rid} | {name} | {proj_n} | {desc} |")
    return 0


def _handle_connections(args) -> int:
    data = _read_knowledge_yaml(SERVICE, "relations.yaml")
    relations = data.get("relations", []) if isinstance(data, dict) else []
    needle = args.entity.lower()
    outgoing = [r for r in relations if needle in str(r.get("subject", "")).lower()]
    incoming = [r for r in relations if needle in str(r.get("object", "")).lower()]
    print(f"### Connections for {args.entity}")
    print()
    print("**Outgoing (this entity -> other):**")
    print("| Predicate | Target | Evidence Project | Confidence |")
    print("|---|---|---|---|")
    for r in outgoing[:80]:
        print(f"| {r.get('predicate','')} | {r.get('object','')} | {r.get('evidence_project','')} | {r.get('confidence','')} |")
    if not outgoing:
        print("| _none_ |  |  |  |")
    print()
    print("**Incoming (other -> this entity):**")
    print("| Source | Predicate | Evidence Project | Confidence |")
    print("|---|---|---|---|")
    for r in incoming[:80]:
        print(f"| {r.get('subject','')} | {r.get('predicate','')} | {r.get('evidence_project','')} | {r.get('confidence','')} |")
    if not incoming:
        print("| _none_ |  |  |  |")
    return 0


def _handle_hypotheses(args) -> int:
    data = _read_knowledge_yaml(SERVICE, "hypotheses.yaml")
    hypotheses = data.get("hypotheses", []) if isinstance(data, dict) else []
    if args.status:
        hypotheses = [h for h in hypotheses if str(h.get("status", "")).lower() == args.status.lower()]
    print(f"### Hypotheses ({args.status or 'all'})")
    print()
    print("| ID | Status | Statement | Origin Project | Evidence |")
    print("|---|---|---|---|---|")
    for h in hypotheses:
        stmt = " ".join(str(h.get("statement", "")).split())[:80]
        sup = len(h.get("evidence_supporting", []) or [])
        con = len(h.get("evidence_contradicting", []) or [])
        print(f"| {h.get('id','')} | {h.get('status','')} | {stmt} | {h.get('origin_project','')} | {sup} supporting, {con} contradicting |")
    if not hypotheses:
        print("| _none_ |  |  |  |  |")
    return 0


def _handle_gaps(args) -> int:
    data = _read_knowledge_yaml(SERVICE, "hypotheses.yaml")
    hypotheses = data.get("hypotheses", []) if isinstance(data, dict) else []
    testing = [h for h in hypotheses if h.get("status") in {"proposed", "testing"}]
    print("### Research Gaps (proposed/testing hypotheses)")
    print()
    for h in testing:
        print(f"- **{h.get('id')}**: {h.get('statement', '')}")
    if not testing:
        print("No open gaps found.")
    return 0


def _handle_timeline(args) -> int:
    data = _read_knowledge_yaml(SERVICE, "timeline.yaml")
    events = data.get("events", []) if isinstance(data, dict) else []
    if args.project:
        target = args.project.strip()
        events = [e for e in events if target in {str(e.get("project", "")), *[str(p) for p in e.get("projects", [])]}]
    suffix = f" for {args.project}" if args.project else ""
    print(f"### Research Timeline{suffix}")
    print()
    print("| Date | Type | Project | Summary |")
    print("|---|---|---|---|")
    for ev in events:
        project = str(ev.get("project", "")) or ", ".join(str(p) for p in ev.get("projects", []))
        summary = " ".join(str(ev.get("summary", "")).split()).replace("|", "/")
        print(f"| {ev.get('date','')} | {ev.get('type','')} | {project} | {summary} |")
    if not events:
        print("| _none_ |  |  |  |")
    return 0


def _handle_backfill(args) -> int:
    data = _read_knowledge_yaml(SERVICE, "timeline.yaml")
    events = data.get("events", []) if isinstance(data, dict) else []
    timeline_projects: set[str] = set()
    for ev in events:
        p = str(ev.get("project", "")).strip()
        if p:
            timeline_projects.add(p)
        for pid in ev.get("projects", []):
            timeline_projects.add(str(pid).strip())

    all_resources = SERVICE.all_resources()
    registered_projects = sorted({pid for r in all_resources.values() for pid in r.project_ids})

    if args.project_id:
        has_coverage = args.project_id in timeline_projects
        print(f"### Layer 3 Coverage for {args.project_id}")
        print(f"- {'Has' if has_coverage else 'Missing'} timeline coverage")
        return 0

    missing = [p for p in registered_projects if p not in timeline_projects]
    print(f"### Projects Missing Layer 3 Coverage ({len(missing)}/{len(registered_projects)})")
    print()
    if not missing:
        print("All projects have graph coverage.")
    else:
        print("| Project |")
        print("|---|")
        for p in missing:
            print(f"| {p} |")
    return 0


def _handle_related(args) -> int:
    related = SERVICE.related_resources(args.id_or_uri, limit=args.limit)
    print(f"Related resources for {args.id_or_uri}")
    print("=" * (len(args.id_or_uri) + 22))
    print()
    if not related:
        print("No related resources found.")
    else:
        for resource in related:
            _print_resource(resource)
    return 0


def _handle_grep(args) -> int:
    result = SERVICE.grep_resources(args.pattern, uri=args.uri, case_insensitive=args.ignore_case)
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
    result = SERVICE.glob_resources(args.pattern)
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
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BERIL knowledge query — delegates all queries to OpenViking."
    )
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Search projects/findings by topic")
    p_search.add_argument("topic")
    p_search.add_argument("--project", default=None)
    p_search.add_argument("--limit", type=int, default=5)

    p_fig = sub.add_parser("figures", help="Search figure catalog")
    p_fig.add_argument("topic")

    p_data = sub.add_parser("data", help="Search reusable data artifacts")
    p_data.add_argument("topic")

    p_project = sub.add_parser("project", help="Show project summary")
    p_project.add_argument("project_id")

    sub.add_parser("landscape", help="Show overall landscape summary")

    p_entities = sub.add_parser("entities", help="List entities by type")
    p_entities.add_argument("entity_type", choices=["organism", "gene", "pathway", "method", "concept"])
    p_entities.add_argument("--query")

    p_conn = sub.add_parser("connections", help="Show relations for an entity")
    p_conn.add_argument("entity")

    p_hyp = sub.add_parser("hypotheses", help="List hypotheses")
    p_hyp.add_argument("status", nargs="?")

    sub.add_parser("gaps", help="Show graph-derived research gaps")

    p_timeline = sub.add_parser("timeline", help="Show timeline events")
    p_timeline.add_argument("project", nargs="?")

    p_backfill = sub.add_parser("backfill", help="List projects missing Layer 3 coverage")
    p_backfill.add_argument("project_id", nargs="?")

    p_related = sub.add_parser("related", help="Show related resources")
    p_related.add_argument("id_or_uri")
    p_related.add_argument("--limit", type=int, default=5)

    p_grep = sub.add_parser("grep", help="Content search across resources")
    p_grep.add_argument("pattern")
    p_grep.add_argument("--uri", default=None, help="Scope search to a URI subtree")
    p_grep.add_argument("--ignore-case", action="store_true")

    p_glob = sub.add_parser("glob", help="File pattern matching")
    p_glob.add_argument("pattern")

    return parser


def main(argv: list[str] | None = None) -> int:
    global SERVICE
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        if argv is None and len(sys.argv) == 2:
            args.command = "search"
            args.topic = sys.argv[1]
            args.project = None
            args.limit = 5
        else:
            parser.print_help()
            return 1

    SERVICE = _build_service()

    handler = _HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
