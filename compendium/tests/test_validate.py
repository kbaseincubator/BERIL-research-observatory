"""Tests for file-level synthesis-wiki validators."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from compendium.validate import (
    validate_page_plan_file,
    validate_project_kg_file,
    validate_statement_card_file,
)


def _statement_card_dict(card_id: str = "stmt:abc123") -> dict:
    return {
        "id": card_id,
        "kind": "finding",
        "statement": "Carbon sources define a three-tier essentiality landscape in ADP1.",
        "scope": "project_local",
        "tier": "asserted",
        "confidence": "medium",
        "about": {
            "entities": ["entity:adp1"],
            "topics": ["topic:carbon-source-essentiality"],
        },
        "links": {
            "supports": [],
            "contradicts": [],
            "motivates": [],
            "refines": [],
            "requires_validation": [],
        },
        "qualifiers": {
            "organism": "entity:adp1",
            "method": "RB-TnSeq",
        },
        "evidence": {
            "source_project": "adp1_deletion_phenotypes",
            "source_doc": "REPORT.md",
            "source_section": "Key Findings",
            "exact": "Carbon sources define a three-tier essentiality landscape",
            "prefix": "The deletion screen showed that ",
            "suffix": " across tested conditions.",
        },
        "extraction": {
            "agent_type": "llm_extractor",
            "skill": "kg-ingest-project",
            "model": "test-model",
            "prompt_hash": "prompt:abc",
            "context_pack_hash": "context:def",
            "repo_commit": "abc123",
            "timestamp": "2026-06-02T00:00:00Z",
        },
    }


def _write_yaml(path: Path, data: object) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    return path


def test_validate_statement_card_file_accepts_valid_card(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path / "card.yaml", _statement_card_dict())

    result = validate_statement_card_file(path)

    assert result.artifact_type == "statement_card"
    assert result.count == 1
    assert result.ids == ["stmt:abc123"]
    assert result.records[0].id == "stmt:abc123"
    assert result.records[0].evidence.exact == (
        "Carbon sources define a three-tier essentiality landscape"
    )


def test_validate_statement_card_file_rejects_missing_evidence(tmp_path: Path) -> None:
    card = _statement_card_dict()
    del card["evidence"]
    path = _write_yaml(tmp_path / "card.yaml", card)

    with pytest.raises(ValueError, match="missing required field 'evidence'"):
        validate_statement_card_file(path)


def test_validate_page_plan_file_rejects_invalid_page_type(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path / "page_plan.yaml",
        {
            "id": "topic:adp1",
            "type": "not_a_page_type",
            "title": "ADP1",
            "member_statement_ids": ["stmt:abc123"],
            "sections": [],
            "outgoing_links": [],
            "backlinks": [],
            "member_hash": "hash:page",
        },
    )

    with pytest.raises(ValueError, match="type must be one of"):
        validate_page_plan_file(path)


def test_validate_project_kg_file_accepts_statement_list(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path / "project.yaml",
        [_statement_card_dict("stmt:abc123"), _statement_card_dict("stmt:def456")],
    )

    result = validate_project_kg_file(path)

    assert result.artifact_type == "project_kg"
    assert result.count == 2
    assert result.ids == ["stmt:abc123", "stmt:def456"]


def test_validate_project_kg_file_accepts_statement_dict_shape(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path / "project.yaml",
        {"project": {"id": "adp1_deletion_phenotypes"}, "statements": [_statement_card_dict()]},
    )

    result = validate_project_kg_file(path)

    assert result.artifact_type == "project_kg"
    assert result.count == 1
    assert result.ids == ["stmt:abc123"]
