"""Compendium CLI for the lightweight topic-MOC wiki."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compendium", description="Lightweight topic-MOC synthesis wiki")
    sub = parser.add_subparsers(dest="cmd")
    audit = sub.add_parser("audit")
    audit.add_argument("--projects", nargs="*", default=None)
    audit.add_argument("--projects-dir", default="../projects")
    audit.add_argument("--out", default="out")
    context_pack = sub.add_parser("context-pack")
    context_pack.add_argument("project")
    context_pack.add_argument("--out", required=True)
    plan_pages = sub.add_parser("plan-pages")
    plan_pages.add_argument("path")
    plan_pages.add_argument("--source-root", default="../projects")
    plan_pages.add_argument("--out")
    page_context = sub.add_parser("page-context")
    page_context.add_argument("path")
    page_context.add_argument("--page-id", required=True)
    page_context.add_argument("--source-root", default="../projects")
    page_context.add_argument("--out", required=True)
    page_artifact = sub.add_parser("page-artifact")
    page_artifact.add_argument("path")
    page_artifact.add_argument("--page-id", required=True)
    page_artifact.add_argument("--markdown", required=True)
    page_artifact.add_argument("--out", required=True)
    page_artifact.add_argument("--model", required=True)
    page_artifact.add_argument("--prompt-hash", required=True)
    page_artifact.add_argument("--source-root", default="../projects")
    wiki_contexts = sub.add_parser("wiki-contexts")
    wiki_contexts.add_argument("path")
    wiki_contexts.add_argument("--source-root", default="../projects")
    wiki_contexts.add_argument("--out", required=True)
    render_markdown = sub.add_parser("render-markdown")
    render_markdown.add_argument("path")
    render_markdown.add_argument("--source-root", default="../projects")
    render_markdown.add_argument("--out", required=True)
    check = sub.add_parser("check")
    check.add_argument("--wiki", required=True)
    validate_card = sub.add_parser("validate-card")
    validate_card.add_argument("path")
    validate_kg = sub.add_parser("validate-kg")
    validate_kg.add_argument("path")
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
