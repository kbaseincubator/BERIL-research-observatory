"""Tests for `beril state` / `beril whereami` subcommands."""

from __future__ import annotations

import argparse
import json
import os
import time

import pytest

from beril_cli import state_cmd
from beril_cli.state_cmd import run_state, run_whereami


@pytest.fixture()
def projects_root(tmp_path, monkeypatch):
    """Point the projects root at a temporary directory."""
    root = tmp_path / "projects"
    root.mkdir()
    monkeypatch.setattr(state_cmd, "PROJECTS_ROOT", root)
    return root


def _make_project(root, name: str, status: str = "exploration", claims=None) -> str:
    """Create a minimal project dir with a beril.yaml (and optional claims.json)."""
    proj = root / name
    proj.mkdir()
    (proj / "beril.yaml").write_text(
        f"project_id: {name}\nstatus: {status}\n", encoding="utf-8"
    )
    if claims is not None:
        (proj / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    return name


def _get_ns(project: str) -> argparse.Namespace:
    return argparse.Namespace(action="get", project=project)


def _set_ns(project: str, obj) -> argparse.Namespace:
    payload = obj if isinstance(obj, str) else json.dumps(obj)
    return argparse.Namespace(action="set", project=project, json=payload)


def _whereami_ns(project=None, reinject=False, json_flag=False) -> argparse.Namespace:
    return argparse.Namespace(project=project, reinject=reinject, json=json_flag)


# --------------------------------------------------------------------------- #
# state get                                                                   #
# --------------------------------------------------------------------------- #


def test_state_get_absent_returns_empty_object(projects_root, capsys):
    _make_project(projects_root, "alpha")
    rc = run_state(_get_ns("alpha"))
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out) == {}


def test_state_get_unknown_project_exits_2(projects_root, capsys):
    rc = run_state(_get_ns("ghost"))
    captured = capsys.readouterr()
    assert rc == 2
    assert "Unknown project" in captured.err


def test_state_get_returns_written_state(projects_root, capsys):
    _make_project(projects_root, "alpha")
    run_state(_set_ns("alpha", {"question": "Why?"}))
    capsys.readouterr()  # drain
    rc = run_state(_get_ns("alpha"))
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["question"] == "Why?"


# --------------------------------------------------------------------------- #
# state set — merge, clamp, derived core                                      #
# --------------------------------------------------------------------------- #


def test_state_set_bad_json_exits_2(projects_root, capsys):
    _make_project(projects_root, "alpha")
    rc = run_state(_set_ns("alpha", "{not json"))
    captured = capsys.readouterr()
    assert rc == 2
    assert "Invalid --json" in captured.err


def test_state_set_unknown_project_exits_2(projects_root, capsys):
    rc = run_state(_set_ns("ghost", {"question": "x"}))
    captured = capsys.readouterr()
    assert rc == 2
    assert "Unknown project" in captured.err


def test_state_set_merge_supplied_replaces_absent_preserved(projects_root, capsys):
    _make_project(projects_root, "alpha")
    run_state(_set_ns("alpha", {"question": "Q1", "assumptions": ["a1"]}))
    capsys.readouterr()
    # Supply only open_questions: question + assumptions must be preserved.
    rc = run_state(_set_ns("alpha", {"open_questions": ["o1"]}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["question"] == "Q1"  # preserved
    assert out["assumptions"] == ["a1"]  # preserved
    assert out["open_questions"] == ["o1"]  # supplied


def test_state_set_supplied_field_replaces_prior(projects_root, capsys):
    _make_project(projects_root, "alpha")
    run_state(_set_ns("alpha", {"assumptions": ["old1", "old2"]}))
    capsys.readouterr()
    rc = run_state(_set_ns("alpha", {"assumptions": ["new"]}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["assumptions"] == ["new"]  # replaced, not appended


def test_state_set_clamp_list_to_eight(projects_root, capsys):
    _make_project(projects_root, "alpha")
    nine = [f"q{i}" for i in range(9)]
    rc = run_state(_set_ns("alpha", {"open_questions": nine}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert len(out["open_questions"]) == 8


def test_state_set_clamp_entry_to_160(projects_root, capsys):
    _make_project(projects_root, "alpha")
    long_line = "x" * 300
    rc = run_state(_set_ns("alpha", {"open_questions": [long_line]}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert len(out["open_questions"][0]) == 160


def test_state_set_clamp_question_to_240(projects_root, capsys):
    _make_project(projects_root, "alpha")
    long_q = "y" * 500
    rc = run_state(_set_ns("alpha", {"question": long_q}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert len(out["question"]) == 240


def test_state_set_updated_at_present_and_iso_z(projects_root, capsys):
    _make_project(projects_root, "alpha")
    rc = run_state(_set_ns("alpha", {"question": "Q"}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert "updated_at" in out
    ts = out["updated_at"]
    assert ts.endswith("Z")
    # Parses as ISO-8601 (do NOT assert the exact value).
    from datetime import datetime

    datetime.fromisoformat(ts.replace("Z", "+00:00"))


def test_state_set_recomputes_derived_core_from_yaml(projects_root, capsys):
    _make_project(projects_root, "alpha", status="active")
    rc = run_state(_set_ns("alpha", {"question": "Q"}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["phase"] == "active"
    assert out["step"] == "analyze"
    assert out["project"] == "alpha"


def test_state_set_omits_claims_when_absent(projects_root, capsys):
    _make_project(projects_root, "alpha")
    rc = run_state(_set_ns("alpha", {"question": "Q"}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert "claims" not in out


def test_state_set_includes_claims_when_present(projects_root, capsys):
    claims = [
        {"status": "supported"},
        {"status": "refuted"},
        {"status": "open"},
    ]
    _make_project(projects_root, "alpha", claims=claims)
    rc = run_state(_set_ns("alpha", {"question": "Q"}))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["claims"] == {"total": 3, "supported": 1, "refuted": 1}


def test_state_set_persists_to_disk(projects_root):
    _make_project(projects_root, "alpha")
    run_state(_set_ns("alpha", {"question": "persisted?"}))
    written = json.loads(
        (projects_root / "alpha" / "research_state.json").read_text(encoding="utf-8")
    )
    assert written["question"] == "persisted?"


# --------------------------------------------------------------------------- #
# whereami                                                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "status, marker, next_fragment",
    [
        ("exploration", "▸explore", "/research-plan"),
        ("proposed", "▸plan", "/execute-plan"),
        ("active", "▸analyze", "discriminating query"),
        ("analysis", "▸review", "/berdl-review"),
        ("reviewed", "▸submit", "/submit"),
    ],
)
def test_whereami_breadcrumb_and_next_per_status(
    projects_root, capsys, status, marker, next_fragment
):
    _make_project(projects_root, "alpha", status=status)
    rc = run_whereami(_whereami_ns(project="alpha"))
    out = capsys.readouterr().out
    assert rc == 0
    assert marker in out
    assert next_fragment in out


def test_whereami_complete_shows_checkmark(projects_root, capsys):
    _make_project(projects_root, "alpha", status="complete")
    rc = run_whereami(_whereami_ns(project="alpha"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "✓" in out
    assert "/suggest-research" in out


def test_whereami_resolves_by_mtime(projects_root, capsys):
    _make_project(projects_root, "older", status="active")
    _make_project(projects_root, "newer", status="proposed")
    # Make "older" genuinely older, "newer" most-recently-touched.
    now = time.time()
    os.utime(projects_root / "older" / "beril.yaml", (now - 100, now - 100))
    os.utime(projects_root / "newer" / "beril.yaml", (now, now))
    rc = run_whereami(_whereami_ns(json_flag=True))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["project"] == "newer"


def test_whereami_mtime_skips_complete(projects_root, capsys):
    _make_project(projects_root, "done_proj", status="complete")
    _make_project(projects_root, "live_proj", status="active")
    now = time.time()
    # complete project is the most recently touched but must be skipped.
    os.utime(projects_root / "done_proj" / "beril.yaml", (now, now))
    os.utime(projects_root / "live_proj" / "beril.yaml", (now - 100, now - 100))
    rc = run_whereami(_whereami_ns(json_flag=True))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["project"] == "live_proj"


def test_whereami_no_project_resolves_exits_0_with_note(projects_root, capsys):
    # Empty projects root -> nothing resolves.
    rc = run_whereami(_whereami_ns())
    out = capsys.readouterr().out
    assert rc == 0
    assert "No active project" in out


def test_whereami_no_project_json_exits_0_empty(projects_root, capsys):
    rc = run_whereami(_whereami_ns(json_flag=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out) == {}


def test_whereami_reinject_emits_guard_block(projects_root, capsys):
    _make_project(projects_root, "alpha", status="active")
    rc = run_whereami(_whereami_ns(project="alpha", reinject=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "orientation only, NOT established findings" in out
    assert "re-run checks before asserting any result as settled" in out


def test_whereami_reinject_writes_the_core(projects_root):
    _make_project(projects_root, "alpha", status="active")
    state_path = projects_root / "alpha" / "research_state.json"
    assert not state_path.exists()
    run_whereami(_whereami_ns(project="alpha", reinject=True))
    written = json.loads(state_path.read_text(encoding="utf-8"))
    assert written["phase"] == "active"
    assert written["step"] == "analyze"
    assert "updated_at" in written


def test_whereami_reinject_preserves_existing_world_model(projects_root, capsys):
    _make_project(projects_root, "alpha", status="active")
    run_state(_set_ns("alpha", {"question": "kept?", "dead_ends": ["d1"]}))
    capsys.readouterr()
    run_whereami(_whereami_ns(project="alpha", reinject=True))
    out = capsys.readouterr().out
    assert "kept?" in out
    written = json.loads(
        (projects_root / "alpha" / "research_state.json").read_text(encoding="utf-8")
    )
    assert written["question"] == "kept?"
    assert written["dead_ends"] == ["d1"]


def test_whereami_reinject_no_project_silent_exit_0(projects_root, capsys):
    rc = run_whereami(_whereami_ns(reinject=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert out == ""  # stays silent so the SessionStart hook adds no context


def test_whereami_default_shows_open_questions_and_dead_ends(projects_root, capsys):
    _make_project(projects_root, "alpha", status="active")
    run_state(_set_ns("alpha", {"open_questions": ["oq1"], "dead_ends": ["de1"]}))
    capsys.readouterr()
    rc = run_whereami(_whereami_ns(project="alpha"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "oq1" in out
    assert "de1" in out
