"""Tests for the KnowledgeIndex."""

from __future__ import annotations

from pathlib import Path

import pytest

from observatory_context.retrieval.knowledge_index import (
    KnowledgeIndex,
    build_knowledge_index,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "knowledge" / "entities" / "organisms.yaml",
        """\
organisms:
  - id: org_adp1
    name: Acinetobacter baylyi ADP1
    strain: ADP1
    projects:
      - essential_genome
      - aromatic_catabolism
  - id: org_dvh
    name: Desulfovibrio vulgaris Hildenborough
    strain: Hildenborough
    projects:
      - metal_fitness_atlas
      - field_vs_lab_fitness
""",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "concepts.yaml",
        """\
concepts:
  - id: conc_essential_genes
    name: Essential genes
    projects:
      - essential_genome
      - conservation_vs_fitness
""",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "genes.yaml",
        """\
genes: []
""",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "pathways.yaml",
        """\
pathways: []
""",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "methods.yaml",
        """\
methods:
  - id: meth_rbtnseq
    name: RB-TnSeq
    projects:
      - essential_genome
""",
    )
    _write(
        tmp_path / "knowledge" / "relations.yaml",
        """\
relations:
  - subject: org_adp1
    predicate: has_essential_gene_data
    object: conc_essential_genes
    evidence_project: essential_genome
    confidence: high
  - subject: org_dvh
    predicate: has_essential_gene_data
    object: conc_essential_genes
    evidence_project: essential_genome
    confidence: high
""",
    )
    _write(
        tmp_path / "knowledge" / "hypotheses.yaml",
        """\
hypotheses:
  - id: H001
    statement: Core genome genes are enriched for metabolic functions.
    status: validated
    origin_project: essential_genome
""",
    )
    return tmp_path


def test_build_knowledge_index_from_sample_repo(sample_repo: Path) -> None:
    index = build_knowledge_index(sample_repo)

    assert index.get_entity("org_adp1") is not None
    assert index.get_entity("org_adp1").name == "Acinetobacter baylyi ADP1"
    assert index.get_entity("org_adp1").kind == "organism"
    assert "essential_genome" in index.get_entity("org_adp1").projects

    assert index.get_entity("conc_essential_genes") is not None
    assert index.get_entity("meth_rbtnseq") is not None

    all_entities = index.list_entities()
    assert len(all_entities) == 4  # 2 organisms + 1 concept + 1 method

    organisms = index.list_entities(kind="organism")
    assert len(organisms) == 2


def test_match_query_finds_entities_by_name_and_alias(sample_repo: Path) -> None:
    index = build_knowledge_index(sample_repo)

    matches = index.match_query("ADP1")
    assert len(matches) >= 1
    assert matches[0].id == "org_adp1"

    matches = index.match_query("Acinetobacter")
    assert len(matches) >= 1
    assert matches[0].id == "org_adp1"

    matches = index.match_query("essential")
    assert any(e.id == "conc_essential_genes" for e in matches)


def test_entity_neighbors_returns_single_hop(sample_repo: Path) -> None:
    index = build_knowledge_index(sample_repo)

    neighbors = index.entity_neighbors("org_adp1")
    assert "conc_essential_genes" in neighbors

    neighbors = index.entity_neighbors("conc_essential_genes")
    assert "org_adp1" in neighbors
    assert "org_dvh" in neighbors


def test_projects_for_entity(sample_repo: Path) -> None:
    index = build_knowledge_index(sample_repo)

    projects = index.projects_for_entity("org_adp1")
    assert "essential_genome" in projects
    assert "aromatic_catabolism" in projects


def test_entities_for_project(sample_repo: Path) -> None:
    index = build_knowledge_index(sample_repo)

    entities = index.entities_for_project("essential_genome")
    assert "org_adp1" in entities
    assert "conc_essential_genes" in entities
    assert "meth_rbtnseq" in entities


def test_entity_connections(sample_repo: Path) -> None:
    index = build_knowledge_index(sample_repo)

    connections = index.entity_connections("org_adp1")
    assert len(connections) == 1
    assert connections[0].predicate == "has_essential_gene_data"
    assert connections[0].object == "conc_essential_genes"


def test_knowledge_index_gracefully_handles_missing_files(tmp_path: Path) -> None:
    index = build_knowledge_index(tmp_path)

    assert index.list_entities() == []
    assert index.match_query("anything") == []
    assert index.entity_neighbors("nothing") == set()
    assert index.get_entity("nope") is None
