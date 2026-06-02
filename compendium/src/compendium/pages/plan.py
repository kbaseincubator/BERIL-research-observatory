"""Deterministic PagePlan generation from statement cards."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from collections.abc import Iterable

from compendium import ids
from compendium.models import (
    PagePlan,
    PageSectionPlan,
    StatementCard,
    TIER_RETRACTED,
)

_SYNTHESIS_PAGE_KINDS = {"claim", "opportunity"}
_CONFLICT_KINDS = {"caveat", "conflict"}
_OPPORTUNITY_KINDS = {"opportunity", "direction", "hypothesis"}
_PRODUCT_KINDS = {"derived_product", "method_note"}
_STATEMENT_LINK_FIELDS = (
    "supports",
    "contradicts",
    "motivates",
    "refines",
    "requires_validation",
)


@dataclass
class _PageDraft:
    id: str
    type: str
    title: str
    member_statement_ids: list[str]
    sections: list[PageSectionPlan]
    outgoing_links: set[str] = field(default_factory=set)


def member_hash(member_statement_ids: Iterable[str]) -> str:
    """Return the stable hash used for page and section member sets."""
    return "hash:" + ids.content_hash(*_unique_sorted(member_statement_ids), n=16)


def page_id_for_statement(card: StatementCard) -> str | None:
    """Return the synthesis-page id for statement kinds with standalone pages."""
    if card.kind not in _SYNTHESIS_PAGE_KINDS:
        return None
    suffix = card.id.split(":", 1)[1] if ":" in card.id else _slug(card.id)
    return f"{card.kind}:{suffix}"


def plan_pages(cards: Iterable[StatementCard]) -> list[PagePlan]:
    """Generate deterministic page plans from statement cards.

    Retracted cards are preserved elsewhere for provenance, but excluded from
    normal synthesis-page membership.
    """
    active_cards = sorted(
        (card for card in cards if card.tier != TIER_RETRACTED),
        key=_card_sort_key,
    )
    card_by_id = {card.id: card for card in active_cards}

    project_members: dict[str, list[str]] = {}
    topic_members: dict[str, list[str]] = {}
    entity_members: dict[str, list[str]] = {}
    for card in active_cards:
        project_members.setdefault(card.evidence.source_project, []).append(card.id)
        for topic_id in card.about.topics:
            topic_members.setdefault(topic_id, []).append(card.id)
        for entity_id in _card_entities(card):
            entity_members.setdefault(entity_id, []).append(card.id)

    incoming_links = _incoming_links(active_cards)
    statement_page_ids = {
        card.id: page_id
        for card in active_cards
        if (page_id := page_id_for_statement(card)) is not None
    }

    drafts: dict[str, _PageDraft] = {}
    all_member_ids = [card.id for card in active_cards]
    _add_draft(drafts, _home_plan(active_cards, all_member_ids))

    for project_id in sorted(project_members):
        _add_draft(
            drafts,
            _project_plan(project_id, project_members[project_id], card_by_id),
        )

    for topic_id in sorted(topic_members):
        member_ids = _topic_member_ids(topic_members[topic_id], card_by_id)
        _add_draft(drafts, _topic_plan(topic_id, member_ids, card_by_id))

    for entity_id in sorted(entity_members):
        _add_draft(
            drafts,
            _entity_plan(entity_id, entity_members[entity_id], card_by_id),
        )

    for card in active_cards:
        page_id = statement_page_ids.get(card.id)
        if page_id is None:
            continue
        _add_draft(
            drafts,
            _statement_plan(card, card_by_id, incoming_links),
        )

    all_page_ids = set(drafts)
    for draft in drafts.values():
        if draft.id == "home":
            draft.outgoing_links.update(pid for pid in all_page_ids if pid != "home")
        else:
            draft.outgoing_links.update(
                _page_links_for_members(draft.member_statement_ids, card_by_id, statement_page_ids)
            )
        draft.outgoing_links.discard(draft.id)
        draft.outgoing_links.intersection_update(all_page_ids)

    backlinks: dict[str, set[str]] = {page_id: set() for page_id in drafts}
    for page_id, draft in drafts.items():
        for target in draft.outgoing_links:
            backlinks[target].add(page_id)

    return [
        PagePlan(
            id=draft.id,
            type=draft.type,
            title=draft.title,
            member_statement_ids=_sort_card_ids(draft.member_statement_ids, card_by_id),
            sections=draft.sections,
            outgoing_links=sorted(draft.outgoing_links),
            backlinks=sorted(backlinks[draft.id]),
            member_hash=member_hash(draft.member_statement_ids),
        )
        for draft in sorted(drafts.values(), key=lambda item: item.id)
    ]


def _home_plan(cards: list[StatementCard], member_ids: list[str]) -> _PageDraft:
    sections = [
        _section("overview", "Cross-Project Overview", member_ids),
        _section("topic_map", "Topic Map", _ids_with_topics(cards)),
        _section(
            "strong_claims",
            "Strong Reusable Claims",
            [
                card.id
                for card in cards
                if card.kind == "claim"
                and card.confidence == "high"
                and card.tier in {"grounded", "reviewed"}
            ],
        ),
        _section(
            "conflicts_and_caveats",
            "Active Conflicts And Caveats",
            [card.id for card in cards if card.kind in _CONFLICT_KINDS or card.tier == "conflict"],
        ),
        _section(
            "opportunities_and_directions",
            "High-Value Opportunities And Directions",
            [card.id for card in cards if card.kind in _OPPORTUNITY_KINDS],
        ),
        _section(
            "reusable_data_products",
            "Reusable Data And Products",
            [card.id for card in cards if card.kind in _PRODUCT_KINDS],
        ),
        _section("recent_changes", "Recently Changed Projects And Pages", _recent_card_ids(cards)),
        _section("browse_lanes", "Browse Lanes", member_ids),
    ]
    return _PageDraft(
        id="home",
        type="home",
        title="State Of The Science",
        member_statement_ids=_unique_sorted(member_ids),
        sections=sections,
    )


def _project_plan(project_id: str, member_ids: list[str], card_by_id: dict[str, StatementCard]) -> _PageDraft:
    sorted_ids = _sort_card_ids(member_ids, card_by_id)
    return _PageDraft(
        id=f"project:{project_id}",
        type="project",
        title=f"Project: {_title(project_id)}",
        member_statement_ids=sorted_ids,
        sections=[
            _section("summary", "Statement Summary", sorted_ids),
            _section("findings", "Findings", _ids_of_kinds(sorted_ids, card_by_id, {"finding"})),
            _section("claims", "Claims", _ids_of_kinds(sorted_ids, card_by_id, {"claim"})),
            _section(
                "conflicts_and_caveats",
                "Conflicts And Caveats",
                _ids_of_kinds(sorted_ids, card_by_id, _CONFLICT_KINDS),
            ),
            _section(
                "opportunities_and_directions",
                "Opportunities And Directions",
                _ids_of_kinds(sorted_ids, card_by_id, _OPPORTUNITY_KINDS),
            ),
            _section(
                "products_and_methods",
                "Reusable Products And Methods",
                _ids_of_kinds(sorted_ids, card_by_id, _PRODUCT_KINDS),
            ),
        ],
    )


def _topic_plan(topic_id: str, member_ids: list[str], card_by_id: dict[str, StatementCard]) -> _PageDraft:
    sorted_ids = _sort_card_ids(member_ids, card_by_id)
    return _PageDraft(
        id=topic_id,
        type="topic",
        title=f"Topic: {_title(topic_id)}",
        member_statement_ids=sorted_ids,
        sections=[
            _section("overview", "Overview", sorted_ids),
            _section("findings", "Findings", _ids_of_kinds(sorted_ids, card_by_id, {"finding"})),
            _section("key_claims", "Key Claims", _ids_of_kinds(sorted_ids, card_by_id, {"claim"})),
            _section(
                "conflicts_and_caveats",
                "Conflicts And Caveats",
                _ids_of_kinds(sorted_ids, card_by_id, _CONFLICT_KINDS),
            ),
            _section(
                "opportunities_and_directions",
                "Opportunities And Directions",
                _ids_of_kinds(sorted_ids, card_by_id, _OPPORTUNITY_KINDS),
            ),
            _section(
                "products_and_methods",
                "Reusable Products And Methods",
                _ids_of_kinds(sorted_ids, card_by_id, _PRODUCT_KINDS),
            ),
        ],
    )


def _entity_plan(entity_id: str, member_ids: list[str], card_by_id: dict[str, StatementCard]) -> _PageDraft:
    sorted_ids = _sort_card_ids(member_ids, card_by_id)
    topic_ids = sorted({topic for sid in sorted_ids for topic in card_by_id[sid].about.topics})
    sections = [
        _section("backlinks", "Backlinks", sorted_ids),
        _section("findings", "Findings", _ids_of_kinds(sorted_ids, card_by_id, {"finding"})),
        _section("claims", "Claims", _ids_of_kinds(sorted_ids, card_by_id, {"claim"})),
        _section(
            "conflicts_and_caveats",
            "Conflicts And Caveats",
            _ids_of_kinds(sorted_ids, card_by_id, _CONFLICT_KINDS),
        ),
        _section(
            "opportunities_and_directions",
            "Opportunities And Directions",
            _ids_of_kinds(sorted_ids, card_by_id, _OPPORTUNITY_KINDS),
        ),
    ]
    sections.extend(
        _section(f"topic_{_slug(topic_id)}", f"Topic: {_title(topic_id)}", _ids_for_topic(sorted_ids, card_by_id, topic_id))
        for topic_id in topic_ids
    )
    return _PageDraft(
        id=entity_id,
        type="entity",
        title=f"Entity: {_title(entity_id)}",
        member_statement_ids=sorted_ids,
        sections=sections,
    )


def _statement_plan(
    card: StatementCard,
    card_by_id: dict[str, StatementCard],
    incoming_links: dict[str, dict[str, list[str]]],
) -> _PageDraft:
    if card.kind == "claim":
        sections = _claim_sections(card, card_by_id, incoming_links)
    else:
        sections = _opportunity_sections(card, card_by_id, incoming_links)
    member_ids = _sort_card_ids(
        {sid for section in sections for sid in section.member_statement_ids},
        card_by_id,
    )
    return _PageDraft(
        id=page_id_for_statement(card) or card.id,
        type=card.kind,
        title=card.statement,
        member_statement_ids=member_ids,
        sections=sections,
    )


def _claim_sections(
    card: StatementCard,
    card_by_id: dict[str, StatementCard],
    incoming_links: dict[str, dict[str, list[str]]],
) -> list[PageSectionPlan]:
    incoming = incoming_links.get(card.id, {})
    linked = _linked_statement_ids(card)
    refutations = set(incoming.get("contradicts", [])) | set(card.links.contradicts)
    downstream = set(card.links.supports) | set(card.links.motivates) | set(card.links.refines)
    caveats = set(incoming.get("requires_validation", [])) | set(card.links.requires_validation)
    caveats.update(
        other.id
        for other in card_by_id.values()
        if other.kind == "caveat" and _shares_context(card, other)
    )
    return [
        _section("claim", "Claim", [card.id]),
        _section("supporting_evidence", "Supporting Evidence", incoming.get("supports", [])),
        _section("refutations", "Refutations", refutations),
        _section("caveats", "Caveats", caveats),
        _section("downstream_uses", "Downstream Uses", downstream | (linked & set(incoming.get("motivates", [])))),
    ]


def _opportunity_sections(
    card: StatementCard,
    card_by_id: dict[str, StatementCard],
    incoming_links: dict[str, dict[str, list[str]]],
) -> list[PageSectionPlan]:
    incoming = incoming_links.get(card.id, {})
    motivating = set(incoming.get("motivates", [])) | set(incoming.get("supports", []))
    validation = set(incoming.get("requires_validation", [])) | set(card.links.requires_validation)
    related_claims = {
        other.id
        for other in card_by_id.values()
        if other.kind == "claim" and (_shares_context(card, other) or card.id in _linked_statement_ids(other))
    }
    return [
        _section("opportunity", "Opportunity", [card.id]),
        _section("motivating_evidence", "Motivating Evidence", motivating),
        _section("required_validation", "Required Validation", validation),
        _section("related_claims", "Related Claims", related_claims),
    ]


def _topic_member_ids(member_ids: list[str], card_by_id: dict[str, StatementCard]) -> list[str]:
    related = set(member_ids)
    for sid in member_ids:
        card = card_by_id[sid]
        for linked_id in _linked_statement_ids(card):
            linked_card = card_by_id.get(linked_id)
            if linked_card and linked_card.kind in {"claim", "conflict", "opportunity", "caveat"}:
                related.add(linked_id)
    return _sort_card_ids(related, card_by_id)


def _page_links_for_members(
    member_ids: Iterable[str],
    card_by_id: dict[str, StatementCard],
    statement_page_ids: dict[str, str],
) -> set[str]:
    links: set[str] = set()
    for sid in member_ids:
        card = card_by_id.get(sid)
        if card is None:
            continue
        links.add(f"project:{card.evidence.source_project}")
        links.update(card.about.topics)
        links.update(_card_entities(card))
        if statement_page_id := statement_page_ids.get(sid):
            links.add(statement_page_id)
        for linked_id in _linked_statement_ids(card):
            if statement_page_id := statement_page_ids.get(linked_id):
                links.add(statement_page_id)
    return links


def _incoming_links(cards: list[StatementCard]) -> dict[str, dict[str, list[str]]]:
    incoming: dict[str, dict[str, list[str]]] = {}
    for card in cards:
        for field_name in _STATEMENT_LINK_FIELDS:
            for target in getattr(card.links, field_name):
                incoming.setdefault(target, {}).setdefault(field_name, []).append(card.id)
    for field_map in incoming.values():
        for field_name, source_ids in field_map.items():
            field_map[field_name] = _unique_sorted(source_ids)
    return incoming


def _linked_statement_ids(card: StatementCard) -> set[str]:
    return {
        linked_id
        for field_name in _STATEMENT_LINK_FIELDS
        for linked_id in getattr(card.links, field_name)
    }


def _shares_context(left: StatementCard, right: StatementCard) -> bool:
    return bool(
        set(left.about.topics) & set(right.about.topics)
        or set(_card_entities(left)) & set(_card_entities(right))
    )


def _card_entities(card: StatementCard) -> list[str]:
    entity_ids = set(card.about.entities)
    entity_ids.update(value for value in card.qualifiers.values() if value.startswith("entity:"))
    return sorted(entity_ids)


def _ids_with_topics(cards: list[StatementCard]) -> list[str]:
    return _unique_sorted(card.id for card in cards if card.about.topics)


def _recent_card_ids(cards: list[StatementCard]) -> list[str]:
    return [
        card.id
        for card in sorted(
            cards,
            key=lambda item: (item.extraction.timestamp, item.evidence.source_project, item.id),
            reverse=True,
        )
    ]


def _ids_of_kinds(
    member_ids: Iterable[str],
    card_by_id: dict[str, StatementCard],
    kinds: set[str],
) -> list[str]:
    return _sort_card_ids((sid for sid in member_ids if card_by_id[sid].kind in kinds), card_by_id)


def _ids_for_topic(
    member_ids: Iterable[str],
    card_by_id: dict[str, StatementCard],
    topic_id: str,
) -> list[str]:
    return _sort_card_ids((sid for sid in member_ids if topic_id in card_by_id[sid].about.topics), card_by_id)


def _section(section_id: str, heading: str, member_ids: Iterable[str]) -> PageSectionPlan:
    ids_ = _unique_sorted(member_ids)
    return PageSectionPlan(
        id=section_id,
        heading=heading,
        member_statement_ids=ids_,
        member_hash=member_hash(ids_),
    )


def _add_draft(drafts: dict[str, _PageDraft], draft: _PageDraft) -> None:
    drafts[draft.id] = draft


def _sort_card_ids(member_ids: Iterable[str], card_by_id: dict[str, StatementCard]) -> list[str]:
    return sorted(set(member_ids), key=lambda sid: _card_sort_key(card_by_id[sid]) if sid in card_by_id else sid)


def _unique_sorted(values: Iterable[str]) -> list[str]:
    return sorted(set(values))


def _card_sort_key(card: StatementCard) -> tuple[str, str, str, str]:
    return (card.kind, card.evidence.source_project, card.statement, card.id)


def _title(value: str) -> str:
    label = value.split(":", 1)[1] if ":" in value else value
    return label.replace("_", " ").replace("-", " ").title()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"
