"""Tests for the Phase 3 OpenViking export materialization slice."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from observatory_context.service import ObservatoryContextService


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "projects" / "beta_proj" / "README.md",
        """
# Beta Project

## Status
In Progress - Beta status

## Research Question
How does beta respond?
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "projects" / "beta_proj" / "REPORT.md",
        """
# Beta Report

## Key Findings
### Beta finding
*(Notebook: 02_beta.ipynb)*
![Beta overview](figures/beta_overview.png)
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "projects" / "beta_proj" / "provenance.yaml",
        """
project_id: beta_proj
findings:
  - title: Beta finding
    notebook: 02_beta.ipynb
    figures:
      - beta_overview.png
data_sources:
  - collection: kbase_ke_pangenome
references:
  - id: beta_ref
    title: Beta reference
cross_project_deps: []
""".strip()
        + "\n",
    )
    _write(tmp_path / "projects" / "beta_proj" / "figures" / "beta_overview.png", "beta\n")

    _write(
        tmp_path / "projects" / "alpha_proj" / "README.md",
        """
# Alpha Project

## Status
Proposed - Alpha status

## Research Question
How does alpha respond?
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "REPORT.md",
        """
# Alpha Report

## Key Findings
### Alpha finding
*(Notebook: 01_alpha.ipynb)*
![Alpha overview](figures/alpha_overview.png)
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "projects" / "alpha_proj" / "provenance.yaml",
        """
project_id: alpha_proj
findings:
  - title: Alpha finding
    notebook: 01_alpha.ipynb
    figures:
      - alpha_overview.png
data_sources:
  - collection: kescience_fitnessbrowser
references:
  - id: alpha_ref
    title: Alpha reference
cross_project_deps:
  - project: beta_proj
""".strip()
        + "\n",
    )
    _write(tmp_path / "projects" / "alpha_proj" / "figures" / "alpha_overview.png", "alpha\n")

    _write(
        tmp_path / "docs" / "project_registry.yaml",
        """
version: 1
generated_at: '2026-03-19T16:43:57'
project_count: 2
projects:
  - id: alpha_proj
    title: Alpha Project
    status: proposed
    research_question: How does alpha respond?
    key_findings: [Alpha finding]
    tags: []
    organisms: []
    databases_used: [kescience_fitnessbrowser]
    notebook_count: 0
    figure_count: 1
    key_data_artifacts: []
    references:
      - id: alpha_ref
        title: Alpha reference
        doi: null
        pmid: null
        type: supporting
    depends_on: [beta_proj]
    enables: []
    has_provenance: true
    date_completed: null
  - id: beta_proj
    title: Beta Project
    status: in-progress
    research_question: How does beta respond?
    key_findings: [Beta finding]
    tags: []
    organisms: []
    databases_used: [kbase_ke_pangenome]
    notebook_count: 0
    figure_count: 1
    key_data_artifacts: []
    references:
      - id: beta_ref
        title: Beta reference
        doi: null
        pmid: null
        type: supporting
    depends_on: []
    enables: [alpha_proj]
    has_provenance: true
    date_completed: null
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "docs" / "figure_catalog.yaml",
        """
version: 1
generated_at: '2026-03-19T16:43:57'
figure_count: 2
figures:
  - project: alpha_proj
    file: alpha_overview.png
    path: projects/alpha_proj/figures/alpha_overview.png
    caption: Alpha overview
    notebook: 01_alpha.ipynb
    tags: []
  - project: beta_proj
    file: beta_overview.png
    path: projects/beta_proj/figures/beta_overview.png
    caption: Beta overview
    notebook: 02_beta.ipynb
    tags: []
""".strip()
        + "\n",
    )
    return tmp_path


@pytest.fixture
def service(sample_repo: Path) -> ObservatoryContextService:
    return ObservatoryContextService(repo_root=sample_repo, client=None)


def test_build_project_registry_export_from_resources(service: ObservatoryContextService) -> None:
    from observatory_context.materialize.exports import build_project_registry_export

    export = build_project_registry_export(
        service,
        project_ids=["beta_proj", "alpha_proj"],
        generated_at="2026-03-19T16:43:57",
    )

    assert export["project_count"] == 2
    assert [project["id"] for project in export["projects"]] == ["alpha_proj", "beta_proj"]
    assert export["projects"][0]["depends_on"] == ["beta_proj"]
    assert export["projects"][1]["enables"] == ["alpha_proj"]


def test_build_figure_catalog_export_from_resources(service: ObservatoryContextService) -> None:
    from observatory_context.materialize.exports import build_figure_catalog_export

    export = build_figure_catalog_export(
        service,
        project_ids=["beta_proj", "alpha_proj"],
        generated_at="2026-03-19T16:43:57",
    )

    assert export["figure_count"] == 2
    assert export["figures"] == [
        {
            "project": "alpha_proj",
            "file": "alpha_overview.png",
            "path": "projects/alpha_proj/figures/alpha_overview.png",
            "caption": "Alpha overview",
            "notebook": "01_alpha.ipynb",
            "tags": [],
        },
        {
            "project": "beta_proj",
            "file": "beta_overview.png",
            "path": "projects/beta_proj/figures/beta_overview.png",
            "caption": "Beta overview",
            "notebook": "02_beta.ipynb",
            "tags": [],
        },
    ]


def test_materialized_exports_use_deterministic_ordering(
    service: ObservatoryContextService,
) -> None:
    from observatory_context.materialize.exports import (
        build_figure_catalog_export,
        build_project_registry_export,
    )

    registry = build_project_registry_export(
        service,
        project_ids=["beta_proj", "alpha_proj"],
        generated_at="2026-03-19T16:43:57",
    )
    figure_catalog = build_figure_catalog_export(
        service,
        project_ids=["beta_proj", "alpha_proj"],
        generated_at="2026-03-19T16:43:57",
    )

    assert [project["id"] for project in registry["projects"]] == ["alpha_proj", "beta_proj"]
    assert [(figure["project"], figure["file"]) for figure in figure_catalog["figures"]] == [
        ("alpha_proj", "alpha_overview.png"),
        ("beta_proj", "beta_overview.png"),
    ]


def test_missing_required_export_metadata_fails(service: ObservatoryContextService) -> None:
    from observatory_context.materialize.exports import (
        ExportMaterializationError,
        build_project_registry_export,
    )

    project_resource = service.get_resource("alpha_proj").resource
    project_resource.metadata.pop("export_project", None)

    with pytest.raises(ExportMaterializationError, match="export_project"):
        build_project_registry_export(
            service,
            project_ids=["alpha_proj"],
            generated_at="2026-03-19T16:43:57",
        )


def test_materialize_and_validate_exports_against_tracked_outputs(
    sample_repo: Path,
) -> None:
    from scripts import viking_materialize_exports, viking_validate_exports

    output_dir = sample_repo / "out"
    materialize_exit = viking_materialize_exports.main(
        [
            "--repo-root",
            str(sample_repo),
            "--output-dir",
            str(output_dir),
            "--generated-at",
            "2026-03-19T16:43:57",
        ]
    )
    assert materialize_exit == 0

    registry = yaml.safe_load((output_dir / "project_registry.yaml").read_text(encoding="utf-8"))
    figures = yaml.safe_load((output_dir / "figure_catalog.yaml").read_text(encoding="utf-8"))
    tracked_registry = yaml.safe_load((sample_repo / "docs" / "project_registry.yaml").read_text(encoding="utf-8"))
    tracked_figures = yaml.safe_load((sample_repo / "docs" / "figure_catalog.yaml").read_text(encoding="utf-8"))

    assert registry == tracked_registry
    assert figures == tracked_figures

    validate_exit = viking_validate_exports.main(
        [
            "--repo-root",
            str(sample_repo),
            "--generated-dir",
            str(output_dir),
        ]
    )
    assert validate_exit == 0

    mutated = dict(figures)
    mutated["figure_count"] = 999
    (output_dir / "figure_catalog.yaml").write_text(
        yaml.safe_dump(mutated, sort_keys=False),
        encoding="utf-8",
    )

    mismatch_exit = viking_validate_exports.main(
        [
            "--repo-root",
            str(sample_repo),
            "--generated-dir",
            str(output_dir),
        ]
    )
    assert mismatch_exit == 1
