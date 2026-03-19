"""Validate generated Phase 3 exports against tracked repository outputs."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Phase 3 generated exports against tracked docs outputs.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument(
        "--generated-dir",
        type=Path,
        required=True,
        help="Directory containing generated project_registry.yaml and figure_catalog.yaml.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tracked_dir = args.repo_root / "docs"

    issues: list[str] = []
    if _normalize(_load_yaml(args.generated_dir / "project_registry.yaml")) != _normalize(
        _load_yaml(tracked_dir / "project_registry.yaml")
    ):
        issues.append("project_registry.yaml does not match tracked output")
    if _normalize(_load_yaml(args.generated_dir / "figure_catalog.yaml")) != _normalize(
        _load_yaml(tracked_dir / "figure_catalog.yaml")
    ):
        issues.append("figure_catalog.yaml does not match tracked output")

    if issues:
        print("FAIL: generated exports do not match tracked outputs.")
        for issue in issues:
            print(issue)
        return 1

    print("PASS: generated exports match tracked outputs.")
    return 0


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _normalize(payload: dict) -> dict:
    normalized = copy.deepcopy(payload)
    normalized.pop("generated_at", None)
    return normalized


if __name__ == "__main__":
    raise SystemExit(main())
