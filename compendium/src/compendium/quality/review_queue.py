"""Deterministic review queue ranking for statement cards."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from compendium.models import PagePlan, StatementCard, TIER_RETRACTED

__all__ = ["build_review_queue"]

_LINK_FIELDS = (
    "supports",
    "contradicts",
    "motivates",
    "refines",
    "requires_validation",
)


def build_review_queue(
    cards: Iterable[StatementCard],
    graph: dict[str, list[dict[str, Any]]],
    page_plans: Iterable[PagePlan] | None = None,
    unresolved_statement_links: Iterable[dict[str, Any]] | dict[str, Any] | None = None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Rank active statement-card candidates for curator review.

    Parameters
    ----------
    cards
        Statement cards to rank. Retracted cards are excluded.
    graph
        Statement graph with ``nodes`` and ``edges`` lists.
    page_plans
        Optional synthesis page plans used to report affected wiki pages and
        modestly prioritize statements that are visible in more places.
    unresolved_statement_links
        Optional unresolved-link details, usually
        ``metrics["statement_link_integrity"]["unresolved_statement_links"]``.
        If omitted, unresolved links are inferred from targets absent from the
        active card set.
    limit
        Optional maximum number of records to return.

    Returns
    -------
    list[dict[str, Any]]
        JSON-friendly queue records sorted by descending score, descending graph
        degree, then statement id.
    """
    active_cards = sorted(
        (card for card in cards if card.tier != TIER_RETRACTED),
        key=lambda card: card.id,
    )
    active_ids = {card.id for card in active_cards}
    degrees = _statement_degrees(graph, active_ids)
    high_centrality_threshold = _centrality_threshold(degrees)
    contradictions = _contradictions_by_statement(active_cards)
    unresolved = _unresolved_by_statement(
        active_cards,
        active_ids,
        unresolved_statement_links,
    )
    affected_pages = _affected_pages_by_statement(page_plans or [])

    records = []
    for card in active_cards:
        score, reasons = _score_card(
            card,
            centrality_degree=degrees.get(card.id, 0),
            high_centrality_threshold=high_centrality_threshold,
            contradiction_count=len(contradictions.get(card.id, [])),
            unresolved_link_count=len(unresolved.get(card.id, [])),
            affected_page_count=len(affected_pages.get(card.id, [])),
        )
        if score <= 0:
            continue
        records.append(
            {
                "statement_id": card.id,
                "score": score,
                "reasons": reasons,
                "kind": card.kind,
                "tier": card.tier,
                "confidence": card.confidence,
                "centrality_degree": degrees.get(card.id, 0),
                "statement": card.statement,
                "evidence_summary": _evidence_summary(card),
                "affected_pages": affected_pages.get(card.id, []),
                "contradictions": contradictions.get(card.id, []),
                "unresolved_statement_links": unresolved.get(card.id, []),
            }
        )

    records.sort(
        key=lambda record: (
            -int(record["score"]),
            -int(record["centrality_degree"]),
            str(record["statement_id"]),
        )
    )
    if limit is None:
        return records
    return records[:limit]


def _score_card(
    card: StatementCard,
    *,
    centrality_degree: int,
    high_centrality_threshold: int | None,
    contradiction_count: int,
    unresolved_link_count: int,
    affected_page_count: int,
) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    if card.kind == "conflict" or card.tier == "conflict":
        score += 50
        reasons.append("conflict_status")
    if contradiction_count:
        score += 30 + (10 * contradiction_count)
        reasons.append(f"contradictions:{contradiction_count}")
    if unresolved_link_count:
        score += 25 + (5 * unresolved_link_count)
        reasons.append(f"unresolved_statement_links:{unresolved_link_count}")
    if card.tier == "asserted":
        score += 20
        reasons.append("asserted_tier")
    if card.confidence == "low":
        score += 25
        reasons.append("low_confidence")

    is_high_centrality = (
        high_centrality_threshold is not None
        and centrality_degree >= high_centrality_threshold
    )
    if is_high_centrality:
        reasons.append(f"high_graph_centrality:{centrality_degree}")

    if reasons:
        score += min(centrality_degree * 3, 30)
        if affected_page_count > 1:
            score += min((affected_page_count - 1) * 5, 15)
            reasons.append(f"affected_pages:{affected_page_count}")

    return score, reasons


def _statement_degrees(
    graph: dict[str, list[dict[str, Any]]],
    statement_ids: set[str],
) -> dict[str, int]:
    degree = Counter({statement_id: 0 for statement_id in statement_ids})
    for edge in graph.get("edges", []):
        source = str(edge.get("s", edge.get("source", "")))
        target = str(edge.get("o", edge.get("target", "")))
        if source in statement_ids:
            degree[source] += 1
        if target in statement_ids:
            degree[target] += 1
    return {statement_id: degree[statement_id] for statement_id in sorted(statement_ids)}


def _centrality_threshold(degrees: dict[str, int]) -> int | None:
    if not degrees:
        return None
    highest = max(degrees.values())
    if highest < 2:
        return None
    return max(2, highest)


def _contradictions_by_statement(cards: list[StatementCard]) -> dict[str, list[dict[str, str]]]:
    active_ids = {card.id for card in cards}
    by_statement: dict[str, list[dict[str, str]]] = {card.id: [] for card in cards}
    for card in cards:
        for target_id in sorted(set(card.links.contradicts)):
            link = {
                "source_statement_id": card.id,
                "target_statement_id": target_id,
            }
            by_statement[card.id].append(link)
            if target_id in active_ids:
                by_statement[target_id].append(link)

    return {
        statement_id: sorted(
            links,
            key=lambda link: (
                link["source_statement_id"],
                link["target_statement_id"],
            ),
        )
        for statement_id, links in by_statement.items()
        if links
    }


def _unresolved_by_statement(
    cards: list[StatementCard],
    active_ids: set[str],
    supplied: Iterable[dict[str, Any]] | dict[str, Any] | None,
) -> dict[str, list[dict[str, str]]]:
    links = (
        _derived_unresolved_links(cards, active_ids)
        if supplied is None
        else _normalize_unresolved_links(supplied)
    )
    by_statement: dict[str, list[dict[str, str]]] = {}
    for link in links:
        source_id = link["source_statement_id"]
        if source_id not in active_ids:
            continue
        by_statement.setdefault(source_id, []).append(link)

    return {
        statement_id: sorted(
            statement_links,
            key=lambda link: (
                link["link_kind"],
                link["target_statement_id"],
            ),
        )
        for statement_id, statement_links in by_statement.items()
    }


def _derived_unresolved_links(
    cards: list[StatementCard],
    active_ids: set[str],
) -> list[dict[str, str]]:
    unresolved = []
    for card in cards:
        for field_name in _LINK_FIELDS:
            for target_id in sorted(set(getattr(card.links, field_name))):
                if target_id not in active_ids:
                    unresolved.append(
                        {
                            "source_statement_id": card.id,
                            "link_kind": field_name,
                            "target_statement_id": target_id,
                        }
                    )
    return unresolved


def _normalize_unresolved_links(
    supplied: Iterable[dict[str, Any]] | dict[str, Any],
) -> list[dict[str, str]]:
    if isinstance(supplied, dict):
        if "statement_link_integrity" in supplied:
            supplied = supplied["statement_link_integrity"]
        supplied = supplied.get("unresolved_statement_links", [])

    normalized = []
    for link in supplied:
        normalized.append(
            {
                "source_statement_id": str(link["source_statement_id"]),
                "link_kind": str(link["link_kind"]),
                "target_statement_id": str(link["target_statement_id"]),
            }
        )
    return normalized


def _affected_pages_by_statement(
    page_plans: Iterable[PagePlan],
) -> dict[str, list[dict[str, Any]]]:
    pages_by_statement: dict[str, list[dict[str, Any]]] = {}
    for plan in sorted(page_plans, key=lambda item: item.id):
        section_ids_by_member: dict[str, set[str]] = {}
        for section in sorted(plan.sections, key=lambda item: item.id):
            for statement_id in section.member_statement_ids:
                section_ids_by_member.setdefault(statement_id, set()).add(section.id)

        member_ids = set(plan.member_statement_ids) | set(section_ids_by_member)
        for statement_id in sorted(member_ids):
            pages_by_statement.setdefault(statement_id, []).append(
                {
                    "page_id": plan.id,
                    "page_type": plan.type,
                    "title": plan.title,
                    "section_ids": sorted(section_ids_by_member.get(statement_id, set())),
                }
            )
    return pages_by_statement


def _evidence_summary(card: StatementCard) -> dict[str, Any]:
    evidence = card.evidence
    return {
        "source_project": evidence.source_project,
        "source_doc": evidence.source_doc,
        "source_section": evidence.source_section,
        "exact": evidence.exact,
        "notebook": evidence.notebook,
        "figure": evidence.figure,
        "p_value": evidence.p_value,
    }
