"""Validate generated Phase 4 overlays against tracked knowledge outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from observatory_context.overlays import build_raw_knowledge_overlays
from observatory_context.service import ObservatoryContextService


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Phase 4 overlays against tracked knowledge outputs.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument(
        "--generated-dir",
        type=Path,
        required=True,
        help="Directory containing generated overlay YAML files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = ObservatoryContextService(repo_root=args.repo_root, client=None)
    issues = collect_overlay_parity_issues(service, args.generated_dir)

    if issues:
        print("FAIL: generated overlays do not match tracked knowledge outputs.")
        for issue in issues:
            print(issue)
        return 1

    print("PASS: generated overlays match tracked knowledge outputs.")
    return 0


def collect_overlay_parity_issues(
    service: ObservatoryContextService,
    generated_dir: Path,
) -> list[str]:
    issues: list[str] = []
    generated_root = Path(generated_dir)
    for overlay in build_raw_knowledge_overlays(service):
        generated_path = generated_root / overlay.relative_path
        tracked_path = service.repo_root / "knowledge" / overlay.relative_path
        if not generated_path.exists():
            issues.append(f"{overlay.relative_path} is missing from generated output")
            continue
        if _load_yaml(generated_path) != _load_yaml(tracked_path):
            issues.append(f"{overlay.relative_path} does not match tracked output")
    return issues


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


if __name__ == "__main__":
    raise SystemExit(main())
