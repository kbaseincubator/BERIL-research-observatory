"""Compendium CLI — deterministic statement-card synthesis-wiki commands.

The statement-card pipeline is the single workflow: ``audit`` and ``context-pack``
for ingestion inputs, then ``statement-graph`` -> ``plan-pages`` -> ``wiki-contexts``
-> ``page-artifact`` -> ``render-markdown`` -> ``quality-synthesis``/``review-queue``.
``dispatch`` is implemented in :mod:`compendium.pipeline`.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compendium", description="Deterministic KG-centered scientific wiki")
    sub = parser.add_subparsers(dest="cmd")
    audit = sub.add_parser("audit")
    audit.add_argument("--projects", nargs="*", default=None)
    audit.add_argument("--projects-dir", default="../projects")
    audit.add_argument("--out", default="out")
    quality = sub.add_parser("quality")
    quality.add_argument("--statement-kg", required=True)
    quality.add_argument("--source-root")
    quality.add_argument("--out", default="out")
    context_pack = sub.add_parser("context-pack")
    context_pack.add_argument("project")
    context_pack.add_argument("--out", required=True)
    statement_graph = sub.add_parser("statement-graph")
    statement_graph.add_argument("path")
    statement_graph.add_argument("--out")
    statement_graph.add_argument("--artifacts-dir")
    plan_pages = sub.add_parser("plan-pages")
    plan_pages.add_argument("path")
    plan_pages.add_argument("--out")
    page_context = sub.add_parser("page-context")
    page_context.add_argument("path")
    page_context.add_argument("--page-id", required=True)
    page_context.add_argument("--source-root")
    page_context.add_argument("--out", required=True)
    page_artifact = sub.add_parser("page-artifact")
    page_artifact.add_argument("path")
    page_artifact.add_argument("--page-id", required=True)
    page_artifact.add_argument("--markdown", required=True)
    page_artifact.add_argument("--out", required=True)
    page_artifact.add_argument("--model", required=True)
    page_artifact.add_argument("--prompt-hash", required=True)
    wiki_contexts = sub.add_parser("wiki-contexts")
    wiki_contexts.add_argument("path")
    wiki_contexts.add_argument("--source-root")
    wiki_contexts.add_argument("--out", required=True)
    render_markdown = sub.add_parser("render-markdown")
    render_markdown.add_argument("path")
    render_markdown.add_argument("--out", required=True)
    quality_synthesis = sub.add_parser("quality-synthesis")
    quality_synthesis.add_argument("path")
    quality_synthesis.add_argument("--source-root")
    quality_synthesis.add_argument("--out")
    quality_synthesis.add_argument("--dashboard-out")
    review_queue = sub.add_parser("review-queue")
    review_queue.add_argument("path")
    review_queue.add_argument("--source-root")
    review_queue.add_argument("--limit", type=int)
    review_queue.add_argument("--out")
    tracer = sub.add_parser("tracer")
    tracer.add_argument("--project-kg")
    tracer.add_argument("--source-root")
    tracer.add_argument("--wiki")
    tracer.add_argument("--out", required=True)
    validate_card = sub.add_parser("validate-card")
    validate_card.add_argument("path")
    validate_project_kg = sub.add_parser("validate-project-kg")
    validate_project_kg.add_argument("path")
    validate_page_plan = sub.add_parser("validate-page-plan")
    validate_page_plan.add_argument("path")
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    try:
        from compendium import pipeline  # noqa: WPS433
    except Exception:  # pragma: no cover - import guard
        print(f"[compendium] '{args.cmd}' could not load the pipeline module.", file=sys.stderr)
        return 2
    try:
        return pipeline.dispatch(args)
    except (OSError, ValueError) as exc:
        print(f"[compendium] error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
