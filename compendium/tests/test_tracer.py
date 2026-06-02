"""End-to-end tracer artifact generation tests."""

from __future__ import annotations

from pathlib import Path

from compendium.models import TIER_RETRACTED
from compendium.tracer import generate_adp1_tracer_artifacts


def test_adp1_tracer_generation_writes_expected_artifacts(tmp_path: Path) -> None:
    artifacts = generate_adp1_tracer_artifacts(tmp_path / "out")

    assert artifacts.graph_json.is_file()
    assert artifacts.nodes_tsv.is_file()
    assert artifacts.edges_tsv.is_file()
    assert artifacts.page_plan_json.is_file()
    assert artifacts.quality_json.is_file()
    assert artifacts.quality_dashboard_json.is_file()
    assert artifacts.quality_dashboard_html.is_file()
    assert artifacts.review_queue_json.is_file()
    assert artifacts.markdown_wiki_dir.is_dir()

    assert (artifacts.page_artifact_dir / "home.md").is_file()
    assert (artifacts.page_artifact_dir / "topics" / "adp1-carbon-fitness.md").is_file()
    assert (artifacts.page_artifact_dir / "entities" / "adp1.md").is_file()
    assert len(artifacts.page_markdown_paths) == len(artifacts.page_plans)
    assert len(artifacts.page_manifest_paths) == len(artifacts.page_plans)

    assert (artifacts.site_dir / "index.html").is_file()
    assert (artifacts.site_dir / "topic_adp1-carbon-fitness.html").is_file()
    assert (artifacts.site_dir / "entity_adp1.html").is_file()
    assert (artifacts.site_dir / "graph.html").is_file()
    assert (artifacts.markdown_wiki_dir / "index.md").is_file()
    assert (artifacts.markdown_wiki_dir / "topics" / "adp1-carbon-fitness.md").is_file()
    assert (artifacts.markdown_wiki_dir / "entities" / "adp1.md").is_file()
    assert (artifacts.markdown_wiki_dir / "graph.md").is_file()

    plan_ids = {plan.id for plan in artifacts.page_plans}
    assert "home" in plan_ids
    assert "topic:adp1-carbon-fitness" in plan_ids
    assert "entity:adp1" in plan_ids
    assert sum(plan.type == "claim" for plan in artifacts.page_plans) >= 2
    assert sum(plan.type == "opportunity" for plan in artifacts.page_plans) >= 1

    entity_html = (artifacts.site_dir / "entity_adp1.html").read_text(encoding="utf-8")
    assert "project_adp1_deletion_phenotypes.html" in entity_html
    assert "project_adp1_triple_essentiality.html" in entity_html
    assert "project:adp1_deletion_phenotypes" in entity_html
    assert "project:adp1_triple_essentiality" in entity_html

    home_markdown = (artifacts.markdown_wiki_dir / "index.md").read_text(encoding="utf-8")
    topic_markdown = (
        artifacts.markdown_wiki_dir / "topics" / "adp1-carbon-fitness.md"
    ).read_text(encoding="utf-8")
    entity_markdown = (artifacts.markdown_wiki_dir / "entities" / "adp1.md").read_text(
        encoding="utf-8"
    )
    assert "[Adp1 Carbon Fitness](topics/adp1-carbon-fitness.md)" in home_markdown
    assert "[Graph](graph.md)" in home_markdown
    assert "[Adp1](../entities/adp1.md)" in topic_markdown
    assert "[Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)" in entity_markdown

    quality = artifacts.quality
    assert quality["graph_integrity"]["dangling_edges"] == 0
    assert quality["link_integrity"]["broken_outgoing_link_count"] == 0
    assert quality["link_integrity"]["broken_backlink_count"] == 0
    assert quality["link_integrity"]["backlink_mismatch_count"] == 0
    assert quality["statement_link_integrity"]["unresolved_statement_link_count"] == 0
    assert quality["page_integrity"]["unknown_page_members"] == []
    assert quality["page_integrity"]["unknown_section_members"] == []
    assert quality["opportunity_targets"]["missing_target_output_statement_ids"] == []

    published_statement_ids = {
        statement_id
        for plan in artifacts.page_plans
        for statement_id in plan.member_statement_ids
    }
    active_cards = [card for card in artifacts.cards if card.tier != TIER_RETRACTED]
    assert published_statement_ids == {card.id for card in active_cards}
    assert all(card.evidence.exact for card in active_cards)
    assert quality["evidence_resolution"]["checked"] is True
    assert quality["evidence_resolution"]["resolved"] == len(active_cards)
    assert quality["evidence_resolution"]["unresolved"] == 0


def test_adp1_tracer_generation_is_byte_deterministic(tmp_path: Path) -> None:
    first = generate_adp1_tracer_artifacts(tmp_path / "first")
    second = generate_adp1_tracer_artifacts(tmp_path / "second")

    assert _file_bytes_by_relative_path(first.output_dir) == _file_bytes_by_relative_path(
        second.output_dir
    )


def _file_bytes_by_relative_path(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
