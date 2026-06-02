"""Tests for deterministic context pack construction."""

from __future__ import annotations

from pathlib import Path

from compendium.context_pack import build_context_pack, context_pack_bytes

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "compendium" / "fixtures" / "proj_demo"
ADP1 = ROOT / "projects" / "adp1_deletion_phenotypes"


def test_context_pack_bytes_are_deterministic() -> None:
    first = build_context_pack(FIXTURE)
    second = build_context_pack(FIXTURE)

    assert first == second
    assert context_pack_bytes(first) == context_pack_bytes(second)
    assert first["context_pack_hash"].startswith("sha256:")


def test_basic_fixture_context_pack_contains_required_scaffold() -> None:
    pack = build_context_pack(FIXTURE)

    assert pack["project"]["id"] == "proj_demo"
    assert pack["project"]["title"] == "Acinetobacter baylyi ADP1 Demo Study"
    assert {source["path"] for source in pack["source_files"]} == {"REPORT.md", "README.md"}
    assert all(source["sha256"].startswith("sha256:") for source in pack["source_files"])
    assert any(section["heading"] == "Key Findings" for section in pack["source_sections"])
    assert any(entity["label"] == "Acinetobacter baylyi ADP1" for entity in pack["deterministic_entities"])
    assert any(hint["label"] == "kescience_fitnessbrowser" for hint in pack["dataset_hints"])
    assert any(anchor["assertion_kind"] == "finding" for anchor in pack["evidence_anchors"])
    assert "claim" in pack["allowed_vocabularies"]["statement_kinds"]
    assert "scientific_edge" in pack["allowed_vocabularies"]["edge_classes"]


def test_adp1_deletion_context_pack_has_extraction_material() -> None:
    pack = build_context_pack(ADP1)

    assert pack["project"]["id"] == "adp1_deletion_phenotypes"
    assert any(
        "Carbon sources define a three-tier essentiality landscape" in section["text"]
        for section in pack["source_sections"]
    )
    assert any(hint["label"] == "kbase_ke_pangenome" for hint in pack["dataset_hints"])
    assert {"path": "01_data_extraction.ipynb"} in pack["asset_hints"]["notebooks"]
    assert {"path": "figures/condition_boxplots.png"} in pack["asset_hints"]["figures"]
    assert pack["openviking_context_refs"] == []
