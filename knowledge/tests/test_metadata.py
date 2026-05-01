from pathlib import Path

from observatory_context.metadata import (
    ProjectMetadata,
    build_project_index,
    build_project_metadata,
)


def test_build_project_metadata_from_beril_yaml_and_readme(tmp_path: Path) -> None:
    project_dir = tmp_path / "alpha"
    project_dir.mkdir()
    (project_dir / "beril.yaml").write_text(
        """
project_id: openviking-alpha
status: active
created_at: 2026-01-02
last_session_at: 2026-02-03T04:05:06Z
branch: feature/context
engine:
  name: gpt-5
authors:
  - name: Ada Lovelace
    affiliation: Analytical Society
    orcid: 0000-0001-2345-6789
  - name: Grace Hopper
""".lstrip(),
        encoding="utf-8",
    )
    (project_dir / "README.md").write_text(
        "# OpenViking Alpha\n\n## Status\nIgnored fallback\n",
        encoding="utf-8",
    )

    metadata = build_project_metadata(project_dir)

    assert metadata == ProjectMetadata(
        project_id="openviking-alpha",
        title="OpenViking Alpha",
        status="active",
        author_names=["Ada Lovelace", "Grace Hopper"],
        markdown=metadata.markdown,
    )
    assert "| Project ID | openviking-alpha |" in metadata.markdown
    assert "| Engine | gpt-5 |" in metadata.markdown
    assert "| Ada Lovelace | Analytical Society | 0000-0001-2345-6789 |" in metadata.markdown
    assert "| Grace Hopper |  |  |" in metadata.markdown


def test_readme_fallback_metadata_and_sorted_index(tmp_path: Path) -> None:
    zeta_dir = tmp_path / "zeta"
    alpha_dir = tmp_path / "alpha"
    zeta_dir.mkdir()
    alpha_dir.mkdir()
    (zeta_dir / "README.md").write_text(
        "# Zeta Project\n\n## Status\n\nReady for review\n",
        encoding="utf-8",
    )
    (alpha_dir / "beril.yaml").write_text(
        "project_id: alpha\nstatus: active\nauthors:\n  - name: Lin Chen\n",
        encoding="utf-8",
    )

    metadata = build_project_metadata(zeta_dir)
    index = build_project_index([zeta_dir, alpha_dir])

    assert metadata.project_id == "zeta"
    assert metadata.title == "Zeta Project"
    assert metadata.status == "Ready for review"
    assert metadata.author_names == []
    assert index == (
        "# BERIL Project Index\n"
        "\n"
        "| Project | Title | Authors | Status |\n"
        "|---|---|---|---|\n"
        "| alpha | alpha | Lin Chen | active |\n"
        "| zeta | Zeta Project |  | Ready for review |"
    )
