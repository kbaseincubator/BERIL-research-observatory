"""Essential tests for CBORG extraction models and prompt generation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from observatory_context.extraction import CBORGExtractor, Entity, EntityExtraction, Relation


def _make_extractor() -> CBORGExtractor:
    return CBORGExtractor(
        api_url="https://api.cborg.lbl.gov/v1",
        model="openai/gpt-4o-mini",
        api_key="test-key",
    )


def test_entity_rejects_invalid_type() -> None:
    with pytest.raises(ValidationError):
        Entity(type="invalid", id="x", name="X")  # type: ignore[arg-type]


def test_relation_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        Relation(
            subject="s",
            predicate="p",
            object="o",
            evidence="e",
            confidence="unknown",  # type: ignore[arg-type]
        )


def test_entity_extraction_uses_independent_defaults() -> None:
    left = EntityExtraction()
    right = EntityExtraction()

    left.entities.append(Entity(type="gene", id="g1", name="Gene A"))

    assert right.entities == []
    assert right.relations == []


def test_build_extraction_prompt_includes_report_and_provenance() -> None:
    extractor = _make_extractor()

    prompt = extractor._build_extraction_prompt(
        report="Gene X knockout reduced fitness.",
        provenance={"project": "essential_genome", "date": "2024-01-01"},
    )

    assert "Gene X knockout reduced fitness." in prompt
    assert "essential_genome" in prompt
    assert "2024-01-01" in prompt
