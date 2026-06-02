"""Markdown wiki export for statement-card synthesis pages."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import re
from typing import Any

from compendium.models import PagePlan, StatementCard
from compendium.pages.plan import page_id_for_statement

_PAGE_DIRS = {
    "topic": "topics",
    "claim": "claims",
    "conflict": "conflicts",
    "opportunity": "opportunities",
    "direction": "directions",
    "hypothesis": "hypotheses",
    "project": "projects",
    "entity": "entities",
}
_LINK_FIELDS = (
    "supports",
    "contradicts",
    "motivates",
    "refines",
    "requires_validation",
)


def render_markdown_wiki(
    cards: list[StatementCard],
    page_plans: list[PagePlan],
    out_dir: str | Path,
    *,
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
) -> list[Path]:
    """Render a linked Markdown wiki from deterministic page plans."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    card_by_id = {card.id: card for card in cards}
    page_paths = _page_paths(page_plans)

    written: list[Path] = []
    for plan in sorted(page_plans, key=_plan_sort_key):
        path = out_path / page_paths[plan.id]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _render_page(plan, card_by_id, page_paths, statement_graph),
            encoding="utf-8",
        )
        written.append(path)

    graph_path = out_path / "graph.md"
    graph_path.write_text(
        _render_graph(page_plans, page_paths, statement_graph),
        encoding="utf-8",
    )
    written.append(graph_path)
    return written


def render_markdown_page(
    plan: PagePlan,
    cards: list[StatementCard],
    *,
    page_plans: list[PagePlan] | None = None,
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    """Render one prose-first Markdown wiki page from a fixed page plan."""
    plans = list(page_plans) if page_plans is not None else [plan]
    if plan.id not in {item.id for item in plans}:
        plans.append(plan)
    card_by_id = {card.id: card for card in cards}
    return _render_page(plan, card_by_id, _page_paths(plans), statement_graph)


def _render_page(
    plan: PagePlan,
    card_by_id: dict[str, StatementCard],
    page_paths: dict[str, Path],
    statement_graph: dict[str, list[dict[str, Any]]] | None,
) -> str:
    current_path = page_paths[plan.id]
    member_cards = [
        card_by_id[statement_id]
        for statement_id in plan.member_statement_ids
        if statement_id in card_by_id
    ]
    lines = [
        "---",
        f"page_id: {plan.id}",
        f"page_type: {plan.type}",
        f"member_hash: {plan.member_hash}",
        "---",
        "",
        f"# {plan.title}",
        "",
        f"- Page type: `{plan.type}`",
        f"- Member hash: `{plan.member_hash}`",
        f"- Graph: {_link('Graph', Path('graph.md'), page_paths[plan.id])}",
        "",
    ]

    lines.extend(_narrative_sections(plan, member_cards, page_paths, current_path))

    lines.extend(["## Structured Evidence Summary", ""])
    for section in sorted(plan.sections, key=lambda item: item.id):
        lines.extend([f"### {section.heading}", ""])
        section_cards = [
            card_by_id[statement_id]
            for statement_id in section.member_statement_ids
            if statement_id in card_by_id
        ]
        if not section_cards:
            lines.extend(["No statements selected for this section.", ""])
            continue
        for card in section_cards:
            lines.append(_statement_summary(card, page_paths, page_paths[plan.id]))
        lines.append("")

    lines.extend(_page_link_section("Outgoing Links", plan.outgoing_links, page_paths, current_path))
    lines.extend(_page_link_section("Backlinks", plan.backlinks, page_paths, current_path))

    lines.extend(["## Source Statements", ""])
    for card in sorted(member_cards, key=lambda item: item.id):
        lines.extend(_statement_detail(card, page_paths, page_paths[plan.id]))

    local_edges = _local_edges(plan, statement_graph)
    lines.extend(["## Local Graph", ""])
    if local_edges:
        for edge in local_edges:
            lines.append(
                "- "
                f"`{edge.get('edge_class')}` `{edge.get('p')}`: "
                f"`{edge.get('s')}` -> `{edge.get('o')}`"
            )
    else:
        lines.append("No local statement-graph edges.")
    lines.append("")
    return "\n".join(lines)


def _narrative_sections(
    plan: PagePlan,
    member_cards: list[StatementCard],
    page_paths: dict[str, Path],
    current_path: Path,
) -> list[str]:
    if not member_cards:
        return [
            "## Introduction",
            "",
            (
                "This page exists in the synthesis graph but currently has no selected "
                "statement cards. It is retained as a navigation target until future "
                "ingestion adds evidence-backed content."
            ),
            "",
        ]

    projects = sorted({card.evidence.source_project for card in member_cards})
    kinds = _cards_by_kind(member_cards)
    citations = ", ".join(_citation(card) for card in member_cards[:4])
    if len(member_cards) > 4:
        citations += f", and {len(member_cards) - 4} more"

    lines = ["## Introduction", ""]
    if plan.type == "home":
        topic_links = _links_for_page_type("topic", page_paths, current_path)
        project_links = _links_for_page_type("project", page_paths, current_path)
        lines.extend(
            [
                (
                    f"This wiki synthesizes {len(member_cards)} evidence-backed statement "
                    f"cards from {len(projects)} source projects into a connected reading "
                    "surface. It is organized around reusable claims, topic pages, project "
                    "pages, opportunities for follow-up work, and entity backlink pages."
                ),
                "",
                (
                    "A useful reading path is to start with the topic pages "
                    f"({', '.join(topic_links)}) and then follow the claim and opportunity "
                    f"links back to the contributing projects ({', '.join(project_links)})."
                ),
                "",
            ]
        )
    elif plan.type == "topic":
        lines.extend(
            [
                (
                    f"This topic summarizes {len(member_cards)} statements from "
                    f"{_project_phrase(projects)}. The page combines findings, reusable "
                    "claims, caveats, and future work so readers can understand the state "
                    "of the topic without opening each source project first."
                ),
                "",
            ]
        )
    elif plan.type == "claim":
        claim = _first_kind(kinds, "claim") or member_cards[0]
        lines.extend(
            [
                (
                    f"This claim page evaluates the statement: {claim.statement} "
                    f"{_citation(claim)}. It collects supporting findings, caveats, and "
                    "downstream uses selected by the deterministic page plan."
                ),
                "",
            ]
        )
    elif plan.type == "opportunity":
        opportunity = _first_kind(kinds, "opportunity") or member_cards[0]
        lines.extend(
            [
                (
                    f"This opportunity proposes a concrete next step: {opportunity.statement} "
                    f"{_citation(opportunity)}. The surrounding links identify the claims "
                    "or findings that motivate the work and the project context that would "
                    "make the work actionable."
                ),
                "",
            ]
        )
    elif plan.type == "project":
        lines.extend(
            [
                (
                    f"This project page summarizes the extractable scientific contribution "
                    f"from `{projects[0]}`. It records {len(member_cards)} statement cards "
                    "and connects them to shared topics, entities, claims, and opportunities "
                    "elsewhere in the wiki."
                ),
                "",
            ]
        )
    elif plan.type == "entity":
        lines.extend(
            [
                (
                    f"This entity page is a backlink hub for {plan.title}. It gathers "
                    f"{len(member_cards)} statements from {_project_phrase(projects)} and "
                    "shows how the entity participates in findings, claims, caveats, and "
                    "opportunities across the wiki."
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                (
                    f"This page synthesizes {len(member_cards)} statements from "
                    f"{_project_phrase(projects)}. The content below is constrained to "
                    "the selected statement cards and their evidence anchors."
                ),
                "",
            ]
        )

    lines.extend(["## Synthesis", ""])
    claim_cards = kinds.get("claim", [])
    finding_cards = kinds.get("finding", [])
    caveat_cards = kinds.get("caveat", []) + kinds.get("conflict", [])
    opportunity_cards = kinds.get("opportunity", [])

    if claim_cards:
        lines.append(_prose_sentence("The central claim is", claim_cards, page_paths, current_path))
    if finding_cards:
        lines.append(_prose_sentence("The main evidence base is", finding_cards, page_paths, current_path))
    if caveat_cards:
        lines.append(_prose_sentence("The page should be read with the following caveat", caveat_cards, page_paths, current_path))
    if opportunity_cards:
        lines.append(_prose_sentence("The most direct follow-up work is", opportunity_cards, page_paths, current_path))
    if not any((claim_cards, finding_cards, caveat_cards, opportunity_cards)):
        lines.append(
            f"The selected evidence is represented by {citations}. These statements are "
            "kept together because the page plan links them through shared topics, entities, "
            "or statement relationships."
        )
    lines.append("")

    lines.extend(["## Navigation Context", ""])
    lines.append(
        f"This page links out to {len(plan.outgoing_links)} related pages and has "
        f"{len(plan.backlinks)} backlinks. Use those links to move between the prose note, "
        "the underlying evidence, and the graph neighborhood."
    )
    lines.append("")
    return lines


def _prose_sentence(
    lead: str,
    cards: list[StatementCard],
    page_paths: dict[str, Path],
    current_path: Path,
) -> str:
    shown = cards[:3]
    clauses = [
        (
            f"{_statement_page_link(card, page_paths, current_path)} "
            f"states that {card.statement} {_citation(card)}."
        )
        for card in shown
    ]
    extra = "" if len(cards) <= 3 else f" {len(cards) - 3} additional statements support this reading."
    if lead == "The central claim is":
        intro = _count_intro(
            cards,
            singular="A central reusable claim frames this page.",
            plural="Reusable claims frame this page.",
        )
    elif lead == "The main evidence base is":
        intro = _count_intro(
            cards,
            singular="The evidence base is anchored by one finding.",
            plural="The evidence base is anchored by several findings.",
        )
    elif lead == "The page should be read with the following caveat":
        intro = _count_intro(
            cards,
            singular="The synthesis should be read with one caveat.",
            plural="The synthesis should be read with several caveats.",
        )
    else:
        intro = _count_intro(
            cards,
            singular="The most direct follow-up work is a concrete opportunity.",
            plural="The most direct follow-up work spans several opportunities.",
        )
    return f"{intro} {' '.join(clauses)}{extra}"


def _count_intro(
    cards: list[StatementCard],
    *,
    singular: str,
    plural: str,
) -> str:
    return singular if len(cards) == 1 else plural


def _cards_by_kind(cards: list[StatementCard]) -> dict[str, list[StatementCard]]:
    grouped: dict[str, list[StatementCard]] = {}
    for card in sorted(cards, key=lambda item: item.id):
        grouped.setdefault(card.kind, []).append(card)
    return grouped


def _first_kind(
    grouped: dict[str, list[StatementCard]],
    kind: str,
) -> StatementCard | None:
    cards = grouped.get(kind)
    return cards[0] if cards else None


def _citation(card: StatementCard) -> str:
    return f"[{card.id}; {card.evidence.source_project}]"


def _project_phrase(projects: list[str]) -> str:
    if len(projects) == 1:
        return f"`{projects[0]}`"
    if len(projects) == 2:
        return f"`{projects[0]}` and `{projects[1]}`"
    return ", ".join(f"`{project}`" for project in projects[:-1]) + f", and `{projects[-1]}`"


def _links_for_page_type(
    page_type: str,
    page_paths: dict[str, Path],
    current_path: Path,
) -> list[str]:
    links = [
        _link(_title(page_id), path, current_path)
        for page_id, path in sorted(page_paths.items())
        if page_id.startswith(f"{page_type}:")
    ]
    return links or [f"no {page_type} pages yet"]


def _render_graph(
    page_plans: list[PagePlan],
    page_paths: dict[str, Path],
    statement_graph: dict[str, list[dict[str, Any]]] | None,
) -> str:
    graph = statement_graph or {"nodes": [], "edges": []}
    lines = [
        "# Graph",
        "",
        f"- Nodes: {len(graph.get('nodes', []))}",
        f"- Edges: {len(graph.get('edges', []))}",
        "",
        "## Pages",
        "",
    ]
    for plan in sorted(page_plans, key=_plan_sort_key):
        lines.append(
            f"- {_link(plan.title, page_paths[plan.id], Path('graph.md'))} "
            f"`{plan.type}` `{plan.id}`"
        )
    lines.extend(["", "## Edge Classes", ""])
    counts: dict[str, int] = {}
    for edge in graph.get("edges", []):
        edge_class = str(edge.get("edge_class", "unknown"))
        counts[edge_class] = counts.get(edge_class, 0) + 1
    if counts:
        for edge_class in sorted(counts):
            lines.append(f"- `{edge_class}`: {counts[edge_class]}")
    else:
        lines.append("No graph edges.")
    lines.append("")
    return "\n".join(lines)


def _page_link_section(
    heading: str,
    page_ids: Iterable[str],
    page_paths: dict[str, Path],
    current_path: Path,
) -> list[str]:
    lines = [f"## {heading}", ""]
    links = [
        _link(_title(page_id), page_paths[page_id], current_path)
        for page_id in sorted(set(page_ids))
        if page_id in page_paths
    ]
    if links:
        lines.extend(f"- {link}" for link in links)
    else:
        lines.append(f"No {heading.lower()}.")
    lines.append("")
    return lines


def _statement_summary(
    card: StatementCard,
    page_paths: dict[str, Path],
    current_path: Path,
) -> str:
    statement_page = _statement_page_link(card, page_paths, current_path)
    return (
        "- "
        f"{statement_page}: {card.statement} "
        f"`{card.kind}` `{card.tier}` `{card.confidence}` "
        f"({card.evidence.source_project}/{card.evidence.source_doc})"
    )


def _statement_detail(
    card: StatementCard,
    page_paths: dict[str, Path],
    current_path: Path,
) -> list[str]:
    lines = [
        f"### {card.id}",
        "",
        f"{card.statement}",
        "",
        f"- Kind/tier/confidence: `{card.kind}` / `{card.tier}` / `{card.confidence}`",
        f"- Scope: `{card.scope}`",
        f"- Source: `{card.evidence.source_project}/{card.evidence.source_doc}`",
        f"- Section: `{card.evidence.source_section or ''}`",
        f"- Evidence: {card.evidence.exact}",
    ]
    if card.evidence.figure:
        lines.append(f"- Figure: `{card.evidence.figure}`")
    if card.evidence.notebook:
        lines.append(f"- Notebook: `{card.evidence.notebook}`")
    topic_links = [
        _link(_title(topic_id), page_paths[topic_id], current_path)
        for topic_id in sorted(set(card.about.topics))
        if topic_id in page_paths
    ]
    entity_links = [
        _link(_title(entity_id), page_paths[entity_id], current_path)
        for entity_id in sorted(set(card.about.entities))
        if entity_id in page_paths
    ]
    if topic_links:
        lines.append(f"- Topics: {', '.join(topic_links)}")
    if entity_links:
        lines.append(f"- Entities: {', '.join(entity_links)}")

    for field_name in _LINK_FIELDS:
        targets = sorted(set(getattr(card.links, field_name)))
        if not targets:
            continue
        lines.append(
            f"- {field_name.replace('_', ' ').title()}: "
            + ", ".join(_statement_target_link(target, page_paths, current_path) for target in targets)
        )
    lines.append("")
    return lines


def _statement_page_link(
    card: StatementCard,
    page_paths: dict[str, Path],
    current_path: Path,
) -> str:
    page_id = page_id_for_statement(card)
    if page_id and page_id in page_paths:
        return _link(card.id, page_paths[page_id], current_path)
    return f"`{card.id}`"


def _statement_target_link(
    statement_id: str,
    page_paths: dict[str, Path],
    current_path: Path,
) -> str:
    suffix = statement_id.split(":", 1)[1] if ":" in statement_id else statement_id
    for prefix in ("claim", "opportunity"):
        page_id = f"{prefix}:{suffix}"
        if page_id in page_paths:
            return _link(statement_id, page_paths[page_id], current_path)
    return f"`{statement_id}`"


def _local_edges(
    plan: PagePlan,
    statement_graph: dict[str, list[dict[str, Any]]] | None,
) -> list[dict[str, Any]]:
    if not statement_graph:
        return []
    local_ids = {plan.id, *plan.member_statement_ids}
    return [
        edge
        for edge in sorted(statement_graph.get("edges", []), key=_edge_sort_key)
        if {
            str(edge.get("s", "")),
            str(edge.get("o", "")),
            *(str(statement_id) for statement_id in edge.get("statement_ids", [])),
        }
        & local_ids
    ]


def _page_paths(page_plans: list[PagePlan]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for plan in sorted(page_plans, key=_plan_sort_key):
        paths[plan.id] = _page_path(plan)
    return paths


def _page_path(plan: PagePlan) -> Path:
    if plan.id == "home":
        return Path("index.md")
    stem = _slug(plan.id.split(":", 1)[1] if ":" in plan.id else plan.id)
    directory = _PAGE_DIRS.get(plan.type, f"{_slug(plan.type)}s")
    return Path(directory) / f"{stem}.md"


def _link(label: str, target_path: Path, current_path: Path) -> str:
    href = _relative_path(current_path, target_path)
    return f"[{label}]({href})"


def _relative_path(current_path: Path, target_path: Path) -> str:
    current_parent = current_path.parent
    if str(current_parent) == ".":
        return target_path.as_posix()
    return Path(*([".."] * len(current_parent.parts)), target_path).as_posix()


def _title(page_id: str) -> str:
    value = page_id.split(":", 1)[1] if ":" in page_id else page_id
    return value.replace("_", " ").replace("-", " ").title()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"


def _plan_sort_key(plan: PagePlan) -> tuple[int, str]:
    return (0 if plan.id == "home" else 1, plan.id)


def _edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(edge.get("edge_class", "")),
        str(edge.get("p", "")),
        str(edge.get("s", "")),
        str(edge.get("o", "")),
        str(edge.get("id", "")),
    )
