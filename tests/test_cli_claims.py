"""Tests for `beril claims` — builds/inspects the per-project claims ledger.

The CLI parses a ``## Claims`` block from REPORT.md, computes groundedness and
tier_mismatch deterministically, and writes/inspects ``claims.json``. The author
writes the confidence WORD; the CLI computes the rest and renders words only.
"""

from __future__ import annotations

import argparse
import json

import pytest

from beril_cli.claims_cmd import build_claim_state, parse_claims_block, run_claims

REPORT = """# Report: Soil Lignin

## Key Findings

Lignin degraders look enriched. (free-form prose, not parsed)

## Claims

### Lignin degraders are enriched in soil communities
- confidence: high
- status: supported
- supports:
  - notebook: notebooks/NB03_stats.ipynb#cell-12 — "p=0.003, n=412"
  - query: q:enrichment_by_ecotype — "OR 2.4, CI 1.8-3.1"
- refutes:
  - paper: PMID:111 — "no enrichment in marine taxa"

### Methylotrophy correlates with depth
- confidence: high
- status: open
- supports:
  - notebook: notebooks/NB04.ipynb#cell-3 — "r=0.7"
  - notebook: notebooks/NB04.ipynb#cell-3 — "same cell restated"

## Methods

This section is after Claims and must not be parsed.
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """A minimal repo: PROJECT.md marker + projects/p1/REPORT.md."""
    (tmp_path / "PROJECT.md").write_text("# repo marker\n")
    proj = tmp_path / "projects" / "p1"
    proj.mkdir(parents=True)
    (proj / "REPORT.md").write_text(REPORT)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _ns(action: str, project: str = "p1", json_flag: bool = False) -> argparse.Namespace:
    return argparse.Namespace(action=action, project=project, json=json_flag)


# --- parsing the ## Claims micro-format ---


def test_parse_extracts_two_claims():
    claims = parse_claims_block(REPORT)
    assert len(claims) == 2
    assert claims[0]["claim"] == "Lignin degraders are enriched in soil communities"
    assert claims[0]["confidence"] == "high"
    assert claims[0]["status"] == "supported"


def test_parse_reads_supports_and_refutes_pointers():
    claims = parse_claims_block(REPORT)
    supports = claims[0]["supports"]
    assert len(supports) == 2
    assert supports[0] == {
        "kind": "notebook",
        "locator": "notebooks/NB03_stats.ipynb#cell-12",
        "exact": '"p=0.003, n=412"',
    }
    assert supports[1]["kind"] == "query"
    assert supports[1]["locator"] == "q:enrichment_by_ecotype"
    refutes = claims[0]["refutes"]
    assert len(refutes) == 1
    assert refutes[0]["kind"] == "paper"
    assert refutes[0]["locator"] == "PMID:111"


def test_parse_ignores_sections_outside_claims():
    # "## Methods" content and the "## Key Findings" prose are not claims.
    claims = parse_claims_block(REPORT)
    assert all("after Claims" not in c["claim"] for c in claims)


def test_parse_no_claims_section_returns_empty():
    assert parse_claims_block("# Report\n\n## Key Findings\n\nNothing.\n") == []


# --- computing the ledger ---


def test_build_state_computes_groundedness_and_mismatch():
    state = build_claim_state("p1", REPORT)
    rows = state["rows"]
    assert len(rows) == 2

    # Claim 1: two DISTINCT result sources -> well-grounded, high confidence -> no mismatch.
    assert rows[0]["groundedness"] == "well-grounded"
    assert rows[0]["tier_mismatch"] is False
    assert rows[0]["claim_id"] == "lignin-degraders-are-enriched-in-soil-communities"

    # Claim 2: two pointers into the SAME notebook cell -> single-source, high -> mismatch.
    assert rows[1]["groundedness"] == "single-source"
    assert rows[1]["tier_mismatch"] is True


def test_build_state_includes_project_and_prefixed_report_hash():
    import hashlib

    state = build_claim_state("p1", REPORT)
    assert state["project"] == "p1"
    assert "updated_at" in state
    expected = "sha256:" + hashlib.sha256(REPORT.encode("utf-8")).hexdigest()
    assert state["report_hash"] == expected


# --- the `build` action writes claims.json ---


def test_build_writes_pretty_json_with_trailing_newline(repo, capsys):
    rc = run_claims(_ns("build"))
    assert rc == 0
    path = repo / "projects" / "p1" / "claims.json"
    raw = path.read_text()
    assert raw.endswith("}\n")  # pretty JSON + trailing newline
    data = json.loads(raw)
    assert len(data["rows"]) == 2
    out = capsys.readouterr().out
    assert "2 claim" in out


# --- the `summary` action prints a word-only advisory, never numeric confidence ---


def test_summary_json_reports_tier_mismatch_count(repo, capsys):
    rc = run_claims(_ns("summary", json_flag=True))
    assert rc == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["total"] == 2
    assert summary["tier_mismatch"] == 1


def test_summary_warns_about_tier_mismatch_in_words(repo, capsys):
    rc = run_claims(_ns("summary"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "high/medium confidence on a single/no re-runnable source" in out
    # The advisory is rendered as words/counts — never a numeric confidence score.
    assert "0." not in out and "%" not in out


def test_summary_does_not_write_claims_json(repo):
    run_claims(_ns("summary"))
    assert not (repo / "projects" / "p1" / "claims.json").exists()


def test_missing_report_is_an_error(repo, capsys):
    (repo / "projects" / "p1" / "REPORT.md").unlink()
    rc = run_claims(_ns("build"))
    assert rc == 1
    assert "REPORT.md" in capsys.readouterr().err


def test_unknown_project_is_an_error(repo, capsys):
    rc = run_claims(_ns("build", project="nope"))
    assert rc == 1


def test_parse_inline_pointer_on_supports_line():
    # An author who writes the pointer on the SAME line as `supports:` must not
    # have it silently dropped (which would wrongly downgrade groundedness).
    md = (
        "## Claims\n\n"
        "### Inline claim\n"
        "- confidence: medium\n"
        '- supports: notebook: notebooks/NB1.ipynb#cell-2 — "x"\n'
    )
    claims = parse_claims_block(md)
    assert len(claims) == 1
    assert claims[0]["supports"] == [
        {"kind": "notebook", "locator": "notebooks/NB1.ipynb#cell-2", "exact": '"x"'}
    ]
