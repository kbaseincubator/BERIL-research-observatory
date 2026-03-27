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
        "--project",
        action="append",
        default=None,
        help="Restrict ingest to one project ID. Repeat to include multiple projects.",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip resources whose target URI already exists in OpenViking.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for OpenViking to finish processing after queueing all uploads.",
    )
    parser.add_argument(
        "--wait-timeout",
        type=float,
        default=None,
        help="Optional timeout in seconds for the final processing wait.",
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=None,
        help="Optional path to write the manifest as JSON.",
    )
    parser.add_argument(
        "--max-figures",
        type=int,
        default=None,
        help="Skip projects with more than N figures (e.g. 25 to exclude large figure-heavy projects).",
    )
    parser.add_argument(
        "--max-report-kb",
        type=float,
        default=None,
        help="Skip projects whose REPORT.md exceeds N kilobytes (e.g. 50).",
    )
    return parser


def _filter_oversized_projects(
    manifest: list,
    max_figures: int | None,
    max_report_kb: float | None,
) -> list:
    if max_figures is None and max_report_kb is None:
        return manifest
    figure_counts: dict[str, int] = {}
    report_bytes: dict[str, int] = {}
    for item in manifest:
        for project_id in item.project_ids:
            if item.kind == "figure":
                figure_counts[project_id] = figure_counts.get(project_id, 0) + 1
            elif item.kind == "project_document" and item.source_path.endswith("REPORT.md"):
                report_bytes[project_id] = Path(item.source_path).stat().st_size
    skip: set[str] = set()
    for project_id in set(figure_counts) | set(report_bytes):
        figs = figure_counts.get(project_id, 0)
        kb = report_bytes.get(project_id, 0) / 1024
        if max_figures is not None and figs > max_figures:
            print(f"Skipping large project {project_id}: {figs} figures > --max-figures {max_figures}")
            skip.add(project_id)
        elif max_report_kb is not None and kb > max_report_kb:
            print(f"Skipping large project {project_id}: REPORT.md is {kb:.0f} KB > --max-report-kb {max_report_kb}")
            skip.add(project_id)
    if not skip:
        return manifest
    return [item for item in manifest if not any(pid in skip for pid in item.project_ids)]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    selected_projects = set(args.project or [])
    manifest = build_resource_manifest(
        REPO_ROOT,
        project_ids=selected_projects,
    )
    manifest = _filter_oversized_projects(manifest, args.max_figures, args.max_report_kb)
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
        if args.resume and client.resource_exists(item.uri):
            print(f"Skipping existing {item.uri}")
            continue
        client.add_manifest_resource(item, wait=False)
        print(f"Queued {item.uri}")
    if args.wait:
        print("Waiting for OpenViking processing to finish...")
        try:
            client.wait_until_processed(timeout=args.wait_timeout)
        except TimeoutError as exc:
            print(f"Warning: {exc}")
            print("Run `uv run scripts/viking_server_healthcheck.py` to check server status.")
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
