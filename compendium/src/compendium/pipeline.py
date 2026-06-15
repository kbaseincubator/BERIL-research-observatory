"""Compendium pipeline wiring for the statement-card synthesis wiki.

context-pack / audit (deterministic ingestion inputs) -> statement-graph -> plan-pages
-> wiki-contexts -> page-artifact (LLM-authored prose, validated) -> render-markdown
-> quality-synthesis.

Deterministic; no LLM on this path. ``dispatch`` is called by ``compendium.cli``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compendium import audit as audit_mod
from compendium.build.statement_graph import build_statement_graph, export_statement_graph_artifacts
from compendium.context_pack import build_context_pack, context_pack_bytes
from compendium.models import StatementCard
from compendium.pages import plan_pages, write_page_artifact, write_page_context
from compendium.quality.synthesis_quality import assess_synthesis_quality
from compendium.render.markdown import render_markdown_wiki
from compendium.validate import (
    validate_page_plan_file,
    validate_project_kg_file,
    validate_statement_card_file,
)

PKG_DIR = Path(__file__).resolve().parent
COMPENDIUM_DIR = PKG_DIR.parents[1]   # .../compendium


def _resolve_projects_dir(projects_dir: str) -> Path:
    p = Path(projects_dir)
    if p.is_absolute() and p.exists():
        return p
    for base in (Path.cwd(), COMPENDIUM_DIR, COMPENDIUM_DIR.parent):
        cand = (base / projects_dir).resolve()
        if cand.exists():
            return cand
    return p.resolve()


def _load_statement_cards(path: str) -> list[StatementCard]:
    result = validate_project_kg_file(path)
    return [record for record in result.records if isinstance(record, StatementCard)]


def _write_json_or_stdout(payload: dict | list, out: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if out:
        out_path = Path(out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"[compendium] wrote {out_path}")
        return
    print(text)


def _clean_page_context_artifacts(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    for pattern in ("*.context.json", "*.prompt.md"):
        for path in sorted(out_dir.rglob(pattern)):
            path.unlink()
    for path in sorted(
        (item for item in out_dir.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        try:
            path.rmdir()
        except OSError:
            pass


def _synthesis_quality_failed(metrics: dict) -> bool:
    evidence = metrics["evidence_resolution"]
    page = metrics["page_integrity"]
    links = metrics["link_integrity"]
    opportunities = metrics["opportunity_targets"]
    statement_links = metrics["statement_link_integrity"]
    return any(
        (
            metrics["graph_integrity"]["dangling_edges"],
            evidence["checked"] and evidence["unresolved"],
            links["broken_outgoing_link_count"],
            links["broken_backlink_count"],
            links["backlink_mismatch_count"],
            page["unknown_page_members"],
            page["unknown_section_members"],
            opportunities["missing_target_output_statement_ids"],
            statement_links["unresolved_statement_link_count"],
        )
    )


def dispatch(args) -> int:
    if args.cmd == "validate-card":
        result = validate_statement_card_file(args.path)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "validate-page-plan":
        result = validate_page_plan_file(args.path)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "context-pack":
        project_dir = Path(args.project).resolve()
        pack = build_context_pack(project_dir)
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(context_pack_bytes(pack))
        print(f"[compendium] context pack: {project_dir.name} -> {out_path}")
        print(f"[compendium] hash: {pack['context_pack_hash']}")
        return 0
    if args.cmd == "statement-graph":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        _write_json_or_stdout(graph, args.out)
        if args.artifacts_dir:
            artifacts_dir = Path(args.artifacts_dir).resolve()
            export_statement_graph_artifacts(graph, artifacts_dir)
            print(f"[compendium] graph artifacts -> {artifacts_dir}")
        return 0
    if args.cmd == "plan-pages":
        cards = _load_statement_cards(args.path)
        _write_json_or_stdout([plan.to_dict() for plan in plan_pages(cards)], args.out)
        return 0
    if args.cmd == "page-context":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        page_plans = plan_pages(cards)
        plans = {plan.id: plan for plan in page_plans}
        plan = plans.get(args.page_id)
        if plan is None:
            raise ValueError(f"unknown page id {args.page_id!r}")
        context_path, prompt_path = write_page_context(
            plan,
            cards,
            Path(args.out).resolve(),
            page_plans=page_plans,
            statement_graph=graph,
            source_root=args.source_root,
        )
        print(f"[compendium] page context: {context_path}")
        print(f"[compendium] page prompt: {prompt_path}")
        return 0
    if args.cmd == "wiki-contexts":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        page_plans = plan_pages(cards)
        out_dir = Path(args.out).resolve()
        _clean_page_context_artifacts(out_dir)
        written = []
        for plan in sorted(page_plans, key=lambda item: item.id):
            written.extend(
                write_page_context(
                    plan,
                    cards,
                    out_dir,
                    page_plans=page_plans,
                    statement_graph=graph,
                    source_root=args.source_root,
                )
            )
        print(f"[compendium] wrote {len(written)} page context artifacts -> {out_dir}")
        return 0
    if args.cmd == "page-artifact":
        cards = _load_statement_cards(args.path)
        plans = {plan.id: plan for plan in plan_pages(cards)}
        plan = plans.get(args.page_id)
        if plan is None:
            raise ValueError(f"unknown page id {args.page_id!r}")
        markdown_path, manifest_path = write_page_artifact(
            plan,
            cards,
            Path(args.out).resolve(),
            markdown=Path(args.markdown).read_text(encoding="utf-8"),
            model=args.model,
            prompt_hash=args.prompt_hash,
        )
        print(f"[compendium] page artifact: {markdown_path}")
        print(f"[compendium] manifest: {manifest_path}")
        return 0
    if args.cmd == "render-markdown":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        out_dir = Path(args.out).resolve()
        rendered = render_markdown_wiki(
            plan_pages(cards),
            out_dir,
            statement_graph=graph,
        )
        print(f"[compendium] rendered {len(rendered)} markdown wiki pages -> {out_dir}")
        return 0
    if args.cmd == "quality-synthesis":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        plans = plan_pages(cards)
        metrics = assess_synthesis_quality(
            cards,
            graph,
            plans,
            source_root=args.source_root,
        )
        _write_json_or_stdout(metrics, args.out)
        if _synthesis_quality_failed(metrics):
            print("[compendium] synthesis quality checks failed", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "audit":
        pdir = _resolve_projects_dir(args.projects_dir)
        rep = audit_mod.audit_corpus(pdir)
        print(json.dumps(rep["rollup"], indent=2, sort_keys=True))
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "audit.json").write_text(json.dumps(rep, indent=2, sort_keys=True))
        return 0

    print(f"[compendium] unknown command {args.cmd!r}")
    return 2
