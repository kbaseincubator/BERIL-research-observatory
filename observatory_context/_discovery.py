"""Shared project discovery helpers."""

from __future__ import annotations

from pathlib import Path


def discover_project_ids(repo_root: Path, selected: set[str] | None = None) -> list[str]:
    """Discover project IDs from the projects/ directory layout.

    Each subdirectory containing a README.md is considered a project.
    When *selected* is non-empty, only matching IDs are returned.
    """
    projects_root = Path(repo_root) / "projects"
    return [
        path.name
        for path in sorted(projects_root.iterdir())
        if path.is_dir()
        and (path / "README.md").exists()
        and (not selected or path.name in selected)
    ]
