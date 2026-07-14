from __future__ import annotations

from pathlib import Path

from .selection import iter_project_dirs


def latest_project_dirs(projects_dir: Path, count: int) -> list[Path]:
    return sorted(
        iter_project_dirs(projects_dir),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )[:count]
