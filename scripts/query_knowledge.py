#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
Deterministic query backend for BERIL knowledge and registry artifacts.

Usage examples:
    uv run scripts/query_knowledge.py search metal
    uv run scripts/query_knowledge.py figures pangenome
    uv run scripts/query_knowledge.py data fitness
    uv run scripts/query_knowledge.py project essential_genome
    uv run scripts/query_knowledge.py landscape
    uv run scripts/query_knowledge.py entities organism --query pseudomonas
    uv run scripts/query_knowledge.py connections org_adp1
    uv run scripts/query_knowledge.py hypotheses testing
    uv run scripts/query_knowledge.py gaps
    uv run scripts/query_knowledge.py timeline field_vs_lab_fitness
    uv run scripts/query_knowledge.py backfill essential_genome
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"

REGISTRY_PATH = DOCS_DIR / "project_registry.yaml"
FIGURE_CATALOG_PATH = DOCS_DIR / "figure_catalog.yaml"
FINDINGS_DIGEST_PATH = DOCS_DIR / "findings_digest.md"
GRAPH_COVERAGE_PATH = DOCS_DIR / "knowledge_graph_coverage.md"
GAPS_PATH = DOCS_DIR / "knowledge_gaps.md"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _load_knowledge_list(path: Path, root_key: str) -> list[dict]:
    payload = _load_yaml(path)
    values = payload.get(root_key, [])
    if not isinstance(values, list):
        return []
    return [v for v in values if isinstance(v, dict)]


def _require_registry_artifacts() -> tuple[dict, dict, str]:
    missing = [p for p in (REGISTRY_PATH, FIGURE_CATALOG_PATH, FINDINGS_DIGEST_PATH) if not p.exists()]
    if missing:
        print("The knowledge registry hasn't been generated yet. Run `/build-registry` to create it.")
        raise SystemExit(1)

    registry = _load_yaml(REGISTRY_PATH)
    figures = _load_yaml(FIGURE_CATALOG_PATH)
    findings = FINDINGS_DIGEST_PATH.read_text(encoding="utf-8")
    return registry, figures, findings


def _text_contains(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def _render_topic_search(topic: str, registry: dict, findings_digest: str) -> str:
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        projects = []
    topic_l = topic.lower()
    scored = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        score = 0
        tags = [str(t) for t in p.get("tags", []) if str(t)]
        rq = str(p.get("research_question", "") or "")
        title = str(p.get("title", "") or "")
        findings = [str(f) for f in p.get("key_findings", []) if str(f)]
        organisms = [str(o) for o in p.get("organisms", []) if str(o)]
        dbs = [str(d) for d in p.get("databases_used", []) if str(d)]

        score += 5 * sum(1 for t in tags if topic_l == t.lower())
        score += 3 if _text_contains(title, topic) else 0
        score += 3 if _text_contains(rq, topic) else 0
        score += 2 * sum(1 for f in findings if _text_contains(f, topic))
        score += 1 * sum(1 for o in organisms if _text_contains(o, topic))
        score += 1 * sum(1 for d in dbs if _text_contains(d, topic))
        if score > 0:
            scored.append((score, str(p.get("id", "")), p))

    scored.sort(key=lambda x: (-x[0], x[1]))
    top = scored[:5]

    lines = [f"### Results for \"{topic}\"", ""]
    if not top:
        lines.append("_No matching projects found._")
    else:
        for i, (_, pid, p) in enumerate(top, 1):
            lines.extend(
                [
                    f"**{i}. {pid}** ({p.get('status', 'unknown')})",
                    f"- **Q**: {p.get('research_question') or 'N/A'}",
                    f"- **Findings**: {', '.join((p.get('key_findings') or [])[:3]) or 'N/A'}",
                    f"- **Tags**: {', '.join(p.get('tags') or []) or 'N/A'}",
                    f"- **Data**: {', '.join(p.get('databases_used') or []) or 'N/A'}",
                    f"- [README](projects/{pid}/README.md) | [REPORT](projects/{pid}/REPORT.md)",
                    "",
                ]
            )

    if topic_l in findings_digest.lower():
        lines.extend(
            [
                "### Findings Digest Hits",
                f"- `{topic}` appears in `docs/findings_digest.md`",
            ]
        )
    return "\n".join(lines)


def _render_figure_search(topic: str, figure_catalog: dict) -> str:
    figures = figure_catalog.get("figures", [])
    if not isinstance(figures, list):
        figures = []
    topic_l = topic.lower()
    matches = []
    for fig in figures:
        if not isinstance(fig, dict):
            continue
        hay = " ".join(
            [
                str(fig.get("caption", "") or ""),
                str(fig.get("file", "") or ""),
                str(fig.get("project", "") or ""),
                " ".join(str(t) for t in fig.get("tags", []) if str(t)),
            ]
        ).lower()
        if topic_l in hay:
            matches.append(fig)
    matches.sort(key=lambda f: (str(f.get("project", "")), str(f.get("file", ""))))

    lines = [f"### Figures matching \"{topic}\"", ""]
    if not matches:
        lines.append("_No matching figures found._")
        return "\n".join(lines)

    lines.append("| Project | Figure | Caption |")
    lines.append("|---|---|---|")
    for fig in matches[:20]:
        proj = str(fig.get("project", ""))
        file = str(fig.get("file", ""))
        caption = str(fig.get("caption", "") or "")
        lines.append(f"| {proj} | [{{file}}](projects/{proj}/figures/{file}) | {caption} |".replace("{file}", file))
    return "\n".join(lines)


def _render_data_search(topic: str, registry: dict) -> str:
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        projects = []
    topic_l = topic.lower()
    rows = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", ""))
        artifacts = p.get("key_data_artifacts", [])
        if not isinstance(artifacts, list):
            continue
        for art in artifacts:
            if not isinstance(art, dict):
                continue
            file = str(art.get("file", "") or "")
            desc = str(art.get("description", "") or "")
            reusable = bool(art.get("reusable", False))
            hay = " ".join([file, desc, str(p.get("research_question", "")), " ".join(p.get("tags", []))]).lower()
            if topic_l in hay:
                rows.append((pid, file, desc, reusable))
    rows.sort(key=lambda x: (x[0], x[1]))

    lines = [f"### Data artifacts matching \"{topic}\"", ""]
    if not rows:
        lines.append("_No matching artifacts found._")
        return "\n".join(lines)
    lines.append("| Project | File | Description | Reusable |")
    lines.append("|---|---|---|---|")
    for pid, file, desc, reusable in rows[:30]:
        lines.append(f"| {pid} | `{file}` | {desc or ''} | {'yes' if reusable else 'no'} |")
    return "\n".join(lines)


def _render_project(project_id: str, registry: dict) -> str:
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        projects = []
    project = next((p for p in projects if isinstance(p, dict) and p.get("id") == project_id), None)
    if not project:
        available = ", ".join(sorted(str(p.get("id", "")) for p in projects if isinstance(p, dict)))
        return f"Project `{project_id}` not found.\n\nAvailable IDs: {available}"

    lines = [
        f"## {project.get('title', project_id)}",
        f"**Status**: {project.get('status')} | **Date**: {project.get('date_completed') or 'N/A'}",
        f"**Research Question**: {project.get('research_question') or 'N/A'}",
        "",
        "### Key Findings",
    ]
    findings = project.get("key_findings") or []
    if findings:
        for i, f in enumerate(findings, 1):
            lines.append(f"{i}. {f}")
    else:
        lines.append("_None_")
    lines.extend(
        [
            "",
            "### Tags",
            ", ".join(project.get("tags") or []) or "_None_",
            "",
            "### Data Sources",
            ", ".join(project.get("databases_used") or []) or "_None_",
            "",
            "### Data Artifacts",
        ]
    )
    artifacts = project.get("key_data_artifacts") or []
    if artifacts:
        lines.append("| File | Description |")
        lines.append("|---|---|")
        for art in artifacts:
            if not isinstance(art, dict):
                continue
            lines.append(f"| `{art.get('file', '')}` | {art.get('description', '') or ''} |")
    else:
        lines.append("_None_")

    lines.extend(
        [
            "",
            "### Dependencies",
            f"- **Depends on**: {', '.join(project.get('depends_on') or []) or 'none'}",
            f"- **Enables**: {', '.join(project.get('enables') or []) or 'none'}",
            "",
            f"**Provenance**: {'Available' if project.get('has_provenance') else 'Not yet generated'}",
        ]
    )
    return "\n".join(lines)


def _render_landscape(registry: dict) -> str:
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        projects = []
    status_counts = Counter(str(p.get("status", "unknown")) for p in projects if isinstance(p, dict))
    tag_counts = Counter()
    coll_counts = Counter()
    for p in projects:
        if not isinstance(p, dict):
            continue
        tag_counts.update(str(t) for t in p.get("tags", []) if str(t))
        coll_counts.update(str(c) for c in p.get("databases_used", []) if str(c))

    enables_sorted = sorted(
        (
            (str(p.get("id", "")), len(p.get("enables") or []), p.get("enables") or [])
            for p in projects
            if isinstance(p, dict)
        ),
        key=lambda x: (-x[1], x[0]),
    )
    depends_sorted = sorted(
        (
            (str(p.get("id", "")), len(p.get("depends_on") or []), p.get("depends_on") or [])
            for p in projects
            if isinstance(p, dict)
        ),
        key=lambda x: (-x[1], x[0]),
    )

    lines = [
        "## Research Landscape",
        "",
        "### Status",
        "| Status | Count |",
        "|---|---|",
    ]
    for st in sorted(status_counts):
        lines.append(f"| {st} | {status_counts[st]} |")

    lines.extend(["", "### Top Tags (by project count)", "| Tag | Projects |", "|---|---|"])
    for tag, count in tag_counts.most_common(10):
        lines.append(f"| {tag} | {count} |")

    lines.extend(["", "### BERDL Collections Used", "| Collection | Projects |", "|---|---|"])
    for coll, count in coll_counts.most_common(10):
        lines.append(f"| {coll} | {count} |")

    lines.extend(["", "### Dependency Graph"])
    lines.append("Projects with most downstream dependents:")
    for pid, n, downstream in enables_sorted[:5]:
        if n == 0:
            continue
        lines.append(f"- {pid}: enables {n} projects ({', '.join(downstream[:5])})")
    lines.append("")
    lines.append("Projects with most upstream dependencies:")
    for pid, n, upstream in depends_sorted[:5]:
        if n == 0:
            continue
        lines.append(f"- {pid}: depends on {n} projects ({', '.join(upstream[:5])})")

    rare_tags = sorted([tag for tag, n in tag_counts.items() if n == 1])
    lines.extend(
        [
            "",
            "### Coverage Gaps",
            f"- Tags with only 1 project: {', '.join(rare_tags[:20]) if rare_tags else 'none'}",
        ]
    )
    if GRAPH_COVERAGE_PATH.exists():
        lines.append("- See `docs/knowledge_graph_coverage.md` for Layer 3 coverage metrics")
    if GAPS_PATH.exists():
        lines.append("- See `docs/knowledge_gaps.md` for prioritized graph-derived opportunities")
    return "\n".join(lines)


def _entity_file_for_type(entity_type: str) -> tuple[Path, str] | None:
    mapping = {
        "organism": (KNOWLEDGE_DIR / "entities/organisms.yaml", "organisms"),
        "gene": (KNOWLEDGE_DIR / "entities/genes.yaml", "genes"),
        "pathway": (KNOWLEDGE_DIR / "entities/pathways.yaml", "pathways"),
        "method": (KNOWLEDGE_DIR / "entities/methods.yaml", "methods"),
        "concept": (KNOWLEDGE_DIR / "entities/concepts.yaml", "concepts"),
    }
    return mapping.get(entity_type)


def _render_entities(entity_type: str, query: str | None) -> str:
    config = _entity_file_for_type(entity_type)
    if config is None:
        return "Valid types: organism, gene, pathway, method, concept"
    path, root_key = config
    rows = _load_knowledge_list(path, root_key)
    if query:
        ql = query.lower()
        filtered = []
        for row in rows:
            hay = " ".join(
                [
                    str(row.get("id", "")),
                    str(row.get("name", "")),
                    str(row.get("description", "")),
                    str(row.get("definition", "")),
                    str(row.get("role", "")),
                    " ".join(str(p) for p in row.get("projects", []) if str(p)),
                ]
            ).lower()
            if ql in hay:
                filtered.append(row)
        rows = filtered

    rows.sort(key=lambda r: str(r.get("id", "")))
    lines = [f"### {entity_type.title()} Entities ({len(rows)} total)", "", "| ID | Name | Projects | Description |", "|---|---|---|---|"]
    for row in rows[:100]:
        rid = str(row.get("id", ""))
        name = str(row.get("name", ""))
        proj_n = len(row.get("projects", []) or [])
        desc = str(row.get("description") or row.get("definition") or row.get("role") or "")
        desc = " ".join(desc.split())
        if len(desc) > 90:
            desc = desc[:89] + "…"
        lines.append(f"| {rid} | {name} | {proj_n} | {desc} |")
    return "\n".join(lines)


def _render_connections(entity: str) -> str:
    relations = _load_knowledge_list(KNOWLEDGE_DIR / "relations.yaml", "relations")
    outgoing = []
    incoming = []
    needle = entity.lower()
    for rel in relations:
        subj = str(rel.get("subject", ""))
        obj = str(rel.get("object", ""))
        if needle in subj.lower():
            outgoing.append(rel)
        if needle in obj.lower():
            incoming.append(rel)
    outgoing.sort(key=lambda r: (str(r.get("predicate", "")), str(r.get("object", ""))))
    incoming.sort(key=lambda r: (str(r.get("predicate", "")), str(r.get("subject", ""))))

    lines = [f"### Connections for {entity}", ""]
    lines.extend(["**Outgoing relations (this entity → other):**", "| Predicate | Target | Evidence Project | Confidence | Note |", "|---|---|---|---|---|"])
    for r in outgoing[:80]:
        lines.append(
            f"| {r.get('predicate','')} | {r.get('object','')} | {r.get('evidence_project','')} | {r.get('confidence','')} | {str(r.get('note','')).replace('|','/')} |"
        )
    if not outgoing:
        lines.append("| _none_ |  |  |  |  |")

    lines.extend(["", "**Incoming relations (other → this entity):**", "| Source | Predicate | Evidence Project | Confidence | Note |", "|---|---|---|---|---|"])
    for r in incoming[:80]:
        lines.append(
            f"| {r.get('subject','')} | {r.get('predicate','')} | {r.get('evidence_project','')} | {r.get('confidence','')} | {str(r.get('note','')).replace('|','/')} |"
        )
    if not incoming:
        lines.append("| _none_ |  |  |  |  |")
    return "\n".join(lines)


def _render_hypotheses(status: str | None) -> str:
    hypotheses = _load_knowledge_list(KNOWLEDGE_DIR / "hypotheses.yaml", "hypotheses")
    if status:
        hypotheses = [h for h in hypotheses if str(h.get("status", "")).lower() == status.lower()]
    hypotheses.sort(key=lambda h: str(h.get("id", "")))

    lines = [f"### Hypotheses ({status or 'all'})", "", "| ID | Status | Statement | Origin Project | Evidence |", "|---|---|---|---|---|"]
    for h in hypotheses:
        statement = " ".join(str(h.get("statement", "")).split())
        if len(statement) > 80:
            statement = statement[:79] + "…"
        sup_n = len(h.get("evidence_supporting", []) or [])
        con_n = len(h.get("evidence_contradicting", []) or [])
        lines.append(
            f"| {h.get('id','')} | {h.get('status','')} | {statement} | {h.get('origin_project','')} | {sup_n} supporting, {con_n} contradicting |"
        )
    if not hypotheses:
        lines.append("| _none_ |  |  |  |  |")
    return "\n".join(lines)


def _render_gaps(registry: dict) -> str:
    if GAPS_PATH.exists():
        return GAPS_PATH.read_text(encoding="utf-8").strip()

    module_path = REPO_ROOT / "scripts" / "build_registry.py"
    spec = importlib.util.spec_from_file_location("build_registry", module_path)
    if not spec or not spec.loader:
        return "Could not load `scripts/build_registry.py`."
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        projects = []
    return module.generate_knowledge_gaps(projects).strip()


def _render_timeline(project_filter: str | None) -> str:
    events = _load_knowledge_list(KNOWLEDGE_DIR / "timeline.yaml", "events")
    filtered = []
    for ev in events:
        project = str(ev.get("project", "")).strip()
        projects = [str(p).strip() for p in (ev.get("projects") or []) if str(p).strip()]
        if project_filter:
            target = project_filter.strip()
            if target != project and target not in projects:
                continue
        filtered.append(ev)
    filtered.sort(key=lambda e: (str(e.get("date", "")), str(e.get("type", "")), str(e.get("ref", ""))))

    suffix = f" for {project_filter}" if project_filter else ""
    lines = [f"### Research Timeline{suffix}", "", "| Date | Type | Project | Summary |", "|---|---|---|---|"]
    for ev in filtered:
        project = str(ev.get("project", "")).strip()
        if not project:
            project = ", ".join(str(p).strip() for p in (ev.get("projects") or []) if str(p).strip())
        summary = " ".join(str(ev.get("summary", "")).split()).replace("|", "/")
        lines.append(f"| {ev.get('date','')} | {ev.get('type','')} | {project} | {summary} |")
    if not filtered:
        lines.append("| _none_ |  |  |  |")
    return "\n".join(lines)


def _render_backfill(project_id: str | None = None) -> str:
    """List projects missing Layer 3 graph coverage."""
    registry, _, _ = _require_registry_artifacts()
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        projects = []

    # Collect projects referenced in timeline events
    timeline_events = _load_knowledge_list(KNOWLEDGE_DIR / "timeline.yaml", "events")
    timeline_projects: set[str] = set()
    for event in timeline_events:
        project = str(event.get("project", "")).strip()
        if project:
            timeline_projects.add(project)
        for pid in event.get("projects") or []:
            pid_text = str(pid).strip()
            if pid_text:
                timeline_projects.add(pid_text)

    # Collect projects referenced in relations
    relations = _load_knowledge_list(KNOWLEDGE_DIR / "relations.yaml", "relations")
    relation_projects: set[str] = set()
    for rel in relations:
        ep = str(rel.get("evidence_project", "")).strip()
        if ep:
            relation_projects.add(ep)

    coverage_rows = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", ""))
        status = str(p.get("status", "unknown"))
        has_timeline = pid in timeline_projects
        has_relations = pid in relation_projects
        coverage_rows.append((pid, status, has_timeline, has_relations))

    if project_id:
        target = next((row for row in coverage_rows if row[0] == project_id), None)
        if target is None:
            return f"Project `{project_id}` not found in the registry."

        pid, status, has_timeline, has_relations = target
        lines = [f"### Layer 3 Coverage for {pid}", "", f"- Status: `{status}`"]
        if has_timeline or has_relations:
            coverage_bits = []
            if has_timeline:
                coverage_bits.append("timeline events")
            if has_relations:
                coverage_bits.append("relation edges")
            lines.append(
                f"- `{pid}` already has Layer 3 coverage via {', '.join(coverage_bits)}."
            )
        else:
            lines.append(
                f"- `{pid}` is missing Layer 3 coverage because it has no timeline events and no relation edges."
            )
        return "\n".join(lines)

    missing = [
        (pid, status)
        for pid, status, has_timeline, has_relations in coverage_rows
        if not has_timeline and not has_relations
    ]
    missing.sort(key=lambda x: (x[1], x[0]))

    lines = ["### Projects Missing Layer 3 Graph Coverage", ""]
    if not missing:
        lines.append("_All projects have graph coverage._")
    else:
        lines.append(f"{len(missing)} project(s) have no timeline events or relation edges:", )
        lines.append("")
        lines.append("| Project | Status |")
        lines.append("|---|---|")
        for pid, status in missing:
            lines.append(f"| {pid} | {status} |")
        lines.append("")
        lines.append("Use `/knowledge backfill <project_id>` to retroactively populate Layer 3.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic knowledge query backend")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Search projects/findings by topic")
    p_search.add_argument("topic")

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
    p_backfill = sub.add_parser("backfill", help="List projects missing Layer 3 graph coverage")
    p_backfill.add_argument("project_id", nargs="?")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Convenience fallback: `query_knowledge.py <topic>` => search
    if args.command is None and len(sys.argv) == 2:
        topic = sys.argv[1]
        registry, _, findings = _require_registry_artifacts()
        print(_render_topic_search(topic, registry, findings))
        return 0

    registry, figures, findings = _require_registry_artifacts()

    if args.command == "search":
        print(_render_topic_search(args.topic, registry, findings))
        return 0
    if args.command == "figures":
        print(_render_figure_search(args.topic, figures))
        return 0
    if args.command == "data":
        print(_render_data_search(args.topic, registry))
        return 0
    if args.command == "project":
        print(_render_project(args.project_id, registry))
        return 0
    if args.command == "landscape":
        print(_render_landscape(registry))
        return 0
    if args.command == "entities":
        print(_render_entities(args.entity_type, args.query))
        return 0
    if args.command == "connections":
        print(_render_connections(args.entity))
        return 0
    if args.command == "hypotheses":
        print(_render_hypotheses(args.status))
        return 0
    if args.command == "gaps":
        print(_render_gaps(registry))
        return 0
    if args.command == "timeline":
        print(_render_timeline(args.project))
        return 0
    if args.command == "backfill":
        print(_render_backfill(args.project_id))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
