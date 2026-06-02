"""Tests for deterministic statement-card review queue ranking."""

from __future__ import annotations

import json

from compendium.models import (
    AboutRefs,
    EvidenceAnchor,
    ExtractionManifest,
    PagePlan,
    PageSectionPlan,
    StatementCard,
    StatementLinks,
    TIER_RETRACTED,
)
from compendium.quality.review_queue import build_review_queue


def _manifest() -> ExtractionManifest:
    return ExtractionManifest(
        agent_type="llm_extractor",
        skill="kg-ingest-project",
        model="test-model",
        prompt_hash="prompt:abc",
        context_pack_hash="context:def",
        repo_commit="abc123",
        timestamp="2026-06-02T00:00:00Z",
    )


def _card(
    id_: str,
    *,
    kind: str = "finding",
    tier: str = "grounded",
    confidence: str = "high",
    links: StatementLinks | None = None,
) -> StatementCard:
    return StatementCard(
        id=id_,
        kind=kind,
        statement=f"{id_} statement",
        scope="project_local",
        tier=tier,
        confidence=confidence,
        about=AboutRefs(
            entities=["entity:adp1"],
            topics=["topic:carbon"],
        ),
        links=links or StatementLinks(),
        qualifiers={"organism": "entity:adp1"},
        evidence=EvidenceAnchor(
            source_project="proj_a",
            source_doc="REPORT.md",
            source_section="Key Findings",
            exact=f"{id_} exact evidence",
            notebook="analysis.ipynb",
        ),
        extraction=_manifest(),
    )


def _page(
    id_: str,
    *,
    type_: str,
    members: list[str],
    section_members: list[str] | None = None,
) -> PagePlan:
    return PagePlan(
        id=id_,
        type=type_,
        title=id_,
        member_statement_ids=list(members),
        sections=[
            PageSectionPlan(
                id="main",
                heading="Main",
                member_statement_ids=section_members or list(members),
                member_hash="hash:test",
            )
        ],
        outgoing_links=[],
        backlinks=[],
        member_hash="hash:test",
    )


def test_review_queue_ranks_conflicts_low_confidence_unresolved_and_pages() -> None:
    cards = [
        _card("stmt:b", tier="asserted", confidence="low"),
        _card(
            "stmt:a",
            kind="conflict",
            tier="conflict",
            confidence="low",
            links=StatementLinks(contradicts=["stmt:b"], requires_validation=["stmt:missing"]),
        ),
        _card("stmt:c"),
    ]
    graph = {
        "nodes": [{"id": card.id} for card in cards],
        "edges": [
            {"id": "e1", "s": "stmt:a", "p": "contradicts", "o": "stmt:b"},
            {"id": "e2", "s": "stmt:c", "p": "supports", "o": "stmt:a"},
            {"id": "e3", "s": "stmt:a", "p": "about_entity", "o": "entity:adp1"},
        ],
    }
    pages = [
        _page("home", type_="home", members=["stmt:a", "stmt:b"]),
        _page("conflict:a", type_="conflict", members=["stmt:a"]),
    ]

    queue = build_review_queue(cards, graph, pages)

    assert [record["statement_id"] for record in queue] == ["stmt:a", "stmt:b"]
    assert queue[0]["score"] > queue[1]["score"]
    assert queue[0]["reasons"] == [
        "conflict_status",
        "contradictions:1",
        "unresolved_statement_links:1",
        "low_confidence",
        "high_graph_centrality:3",
        "affected_pages:2",
    ]
    assert queue[0]["evidence_summary"] == {
        "source_project": "proj_a",
        "source_doc": "REPORT.md",
        "source_section": "Key Findings",
        "exact": "stmt:a exact evidence",
        "notebook": "analysis.ipynb",
        "figure": None,
        "p_value": None,
    }
    assert queue[0]["affected_pages"] == [
        {
            "page_id": "conflict:a",
            "page_type": "conflict",
            "title": "conflict:a",
            "section_ids": ["main"],
        },
        {
            "page_id": "home",
            "page_type": "home",
            "title": "home",
            "section_ids": ["main"],
        },
    ]
    assert queue[0]["unresolved_statement_links"] == [
        {
            "source_statement_id": "stmt:a",
            "link_kind": "requires_validation",
            "target_statement_id": "stmt:missing",
        }
    ]
    assert json.loads(json.dumps(queue, sort_keys=True)) == queue


def test_review_queue_uses_supplied_unresolved_links_and_tie_breaks() -> None:
    cards = [
        _card("stmt:z", tier="asserted"),
        _card("stmt:a", tier="asserted"),
        _card("stmt:old", tier=TIER_RETRACTED, confidence="low"),
    ]
    graph = {"nodes": [{"id": card.id} for card in cards], "edges": []}
    metrics = {
        "statement_link_integrity": {
            "unresolved_statement_links": [
                {
                    "source_statement_id": "stmt:z",
                    "link_kind": "supports",
                    "target_statement_id": "stmt:missing",
                }
            ]
        }
    }

    queue = build_review_queue(cards, graph, unresolved_statement_links=metrics)

    assert [record["statement_id"] for record in queue] == ["stmt:z", "stmt:a"]
    assert queue[0]["reasons"] == [
        "unresolved_statement_links:1",
        "asserted_tier",
    ]
    assert queue[1]["reasons"] == ["asserted_tier"]


def test_review_queue_promotes_high_centrality_grounded_statements() -> None:
    cards = [
        _card("stmt:leaf_b"),
        _card("stmt:hub"),
        _card("stmt:leaf_a"),
    ]
    graph = {
        "nodes": [{"id": card.id} for card in cards],
        "edges": [
            {"id": "e1", "s": "stmt:hub", "p": "supports", "o": "stmt:leaf_a"},
            {"id": "e2", "s": "stmt:leaf_b", "p": "supports", "o": "stmt:hub"},
            {"id": "e3", "s": "stmt:hub", "p": "member_of_topic", "o": "topic:carbon"},
        ],
    }

    queue = build_review_queue(cards, graph, limit=1)

    assert queue == [
        {
            "statement_id": "stmt:hub",
            "score": 9,
            "reasons": ["high_graph_centrality:3"],
            "kind": "finding",
            "tier": "grounded",
            "confidence": "high",
            "centrality_degree": 3,
            "statement": "stmt:hub statement",
            "evidence_summary": {
                "source_project": "proj_a",
                "source_doc": "REPORT.md",
                "source_section": "Key Findings",
                "exact": "stmt:hub exact evidence",
                "notebook": "analysis.ipynb",
                "figure": None,
                "p_value": None,
            },
            "affected_pages": [],
            "contradictions": [],
            "unresolved_statement_links": [],
        }
    ]
