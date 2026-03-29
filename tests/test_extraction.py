"""Tests for CBORGExtractor schema models and class initialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from observatory_context.extraction import (
    CBORGExtractor,
    Entity,
    EntityExtraction,
    HypothesisUpdate,
    Relation,
    TimelineEvent,
)


# --- Entity ---


class TestEntity:
    def test_construction(self) -> None:
        entity = Entity(type="organism", id="org_1", name="E. coli")
        assert entity.type == "organism"
        assert entity.id == "org_1"
        assert entity.name == "E. coli"
        assert entity.metadata == {}

    def test_all_valid_types(self) -> None:
        for t in ("organism", "gene", "pathway", "method", "concept"):
            e = Entity(type=t, id="x", name="X")  # type: ignore[arg-type]
            assert e.type == t

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Entity(type="invalid", id="x", name="X")  # type: ignore[arg-type]

    def test_metadata_default_independent(self) -> None:
        a = Entity(type="gene", id="g1", name="Gene A")
        b = Entity(type="gene", id="g2", name="Gene B")
        a.metadata["key"] = "value"
        assert b.metadata == {}

    def test_custom_metadata(self) -> None:
        entity = Entity(type="gene", id="g1", name="Gene A", metadata={"db": "NCBI"})
        assert entity.metadata["db"] == "NCBI"


# --- Relation ---


class TestRelation:
    def test_construction(self) -> None:
        rel = Relation(
            subject="org_1",
            predicate="has_gene",
            object="gene_1",
            evidence="paper_123",
            confidence="high",
        )
        assert rel.subject == "org_1"
        assert rel.predicate == "has_gene"
        assert rel.object == "gene_1"
        assert rel.evidence == "paper_123"
        assert rel.confidence == "high"

    def test_valid_confidence_values(self) -> None:
        for conf in ("high", "moderate", "low"):
            r = Relation(
                subject="s",
                predicate="p",
                object="o",
                evidence="e",
                confidence=conf,  # type: ignore[arg-type]
            )
            assert r.confidence == conf

    def test_invalid_confidence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Relation(
                subject="s",
                predicate="p",
                object="o",
                evidence="e",
                confidence="unknown",  # type: ignore[arg-type]
            )


# --- HypothesisUpdate ---


class TestHypothesisUpdate:
    def test_construction(self) -> None:
        update = HypothesisUpdate(
            id="hyp_1",
            status="supported",
            claim="Gene X is essential",
            evidence_delta="Observed in 5 experiments",
        )
        assert update.id == "hyp_1"
        assert update.status == "supported"
        assert update.claim == "Gene X is essential"
        assert update.evidence_delta == "Observed in 5 experiments"

    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            HypothesisUpdate(id="h1", status="supported")  # type: ignore[call-arg]


# --- TimelineEvent ---


class TestTimelineEvent:
    def test_construction(self) -> None:
        event = TimelineEvent(
            date="2024-01-15",
            event="Started genome sequencing",
            type="milestone",
            project="essential_genome",
        )
        assert event.date == "2024-01-15"
        assert event.event == "Started genome sequencing"
        assert event.type == "milestone"
        assert event.project == "essential_genome"

    def test_project_optional(self) -> None:
        event = TimelineEvent(date="2024-01-15", event="Lab meeting", type="meeting")
        assert event.project is None

    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            TimelineEvent(date="2024-01-15", event="Something")  # type: ignore[call-arg]


# --- EntityExtraction ---


class TestEntityExtraction:
    def test_empty_defaults(self) -> None:
        result = EntityExtraction()
        assert result.entities == []
        assert result.relations == []
        assert result.hypotheses == []
        assert result.timeline_events == []

    def test_construction_with_data(self) -> None:
        entity = Entity(type="gene", id="g1", name="Gene A")
        relation = Relation(
            subject="g1", predicate="in_pathway", object="p1", evidence="ref", confidence="moderate"
        )
        hypothesis = HypothesisUpdate(
            id="h1", status="open", claim="Gene A is essential", evidence_delta="none yet"
        )
        timeline = TimelineEvent(date="2024-02-01", event="Analysis started", type="start")
        result = EntityExtraction(
            entities=[entity],
            relations=[relation],
            hypotheses=[hypothesis],
            timeline_events=[timeline],
        )
        assert len(result.entities) == 1
        assert len(result.relations) == 1
        assert len(result.hypotheses) == 1
        assert len(result.timeline_events) == 1

    def test_mutable_defaults_are_independent(self) -> None:
        a = EntityExtraction()
        b = EntityExtraction()
        a.entities.append(Entity(type="gene", id="g1", name="Gene A"))
        assert b.entities == []


# --- CBORGExtractor ---


class TestCBORGExtractor:
    def test_stores_model_name(self) -> None:
        extractor = CBORGExtractor(
            api_url="https://api.cborg.lbl.gov/v1",
            model="openai/gpt-4o-mini",
            api_key="test-key",
        )
        assert extractor.model == "openai/gpt-4o-mini"

    def test_build_extraction_prompt_contains_schema(self) -> None:
        extractor = CBORGExtractor(
            api_url="https://api.cborg.lbl.gov/v1",
            model="openai/gpt-4o-mini",
            api_key="test-key",
        )
        prompt = extractor._build_extraction_prompt(
            report="Gene X knockout reduced fitness.",
            provenance={"project": "essential_genome", "date": "2024-01-01"},
        )
        assert "entities" in prompt
        assert "relations" in prompt
        assert "hypotheses" in prompt
        assert "timeline_events" in prompt

    def test_build_extraction_prompt_includes_report(self) -> None:
        extractor = CBORGExtractor(
            api_url="https://api.cborg.lbl.gov/v1",
            model="openai/gpt-4o-mini",
            api_key="test-key",
        )
        report_text = "Gene X knockout reduced fitness."
        prompt = extractor._build_extraction_prompt(
            report=report_text,
            provenance={"project": "essential_genome"},
        )
        assert report_text in prompt

    def test_build_extraction_prompt_includes_provenance(self) -> None:
        extractor = CBORGExtractor(
            api_url="https://api.cborg.lbl.gov/v1",
            model="openai/gpt-4o-mini",
            api_key="test-key",
        )
        prompt = extractor._build_extraction_prompt(
            report="Some report.",
            provenance={"project": "essential_genome", "date": "2024-01-01"},
        )
        assert "essential_genome" in prompt
