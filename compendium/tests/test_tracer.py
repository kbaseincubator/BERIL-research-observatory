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
    assert artifacts.page_context_dir.is_dir()

    assert (artifacts.page_context_dir / "home.context.json").is_file()
    assert (
        artifacts.page_context_dir / "topics" / "adp1-carbon-fitness.context.json"
    ).is_file()
    assert (artifacts.page_context_dir / "entities" / "adp1.context.json").is_file()
    assert len(artifacts.page_context_paths) == len(artifacts.page_plans)
    assert len(artifacts.page_prompt_paths) == len(artifacts.page_plans)

    assert artifacts.markdown_wiki_dir is None
    assert artifacts.markdown_wiki_paths == []

    plan_ids = {plan.id for plan in artifacts.page_plans}
    assert "home" in plan_ids
    assert "topic:adp1-carbon-fitness" in plan_ids
    assert "entity:adp1" in plan_ids
    assert sum(plan.type == "claim" for plan in artifacts.page_plans) >= 2
    assert sum(plan.type == "opportunity" for plan in artifacts.page_plans) >= 1

    topic_context = (
        artifacts.page_context_dir / "topics" / "adp1-carbon-fitness.context.json"
    ).read_text(encoding="utf-8")
    assert "topic:adp1-carbon-fitness" in topic_context
    assert "member_statements" in topic_context
    assert "local_graph" in topic_context

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
