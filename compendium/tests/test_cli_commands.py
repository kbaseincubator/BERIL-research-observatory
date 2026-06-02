"""CLI smoke tests for deterministic synthesis-wiki commands."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from compendium.cli import main

from .test_validate import _statement_card_dict

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "compendium" / "fixtures" / "proj_demo"
STATEMENT_FIXTURE = ROOT / "compendium" / "fixtures" / "statement_cards" / "adp1_tracer.yaml"


def test_context_pack_command_writes_canonical_json(tmp_path: Path) -> None:
    out = tmp_path / "context.json"

    assert main(["context-pack", str(FIXTURE), "--out", str(out)]) == 0

    text = out.read_text(encoding="utf-8")
    assert '"context_pack_hash"' in text
    assert '"proj_demo"' in text


def test_validate_commands_accept_statement_project_and_page_plan(tmp_path: Path) -> None:
    card = _statement_card_dict()
    card_path = tmp_path / "card.yaml"
    project_path = tmp_path / "project.yaml"
    page_path = tmp_path / "page.yaml"
    card_path.write_text(yaml.safe_dump(card, sort_keys=True), encoding="utf-8")
    project_path.write_text(yaml.safe_dump({"statements": [card]}, sort_keys=True), encoding="utf-8")
    page_path.write_text(
        yaml.safe_dump(
            {
                "id": "topic:adp1",
                "type": "topic",
                "title": "ADP1",
                "member_statement_ids": ["stmt:abc123"],
                "sections": [],
                "outgoing_links": [],
                "backlinks": [],
                "member_hash": "hash:page",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    assert main(["validate-card", str(card_path)]) == 0
    assert main(["validate-project-kg", str(project_path)]) == 0
    assert main(["validate-page-plan", str(page_path)]) == 0


def test_cli_validation_errors_return_without_traceback(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.yaml"

    assert main(["statement-graph", str(missing)]) == 2

    captured = capsys.readouterr()
    assert "[compendium] error:" in captured.err
    assert "Traceback" not in captured.err


def test_statement_graph_command_writes_graph_json(tmp_path: Path) -> None:
    out = tmp_path / "statement-graph.json"

    assert main(["statement-graph", str(STATEMENT_FIXTURE), "--out", str(out)]) == 0

    graph = json.loads(out.read_text(encoding="utf-8"))
    assert any(node["id"] == "stmt:adp1-continuum-claim" for node in graph["nodes"])
    assert any(edge["p"] == "has_evidence" for edge in graph["edges"])
    assert any(edge["p"] == "about_entity" for edge in graph["edges"])


def test_plan_pages_command_writes_page_plan_json(tmp_path: Path) -> None:
    out = tmp_path / "pages.json"

    assert main(["plan-pages", str(STATEMENT_FIXTURE), "--out", str(out)]) == 0

    plans = json.loads(out.read_text(encoding="utf-8"))
    plan_ids = {plan["id"] for plan in plans}
    assert "home" in plan_ids
    assert "topic:adp1-carbon-fitness" in plan_ids
    assert "claim:adp1-continuum-claim" in plan_ids
    assert all(plan["member_hash"].startswith("hash:") for plan in plans)


def test_render_synthesis_command_writes_static_site(tmp_path: Path) -> None:
    out_dir = tmp_path / "site"

    assert main(["render-synthesis", str(STATEMENT_FIXTURE), "--out", str(out_dir)]) == 0

    assert (out_dir / "index.html").is_file()
    claim_page = out_dir / "claim_adp1-continuum-claim.html"
    assert claim_page.is_file()
    assert "ADP1 condition-dependent essentiality" in claim_page.read_text(encoding="utf-8")


def test_quality_synthesis_command_writes_metrics_json(tmp_path: Path) -> None:
    out = tmp_path / "quality.json"

    assert main(
        [
            "quality-synthesis",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(ROOT / "projects"),
            "--out",
            str(out),
        ]
    ) == 0

    metrics = json.loads(out.read_text(encoding="utf-8"))
    assert metrics["statement_counts"]["total"] == 6
    assert metrics["evidence_resolution"]["resolved"] == 6
    assert metrics["graph_integrity"]["dangling_edges"] == 0
    assert metrics["link_integrity"]["broken_outgoing_link_count"] == 0
    assert metrics["statement_link_integrity"]["unresolved_statement_link_count"] == 0
    assert metrics["opportunity_targets"]["missing_target_output_statement_ids"] == []


def test_quality_synthesis_command_fails_quality_gate_but_writes_metrics(tmp_path: Path) -> None:
    project_path = tmp_path / "project.yaml"
    out = tmp_path / "quality.json"
    project_path.write_text(
        yaml.safe_dump({"statements": [_statement_card_dict()]}, sort_keys=True),
        encoding="utf-8",
    )

    assert main(
        [
            "quality-synthesis",
            str(project_path),
            "--source-root",
            str(tmp_path / "empty-source-root"),
            "--out",
            str(out),
        ]
    ) == 1

    metrics = json.loads(out.read_text(encoding="utf-8"))
    assert metrics["evidence_resolution"]["unresolved"] == 1
