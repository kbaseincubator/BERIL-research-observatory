"""Tests for conservative project resolution and atomic runtime sessions."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path

import pytest

from beril_cli import audit_cmd
from beril_cli.audit_cmd import (
    record_session_cost,
    resolve_project,
    run_runtime_snapshot,
)


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    # The CLI falls back to these env vars; clear them so a live Claude Code
    # session running the suite can't leak effort / session id into fixtures.
    monkeypatch.delenv("CLAUDE_EFFORT", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    (tmp_path / "PROJECT.md").write_text("# marker\n")
    for name in ("p1", "p2"):
        project = tmp_path / "projects" / name
        project.mkdir(parents=True)
        (project / "beril.yaml").write_text(f"project_id: {name}\n")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _stdin(monkeypatch, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


def _snap(repo, monkeypatch, session_id="s1", **extra):
    payload = {
        "session_id": session_id,
        "cwd": str(repo / "projects" / "p1"),
        **extra,
    }
    _stdin(monkeypatch, payload)
    assert run_runtime_snapshot(argparse.Namespace()) == 0
    return json.loads((repo / "projects" / "p1" / "runtime.json").read_text())


def test_explicit_binding_has_highest_precedence(repo):
    payload = {
        "project_id": "p1",
        "transcript_path": str(repo / "projects" / "p2" / "session.jsonl"),
        "cwd": str(repo / "projects" / "p2"),
    }
    assert resolve_project(payload, repo_root=repo, branch="projects/p2") == "p1"


def test_nested_session_binding_is_supported(repo):
    assert (
        resolve_project(
            {"session": {"project_id": "p2"}, "cwd": str(repo)},
            repo_root=repo,
            branch="unknown",
        )
        == "p2"
    )


def test_payload_project_path_precedes_cwd(repo):
    payload = {
        "transcript_path": str(repo / "projects" / "p1" / "session.jsonl"),
        "cwd": str(repo / "projects" / "p2"),
    }
    assert resolve_project(payload, repo_root=repo, branch="projects/p2") == "p1"


def test_ambiguous_payload_paths_return_no_project(repo):
    payload = {
        "transcript_path": str(repo / "projects" / "p1" / "session.jsonl"),
        "other_path": str(repo / "projects" / "p2" / "notes.md"),
        "cwd": str(repo / "projects" / "p1"),
    }
    assert resolve_project(payload, repo_root=repo, branch="projects/p1") is None


def test_cwd_inside_project_precedes_branch(repo):
    payload = {"cwd": str(repo / "projects" / "p2")}
    assert resolve_project(payload, repo_root=repo, branch="projects/p1") == "p2"


def test_repository_root_startup_resolves_exact_project_branch(repo):
    assert (
        resolve_project({"cwd": str(repo)}, repo_root=repo, branch="projects/p1")
        == "p1"
    )


def test_repository_root_startup_resolves_unique_manifest_branch(repo):
    (repo / "projects" / "p2" / "beril.yaml").write_text(
        "project_id: p2\nbranch: feat/p2-analysis\n"
    )
    assert (
        resolve_project({"cwd": str(repo)}, repo_root=repo, branch="feat/p2-analysis")
        == "p2"
    )


def test_ambiguous_branch_mapping_returns_no_project(repo):
    for name in ("p1", "p2"):
        (repo / "projects" / name / "beril.yaml").write_text(
            f"project_id: {name}\nbranch: shared\n"
        )
    assert resolve_project({"cwd": str(repo)}, repo_root=repo, branch="shared") is None


def test_manifest_naming_default_branch_binds_nothing(repo):
    """A lone `branch: main` must not capture every repo-root session on main.

    The ambiguity guard cannot catch this: one such manifest looks exactly like a
    correct unique match.
    """
    (repo / "projects" / "p2" / "beril.yaml").write_text(
        "project_id: p2\nbranch: main\n"
    )
    assert resolve_project({"cwd": str(repo)}, repo_root=repo, branch="main") is None
    assert resolve_project({"cwd": str(repo)}, repo_root=repo, branch="master") is None


def test_default_branch_guard_spares_conventional_form(repo):
    """`projects/<id>` still resolves even for a project literally named `main`."""
    (repo / "projects" / "main").mkdir()
    assert (
        resolve_project({"cwd": str(repo)}, repo_root=repo, branch="projects/main")
        == "main"
    )


def test_unknown_explicit_binding_does_not_fall_through(repo):
    payload = {"project_id": "ghost", "cwd": str(repo / "projects" / "p1")}
    assert resolve_project(payload, repo_root=repo, branch="projects/p1") is None


def test_unknown_branch_and_file_mtimes_do_not_guess(repo):
    os.utime(repo / "projects" / "p2", (2_000_000_000, 2_000_000_000))
    assert (
        resolve_project({"cwd": str(repo)}, repo_root=repo, branch="feat/other") is None
    )


def test_runtime_writes_versioned_atomic_session(repo, monkeypatch):
    data = _snap(
        repo,
        monkeypatch,
        model_id="claude-x",
        permission_mode="auto",
        source="startup",
        effort={"level": "high"},
    )
    assert data["schema_version"] == "2.0"
    assert data["project"] == "p1"
    assert len(data["sessions"]) == 1
    session = data["sessions"][0]
    assert session["session_id"] == "s1"
    assert session["agent"]["model_id"] == "claude-x"
    assert session["agent"]["effort"] == "high"
    assert session["activity"] == {"permission_mode": "auto", "source": "startup"}
    assert session["tenant"]


def test_new_session_never_inherits_prior_model_or_activity(repo, monkeypatch):
    _snap(
        repo,
        monkeypatch,
        session_id="s1",
        model_id="claude-x",
        effort="high",
        source="startup",
    )
    data = _snap(repo, monkeypatch, session_id="s2")
    first, second = data["sessions"]
    assert first["agent"]["model_id"] == "claude-x"
    assert "model_id" not in second["agent"]
    assert "effort" not in second["agent"]
    assert second["activity"] == {}


def _write_transcript(repo, records):
    path = repo / "projects" / "p1" / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
    return path


def test_model_and_permission_mode_recovered_from_transcript(repo, monkeypatch):
    # The real SessionStart payload carries neither; both live in the transcript.
    transcript = _write_transcript(
        repo,
        [
            {"type": "assistant", "message": {"model": "claude-opus-4-8"}},
            {"type": "permission-mode", "permissionMode": "bypassPermissions"},
        ],
    )
    data = _snap(repo, monkeypatch, transcript_path=str(transcript), source="startup")
    session = data["sessions"][0]
    assert session["agent"]["model_id"] == "claude-opus-4-8"
    assert session["activity"]["permission_mode"] == "bypassPermissions"


def test_transcript_model_reflects_latest_assistant_turn(repo, monkeypatch):
    # A mid-session /model switch: the last assistant turn is the model in effect.
    transcript = _write_transcript(
        repo,
        [
            {"type": "assistant", "message": {"model": "claude-opus-4-8"}},
            {"type": "assistant", "message": {"model": "claude-haiku-4-5"}},
        ],
    )
    data = _snap(repo, monkeypatch, transcript_path=str(transcript))
    assert data["sessions"][0]["agent"]["model_id"] == "claude-haiku-4-5"


def test_missing_or_empty_transcript_omits_model(repo, monkeypatch):
    # Fresh session with no turns yet — omit the model, never fabricate or crash.
    data = _snap(
        repo,
        monkeypatch,
        transcript_path=str(repo / "projects" / "p1" / "does-not-exist.jsonl"),
    )
    assert "model_id" not in data["sessions"][0]["agent"]


def test_payload_model_wins_over_transcript(repo, monkeypatch):
    transcript = _write_transcript(
        repo, [{"type": "assistant", "message": {"model": "claude-transcript"}}]
    )
    data = _snap(
        repo, monkeypatch, model_id="claude-payload", transcript_path=str(transcript)
    )
    assert data["sessions"][0]["agent"]["model_id"] == "claude-payload"


def test_same_session_is_idempotent_and_does_not_rewrite(repo, monkeypatch):
    monkeypatch.setattr("beril_cli.audit_cmd._now_iso", lambda: "2026-01-01T00:00:00Z")
    _snap(repo, monkeypatch, model_id="claude-x")
    path = repo / "projects" / "p1" / "runtime.json"
    first = path.read_text()
    monkeypatch.setattr("beril_cli.audit_cmd._now_iso", lambda: "2026-01-02T00:00:00Z")
    _snap(repo, monkeypatch, model_id="claude-x")
    assert path.read_text() == first


def test_same_session_changed_snapshot_replaces_atomically(repo, monkeypatch):
    _snap(repo, monkeypatch, model_id="claude-x", source="startup")
    data = _snap(repo, monkeypatch, model_id="claude-y")
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["agent"]["model_id"] == "claude-y"
    assert data["sessions"][0]["activity"] == {}


def test_runtime_requires_session_id(repo, monkeypatch):
    _stdin(monkeypatch, {"cwd": str(repo / "projects" / "p1")})
    assert run_runtime_snapshot(argparse.Namespace()) == 0
    assert not (repo / "projects" / "p1" / "runtime.json").exists()


def test_runtime_no_project_writes_nothing(repo, monkeypatch):
    _stdin(monkeypatch, {"session_id": "s1", "cwd": str(repo)})
    assert run_runtime_snapshot(argparse.Namespace()) == 0
    assert not (repo / "projects" / "p1" / "runtime.json").exists()
    assert not (repo / "projects" / "p2" / "runtime.json").exists()


def test_runtime_survives_malformed_stdin(repo, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json{"))
    assert run_runtime_snapshot(argparse.Namespace()) == 0


def test_documented_datasets_snapshot_is_hashed_and_session_scoped(repo, monkeypatch):
    report = (
        "# R\n\n## Data\n\n### Sources\n"
        "| Collection | Tables Used | Purpose |\n"
        "|---|---|---|\n"
        "| `kbase_ke_pangenome` | `genome`, `gene_cluster` | pangenome |\n"
    )
    (repo / "projects" / "p1" / "REPORT.md").write_text(report)
    session = _snap(repo, monkeypatch)["sessions"][0]
    snapshot = session["documented_datasets_snapshot"]
    assert (
        snapshot["report_hash"]
        == "sha256:" + hashlib.sha256(report.encode()).hexdigest()
    )
    assert snapshot["observed_at"] == session["observed_at"]
    assert snapshot["datasets"] == [
        {"collection": "kbase_ke_pangenome", "tables": ["genome", "gene_cluster"]}
    ]


def test_runtime_omits_dataset_snapshot_when_report_has_no_parseable_table(
    repo, monkeypatch
):
    assert "documented_datasets_snapshot" not in _snap(repo, monkeypatch)["sessions"][0]


def test_git_state_and_actor_are_inside_session_record(repo, monkeypatch):
    monkeypatch.setattr(
        "beril_cli.audit_cmd._git_info",
        lambda root, ignored_path=None: {"git_sha": "abc", "git_dirty": False},
    )
    monkeypatch.setenv("USER", "dkishore")
    (repo / "projects" / "p1" / "beril.yaml").write_text(
        'authors:\n  - orcid: "0009-0006-4046-889X"\n'
    )
    session = _snap(repo, monkeypatch)["sessions"][0]
    assert session["code"] == {"git_sha": "abc", "git_dirty": False}
    assert session["actor"] == {
        "user": "dkishore",
        "orcid": "0009-0006-4046-889X",
    }


def test_non_v2_runtime_file_is_replaced_with_fresh_v2_state(repo, monkeypatch):
    path = repo / "projects" / "p1" / "runtime.json"
    path.write_text(
        json.dumps({"project": "p1", "agent": {"model_id": "old-model"}}) + "\n"
    )
    data = _snap(repo, monkeypatch, session_id="new-session")
    assert data["schema_version"] == "2.0"
    assert "legacy_snapshot" not in data
    assert [s["session_id"] for s in data["sessions"]] == ["new-session"]



# --- agent cost ------------------------------------------------------------
#
# Scoped like the rest of this file: only what breaks *silently*. The stamp
# actually working end-to-end is proved in tests/test_statusline.py, which runs
# the real hook script — these cover the arithmetic and the honesty rules that a
# green in-process run would otherwise hide.


def _runtime(repo, project="p1"):
    return json.loads((repo / "projects" / project / "runtime.json").read_text())


def _yaml(repo, project="p1"):
    return (repo / "projects" / project / "beril.yaml").read_text()


def _set_status(repo, status, project="p1"):
    """Edit `status:` in place, the way a skill performing a transition does.

    Rewriting the whole manifest would silently wipe the ledger under test.
    """
    manifest = repo / "projects" / project / "beril.yaml"
    text = manifest.read_text()
    if re.search(r"^status:", text, re.MULTILINE):
        text = re.sub(
            r"^status:(\s*)[^\s#]+",
            rf"status:\g<1>{status}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        text += f"status: {status}\n"
    manifest.write_text(text)


def test_a_session_spanning_two_stages_is_never_counted_twice(repo, monkeypatch):
    """The core arithmetic. One session outlives the stage it started in, so
    each stage gets the spend earned inside it and the deltas sum to the total
    observed. A window over session start times would misattribute both."""
    _set_status(repo, "exploration")
    _snap(repo, monkeypatch)
    record_session_cost(repo / "projects" / "p1", "s1", 4.12)
    _set_status(repo, "proposed")
    _snap(repo, monkeypatch)
    record_session_cost(repo / "projects" / "p1", "s1", 9.80)  # same session
    _set_status(repo, "active")
    _snap(repo, monkeypatch)

    stages = re.findall(r"- stage: (\w+)\n.*?\n(?:      usd: ([\d.]+)\n)?", _yaml(repo))
    assert stages == [("exploration", "4.12"), ("proposed", "5.68")]


def test_an_unobserved_stage_omits_usd_rather_than_recording_zero(repo, monkeypatch):
    """`usd: 0.00` reads as "this stage was free". A missing key reads as
    "nobody watched", which is the true statement — and the same rule holds at
    the input side, where an unreported cost writes no `cost` key at all."""
    _set_status(repo, "exploration")
    _snap(repo, monkeypatch)
    record_session_cost(repo / "projects" / "p1", "s1", 0)  # harness reported none
    assert "cost" not in _runtime(repo)["sessions"][0]

    _set_status(repo, "proposed")
    _snap(repo, monkeypatch)
    text = _yaml(repo)
    assert "- stage: exploration" in text
    assert "sessions_observed: 0" in text
    assert "usd:" not in text


def test_a_snapshot_replace_carries_cost_forward(repo, monkeypatch):
    """The two writers of runtime.json must not clobber each other. Only the
    status line sees cost; only the hook sees the model. A re-snapshot replaces
    the whole record, so without this every model switch erased the spend."""
    _snap(repo, monkeypatch, session_id="s1", model="claude-opus-5")
    record_session_cost(repo / "projects" / "p1", "s1", 4.12)
    session = _snap(repo, monkeypatch, session_id="s1", model="claude-sonnet-5")[
        "sessions"
    ][0]
    assert session["agent"]["model_id"] == "claude-sonnet-5"
    assert session["cost"]["usd"] == 4.12


def test_the_ledger_leaves_the_rest_of_the_manifest_alone(repo, monkeypatch):
    """beril.yaml is a reviewed file carrying an authoritative approval block and
    inline comments. Appending to it by text is what avoids a YAML round-trip
    eating them — silently, in a file nobody re-reads after a transition."""
    manifest = repo / "projects" / "p1" / "beril.yaml"
    manifest.write_text(
        "project_id: p1\n"
        "status: exploration          # exploration | proposed | active\n"
        "approval:\n"
        '  by: "0000-0001-9076-6066"\n'
        "\n"
        "# trailing note about submissions\n"
        "submissions: []\n"
    )
    _snap(repo, monkeypatch)
    record_session_cost(repo / "projects" / "p1", "s1", 1.50)
    _set_status(repo, "proposed")
    _snap(repo, monkeypatch)

    text = manifest.read_text()
    assert "# exploration | proposed | active" in text
    assert "# trailing note about submissions" in text
    assert '  by: "0000-0001-9076-6066"' in text
    assert "submissions: []" in text
    assert "- stage: exploration" in text


def test_an_unchanged_cents_value_does_not_rewrite_runtime_json(repo, monkeypatch):
    """The status line renders every turn. Rewriting on each render would churn
    a file the hook also writes, for no new information."""
    _snap(repo, monkeypatch, session_id="s1")
    path = repo / "projects" / "p1" / "runtime.json"
    record_session_cost(repo / "projects" / "p1", "s1", 4.12)
    before = path.stat().st_mtime_ns
    record_session_cost(repo / "projects" / "p1", "s1", 4.1234)  # same cents
    assert path.stat().st_mtime_ns == before
    record_session_cost(repo / "projects" / "p1", "s1", 4.13)  # a cent more
    assert path.stat().st_mtime_ns != before


def test_audit_cmd_stays_off_the_cli_import_chain():
    """The hook falls back to a bare `python3` when there is no venv — the BERDL
    pod. `approve_cmd` reaches `tomllib` (3.11+) via its config import, and
    sourcing `block_span` from there made every stamp raise ModuleNotFoundError
    into this module's blanket `except`: no error, no stamp, on exactly the
    image the fallback exists for.

    The end-to-end test in test_statusline.py catches this for real, but only
    when the system python3 happens to be old. This one is deterministic.
    """
    source = Path(audit_cmd.__file__).read_text()
    reached = set(re.findall(r"^\s*from (beril_cli\.[\w.]+) import", source, re.MULTILINE))
    assert reached == {"beril_cli.project_resolution"}, (
        f"audit_cmd runs under the hook's bare-python3 fallback; {reached} may"
        " drag in tomllib/httpx and silently disable stage stamping"
    )
