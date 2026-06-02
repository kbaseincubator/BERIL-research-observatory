"""Tests for the Phase-0 corpus audit module."""

from __future__ import annotations

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
