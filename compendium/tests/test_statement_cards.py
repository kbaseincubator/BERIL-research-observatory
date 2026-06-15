"""Tests for the simple statement-card contracts."""

from __future__ import annotations

import json

import pytest
import yaml

from compendium.models import (
    EvidenceAnchor,
    PagePlan,
    PageSectionPlan,
    StatementCard,
    StatementLinks,
)


def _evidence() -> EvidenceAnchor:
    return EvidenceAnchor(
        source_project="adp1_deletion_phenotypes",
        source_doc="REPORT.md",
        source_section="Key Findings",
        quote="Carbon sources define a three-tier essentiality landscape",
    )


def _card() -> StatementCard:
    return StatementCard(
        id="stmt:abc123",
        kind="finding",
        text="Carbon sources define a three-tier essentiality landscape in ADP1.",
        confidence="medium",
        topics=["topic:carbon-source-essentiality"],
        entities=["entity:adp1"],
        links=StatementLinks(supports=["stmt:def456"]),
        evidence=[_evidence()],
    )


def test_statement_card_round_trips_through_json_and_yaml() -> None:
    card = _card()

    json_payload = json.loads(json.dumps(card.to_dict(), sort_keys=True))
    yaml_payload = yaml.safe_load(yaml.safe_dump(card.to_dict(), sort_keys=True))

    assert StatementCard.from_dict(json_payload).to_dict() == card.to_dict()
    assert StatementCard.from_dict(yaml_payload).to_dict() == card.to_dict()


def test_statement_card_requires_evidence_quote() -> None:
    with pytest.raises(ValueError, match="quote is required"):
        EvidenceAnchor(
            source_project="adp1_deletion_phenotypes",
            source_doc="REPORT.md",
            quote="",
        )

    with pytest.raises(ValueError, match="evidence is required"):
        StatementCard(
            id="stmt:abc123",
            kind="finding",
            text="ADP1 grows on quinate.",
            confidence="medium",
            topics=[],
            entities=[],
            links=StatementLinks(),
            evidence=[],
        )


def test_statement_card_rejects_legacy_kind() -> None:
    payload = _card().to_dict()
    payload["kind"] = "derived_product"

    with pytest.raises(ValueError, match="kind must be one of"):
        StatementCard.from_dict(payload)


def test_statement_links_reject_unknown_link_fields() -> None:
    payload = _card().to_dict()
    payload["links"]["requires_human_review"] = ["stmt:future"]

    with pytest.raises(ValueError, match="unsupported statement link"):
        StatementCard.from_dict(payload)


def test_statement_card_reads_legacy_field_names_for_migration() -> None:
    payload = {
        "id": "stmt:legacy",
        "kind": "finding",
        "statement": "Legacy statement text.",
        "confidence": "high",
        "about": {"topics": ["topic:x"], "entities": ["entity:y"]},
        "links": {"supports": [], "contradicts": [], "refines": []},
        "evidence": {
            "source_project": "proj",
            "source_doc": "REPORT.md",
            "exact": "Legacy evidence text.",
        },
    }

    card = StatementCard.from_dict(payload)

    assert card.text == "Legacy statement text."
    assert card.topics == ["topic:x"]
    assert card.entities == ["entity:y"]
    assert card.evidence[0].quote == "Legacy evidence text."


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
        outgoing_links=["topic:carbon-source-essentiality"],
        backlinks=["home"],
        member_hash="hash:page",
    )

    assert PagePlan.from_dict(plan.to_dict()).to_dict() == plan.to_dict()
