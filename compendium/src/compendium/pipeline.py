"""End-to-end Compendium pipeline wiring (Task 10).

audit -> extract (Stage-1) -> ground -> verify -> build (canonicalize+assemble+layout)
-> KGX export -> render (static site) -> quality assessment.

Deterministic; no LLM on this path. ``dispatch`` is called by ``compendium.cli``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import yaml

from compendium import audit as audit_mod
from compendium.build.assemble import build, to_kgx
from compendium.corrections import load_corrections
from compendium.extract.structural import extract_project
from compendium.ground.grounder import ground
from compendium.models import ProjectKG
from compendium.quality.kg_quality import assess_kg
from compendium.quality.wiki_quality import assess_wiki
from compendium.render.render import render_site
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
