"""Deterministic tracer artifact generation for statement-card fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from compendium.build.statement_graph import (
    build_statement_graph,
    export_statement_graph_artifacts,
)
from compendium.models import PagePlan, StatementCard
from compendium.pages import write_page_context
from compendium.pages.plan import plan_pages
from compendium.quality.review_queue import build_review_queue
from compendium.quality.synthesis_dashboard import (
    build_synthesis_quality_dashboard,
    render_synthesis_quality_dashboard_html,
)
from compendium.quality.synthesis_quality import assess_synthesis_quality
from compendium.render.markdown import render_markdown_wiki
from compendium.validate import validate_project_kg_file

PKG_DIR = Path(__file__).resolve().parent
COMPENDIUM_DIR = PKG_DIR.parents[1]
REPO_ROOT = COMPENDIUM_DIR.parent
ADP1_TRACER_FIXTURE = COMPENDIUM_DIR / "fixtures" / "statement_cards" / "adp1_tracer.yaml"
ADP1_SOURCE_ROOT = REPO_ROOT / "projects"


@dataclass(frozen=True)
class TracerArtifacts:
    """Paths and in-memory records produced by a tracer artifact build."""

    output_dir: Path
    graph_dir: Path
    graph_json: Path
    nodes_tsv: Path
    edges_tsv: Path
    page_plan_json: Path
    page_context_dir: Path
    page_context_paths: list[Path]
    page_prompt_paths: list[Path]
    markdown_wiki_dir: Path | None
    markdown_wiki_paths: list[Path]
    quality_json: Path
    quality_dashboard_json: Path
    quality_dashboard_html: Path
    review_queue_json: Path
    cards: list[StatementCard]
    graph: dict[str, list[dict[str, Any]]]
    page_plans: list[PagePlan]
    quality: dict[str, Any]
    review_queue: list[dict[str, Any]]


def load_statement_cards(path: str | Path) -> list[StatementCard]:
    """Load a statement-card project KG fixture from YAML or JSON."""
    result = validate_project_kg_file(path)
    return [record for record in result.records if isinstance(record, StatementCard)]


def generate_tracer_artifacts(
    cards: list[StatementCard],
    output_dir: str | Path,
    *,
    source_root: str | Path | None = None,
    authored_pages_dir: str | Path | None = None,
) -> TracerArtifacts:
    """Write deterministic graph, page context, quality, and review artifacts.

    This helper is intentionally offline. It composes the deterministic graph,
    page-plan, page-context, quality, dashboard, and review-queue primitives
    without calling synthesis skills or model-backed services. If authored
    pages are supplied, it also publishes the Markdown wiki.
    """
    card_list = list(cards)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    graph = build_statement_graph(card_list)
    graph_dir = out_dir / "graph"
    export_statement_graph_artifacts(graph, graph_dir)

    page_plans = plan_pages(card_list)
    page_plan_json = out_dir / "page-plans.json"
    _write_json([plan.to_dict() for plan in page_plans], page_plan_json)

    page_context_dir = out_dir / "page-contexts"
    page_context_paths = []
    page_prompt_paths = []
    for plan in sorted(page_plans, key=lambda item: item.id):
        context_path, prompt_path = write_page_context(
            plan,
            card_list,
            page_context_dir,
            page_plans=page_plans,
            statement_graph=graph,
            source_root=source_root,
        )
        page_context_paths.append(context_path)
        page_prompt_paths.append(prompt_path)

    markdown_wiki_dir = None
    markdown_wiki_paths = []
    if authored_pages_dir is not None:
        markdown_wiki_dir = out_dir / "wiki"
        markdown_wiki_paths = render_markdown_wiki(
            page_plans,
            authored_pages_dir,
            markdown_wiki_dir,
            statement_graph=graph,
        )

    quality = assess_synthesis_quality(
        card_list,
        graph,
        page_plans,
        source_root=source_root,
    )
    quality_json = out_dir / "quality.json"
    _write_json(quality, quality_json)

    review_queue = build_review_queue(
        card_list,
        graph,
        page_plans,
        unresolved_statement_links=quality,
    )
    review_queue_json = out_dir / "review-queue.json"
    _write_json(review_queue, review_queue_json)

    dashboard = build_synthesis_quality_dashboard(quality, review_queue)
    quality_dashboard_json = out_dir / "quality-dashboard.json"
    _write_json(dashboard, quality_dashboard_json)

    quality_dashboard_html = out_dir / "quality-dashboard.html"
    quality_dashboard_html.write_text(
        render_synthesis_quality_dashboard_html(quality, review_queue),
        encoding="utf-8",
    )

    return TracerArtifacts(
        output_dir=out_dir,
        graph_dir=graph_dir,
        graph_json=graph_dir / "graph.json",
        nodes_tsv=graph_dir / "nodes.tsv",
        edges_tsv=graph_dir / "edges.tsv",
        page_plan_json=page_plan_json,
        page_context_dir=page_context_dir,
        page_context_paths=page_context_paths,
        page_prompt_paths=page_prompt_paths,
        markdown_wiki_dir=markdown_wiki_dir,
        markdown_wiki_paths=markdown_wiki_paths,
        quality_json=quality_json,
        quality_dashboard_json=quality_dashboard_json,
        quality_dashboard_html=quality_dashboard_html,
        review_queue_json=review_queue_json,
        cards=card_list,
        graph=graph,
        page_plans=page_plans,
        quality=quality,
        review_queue=review_queue,
    )


def generate_adp1_tracer_artifacts(
    output_dir: str | Path,
    *,
    fixture_path: str | Path = ADP1_TRACER_FIXTURE,
    source_root: str | Path = ADP1_SOURCE_ROOT,
    authored_pages_dir: str | Path | None = None,
) -> TracerArtifacts:
    """Build all deterministic artifacts for the committed ADP1 tracer fixture."""
    return generate_tracer_artifacts(
        load_statement_cards(fixture_path),
        output_dir,
        source_root=source_root,
        authored_pages_dir=authored_pages_dir,
    )


def _write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
