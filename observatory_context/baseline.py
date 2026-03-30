"""Phase 0 baseline capture helpers."""

from __future__ import annotations

from pathlib import Path

from observatory_context._discovery import discover_project_ids


def capture_baseline_snapshot(
    repo_root: Path,
    query_outputs: dict[str, str],
    validator_results: dict[str, bool],
) -> dict:
    """Capture deterministic baseline counts and query fixtures."""
    project_ids = discover_project_ids(repo_root)

    counts = {
        "projects": len(project_ids),
    }

    return {
        "counts": counts,
        "queries": query_outputs,
        "validators": validator_results,
    }
