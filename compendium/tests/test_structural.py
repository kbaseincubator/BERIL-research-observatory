"""Tests for the Stage-1 deterministic structural extractor."""

from __future__ import annotations

import pathlib

import pytest

from compendium.extract.structural import extract_project
from compendium.models import ProjectKG

FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "proj_demo"


@pytest.fixture(scope="module")
def kg() -> ProjectKG:
    return extract_project(FIXTURE)


def _entities(kg: ProjectKG, type_: str) -> list:
    return [e for e in kg.entities if e.type == type_]


def _labels(kg: ProjectKG, type_: str) -> set[str]:
    return {e.label for e in _entities(kg, type_)}


def test_returns_project_kg(kg: ProjectKG) -> None:
    assert isinstance(kg, ProjectKG)


def test_project_meta(kg: ProjectKG) -> None:
    assert kg.project.id == "proj_demo"
    assert kg.project.title == "Acinetobacter baylyi ADP1 Demo Study"
    assert kg.project.report_hash  # non-empty hash of report text
    assert kg.project.stage1_coverage == 0.0


def test_coverage_from_audit() -> None:
    kg = extract_project(FIXTURE, audit={"stage1_coverage": 0.42})
    assert kg.project.stage1_coverage == 0.42


def test_project_entity(kg: ProjectKG) -> None:
    projects = _entities(kg, "Project")
    assert len(projects) == 1
    assert projects[0].label == "Acinetobacter baylyi ADP1 Demo Study"


def test_findings(kg: ProjectKG) -> None:
    findings = [a for a in kg.assertions if a.kind == "finding"]
    assert len(findings) >= 3
    for a in findings:
        assert a.id.startswith("a:")
        assert a.statement
        assert a.evidence is not None
        assert a.evidence.span is not None
        assert a.evidence.span.heading == "Key Findings"
        assert a.tier == "asserted"


def test_opportunities(kg: ProjectKG) -> None:
    opps = [a for a in kg.assertions if a.kind == "opportunity"]
    assert len(opps) >= 2
    for a in opps:
        assert a.id.startswith("a:")
        assert a.statement


def test_dataset_entities(kg: ProjectKG) -> None:
    labels = _labels(kg, "Dataset")
    assert "kescience_fitnessbrowser" in labels
    assert "kbase_ke_pangenome" in labels


def test_dataset_uses_relations(kg: ProjectKG) -> None:
    rels = [a for a in kg.assertions if a.kind == "relation" and a.p == "uses"]
    assert len(rels) >= 2
    for a in rels:
        assert a.id.startswith("a:")
        assert a.s and a.o


def test_organism_canonicalized(kg: ProjectKG) -> None:
    labels = _labels(kg, "Organism")
    assert "Acinetobacter baylyi ADP1" in labels


def test_ko_entity(kg: ProjectKG) -> None:
    labels = _labels(kg, "KO")
    assert "K00845" in labels


def test_publication_entity(kg: ProjectKG) -> None:
    labels = _labels(kg, "Publication")
    assert "PMID:12345678" in labels


def test_entities_deduped_by_node(kg: ProjectKG) -> None:
    nodes = [e.node for e in kg.entities]
    assert len(nodes) == len(set(nodes))


def test_mentions_have_ids_and_spans(kg: ProjectKG) -> None:
    assert kg.mentions
    for m in kg.mentions:
        assert m.id.startswith("proj_demo/m/")
        assert m.span is not None


def test_deterministic(kg: ProjectKG) -> None:
    again = extract_project(FIXTURE)
    assert kg.to_dict() == again.to_dict()


def test_missing_report(tmp_path: pathlib.Path) -> None:
    (tmp_path / "empty_proj").mkdir()
    kg = extract_project(tmp_path / "empty_proj")
    assert isinstance(kg, ProjectKG)
    assert kg.project.id == "empty_proj"
    assert kg.project.report_hash is not None
