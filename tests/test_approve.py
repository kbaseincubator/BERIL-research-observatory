"""Tests for `beril approve` — the human witness for the plan-review checkpoint.

The digest RULE (what a Revision History append does and does not invalidate)
is pinned end-to-end in `tests/test_plan_gate.py`, and
`test_plan_gate.py::test_digest_twins_agree` holds this module's `plan_digest`
to the hook's output over a plan with and without the heading, a section below
it, and CRLF. What is left to test here is what only this command does: refuse,
disclose, and record.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

import pytest

from beril_cli import approve_cmd
from beril_cli.approve_cmd import plan_digest, run_approve

PLAN = """# Research Plan

## Competing Hypotheses
- **H1**: gene loss tracks habitat breadth (reject if r < 0.3)

## Revision History
- **v1** (2026-07-28): Initial plan
"""

ORCID = "0000-0001-2345-6789"


class _FakeStdin:
    """Stand-in for sys.stdin: only `isatty` matters (input is monkeypatched)."""

    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """A repo root with one planned project, a TTY, and a configured ORCID."""
    (tmp_path / "PROJECT.md").write_text("# repo\n", encoding="utf-8")
    project = tmp_path / "projects" / "alpha"
    project.mkdir(parents=True)
    (project / "RESEARCH_PLAN.md").write_text(PLAN, encoding="utf-8")

    monkeypatch.setattr(approve_cmd, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "stdin", _FakeStdin(True))
    monkeypatch.setattr(approve_cmd.config, "load", lambda: {"user": {"orcid": ORCID}})
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    return project


def _ns(project: str = "alpha", relayed: bool = False) -> argparse.Namespace:
    return argparse.Namespace(project=project, relayed=relayed)


def _field(manifest_text: str, key: str) -> str:
    line = next(
        ln for ln in manifest_text.splitlines() if ln.strip().startswith(key + ":")
    )
    return line.split('"')[1]


# --------------------------------------------------------------------------- #
# refusals                                                                     #
# --------------------------------------------------------------------------- #


def _nothing(repo, monkeypatch):
    pass


def _no_tty(repo, monkeypatch):
    monkeypatch.setattr(sys, "stdin", _FakeStdin(False))


def _no_plan(repo, monkeypatch):
    (repo / "RESEARCH_PLAN.md").unlink()


def _no_orcid(repo, monkeypatch):
    monkeypatch.setattr(approve_cmd.config, "load", lambda: {})


def _malformed_orcid(repo, monkeypatch):
    monkeypatch.setattr(
        approve_cmd.config, "load", lambda: {"user": {"orcid": "not-an-orcid"}}
    )


def _answers_no(repo, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")


def _real_plan_outside_projects(repo, monkeypatch):
    """A genuine plan at `projects/../escape`, so the refusal is not just a miss."""
    outside = repo.parents[1] / "escape"
    outside.mkdir()
    (outside / "RESEARCH_PLAN.md").write_text(PLAN, encoding="utf-8")


@pytest.mark.parametrize(
    "setup,project,relayed,message",
    [
        # no TTY and no --relayed: still refuses, and the message tells the
        # agent reading it what to do if the user really did approve
        (_no_tty, "alpha", False, "--relayed"),
        (_no_plan, "alpha", False, "/research-plan"),
        (_no_orcid, "alpha", False, "No anonymous approvals"),
        # reported as CONFIGURED and diagnosed as malformed — a different
        # diagnosis from "none set", which is what an empty normalization means
        (_malformed_orcid, "alpha", False, "'not-an-orcid' is not a valid ORCID"),
        (_answers_no, "alpha", False, "nothing written"),
        (_real_plan_outside_projects, "../escape", False, "unknown project"),
        # `Path("..").name` is `".."`, so the name check alone lets this one
        # through where `../escape` is already caught
        (_nothing, "..", False, "unknown project"),
        # --relayed buys past the missing terminal and nothing else. The ORCID
        # check is the only one that runs *after* the flag has been acted on;
        # the plan and project checks run before it is ever read.
        (_no_orcid, "alpha", True, "No anonymous approvals"),
    ],
    ids=[
        "no-tty",
        "no-plan",
        "no-orcid",
        "malformed-orcid",
        "answered-no",
        "escapes-projects",
        "dotdot",
        "relayed-no-orcid",
    ],
)
def test_refusals_write_nothing(
    repo, tmp_path, capsys, monkeypatch, setup, project, relayed, message
):
    if relayed:
        # the real relayed case is an agent at a pipe, so the refusal under test
        # cannot be the missing-terminal one
        monkeypatch.setattr(sys, "stdin", _FakeStdin(False))
    setup(repo, monkeypatch)

    assert run_approve(_ns(project, relayed=relayed)) == 1

    captured = capsys.readouterr()
    assert message in captured.err + captured.out
    assert list(tmp_path.rglob("beril.yaml")) == []


# --------------------------------------------------------------------------- #
# the write                                                                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "configured,relayed,tty,via",
    [
        (ORCID, False, True, "terminal"),
        # `beril setup` stores whatever was typed, and this repo's house style is
        # the URL form: it must normalize, not hard-fail at the checkpoint
        (f"https://orcid.org/{ORCID}", False, True, "terminal"),
        (ORCID, True, False, "agent-relayed"),
        # --relayed asserts provenance, not the state of the pipe
        (ORCID, True, True, "agent-relayed"),
    ],
    ids=["bare", "url", "relayed", "relayed-at-a-tty"],
)
def test_records_the_approval_in_a_new_manifest(
    repo, capsys, monkeypatch, configured, relayed, tty, via
):
    """The record says which plan, who, and HOW the approval was obtained."""
    monkeypatch.setattr(
        approve_cmd.config, "load", lambda: {"user": {"orcid": configured}}
    )
    monkeypatch.setattr(sys, "stdin", _FakeStdin(tty))
    asked = []

    def answer(prompt=""):
        asked.append(prompt)
        return "y"

    monkeypatch.setattr("builtins.input", answer)

    assert run_approve(_ns(relayed=relayed)) == 0

    # nobody is at the far end of a pipe, so the relayed path never asks
    assert bool(asked) is not relayed
    manifest = (repo / "beril.yaml").read_text(encoding="utf-8")
    assert "project_id: alpha" in manifest
    assert "status: proposed" in manifest
    assert f'by: "{ORCID}"' in manifest
    assert f"  via: {via}\n" in manifest
    # exactly the shape the hook parses: a direct child of plan_approval, quoted,
    # `sha256:`-prefixed
    assert f'  plan_hash: "sha256:{plan_digest(PLAN.encode())}"' in manifest
    datetime.strptime(_field(manifest, "at"), "%Y-%m-%dT%H:%M:%SZ")
    if relayed:
        # a human reads this in the transcript: it has to say what was recorded
        out = capsys.readouterr().out
        assert "did not witness" in out
        assert "agent-relayed" in out


def test_discloses_plan_and_manifest_before_asking(repo, capsys, monkeypatch):
    """The human must see WHICH plan, in WHICH checkout, before answering.

    Read after the call, capsys cannot show ordering — deleting the disclosure
    entirely would still pass. So the prompt itself reports what had been printed
    by the time it was asked.
    """
    seen = {}

    def answer(prompt=""):
        seen["out"] = capsys.readouterr().out
        return "y"

    monkeypatch.setattr("builtins.input", answer)

    assert run_approve(_ns()) == 0

    assert str((repo / "RESEARCH_PLAN.md").resolve()) in seen["out"]
    assert str((repo / "beril.yaml").resolve()) in seen["out"]
    assert ORCID in seen["out"]


def test_reapproval_replaces_the_whole_old_block(repo):
    """Re-approving replaces the record, blank and comment lines included.

    Two `plan_approval:` keys are legal YAML that resolves to whichever came
    last, so a stacked block would leave the manifest claiming a hash nobody
    approved.
    """
    stale = "0" * 64
    (repo / "beril.yaml").write_text(
        "project_id: alpha\n"
        "title: Habitat breadth and gene loss\n"
        "plan_approval:\n"
        f'  by: "0000-0000-0000-0000"\n'
        "\n"
        "  # recorded by an older client\n"
        '  at: "2026-01-01T00:00:00Z"\n'
        f'  plan_hash: "sha256:{stale}"\n'
        "status: proposed\n",
        encoding="utf-8",
    )
    plan_path = repo / "RESEARCH_PLAN.md"
    plan_path.write_text(PLAN.replace("r < 0.3", "r < 0.5"), encoding="utf-8")

    assert run_approve(_ns()) == 0

    manifest = (repo / "beril.yaml").read_text(encoding="utf-8")
    assert manifest.count("plan_approval:") == 1
    assert manifest.count("plan_hash:") == 1
    assert stale not in manifest
    assert "older client" not in manifest
    assert (
        _field(manifest, "plan_hash") == f"sha256:{plan_digest(plan_path.read_bytes())}"
    )
    # the surrounding manifest survives — an existing manifest is appended to,
    # not rebuilt from project_id/status, which would drop every other key
    assert "project_id: alpha" in manifest
    assert "title: Habitat breadth and gene loss" in manifest
    assert "status: proposed" in manifest


def test_hashes_the_plan_after_the_answer(repo, monkeypatch):
    """TOCTOU: the record attests to the plan as it stood when the human said yes,
    not to bytes that may have been rewritten while the prompt sat open."""
    plan_path = repo / "RESEARCH_PLAN.md"
    edited = PLAN.replace("r < 0.3", "r < 0.5")

    def edit_then_confirm(prompt=""):
        plan_path.write_text(edited, encoding="utf-8")
        return "y"

    monkeypatch.setattr("builtins.input", edit_then_confirm)

    assert run_approve(_ns()) == 0

    manifest = (repo / "beril.yaml").read_text(encoding="utf-8")
    assert _field(manifest, "plan_hash") == f"sha256:{plan_digest(edited.encode())}"

