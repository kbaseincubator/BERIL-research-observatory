"""CLI smoke tests for deterministic synthesis-wiki commands."""

from __future__ import annotations

from pathlib import Path

import yaml

from compendium.cli import main

from .test_validate import _statement_card_dict

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "compendium" / "fixtures" / "proj_demo"


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
