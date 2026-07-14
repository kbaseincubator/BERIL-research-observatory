from __future__ import annotations

import shutil
from pathlib import Path

from .metadata import build_project_metadata
from .selection import MEMORY_DIR_NAME, select_project_files, select_project_memories


def stage_project(project_dir: Path, staging_dir: Path) -> Path:
    target = staging_dir / "projects" / project_dir.name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for source in select_project_files(project_dir):
        shutil.copy2(source, target / source.name)

    memories = select_project_memories(project_dir)
    if memories:
        memories_target = target / MEMORY_DIR_NAME
        memories_target.mkdir(parents=True, exist_ok=True)
        for source in memories:
            shutil.copy2(source, memories_target / source.name)

    metadata = build_project_metadata(project_dir)
    (target / "PROJECT_METADATA.md").write_text(metadata.markdown, encoding="utf-8")
    return target


def stage_doc(doc_path: Path, staging_dir: Path) -> Path:
    target = staging_dir / "docs" / doc_path.stem
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(doc_path, target / doc_path.name)
    return target
