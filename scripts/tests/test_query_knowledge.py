"""Tests for deterministic render functions in query_knowledge_unified.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import scripts.query_knowledge_unified as query_knowledge


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


@pytest.fixture
def knowledge_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    docs_dir = tmp_path / "docs"
    knowledge_dir = tmp_path / "knowledge"

    _write_yaml(
        docs_dir / "project_registry.yaml",
        {
            "projects": [
                {"id": "essential_genome", "status": "complete"},
                {"id": "orphan_project", "status": "proposed"},
            ]
        },
    )
    _write_yaml(docs_dir / "figure_catalog.yaml", {"figures": []})
    (docs_dir / "findings_digest.md").write_text("# Findings\n", encoding="utf-8")

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

    monkeypatch.setattr(query_knowledge, "DOCS_DIR", docs_dir)
    monkeypatch.setattr(query_knowledge, "KNOWLEDGE_DIR", knowledge_dir)
    monkeypatch.setattr(query_knowledge, "REGISTRY_PATH", docs_dir / "project_registry.yaml")
    monkeypatch.setattr(query_knowledge, "FIGURE_CATALOG_PATH", docs_dir / "figure_catalog.yaml")
    monkeypatch.setattr(query_knowledge, "FINDINGS_DIGEST_PATH", docs_dir / "findings_digest.md")
    monkeypatch.setattr(query_knowledge, "GRAPH_COVERAGE_PATH", docs_dir / "knowledge_graph_coverage.md")
    monkeypatch.setattr(query_knowledge, "GAPS_PATH", docs_dir / "knowledge_gaps.md")

    return tmp_path


def test_backfill_parser_accepts_optional_project_id() -> None:
    parser = query_knowledge.build_parser()

    args = parser.parse_args(["backfill", "essential_genome"])

    assert args.command == "backfill"
    assert args.project_id == "essential_genome"


def test_render_backfill_reports_single_project_status(knowledge_artifacts: Path) -> None:
    output = query_knowledge._render_backfill("essential_genome")

    assert "essential_genome" in output
    assert "already has Layer 3 coverage" in output


def test_render_backfill_reports_missing_project_coverage(knowledge_artifacts: Path) -> None:
    output = query_knowledge._render_backfill("orphan_project")

    assert "orphan_project" in output
    assert "missing Layer 3 coverage" in output
