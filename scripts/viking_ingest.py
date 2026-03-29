"""Build, ingest, check, and fix the OpenViking resource manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from observatory_context.client import OpenVikingObservatoryClient
from observatory_context.config import ObservatoryContextSettings
from observatory_context.delivery import ContextDelivery
from observatory_context.ingest import build_resource_manifest

if TYPE_CHECKING:
    from observatory_context.extraction import CBORGExtractor

console = Console()
REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_progress(**kwargs) -> Progress:
    """Create a Rich progress bar with consistent styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        **kwargs,
    )


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
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify all manifest resources exist in OpenViking without uploading.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Re-ingest any missing resources found by --check.",
    )
    parser.add_argument(
        "--rebuild-graph",
        action="store_true",
        help="Run Phase 2+3: extract knowledge graph from projects via CBORG after resource upload.",
    )
    parser.add_argument(
        "--graph-only",
        action="store_true",
        help="Skip Phase 1 resource upload, only rebuild knowledge graph.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="CBORG model override (e.g. 'claude-haiku', 'gpt-5.4-mini'). Uses config default if unset.",
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
            console.print(f"  [yellow]Skipping {project_id}: {figs} figures > --max-figures {max_figures}[/]")
            skip.add(project_id)
        elif max_report_kb is not None and kb > max_report_kb:
            console.print(f"  [yellow]Skipping {project_id}: REPORT.md {kb:.0f} KB > --max-report-kb {max_report_kb}[/]")
            skip.add(project_id)
    if not skip:
        return manifest
    return [item for item in manifest if not any(pid in skip for pid in item.project_ids)]


def _check_manifest(client: OpenVikingObservatoryClient, manifest: list) -> list:
    """Check which manifest items exist in OpenViking. Returns list of missing items."""
    missing: list = []
    with _make_progress() as progress:
        task = progress.add_task("Checking resources", total=len(manifest))
        for item in manifest:
            if client.resource_exists(item.uri):
                progress.advance(task)
            else:
                missing.append(item)
                progress.advance(task)

    if missing:
        table = Table(title=f"[red]{len(missing)} Missing Resources[/]")
        table.add_column("URI", style="red")
        table.add_column("Kind")
        for item in missing:
            table.add_row(item.uri, item.kind)
        console.print(table)
    else:
        console.print(f"[green]All {len(manifest)} resources present.[/]")

    return missing


def _generate_rollup_tiers(
    delivery: ContextDelivery,
    extractor: CBORGExtractor,
    all_entities: list,
    progress: Progress,
    task_id: int,
) -> None:
    """Generate L0/L1 tier summaries for knowledge graph directories."""
    from observatory_context.uris import (
        _ENTITY_TYPE_PLURALS,
        _ROOT,
        build_knowledge_graph_uri,
    )

    # Collect summaries per entity type
    type_summaries: dict[str, list[str]] = {}
    for entity in all_entities:
        plural = _ENTITY_TYPE_PLURALS.get(entity.type, f"{entity.type}s")
        type_summaries.setdefault(plural, []).append(f"- {entity.name} ({entity.type}/{entity.id})")

    # Total tier generation steps: per-type (2 each) + entities root (2) + kg root (2) + hypotheses (2)
    total_steps = len(type_summaries) * 2 + 6
    progress.update(task_id, total=total_steps, completed=0)

    all_lines = []
    for plural, lines in sorted(type_summaries.items()):
        type_dir_uri = f"{_ROOT}/knowledge-graph/entities/{plural}"
        content = f"# Entities: {plural}\n\n" + "\n".join(lines)
        all_lines.extend(lines)

        progress.update(task_id, description=f"Tiers: entities/{plural}")
        abstract = extractor.generate_abstract(content)
        overview = extractor.generate_overview(content)

        delivery.ingest_resource(
            f"{type_dir_uri}/.abstract.md", abstract,
            metadata={"title": f"{plural} abstract", "kind": "tier_summary"},
            generate_tiers=False,
        )
        progress.advance(task_id)
        delivery.ingest_resource(
            f"{type_dir_uri}/.overview.md", overview,
            metadata={"title": f"{plural} overview", "kind": "tier_summary"},
            generate_tiers=False,
        )
        progress.advance(task_id)

    # Entities root
    progress.update(task_id, description="Tiers: entities/")
    entities_uri = f"{_ROOT}/knowledge-graph/entities"
    entities_content = f"# All entities\n\n{len(all_entities)} entities across {len(type_summaries)} types.\n\n" + "\n".join(all_lines)
    delivery.ingest_resource(
        f"{entities_uri}/.abstract.md",
        extractor.generate_abstract(entities_content),
        metadata={"title": "entities abstract", "kind": "tier_summary"},
        generate_tiers=False,
    )
    progress.advance(task_id)
    delivery.ingest_resource(
        f"{entities_uri}/.overview.md",
        extractor.generate_overview(entities_content),
        metadata={"title": "entities overview", "kind": "tier_summary"},
        generate_tiers=False,
    )
    progress.advance(task_id)

    # Knowledge graph root
    progress.update(task_id, description="Tiers: knowledge-graph/")
    kg_uri = build_knowledge_graph_uri()
    kg_content = (
        f"# Knowledge Graph\n\n"
        f"{len(all_entities)} entities, {len(type_summaries)} entity types.\n\n"
        f"Entity types: {', '.join(sorted(type_summaries.keys()))}"
    )
    delivery.ingest_resource(
        f"{kg_uri}/.abstract.md",
        extractor.generate_abstract(kg_content),
        metadata={"title": "knowledge-graph abstract", "kind": "tier_summary"},
        generate_tiers=False,
    )
    progress.advance(task_id)
    delivery.ingest_resource(
        f"{kg_uri}/.overview.md",
        extractor.generate_overview(kg_content),
        metadata={"title": "knowledge-graph overview", "kind": "tier_summary"},
        generate_tiers=False,
    )
    progress.advance(task_id)

    # Hypotheses directory
    progress.update(task_id, description="Tiers: hypotheses/")
    hyp_uri = f"{_ROOT}/knowledge-graph/hypotheses"
    delivery.ingest_resource(
        f"{hyp_uri}/.abstract.md",
        extractor.generate_abstract("Hypotheses extracted from observatory project reports."),
        metadata={"title": "hypotheses abstract", "kind": "tier_summary"},
        generate_tiers=False,
    )
    progress.advance(task_id)
    delivery.ingest_resource(
        f"{hyp_uri}/.overview.md",
        extractor.generate_overview("Hypotheses extracted from observatory project reports."),
        metadata={"title": "hypotheses overview", "kind": "tier_summary"},
        generate_tiers=False,
    )
    progress.advance(task_id)


def _fetch_model_limits(api_key: str, model: str) -> dict:
    """Fetch max_input_tokens and max_output_tokens from the CBORG model info endpoint."""
    import httpx

    try:
        resp = httpx.get(
            "https://api.cborg.lbl.gov/model/info",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        for entry in resp.json().get("data", []):
            if entry["model_name"] == model:
                info = entry.get("model_info", {})
                return {
                    "max_input_tokens": info.get("max_input_tokens"),
                    "max_output_tokens": info.get("max_output_tokens"),
                }
    except Exception as exc:
        console.print(f"[yellow]Warning: could not fetch model limits: {exc}[/]")
    return {}


def _rebuild_knowledge_graph(
    delivery: ContextDelivery,
    manifest: list,
    args: argparse.Namespace,
) -> None:
    """Phase 2+3: Extract knowledge graph from projects via CBORG."""
    from observatory_context.extraction import CBORGExtractor
    from observatory_context.uris import build_hypothesis_uri, build_timeline_uri

    settings = ObservatoryContextSettings()
    model = args.model or settings.cborg_model
    api_key = settings.cborg_api_key
    if not api_key:
        console.print("[red]Error: CBORG_API_KEY not set. Required for --rebuild-graph.[/]")
        return

    with console.status(f"[bold]Fetching model limits for {model}..."):
        model_limits = _fetch_model_limits(api_key, model)

    extractor = CBORGExtractor(
        api_url=settings.cborg_api_url,
        model=model,
        api_key=api_key,
        max_input_tokens=model_limits.get("max_input_tokens"),
        max_output_tokens=model_limits.get("max_output_tokens"),
    )

    console.print(f"[bold]Model:[/] {model}", highlight=False)
    if model_limits:
        console.print(
            f"[dim]  input: {model_limits.get('max_input_tokens', '?'):,} tokens, "
            f"output: {model_limits.get('max_output_tokens', '?'):,} tokens[/]"
        )

    # Get unique project IDs from manifest
    project_ids = sorted({pid for item in manifest for pid in item.project_ids})

    all_entities = []
    skipped = 0
    totals = {"entities": 0, "relations": 0, "hypotheses": 0, "events": 0}

    with _make_progress() as progress:
        extract_task = progress.add_task(
            "Phase 2: Extracting",
            total=len(project_ids),
        )

        for pid in project_ids:
            progress.update(extract_task, description=f"Extracting: {pid}")
            report_path = REPO_ROOT / "projects" / pid / "REPORT.md"
            prov_path = REPO_ROOT / "projects" / pid / "provenance.yaml"

            if not report_path.exists():
                skipped += 1
                progress.advance(extract_task)
                continue

            report = report_path.read_text(encoding="utf-8")
            provenance: dict = {}
            if prov_path.exists():
                import yaml

                provenance = yaml.safe_load(prov_path.read_text(encoding="utf-8")) or {}

            if args.dry_run:
                progress.advance(extract_task)
                continue

            try:
                extraction = extractor.extract_knowledge(report, provenance)
            except ValueError:
                skipped += 1
                progress.advance(extract_task)
                continue

            totals["entities"] += len(extraction.entities)
            totals["relations"] += len(extraction.relations)
            totals["hypotheses"] += len(extraction.hypotheses)
            totals["events"] += len(extraction.timeline_events)

            for entity in extraction.entities:
                profile = {"name": entity.name, "type": entity.type, "projects": [pid], **entity.metadata}
                entity_relations = [
                    r.model_dump() for r in extraction.relations if r.subject == entity.id
                ]
                delivery.ingest_entity(entity.type, entity.id, profile, relations=entity_relations)
                all_entities.append(entity)

            for hyp in extraction.hypotheses:
                uri = build_hypothesis_uri(hyp.id)
                content = (
                    f"claim: {hyp.claim}\n"
                    f"status: {hyp.status}\n"
                    f"evidence_delta: {hyp.evidence_delta}\n"
                )
                delivery.ingest_resource(
                    f"{uri}/hypothesis.yaml",
                    content,
                    metadata={
                        "title": hyp.claim[:80],
                        "kind": "hypothesis",
                        "status": hyp.status,
                        "project_ids": [pid],
                    },
                )

            for evt in extraction.timeline_events:
                uri = build_timeline_uri()
                content = (
                    f"date: {evt.date}\n"
                    f"event: {evt.event}\n"
                    f"type: {evt.type}\n"
                    f"project: {evt.project or pid}\n"
                )
                delivery.ingest_resource(
                    f"{uri}/{evt.date}_{pid}.yaml",
                    content,
                    metadata={
                        "title": evt.event[:80],
                        "kind": "timeline_event",
                        "date": evt.date,
                        "project_ids": [pid],
                    },
                )

            progress.advance(extract_task)

    # Summary table
    table = Table(title="Phase 2 Summary", show_header=False, box=None, pad_edge=False)
    table.add_column(style="bold")
    table.add_column(justify="right")
    table.add_row("Projects processed", str(len(project_ids) - skipped))
    table.add_row("Projects skipped", str(skipped))
    table.add_row("Entities", str(totals["entities"]))
    table.add_row("Relations", str(totals["relations"]))
    table.add_row("Hypotheses", str(totals["hypotheses"]))
    table.add_row("Timeline events", str(totals["events"]))
    console.print(table)

    if args.dry_run:
        return

    # Phase 3: Generate roll-up tiers
    console.print()
    with _make_progress() as progress:
        tier_task = progress.add_task("Phase 3: Generating tiers", total=0)
        _generate_rollup_tiers(delivery, extractor, all_entities, progress, tier_task)

    console.print("[green]Knowledge graph rebuild complete.[/]")


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

    if args.dry_run and not (args.rebuild_graph or args.graph_only):
        print(json.dumps([item.to_dict() for item in manifest], indent=2, sort_keys=True))
        return 0

    client = OpenVikingObservatoryClient(ObservatoryContextSettings())

    if not args.dry_run and hasattr(client, "health"):
        try:
            if not client.health():
                raise RuntimeError
        except Exception:
            url = getattr(getattr(client, "settings", None), "openviking_url", "http://127.0.0.1:1933")
            console.print(f"[red]OpenViking server is not reachable at {url}[/]")
            console.print("Start it with: uv run openviking-server --config config/openviking/ov.conf")
            return 1

    if args.check and not args.fix:
        missing = _check_manifest(client, manifest)
        return 1 if missing else 0

    if args.fix:
        console.rule("Checking for missing resources")
        missing = _check_manifest(client, manifest)
        if not missing:
            console.print("[green]All resources present — nothing to fix.[/]")
            return 0
        console.rule(f"Re-ingesting {len(missing)} missing resources")
        with _make_progress() as progress:
            task = progress.add_task("Re-ingesting", total=len(missing))
            for item in missing:
                client.add_manifest_resource(item, wait=False)
                progress.advance(task)
        if args.wait:
            with console.status("[bold]Waiting for OpenViking to process..."):
                try:
                    client.wait_until_processed(timeout=args.wait_timeout)
                except TimeoutError as exc:
                    console.print(f"[yellow]Warning: {exc}[/]")
        console.rule("Re-checking")
        still_missing = _check_manifest(client, manifest)
        return 1 if still_missing else 0

    # Phase 1: Resource upload (skip if --graph-only)
    if not args.graph_only:
        if args.dry_run:
            print(json.dumps([item.to_dict() for item in manifest], indent=2, sort_keys=True))
        else:
            queued = 0
            skipped = 0
            with _make_progress() as progress:
                task = progress.add_task("Phase 1: Uploading resources", total=len(manifest))
                for item in manifest:
                    if args.resume and client.resource_exists(item.uri):
                        skipped += 1
                    else:
                        client.add_manifest_resource(item, wait=False)
                        queued += 1
                    progress.advance(task)
            console.print(f"  Queued [green]{queued}[/], skipped [dim]{skipped}[/] existing")

    # Phase 2+3: Knowledge graph extraction
    if args.rebuild_graph or args.graph_only:
        delivery = ContextDelivery(client=client, extractor=None)
        _rebuild_knowledge_graph(delivery, manifest, args)

    # Final wait — covers both Phase 1 and Phase 2/3 queued resources
    if args.wait and not args.dry_run:
        with console.status("[bold]Waiting for OpenViking to finish processing..."):
            try:
                client.wait_until_processed(timeout=args.wait_timeout)
            except TimeoutError as exc:
                console.print(f"[yellow]Warning: {exc}[/]")
                console.print("Run `uv run scripts/viking_server_healthcheck.py` to check server status.")
                return 0
        console.print("[green]All resources processed.[/]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
