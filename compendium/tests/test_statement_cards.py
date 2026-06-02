"""Tests for synthesis-wiki statement-card contracts."""

from __future__ import annotations

import json

import pytest
import yaml

from compendium.models import (
    AboutRefs,
    EvidenceAnchor,
    ExtractionManifest,
    PagePlan,
    PageSectionPlan,
    StatementCard,
    StatementEdge,
    StatementLinks,
)


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


def _evidence() -> EvidenceAnchor:
    return EvidenceAnchor(
        source_project="adp1_deletion_phenotypes",
        source_doc="REPORT.md",
        source_section="Key Findings",
        exact="Carbon sources define a three-tier essentiality landscape",
        prefix="The deletion screen showed that ",
        suffix=" across tested conditions.",
    )


def _card() -> StatementCard:
    return StatementCard(
        id="stmt:abc123",
        kind="finding",
        statement="Carbon sources define a three-tier essentiality landscape in ADP1.",
        scope="project_local",
        tier="asserted",
        confidence="medium",
        about=AboutRefs(
            entities=["entity:adp1"],
            topics=["topic:carbon-source-essentiality"],
        ),
        links=StatementLinks(
            supports=["stmt:def456"],
            motivates=["stmt:ghi789"],
        ),
        qualifiers={
            "organism": "entity:adp1",
            "condition": "quinate",
            "method": "RB-TnSeq",
        },
        evidence=_evidence(),
        extraction=_manifest(),
    )


def test_statement_card_round_trips_through_json_and_yaml() -> None:
    card = _card()

    json_payload = json.loads(json.dumps(card.to_dict(), sort_keys=True))
    yaml_payload = yaml.safe_load(yaml.safe_dump(card.to_dict(), sort_keys=True))

    assert StatementCard.from_dict(json_payload).to_dict() == card.to_dict()
    assert StatementCard.from_dict(yaml_payload).to_dict() == card.to_dict()


def test_statement_card_requires_exact_evidence_text() -> None:
    with pytest.raises(ValueError, match="exact is required"):
        EvidenceAnchor(
            source_project="adp1_deletion_phenotypes",
            source_doc="REPORT.md",
            exact="",
        )

    with pytest.raises(ValueError, match="evidence is required"):
        StatementCard(
            id="stmt:abc123",
            kind="finding",
            statement="ADP1 grows on quinate.",
            scope="project_local",
            tier="asserted",
            confidence="medium",
            about=AboutRefs(),
            links=StatementLinks(),
            qualifiers={},
            evidence=None,  # type: ignore[arg-type]
            extraction=_manifest(),
        )


def test_statement_edge_validates_class_vocabulary() -> None:
    edge = StatementEdge(
        s="stmt:abc123",
        p="supports",
        o="stmt:def456",
        edge_class="scientific_edge",
        statement_ids=["stmt:abc123"],
    )

    assert StatementEdge.from_dict(edge.to_dict()).to_dict() == edge.to_dict()

    with pytest.raises(ValueError, match="p must be one of"):
        StatementEdge(
            s="stmt:abc123",
            p="supports",
            o="stmt:def456",
            edge_class="provenance_edge",
        )


def test_page_plan_round_trips() -> None:
    plan = PagePlan(
        id="topic:adp1",
        type="topic",
        title="ADP1",
        member_statement_ids=["stmt:abc123"],
        sections=[
            PageSectionPlan(
                id="overview",
                heading="Overview",
                member_statement_ids=["stmt:abc123"],
                member_hash="hash:section",
            )
        ],
        outgoing_links=["claim:carbon-source-essentiality"],
        backlinks=["home"],
        member_hash="hash:page",
    )

    assert PagePlan.from_dict(plan.to_dict()).to_dict() == plan.to_dict()
