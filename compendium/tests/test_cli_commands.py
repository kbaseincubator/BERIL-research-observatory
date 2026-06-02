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
    artifacts_dir = tmp_path / "graph-artifacts"

    assert main(
        [
            "statement-graph",
            str(STATEMENT_FIXTURE),
            "--out",
            str(out),
            "--artifacts-dir",
            str(artifacts_dir),
        ]
    ) == 0

    graph = json.loads(out.read_text(encoding="utf-8"))
    assert any(node["id"] == "stmt:adp1-continuum-claim" for node in graph["nodes"])
    assert any(edge["p"] == "has_evidence" for edge in graph["edges"])
    assert any(edge["p"] == "about_entity" for edge in graph["edges"])
    assert (artifacts_dir / "graph.json").is_file()
    assert (artifacts_dir / "nodes.tsv").is_file()
    assert (artifacts_dir / "edges.tsv").is_file()


def test_plan_pages_command_writes_page_plan_json(tmp_path: Path) -> None:
    out = tmp_path / "pages.json"

    assert main(["plan-pages", str(STATEMENT_FIXTURE), "--out", str(out)]) == 0

    plans = json.loads(out.read_text(encoding="utf-8"))
    plan_ids = {plan["id"] for plan in plans}
    assert "home" in plan_ids
    assert "topic:adp1-carbon-fitness" in plan_ids
    assert "claim:adp1-continuum-claim" in plan_ids
    assert all(plan["member_hash"].startswith("hash:") for plan in plans)


def test_synthesize_page_command_writes_markdown_and_manifest(tmp_path: Path) -> None:
    out_dir = tmp_path / "pages"

    assert main(
        [
            "synthesize-page",
            str(STATEMENT_FIXTURE),
            "--page-id",
            "topic:adp1-carbon-fitness",
            "--out",
            str(out_dir),
            "--model",
            "test-model",
            "--prompt-hash",
            "prompt:test",
        ]
    ) == 0

    markdown = out_dir / "topics" / "adp1-carbon-fitness.md"
    manifest = out_dir / "topics" / "adp1-carbon-fitness.manifest.json"
    assert markdown.is_file()
    assert manifest.is_file()
    assert "[stmt:adp1-continuum-claim; adp1_deletion_phenotypes]" in markdown.read_text(
        encoding="utf-8"
    )
    assert json.loads(manifest.read_text(encoding="utf-8"))["model"] == "test-model"


def test_render_synthesis_command_writes_static_site(tmp_path: Path) -> None:
    out_dir = tmp_path / "site"

    assert main(["render-synthesis", str(STATEMENT_FIXTURE), "--out", str(out_dir)]) == 0

    assert (out_dir / "index.html").is_file()
    assert (out_dir / "graph.html").is_file()
    claim_page = out_dir / "claim_adp1-continuum-claim.html"
    assert claim_page.is_file()
    assert "ADP1 condition-dependent essentiality" in claim_page.read_text(encoding="utf-8")


def test_quality_synthesis_command_writes_metrics_json(tmp_path: Path) -> None:
    out = tmp_path / "quality.json"
    dashboard = tmp_path / "quality.html"

    assert main(
        [
            "quality-synthesis",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(ROOT / "projects"),
            "--out",
            str(out),
            "--dashboard-out",
            str(dashboard),
        ]
    ) == 0

    metrics = json.loads(out.read_text(encoding="utf-8"))
    assert metrics["statement_counts"]["total"] == 6
    assert metrics["evidence_resolution"]["resolved"] == 6
    assert metrics["graph_integrity"]["dangling_edges"] == 0
    assert metrics["link_integrity"]["broken_outgoing_link_count"] == 0
    assert metrics["statement_link_integrity"]["unresolved_statement_link_count"] == 0
    assert metrics["opportunity_targets"]["missing_target_output_statement_ids"] == []
    assert "Synthesis Quality Dashboard" in dashboard.read_text(encoding="utf-8")


def test_quality_command_writes_statement_quality_bundle(tmp_path: Path) -> None:
    out_dir = tmp_path / "quality"

    assert main(
        [
            "quality",
            "--statement-kg",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(ROOT / "projects"),
            "--out",
            str(out_dir),
        ]
    ) == 0

    metrics = json.loads((out_dir / "quality.json").read_text(encoding="utf-8"))
    dashboard = json.loads(
        (out_dir / "quality-dashboard.json").read_text(encoding="utf-8")
    )
    queue = json.loads((out_dir / "review-queue.json").read_text(encoding="utf-8"))
    assert metrics["evidence_resolution"]["resolved"] == 6
    assert dashboard["summary"]["statement_total"] == 6
    assert isinstance(queue, list)
    assert "Synthesis Quality Dashboard" in (
        out_dir / "quality-dashboard.html"
    ).read_text(encoding="utf-8")


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


def test_review_queue_command_writes_ranked_json(tmp_path: Path) -> None:
    out = tmp_path / "review-queue.json"

    assert main(
        [
            "review-queue",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(ROOT / "projects"),
            "--limit",
            "2",
            "--out",
            str(out),
        ]
    ) == 0

    queue = json.loads(out.read_text(encoding="utf-8"))
    assert len(queue) <= 2
    assert all("statement_id" in item for item in queue)
    assert all("reasons" in item for item in queue)


def test_tracer_command_writes_full_adp1_artifact_bundle(tmp_path: Path) -> None:
    out_dir = tmp_path / "tracer"

    assert main(["tracer", "--out", str(out_dir)]) == 0

    assert (out_dir / "graph" / "graph.json").is_file()
    assert (out_dir / "page-plans.json").is_file()
    assert (out_dir / "page-artifacts" / "home.md").is_file()
    assert (out_dir / "site" / "index.html").is_file()
    assert (out_dir / "site" / "entity_adp1.html").is_file()
    assert (out_dir / "site" / "graph.html").is_file()
    assert (out_dir / "quality.json").is_file()
    assert (out_dir / "quality-dashboard.html").is_file()
    assert (out_dir / "review-queue.json").is_file()
