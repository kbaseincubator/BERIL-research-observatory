"""Deterministic shared-collection index (zero-LLM connector).

Maps the canonical BERDL collection IDs (``ui/config/collections.yaml``) to the projects that
cite them. The grouping is a pure function; ``load_canonical_ids`` reads the canonical id list.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class CollectionRecord:
    """One canonical collection and the projects that cite it."""

    id: str
    projects: list[str]


def build_collection_index(
    cited: dict[str, set[str]], canonical: set[str]
) -> dict[str, CollectionRecord]:
    """Group projects by the canonical collection they cite.

    For each canonical id, collect the projects whose cited set contains it (sorted). Canonical
    ids that no project cites are omitted.
    """
    index: dict[str, CollectionRecord] = {}
    for coll_id in sorted(canonical):  # sorted -> deterministic key order
        projects = sorted(pid for pid, mentions in cited.items() if coll_id in mentions)
        if projects:
            index[coll_id] = CollectionRecord(id=coll_id, projects=projects)
    return index


def load_canonical_ids(collections_yaml_path: Path) -> set[str]:
    """Read the ``collections[].id`` set from ``ui/config/collections.yaml``."""
    data = yaml.safe_load(Path(collections_yaml_path).read_text(encoding="utf-8"))
    return {c["id"] for c in data["collections"]}
