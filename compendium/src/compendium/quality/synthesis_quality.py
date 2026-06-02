"""Quality metrics for v4 synthesis statement-card graph and page plans."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from compendium.models import PagePlan, StatementCard, TIER_RETRACTED

_LINK_FIELDS = (
    "supports",
    "contradicts",
    "motivates",
    "refines",
    "requires_validation",
)
_TARGET_OUTPUT_QUALIFIERS = {
    "deliverable",
    "derived_product",
    "output",
    "product",
    "target",
    "target_output",
    "target_outputs",
}


def assess_synthesis_quality(
    cards: Iterable[StatementCard],
    graph: dict[str, list[dict[str, Any]]],
    page_plans: Iterable[PagePlan],
    source_root: str | Path | None = None,
) -> dict[str, Any]:
    """Compute deterministic quality metrics for statement-card wiki artifacts.

    Parameters
    ----------
    cards
        Statement cards that feed graph assembly and page planning.
    graph
        Graph dictionary with ``nodes`` and ``edges`` lists.
    page_plans
        Deterministic page plans for generated synthesis/evidence/entity pages.
    source_root
        Optional root used to resolve evidence anchors. The resolver checks both
        ``source_root/source_project/source_doc`` and ``source_root/source_doc``.

    Returns
    -------
    dict[str, Any]
        JSON/YAML-friendly metrics with stable key and list ordering.
    """
    card_list = sorted(cards, key=lambda card: card.id)
    active_cards = [card for card in card_list if card.tier != TIER_RETRACTED]
    active_card_ids = {card.id for card in active_cards}
    active_card_by_id = {card.id: card for card in active_cards}
    plans = sorted(page_plans, key=lambda plan: plan.id)

    return {
        "statement_counts": _statement_counts(card_list),
        "evidence_resolution": _evidence_resolution(active_cards, source_root),
        "topic_coverage": _topic_coverage(active_cards, plans),
        "claim_balance": _claim_balance(active_cards),
        "graph_integrity": _graph_integrity(graph),
        "page_integrity": _page_integrity(plans, active_card_ids),
        "link_integrity": _link_integrity(plans),
        "statement_link_integrity": _statement_link_integrity(active_cards, active_card_ids),
        "opportunity_targets": _opportunity_targets(active_cards, active_card_by_id),
        "active_conflicts": _active_conflicts(active_cards),
        "high_centrality_asserted_statements": _high_centrality_asserted_statements(
            active_cards,
            graph,
        ),
        "synthesis_page_changes": _synthesis_page_changes(plans),
    }


def _statement_counts(cards: list[StatementCard]) -> dict[str, Any]:
    return {
        "total": len(cards),
        "by_kind": _counter_dict(card.kind for card in cards),
        "by_tier": _counter_dict(card.tier for card in cards),
        "by_source_project": _counter_dict(card.evidence.source_project for card in cards),
    }


def _evidence_resolution(
    cards: list[StatementCard],
    source_root: str | Path | None,
) -> dict[str, Any]:
    if source_root is None:
        return {
            "checked": False,
            "total": len(cards),
            "resolved": 0,
            "unresolved": len(cards),
            "rate": None,
            "unresolved_statement_ids": [card.id for card in cards],
        }

    root = Path(source_root)
    unresolved = [
        card.id
        for card in cards
        if not _evidence_anchor_resolves(root, card)
    ]
    resolved = len(cards) - len(unresolved)
    return {
        "checked": True,
        "total": len(cards),
        "resolved": resolved,
        "unresolved": len(unresolved),
        "rate": resolved / len(cards) if cards else 0.0,
        "unresolved_statement_ids": unresolved,
    }


def _evidence_anchor_resolves(root: Path, card: StatementCard) -> bool:
    evidence = card.evidence
    candidates = (
        root / evidence.source_project / evidence.source_doc,
        root / evidence.source_doc,
    )
    needle = evidence.exact.strip()
    if not needle:
        return False
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if needle in text:
            return True
    return False


def _topic_coverage(cards: list[StatementCard], plans: list[PagePlan]) -> dict[str, Any]:
    topic_statement_counts = Counter(
        topic_id
        for card in cards
        for topic_id in sorted(set(card.about.topics))
    )
    topic_ids = set(topic_statement_counts)
    topic_page_ids = {plan.id for plan in plans if plan.type == "topic"}
    covered_topics = topic_ids & topic_page_ids
    statements_without_topics = sorted(
        card.id for card in cards if not card.about.topics
    )

    return {
        "topic_count": len(topic_ids),
        "topic_page_count": len(topic_page_ids),
        "covered_topic_count": len(covered_topics),
        "coverage_rate": len(covered_topics) / len(topic_ids) if topic_ids else 0.0,
        "topics_without_pages": sorted(topic_ids - topic_page_ids),
        "topic_pages_without_statements": sorted(topic_page_ids - topic_ids),
        "statements_with_topics": len(cards) - len(statements_without_topics),
        "statements_without_topics": statements_without_topics,
        "topic_statement_counts": {
            topic_id: topic_statement_counts[topic_id]
            for topic_id in sorted(topic_statement_counts)
        },
    }


def _claim_balance(cards: list[StatementCard]) -> dict[str, Any]:
    active_card_ids = {card.id for card in cards}
    claim_ids = {card.id for card in cards if card.kind == "claim"}
    support_by_claim: dict[str, set[str]] = {claim_id: set() for claim_id in claim_ids}
    refutation_by_claim: dict[str, set[str]] = {claim_id: set() for claim_id in claim_ids}

    for card in cards:
        for target_id in card.links.supports:
            if target_id in support_by_claim:
                support_by_claim[target_id].add(card.id)
        for target_id in card.links.contradicts:
            if target_id in refutation_by_claim:
                refutation_by_claim[target_id].add(card.id)
            if card.id in refutation_by_claim and target_id in active_card_ids:
                refutation_by_claim[card.id].add(target_id)

    claims = [
        {
            "statement_id": claim_id,
            "support_count": len(support_by_claim[claim_id]),
            "refutation_count": len(refutation_by_claim[claim_id]),
            "supporting_statement_ids": sorted(support_by_claim[claim_id]),
            "refuting_statement_ids": sorted(refutation_by_claim[claim_id]),
        }
        for claim_id in sorted(claim_ids)
    ]
    support_link_count = sum(item["support_count"] for item in claims)
    refutation_link_count = sum(item["refutation_count"] for item in claims)

    return {
        "total_claims": len(claims),
        "supported_claims": sum(1 for item in claims if item["support_count"]),
        "refuted_claims": sum(1 for item in claims if item["refutation_count"]),
        "unsupported_claim_statement_ids": [
            item["statement_id"] for item in claims if not item["support_count"]
        ],
        "support_link_count": support_link_count,
        "refutation_link_count": refutation_link_count,
        "net_support_balance": support_link_count - refutation_link_count,
        "claims": claims,
    }


def _graph_integrity(graph: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    nodes = sorted(graph.get("nodes", []), key=lambda node: str(node.get("id", "")))
    edges = sorted(
        graph.get("edges", []),
        key=lambda edge: (
            str(edge.get("s", edge.get("source", ""))),
            str(edge.get("p", edge.get("predicate", ""))),
            str(edge.get("o", edge.get("target", ""))),
            str(edge.get("id", "")),
        ),
    )
    node_ids = {str(node.get("id", "")) for node in nodes if node.get("id")}
    dangling = []
    for edge in edges:
        source = str(edge.get("s", edge.get("source", "")))
        target = str(edge.get("o", edge.get("target", "")))
        missing = sorted(endpoint for endpoint in (source, target) if endpoint not in node_ids)
        if missing:
            dangling.append(
                {
                    "edge_id": edge.get("id"),
                    "source": source,
                    "predicate": edge.get("p", edge.get("predicate")),
                    "target": target,
                    "missing_endpoints": missing,
                }
            )

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "dangling_edges": len(dangling),
        "dangling_edge_details": dangling,
    }


def _page_integrity(plans: list[PagePlan], active_card_ids: set[str]) -> dict[str, Any]:
    pages_by_type = _counter_dict(plan.type for plan in plans)
    unknown_page_members = []
    unknown_section_members = []
    member_page_ids: set[str] = set()

    for plan in plans:
        for member_id in sorted(set(plan.member_statement_ids)):
            if member_id in active_card_ids:
                member_page_ids.add(member_id)
            else:
                unknown_page_members.append({"page_id": plan.id, "member_statement_id": member_id})
        for section in sorted(plan.sections, key=lambda item: item.id):
            for member_id in sorted(set(section.member_statement_ids)):
                if member_id not in active_card_ids:
                    unknown_section_members.append(
                        {
                            "page_id": plan.id,
                            "section_id": section.id,
                            "member_statement_id": member_id,
                        }
                    )

    orphan_pages = sorted(
        plan.id
        for plan in plans
        if plan.id != "home"
        and not plan.member_statement_ids
        and not plan.outgoing_links
        and not plan.backlinks
    )
    weakly_connected_pages = [
        {
            "page_id": plan.id,
            "link_degree": len(set(plan.outgoing_links)) + len(set(plan.backlinks)),
            "member_count": len(set(plan.member_statement_ids)),
        }
        for plan in plans
        if plan.id != "home" and len(set(plan.outgoing_links)) + len(set(plan.backlinks)) <= 1
    ]
    statements_without_page_membership = sorted(active_card_ids - member_page_ids)

    return {
        "page_count": len(plans),
        "pages_by_type": pages_by_type,
        "orphan_pages": orphan_pages,
        "weakly_connected_pages": weakly_connected_pages,
        "unknown_page_members": unknown_page_members,
        "unknown_section_members": unknown_section_members,
        "statements_without_page_membership": statements_without_page_membership,
    }


def _link_integrity(plans: list[PagePlan]) -> dict[str, Any]:
    page_ids = {plan.id for plan in plans}
    outgoing_by_page = {plan.id: set(plan.outgoing_links) for plan in plans}
    backlinks_by_page = {plan.id: set(plan.backlinks) for plan in plans}
    broken_outgoing = []
    broken_backlinks = []
    missing_backlinks = []
    stale_backlinks = []

    for plan in plans:
        for target in sorted(outgoing_by_page[plan.id]):
            if target not in page_ids:
                broken_outgoing.append({"page_id": plan.id, "target_page_id": target})
                continue
            if plan.id not in backlinks_by_page[target]:
                missing_backlinks.append({"page_id": plan.id, "target_page_id": target})

        for source in sorted(backlinks_by_page[plan.id]):
            if source not in page_ids:
                broken_backlinks.append({"page_id": plan.id, "source_page_id": source})
                continue
            if plan.id not in outgoing_by_page[source]:
                stale_backlinks.append({"page_id": plan.id, "source_page_id": source})

    return {
        "broken_outgoing_links": broken_outgoing,
        "broken_backlinks": broken_backlinks,
        "missing_backlinks": missing_backlinks,
        "stale_backlinks": stale_backlinks,
        "broken_outgoing_link_count": len(broken_outgoing),
        "broken_backlink_count": len(broken_backlinks),
        "backlink_mismatch_count": len(missing_backlinks) + len(stale_backlinks),
    }


def _statement_link_integrity(
    cards: list[StatementCard],
    active_card_ids: set[str],
) -> dict[str, Any]:
    unresolved = []
    for card in cards:
        for field_name in _LINK_FIELDS:
            for target_id in sorted(set(getattr(card.links, field_name))):
                if target_id not in active_card_ids:
                    unresolved.append(
                        {
                            "source_statement_id": card.id,
                            "link_kind": field_name,
                            "target_statement_id": target_id,
                        }
                    )
    return {
        "unresolved_statement_link_count": len(unresolved),
        "unresolved_statement_links": unresolved,
    }


def _opportunity_targets(
    cards: list[StatementCard],
    card_by_id: dict[str, StatementCard],
) -> dict[str, Any]:
    opportunities = [card for card in cards if card.kind == "opportunity"]
    with_targets = []
    without_targets = []

    for card in opportunities:
        target_outputs = _target_outputs_for_opportunity(card, card_by_id)
        item = {"statement_id": card.id, "target_outputs": target_outputs}
        if target_outputs:
            with_targets.append(item)
        else:
            without_targets.append(card.id)

    return {
        "total": len(opportunities),
        "with_target_outputs": len(with_targets),
        "rate": len(with_targets) / len(opportunities) if opportunities else 0.0,
        "opportunities": with_targets,
        "missing_target_output_statement_ids": sorted(without_targets),
    }


def _target_outputs_for_opportunity(
    card: StatementCard,
    card_by_id: dict[str, StatementCard],
) -> list[str]:
    outputs = {
        str(value)
        for key, value in card.qualifiers.items()
        if value and (_is_target_output_qualifier(key) or _looks_like_output_value(str(value)))
    }
    linked_ids = {
        linked_id
        for field_name in _LINK_FIELDS
        for linked_id in getattr(card.links, field_name)
    }
    for linked_id in linked_ids:
        linked_card = card_by_id.get(linked_id)
        if linked_card and linked_card.kind == "derived_product":
            outputs.add(linked_card.id)
    return sorted(outputs)


def _is_target_output_qualifier(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in _TARGET_OUTPUT_QUALIFIERS or (
        "target" in normalized and "output" in normalized
    )


def _looks_like_output_value(value: str) -> bool:
    return value.startswith(("product:", "derived_product:", "dataset:", "notebook:"))


def _active_conflicts(cards: list[StatementCard]) -> dict[str, Any]:
    conflict_statement_ids = sorted(
        card.id for card in cards if card.kind == "conflict" or card.tier == "conflict"
    )
    contradiction_links = []
    for card in cards:
        for target_id in sorted(set(card.links.contradicts)):
            contradiction_links.append(
                {"source_statement_id": card.id, "target_statement_id": target_id}
            )

    return {
        "count": len(conflict_statement_ids) + len(contradiction_links),
        "conflict_statement_ids": conflict_statement_ids,
        "contradiction_links": contradiction_links,
    }


def _high_centrality_asserted_statements(
    cards: list[StatementCard],
    graph: dict[str, list[dict[str, Any]]],
) -> list[dict[str, int | str]]:
    asserted_ids = {card.id for card in cards if card.tier == "asserted"}
    degree = Counter()
    for edge in graph.get("edges", []):
        source = str(edge.get("s", edge.get("source", "")))
        target = str(edge.get("o", edge.get("target", "")))
        if source in asserted_ids:
            degree[source] += 1
        if target in asserted_ids:
            degree[target] += 1

    if not degree:
        return []

    threshold = max(2, max(degree.values()))
    return [
        {"statement_id": statement_id, "degree": degree[statement_id]}
        for statement_id in sorted(degree)
        if degree[statement_id] >= threshold
    ]


def _synthesis_page_changes(plans: list[PagePlan]) -> dict[str, Any]:
    tracked_page_ids = []
    regenerated_page_ids = []
    changed_page_ids = []

    for plan in plans:
        regenerated = _optional_bool(
            plan,
            ("regenerated", "was_regenerated", "page_regenerated"),
        )
        changed = _optional_bool(
            plan,
            (
                "changed",
                "was_changed",
                "content_changed",
                "member_hash_changed",
                "page_changed",
            ),
        )
        if regenerated is not None or changed is not None:
            tracked_page_ids.append(plan.id)
        if regenerated:
            regenerated_page_ids.append(plan.id)
        if changed:
            changed_page_ids.append(plan.id)

    return {
        "available": bool(tracked_page_ids),
        "tracked_page_count": len(tracked_page_ids),
        "regenerated": len(regenerated_page_ids),
        "changed": len(changed_page_ids),
        "regenerated_page_ids": sorted(regenerated_page_ids),
        "changed_page_ids": sorted(changed_page_ids),
    }


def _optional_bool(item: Any, field_names: tuple[str, ...]) -> bool | None:
    for field_name in field_names:
        if hasattr(item, field_name):
            value = getattr(item, field_name)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "changed", "regenerated"}:
                    return True
                if normalized in {"false", "0", "no", "unchanged", "stable"}:
                    return False
            return bool(value)
    return None


def _counter_dict(values: Iterable[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}
