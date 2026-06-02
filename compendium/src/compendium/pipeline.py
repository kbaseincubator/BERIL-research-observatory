"""End-to-end Compendium pipeline wiring (Task 10).

audit -> extract (Stage-1) -> ground -> verify -> build (canonicalize+assemble+layout)
-> KGX export -> render (static site) -> quality assessment.

Deterministic; no LLM on this path. ``dispatch`` is called by ``compendium.cli``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from compendium import audit as audit_mod
from compendium.build.assemble import build, to_kgx
from compendium.build.statement_graph import build_statement_graph, export_statement_graph_artifacts
from compendium.context_pack import build_context_pack, context_pack_bytes
from compendium.corrections import load_corrections
from compendium.extract.structural import extract_project
from compendium.ground.grounder import ground
from compendium.models import ProjectKG, StatementCard
from compendium.pages import plan_pages, write_page_artifact
from compendium.quality.kg_quality import assess_kg
from compendium.quality.review_queue import build_review_queue
from compendium.quality.synthesis_dashboard import (
    build_synthesis_quality_dashboard,
    render_synthesis_quality_dashboard_html,
)
from compendium.quality.synthesis_quality import assess_synthesis_quality
from compendium.quality.wiki_quality import assess_wiki
from compendium.render.render import render_site
from compendium.render.synthesis import render_synthesis_site
from compendium.validate import (
    validate_page_plan_file,
    validate_project_kg_file,
    validate_statement_card_file,
)
from compendium.verify.verifier import verify

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


def _project_kgs(projects, projects_dir: Path, corpus_audit: dict) -> list[ProjectKG]:
    pkgs: list[ProjectKG] = []
    for pid in projects:
        pdir = projects_dir / pid
        a = corpus_audit.get("projects", {}).get(pid)
        pkg = extract_project(pdir, audit=a)
        pkg = ground(pkg)
        pkg = verify(pkg, pdir)
        pkgs.append(pkg)
    return pkgs


def _write_kg_yaml(pkgs: list[ProjectKG], out_kg_dir: Path) -> None:
    out_kg_dir.mkdir(parents=True, exist_ok=True)
    for pkg in pkgs:
        text = yaml.safe_dump(pkg.to_dict(), sort_keys=True, allow_unicode=True)
        (out_kg_dir / f"{pkg.project.id}.kg.yaml").write_text(text)


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


def _write_json_file(payload: dict | list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _run_statement_quality(path: str, out: str, source_root: str | None = None) -> int:
    cards = _load_statement_cards(path)
    graph = build_statement_graph(cards)
    plans = plan_pages(cards)
    metrics = assess_synthesis_quality(
        cards,
        graph,
        plans,
        source_root=source_root,
    )
    queue = build_review_queue(
        cards,
        graph,
        plans,
        unresolved_statement_links=metrics,
    )

    out_dir = Path(out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json_file(metrics, out_dir / "quality.json")
    _write_json_file(queue, out_dir / "review-queue.json")
    _write_json_file(
        build_synthesis_quality_dashboard(metrics, queue),
        out_dir / "quality-dashboard.json",
    )
    (out_dir / "quality-dashboard.html").write_text(
        render_synthesis_quality_dashboard_html(metrics, queue),
        encoding="utf-8",
    )
    print(f"[compendium] statement quality artifacts -> {out_dir}")
    if _synthesis_quality_failed(metrics):
        print("[compendium] synthesis quality checks failed", file=sys.stderr)
        return 1
    return 0


def run_all(projects, projects_dir: str, out: str, corrections_dir: str | None = None) -> dict:
    pdir = _resolve_projects_dir(projects_dir)
    out_dir = Path(out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    kg_dir = COMPENDIUM_DIR / "kg"
    corr_dir = Path(corrections_dir) if corrections_dir else (COMPENDIUM_DIR / "corrections")

    # audit (Phase-0 premise check) restricted to the chosen projects when given
    corpus_audit = {"projects": {}, "rollup": {}}
    for pid in projects:
        corpus_audit["projects"][pid] = audit_mod.audit_project(pdir / pid)

    pkgs = _project_kgs(projects, pdir, corpus_audit)
    _write_kg_yaml(pkgs, kg_dir)

    corrections = load_corrections(corr_dir)
    graph = build(pkgs, corrections=corrections, layout_seed=0)

    to_kgx(graph, out_dir)
    # Cross-project synthesis narratives (produced offline by the kg-synthesize skill) are injected
    # into the deterministic render if present — never generated on the render path.
    narration_path = kg_dir / "narration.json"
    narration = json.loads(narration_path.read_text()) if narration_path.exists() else None
    site_dir = out_dir / "site"
    render_site(graph, site_dir, narration=narration)

    kgq = assess_kg(graph)
    wikiq = assess_wiki(site_dir, graph)
    quality = {"projects": list(projects), "kg": kgq, "wiki": wikiq,
               "audit": {pid: corpus_audit["projects"][pid].get("coverage") for pid in projects}}
    (out_dir / "quality.json").write_text(json.dumps(quality, indent=2, sort_keys=True))

    print(f"[compendium] projects: {', '.join(projects)}")
    print(f"[compendium] KG: {kgq['n_nodes']} nodes, {kgq['n_edges']} edges; "
          f"grounding_rate={kgq['grounding_rate']:.2f}; cross_project_edges={kgq['cross_project_edges']}; "
          f"dangling_edges={kgq['dangling_edges']}")
    print(f"[compendium] node tiers: {kgq['node_tier_distribution']}")
    print(f"[compendium] wiki: {wikiq['page_count']} pages; coverage={wikiq['coverage']:.2f}; "
          f"broken_links={wikiq['broken_internal_links']}")
    print(f"[compendium] artifacts: {out_dir}/nodes.tsv, edges.tsv, site/, quality.json; kg/ -> {kg_dir}")
    return quality


def dispatch(args) -> int:
    if args.cmd == "validate-card":
        result = validate_statement_card_file(args.path)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "validate-project-kg":
        result = validate_project_kg_file(args.path)
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
    if args.cmd == "quality" and args.statement_kg:
        return _run_statement_quality(args.statement_kg, args.out, args.source_root)
    if args.cmd == "tracer":
        from compendium.tracer import generate_adp1_tracer_artifacts

        tracer_kwargs = {}
        if args.project_kg:
            tracer_kwargs["fixture_path"] = args.project_kg
        if args.source_root:
            tracer_kwargs["source_root"] = args.source_root
        artifacts = generate_adp1_tracer_artifacts(args.out, **tracer_kwargs)
        print(f"[compendium] tracer artifacts -> {artifacts.output_dir.resolve()}")
        print(f"[compendium] site -> {artifacts.site_dir.resolve()}")
        print(f"[compendium] quality -> {artifacts.quality_json.resolve()}")
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
    if args.cmd == "synthesize-page":
        cards = _load_statement_cards(args.path)
        plans = {plan.id: plan for plan in plan_pages(cards)}
        plan = plans.get(args.page_id)
        if plan is None:
            raise ValueError(f"unknown page id {args.page_id!r}")
        markdown_path, manifest_path = write_page_artifact(
            plan,
            cards,
            Path(args.out).resolve(),
            model=args.model,
            prompt_hash=args.prompt_hash,
        )
        print(f"[compendium] page artifact: {markdown_path}")
        print(f"[compendium] manifest: {manifest_path}")
        return 0
    if args.cmd == "render-synthesis":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        out_dir = Path(args.out).resolve()
        rendered = render_synthesis_site(
            cards,
            plan_pages(cards),
            out_dir,
            statement_graph=graph,
        )
        print(f"[compendium] rendered {len(rendered)} synthesis pages -> {out_dir}")
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
        if args.dashboard_out:
            queue = build_review_queue(
                cards,
                graph,
                plans,
                unresolved_statement_links=metrics,
            )
            dashboard_path = Path(args.dashboard_out).resolve()
            dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            dashboard_path.write_text(
                render_synthesis_quality_dashboard_html(metrics, queue),
                encoding="utf-8",
            )
            print(f"[compendium] dashboard: {dashboard_path}")
        _write_json_or_stdout(metrics, args.out)
        if _synthesis_quality_failed(metrics):
            print("[compendium] synthesis quality checks failed", file=sys.stderr)
            return 1
        return 0
    if args.cmd == "review-queue":
        cards = _load_statement_cards(args.path)
        graph = build_statement_graph(cards)
        plans = plan_pages(cards)
        metrics = assess_synthesis_quality(
            cards,
            graph,
            plans,
            source_root=args.source_root,
        )
        queue = build_review_queue(
            cards,
            graph,
            plans,
            unresolved_statement_links=metrics,
            limit=args.limit,
        )
        _write_json_or_stdout(queue, args.out)
        return 0

    projects = args.projects or []
    if args.cmd in ("build", "render", "quality", "all") and not projects:
        print("[compendium] provide --projects <id ...> (this build does not ingest all projects).")
        return 2
    if args.cmd == "audit":
        pdir = _resolve_projects_dir(args.projects_dir)
        rep = audit_mod.audit_corpus(pdir)
        print(json.dumps(rep["rollup"], indent=2, sort_keys=True))
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "audit.json").write_text(json.dumps(rep, indent=2, sort_keys=True))
        return 0
    # build / render / quality / all currently share the full deterministic pipeline
    run_all(projects, args.projects_dir, args.out)
    return 0
