"""Materialize deterministic Phase 4 overlays from tracked knowledge resources."""

from __future__ import annotations

import argparse
from pathlib import Path

from observatory_context.overlays import build_raw_knowledge_overlays, write_overlay_documents
from observatory_context import runtime


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".cache" / "openviking" / "overlays"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize Phase 4 overlay YAML outputs.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory for overlay YAML.")
    parser.add_argument("--offline", action="store_true", help="Materialize from repository files without a live server.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = runtime.build_service(args.repo_root, offline=args.offline, require_live=not args.offline)
    overlays = build_raw_knowledge_overlays(service)
    write_overlay_documents(args.output_dir, overlays)
    print(f"Wrote overlays to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
