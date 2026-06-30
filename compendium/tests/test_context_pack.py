"""Tests for deterministic context pack construction."""

from __future__ import annotations

from pathlib import Path

from compendium.context_pack import build_context_pack, context_pack_bytes

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "compendium" / "fixtures" / "proj_demo"
ADP1 = ROOT / "projects" / "adp1_deletion_phenotypes"

# Keys retired by the context-pack v2 rework; none may resurface.
_DROPPED_KEYS = {
    "deterministic_entities",
    "deterministic_mentions",
    "evidence_anchors",
    "dataset_hints",
    "openviking_context_refs",
}


def test_context_pack_bytes_are_deterministic() -> None:
    first = build_context_pack(FIXTURE)
    second = build_context_pack(FIXTURE)

    assert first == second
    assert context_pack_bytes(first) == context_pack_bytes(second)
    assert first["context_pack_hash"].startswith("sha256:")


def test_basic_fixture_context_pack_contains_required_scaffold() -> None:
    pack = build_context_pack(FIXTURE)

    assert pack["context_pack_version"] == 2
    project = pack["project"]
    assert project["id"] == "proj_demo"
    # No beril.yaml: title falls back to the REPORT.md H1 line.
    assert project["title"] == "Report: Acinetobacter baylyi ADP1 Demo Study"
    assert "stage1_coverage" not in project
    assert project["coverage"] == 1.0
    # README has no ## Authors block -> empty list, but the key is present and a list.
    assert isinstance(project["authors"], list)
    assert project["authors"] == []

    assert {source["path"] for source in pack["source_files"]} == {"REPORT.md", "README.md"}
    assert all(source["sha256"].startswith("sha256:") for source in pack["source_files"])
    assert any(section["heading"] == "Key Findings" for section in pack["source_sections"])
    assert any(anchor["kind"] == "notebook" for anchor in pack["source_anchors"])

    # candidate_terms are {kind: sorted distinct 'exact' values} from source_anchors.
    terms = pack["candidate_terms"]
    assert isinstance(terms, dict)
    assert "dataset" in terms
    assert terms["dataset"] == sorted(terms["dataset"])
    anchor_datasets = {a["exact"] for a in pack["source_anchors"] if a["kind"] == "dataset"}
    assert set(terms["dataset"]) == anchor_datasets

    vocab = pack["allowed_vocabularies"]
    assert "claim" in vocab["statement_kinds"]
    assert "supports" in vocab["statement_links"]
    # Legacy vocabularies were trimmed out.
    assert "edge_classes" not in vocab
    assert "entity_types" not in vocab
    assert "legacy_assertion_kinds" not in vocab

    assert _DROPPED_KEYS.isdisjoint(pack)


def test_adp1_context_pack_resolves_authors_and_terms() -> None:
    pack = build_context_pack(ADP1)

    project = pack["project"]
    assert project["id"] == "adp1_deletion_phenotypes"
    # README ## Authors block -> author dicts with name/orcid/affiliation keys.
    authors = project["authors"]
    assert authors and all({"name", "orcid", "affiliation"} <= set(a) for a in authors)
    dehal = next(a for a in authors if a["orcid"] == "0000-0001-5810-2497")
    assert dehal["name"] == "Paramvir S. Dehal"

    assert any(
        "Carbon sources define a three-tier essentiality landscape" in section["text"]
        for section in pack["source_sections"]
    )
    # Shared collection surfaces as a candidate dataset term.
    assert "kbase_ke_pangenome" in pack["candidate_terms"].get("dataset", [])
    assert {"path": "01_data_extraction.ipynb"} in pack["asset_hints"]["notebooks"]
    assert {"path": "figures/condition_boxplots.png"} in pack["asset_hints"]["figures"]
    assert _DROPPED_KEYS.isdisjoint(pack)
