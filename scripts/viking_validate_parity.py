"""Validate local parity expectations for the Phase 1 migration slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from observatory_context.baseline import capture_baseline_snapshot
from observatory_context.ingest import build_resource_manifest
from observatory_context.parity import collect_parity_issues


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = REPO_ROOT / "docs" / "migration_baseline" / "2026-03-19" / "baseline_snapshot.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate parity against the captured migration baseline.")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help="Baseline snapshot produced by scripts/viking_capture_baseline.py.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.snapshot.exists():
        print(f"FAIL: baseline snapshot not found at {args.snapshot}")
        return 1

    baseline = json.loads(args.snapshot.read_text(encoding="utf-8"))
    current = capture_baseline_snapshot(
        REPO_ROOT,
        query_outputs={key: value for key, value in baseline.get("queries", {}).items()},
        validator_results={key: bool(value) for key, value in baseline.get("validators", {}).items()},
    )

    manifest = build_resource_manifest(REPO_ROOT)
    project_ids = sorted(current["counts"].get("projects", 0) and {
        item.metadata["id"]
        for item in manifest
        if item.kind == "project"
    })
    duplicate_uris = _duplicate_uris([item.uri for item in manifest])
    missing_project_ids = sorted(
        set(project["id"] for project in _load_registry_projects(REPO_ROOT))
        - set(project_ids)
    )

    issues = collect_parity_issues(
        expected_counts=baseline["counts"],
        actual_counts=current["counts"],
        duplicate_uris=duplicate_uris,
        missing_project_ids=missing_project_ids,
    )

    if issues:
        print("FAIL: parity issues detected.\n")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("PASS: local parity checks match the captured baseline.")
    return 0


def _duplicate_uris(uris: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for uri in uris:
        if uri in seen:
            duplicates.append(uri)
        seen.add(uri)
    return duplicates


def _load_registry_projects(repo_root: Path) -> list[dict]:
    import yaml

    path = repo_root / "docs" / "project_registry.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload.get("projects", [])


if __name__ == "__main__":
    raise SystemExit(main())
