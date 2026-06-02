"""Tests for deterministic synthesis page artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from compendium.pages import build_page_artifact, page_artifact_path, plan_pages, write_page_artifact

from .test_page_planner import _cards


def test_page_artifact_has_manifest_hashes_and_citations() -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}
    plan = plans["topic:carbon-source-essentiality"]

    artifact = build_page_artifact(
        plan,
        _cards(),
        model="test-model",
        prompt_hash="prompt:test",
        repo_commit="abc123",
        timestamp="2026-06-02T00:00:00Z",
    )

    assert artifact["path"] == "topics/carbon-source-essentiality.md"
    assert "# Topic: Carbon Source Essentiality" in artifact["markdown"]
    assert "## Introduction" in artifact["markdown"]
    assert "## Synthesis" in artifact["markdown"]
    assert "This topic summarizes" in artifact["markdown"]
    assert "[stmt:c1; adp1_deletion_phenotypes]" in artifact["markdown"]
    assert "Kind/tier/confidence: `claim` / `grounded` / `high`" in artifact["markdown"]
    assert artifact["manifest"]["skill"] == "kg-synthesize-page"
    assert artifact["manifest"]["model"] == "test-model"
    assert artifact["manifest"]["prompt_hash"] == "prompt:test"
    assert artifact["manifest"]["page_plan_hash"].startswith("hash:")
    assert artifact["manifest"]["member_hash"] == plan.member_hash
    assert artifact["manifest"]["section_hashes"]["overview"].startswith("hash:")
    assert "stmt:c1" in artifact["manifest"]["cited_statement_ids"]
    assert json.loads(json.dumps(artifact["manifest"], sort_keys=True)) == artifact["manifest"]


def test_page_artifact_paths_are_stable_by_page_type() -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}

    assert page_artifact_path(plans["home"]).as_posix() == "home.md"
    assert page_artifact_path(plans["claim:c1"]).as_posix() == "claims/c1.md"
    assert page_artifact_path(plans["opportunity:o1"]).as_posix() == "opportunities/o1.md"
    assert page_artifact_path(plans["entity:adp1"]).as_posix() == "entities/adp1.md"


def test_write_page_artifact_writes_markdown_and_manifest(tmp_path: Path) -> None:
    plans = {plan.id: plan for plan in plan_pages(_cards())}

    markdown_path, manifest_path = write_page_artifact(
        plans["claim:c1"],
        _cards(),
        tmp_path,
        model="test-model",
        prompt_hash="prompt:test",
    )

    assert markdown_path == tmp_path / "claims" / "c1.md"
    assert manifest_path == tmp_path / "claims" / "c1.manifest.json"
    assert markdown_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["page_id"] == "claim:c1"
    assert manifest["member_hash"] == plans["claim:c1"].member_hash
