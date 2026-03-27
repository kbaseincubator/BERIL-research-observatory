"""Generate deterministic L0/L1/L2 render files for manifest resources."""

from __future__ import annotations

import argparse
from pathlib import Path

from observatory_context.ingest import build_resource_manifest
from observatory_context.render import RenderLevel, render_resource


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".cache" / "openviking" / "renders"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize deterministic L0/L1/L2 render files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where render files will be written.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_resource_manifest(REPO_ROOT)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for item in manifest:
        safe_name = item.uri.replace("viking://", "").replace("/", "__")
        for level in RenderLevel:
            out_path = args.output_dir / f"{safe_name}.{level.value}.md"
            out_path.write_text(render_resource(item.metadata, level), encoding="utf-8")
    print(f"Wrote renders to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

