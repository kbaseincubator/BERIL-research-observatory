from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from observatory_context import staging
from observatory_context.manifest import build_manifest, changed_targets


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_manifest_detects_changed_and_unchanged_targets(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    write(source, "same")

    old = build_manifest({"target-b": [source], "target-a": [source]}, tmp_path)
    unchanged = build_manifest({"target-b": [source], "target-a": [source]}, tmp_path)

    assert changed_targets(old, unchanged) == []

    write(source, "changed")
    changed = build_manifest({"target-b": [source], "target-a": [source]}, tmp_path)

    assert changed_targets(old, changed) == ["target-a", "target-b"]


def test_stage_project_excludes_data_and_removes_stale_file(
    tmp_path: Path, monkeypatch
) -> None:
    project = tmp_path / "projects" / "demo"
    staging_dir = tmp_path / "knowledge" / "staging"
    write(project / "README.md", "# Demo\n")
    write(project / "REPORT.md", "# Report\n")
    write(project / "data" / "README.md", "# Data\n")
    write(staging_dir / "projects" / "demo" / "OLD.md", "old")

    monkeypatch.setattr(
        staging,
        "select_project_files",
        lambda project_dir: [project_dir / "README.md", project_dir / "REPORT.md"],
    )
    monkeypatch.setattr(
        staging,
        "build_project_metadata",
        lambda project_dir: SimpleNamespace(markdown="# Metadata\n"),
    )

    staged = staging.stage_project(project, staging_dir)

    assert staged == staging_dir / "projects" / "demo"
    assert (staged / "README.md").read_text(encoding="utf-8") == "# Demo\n"
    assert (staged / "REPORT.md").is_file()
    assert (staged / "PROJECT_METADATA.md").read_text(encoding="utf-8") == "# Metadata\n"
    assert not (staged / "data" / "README.md").exists()
    assert not (staged / "OLD.md").exists()


