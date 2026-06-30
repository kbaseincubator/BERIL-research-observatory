"""Compendium pipeline wiring for the lightweight topic-MOC wiki."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compendium import audit as audit_mod
from compendium import data_index, people
from compendium.check import check_wiki
from compendium.context_pack import build_context_pack, context_pack_bytes
from compendium.models import StatementCard
from compendium.pages import plan_pages, write_page_artifact, write_page_context
from compendium.registry import Registry
from compendium.render.cosma import write_cosma_project
from compendium.render.markdown import render_markdown_wiki
from compendium.validate import (
    validate_page_plan_file,
    validate_project_kg_file,
    validate_statement_card_file,
)

PKG_DIR = Path(__file__).resolve().parent
COMPENDIUM_DIR = PKG_DIR.parents[1]   # .../compendium
REGISTRY_PATH = COMPENDIUM_DIR / "registry.yaml"
COLLECTIONS_PATH = COMPENDIUM_DIR.parent / "ui" / "config" / "collections.yaml"


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


def _build_plan_inputs(source_root: str | None) -> dict:
    """Assemble ``registry`` / ``authors`` / ``collections`` for ``plan_pages``.

    Each input is optional: ``registry.yaml`` is loaded when present (else None, identity
    resolution); the author and collection indexes are built from ``source_root`` READMEs and the
    corpus ``collections.yaml`` when those exist (else ``{}``). Pages just omit author/data when
    their inputs are absent, so the planner still works on bare cards.
    """
    registry = Registry.from_yaml(REGISTRY_PATH) if REGISTRY_PATH.is_file() else None

    authors: dict = {}
    collections: dict = {}
    root = _resolve_projects_dir(source_root) if source_root else None
    if root is not None and root.is_dir():
        project_to_readme = {
            child.name: (child / "README.md").read_text(encoding="utf-8", errors="replace")
            for child in sorted(root.iterdir())
            if child.is_dir() and (child / "README.md").is_file()
        }
        authors = people.build_author_index(project_to_readme)

        if COLLECTIONS_PATH.is_file():
            canonical = data_index.load_canonical_ids(COLLECTIONS_PATH)
            cited = {
                child.name: data_index.cited_collections(child, canonical)
                for child in sorted(root.iterdir())
                if child.is_dir()
            }
            collections = data_index.build_collection_index(cited, canonical)

    return {"registry": registry, "authors": authors, "collections": collections}


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


def dispatch(args) -> int:
    if args.cmd == "validate-card":
        result = validate_statement_card_file(args.path)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "validate-kg":
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
    if args.cmd == "plan-pages":
        cards = _load_statement_cards(args.path)
        plan_inputs = _build_plan_inputs(getattr(args, "source_root", None))
        _write_json_or_stdout(
            [plan.to_dict() for plan in plan_pages(cards, **plan_inputs)], args.out
        )
        return 0
    if args.cmd == "page-context":
        cards = _load_statement_cards(args.path)
        page_plans = plan_pages(cards, **_build_plan_inputs(args.source_root))
        plans = {plan.id: plan for plan in page_plans}
        plan = plans.get(args.page_id)
        if plan is None:
            raise ValueError(f"unknown page id {args.page_id!r}")
        context_path, prompt_path = write_page_context(
            plan,
            cards,
            Path(args.out).resolve(),
            page_plans=page_plans,
            source_root=args.source_root,
        )
        print(f"[compendium] page context: {context_path}")
        print(f"[compendium] page prompt: {prompt_path}")
        return 0
    if args.cmd == "wiki-contexts":
        cards = _load_statement_cards(args.path)
        page_plans = plan_pages(cards, **_build_plan_inputs(args.source_root))
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
                    source_root=args.source_root,
                )
            )
        print(f"[compendium] wrote {len(written)} page context artifacts -> {out_dir}")
        return 0
    if args.cmd == "page-artifact":
        cards = _load_statement_cards(args.path)
        plan_inputs = _build_plan_inputs(getattr(args, "source_root", None))
        plans = {plan.id: plan for plan in plan_pages(cards, **plan_inputs)}
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
            page_plans=list(plans.values()),
        )
        print(f"[compendium] page artifact: {markdown_path}")
        print(f"[compendium] manifest: {manifest_path}")
        return 0
    if args.cmd == "render-markdown":
        cards = _load_statement_cards(args.path)
        out_dir = Path(args.out).resolve()
        rendered = render_markdown_wiki(
            plan_pages(cards, **_build_plan_inputs(getattr(args, "source_root", None))),
            out_dir,
        )
        print(f"[compendium] rendered {len(rendered)} markdown wiki pages -> {out_dir}")
        return 0
    if args.cmd == "export-cosma":
        cards = _load_statement_cards(args.path)
        plan_inputs = _build_plan_inputs(getattr(args, "source_root", None))
        written = write_cosma_project(
            plan_pages(cards, **plan_inputs),
            wiki_dir=Path(args.wiki).resolve(),
            out_dir=Path(args.out).resolve(),
            title=args.title,
        )
        out_dir = Path(args.out).resolve()
        print(f"[compendium] wrote {len(written)} cosma files -> {out_dir}")
        print(f"[compendium] next: cd {out_dir} && npx -y @graphlab-fr/cosma modelize")
        return 0
    if args.cmd == "check":
        problems = check_wiki(Path(args.wiki).resolve())
        for problem in problems:
            print(problem)
        if problems:
            print(f"[compendium] wiki integrity check found {len(problems)} problem(s)", file=sys.stderr)
            return 1
        print("[compendium] wiki integrity check passed")
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
