"""Tests for scripts/validate_knowledge_graph.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_knowledge_graph.py"
SPEC = importlib.util.spec_from_file_location("validate_knowledge_graph", MODULE_PATH)
assert SPEC and SPEC.loader
validate_knowledge_graph = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_knowledge_graph)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_validate_graph_passes_for_consistent_data(tmp_path, monkeypatch) -> None:
    projects_dir = tmp_path / "projects"
    for project_id in ("essential_genome", "metal_fitness_atlas"):
        project_dir = projects_dir / project_id
        project_dir.mkdir(parents=True)
        (project_dir / "README.md").write_text(f"# {project_id}\n", encoding="utf-8")

    knowledge_dir = tmp_path / "knowledge"
    _write_yaml(
        knowledge_dir / "entities/genes.yaml",
        {"genes": [{"id": "gene_a", "name": "Gene A", "projects": ["essential_genome"]}]},
    )
    _write_yaml(
        knowledge_dir / "entities/concepts.yaml",
        {"concepts": [{"id": "concept_b", "name": "Concept B", "projects": ["metal_fitness_atlas"]}]},
    )
    _write_yaml(knowledge_dir / "entities/organisms.yaml", {"organisms": []})
    _write_yaml(knowledge_dir / "entities/pathways.yaml", {"pathways": []})
    _write_yaml(knowledge_dir / "entities/methods.yaml", {"methods": []})
    _write_yaml(
        knowledge_dir / "relations.yaml",
        {
            "relations": [
                {
                    "subject": "gene_a",
                    "predicate": "supports",
                    "object": "concept_b",
                    "evidence_project": "essential_genome",
                }
            ]
        },
    )
    _write_yaml(
        knowledge_dir / "hypotheses.yaml",
        {
            "hypotheses": [
                {
                    "id": "H001",
                    "status": "testing",
                    "statement": "A test hypothesis.",
                    "origin_project": "metal_fitness_atlas",
                    "entities": ["gene_a", "concept_b"],
                }
            ]
        },
    )
    _write_yaml(
        knowledge_dir / "timeline.yaml",
        {
            "events": [
                {
                    "date": "2026-01-10",
                    "type": "hypothesis_proposed",
                    "project": "essential_genome",
                    "summary": "Hypothesis opened.",
                }
            ]
        },
    )

    monkeypatch.setattr(validate_knowledge_graph, "PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(validate_knowledge_graph, "KNOWLEDGE_DIR", knowledge_dir)

    assert validate_knowledge_graph.main() == 0


def test_validate_graph_fails_on_unknown_relation_entity(tmp_path, monkeypatch) -> None:
    projects_dir = tmp_path / "projects"
    project_dir = projects_dir / "essential_genome"
    project_dir.mkdir(parents=True)
    (project_dir / "README.md").write_text("# essential_genome\n", encoding="utf-8")

    knowledge_dir = tmp_path / "knowledge"
    _write_yaml(knowledge_dir / "entities/genes.yaml", {"genes": []})
    _write_yaml(knowledge_dir / "entities/concepts.yaml", {"concepts": []})
    _write_yaml(knowledge_dir / "entities/organisms.yaml", {"organisms": []})
    _write_yaml(knowledge_dir / "entities/pathways.yaml", {"pathways": []})
    _write_yaml(knowledge_dir / "entities/methods.yaml", {"methods": []})
    _write_yaml(
        knowledge_dir / "relations.yaml",
        {
            "relations": [
                {
                    "subject": "missing_gene",
                    "predicate": "supports",
                    "object": "missing_concept",
                    "evidence_project": "essential_genome",
                }
            ]
        },
    )
    _write_yaml(knowledge_dir / "hypotheses.yaml", {"hypotheses": []})
    _write_yaml(knowledge_dir / "timeline.yaml", {"events": []})

    monkeypatch.setattr(validate_knowledge_graph, "PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(validate_knowledge_graph, "KNOWLEDGE_DIR", knowledge_dir)

    assert validate_knowledge_graph.main() == 1
