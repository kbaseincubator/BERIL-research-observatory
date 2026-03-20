"""Build and optionally ingest the Phase 1 OpenViking manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from observatory_context.client import OpenVikingObservatoryClient
from observatory_context.config import ObservatoryContextSettings
from observatory_context.ingest import build_resource_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and ingest observatory resources into OpenViking.")
    parser.add_argument("--dry-run", action="store_true", help="Print the manifest without uploading resources.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N manifest items.")
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=None,
        help="Optional path to write the manifest as JSON.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_resource_manifest(REPO_ROOT)
    if args.limit is not None:
        manifest = manifest[: args.limit]

    if args.manifest_json:
        args.manifest_json.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_json.write_text(
            json.dumps([item.to_dict() for item in manifest], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    if args.dry_run:
        print(json.dumps([item.to_dict() for item in manifest], indent=2, sort_keys=True))
        return 0

    client = OpenVikingObservatoryClient(ObservatoryContextSettings())
    for item in manifest:
        client.add_manifest_resource(item)
        print(f"Ingested {item.uri}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
