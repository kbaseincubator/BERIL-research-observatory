"""Phase 0 baseline capture helpers."""

from __future__ import annotations

from pathlib import Path

import yaml


def capture_baseline_snapshot(
    repo_root: Path,
    query_outputs: dict[str, str],
    validator_results: dict[str, bool],
) -> dict:
    """Capture deterministic baseline counts and query fixtures."""
    docs_dir = repo_root / "docs"
    knowledge_dir = repo_root / "knowledge"

    registry = yaml.safe_load((docs_dir / "project_registry.yaml").read_text(encoding="utf-8"))
    figure_catalog = yaml.safe_load((docs_dir / "figure_catalog.yaml").read_text(encoding="utf-8"))

    counts = {
        "projects": len(registry.get("projects", [])),
        "figures": figure_catalog.get("figure_count", len(figure_catalog.get("figures", []))),
    }
    counts.update(_knowledge_counts(knowledge_dir))

    return {
        "counts": counts,
        "queries": query_outputs,
        "validators": validator_results,
    }


def _knowledge_counts(knowledge_dir: Path) -> dict[str, int]:
    targets = {
        "organisms": knowledge_dir / "entities" / "organisms.yaml",
        "genes": knowledge_dir / "entities" / "genes.yaml",
        "pathways": knowledge_dir / "entities" / "pathways.yaml",
        "methods": knowledge_dir / "entities" / "methods.yaml",
        "concepts": knowledge_dir / "entities" / "concepts.yaml",
        "relations": knowledge_dir / "relations.yaml",
        "hypotheses": knowledge_dir / "hypotheses.yaml",
        "timeline_events": knowledge_dir / "timeline.yaml",
    }
    counts: dict[str, int] = {}
    for name, path in targets.items():
        if not path.exists():
            counts[name] = 0
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        list_value = next((value for value in data.values() if isinstance(value, list)), [])
        counts[name] = len(list_value)
    return counts

