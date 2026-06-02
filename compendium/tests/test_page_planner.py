"""Tests for deterministic synthesis-wiki page planning."""

from __future__ import annotations

from compendium.models import (
    AboutRefs,
    EvidenceAnchor,
    ExtractionManifest,
    StatementCard,
    StatementLinks,
)
from compendium.pages import page_id_for_statement, plan_pages


def _manifest(timestamp: str = "2026-06-02T00:00:00Z") -> ExtractionManifest:
    return ExtractionManifest(
        agent_type="llm_extractor",
        skill="kg-ingest-project",
        model="test-model",
        prompt_hash="prompt:abc",
        context_pack_hash="context:def",
        repo_commit="abc123",
        timestamp=timestamp,
    )


def _card(
    *,
    id_: str,
    kind: str,
    statement: str,
    project: str,
    topics: list[str],
    entities: list[str],
    confidence: str = "medium",
    tier: str = "grounded",
    links: StatementLinks | None = None,
    timestamp: str = "2026-06-02T00:00:00Z",
) -> StatementCard:
    return StatementCard(
        id=id_,
        kind=kind,
        statement=statement,
        scope="cross_project" if kind == "claim" else "project_local",
        tier=tier,
        confidence=confidence,
        about=AboutRefs(entities=entities, topics=topics),
        links=links or StatementLinks(),
        qualifiers={"organism": "entity:adp1"},
        evidence=EvidenceAnchor(
            source_project=project,
            source_doc="REPORT.md",
            source_section="Key Findings",
            exact=statement,
        ),
        extraction=_manifest(timestamp),
    )


def _cards() -> list[StatementCard]:
    carbon = "topic:carbon-source-essentiality"
    genetics = "topic:genetics"
    adp1 = "entity:adp1"
    return [
        _card(
            id_="stmt:f1",
            kind="finding",
            statement="ADP1 carbon sources define condition-specific essentiality.",
            project="adp1_deletion_phenotypes",
            topics=[carbon],
            entities=[adp1],
            links=StatementLinks(supports=["stmt:c1"], motivates=["stmt:o1"]),
            timestamp="2026-06-02T00:00:01Z",
        ),
        _card(
            id_="stmt:c1",
            kind="claim",
            statement="ADP1 has a reusable carbon-source essentiality landscape.",
            project="adp1_deletion_phenotypes",
            topics=[carbon],
            entities=[adp1],
            confidence="high",
            links=StatementLinks(motivates=["stmt:o1"]),
            timestamp="2026-06-02T00:00:02Z",
        ),
        _card(
            id_="stmt:o1",
            kind="opportunity",
            statement="Compare ADP1 essential genes across additional carbon sources.",
            project="adp1_deletion_phenotypes",
            topics=[carbon],
            entities=[adp1],
        ),
        _card(
            id_="stmt:f2",
            kind="finding",
            statement="ADP1 project data connects genotype and phenotype evidence.",
            project="acinetobacter_adp1_explorer",
            topics=[carbon, genetics],
            entities=[adp1],
            links=StatementLinks(supports=["stmt:c1"]),
        ),
        _card(
            id_="stmt:v1",
            kind="caveat",
            statement="Carbon-source conclusions depend on tested growth conditions.",
            project="acinetobacter_adp1_explorer",
            topics=[carbon],
            entities=[adp1],
            links=StatementLinks(contradicts=["stmt:c1"]),
        ),
        _card(
            id_="stmt:d1",
            kind="derived_product",
            statement="A reusable ADP1 carbon-source table is available.",
            project="adp1_deletion_phenotypes",
            topics=[carbon],
            entities=[adp1],
        ),
    ]


def _plan_map(cards: list[StatementCard]) -> dict[str, object]:
    return {plan.id: plan for plan in plan_pages(cards)}


def test_page_plans_are_deterministic_for_shuffled_cards() -> None:
    cards = _cards()

    forward = [plan.to_dict() for plan in plan_pages(cards)]
    backward = [plan.to_dict() for plan in plan_pages(list(reversed(cards)))]

    assert forward == backward


def test_home_plan_has_task_6_lanes_and_hashes() -> None:
    home = _plan_map(_cards())["home"]

    assert home.type == "home"
    assert set(home.member_statement_ids) == {"stmt:c1", "stmt:d1", "stmt:v1", "stmt:f2", "stmt:f1", "stmt:o1"}
    assert [section.id for section in home.sections] == [
        "overview",
        "topic_map",
        "strong_claims",
        "conflicts_and_caveats",
        "opportunities_and_directions",
        "reusable_data_products",
        "recent_changes",
        "browse_lanes",
    ]
    sections = {section.id: section for section in home.sections}
    assert sections["strong_claims"].member_statement_ids == ["stmt:c1"]
    assert sections["conflicts_and_caveats"].member_statement_ids == ["stmt:v1"]
    assert sections["opportunities_and_directions"].member_statement_ids == ["stmt:o1"]
    assert sections["reusable_data_products"].member_statement_ids == ["stmt:d1"]
    assert home.member_hash.startswith("hash:")
    assert all(section.member_hash.startswith("hash:") for section in home.sections)


def test_project_entity_and_topic_membership() -> None:
    plans = _plan_map(_cards())
    carbon_topic = plans["topic:carbon-source-essentiality"]
    entity = plans["entity:adp1"]
    deletion_project = plans["project:adp1_deletion_phenotypes"]

    assert set(carbon_topic.member_statement_ids) == {
        "stmt:c1",
        "stmt:d1",
        "stmt:v1",
        "stmt:f2",
        "stmt:f1",
        "stmt:o1",
    }
    assert entity.member_statement_ids == carbon_topic.member_statement_ids
    assert deletion_project.member_statement_ids == ["stmt:c1", "stmt:d1", "stmt:f1", "stmt:o1"]

    entity_sections = {section.id: section for section in entity.sections}
    assert entity_sections["claims"].member_statement_ids == ["stmt:c1"]
    assert set(entity_sections["topic_topic-carbon-source-essentiality"].member_statement_ids) == {
        "stmt:c1",
        "stmt:d1",
        "stmt:v1",
        "stmt:f2",
        "stmt:f1",
        "stmt:o1",
    }


def test_outgoing_links_and_backlinks_are_page_ids() -> None:
    cards = _cards()
    plans = _plan_map(cards)
    claim_page_id = page_id_for_statement(cards[1])
    opportunity_page_id = page_id_for_statement(cards[2])
    assert claim_page_id == "claim:c1"
    assert opportunity_page_id == "opportunity:o1"

    topic = plans["topic:carbon-source-essentiality"]
    claim = plans[claim_page_id]
    opportunity = plans[opportunity_page_id]

    assert set(topic.outgoing_links) >= {
        "claim:c1",
        "entity:adp1",
        "opportunity:o1",
        "project:acinetobacter_adp1_explorer",
        "project:adp1_deletion_phenotypes",
    }
    assert set(claim.outgoing_links) >= {
        "entity:adp1",
        "opportunity:o1",
        "project:adp1_deletion_phenotypes",
        "topic:carbon-source-essentiality",
    }
    assert "home" in claim.backlinks
    assert "topic:carbon-source-essentiality" in claim.backlinks
    assert "claim:c1" in opportunity.backlinks
    assert all(link in plans for link in claim.outgoing_links)
