"""Deterministic static render of the canonical graph into a small HTML wiki.

Pure, stdlib + Jinja2 only. No LLM, no network (Cytoscape/Mermaid load from pinned CDNs at
view time). Output is byte-stable for a given graph: ordering is sorted, ids are content-addressed.
"""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from compendium import ids
from compendium.models import (
    BIOLOGY_TYPES,
    Edge,
    Graph,
    Node,
    Page,
)

_TEMPLATES = Path(__file__).parent / "templates"
_TIER_BADGE = {
    "grounded": ("green", "grounded"),
    "asserted": ("amber", "asserted"),
    "conflict": ("red", "conflict"),
}
_CYTOSCAPE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"
_MERMAID_CDN = "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"


def safe(node_id: str) -> str:
    """Filesystem/href-safe slug: replace ``:`` and ``/`` with ``_``."""
    return node_id.replace(":", "_").replace("/", "_")


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=select_autoescape(["html", "xml", "html.j2"]),
    )


def _tier_badge(tier: str) -> dict:
    color, label = _TIER_BADGE.get(tier, ("amber", tier))
    return {"color": color, "label": label, "tier": tier}


def _mermaid_label(text: str) -> str:
    """Escape a label for a Mermaid node body (quoted)."""
    return text.replace('"', "'").replace("\n", " ")


def _neighbors(graph: Graph, node: Node) -> list[dict]:
    """Direct facts (edges touching ``node``) as render dicts, sorted deterministically."""
    facts: list[dict] = []
    for edge in graph.edges:
        if edge.s == node.id:
            other = graph.node_by_id(edge.o)
            direction = "out"
        elif edge.o == node.id:
            other = graph.node_by_id(edge.s)
            direction = "in"
        else:
            continue
        facts.append(
            {
                "predicate": edge.p,
                "direction": direction,
                "neighbor_id": other.id if other else (edge.o if direction == "out" else edge.s),
                "neighbor_label": other.label if other else "(unknown)",
                "neighbor_safe": safe(other.id) if other else "",
                "tier": edge.tier,
                "badge": _tier_badge(edge.tier),
                "provenance": list(edge.provenance),
                "evidence": list(edge.evidence),
                "polarity": edge.polarity,
            }
        )
    facts.sort(key=lambda f: (f["predicate"], f["neighbor_id"], f["direction"]))
    return facts


def _fact_strings(node: Node, facts: list[dict]) -> list[str]:
    parts = [f"{node.id}|{node.type}|{node.tier}|{node.curie or ''}"]
    for f in facts:
        parts.append(f"{f['direction']}|{f['predicate']}|{f['neighbor_id']}|{f['tier']}")
    return parts


def _mermaid(node: Node, facts: list[dict]) -> str:
    lines = ["graph TD"]
    nid = safe(node.id)
    lines.append(f'  {nid}["{_mermaid_label(node.label)}"]')
    seen = {nid}
    for f in facts:
        if not f["neighbor_safe"]:
            continue
        oid = f["neighbor_safe"]
        if oid not in seen:
            lines.append(f'  {oid}["{_mermaid_label(f["neighbor_label"])}"]')
            seen.add(oid)
        if f["direction"] == "out":
            lines.append(f'  {nid} -->|{_mermaid_label(f["predicate"])}| {oid}')
        else:
            lines.append(f'  {oid} -->|{_mermaid_label(f["predicate"])}| {nid}')
    return "\n".join(lines)


def _cytoscape_payload(graph: Graph) -> dict:
    nodes = [
        {
            "data": {"id": n.id, "label": n.label, "type": n.type, "tier": n.tier},
            "position": {"x": n.x, "y": n.y},
        }
        for n in sorted(graph.nodes, key=lambda n: n.id)
    ]
    edges = [
        {"data": {"source": e.s, "target": e.o, "label": e.p}}
        for e in sorted(graph.edges, key=lambda e: (e.s, e.p, e.o))
    ]
    return {"nodes": nodes, "edges": edges}


def render_site(graph: Graph, out_dir: Path, narration: dict | None = None) -> list[Page]:
    """Render the canonical graph to a static HTML wiki under ``out_dir``.

    Writes ``index.html``, ``wiki/<safe id>.html`` per node, ``graph.html`` + ``wiki/graph.json``.
    Returns the list of :class:`Page` records (deterministic order, sorted by slug).
    """
    out_dir = Path(out_dir)
    narration = narration or {}
    wiki = out_dir / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)

    env = _env()
    base_ctx = {
        "cytoscape_cdn": _CYTOSCAPE_CDN,
        "mermaid_cdn": _MERMAID_CDN,
    }
    pages: list[Page] = []
    nodes = sorted(graph.nodes, key=lambda n: n.id)

    for node in nodes:
        facts = _neighbors(graph, node)
        fact_strings = _fact_strings(node, facts)
        fact_hash = ids.section_fact_hash(fact_strings)
        slug = safe(node.id)
        cite = narration.get(node.id)
        links = sorted({f["neighbor_safe"] for f in facts if f["neighbor_safe"]})

        ctx = {
            **base_ctx,
            "node": node,
            "badge": _tier_badge(node.tier),
            "facts": facts,
            "mermaid": _mermaid(node, facts),
            "fact_hash": fact_hash,
            "narration": cite,
        }
        template = "entity.html.j2" if node.type in BIOLOGY_TYPES else "synthesis.html.j2"
        html = env.get_template(template).render(**ctx)
        (wiki / f"{slug}.html").write_text(html, encoding="utf-8")

        pages.append(
            Page(
                slug=slug,
                title=node.label,
                type=node.type,
                sections=[{"id": "facts", "heading": "Facts", "fact_hash": fact_hash}],
                links=links,
                fact_hash=fact_hash,
            )
        )

    # graph.json + graph.html
    payload = _cytoscape_payload(graph)
    (wiki / "graph.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    graph_html = env.get_template("graph.html.j2").render(
        **base_ctx, graph_json=json.dumps(payload, sort_keys=True)
    )
    (out_dir / "graph.html").write_text(graph_html, encoding="utf-8")

    # index
    tier_counts: dict[str, int] = {}
    for n in graph.nodes:
        tier_counts[n.tier] = tier_counts.get(n.tier, 0) + 1
    tier_dist = [
        {"badge": _tier_badge(t), "count": tier_counts[t]} for t in sorted(tier_counts)
    ]
    entries = [
        {
            "slug": safe(n.id),
            "label": n.label,
            "type": n.type,
            "badge": _tier_badge(n.tier),
        }
        for n in nodes
    ]
    index_html = env.get_template("index.html.j2").render(
        **base_ctx,
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        tier_dist=tier_dist,
        entries=entries,
    )
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    return pages
