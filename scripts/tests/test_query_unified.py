"""Tests for the unified query script."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def sample_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _write(
        tmp_path / "docs" / "project_registry.yaml",
        """\
projects:
  - id: alpha_proj
    title: Alpha Project
    status: complete
    tags: [metal-stress, fitness]
    research_question: How does alpha respond?
    key_findings:
      - Alpha is resilient
    databases_used: []
    key_data_artifacts: []
    depends_on: []
    enables: []
    has_provenance: true
""",
    )
    _write(
        tmp_path / "docs" / "figure_catalog.yaml",
        """\
figure_count: 1
figures:
  - id: alpha_proj__main
    project: alpha_proj
    file: main.png
    caption: Main alpha figure
    tags: [metal-stress]
""",
    )
    _write(tmp_path / "docs" / "findings_digest.md", "# Findings\n\nAlpha is resilient.\n")
    _write(
        tmp_path / "knowledge" / "entities" / "organisms.yaml",
        "organisms:\n  - id: org_alpha\n    name: Alpha organism\n    projects: [alpha_proj]\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "genes.yaml",
        "genes: []\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "pathways.yaml",
        "pathways: []\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "methods.yaml",
        "methods: []\n",
    )
    _write(
        tmp_path / "knowledge" / "entities" / "concepts.yaml",
        "concepts: []\n",
    )
    _write(
        tmp_path / "knowledge" / "relations.yaml",
        "relations: []\n",
    )
    _write(
        tmp_path / "knowledge" / "hypotheses.yaml",
        "hypotheses:\n  - id: H001\n    statement: Test hypo\n    status: testing\n    origin_project: alpha_proj\n",
    )
    _write(
        tmp_path / "knowledge" / "timeline.yaml",
        "events: []\n",
    )

    import scripts.query_knowledge_unified as qu

    monkeypatch.setattr(qu, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(qu, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(qu, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    monkeypatch.setattr(qu, "REGISTRY_PATH", tmp_path / "docs" / "project_registry.yaml")
    monkeypatch.setattr(qu, "FIGURE_CATALOG_PATH", tmp_path / "docs" / "figure_catalog.yaml")
    monkeypatch.setattr(qu, "FINDINGS_DIGEST_PATH", tmp_path / "docs" / "findings_digest.md")
    monkeypatch.setattr(qu, "GAPS_PATH", tmp_path / "docs" / "knowledge_gaps.md")
    monkeypatch.setattr(qu, "GRAPH_COVERAGE_PATH", tmp_path / "docs" / "knowledge_graph_coverage.md")

    return tmp_path


def test_search_falls_back_to_deterministic_on_connection_error(
    sample_repo: Path, capsys: pytest.CaptureFixture
) -> None:
    import scripts.query_knowledge_unified as qu

    def offline_service(offline=False):
        from observatory_context.service import ObservatoryContextService

        return ObservatoryContextService(repo_root=sample_repo, client=None)

    with patch.object(qu, "_try_build_service", side_effect=offline_service):
        rc = qu.main(["search", "alpha"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha_proj" in out


def test_all_subcommands_work_in_offline_mode(
    sample_repo: Path, capsys: pytest.CaptureFixture
) -> None:
    import scripts.query_knowledge_unified as qu

    def offline_service(offline=False):
        from observatory_context.service import ObservatoryContextService

        return ObservatoryContextService(repo_root=sample_repo, client=None)

    with patch.object(qu, "_try_build_service", side_effect=offline_service):
        assert qu.main(["search", "alpha"]) == 0
        assert qu.main(["figures", "alpha"]) == 0
        assert qu.main(["data", "alpha"]) == 0
        assert qu.main(["project", "alpha_proj"]) == 0
        assert qu.main(["landscape"]) == 0
        assert qu.main(["entities", "organism"]) == 0
        assert qu.main(["connections", "org_alpha"]) == 0
        assert qu.main(["hypotheses"]) == 0
        assert qu.main(["hypotheses", "testing"]) == 0
        assert qu.main(["timeline"]) == 0
        assert qu.main(["backfill"]) == 0


def test_entities_subcommand_output(
    sample_repo: Path, capsys: pytest.CaptureFixture
) -> None:
    import scripts.query_knowledge_unified as qu

    rc = qu.main(["entities", "organism"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "org_alpha" in out


def test_hypotheses_subcommand_output(
    sample_repo: Path, capsys: pytest.CaptureFixture
) -> None:
    import scripts.query_knowledge_unified as qu

    rc = qu.main(["hypotheses", "testing"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "H001" in out
