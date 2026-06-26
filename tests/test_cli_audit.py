"""Tests for `beril trace-append` / `beril provenance-snapshot`.

Best-effort audit writers driven by settings.json hooks (PostToolUse /
SessionStart). They read the hook JSON payload from stdin, redact secrets, and
append/merge per-project provenance artifacts. They MUST never raise and always
exit 0 (never block a turn). Ported from beril-pi-agent lib/project-audit.ts.
"""

from __future__ import annotations

import argparse
import io
import json

import pytest

from beril_cli.audit_cmd import (
    redact_for_trace,
    resolve_project,
    run_provenance_snapshot,
    run_trace_append,
)


# --- secret redaction (key-name based, recursive, size-capped) ---


def test_redacts_secret_keys():
    out = redact_for_trace(
        {
            "api_key": "x",
            "token": "y",
            "password": "z",
            "authorization": "a",
            "credential": "c",
            "keep": "ok",
        }
    )
    assert out == {
        "api_key": "[redacted]",
        "token": "[redacted]",
        "password": "[redacted]",
        "authorization": "[redacted]",
        "credential": "[redacted]",
        "keep": "ok",
    }


def test_redaction_is_case_insensitive_and_recursive():
    out = redact_for_trace({"outer": {"API_KEY": "x", "note": "fine"}})
    assert out["outer"]["API_KEY"] == "[redacted]"
    assert out["outer"]["note"] == "fine"


def test_redaction_caps_arrays_at_50():
    assert redact_for_trace(list(range(60))) == list(range(50))


def test_redaction_caps_strings_at_240():
    assert redact_for_trace("a" * 300) == "a" * 240 + "..."


# --- value-level secret scrubbing (secrets embedded in ordinary string fields) ---


def test_redacts_secret_assignment_in_command_string():
    out = redact_for_trace({"command": "export KBASE_AUTH_TOKEN=sk-abc123 && python run.py"})
    assert "sk-abc123" not in out["command"]
    assert "[redacted]" in out["command"]
    assert "python run.py" in out["command"]  # non-secret tail preserved


def test_redacts_bearer_token_in_command():
    out = redact_for_trace(
        {"command": "curl -H 'Authorization: Bearer sk-xyz789' https://api.example/x"}
    )
    assert "sk-xyz789" not in out["command"]
    assert "https://api.example/x" in out["command"]


def test_redacts_secret_in_written_file_content():
    out = redact_for_trace({"content": "DB_PASSWORD=hunter2\nDEBUG=true"})
    assert "hunter2" not in out["content"]
    assert "DEBUG=true" in out["content"]


def test_does_not_redact_plain_command():
    out = redact_for_trace({"command": "ls projects/p1 && cat REPORT.md"})
    assert out["command"] == "ls projects/p1 && cat REPORT.md"


def test_does_not_redact_prose_mentioning_token():
    # A bare mention with no assignment must not be redacted.
    assert redact_for_trace("rotate the auth token regularly") == "rotate the auth token regularly"


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


# --- trace-append ---


def test_trace_append_writes_one_redacted_line(repo, monkeypatch):
    _stdin(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_use_id": "t1",
            "tool_input": {"file_path": "projects/p1/REPORT.md", "token": "SECRET"},
            "cwd": str(repo),
        },
    )
    rc = run_trace_append(argparse.Namespace())
    assert rc == 0
    lines = (repo / "projects" / "p1" / "TRACE.jsonl").read_text().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["project"] == "p1"
    assert row["tool"] == "Write"
    assert row["event"] == "PostToolUse"
    assert "at" in row
    # secret redacted, non-secret preserved
    assert row["input"]["token"] == "[redacted]"
    assert row["input"]["file_path"] == "projects/p1/REPORT.md"


def test_trace_append_is_append_only(repo, monkeypatch):
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls projects/p1"}, "cwd": str(repo)}
    _stdin(monkeypatch, payload)
    run_trace_append(argparse.Namespace())
    _stdin(monkeypatch, payload)
    run_trace_append(argparse.Namespace())
    lines = (repo / "projects" / "p1" / "TRACE.jsonl").read_text().splitlines()
    assert len(lines) == 2


def test_trace_append_skips_when_no_project(repo, monkeypatch):
    _stdin(monkeypatch, {"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(repo)})
    rc = run_trace_append(argparse.Namespace())
    assert rc == 0
    assert not (repo / "projects" / "p1" / "TRACE.jsonl").exists()


def test_trace_append_survives_malformed_stdin(repo, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json{"))
    assert run_trace_append(argparse.Namespace()) == 0


# --- provenance-snapshot ---


def test_provenance_snapshot_writes_runtime_block(repo, monkeypatch):
    _stdin(
        monkeypatch,
        {
            "hook_event_name": "SessionStart",
            "session_id": "s1",
            "permission_mode": "auto",
            "cwd": str(repo / "projects" / "p1"),
        },
    )
    rc = run_provenance_snapshot(argparse.Namespace())
    assert rc == 0
    data = json.loads((repo / "projects" / "p1" / "provenance.json").read_text())
    assert data["project"] == "p1"
    assert data["runtime"]["beril_package_version"]
    assert data["runtime"]["permission_mode"] == "auto"


def test_provenance_snapshot_merges_not_overwrites(repo, monkeypatch):
    p = repo / "projects" / "p1"
    _stdin(monkeypatch, {"session_id": "s1", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    # a downstream writer adds a custom key
    data = json.loads((p / "provenance.json").read_text())
    data["custom"] = "keep"
    (p / "provenance.json").write_text(json.dumps(data) + "\n")
    _stdin(monkeypatch, {"session_id": "s2", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    merged = json.loads((p / "provenance.json").read_text())
    assert merged["custom"] == "keep"


def test_provenance_snapshot_skips_when_no_project(repo, monkeypatch):
    _stdin(monkeypatch, {"session_id": "s1", "cwd": str(repo)})
    assert run_provenance_snapshot(argparse.Namespace()) == 0
    assert not (repo / "projects" / "p1" / "provenance.json").exists()


def test_provenance_snapshot_deep_merges_runtime(repo, monkeypatch):
    p = repo / "projects" / "p1"
    # an earlier snapshot captures a model_id
    _stdin(monkeypatch, {"session_id": "s1", "model_id": "claude-x", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    # a later snapshot lacks model_id; it must NOT clobber the earlier runtime field
    _stdin(monkeypatch, {"session_id": "s2", "cwd": str(p)})
    run_provenance_snapshot(argparse.Namespace())
    runtime = json.loads((p / "provenance.json").read_text())["runtime"]
    assert runtime["model_id"] == "claude-x"
    assert runtime["session_id"] == "s2"
