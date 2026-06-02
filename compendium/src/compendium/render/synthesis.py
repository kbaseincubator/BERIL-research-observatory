"""Deterministic HTML render for v4 synthesis-wiki page plans."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from compendium.models import PagePlan, PageSectionPlan, StatementCard
from compendium.pages import page_id_for_statement

_TEMPLATES = Path(__file__).parent / "templates"
_GRAPH_FILENAME = "graph.html"
_LINK_FIELDS = (
    "supports",
    "contradicts",
    "motivates",
    "refines",
    "requires_validation",
)


def render_synthesis_site(
    cards: list[StatementCard],
    page_plans: list[PagePlan],
    out_dir: Path,
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
) -> list[Path]:
    """Render v4 ``PagePlan`` and ``StatementCard`` artifacts to static HTML.

    The home page is written to ``index.html``. Other page ids are written to a
    stable, filesystem-safe filename in ``out_dir``. Output is byte-stable for
    a fixed set of cards and page plans.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    card_by_id = _unique_by_id(cards, "card")
    plan_by_id = _unique_by_id(page_plans, "page plan")
    page_paths = _page_paths(plan_by_id)
    env = _env()
    graph_href = _GRAPH_FILENAME if statement_graph is not None else None
    if graph_href in page_paths.values():
        raise ValueError(
            f"graph view renders to the same filename {graph_href!r} as a page plan"
        )

    template = env.get_template("synthesis_page.html.j2")

    rendered: list[Path] = []
    for plan in sorted(page_plans, key=_plan_sort_key):
        path = out_dir / page_paths[plan.id]
        html = template.render(
            page=_page_view(plan, card_by_id, page_paths, graph_href),
            generated_index=False,
        )
        path.write_text(html, encoding="utf-8")
        rendered.append(path)

    if "home" not in plan_by_id:
        index_path = out_dir / "index.html"
        html = template.render(
            page=_index_view(page_plans, page_paths, graph_href),
            generated_index=True,
        )
        index_path.write_text(html, encoding="utf-8")
        rendered.insert(0, index_path)

    if statement_graph is not None:
        graph_path = out_dir / _GRAPH_FILENAME
        graph_template = env.get_template("synthesis_graph.html.j2")
        html = graph_template.render(graph=_graph_view(statement_graph, page_paths))
        graph_path.write_text(html, encoding="utf-8")
        rendered.append(graph_path)

    return rendered


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=select_autoescape(["html", "xml", "html.j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _unique_by_id(items: Iterable[Any], label: str) -> dict[str, Any]:
    by_id: dict[str, Any] = {}
    for item in items:
        if item.id in by_id:
            raise ValueError(f"duplicate {label} id: {item.id}")
        by_id[item.id] = item
    return by_id


def _page_view(
    plan: PagePlan,
    card_by_id: dict[str, StatementCard],
    page_paths: dict[str, str],
    graph_href: str | None,
) -> dict[str, Any]:
    member_ids = _unique_preserving_order(plan.member_statement_ids)
    member_cards = [_statement_view(card_by_id[sid], page_paths) for sid in member_ids if sid in card_by_id]
    missing_members = [sid for sid in member_ids if sid not in card_by_id]
    return {
        "id": plan.id,
        "type": plan.type,
        "title": plan.title,
        "path": page_paths[plan.id],
        "member_hash": plan.member_hash,
        "sections": [
            _section_view(section, card_by_id, page_paths)
            for section in plan.sections
        ],
        "statements": member_cards,
        "missing_members": missing_members,
        "source_projects": _source_projects(member_cards, page_paths),
        "outgoing_links": _page_links(plan.outgoing_links, page_paths),
        "backlinks": _page_links(plan.backlinks, page_paths),
        "all_pages": _page_links(page_paths, page_paths),
        "graph_href": graph_href,
    }


def _index_view(
    page_plans: list[PagePlan],
    page_paths: dict[str, str],
    graph_href: str | None,
) -> dict[str, Any]:
    return {
        "id": "home",
        "type": "index",
        "title": "Synthesis Wiki",
        "path": "index.html",
        "member_hash": "",
        "sections": [],
        "statements": [],
        "missing_members": [],
        "source_projects": [],
        "outgoing_links": [
            {
                "id": plan.id,
                "title": plan.title,
                "type": plan.type,
                "href": page_paths[plan.id],
                "missing": False,
            }
            for plan in sorted(page_plans, key=_plan_sort_key)
        ],
        "backlinks": [],
        "all_pages": _page_links(page_paths, page_paths),
        "graph_href": graph_href,
    }


def _graph_view(
    statement_graph: dict[str, list[dict[str, Any]]],
    page_paths: dict[str, str],
) -> dict[str, Any]:
    nodes = [
        _graph_node_view(node, page_paths)
        for node in sorted(statement_graph.get("nodes", []), key=_graph_node_sort_key)
    ]
    node_by_id = {node["id"]: node for node in nodes}
    edges = [
        _graph_edge_view(edge, node_by_id)
        for edge in sorted(statement_graph.get("edges", []), key=_graph_edge_sort_key)
    ]
    return {
        "title": "Synthesis Graph",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "statement_nodes": [node for node in nodes if node["type"] == "statement_card"],
        "edges": edges,
        "all_pages": _page_links(page_paths, page_paths),
    }


def _graph_node_view(node: dict[str, Any], page_paths: dict[str, str]) -> dict[str, Any]:
    node_id = str(node["id"])
    attrs = node.get("attrs", {})
    return {
        "id": node_id,
        "type": str(node["type"]),
        "label": str(node.get("label") or node_id),
        "href": _graph_node_href(node_id, page_paths),
        "kind": attrs.get("kind"),
        "confidence": attrs.get("confidence"),
    }


def _graph_edge_view(
    edge: dict[str, Any],
    node_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id = str(edge["s"])
    target_id = str(edge["o"])
    source = node_by_id.get(source_id, _graph_endpoint_fallback(source_id))
    target = node_by_id.get(target_id, _graph_endpoint_fallback(target_id))
    edge_class = str(edge["edge_class"])
    predicate = str(edge["p"])
    return {
        "id": str(edge["id"]),
        "edge_class": edge_class,
        "edge_class_css": _safe_css_class(edge_class),
        "predicate": predicate,
        "source": source,
        "target": target,
        "statement_ids": sorted(
            str(statement_id) for statement_id in edge.get("statement_ids", [])
        ),
    }


def _graph_endpoint_fallback(node_id: str) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": "missing",
        "label": node_id,
        "href": None,
        "kind": None,
        "confidence": None,
    }


def _section_view(
    section: PageSectionPlan,
    card_by_id: dict[str, StatementCard],
    page_paths: dict[str, str],
) -> dict[str, Any]:
    member_ids = _unique_preserving_order(section.member_statement_ids)
    return {
        "id": _safe_fragment(section.id),
        "heading": section.heading,
        "member_hash": section.member_hash,
        "statements": [
            _statement_ref(card_by_id[sid], page_paths)
            for sid in member_ids
            if sid in card_by_id
        ],
        "missing_members": [sid for sid in member_ids if sid not in card_by_id],
    }


def _statement_view(card: StatementCard, page_paths: dict[str, str]) -> dict[str, Any]:
    evidence = card.evidence
    source_project_page_id = f"project:{evidence.source_project}"
    return {
        "id": card.id,
        "anchor": _statement_anchor(card.id),
        "kind": card.kind,
        "statement": card.statement,
        "scope": card.scope,
        "tier": card.tier,
        "confidence": card.confidence,
        "topics": _page_links(card.about.topics, page_paths),
        "entities": _page_links(card.about.entities, page_paths),
        "qualifiers": sorted(card.qualifiers.items()),
        "links": [
            {
                "kind": field_name.replace("_", " "),
                "targets": [
                    _statement_link(target_id, page_paths)
                    for target_id in sorted(set(getattr(card.links, field_name)))
                ],
            }
            for field_name in _LINK_FIELDS
            if getattr(card.links, field_name)
        ],
        "evidence": {
            "source_project": evidence.source_project,
            "source_project_href": page_paths.get(source_project_page_id),
            "source_doc": evidence.source_doc,
            "source_section": evidence.source_section,
            "exact": evidence.exact,
            "notebook": evidence.notebook,
            "figure": evidence.figure,
            "p_value": evidence.p_value,
        },
        "extraction": {
            "skill": card.extraction.skill,
            "model": card.extraction.model,
            "timestamp": card.extraction.timestamp,
            "repo_commit": card.extraction.repo_commit,
        },
    }


def _statement_ref(card: StatementCard, page_paths: dict[str, str]) -> dict[str, str | None]:
    statement_page_id = page_id_for_statement(card)
    href = page_paths.get(statement_page_id) if statement_page_id else None
    return {
        "id": card.id,
        "kind": card.kind,
        "statement": card.statement,
        "href": href,
        "anchor": _statement_anchor(card.id),
    }


def _statement_link(target_id: str, page_paths: dict[str, str]) -> dict[str, str | None]:
    href = None
    if ":" in target_id:
        suffix = target_id.split(":", 1)[1]
        for prefix in ("claim", "opportunity"):
            if prefix_href := page_paths.get(f"{prefix}:{suffix}"):
                href = prefix_href
                break
    return {
        "id": target_id,
        "href": href,
    }


def _graph_node_href(node_id: str, page_paths: dict[str, str]) -> str | None:
    if href := page_paths.get(node_id):
        return href
    if not node_id.startswith("stmt:"):
        return None
    return _statement_link(node_id, page_paths)["href"]


def _source_projects(member_cards: list[dict[str, Any]], page_paths: dict[str, str]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for card in member_cards:
        evidence = card["evidence"]
        project_id = evidence["source_project"]
        project = grouped.setdefault(
            project_id,
            {
                "id": project_id,
                "href": page_paths.get(f"project:{project_id}"),
                "statement_count": 0,
                "documents": set(),
            },
        )
        project["statement_count"] += 1
        project["documents"].add(evidence["source_doc"])
    return [
        {
            "id": project_id,
            "href": project["href"],
            "statement_count": project["statement_count"],
            "documents": sorted(project["documents"]),
        }
        for project_id, project in sorted(grouped.items())
    ]


def _page_links(page_ids: Iterable[str] | dict[str, str], page_paths: dict[str, str]) -> list[dict[str, Any]]:
    ids = page_ids.keys() if isinstance(page_ids, dict) else page_ids
    return [
        {
            "id": page_id,
            "href": page_paths.get(page_id),
            "missing": page_id not in page_paths,
        }
        for page_id in sorted(set(ids))
    ]


def _page_paths(plan_by_id: dict[str, PagePlan]) -> dict[str, str]:
    page_paths: dict[str, str] = {}
    filename_to_page_id: dict[str, str] = {}
    for page_id in sorted(plan_by_id):
        filename = _page_filename(page_id)
        if existing_page_id := filename_to_page_id.get(filename):
            raise ValueError(
                f"page ids {existing_page_id!r} and {page_id!r} render to the same filename {filename!r}"
            )
        page_paths[page_id] = filename
        filename_to_page_id[filename] = page_id
    return page_paths


def _page_filename(page_id: str) -> str:
    if page_id == "home":
        return "index.html"
    return f"{_safe_page_id(page_id)}.html"


def _safe_page_id(page_id: str) -> str:
    return page_id.replace(":", "_").replace("/", "_")


def _safe_fragment(value: str) -> str:
    return _safe_page_id(value).replace(" ", "_")


def _statement_anchor(statement_id: str) -> str:
    return f"statement-{_safe_fragment(statement_id)}"


def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _plan_sort_key(plan: PagePlan) -> tuple[int, str]:
    return (0 if plan.id == "home" else 1, plan.id)


def _graph_node_sort_key(node: dict[str, Any]) -> tuple[str, str]:
    return (str(node.get("type", "")), str(node.get("id", "")))


def _graph_edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(edge.get("edge_class", "")),
        str(edge.get("p", "")),
        str(edge.get("s", "")),
        str(edge.get("o", "")),
        str(edge.get("id", "")),
    )


def _safe_css_class(value: str) -> str:
    return _safe_page_id(value).replace(" ", "_")
