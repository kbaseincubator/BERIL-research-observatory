"""CLI smoke tests for deterministic synthesis-wiki commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import compendium.pipeline as _pipeline
from compendium.cli import main
from compendium.models import StatementCard
from compendium.pages import plan_pages, write_page_artifact
from compendium.validate import validate_project_kg_file

from .test_validate import _statement_card_dict

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "compendium" / "fixtures" / "proj_demo"
STATEMENT_FIXTURE = ROOT / "compendium" / "fixtures" / "statement_cards" / "adp1_tracer.yaml"


@pytest.fixture(autouse=True)
def _isolate_registry(monkeypatch, tmp_path_factory):
    """Isolate CLI tests from a committed ``registry.yaml``.

    These tests assert identity (raw-slug) page ids; registry canonicalization is covered by
    ``test_page_planner`` with an explicit ``Registry``. Point ``REGISTRY_PATH`` at a missing file
    so ``plan_pages`` uses identity resolution regardless of the repo's registry.
    """
    monkeypatch.setattr(
        _pipeline, "REGISTRY_PATH", tmp_path_factory.mktemp("noreg") / "registry.yaml"
    )


def test_context_pack_command_writes_canonical_json(tmp_path: Path) -> None:
    out = tmp_path / "context.json"

    assert main(["context-pack", str(FIXTURE), "--out", str(out)]) == 0

    text = out.read_text(encoding="utf-8")
    assert '"context_pack_hash"' in text
    assert '"proj_demo"' in text


def test_validate_commands_accept_statement_card_and_page_plan(tmp_path: Path) -> None:
    card = _statement_card_dict()
    card_path = tmp_path / "card.yaml"
    page_path = tmp_path / "page.yaml"
    card_path.write_text(yaml.safe_dump(card, sort_keys=True), encoding="utf-8")
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
    assert main(["validate-kg", str(STATEMENT_FIXTURE)]) == 0
    assert main(["validate-page-plan", str(page_path)]) == 0


def test_cli_validation_errors_return_without_traceback(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.yaml"

    assert main(["plan-pages", str(missing)]) == 2

    captured = capsys.readouterr()
    assert "[compendium] error:" in captured.err
    assert "Traceback" not in captured.err

def test_plan_pages_command_writes_page_plan_json(tmp_path: Path) -> None:
    out = tmp_path / "pages.json"
    empty_root = tmp_path / "no-projects"
    empty_root.mkdir()

    assert main(
        ["plan-pages", str(STATEMENT_FIXTURE), "--source-root", str(empty_root), "--out", str(out)]
    ) == 0

    plans = json.loads(out.read_text(encoding="utf-8"))
    plan_ids = {plan["id"] for plan in plans}
    plan_types = {plan["type"] for plan in plans}
    assert "home" in plan_ids
    assert "topic:adp1-carbon-fitness" in plan_ids
    # Claims/entities are sections, not standalone pages; project pages now exist.
    assert "claim:adp1-continuum-claim" not in plan_ids
    assert plan_types <= {"home", "topic", "data", "author", "project"}
    assert any(pid.startswith("project:") for pid in plan_ids)
    assert all(plan["member_hash"].startswith("hash:") for plan in plans)


def test_page_context_command_writes_context_and_prompt(tmp_path: Path) -> None:
    out_dir = tmp_path / "contexts"

    assert main(
        [
            "page-context",
            str(STATEMENT_FIXTURE),
            "--page-id",
            "topic:adp1-carbon-fitness",
            "--source-root",
            str(ROOT / "projects"),
            "--out",
            str(out_dir),
        ]
    ) == 0

    context = out_dir / "topics" / "adp1-carbon-fitness.context.json"
    prompt = out_dir / "topics" / "adp1-carbon-fitness.prompt.md"
    assert context.is_file()
    assert prompt.is_file()
    context_payload = json.loads(context.read_text(encoding="utf-8"))
    assert context_payload["page"]["id"] == "topic:adp1-carbon-fitness"
    assert context_payload["statements"]
    assert context_payload["narrative"]["lead"]
    assert "only allowed scientific context" in prompt.read_text(encoding="utf-8")


def test_wiki_contexts_command_removes_stale_context_artifacts(tmp_path: Path) -> None:
    out_dir = tmp_path / "contexts"
    stale_context = out_dir / "claims" / "stale.context.json"
    stale_prompt = out_dir / "claims" / "stale.prompt.md"
    stale_context.parent.mkdir(parents=True)
    stale_context.write_text("{}", encoding="utf-8")
    stale_prompt.write_text("# stale\n", encoding="utf-8")

    assert main(
        [
            "wiki-contexts",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(ROOT / "projects"),
            "--out",
            str(out_dir),
        ]
    ) == 0

    assert not stale_context.exists()
    assert not stale_prompt.exists()
    assert (out_dir / "home.context.json").is_file()
    assert (out_dir / "home.prompt.md").is_file()


def test_page_artifact_command_validates_authored_markdown(tmp_path: Path) -> None:
    draft = tmp_path / "draft.md"
    out_dir = tmp_path / "wiki"
    draft.write_text(
        "# Topic: ADP1 Carbon Fitness\n\n"
        "ADP1 essentiality should be read through cited project evidence "
        "[stmt:adp1-continuum-claim; adp1_deletion_phenotypes].\n",
        encoding="utf-8",
    )

    assert main(
        [
            "page-artifact",
            str(STATEMENT_FIXTURE),
            "--page-id",
            "topic:adp1-carbon-fitness",
            "--markdown",
            str(draft),
            "--out",
            str(out_dir),
            "--model",
            "test-model",
            "--prompt-hash",
            "prompt:test",
        ]
    ) == 0

    page = out_dir / "topics" / "adp1-carbon-fitness.md"
    manifest = out_dir / ".manifests" / "topics" / "adp1-carbon-fitness.manifest.json"
    assert page.is_file()
    assert manifest.is_file()
    assert json.loads(manifest.read_text(encoding="utf-8"))["cited_statement_ids"] == [
        "stmt:adp1-continuum-claim"
    ]


def test_render_markdown_command_writes_linked_markdown_wiki(tmp_path: Path) -> None:
    out_dir = tmp_path / "wiki"
    empty_root = tmp_path / "no-projects"
    empty_root.mkdir()
    _write_authored_pages(STATEMENT_FIXTURE, out_dir, source_root=empty_root)

    assert main(
        [
            "render-markdown",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(empty_root),
            "--out",
            str(out_dir),
        ]
    ) == 0

    home = out_dir / "index.md"
    topic = out_dir / "topics" / "adp1-carbon-fitness.md"
    assert home.is_file()
    assert topic.is_file()
    # graph.md is no longer a reader page.
    assert not (out_dir / "graph.md").exists()
    assert "# State Of The Science" in home.read_text(encoding="utf-8")
    assert "# Topic: Adp1 Carbon Fitness" in topic.read_text(encoding="utf-8")


def test_render_markdown_command_rejects_stale_wiki_pages_and_manifests(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "wiki"
    empty_root = tmp_path / "no-projects"
    empty_root.mkdir()
    _write_authored_pages(STATEMENT_FIXTURE, out_dir, source_root=empty_root)
    stale_page = out_dir / "topics" / "stale.md"
    stale_manifest = out_dir / ".manifests" / "topics" / "stale.manifest.json"
    stale_page.write_text("# Stale\n\nOld generated page.\n", encoding="utf-8")
    stale_manifest.write_text('{"page_id":"topic:stale"}\n', encoding="utf-8")

    assert main(
        [
            "render-markdown",
            str(STATEMENT_FIXTURE),
            "--source-root",
            str(empty_root),
            "--out",
            str(out_dir),
        ]
    ) == 2

    captured = capsys.readouterr()
    assert "stale wiki markdown pages" in captured.err
    assert "topics/stale.md" in captured.err


def test_check_command_exits_zero_on_clean_and_nonzero_on_broken_wiki(tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    (clean / "topics").mkdir(parents=True)
    (clean / "index.md").write_text("# Home\n\n[x](topics/x.md)\n", encoding="utf-8")
    (clean / "topics" / "x.md").write_text("# X\n\nBody.\n", encoding="utf-8")

    assert main(["check", "--wiki", str(clean)]) == 0

    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "index.md").write_text("# Home\n\n[gone](topics/gone.md)\n", encoding="utf-8")

    assert main(["check", "--wiki", str(broken)]) == 1


def _write_authored_pages(
    statement_fixture: Path, pages_dir: Path, *, source_root: Path | None = None
) -> None:
    from compendium.pipeline import _build_plan_inputs

    result = validate_project_kg_file(statement_fixture)
    cards = [record for record in result.records if isinstance(record, StatementCard)]
    card_by_id = {card.id: card for card in cards}
    plan_inputs = _build_plan_inputs(str(source_root) if source_root else None)
    for plan in plan_pages(cards, **plan_inputs):
        cited_card = card_by_id[plan.member_statement_ids[0]]
        write_page_artifact(
            plan,
            cards,
            pages_dir,
            model="test-model",
            prompt_hash="prompt:test",
            markdown="\n".join(
                (
                    f"# {plan.title}",
                    "",
                    "## Introduction",
                    "",
                    f"This authored test page cites {cited_card.id} "
                    f"[{cited_card.id}; {cited_card.evidence[0].source_project}].",
                    "",
                )
            ),
        )
