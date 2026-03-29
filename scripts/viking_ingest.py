"""Build, ingest, check, and fix the OpenViking resource manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
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
from observatory_context.ingest import build_resource_manifest
from observatory_context.uris import (
    _ENTITY_TYPE_PLURALS,
    _ROOT,
)

if TYPE_CHECKING:
    from observatory_context.extraction import CBORGExtractor, EntityExtraction

console = Console()
REPO_ROOT = Path(__file__).resolve().parents[1]

_KG_URI = f"{_ROOT}/knowledge-graph"
_CACHE_DIR = REPO_ROOT / ".kg_cache"


def _make_progress(**kwargs) -> Progress:
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


# ------------------------------------------------------------------
# Extraction cache — avoid re-calling CBORG for unchanged projects
# ------------------------------------------------------------------


def _file_hash(path: Path) -> str:
    """SHA-256 of a file's content, or empty string if missing."""
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project_hash(pid: str) -> str:
    """Combined hash of a project's REPORT.md and provenance.yaml."""
    report_hash = _file_hash(REPO_ROOT / "projects" / pid / "REPORT.md")
    prov_hash = _file_hash(REPO_ROOT / "projects" / pid / "provenance.yaml")
    return hashlib.sha256(f"{report_hash}:{prov_hash}".encode()).hexdigest()


class _ExtractionCache:
    """Caches CBORG extraction results on disk to enable incremental rebuilds.

    Layout::

        .kg_cache/
            state.json              # {project_id: hash}
            extractions/
                <project_id>.json   # serialised EntityExtraction
    """

    def __init__(self, cache_dir: Path = _CACHE_DIR) -> None:
        self._dir = cache_dir
        self._extractions_dir = cache_dir / "extractions"
        self._state_path = cache_dir / "state.json"
        self._state: dict[str, str] = {}
        if self._state_path.exists():
            self._state = json.loads(self._state_path.read_text())

    def is_current(self, pid: str) -> bool:
        """True if the cached extraction matches the current project files."""
        cached_hash = self._state.get(pid)
        if not cached_hash:
            return False
        return cached_hash == _project_hash(pid)

    def load(self, pid: str) -> EntityExtraction:
        """Load a cached extraction result."""
        from observatory_context.extraction import EntityExtraction

        path = self._extractions_dir / f"{pid}.json"
        return EntityExtraction.model_validate_json(path.read_text())

    def save(self, pid: str, extraction: EntityExtraction) -> None:
        """Save an extraction result and update the hash."""
        self._extractions_dir.mkdir(parents=True, exist_ok=True)
        path = self._extractions_dir / f"{pid}.json"
        path.write_text(extraction.model_dump_json(indent=2))
        self._state[pid] = _project_hash(pid)

    def flush(self) -> None:
        """Write the state index to disk."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(self._state, indent=2, sort_keys=True))

    def clear(self) -> None:
        """Remove all cached data."""
        if self._dir.exists():
            shutil.rmtree(self._dir)
        self._state = {}


# ------------------------------------------------------------------
# Local file-tree builder for batch upload
# ------------------------------------------------------------------


def _write_file(base: Path, rel_path: str, content: str, metadata: dict | None = None) -> None:
    dest = base / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        if metadata:
            fh.write("---\n")
            fh.write(yaml.safe_dump(metadata, sort_keys=True))
            fh.write("---\n\n")
        fh.write(content)


# ------------------------------------------------------------------
# Deduplicating collector
# ------------------------------------------------------------------


class _MergedEntity:
    __slots__ = ("entity_type", "entity_id", "name", "projects", "metadata", "relations")

    def __init__(self, entity_type: str, entity_id: str, name: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.name = name
        self.projects: list[str] = []
        self.metadata: dict = {}
        self.relations: dict[str, dict] = {}

    def add(self, pid: str, metadata: dict, relations: list[dict]) -> None:
        if pid not in self.projects:
            self.projects.append(pid)
        self.metadata.update(metadata)
        for rel in relations:
            key = f"{rel['predicate']}__{rel['object']}"
            self.relations[key] = rel


class _MergedHypothesis:
    __slots__ = ("hyp_id", "claim", "status", "evidence_parts", "projects")

    def __init__(self, hyp_id: str, claim: str, status: str) -> None:
        self.hyp_id = hyp_id
        self.claim = claim
        self.status = status
        self.evidence_parts: list[str] = []
        self.projects: list[str] = []

    def add(self, pid: str, evidence_delta: str, status: str) -> None:
        if pid not in self.projects:
            self.projects.append(pid)
        if evidence_delta and evidence_delta not in self.evidence_parts:
            self.evidence_parts.append(evidence_delta)
        self.status = status


class _KnowledgeGraphCollector:
    def __init__(self) -> None:
        self.entities: dict[str, _MergedEntity] = {}
        self.hypotheses: dict[str, _MergedHypothesis] = {}
        self.timeline_events: dict[str, tuple[str, dict]] = {}

    def add_extraction(self, pid: str, extraction: EntityExtraction) -> None:
        for entity in extraction.entities:
            key = f"{entity.type}/{entity.id}"
            if key not in self.entities:
                self.entities[key] = _MergedEntity(entity.type, entity.id, entity.name)
            relations = [r.model_dump() for r in extraction.relations if r.subject == entity.id]
            self.entities[key].add(pid, entity.metadata, relations)

        for hyp in extraction.hypotheses:
            if hyp.id not in self.hypotheses:
                self.hypotheses[hyp.id] = _MergedHypothesis(hyp.id, hyp.claim, hyp.status)
            self.hypotheses[hyp.id].add(pid, hyp.evidence_delta, hyp.status)

        for evt in extraction.timeline_events:
            filename = f"{evt.date}_{pid}.yaml"
            content = f"date: {evt.date}\nevent: {evt.event}\ntype: {evt.type}\nproject: {evt.project or pid}\n"
            metadata = {"title": evt.event[:80], "kind": "timeline_event", "date": evt.date, "project_ids": [pid]}
            self.timeline_events[filename] = (content, metadata)

    def stage_all(self, base: Path) -> list[_MergedEntity]:
        for me in self.entities.values():
            self._stage_entity(base, me)

        for mh in self.hypotheses.values():
            evidence = "\n".join(mh.evidence_parts)
            content = f"claim: {mh.claim}\nstatus: {mh.status}\nevidence_delta: {evidence}\n"
            metadata = {"title": mh.claim[:80], "kind": "hypothesis", "status": mh.status, "project_ids": mh.projects}
            _write_file(base, f"hypotheses/{mh.hyp_id}/hypothesis.yaml", content, metadata)

        for filename, (content, metadata) in self.timeline_events.items():
            _write_file(base, f"timeline/{filename}", content, metadata)

        return list(self.entities.values())

    @staticmethod
    def _stage_entity(base: Path, me: _MergedEntity) -> None:
        plural = _ENTITY_TYPE_PLURALS.get(me.entity_type, f"{me.entity_type}s")
        entity_dir = f"entities/{plural}/{me.entity_id}"

        profile = {"name": me.name, "type": me.entity_type, "projects": me.projects, **me.metadata}
        _write_file(
            base, f"{entity_dir}/profile.yaml",
            yaml.safe_dump(profile, sort_keys=True),
            metadata={"title": me.name, "kind": "entity",
                       "entity_type": me.entity_type, "entity_id": me.entity_id},
        )

        for rel_key, rel in me.relations.items():
            _write_file(
                base, f"{entity_dir}/relations/{rel_key}.yaml",
                yaml.safe_dump(rel, sort_keys=True),
                metadata={"kind": "relation"},
            )

            obj_ref = rel["object"]
            parts = obj_ref.split("/", 1)
            if len(parts) == 2:
                obj_plural, obj_id = parts
                subj_ref = rel["subject"]
                predicate = rel["predicate"]
                inv_key = f"inv_{predicate}__{subj_ref.replace('/', '__')}"
                inverse_rel = {
                    "subject": obj_ref,
                    "predicate": f"inverse_{predicate}",
                    "object": subj_ref,
                    "evidence": rel.get("evidence", ""),
                    "confidence": rel.get("confidence", "moderate"),
                }
                _write_file(
                    base, f"entities/{obj_plural}/{obj_id}/relations/{inv_key}.yaml",
                    yaml.safe_dump(inverse_rel, sort_keys=True),
                    metadata={"kind": "relation"},
                )


# ------------------------------------------------------------------
# Tier generation
# ------------------------------------------------------------------


def _stage_rollup_tiers(
    base: Path,
    extractor: CBORGExtractor,
    all_entities: list[_MergedEntity],
    progress: Progress,
    task_id: int,
) -> None:
    type_summaries: dict[str, list[str]] = {}
    for entity in all_entities:
        plural = _ENTITY_TYPE_PLURALS.get(entity.entity_type, f"{entity.entity_type}s")
        type_summaries.setdefault(plural, []).append(f"- {entity.name} ({entity.entity_type}/{entity.entity_id})")

    total_steps = len(type_summaries) * 2 + 6
    progress.update(task_id, total=total_steps, completed=0)

    all_lines = []
    for plural, lines in sorted(type_summaries.items()):
        content = f"# Entities: {plural}\n\n" + "\n".join(lines)
        all_lines.extend(lines)

        progress.update(task_id, description=f"Tiers: entities/{plural}")
        abstract = extractor.generate_abstract(content)
        _write_file(base, f"entities/{plural}/.abstract.md", abstract,
                     {"title": f"{plural} abstract", "kind": "tier_summary"})
        progress.advance(task_id)
        overview = extractor.generate_overview(content)
        _write_file(base, f"entities/{plural}/.overview.md", overview,
                     {"title": f"{plural} overview", "kind": "tier_summary"})
        progress.advance(task_id)

    progress.update(task_id, description="Tiers: entities/")
    entities_content = f"# All entities\n\n{len(all_entities)} entities across {len(type_summaries)} types.\n\n" + "\n".join(all_lines)
    _write_file(base, "entities/.abstract.md", extractor.generate_abstract(entities_content),
                 {"title": "entities abstract", "kind": "tier_summary"})
    progress.advance(task_id)
    _write_file(base, "entities/.overview.md", extractor.generate_overview(entities_content),
                 {"title": "entities overview", "kind": "tier_summary"})
    progress.advance(task_id)

    progress.update(task_id, description="Tiers: knowledge-graph/")
    kg_content = (
        f"# Knowledge Graph\n\n"
        f"{len(all_entities)} entities, {len(type_summaries)} entity types.\n\n"
        f"Entity types: {', '.join(sorted(type_summaries.keys()))}"
    )
    _write_file(base, ".abstract.md", extractor.generate_abstract(kg_content),
                 {"title": "knowledge-graph abstract", "kind": "tier_summary"})
    progress.advance(task_id)
    _write_file(base, ".overview.md", extractor.generate_overview(kg_content),
                 {"title": "knowledge-graph overview", "kind": "tier_summary"})
    progress.advance(task_id)

    progress.update(task_id, description="Tiers: hypotheses/")
    _write_file(base, "hypotheses/.abstract.md",
                 extractor.generate_abstract("Hypotheses extracted from observatory project reports."),
                 {"title": "hypotheses abstract", "kind": "tier_summary"})
    progress.advance(task_id)
    _write_file(base, "hypotheses/.overview.md",
                 extractor.generate_overview("Hypotheses extracted from observatory project reports."),
                 {"title": "hypotheses overview", "kind": "tier_summary"})
    progress.advance(task_id)


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and ingest observatory resources into OpenViking.")
    parser.add_argument("--dry-run", action="store_true", help="Print the manifest without uploading resources.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N manifest items.")
    parser.add_argument(
        "--project", action="append", default=None,
        help="Restrict ingest to one project ID. Repeat to include multiple projects.",
    )
    parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True,
        help="Skip resources whose target URI already exists in OpenViking.",
    )
    parser.add_argument("--wait", action="store_true",
        help="Wait for OpenViking to finish processing after queueing all uploads.",
    )
    parser.add_argument("--wait-timeout", type=float, default=None,
        help="Optional timeout in seconds for the final processing wait.",
    )
    parser.add_argument("--manifest-json", type=Path, default=None,
        help="Optional path to write the manifest as JSON.",
    )
    parser.add_argument("--max-figures", type=int, default=None,
        help="Skip projects with more than N figures (e.g. 25 to exclude large figure-heavy projects).",
    )
    parser.add_argument("--max-report-kb", type=float, default=None,
        help="Skip projects whose REPORT.md exceeds N kilobytes (e.g. 50).",
    )
    parser.add_argument("--check", action="store_true",
        help="Verify all manifest resources exist in OpenViking without uploading.",
    )
    parser.add_argument("--fix", action="store_true",
        help="Re-ingest any missing resources found by --check.",
    )
    parser.add_argument("--rebuild-graph", action="store_true",
        help="Run Phase 2+3: extract knowledge graph from projects via CBORG after resource upload.",
    )
    parser.add_argument("--graph-only", action="store_true",
        help="Skip Phase 1 resource upload, only rebuild knowledge graph.",
    )
    parser.add_argument("--model", type=str, default=None,
        help="CBORG model override (e.g. 'claude-haiku', 'gpt-5.4-mini'). Uses config default if unset.",
    )
    parser.add_argument(
        "--clean", action=argparse.BooleanOptionalAction, default=False,
        help="Delete existing knowledge graph and extraction cache before rebuilding.",
    )
    return parser


def _filter_oversized_projects(manifest: list, max_figures: int | None, max_report_kb: float | None) -> list:
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
    missing: list = []
    with _make_progress() as progress:
        task = progress.add_task("Checking resources", total=len(manifest))
        for item in manifest:
            missing.append(item) if not client.resource_exists(item.uri) else None
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


def _fetch_model_limits(api_key: str, model: str) -> dict:
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
    client: OpenVikingObservatoryClient,
    manifest: list,
    args: argparse.Namespace,
) -> None:
    """Extract knowledge graph incrementally, merge, and upload as one batch.

    Uses a local extraction cache (.kg_cache/) to skip CBORG calls for
    projects whose REPORT.md and provenance.yaml haven't changed.
    """
    from observatory_context.extraction import CBORGExtractor

    settings = ObservatoryContextSettings()
    model = args.model or settings.cborg_model
    api_key = settings.cborg_api_key
    if not api_key:
        console.print("[red]Error: CBORG_API_KEY not set. Required for --rebuild-graph.[/]")
        return

    cache = _ExtractionCache()

    # --clean: wipe OpenViking knowledge graph + local cache
    if args.clean and not args.dry_run:
        cache.clear()
        with console.status("[bold]Deleting existing knowledge graph..."):
            try:
                client.client.rm(_KG_URI, recursive=True)
                console.print(f"  Deleted [bold]{_KG_URI}[/]")
            except Exception as exc:
                if "NotFound" in type(exc).__name__ or "NotFound" in str(exc):
                    console.print("  [dim]No existing knowledge graph to delete[/]")
                else:
                    raise

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

    project_ids = sorted({pid for item in manifest for pid in item.project_ids})

    staging_dir = Path(tempfile.mkdtemp(prefix="ov_kg_"))
    collector = _KnowledgeGraphCollector()
    cached_count = 0
    extracted_count = 0
    skipped = 0
    totals = {"entities": 0, "relations": 0, "hypotheses": 0, "events": 0}

    try:
        with _make_progress() as progress:
            task = progress.add_task("Phase 2: Extracting", total=len(project_ids))

            for pid in project_ids:
                report_path = REPO_ROOT / "projects" / pid / "REPORT.md"

                if not report_path.exists():
                    skipped += 1
                    progress.advance(task)
                    continue

                # Check cache — skip CBORG call if project hasn't changed
                if cache.is_current(pid):
                    progress.update(task, description=f"Cached: {pid}")
                    extraction = cache.load(pid)
                    cached_count += 1
                else:
                    progress.update(task, description=f"Extracting: {pid}")

                    if args.dry_run:
                        progress.advance(task)
                        continue

                    report = report_path.read_text(encoding="utf-8")
                    prov_path = REPO_ROOT / "projects" / pid / "provenance.yaml"
                    provenance: dict = {}
                    if prov_path.exists():
                        provenance = yaml.safe_load(prov_path.read_text(encoding="utf-8")) or {}

                    try:
                        extraction = extractor.extract_knowledge(report, provenance)
                    except ValueError:
                        skipped += 1
                        progress.advance(task)
                        continue

                    cache.save(pid, extraction)
                    extracted_count += 1

                totals["entities"] += len(extraction.entities)
                totals["relations"] += len(extraction.relations)
                totals["hypotheses"] += len(extraction.hypotheses)
                totals["events"] += len(extraction.timeline_events)

                collector.add_extraction(pid, extraction)
                progress.advance(task)

        # Save cache state
        if not args.dry_run:
            cache.flush()

        # Summary
        unique_entities = len(collector.entities)
        unique_hypotheses = len(collector.hypotheses)
        table = Table(title="Phase 2 Summary", show_header=False, box=None, pad_edge=False)
        table.add_column(style="bold")
        table.add_column(justify="right")
        table.add_row("Projects extracted (CBORG)", f"[cyan]{extracted_count}[/]")
        table.add_row("Projects from cache", f"[green]{cached_count}[/]")
        table.add_row("Projects skipped", str(skipped))
        table.add_row("Entities (extracted)", str(totals["entities"]))
        table.add_row("Entities (unique)", f"[green]{unique_entities}[/]")
        table.add_row("Relations", str(totals["relations"]))
        table.add_row("Hypotheses (extracted)", str(totals["hypotheses"]))
        table.add_row("Hypotheses (unique)", f"[green]{unique_hypotheses}[/]")
        table.add_row("Timeline events", str(totals["events"]))
        console.print(table)

        if args.dry_run:
            return

        # Stage merged data
        with console.status("[bold]Staging merged knowledge graph..."):
            all_entities = collector.stage_all(staging_dir)

        # Phase 3: Tier summaries
        console.print()
        with _make_progress() as progress:
            tier_task = progress.add_task("Phase 3: Generating tiers", total=0)
            _stage_rollup_tiers(staging_dir, extractor, all_entities, progress, tier_task)

        # Count staged files
        file_count = sum(1 for f in staging_dir.rglob("*") if f.is_file())
        console.print(f"\n  Staged [bold]{file_count}[/] files in local tree")

        # Delete old knowledge graph before uploading new one to avoid duplicates
        with console.status("[bold]Replacing knowledge graph in OpenViking..."):
            # Wait for any pending processing first — rm fails on in-progress resources
            try:
                client.wait_until_processed(timeout=120)
            except (TimeoutError, Exception):
                pass  # best effort
            try:
                client.client.rm(_KG_URI, recursive=True)
            except Exception as exc:
                if "NotFound" not in type(exc).__name__ and "NotFound" not in str(exc):
                    console.print(f"[yellow]Warning: could not delete old graph: {exc}[/]")

        # Single batch upload
        with console.status("[bold]Uploading knowledge graph to OpenViking..."):
            result = client.client.add_resource(
                path=str(staging_dir),
                to=_KG_URI,
                reason="Knowledge graph rebuild (batch)",
                wait=False,
            )

        meta = result.get("meta", {})
        processed = len(meta.get("processed_files", []))
        failed = len(meta.get("failed_files", []))

        if failed:
            console.print(f"  Uploaded [green]{processed}[/] files, [red]{failed} failed[/]")
            for f in meta.get("failed_files", [])[:10]:
                console.print(f"    [red]✗[/] {f}")
        else:
            console.print(f"  Uploaded [green]{processed}[/] files")

        console.print("[green]Knowledge graph rebuild complete.[/]")

    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


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
        _rebuild_knowledge_graph(client, manifest, args)

    # Final wait
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
