"""Regression tests for the three-project statement-card ingestion tracer."""

from __future__ import annotations

from pathlib import Path

from compendium.build.statement_graph import build_statement_graph
from compendium.pages.plan import plan_pages
from compendium.quality.synthesis_quality import assess_synthesis_quality
from compendium.tracer import generate_tracer_artifacts, load_statement_cards

ROOT = Path(__file__).resolve().parents[2]
INGESTED_TRACER = (
    ROOT / "compendium" / "fixtures" / "statement_cards" / "adp1_three_project_ingestion.yaml"
)
SOURCE_ROOT = ROOT / "projects"


def test_three_project_ingestion_fixture_meets_quality_bar(tmp_path: Path) -> None:
    cards = load_statement_cards(INGESTED_TRACER)

    assert len(cards) == 19
    assert {card.evidence.source_project for card in cards} == {
        "acinetobacter_adp1_explorer",
        "adp1_deletion_phenotypes",
        "adp1_triple_essentiality",
    }

    graph = build_statement_graph(cards)
    plans = plan_pages(cards)
    metrics = assess_synthesis_quality(cards, graph, plans, source_root=SOURCE_ROOT)

    assert metrics["evidence_resolution"]["rate"] == 1.0
    assert metrics["topic_coverage"]["coverage_rate"] == 1.0
    assert metrics["claim_balance"]["unsupported_claim_statement_ids"] == []
    assert metrics["opportunity_targets"]["missing_target_output_statement_ids"] == []
    assert metrics["graph_integrity"]["dangling_edges"] == 0
    assert metrics["link_integrity"]["broken_outgoing_link_count"] == 0
    assert metrics["link_integrity"]["broken_backlink_count"] == 0
    assert metrics["link_integrity"]["backlink_mismatch_count"] == 0
    assert metrics["statement_link_integrity"]["unresolved_statement_link_count"] == 0

    artifacts = generate_tracer_artifacts(cards, tmp_path / "wiki", source_root=SOURCE_ROOT)

    assert (artifacts.site_dir / "index.html").is_file()
    assert (artifacts.site_dir / "topics" / "adp1-carbon-fitness.html").is_file()
    assert (artifacts.site_dir / "topics" / "adp1-data-integration.html").is_file()
    assert (artifacts.site_dir / "topics" / "adp1-model-quality.html").is_file()
    assert (artifacts.site_dir / "entities" / "adp1.html").is_file()
    assert (artifacts.site_dir / "graph.html").is_file()
    assert (artifacts.markdown_wiki_dir / "index.md").is_file()
    assert (artifacts.markdown_wiki_dir / "topics" / "adp1-carbon-fitness.md").is_file()
    assert (artifacts.markdown_wiki_dir / "topics" / "adp1-data-integration.md").is_file()
    assert (artifacts.markdown_wiki_dir / "topics" / "adp1-model-quality.md").is_file()
    assert (artifacts.markdown_wiki_dir / "entities" / "adp1.md").is_file()
    assert (artifacts.markdown_wiki_dir / "graph.md").is_file()
    assert sum(plan.type == "project" for plan in artifacts.page_plans) == 3
    assert sum(plan.type == "claim" for plan in artifacts.page_plans) == 3
    assert sum(plan.type == "opportunity" for plan in artifacts.page_plans) == 4
