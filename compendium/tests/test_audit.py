"""Tests for the Phase-0 corpus audit module."""

from __future__ import annotations

import hashlib
from pathlib import Path

from compendium.audit import audit_corpus, audit_project, parse_headings

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DEMO = FIXTURES / "proj_demo"


def test_parse_headings_finds_h1_and_h2():
    text = (DEMO / "REPORT.md").read_text()
    headings = parse_headings(text)
    h1 = [h for h in headings if h["level"] == 1]
    assert any(h["text"].startswith("Report:") for h in h1)
    assert any(h["level"] == 2 and h["text"] == "Key Findings" for h in headings)
    # char is the byte/char offset of the line start.
    first = headings[0]
    assert first["char"] == 0
    assert first["line"] == 1


def test_parse_headings_ignores_h4_and_blank():
    text = "#### too deep\n\nnot a heading\n## Real\n"
    headings = parse_headings(text)
    assert [h["text"] for h in headings] == ["Real"]


def test_audit_project_demo():
    audit = audit_project(DEMO)
    assert audit["files"]["report"] is True
    assert audit["coverage"] >= 0.9
    assert audit["metadata_source"] == "readme"
    texts = [h["text"] for h in audit["headings"]]
    assert "Key Findings" in texts
    assert audit["id"] == "proj_demo"


def test_audit_project_source_sections_have_exact_ranges_and_hashes():
    audit = audit_project(DEMO)
    report = (DEMO / "REPORT.md").read_text()
    data = next(
        section
        for section in audit["source_sections"]
        if section["source_doc"] == "REPORT.md" and section["heading"] == "Data"
    )

    start, end = data["char"]
    exact = report[start:end]
    assert exact == data["text"]
    assert data["line"] == [27, 28]
    assert data["text_hash"] == "sha256:" + hashlib.sha256(exact.encode()).hexdigest()
    assert data["id"].startswith("source_section:")


def test_audit_project_source_anchors_for_demo_fixture():
    audit = audit_project(DEMO)
    anchors = {(anchor["kind"], anchor["exact"]) for anchor in audit["source_anchors"]}

    assert ("dataset", "kescience_fitnessbrowser") in anchors
    assert ("dataset", "kbase_ke_pangenome") in anchors
    assert ("notebook", "01_demo.ipynb") in anchors
    assert ("figure", "figures/fitness_overview.png") in anchors
    assert ("pmid", "PMID:12345678") in anchors
    assert ("ko", "K00845") in anchors
    assert ("cog", "COG0791") in anchors
    assert ("dataset", "data/fitness_summary.tsv") not in anchors

    ko = next(
        anchor
        for anchor in audit["source_anchors"]
        if anchor["kind"] == "ko" and anchor["exact"] == "K00845"
    )
    report = (DEMO / "REPORT.md").read_text()
    start, end = ko["char"]
    assert report[start:end] == ko["exact"]
    assert ko["source_section_heading"] == "2. Gene K00845 is essential for glucose metabolism"
    assert ko["id"].startswith("source_anchor:")


def test_audit_project_source_inventory_covers_all_canonical_files(tmp_path):
    (tmp_path / "REPORT.md").write_text(
        "\n".join([
            "# Report: Source Inventory",
            "",
            "## Data",
            "- BERDL collection `kbase_ke_pangenome`",
            "- Genome RS_GCF_003028315.1 maps to s__Neisseria_mucosa_A.",
            "- PF02085 and K00198 are marker identifiers.",
            "",
            "## References",
            "- DOI: 10.1128/mSphere.00223-21",
        ])
        + "\n"
    )
    (tmp_path / "RESEARCH_PLAN.md").write_text(
        "# Plan\n\nSee [parent](../functional_dark_matter/) and 01_plan.ipynb.\n"
    )
    (tmp_path / "REVIEW.md").write_text("# Review\n\nCOG1028 is mentioned.\n")
    (tmp_path / "README.md").write_text("# Readme\n\nSee [Report](REPORT.md).\n")
    (tmp_path / "beril.yaml").write_text("project: source_inventory\nstatus: complete\n")

    first = audit_project(tmp_path)
    second = audit_project(tmp_path)
    assert first["source_files"] == second["source_files"]
    assert first["source_sections"] == second["source_sections"]
    assert first["source_anchors"] == second["source_anchors"]
    assert {source["path"] for source in first["source_files"]} == {
        "REPORT.md",
        "RESEARCH_PLAN.md",
        "REVIEW.md",
        "README.md",
        "beril.yaml",
    }

    anchors = {(anchor["kind"], anchor["exact"]) for anchor in first["source_anchors"]}
    assert ("doi", "DOI: 10.1128/mSphere.00223-21") in anchors
    assert ("project_link", "../functional_dark_matter/") in anchors
    assert ("project_link", "REPORT.md") in anchors
    assert ("notebook", "01_plan.ipynb") in anchors
    assert ("pfam", "PF02085") in anchors
    assert ("ko", "K00198") in anchors
    assert ("cog", "COG1028") in anchors
    assert ("gtdb_taxon", "s__Neisseria_mucosa_A") in anchors
    assert ("genome_id", "RS_GCF_003028315.1") in anchors

    beril_section = next(
        section for section in first["source_sections"] if section["source_doc"] == "beril.yaml"
    )
    assert beril_section["heading"] is None
    assert beril_section["line"] == [1, 2]


def test_audit_project_missing_report(tmp_path):
    (tmp_path / "README.md").write_text("# Empty\n")
    audit = audit_project(tmp_path)
    assert audit["files"]["report"] is False
    assert audit["coverage"] == 0.0


def test_audit_corpus_rollup(tmp_path):
    # one good project (copy of demo) + one empty project.
    good = tmp_path / "good"
    good.mkdir()
    (good / "REPORT.md").write_text((DEMO / "REPORT.md").read_text())
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "README.md").write_text("# nothing\n")

    corpus = audit_corpus(tmp_path)
    assert set(corpus["projects"]) == {"good", "empty"}
    roll = corpus["rollup"]
    assert roll["n_projects"] == 2
    assert roll["has_report"] == 1
    assert 0.0 < roll["mean_coverage"] <= 1.0
    assert roll["file_presence"]["report"] == 1
