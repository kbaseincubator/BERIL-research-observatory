from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .selection import project_target_uri


def read_related_projects(project_dir: Path) -> list[str]:
    """Read beril.yaml's optional `related_projects:` list of project IDs."""
    beril_path = project_dir / "beril.yaml"
    if not beril_path.is_file():
        return []
    data = yaml.safe_load(beril_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return []
    raw = data.get("related_projects")
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def apply_project_relations(
    client: Any,
    project_dir: Path,
    projects_dir: Path,
) -> list[str]:
    """Create links to existing related projects declared in beril.yaml.

    Skips related IDs whose directories are missing on disk so a stale
    reference can't break ingest. Returns the URIs that were linked.
    """
    related_ids = read_related_projects(project_dir)
    if not related_ids:
        return []
    from_uri = project_target_uri(project_dir.name)
    valid_targets = [
        project_target_uri(rid)
        for rid in related_ids
        if (projects_dir / rid).is_dir() and rid != project_dir.name
    ]
    if not valid_targets:
        return []
    client.link(from_uri, valid_targets, reason="beril.yaml related_projects")
    return valid_targets
