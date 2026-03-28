"""Tests for manifest and parity helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from observatory_context.baseline import capture_baseline_snapshot
from observatory_context.ingest.manifest import build_resource_manifest
from observatory_context.parity import collect_parity_issues
from observatory_context.render import RenderLevel, render_resource
from observatory_context.uris import (
    build_figure_resource_uri,
    build_project_resource_uri,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "docs" / "project_registry.yaml",
        """
projects:
  - id: alpha_proj
    title: Alpha Project
    status: complete
    tags: [metal-stress, fitness]
    research_question: How does alpha respond?
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "docs" / "figure_catalog.yaml",
        """
figure_count: 1
figures:
  - id: alpha_proj__main
    project_id: alpha_proj
    figure_file: figures/main.png
    caption: Main alpha figure
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "README.md",
        "# Alpha Project\n\nQuestion: How does alpha respond?\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "REPORT.md",
        "# Report\n\nAlpha report body.\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "provenance.yaml",
        """
project_id: alpha_proj
created_at: 2026-03-18
""".strip()
        + "\n",
    )
    return tmp_path


def test_resource_uris_are_deterministic() -> None:
    assert (
        build_project_resource_uri("alpha_proj", "authored", "README.md")
        == "viking://resources/observatory/projects/alpha_proj/authored/README.md"
    )
    assert (
        build_figure_resource_uri("alpha_proj", "main")
        == "viking://resources/observatory/projects/alpha_proj/authored/figures/main"
    )
def test_manifest_deduplicates_duplicate_figure_uris(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "project_registry.yaml",
        """
projects:
  - id: alpha_proj
    title: Alpha Project
    status: complete
    tags: []
    research_question: How does alpha respond?
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "docs" / "figure_catalog.yaml",
        """
figure_count: 1
figures:
  - id: alpha_proj__main
    project_id: alpha_proj
    figure_file: figures/main.png
    caption: Main alpha figure
""".strip()
        + "\n",
    )
    _write(tmp_path / "projects" / "alpha_proj" / "README.md", "# Alpha Project\n")
    _write(
        tmp_path / "projects" / "alpha_proj" / "REPORT.md",
        """
# Alpha Report

![Main alpha figure](figures/main.png)
![Main alpha figure again](figures/main.png)
""".strip()
        + "\n",
    )
    _write(tmp_path / "projects" / "alpha_proj" / "provenance.yaml", "project_id: alpha_proj\n")
    _write(tmp_path / "projects" / "alpha_proj" / "figures" / "main.png", "not-a-real-png\n")

    manifest = build_resource_manifest(tmp_path)
    figure_uris = [item.uri for item in manifest if item.kind == "figure"]

    assert figure_uris == ["viking://resources/observatory/projects/alpha_proj/authored/figures/alpha_proj__main"]


def test_render_resource_returns_deterministic_project_views() -> None:
    resource = {
        "id": "alpha_proj",
        "kind": "project",
        "title": "Alpha Project",
        "project_ids": ["alpha_proj"],
        "tags": ["metal-stress", "fitness"],
        "research_question": "How does alpha respond?",
        "summary": "Alpha project summary.",
    }

    l0 = render_resource(resource, RenderLevel.L0)
    l1 = render_resource(resource, RenderLevel.L1)

    assert "Alpha Project" in l0
    assert "metal-stress" in l0
    assert "Alpha project summary." in l1
    assert "How does alpha respond?" in l1


def test_capture_baseline_snapshot_collects_counts(sample_repo: Path) -> None:
    snapshot = capture_baseline_snapshot(
        sample_repo,
        query_outputs={
            "metal stress": "alpha hit",
            "essential genes": "beta hit",
            "org_adp1": "no direct hit",
            "landscape": "landscape output",
            "gaps": "gaps output",
        },
        validator_results={
            "validate_provenance": True,
        },
    )

    assert snapshot["counts"]["projects"] == 1
    assert snapshot["queries"]["org_adp1"] == "no direct hit"


def test_collect_parity_issues_reports_count_mismatches() -> None:
    issues = collect_parity_issues(
        expected_counts={"projects": 46, "figures": 383},
        actual_counts={"projects": 45, "figures": 383},
        duplicate_uris=["viking://resources/observatory/projects/alpha_proj"],
        missing_project_ids=["alpha_proj"],
    )

    assert "project count mismatch: expected 46, got 45" in issues
    assert "duplicate logical resources detected: 1" in issues
    assert "missing project workspaces: alpha_proj" in issues
