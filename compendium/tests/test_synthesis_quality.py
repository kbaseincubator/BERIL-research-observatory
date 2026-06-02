"""Tests for v4 statement-card synthesis quality metrics."""

from __future__ import annotations

import pathlib

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
from compendium.quality.synthesis_quality import assess_synthesis_quality


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
    project: str = "proj_a",
    exact: str = "ADP1 grows on quinate.",
    links: StatementLinks | None = None,
    qualifiers: dict[str, str] | None = None,
    topics: list[str] | None = None,
) -> StatementCard:
    return StatementCard(
        id=id_,
        kind=kind,
        statement=f"{id_} statement",
        scope="project_local",
        tier=tier,
        confidence="high",
        about=AboutRefs(
            entities=["entity:adp1"],
            topics=["topic:carbon"] if topics is None else topics,
        ),
        links=links or StatementLinks(),
        qualifiers=qualifiers or {"organism": "entity:adp1"},
        evidence=EvidenceAnchor(
            source_project=project,
            source_doc="REPORT.md",
            source_section="Key Findings",
            exact=exact,
        ),
        extraction=_manifest(),
    )


def _page(
    id_: str,
    *,
    type_: str,
    members: list[str],
    outgoing: list[str] | None = None,
    backlinks: list[str] | None = None,
) -> PagePlan:
    return PagePlan(
        id=id_,
        type=type_,
        title=id_,
        member_statement_ids=members,
        sections=[
            PageSectionPlan(
                id="main",
                heading="Main",
                member_statement_ids=list(members),
                member_hash="hash:test",
            )
        ],
        outgoing_links=outgoing or [],
        backlinks=backlinks or [],
        member_hash="hash:test",
    )


def test_synthesis_quality_counts_evidence_opportunities_and_conflicts(
    tmp_path: pathlib.Path,
) -> None:
    source_dir = tmp_path / "proj_a"
    source_dir.mkdir()
    (source_dir / "REPORT.md").write_text(
        "Key Findings\n\nADP1 grows on quinate.\nA reusable table was generated.\n",
        encoding="utf-8",
    )
    cards = [
        _card(
            "stmt:finding",
            links=StatementLinks(supports=["stmt:asserted"], contradicts=["stmt:conflict"]),
        ),
        _card("stmt:asserted", kind="claim", tier="asserted"),
        _card("stmt:conflict", kind="conflict", tier="conflict"),
        _card(
            "stmt:opportunity",
            kind="opportunity",
            exact="A reusable table was generated.",
            links=StatementLinks(motivates=["stmt:product"]),
        ),
        _card("stmt:product", kind="derived_product", exact="A reusable table was generated."),
        _card("stmt:missing_evidence", project="proj_b", exact="This span is absent."),
    ]
    graph = {
        "nodes": [{"id": card.id, "type": "statement_card"} for card in cards],
        "edges": [
            {"id": "e1", "s": "stmt:finding", "p": "supports", "o": "stmt:asserted"},
            {"id": "e2", "s": "stmt:asserted", "p": "about_entity", "o": "stmt:finding"},
            {"id": "e3", "s": "stmt:asserted", "p": "member_of_topic", "o": "stmt:conflict"},
            {"id": "e4", "s": "stmt:asserted", "p": "supports", "o": "stmt:opportunity"},
        ],
    }
    pages = [
        _page("home", type_="home", members=[card.id for card in cards], outgoing=["claim:asserted"]),
        _page("claim:asserted", type_="claim", members=["stmt:asserted"], backlinks=["home"]),
    ]

    metrics = assess_synthesis_quality(cards, graph, pages, source_root=tmp_path)

    assert metrics["statement_counts"]["by_kind"] == {
        "claim": 1,
        "conflict": 1,
        "derived_product": 1,
        "finding": 2,
        "opportunity": 1,
    }
    assert metrics["statement_counts"]["by_tier"] == {"asserted": 1, "conflict": 1, "grounded": 4}
    assert metrics["statement_counts"]["by_source_project"] == {"proj_a": 5, "proj_b": 1}
    assert metrics["evidence_resolution"]["resolved"] == 5
    assert metrics["evidence_resolution"]["rate"] == 5 / 6
    assert metrics["evidence_resolution"]["unresolved_statement_ids"] == ["stmt:missing_evidence"]
    assert metrics["topic_coverage"]["topic_statement_counts"] == {"topic:carbon": 6}
    assert metrics["topic_coverage"]["topics_without_pages"] == ["topic:carbon"]
    assert metrics["claim_balance"] == {
        "total_claims": 1,
        "supported_claims": 1,
        "refuted_claims": 0,
        "unsupported_claim_statement_ids": [],
        "support_link_count": 1,
        "refutation_link_count": 0,
        "net_support_balance": 1,
        "claims": [
            {
                "statement_id": "stmt:asserted",
                "support_count": 1,
                "refutation_count": 0,
                "supporting_statement_ids": ["stmt:finding"],
                "refuting_statement_ids": [],
            }
        ],
    }
    assert metrics["opportunity_targets"]["with_target_outputs"] == 1
    assert metrics["opportunity_targets"]["opportunities"] == [
        {"statement_id": "stmt:opportunity", "target_outputs": ["stmt:product"]}
    ]
    assert metrics["active_conflicts"] == {
        "count": 2,
        "conflict_statement_ids": ["stmt:conflict"],
        "contradiction_links": [
            {"source_statement_id": "stmt:finding", "target_statement_id": "stmt:conflict"}
        ],
    }
    assert metrics["high_centrality_asserted_statements"] == [
        {"statement_id": "stmt:asserted", "degree": 4}
    ]


def test_synthesis_quality_reports_graph_and_page_integrity() -> None:
    cards = [
        _card("stmt:a"),
        _card("stmt:b", kind="opportunity", qualifiers={"target_output": "dataset:carbon_table"}),
    ]
    graph = {
        "nodes": [{"id": "stmt:a"}, {"id": "stmt:b"}],
        "edges": [
            {"id": "ok", "s": "stmt:a", "p": "supports", "o": "stmt:b"},
            {"id": "dangling", "s": "stmt:b", "p": "supports", "o": "stmt:missing"},
        ],
    }
    pages = [
        _page(
            "home",
            type_="home",
            members=["stmt:a"],
            outgoing=["opportunity:b", "missing:page"],
        ),
        _page("opportunity:b", type_="opportunity", members=["stmt:b", "stmt:unknown"]),
        _page("orphan:page", type_="topic", members=[]),
    ]

    metrics = assess_synthesis_quality(cards, graph, pages)

    assert metrics["evidence_resolution"] == {
        "checked": False,
        "total": 2,
        "resolved": 0,
        "unresolved": 2,
        "rate": None,
        "unresolved_statement_ids": ["stmt:a", "stmt:b"],
    }
    assert metrics["graph_integrity"]["dangling_edges"] == 1
    assert metrics["graph_integrity"]["dangling_edge_details"] == [
        {
            "edge_id": "dangling",
            "source": "stmt:b",
            "predicate": "supports",
            "target": "stmt:missing",
            "missing_endpoints": ["stmt:missing"],
        }
    ]
    assert metrics["page_integrity"]["pages_by_type"] == {
        "home": 1,
        "opportunity": 1,
        "topic": 1,
    }
    assert metrics["page_integrity"]["orphan_pages"] == ["orphan:page"]
    assert metrics["page_integrity"]["weakly_connected_pages"] == [
        {"page_id": "opportunity:b", "link_degree": 0, "member_count": 2},
        {"page_id": "orphan:page", "link_degree": 0, "member_count": 0},
    ]
    assert metrics["page_integrity"]["unknown_page_members"] == [
        {"page_id": "opportunity:b", "member_statement_id": "stmt:unknown"}
    ]
    assert metrics["page_integrity"]["unknown_section_members"] == [
        {
            "page_id": "opportunity:b",
            "section_id": "main",
            "member_statement_id": "stmt:unknown",
        }
    ]
    assert metrics["link_integrity"]["broken_outgoing_links"] == [
        {"page_id": "home", "target_page_id": "missing:page"}
    ]
    assert metrics["link_integrity"]["missing_backlinks"] == [
        {"page_id": "home", "target_page_id": "opportunity:b"}
    ]
    assert metrics["opportunity_targets"]["opportunities"] == [
        {"statement_id": "stmt:b", "target_outputs": ["dataset:carbon_table"]}
    ]


def test_synthesis_quality_reports_topic_coverage_claim_balance_and_page_changes() -> None:
    cards = [
        _card(
            "stmt:support",
            links=StatementLinks(supports=["stmt:claim"]),
            topics=["topic:carbon"],
        ),
        _card(
            "stmt:refute",
            links=StatementLinks(contradicts=["stmt:claim"]),
            topics=["topic:missing"],
        ),
        _card("stmt:claim", kind="claim", tier="asserted", topics=["topic:carbon"]),
        _card("stmt:untopiced", topics=[]),
    ]
    topic_page = _page(
        "topic:carbon",
        type_="topic",
        members=["stmt:support", "stmt:claim"],
        outgoing=["claim:claim"],
        backlinks=["home"],
    )
    claim_page = _page(
        "claim:claim",
        type_="claim",
        members=["stmt:claim"],
        outgoing=[],
        backlinks=["topic:carbon"],
    )
    setattr(topic_page, "regenerated", True)
    setattr(claim_page, "changed", True)

    metrics = assess_synthesis_quality(
        cards,
        graph={"nodes": [{"id": card.id} for card in cards], "edges": []},
        page_plans=[topic_page, claim_page],
    )

    assert metrics["topic_coverage"] == {
        "topic_count": 2,
        "topic_page_count": 1,
        "covered_topic_count": 1,
        "coverage_rate": 0.5,
        "topics_without_pages": ["topic:missing"],
        "topic_pages_without_statements": [],
        "statements_with_topics": 3,
        "statements_without_topics": ["stmt:untopiced"],
        "topic_statement_counts": {"topic:carbon": 2, "topic:missing": 1},
    }
    assert metrics["claim_balance"] == {
        "total_claims": 1,
        "supported_claims": 1,
        "refuted_claims": 1,
        "unsupported_claim_statement_ids": [],
        "support_link_count": 1,
        "refutation_link_count": 1,
        "net_support_balance": 0,
        "claims": [
            {
                "statement_id": "stmt:claim",
                "support_count": 1,
                "refutation_count": 1,
                "supporting_statement_ids": ["stmt:support"],
                "refuting_statement_ids": ["stmt:refute"],
            }
        ],
    }
    assert metrics["synthesis_page_changes"] == {
        "available": True,
        "tracked_page_count": 2,
        "regenerated": 1,
        "changed": 1,
        "regenerated_page_ids": ["topic:carbon"],
        "changed_page_ids": ["claim:claim"],
    }


def test_synthesis_quality_reports_unresolved_statement_links() -> None:
    cards = [
        _card("stmt:a", links=StatementLinks(supports=["stmt:missing"])),
        _card("stmt:b"),
    ]
    graph = {
        "nodes": [{"id": "stmt:a"}, {"id": "stmt:b"}, {"id": "stmt:missing"}],
        "edges": [{"id": "materialized", "s": "stmt:a", "p": "supports", "o": "stmt:missing"}],
    }
    pages = [_page("home", type_="home", members=["stmt:a", "stmt:b"])]

    metrics = assess_synthesis_quality(cards, graph, pages)

    assert metrics["graph_integrity"]["dangling_edges"] == 0
    assert metrics["statement_link_integrity"] == {
        "unresolved_statement_link_count": 1,
        "unresolved_statement_links": [
            {
                "source_statement_id": "stmt:a",
                "link_kind": "supports",
                "target_statement_id": "stmt:missing",
            }
        ],
    }


def test_synthesis_quality_ignores_retracted_opportunity_target_products() -> None:
    cards = [
        _card(
            "stmt:opportunity",
            kind="opportunity",
            links=StatementLinks(motivates=["stmt:product"]),
        ),
        _card("stmt:product", kind="derived_product", tier=TIER_RETRACTED),
    ]
    graph = {
        "nodes": [{"id": "stmt:opportunity"}, {"id": "stmt:product"}],
        "edges": [{"id": "motivation", "s": "stmt:opportunity", "p": "motivates", "o": "stmt:product"}],
    }
    pages = [_page("home", type_="home", members=["stmt:opportunity"])]

    metrics = assess_synthesis_quality(cards, graph, pages)

    assert metrics["opportunity_targets"]["missing_target_output_statement_ids"] == [
        "stmt:opportunity"
    ]
    assert metrics["statement_link_integrity"]["unresolved_statement_links"] == [
        {
            "source_statement_id": "stmt:opportunity",
            "link_kind": "motivates",
            "target_statement_id": "stmt:product",
        }
    ]


def test_synthesis_quality_ignores_retracted_cards_for_evidence_resolution(
    tmp_path: pathlib.Path,
) -> None:
    source_dir = tmp_path / "proj_a"
    source_dir.mkdir()
    (source_dir / "REPORT.md").write_text("ADP1 grows on quinate.", encoding="utf-8")
    cards = [
        _card("stmt:published"),
        _card("stmt:retracted", tier=TIER_RETRACTED, exact="Missing retracted span."),
    ]

    metrics = assess_synthesis_quality(
        cards,
        graph={"nodes": [{"id": card.id} for card in cards], "edges": []},
        page_plans=[_page("home", type_="home", members=["stmt:published"])],
        source_root=tmp_path,
    )

    assert metrics["evidence_resolution"]["total"] == 1
    assert metrics["evidence_resolution"]["resolved"] == 1
    assert metrics["evidence_resolution"]["unresolved_statement_ids"] == []
