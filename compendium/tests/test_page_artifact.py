"""Tests for deterministic synthesis page artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from compendium.pages import (
    build_page_context,
    page_artifact_path,
    plan_pages,
    write_page_artifact,
    write_page_context,
)

from .test_page_planner import _cards


def test_page_context_contains_bounded_llm_inputs() -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}
    plan = plans["topic:carbon-source-essentiality"]

    context = build_page_context(
        plan,
        _cards(),
        page_plans=list(plans.values()),
    )

    assert context["page"]["id"] == "topic:carbon-source-essentiality"
    assert context["page"]["artifact_path"] == "topics/carbon-source-essentiality.md"
    assert context["page"]["wiki_path"] == "topics/carbon-source-essentiality.md"
    assert context["member_statements"][0]["id"].startswith("stmt:")
    assert context["sections"][0]["statements"]
    assert "outgoing" in context["link_map"]
    assert "Write the full page body" in context["instructions"]["prose"]


def test_page_artifact_paths_are_stable_by_page_type() -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}

    assert page_artifact_path(plans["home"]).as_posix() == "home.md"
    assert page_artifact_path(plans["claim:c1"]).as_posix() == "claims/c1.md"
    assert page_artifact_path(plans["opportunity:o1"]).as_posix() == "opportunities/o1.md"
    assert page_artifact_path(plans["entity:adp1"]).as_posix() == "entities/adp1.md"


def test_write_page_context_writes_json_and_prompt(tmp_path: Path) -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}
    context_path, prompt_path = write_page_context(
        plans["topic:carbon-source-essentiality"],
        _cards(),
        tmp_path,
        page_plans=list(plans.values()),
    )

    assert context_path == tmp_path / "topics" / "carbon-source-essentiality.context.json"
    assert prompt_path == tmp_path / "topics" / "carbon-source-essentiality.prompt.md"
    assert context_path.is_file()
    assert "only allowed scientific context" in prompt_path.read_text(encoding="utf-8")


def test_write_page_artifact_requires_authored_markdown_and_writes_manifest(
    tmp_path: Path,
) -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}
    markdown = (
        "# Claim: C1\n\n"
        "## Introduction\n\n"
        "ADP1 has a reusable carbon-source essentiality landscape "
        "[stmt:c1; adp1_deletion_phenotypes].\n"
    )

    markdown_path, manifest_path = write_page_artifact(
        plans["claim:c1"],
        _cards(),
        tmp_path,
        model="test-model",
        prompt_hash="prompt:test",
        markdown=markdown,
    )

    assert markdown_path == tmp_path / "claims" / "c1.md"
    assert manifest_path == tmp_path / "claims" / "c1.manifest.json"
    assert markdown_path.is_file()
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["page_id"] == "claim:c1"
    assert manifest["member_hash"] == plans["claim:c1"].member_hash
    assert manifest["cited_statement_ids"] == ["stmt:c1"]


def test_write_page_artifact_rejects_nonmember_citations(tmp_path: Path) -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}

    with pytest.raises(ValueError, match="outside page membership"):
        write_page_artifact(
            plans["claim:c1"],
            _cards(),
            tmp_path,
            model="test-model",
            prompt_hash="prompt:test",
            markdown="# Claim\n\nUnsupported citation [stmt:bogus; adp1_deletion_phenotypes].",
        )
