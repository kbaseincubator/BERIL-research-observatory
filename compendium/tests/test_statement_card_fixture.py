"""Tests for curated statement-card fixtures."""

from __future__ import annotations

from pathlib import Path

import yaml

from compendium.validate import validate_project_kg_file


ROOT = Path(__file__).resolve().parents[2]
COMPENDIUM = ROOT / "compendium"
FIXTURE = COMPENDIUM / "fixtures" / "statement_cards" / "adp1_tracer.yaml"
PROJECTS = ROOT / "projects"


def test_adp1_tracer_fixture_validates_as_project_kg() -> None:
    payload = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))

    result = validate_project_kg_file(FIXTURE)
    cards = result.records
    kinds = [card.kind for card in cards]

    assert payload["project"]["id"] == "adp1_tracer"
    assert result.artifact_type == "project_kg"
    assert result.count == 6
    assert kinds.count("finding") >= 2
    assert kinds.count("claim") >= 2
    assert "opportunity" in kinds
    assert any(kind in {"caveat", "conflict"} for kind in kinds)
    assert {card.evidence.source_project for card in cards} == {
        "adp1_deletion_phenotypes",
        "adp1_triple_essentiality",
    }
    assert all("entity:adp1" in card.about.entities for card in cards)
    assert all("topic:adp1-carbon-fitness" in card.about.topics for card in cards)


def test_adp1_tracer_evidence_exact_text_resolves() -> None:
    result = validate_project_kg_file(FIXTURE)

    for card in result.records:
        source = PROJECTS / card.evidence.source_project / card.evidence.source_doc
        source_text = source.read_text(encoding="utf-8")

        assert card.evidence.exact in source_text, card.id
