"""Materialize deterministic Phase 3 exports from OpenViking-backed resources."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from observatory_context.materialize import (
    build_figure_catalog_export,
    build_project_registry_export,
    collect_project_ids,
    write_yaml_export,
)
from observatory_context import runtime


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize Phase 3 Git review exports.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory for YAML exports.")
    parser.add_argument("--offline", action="store_true", help="Materialize from repository files without a live server.")
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Override generated_at timestamp for deterministic test materialization.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    service = runtime.build_service(args.repo_root, offline=args.offline, require_live=not args.offline)
    project_ids = collect_project_ids(args.repo_root)
    registry = build_project_registry_export(service, project_ids=project_ids, generated_at=generated_at)
    figure_catalog = build_figure_catalog_export(service, project_ids=project_ids, generated_at=generated_at)
    write_yaml_export(args.output_dir / "project_registry.yaml", registry)
    write_yaml_export(args.output_dir / "figure_catalog.yaml", figure_catalog)
    print(f"Wrote exports to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
