"""Materialize deterministic Phase 4 overlays from tracked knowledge resources."""

from __future__ import annotations

import argparse
from pathlib import Path

from observatory_context.overlays import build_raw_knowledge_overlays, write_overlay_documents
from observatory_context.service import ObservatoryContextService


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize Phase 4 overlay YAML outputs.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory for overlay YAML.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = ObservatoryContextService(repo_root=args.repo_root, client=None)
    overlays = build_raw_knowledge_overlays(service)
    write_overlay_documents(args.output_dir, overlays)
    print(f"Wrote overlays to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
