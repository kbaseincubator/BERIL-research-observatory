"""Tests for deterministic synthesis page artifacts (topic/data/author/home model)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from compendium.pages import (
    build_page_context,
    page_artifact_path,
    wiki_page_path,
    write_page_artifact,
    write_page_context,
)
from compendium.render.markdown import render_markdown_wiki

from .test_page_planner import _cards, _plans


def test_page_context_contains_bounded_llm_inputs() -> None:
    plans = _plans()
    plan = plans["topic:metal-resistance"]

    context = build_page_context(plan, _cards(), page_plans=list(plans.values()))

    assert context["page"]["id"] == "topic:metal-resistance"
    assert context["page"]["wiki_path"] == "topics/metal-resistance.md"
    assert (
        context["page"]["manifest_path"]
        == ".manifests/topics/metal-resistance.manifest.json"
    )
    assert context["statements"][0]["id"].startswith("stmt:")
    assert context["projects"]
    assert context["topics"]
    assert context["entities"]
    assert context["adjacent_pages"]
    assert context["allowed_citations"]
    assert context["narrative"]["lead"]
    assert [section["heading"] for section in context["narrative"]["section_plan"]][:2] == [
        "Overview",
        "What the Corpus Shows",
    ]
    assert "statement-by-statement" in context["instructions"]["body_rule"]


def test_page_artifact_paths_are_stable_by_page_type() -> None:
    plans = _plans()

    assert page_artifact_path(plans["home"]).as_posix() == "home.md"
    assert wiki_page_path(plans["home"]).as_posix() == "index.md"
    assert (
        page_artifact_path(plans["topic:metal-resistance"]).as_posix()
        == "topics/metal-resistance.md"
    )
    assert (
        page_artifact_path(plans["data:kbase_ke_pangenome"]).as_posix()
        == "data/kbase-ke-pangenome.md"
    )
    assert (
        page_artifact_path(plans["author:0000-0001-5810-2497"]).as_posix()
        == "authors/0000-0001-5810-2497.md"
    )


def test_write_page_context_writes_json_and_prompt(tmp_path: Path) -> None:
    plans = _plans()
    context_path, prompt_path = write_page_context(
        plans["topic:metal-resistance"],
        _cards(),
        tmp_path,
        page_plans=list(plans.values()),
    )

    assert context_path == tmp_path / "topics" / "metal-resistance.context.json"
    assert prompt_path == tmp_path / "topics" / "metal-resistance.prompt.md"
    assert context_path.is_file()
    assert "only allowed scientific context" in prompt_path.read_text(encoding="utf-8")


def test_write_page_artifact_requires_authored_markdown_and_writes_manifest(
    tmp_path: Path,
) -> None:
    plans = _plans()
    markdown = (
        "# Topic: Metal Resistance\n\n"
        "## Overview\n\n"
        "Metal resistance is largely shared across the tested strains "
        "[stmt:m2; metal_fitness_atlas].\n"
    )

    markdown_path, manifest_path = write_page_artifact(
        plans["topic:metal-resistance"],
        _cards(),
        tmp_path,
        model="test-model",
        prompt_hash="prompt:test",
        markdown=markdown,
    )

    assert markdown_path == tmp_path / "topics" / "metal-resistance.md"
    assert manifest_path == tmp_path / ".manifests" / "topics" / "metal-resistance.manifest.json"
    assert markdown_path.is_file()

    # The inline token is rewritten to a numbered marker + appended References list.
    published = markdown_path.read_text(encoding="utf-8")
    assert "[stmt:m2;" not in published
    assert "## References" in published
    assert "1. [Metal Fitness Atlas](../projects/metal-fitness-atlas.md)" in published

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["page_id"] == "topic:metal-resistance"
    assert manifest["page_type"] == "topic"
    assert manifest["member_hash"] == plans["topic:metal-resistance"].member_hash
    assert manifest["cited_statement_ids"] == ["stmt:m2"]


def test_write_page_artifact_rejects_nonmember_citations(tmp_path: Path) -> None:
    plans = _plans()

    with pytest.raises(ValueError, match="outside page membership"):
        write_page_artifact(
            plans["topic:metal-resistance"],
            _cards(),
            tmp_path,
            model="test-model",
            prompt_hash="prompt:test",
            markdown="# Topic\n\nUnsupported citation [stmt:bogus; metal_fitness_atlas].",
        )


def _author_one_member(plan, cards) -> str:
    """Return the markdown body for a page, citing one member statement when it has any."""
    card_by_id = {card.id: card for card in cards}
    members = [sid for sid in plan.member_statement_ids if sid in card_by_id]
    body = [f"# {plan.title}", "", "## Overview", ""]
    if members:
        cited = card_by_id[members[0]]
        body.append(
            f"This page cites project evidence "
            f"[{cited.id}; {cited.evidence[0].source_project}]."
        )
    else:
        body.append("This page has no member statements.")
    body.append("")
    return "\n".join(body)


def test_end_to_end_plan_author_and_render_validates_clean(tmp_path: Path) -> None:
    cards = _cards()
    page_plans = list(_plans().values())
    out_dir = tmp_path / "wiki"

    for plan in page_plans:
        write_page_artifact(
            plan,
            cards,
            out_dir,
            model="test-model",
            prompt_hash="prompt:test",
            markdown=_author_one_member(plan, cards),
        )

    rendered = render_markdown_wiki(page_plans, out_dir)

    # Every planned page renders; no graph.md is emitted.
    assert (out_dir / "index.md").is_file()
    assert (out_dir / "topics" / "metal-resistance.md").is_file()
    assert (out_dir / "data" / "kbase-ke-pangenome.md").is_file()
    assert (out_dir / "authors" / "0000-0001-5810-2497.md").is_file()
    assert not (out_dir / "graph.md").exists()
    assert len(rendered) == len(page_plans)
