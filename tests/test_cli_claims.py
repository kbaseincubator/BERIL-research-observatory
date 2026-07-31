"""Tests for the versioned, resolution-aware per-project claims ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pytest

from beril_cli.claims_cmd import (
    build_claim_state,
    parse_claims_block,
    resolve_evidence_pointer,
    run_claims,
    summarize,
)

REPORT = """# Report: Soil Lignin

## Claims

### Lignin degraders are enriched in soil communities
- confidence: high
- status: supported
- supports:
  - notebook: notebooks/NB03_stats.ipynb#cell-2 — "p=0.003, n=412"
  - query: q:enrichment_by_ecotype — "OR 2.4, CI 1.8-3.1"
- refutes:
  - paper: PMID:111 — "no enrichment in marine taxa"

### Methylotrophy correlates with depth
- confidence: high
- status: open
- supports:
  - notebook: notebooks/NB04.ipynb#cell-1 — "r=0.7"
  - notebook: notebooks/NB04.ipynb#cell-1 — "same cell restated"

## Methods

This section is after Claims and must not be parsed.
"""


def _write_notebook(path: Path, cells: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "nbformat": 4,
                "nbformat_minor": 5,
                "metadata": {},
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "source": [f"x = {i}"],
                        "outputs": [],
                    }
                    for i in range(cells)
                ],
            }
        )
        + "\n"
    )


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    (tmp_path / "PROJECT.md").write_text("# repo marker\n")
    project = tmp_path / "projects" / "p1"
    project.mkdir(parents=True)
    (project / "REPORT.md").write_text(REPORT)
    _write_notebook(project / "notebooks" / "NB03_stats.ipynb")
    _write_notebook(project / "notebooks" / "NB04.ipynb")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _ns(
    action: str, project: str = "p1", json_flag: bool = False
) -> argparse.Namespace:
    return argparse.Namespace(action=action, project=project, json=json_flag)


def test_parse_extracts_author_assertions_and_evidence():
    claims = parse_claims_block(REPORT)
    assert len(claims) == 2
    assert claims[0]["confidence"] == "high"
    assert claims[0]["status"] == "supported"
    assert claims[0]["supports"][0] == {
        "kind": "notebook",
        "locator": "notebooks/NB03_stats.ipynb#cell-2",
        "exact": '"p=0.003, n=412"',
    }
    assert claims[0]["refutes"][0]["kind"] == "paper"


def test_parse_stream_metadata_is_explicit():
    md = """## Claims

### Replicated claim
- supports:
  - notebook: notebooks/a.ipynb#cell-1 [stream: field-cohort] — "field"
"""
    assert parse_claims_block(md)[0]["supports"][0]["stream"] == "field-cohort"


def test_parse_ignores_sections_outside_claims_and_handles_missing_section():
    assert all("after Claims" not in c["claim"] for c in parse_claims_block(REPORT))
    assert parse_claims_block("# Report\n\n## Key Findings\nNothing\n") == []


def test_resolves_existing_notebook_and_validates_one_based_cell(repo):
    project = repo / "projects" / "p1"
    pointer = resolve_evidence_pointer(
        project,
        {
            "kind": "notebook",
            "locator": "notebooks/NB03_stats.ipynb#cell-2",
            "exact": "x",
        },
    )
    assert pointer["resolution"]["status"] == "resolved"
    assert pointer["resolution"]["cell"] == 2


@pytest.mark.parametrize(
    ("locator", "status"),
    [
        ("notebooks/missing.ipynb#cell-1", "unresolved"),
        ("../outside.ipynb#cell-1", "invalid"),
        ("/tmp/outside.ipynb#cell-1", "invalid"),
        ("notebooks/NB03_stats.ipynb#cell-zero", "invalid"),
        ("notebooks/NB03_stats.ipynb#cell-99", "unresolved"),
    ],
)
def test_notebook_locator_failures_are_safe(repo, locator, status):
    project = repo / "projects" / "p1"
    pointer = resolve_evidence_pointer(
        project, {"kind": "notebook", "locator": locator, "exact": ""}
    )
    assert pointer["resolution"]["status"] == status


def test_query_pointer_is_preserved_but_unresolved_when_never_captured(repo):
    pointer = resolve_evidence_pointer(
        repo / "projects" / "p1",
        {"kind": "query", "locator": "q:enrichment_by_ecotype", "exact": "OR 2.4"},
    )
    assert pointer["locator"] == "q:enrichment_by_ecotype"
    assert pointer["resolution"] == {
        "status": "unresolved",
        "reason": "query-not-recorded",
    }


def test_two_nonexistent_notebooks_never_create_positive_support(tmp_path):
    report = """## Claims
### Fake support
- confidence: high
- supports:
  - notebook: notebooks/a.ipynb
  - notebook: notebooks/b.ipynb
"""
    state = build_claim_state("p", report, project_dir=tmp_path)
    claim = state["claims"][0]
    assert claim["computed"]["resolved_artifact_support"] == "none"
    assert claim["computed"]["confidence_mismatch"] is True


def test_two_resolved_notebooks_default_to_one_stream(tmp_path):
    _write_notebook(tmp_path / "notebooks" / "a.ipynb", 1)
    _write_notebook(tmp_path / "notebooks" / "b.ipynb", 1)
    report = """## Claims
### Same stream unless declared otherwise
- confidence: high
- supports:
  - notebook: notebooks/a.ipynb#cell-1
  - notebook: notebooks/b.ipynb#cell-1
"""
    claim = build_claim_state("p", report, project_dir=tmp_path)["claims"][0]
    assert claim["computed"]["resolved_artifact_support"] == "single-stream"


def test_explicit_resolved_streams_are_distinguished(tmp_path):
    _write_notebook(tmp_path / "notebooks" / "a.ipynb", 1)
    _write_notebook(tmp_path / "notebooks" / "b.ipynb", 1)
    report = """## Claims
### Explicit streams
- confidence: high
- supports:
  - notebook: notebooks/a.ipynb#cell-1 [stream: field]
  - notebook: notebooks/b.ipynb#cell-1 [stream: culture]
"""
    claim = build_claim_state("p", report, project_dir=tmp_path)["claims"][0]
    assert claim["computed"]["resolved_artifact_support"] == "multiple-streams"
    assert claim["computed"]["confidence_mismatch"] is False


def test_build_state_v2_separates_assertions_from_computation(repo):
    project = repo / "projects" / "p1"
    state = build_claim_state("p1", REPORT, project_dir=project)
    claim = state["claims"][0]
    assert state["schema_version"] == "2.0"
    assert claim["author_assertions"] == {
        "status": "supported",
        "confidence": "high",
        "source": "REPORT.md",
    }
    assert claim["computed"]["resolved_artifact_support"] == "single-stream"
    assert claim["supports"][0]["resolution"]["status"] == "resolved"
    assert claim["supports"][1]["resolution"]["status"] == "unresolved"
    expected = "sha256:" + hashlib.sha256(REPORT.encode()).hexdigest()
    assert state["report_hash"] == expected


def test_reviewer_notes_are_carried_forward_by_claim_id(repo):
    prior = {
        "claims": [
            {
                "claim_id": "lignin-degraders-are-enriched-in-soil-communities",
                "reviewer_notes": "keep",
            }
        ]
    }
    state = build_claim_state("p1", REPORT, prior, repo / "projects" / "p1")
    assert state["claims"][0]["reviewer_notes"] == "keep"


def test_summarize_tallies_author_status_and_mismatch():
    v2 = {
        "claims": [
            {
                "author_assertions": {"status": "supported"},
                "computed": {"confidence_mismatch": False},
                "supports": [],
            },
            {
                "author_assertions": {"status": "open"},
                "computed": {"confidence_mismatch": True},
                "supports": [],
            },
        ]
    }
    assert summarize(v2)["author_status"]["supported"] == 1
    assert summarize(v2)["confidence_mismatch"] == 1


def test_build_writes_versioned_claims_collection(repo, capsys):
    assert run_claims(_ns("build")) == 0
    raw = (repo / "projects" / "p1" / "claims.json").read_text()
    data = json.loads(raw)
    assert raw.endswith("}\n")
    assert data["schema_version"] == "2.0"
    assert len(data["claims"]) == 2
    assert data["summary"]["total"] == 2
    assert "author-marked" in capsys.readouterr().out


def test_summary_is_read_only_and_clear_about_author_assertions(repo, capsys):
    assert run_claims(_ns("summary", json_flag=True)) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["total"] == 2
    assert summary["author_status"]["supported"] == 1
    assert not (repo / "projects" / "p1" / "claims.json").exists()


def test_summary_human_warning_names_resolved_artifact_support(repo, capsys):
    run_claims(_ns("summary"))
    out = capsys.readouterr().out
    assert "author-marked supported" in out
    assert "resolved artifact support" in out
    assert "0." not in out and "%" not in out


def test_missing_report_and_unknown_project_are_errors(repo, capsys):
    (repo / "projects" / "p1" / "REPORT.md").unlink()
    assert run_claims(_ns("build")) == 1
    assert "REPORT.md" in capsys.readouterr().err
    assert run_claims(_ns("build", project="nope")) == 1


def test_parse_inline_pointer_on_supports_line():
    md = '## Claims\n\n### Inline\n- supports: notebook: notebooks/NB1.ipynb#cell-2 — "x"\n'
    assert parse_claims_block(md)[0]["supports"] == [
        {"kind": "notebook", "locator": "notebooks/NB1.ipynb#cell-2", "exact": '"x"'}
    ]
