"""Tests for the durable query registry — capture, and the resolver it unblocks."""

from __future__ import annotations

import argparse
import json

import pytest

from beril_cli.audit_cmd import run_capture_event
from beril_cli.claims_cmd import build_claim_state, resolve_evidence_pointer
from beril_cli.journal import JOURNAL_FILE, find_query


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    (tmp_path / "PROJECT.md").write_text("# repo marker\n")
    (tmp_path / "projects" / "p1").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    return tmp_path


def _ns(locator: str, payload: str = "SELECT 1", project: str | None = "p1", **kwargs):
    return argparse.Namespace(
        locator=locator,
        payload=payload,
        project=project,
        session=kwargs.get("session"),
    )


def _lines(repo):
    path = repo / "projects" / "p1" / JOURNAL_FILE
    return (
        [json.loads(ln) for ln in path.read_text().splitlines()]
        if path.exists()
        else []
    )


def test_capture_appends_a_record_and_omits_an_unknown_session(repo):
    assert run_capture_event(_ns("q:enrichment", "SELECT 1")) == 0
    (record,) = _lines(repo)
    assert record["kind"] == "query"
    assert record["locator"] == "q:enrichment"
    assert record["payload"] == "SELECT 1"
    assert record["ts"].endswith("Z")
    assert "session_id" not in record  # omitted, never fabricated


def test_capture_is_append_only(repo):
    run_capture_event(_ns("q:first", "SELECT 1"))
    run_capture_event(_ns("q:second", "SELECT 2", session="s-9"))
    first, second = _lines(repo)
    assert first["locator"] == "q:first"
    assert second["session_id"] == "s-9"


def test_project_resolves_from_cwd_when_not_named(repo, monkeypatch):
    monkeypatch.chdir(repo / "projects" / "p1")
    assert run_capture_event(_ns("q:from_cwd", project=None)) == 0
    assert _lines(repo)[0]["locator"] == "q:from_cwd"


def test_capture_never_blocks_and_records_nothing_it_cannot_stand_behind(repo, capsys):
    assert run_capture_event(_ns("enrichment")) == 0  # no q: prefix
    assert run_capture_event(_ns("q:enrichment", project="nope")) == 0
    assert run_capture_event(_ns("q:enrichment", payload="  ")) == 0  # no SQL
    assert _lines(repo) == []
    assert capsys.readouterr().err.count("nothing recorded") == 3


def test_find_query_returns_the_most_recent_and_skips_junk(repo):
    journal = repo / "projects" / "p1" / JOURNAL_FILE
    journal.write_text(
        '{"ts": "2026-07-01T00:00:00Z", "kind": "query", "locator": "q:a", "payload": "old"}\n'
        "not json at all\n"
        '{"kind": "query", "locator": "q:a", "payload": "no ts"}\n'
        '{"ts": "", "kind": "query", "locator": "q:a", "payload": "empty ts"}\n'
        '{"ts": "2026-07-02T00:00:00Z", "kind": "query", "locator": "q:a", "payload": "new"}\n'
    )
    assert find_query(journal.parent, "q:a")["payload"] == "new"
    assert find_query(journal.parent, "q:b") is None


def test_undecodable_bytes_never_raise_out_of_the_resolver(repo):
    """A partial write must not abort `beril claims build` for the whole project.

    ``UnicodeDecodeError`` is a ``ValueError``, so an ``except OSError`` around
    the read does not catch it — it would propagate through
    ``build_claim_state`` and take down the projection. Undecodable bytes
    degrade to U+FFFD instead: a record whose ``ts`` and ``locator`` survive
    still resolves (with a mangled payload), and one corrupted into invalid
    JSON is skipped like any other junk line.
    """
    project = repo / "projects" / "p1"
    (project / JOURNAL_FILE).write_bytes(
        b'{"ts": "2026-07-01T00:00:00Z", "kind": "query", "locator": "q:a", "payload": "\xff\xfe"}\n'
        b'{"ts": "2026-07-02T00:00:00Z", "kind": "query", "\xff\xfe": "q:b", "payload": "x"}\n'
    )
    assert find_query(project, "q:a")["ts"] == "2026-07-01T00:00:00Z"
    assert find_query(project, "q:b") is None  # its locator key did not survive
    assert (
        resolve_evidence_pointer(
            project, {"kind": "query", "locator": "q:b", "exact": ""}
        )["resolution"]["reason"]
        == "query-not-recorded"
    )


def test_captured_query_resolves_and_grounds_a_claim(repo):
    project = repo / "projects" / "p1"
    run_capture_event(_ns("q:enrichment_by_ecotype", "SELECT * FROM genomes"))

    pointer = resolve_evidence_pointer(
        project,
        {"kind": "query", "locator": "q:enrichment_by_ecotype", "exact": "OR 2.4"},
    )
    assert pointer["resolution"]["status"] == "resolved"
    assert pointer["resolution"]["query_id"] == "enrichment_by_ecotype"
    assert pointer["resolution"]["recorded_at"].endswith("Z")

    # The whole point: a captured query now feeds the computed support axis.
    report = """## Claims
### Lignin degraders are enriched
- confidence: medium
- supports:
  - query: q:enrichment_by_ecotype — "OR 2.4"
"""
    claim = build_claim_state("p1", report, project_dir=project)["claims"][0]
    assert claim["computed"]["resolved_artifact_support"] == "single-stream"
    assert claim["computed"]["evidence_resolution"]["resolved"] == 1


def test_malformed_query_locator_stays_invalid_not_merely_uncaptured(repo):
    pointer = resolve_evidence_pointer(
        repo / "projects" / "p1", {"kind": "query", "locator": "q:", "exact": ""}
    )
    assert pointer["resolution"] == {
        "status": "invalid",
        "reason": "malformed-query-locator",
    }


def test_query_without_a_project_directory_is_unresolved_not_invalid():
    pointer = resolve_evidence_pointer(
        None, {"kind": "query", "locator": "q:enrichment", "exact": ""}
    )
    assert pointer["resolution"] == {
        "status": "unresolved",
        "reason": "project-directory-unavailable",
    }
