"""Deterministic PagePlan generation from statement cards.

Emits the four reader page types (home / topic / data / author). Topics and entities are
canonicalized through the additive ``Registry`` before grouping; author and data pages join in
the zero-LLM author and shared-collection indexes. Claims/conflicts/opportunities are *sections*
inside topic pages, not standalone pages.
"""

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

_CONFLICT_KINDS = {"caveat", "conflict"}
_OPPORTUNITY_KINDS = {"opportunity", "direction", "hypothesis"}
_LINKED_TOPIC_KINDS = {"claim", "conflict", "opportunity", "caveat"}
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


def plan_pages(
    cards: Iterable[StatementCard],
    *,
    registry=None,
    authors: dict | None = None,
    collections: dict | None = None,
) -> list[PagePlan]:
    """Generate deterministic page plans (home/topic/data/author) from statement cards.

    Topics and entities are canonicalized through ``registry`` (identity when None) before
    grouping. ``authors`` is a ``{key: AuthorRecord}`` index and ``collections`` is a
    ``{collection_id: CollectionRecord}`` index; author/data pages are emitted only for records
    whose projects appear among the active cards. Retracted cards are excluded from membership.
    """
    authors = authors or {}
    collections = collections or {}
    active_cards = sorted(
        (card for card in cards if card.tier != TIER_RETRACTED),
        key=_card_sort_key,
    )
    card_by_id = {card.id: card for card in active_cards}

    # Canonical topic/entity keys per card (registry None -> identity passthrough).
    card_topics = {card.id: _canonical_topics(card, registry) for card in active_cards}

    project_members: dict[str, list[str]] = {}
    topic_members: dict[str, list[str]] = {}
    project_topics: dict[str, set[str]] = {}
    for card in active_cards:
        project = card.evidence.source_project
        project_members.setdefault(project, []).append(card.id)
        for topic_key in card_topics[card.id]:
            topic_members.setdefault(topic_key, []).append(card.id)
            project_topics.setdefault(project, set()).add(topic_key)

    drafts: dict[str, _PageDraft] = {}
    all_member_ids = [card.id for card in active_cards]
    _add_draft(drafts, _home_plan(active_cards, all_member_ids, card_topics))

    for topic_key in sorted(topic_members):
        member_ids = _topic_member_ids(topic_members[topic_key], card_by_id)
        _add_draft(drafts, _topic_plan(topic_key, member_ids, card_by_id))

    collection_drafts = _data_plans(collections, project_members, card_by_id)
    for draft in collection_drafts:
        _add_draft(drafts, draft)

    author_drafts = _author_plans(authors, project_members, card_by_id)
    for draft in author_drafts:
        _add_draft(drafts, draft)

    _wire_cross_links(
        drafts,
        card_topics=card_topics,
        project_topics=project_topics,
        project_members=project_members,
        collections=collections,
        authors=authors,
    )

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


def _home_plan(
    cards: list[StatementCard],
    member_ids: list[str],
    card_topics: dict[str, list[str]],
) -> _PageDraft:
    sections = [
        _section("overview", "Cross-Project Overview", member_ids),
        _section("topic_map", "Topic Map", [c.id for c in cards if card_topics[c.id]]),
        _section("author_map", "Author Map", member_ids),
        _section("data_map", "Data Map", member_ids),
    ]
    return _PageDraft(
        id="home",
        type="home",
        title="State Of The Science",
        member_statement_ids=_unique_sorted(member_ids),
        sections=sections,
    )


def _topic_plan(topic_key: str, member_ids: list[str], card_by_id: dict[str, StatementCard]) -> _PageDraft:
    sorted_ids = _sort_card_ids(member_ids, card_by_id)
    return _PageDraft(
        id=topic_key,
        type="topic",
        title=f"Topic: {_title(topic_key)}",
        member_statement_ids=sorted_ids,
        sections=[
            _section("overview", "Overview", sorted_ids),
            _section("key_claims", "Key Claims", _ids_of_kinds(sorted_ids, card_by_id, {"claim"})),
            _section(
                "conflicts_and_caveats",
                "Conflicts & Caveats",
                _ids_for_conflicts(sorted_ids, card_by_id),
            ),
            _section(
                "open_directions",
                "Open Directions",
                _ids_of_kinds(sorted_ids, card_by_id, _OPPORTUNITY_KINDS),
            ),
        ],
    )


def _data_plans(
    collections: dict,
    project_members: dict[str, list[str]],
    card_by_id: dict[str, StatementCard],
) -> list[_PageDraft]:
    drafts: list[_PageDraft] = []
    for collection_id in sorted(collections):
        record = collections[collection_id]
        present_projects = [p for p in record.projects if p in project_members]
        if not present_projects:
            continue
        member_ids = _members_for_projects(present_projects, project_members)
        sorted_ids = _sort_card_ids(member_ids, card_by_id)
        title = getattr(record, "label", None) or _title(collection_id)
        drafts.append(
            _PageDraft(
                id=f"data:{collection_id}",
                type="data",
                title=title,
                member_statement_ids=sorted_ids,
                sections=[
                    _section("overview", "Overview", sorted_ids),
                    _section("projects", "Projects Using This Collection", sorted_ids),
                ],
            )
        )
    return drafts


def _author_plans(
    authors: dict,
    project_members: dict[str, list[str]],
    card_by_id: dict[str, StatementCard],
) -> list[_PageDraft]:
    drafts: list[_PageDraft] = []
    for record in sorted(authors.values(), key=lambda r: _author_slug(r)):
        present_projects = [p for p in record.projects if p in project_members]
        if not present_projects:
            continue
        member_ids = _members_for_projects(present_projects, project_members)
        sorted_ids = _sort_card_ids(member_ids, card_by_id)
        drafts.append(
            _PageDraft(
                id=f"author:{_author_slug(record)}",
                type="author",
                title=record.name,
                member_statement_ids=sorted_ids,
                sections=[
                    _section("overview", "Overview", sorted_ids),
                    _section("projects", "Projects", sorted_ids),
                    _section("topics", "Topics", sorted_ids),
                ],
            )
        )
    return drafts


def _wire_cross_links(
    drafts: dict[str, _PageDraft],
    *,
    card_topics: dict[str, list[str]],
    project_topics: dict[str, set[str]],
    project_members: dict[str, list[str]],
    collections: dict,
    authors: dict,
) -> None:
    all_page_ids = set(drafts)

    # Reverse lookups from project -> data/author page ids that are actually present.
    project_data_pages: dict[str, set[str]] = {}
    for collection_id, record in collections.items():
        page_id = f"data:{collection_id}"
        if page_id not in all_page_ids:
            continue
        for project in record.projects:
            project_data_pages.setdefault(project, set()).add(page_id)
    project_author_pages: dict[str, set[str]] = {}
    for record in authors.values():
        page_id = f"author:{_author_slug(record)}"
        if page_id not in all_page_ids:
            continue
        for project in record.projects:
            project_author_pages.setdefault(project, set()).add(page_id)

    for draft in drafts.values():
        if draft.type == "home":
            draft.outgoing_links.update(pid for pid in all_page_ids if pid != "home")
        elif draft.type == "topic":
            member_projects = _member_projects(draft.member_statement_ids, project_members)
            # Adjacent topics (share >=1 source project) + data + author pages of those projects.
            for project in member_projects:
                for other_topic in project_topics.get(project, set()):
                    if other_topic != draft.id:
                        draft.outgoing_links.add(other_topic)
                draft.outgoing_links.update(project_data_pages.get(project, set()))
                draft.outgoing_links.update(project_author_pages.get(project, set()))
        elif draft.type == "data":
            member_projects = _member_projects(draft.member_statement_ids, project_members)
            for project in member_projects:
                draft.outgoing_links.update(project_topics.get(project, set()))
                draft.outgoing_links.update(project_author_pages.get(project, set()))
        elif draft.type == "author":
            member_projects = _member_projects(draft.member_statement_ids, project_members)
            for project in member_projects:
                draft.outgoing_links.update(project_topics.get(project, set()))
                draft.outgoing_links.update(project_data_pages.get(project, set()))
        draft.outgoing_links.discard(draft.id)
        draft.outgoing_links.intersection_update(all_page_ids)


def _members_for_projects(
    projects: Iterable[str], project_members: dict[str, list[str]]
) -> list[str]:
    return [sid for project in projects for sid in project_members.get(project, [])]


def _member_projects(
    member_ids: Iterable[str], project_members: dict[str, list[str]]
) -> set[str]:
    member_set = set(member_ids)
    return {
        project
        for project, ids_ in project_members.items()
        if member_set & set(ids_)
    }


def _topic_member_ids(member_ids: list[str], card_by_id: dict[str, StatementCard]) -> list[str]:
    related = set(member_ids)
    for sid in member_ids:
        card = card_by_id[sid]
        for linked_id in _linked_statement_ids(card):
            linked_card = card_by_id.get(linked_id)
            if linked_card and linked_card.kind in _LINKED_TOPIC_KINDS:
                related.add(linked_id)
    return _sort_card_ids(related, card_by_id)


def _canonical_topics(card: StatementCard, registry) -> list[str]:
    if registry is None:
        return _unique_sorted(card.about.topics)
    return _unique_sorted(registry.topic_key(topic) for topic in card.about.topics)


def _linked_statement_ids(card: StatementCard) -> set[str]:
    return {
        linked_id
        for field_name in _STATEMENT_LINK_FIELDS
        for linked_id in getattr(card.links, field_name)
    }


def _ids_of_kinds(
    member_ids: Iterable[str],
    card_by_id: dict[str, StatementCard],
    kinds: set[str],
) -> list[str]:
    return _sort_card_ids((sid for sid in member_ids if card_by_id[sid].kind in kinds), card_by_id)


def _ids_for_conflicts(
    member_ids: Iterable[str],
    card_by_id: dict[str, StatementCard],
) -> list[str]:
    return _sort_card_ids(
        (
            sid
            for sid in member_ids
            if card_by_id[sid].kind in _CONFLICT_KINDS or card_by_id[sid].tier == "conflict"
        ),
        card_by_id,
    )


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


def _author_slug(record) -> str:
    return _slug(record.orcid or record.name)


def _title(value: str) -> str:
    label = value.split(":", 1)[1] if ":" in value else value
    return label.replace("_", " ").replace("-", " ").title()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"
