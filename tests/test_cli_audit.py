"""Tests for `beril provenance-snapshot` — best-effort runtime provenance writer.

Driven by a SessionStart hook: reads the hook payload from stdin, resolves the
active project, and writes/merges a per-project provenance.json shaped loosely to
W3C PROV (entity = the project, activity = the session, agent = beril + model).
Must never raise and always exit 0 (never block a turn).
"""

from __future__ import annotations

import argparse
import io
import json

import pytest

from beril_cli.audit_cmd import resolve_project, run_provenance_snapshot


# --- project resolution from the hook payload (cwd is repo root, so use paths) ---


def test_resolve_project_from_tool_input_path():
    assert resolve_project({"tool_input": {"file_path": "projects/p1/notebooks/x.ipynb"}}) == "p1"


def test_resolve_project_from_cwd():
    assert resolve_project({"cwd": "/home/u/repo/projects/p2"}) == "p2"


def test_resolve_project_prefers_tool_input_over_cwd():
    payload = {"tool_input": {"file_path": "projects/p1/x"}, "cwd": "/repo/projects/p2"}
    assert resolve_project(payload) == "p1"


def test_resolve_project_none_when_absent():
    assert resolve_project({"tool_input": {"command": "ls"}, "cwd": "/home/u/repo"}) is None


def test_resolve_project_rejects_punctuation_prefixed():
    # `projects/` must sit at a path-segment boundary (start, slash, or space) —
    # a punctuation-glued token like `x-projects/p1` must NOT resolve.
    assert resolve_project({"tool_input": {"command": "cat x-projects/p1/f"}}) is None


# --- shared fixture: a minimal repo with one project ---


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    (tmp_path / "PROJECT.md").write_text("# marker\n")
    (tmp_path / "projects" / "p1").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _stdin(monkeypatch, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


# --- provenance-snapshot: PROV-shaped entity / activity / agent ---


def test_provenance_snapshot_writes_prov_shape(repo, monkeypatch):
    _stdin(
        monkeypatch,
        {
            "hook_event_name": "SessionStart",
            "session_id": "s1",
            "permission_mode": "auto",
            "model_id": "claude-x",
            "cwd": str(repo / "projects" / "p1"),
        },
    )
    rc = run_provenance_snapshot(argparse.Namespace())
    assert rc == 0
    data = json.loads((repo / "projects" / "p1" / "provenance.json").read_text())
    assert data["project"] == "p1"
    assert data["agent"]["beril_version"]
    assert data["agent"]["model_id"] == "claude-x"
    assert data["activity"]["session_id"] == "s1"
    assert data["activity"]["permission_mode"] == "auto"


def test_provenance_snapshot_merges_not_overwrites(repo, monkeypatch):
    p = repo / "projects" / "p1"
    _stdin(monkeypatch, {"session_id": "s1", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    data = json.loads((p / "provenance.json").read_text())
    data["custom"] = "keep"  # a downstream writer adds a sibling key
    (p / "provenance.json").write_text(json.dumps(data) + "\n")
    _stdin(monkeypatch, {"session_id": "s2", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    assert json.loads((p / "provenance.json").read_text())["custom"] == "keep"


def test_provenance_snapshot_deep_merges_agent(repo, monkeypatch):
    p = repo / "projects" / "p1"
    # an earlier snapshot captures a model_id
    _stdin(monkeypatch, {"session_id": "s1", "model_id": "claude-x", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    # a later snapshot lacks model_id; it must NOT clobber the earlier agent field
    _stdin(monkeypatch, {"session_id": "s2", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    data = json.loads((p / "provenance.json").read_text())
    assert data["agent"]["model_id"] == "claude-x"  # preserved
    assert data["activity"]["session_id"] == "s2"  # updated


def test_provenance_snapshot_skips_when_no_project(repo, monkeypatch):
    _stdin(monkeypatch, {"session_id": "s1", "cwd": str(repo)})
    assert run_provenance_snapshot(argparse.Namespace()) == 0
    assert not (repo / "projects" / "p1" / "provenance.json").exists()


def test_provenance_snapshot_survives_malformed_stdin(repo, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json{"))
    assert run_provenance_snapshot(argparse.Namespace()) == 0
