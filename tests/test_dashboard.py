"""Tests for `tools.dashboard` — the live in-progress project dashboard.

Design: docs/live-dashboard-design.md.

Scoped deliberately. Two things earn a test here: the honesty rules (the page
must never assert a stage, an approval or a review it cannot back with something
on disk) and the five bugs that actually occurred during development, each
marked REGRESSION. Cosmetic rendering is not tested — it is visible.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Allow `import tools.dashboard` from the repo-root tests/ directory.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.dashboard import (  # noqa: E402
    _cost_readout,
    _rail,
    agent_cost,
    jupyter_python,
    _approval_chip,
    count_deviations,
    main,
    notebook_stats,
    parse_worklog,
    plan_approval,
    plan_digest,
    render,
    resolve_stage,
    review_docs,
    scan,
)

# The RESEARCH_PLAN.md template always ships a Revision History section. That
# matters: the canonical digest covers everything above the heading *including*
# the newline before it, so adding the section changes the digest while
# appending an entry under it does not.
PLAN_BODY = "# Plan\n\nH1: metal tolerance tracks copA copy number.\n\n"
PLAN = PLAN_BODY + "## Revision History\n\n- **v1** (2026-07-28): first draft\n"
PLAN_V2 = PLAN + "- **v2** (2026-07-29): added a no-metal control\n"
PLAN_MATERIAL_EDIT = PLAN.replace("copA", "copB")

NB_OK = json.dumps(
    {
        "cells": [
            {"cell_type": "code", "outputs": [{"output_type": "stream"}]},
            {"cell_type": "code", "outputs": [{"output_type": "error", "ename": "V"}]},
            {"cell_type": "markdown"},
        ]
    }
)
NB_NO_OUTPUT = json.dumps({"cells": [{"cell_type": "code", "outputs": []}]})

WORKLOG = """# Worklog — demo

## 2026-02-18 · plan written → proposed
Rejected a pure TnSeq cutoff — no orthogonal check.
→ [RESEARCH_PLAN.md](RESEARCH_PLAN.md)

## 2026-02-18 · essentiality vectors built
Dropped 412 genes absent from the FBA model.
→ [fig](figures/overview.png) ×2

## 2026-02-19 · COG parsing bug
Wrong delimiter. Re-ran 02.
→ [gone](figures/deleted.png)
"""


def _project(tmp_path: Path, files: dict = None, name: str = "demo") -> Path:
    project = tmp_path / name
    (project / "notebooks").mkdir(parents=True)
    (project / "figures").mkdir()
    for rel, body in (files or {}).items():
        target = project / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return project


def _approve(project: Path, digest: str) -> None:
    (project / "beril.yaml").write_text(
        "project_id: demo\nstatus: active\nplan_approval:\n"
        '  by: "0000-0002-4999-2931"\n  at: "2026-07-28T10:00:00Z"\n'
        f'  plan_hash: "sha256:{digest}"\n'
    )


# --------------------------------------------------------------------------
# Stage — the page must never assert a stage it cannot back
# --------------------------------------------------------------------------


def test_stage_inferred_from_filesystem_when_no_manifest(tmp_path):
    """61 of 78 projects have no beril.yaml. Inference is the normal path."""
    project = _project(tmp_path)
    assert resolve_stage(project) == ("exploration", True)

    (project / "RESEARCH_PLAN.md").write_text(PLAN)
    assert resolve_stage(project) == ("proposed", True)

    # A notebook with no saved outputs has not run — it must not imply `active`.
    (project / "notebooks" / "01.ipynb").write_text(NB_NO_OUTPUT)
    assert resolve_stage(project) == ("proposed", True)

    (project / "notebooks" / "01.ipynb").write_text(NB_OK)
    assert resolve_stage(project) == ("active", True)

    (project / "REPORT.md").write_text("# Report\n")
    assert resolve_stage(project) == ("analysis", True)

    (project / "REVIEW_1.md").write_text("# Review\n")
    assert resolve_stage(project) == ("reviewed", True)

    (project / "SUBMITTED.md").write_text("archived\n")
    assert resolve_stage(project) == ("complete", True)


def test_manifest_wins_and_only_approval_grants_complete(tmp_path):
    project = _project(tmp_path, {"RESEARCH_PLAN.md": PLAN})

    (project / "beril.yaml").write_text("project_id: demo\nstatus: active\n")
    assert resolve_stage(project) == ("active", False)

    # `plan_approval` is the checkpoint witness, NOT the submission approval.
    (project / "beril.yaml").write_text(
        'status: active\nplan_approval:\n  by: "0000-0002"\n'
    )
    assert resolve_stage(project) == ("active", False)

    (project / "beril.yaml").write_text(
        'status: reviewed\napproval:\n  by: "0000-0002-4999-2931"\n'
    )
    assert resolve_stage(project) == ("complete", False)


# --------------------------------------------------------------------------
# Plan approval — the witness `status` does not provide
# --------------------------------------------------------------------------


def test_module_level_imports_are_all_stdlib():
    """The pod launches this with a bare `python3` and no install, so every
    third-party import has to stay *inside* a function behind a try/except. A
    top-level `import mistune` would still pass the whole suite here — the test
    venv has it — and then fail to start on any image that doesn't. The PEP 723
    header serves `uv run` off-cluster; it does nothing for the pod path.
    """
    import ast

    tree = ast.parse((ROOT / "tools" / "dashboard.py").read_text(encoding="utf-8"))
    top_level = []
    for node in tree.body:  # module body only — nested imports are the escape hatch
        if isinstance(node, ast.Import):
            top_level += [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            top_level.append(node.module.split(".")[0])

    third_party = sorted(set(top_level) - sys.stdlib_module_names - {"__future__"})
    assert not third_party, (
        f"tools/dashboard.py imports {third_party} at module level; the pod runs it "
        "with a bare python3, so these must move inside a guarded import"
    )


def test_plan_summary_extracts_orientation_and_counts_only(tmp_path):
    """The question and hypothesis are what anchor the worklog below them, and
    both heading spellings occur across the 73 plans on disk.

    `planned_notebooks` is a count, never a mapping. Plan section numbers do not
    correspond to filenames — measured: one plan's "Notebook 1" is
    `00_inventory_audit.ipynb`, another's is `02_essential_families.ipynb`,
    notebooks get renamed after the plan freezes and unplanned ones appear. A
    per-notebook done/not-done would be confidently wrong.
    """
    from tools.dashboard import plan_summary

    project = _project(tmp_path, {"RESEARCH_PLAN.md": (
        "# Plan\n\n## Research Question\nDoes copA copy number track tolerance?\n\n"
        "## Hypotheses\nH1: yes, monotonically.\n\n"
        "## Expected Outcomes\nSupported if OR > 2 across both cohorts.\n\n"
        "## Analysis Plan\n### Notebook 1: cohort\n### Notebook 2: scoring\n\n"
        "## Revision History\n- v1\n"
    )})
    s = plan_summary(project)
    assert s["question"] == "Does copA copy number track tolerance?"
    assert s["hypothesis"] == "H1: yes, monotonically."
    assert s["outcomes"] == "Supported if OR > 2 across both cohorts."
    assert s["planned_notebooks"] == 2
    # The Revision History heading must not bleed into the section above it.
    assert "v1" not in s["hypothesis"]

    # Singular spelling, and a plan with no analysis plan at all.
    other = _project(tmp_path, {"RESEARCH_PLAN.md":
                                "## Hypothesis\nH1: singular heading.\n"}, name="b")
    s2 = plan_summary(other)
    assert s2["hypothesis"] == "H1: singular heading."
    assert s2["question"] == ""
    assert s2["planned_notebooks"] == 0

    assert plan_summary(_project(tmp_path, name="c")) == {}


def test_plan_digest_excises_the_section_not_the_tail():
    """REGRESSION, and the reason the twin test below was not enough.

    The canonical rule removes the Revision History *section* and keeps whatever
    follows it. Truncating from the heading to EOF agrees on any plan where
    Revision History happens to be last — which every fixture in the twin test
    was — and disagrees on **53 of the 73 real plans on disk**, all of which have
    `## Authors` after it. The #305 plan template puts Authors last too, so every
    future plan would have diverged as well.

    Pinned by restating the rule here rather than by importing beril_cli, so this
    is red on `main` today instead of waiting for #305 to make it runnable.
    """
    body = b"# Plan\n\nH1: copA copy number.\n\n"
    revhist = b"## Revision History\n\n- v1\n\n"
    authors = b"## Authors\n\n- Arkin\n"

    assert plan_digest(body + revhist + authors) == (
        hashlib.sha256(body + authors).hexdigest()
    )
    # Revision History last -> nothing follows to keep; both rules coincide here,
    # which is precisely why this case could not catch the bug.
    assert plan_digest(body + revhist) == hashlib.sha256(body).hexdigest()
    # No Revision History at all -> the whole file.
    assert plan_digest(body) == hashlib.sha256(body).hexdigest()
    # Bytes, not text: read_text would translate CRLF and change the digest.
    assert plan_digest(b"# Plan\r\n") != plan_digest(b"# Plan\n")


def test_plan_digest_is_a_twin_of_beril_approve():
    """REGRESSION guard. tools/dashboard.py cannot import beril_cli (bare python3
    in an ephemeral pod), so this is the only thing between a copied function and
    silent drift. Skips until feat/planning-workflow lands, then enforces."""
    approve_cmd = pytest.importorskip(
        "beril_cli.approve_cmd", reason="feat/planning-workflow not merged yet"
    )
    for raw in (
        PLAN.encode(),
        PLAN_V2.encode(),
        b"",
        b"# Plan\r\n\r\nH1\r\n",
        # The case the original four missed: a section after Revision History.
        # Every real plan on disk has one, and so does the #305 template.
        (PLAN + "\n## Authors\n\n- Arkin\n").encode(),
    ):
        assert plan_digest(raw) == approve_cmd.plan_digest(raw)


def test_plan_approval_states(tmp_path, monkeypatch):
    import tools.dashboard as dash

    project = _project(tmp_path, {"RESEARCH_PLAN.md": PLAN})

    # REGRESSION: without the plan-gate machinery there is no such thing as an
    # unapproved plan. All 78 projects on disk predate it and were being flagged
    # `plan not approved` — a false accusation on every finished project.
    monkeypatch.setattr(dash, "_planning_workflow_installed", lambda: False)
    assert plan_approval(project, "active")["state"] == "na"

    # No block, machinery present: only an assertion once past the checkpoint.
    monkeypatch.setattr(dash, "_planning_workflow_installed", lambda: True)
    (project / "beril.yaml").write_text("status: active\n")
    assert plan_approval(project, "active")["state"] == "missing"
    assert plan_approval(project, "proposed")["state"] == "na"

    # REGRESSION: gating on repo-wide machinery alone only deferred the false
    # accusation. Simulated, the day the plan-gate lands all 78 projects flipped
    # to `plan not approved`, 17 of them already complete. A finished project
    # with no deviation record predates the gate and must stay silent...
    assert plan_approval(project, "reviewed")["state"] == "na"
    assert plan_approval(project, "complete")["state"] == "na"
    # ...unless the hook actually logged a write under no valid approval, which
    # is proof the gate was watching.
    (project / "plan_deviations.jsonl").write_text('{"path":"notebooks/01.ipynb"}\n')
    assert plan_approval(project, "complete")["state"] == "missing"
    (project / "plan_deviations.jsonl").unlink()

    _approve(project, plan_digest(PLAN.encode()))
    approved = plan_approval(project, "active")
    assert approved["state"] == "approved"
    assert approved["by"] == "0000-0002-4999-2931"

    # A Revision History append keeps the approval; a material edit breaks it.
    (project / "RESEARCH_PLAN.md").write_text(PLAN_V2)
    assert plan_approval(project, "active")["state"] == "approved"
    (project / "RESEARCH_PLAN.md").write_text(PLAN_MATERIAL_EDIT)
    assert plan_approval(project, "active")["state"] == "stale"

    # `beril approve --relayed` records that the agent, not a human at a TTY,
    # recorded the approval. Rendering both as a green tick overstates the weaker.
    (project / "RESEARCH_PLAN.md").write_text(PLAN)
    assert plan_approval(project, "active")["via"] == ""
    assert "relayed" not in _approval_chip(plan_approval(project, "active"))
    (project / "beril.yaml").write_text(
        (project / "beril.yaml").read_text().replace(
            "  plan_hash:", "  via: agent-relayed\n  plan_hash:")
    )
    assert "relayed" in _approval_chip(plan_approval(project, "active"))


def test_plan_reviews_are_listed_and_chipped_against_the_plan(tmp_path):
    """`glob("REVIEW*.md")` is anchored, so it never matched `PLAN_REVIEW_1.md` —
    the file `/berdl_start`'s plan-review checkpoint option (b) tells the operator
    to produce. The default path through the workflow generated a document
    § Documents could not see.

    Each family is chipped against its own subject, so a plan review must not go
    stale merely because REPORT.md changed, and vice versa.
    """
    project = _project(tmp_path, {
        "RESEARCH_PLAN.md": "# Plan\n\n## Research Question\nQ?\n",
        "REPORT.md": "# Report\n\nFindings.\n",
    })
    plan_sha = hashlib.sha256((project / "RESEARCH_PLAN.md").read_bytes()).hexdigest()
    report_sha = hashlib.sha256((project / "REPORT.md").read_bytes()).hexdigest()

    (project / "PLAN_REVIEW_1.md").write_text(f"<!-- plan_hash: sha256:{plan_sha} -->\n")
    (project / "PLAN_REVIEW_2.md").write_text("<!-- plan_hash: sha256:dead -->\n")
    (project / "REVIEW_1.md").write_text(f"<!-- report_hash: sha256:{report_sha} -->\n")

    chips = {doc.name: doc.chip for doc in review_docs(project)}
    assert chips == {
        "PLAN_REVIEW_1.md": "current",
        "PLAN_REVIEW_2.md": "stale",
        "REVIEW_1.md": "current",
    }

    # A plan review is checked against the plan only. Rewriting REPORT.md must
    # not touch it, or every plan review would go stale at synthesis time.
    (project / "REPORT.md").write_text("# Report\n\nRevised.\n")
    after = {doc.name: doc.chip for doc in review_docs(project)}
    assert after["PLAN_REVIEW_1.md"] == "current"
    assert after["REVIEW_1.md"] == "stale"

    # The deviation count rides along here: it is the other number § Documents
    # prints, and no other test in this file is sensitive to it. A blank
    # trailing line is not a deviation.
    assert count_deviations(project) == 0
    (project / "plan_deviations.jsonl").write_text('{"path":"a"}\n{"path":"b"}\n\n')
    assert count_deviations(project) == 2


def test_plan_review_chip_matches_review_sh_not_plan_digest(tmp_path):
    """`review.sh` line 130 writes `sha256sum` of the *whole* RESEARCH_PLAN.md.
    `plan_digest` deliberately excludes `## Revision History` so a revision bump
    does not void a human's approval. Checking a plan review against the digest
    instead of the file would mark every one of them stale forever.
    """
    plan = "# Plan\n\n## Research Question\nQ?\n\n## Revision History\n- v1\n"
    project = _project(tmp_path, {"RESEARCH_PLAN.md": plan})
    raw = (project / "RESEARCH_PLAN.md").read_bytes()

    assert plan_digest(raw) != hashlib.sha256(raw).hexdigest(), (
        "fixture must exercise the divergence, or this test proves nothing")

    (project / "PLAN_REVIEW_1.md").write_text(
        f"<!-- plan_hash: sha256:{hashlib.sha256(raw).hexdigest()} -->\n")
    assert review_docs(project)[0].chip == "current"

    (project / "PLAN_REVIEW_1.md").write_text(
        f"<!-- plan_hash: sha256:{plan_digest(raw)} -->\n")
    assert review_docs(project)[0].chip == "stale"


def test_notebook_tally_never_reads_as_a_fraction(tmp_path):
    """Phase A mandates an exploration notebook the plan template never lists, so
    written > planned is the normal steady state, not an error. Leading with the
    plan count put the two numbers in an n/m relationship and made a correct
    tally look wrong.
    """
    page = _render(tmp_path, {
        # A Research Question is required or the whole plan block, tally
        # included, is omitted (see _plan_html).
        "RESEARCH_PLAN.md": "# Plan\n\n## Research Question\nQ?\n\n"
                            "## Analysis Plan\n\n"
                            "### Notebook 1: A\n\n### Notebook 2: B\n",
        # Three on disk against two in the plan: the exploration notebook is the
        # one Phase A adds and the plan never names.
        "notebooks/00_exploration.ipynb": NB_OK,
        "notebooks/01_a.ipynb": NB_OK,
        "notebooks/02_b.ipynb": NB_NO_OUTPUT,
    })
    assert "3 written &middot; 2 executed &middot; plan lists 2" in page
    # The old ordering is what made "3 written" against "2 planned" read as 3/2.
    assert "2 planned" not in page


# --------------------------------------------------------------------------
# Reading the project
# --------------------------------------------------------------------------


def test_parse_worklog(tmp_path):
    """Also pins the `!` correction marker: it is the only thing separating the
    entries that record a change of direction from "ran notebook 3", and it must
    not swallow a `→ status` transition."""
    project = _project(tmp_path, {"figures/overview.png": "x"})
    entries = parse_worklog(WORKLOG, project)

    assert [e.title for e in entries] == [
        "plan written",
        "essentiality vectors built",
        "COG parsing bug",
    ]
    # A transition carries the new status; a work unit does not.
    assert entries[0].new_status == "proposed"
    assert entries[1].new_status is None
    # Links are lifted out of the prose, counted, and checked against disk.
    assert "RESEARCH_PLAN.md" not in entries[0].prose
    assert entries[1].links[0].count == 2
    assert entries[1].links[0].exists is True
    assert entries[2].links[0].exists is False

    fix, routine, demote = parse_worklog(
        "## 2026-07-29 · ! COG bug\nRe-ran 02.\n\n"
        "## 2026-07-29 · NB03 executed\nRoutine.\n\n"
        "## 2026-07-29 · ! plan revised → proposed\nDropped H2.\n",
        project,
    )
    assert (fix.correction, fix.title) == (True, "COG bug")
    assert routine.correction is False
    assert (demote.correction, demote.title, demote.new_status) == (
        True, "plan revised", "proposed",
    )


def test_notebook_stats_and_partial_writes(tmp_path):
    """A partial read while the agent writes the notebook is routine, not
    exceptional — the caller renders a placeholder and self-heals next poll."""
    project = _project(tmp_path, {"notebooks/01.ipynb": NB_OK})
    stats = notebook_stats(project / "notebooks" / "01.ipynb")
    assert (stats.cells, stats.with_output, stats.errors) == (3, 2, 1)

    (project / "notebooks" / "02.ipynb").write_text('{"cells": [{"cell_ty')
    assert notebook_stats(project / "notebooks" / "02.ipynb") is None


def test_scan_and_etag(tmp_path):
    project = _project(
        tmp_path,
        {
            "REPORT.md": "# Report\n",
            "notebooks/01.ipynb": NB_OK,
            "notebooks/.ipynb_checkpoints/01-checkpoint.ipynb": NB_OK,
            "figures/a.png": "x",
            "data/out.csv": "a,b\n",
            "WORKLOG.md": WORKLOG,
        },
        name="adp1",
    )
    state = scan(project)
    assert state.project_id == "adp1"
    assert state.stage == "analysis"
    assert [nb.name for nb in state.notebooks] == ["01.ipynb"]  # checkpoints excluded
    assert len(state.entries) == 3

    # The ETag drives the 304 path, so it must move iff the page would.
    first = scan(project).etag
    assert scan(project).etag == first
    (project / "REPORT.md").write_text("# Report\n\nmore\n")
    assert scan(project).etag != first


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------


def _render(tmp_path, files=None, name="demo") -> str:
    return render(scan(_project(tmp_path, files, name)), css="body{}")


def test_render_has_no_absolute_urls(tmp_path):
    """REGRESSION. /proxy/<port>/ strips the prefix, so an absolute URL breaks
    only inside JupyterHub and never on a developer's machine."""
    html = _render(
        tmp_path,
        {
            "WORKLOG.md": WORKLOG,
            "RESEARCH_PLAN.md": PLAN,
            "figures/a.png": "x",
            "notebooks/01.ipynb": NB_OK,
            "data/out.csv": "a,b\n",
        },
    )
    assert 'href="/' not in html
    assert 'src="/' not in html


def test_inline_md_renders_emphasis_and_escapes_first(tmp_path):
    """Worklog and plan text is markdown; rendering it flat left literal `**` and
    backticks on the page. Only the three constructs that actually occur are
    supported (bold 62/72 projects, italic 21, code 14).

    Escaping runs BEFORE the patterns, so the only tags this can emit are its
    own three. That ordering is the whole safety argument.
    """
    from tools.dashboard import inline_md

    assert inline_md("a **b** c") == "a <strong>b</strong> c"
    assert inline_md("in *Acinetobacter* sp.") == "in <em>Acinetobacter</em> sp."
    assert inline_md("use `ncbi_env` here") == "use <code>ncbi_env</code> here"

    # A `*` inside a code span is literal, not emphasis.
    assert inline_md("`a * b`") == "<code>a * b</code>"
    # ...and emphasis may still span a code span. Real prose from two projects;
    # an earlier split-on-code-first version left both `**` unmatched here.
    assert inline_md("**count in `bakta` here**") == (
        "<strong>count in <code>bakta</code> here</strong>"
    )
    # Bold wins over italic; no stray <em> from the inner pair.
    assert inline_md("**x**") == "<strong>x</strong>"

    # Injection is neutralised before any pattern runs.
    assert inline_md("<script>alert(1)</script>") == (
        "&lt;script&gt;alert(1)&lt;/script&gt;"
    )
    assert "<img" not in inline_md("*<img src=x onerror=1>*")

    html = _render(tmp_path, {"WORKLOG.md":
                              "## 2026-07-29 · nb run\n**Dropped** 412 `genes`.\n"})
    assert "<strong>Dropped</strong>" in html and "<code>genes</code>" in html


def test_render_escapes_agent_authored_text(tmp_path):
    """The agent writes the worklog. This is a trust boundary."""
    evil = "## 2026-07-28 · <script>alert(1)</script>\nprose <img src=x onerror=1>\n"
    html = _render(tmp_path, {"WORKLOG.md": evil})
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x onerror" not in html
    assert "&lt;script&gt;" in html


def test_render_states_what_it_cannot_prove(tmp_path, monkeypatch):
    """Every honesty rule in one place: inferred stage, unapproved plan, an
    unresolvable worklog link, a notebook that errored, and a client-side
    timestamp (a server-rendered one freezes on 304, leaving a green 'alive' dot
    on a wedged agent)."""
    html = _render(
        tmp_path,
        {
            "RESEARCH_PLAN.md": PLAN,
            "REPORT.md": "# R\n",
            "WORKLOG.md": WORKLOG,
            "notebooks/01.ipynb": NB_OK,
        },
    )
    assert "inferred from files" in html
    assert "missing" in html
    assert "1 error" in html

    import tools.dashboard as dash
    monkeypatch.setattr(dash, "_planning_workflow_installed", lambda: True)
    assert "not approved" in _render(
        tmp_path, {"RESEARCH_PLAN.md": PLAN, "beril.yaml": "status: active\n"}, "u"
    )
    assert "data-epoch=" in html

    assert "No worklog entries yet" in _render(tmp_path, name="empty")


# --------------------------------------------------------------------------
# Serving
# --------------------------------------------------------------------------


def test_live_mode_needs_the_proxy_only_inside_jupyterhub(tmp_path, monkeypatch):
    """REGRESSION. The proxy probe gated all live serving, so the dashboard
    refused to run on a laptop, where 127.0.0.1:<port> is directly reachable."""
    import tools.dashboard as dash

    monkeypatch.setattr(dash, "proxy_enabled", lambda: False)

    # The project is kept INSIDE the server root throughout, so the only variable
    # is the prefix — otherwise `jupyter_routes` returns None for the unrelated
    # reason that the path escapes root_dir, and the assertion proves nothing.
    monkeypatch.setenv("JUPYTER_SERVER_ROOT", str(tmp_path))
    project = tmp_path / "demo"

    monkeypatch.delenv("JUPYTERHUB_SERVICE_PREFIX", raising=False)
    assert dash.can_serve_live() is True
    assert dash.public_url(8742) == "http://127.0.0.1:8742/"
    # Same split for document links: off-cluster there is no Jupyter to open a
    # file in, so they must stay relative. Kept because this is the one direction
    # that cannot be checked by clicking around inside JupyterHub.
    assert dash.jupyter_routes(project) is None

    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/dkishore/")
    assert dash.can_serve_live() is False
    assert dash.public_url(8742) == "https://hub.berdl.kbase.us/user/dkishore/proxy/8742/"
    assert dash.jupyter_routes(project) is not None


def test_the_snapshot_url_is_root_relative(tmp_path, monkeypatch):
    """REGRESSION. Jupyter's `files/` route resolves against root_dir, so an
    absolute path after it yields `files//home/<user>/...`, which the server reads
    as `<root_dir>/home/<user>/...` and answers 404. Measured against the running
    server: 200 for the relative form, 404 for the absolute one.

    It broke the fallback in precisely the case where the fallback is all the user
    has — no proxy, so no live mode, and the one printed link is dead.
    """
    import tools.dashboard as dash

    monkeypatch.setenv("JUPYTER_SERVER_ROOT", str(tmp_path))
    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/bill/")
    project = tmp_path / "repo" / "projects" / "demo"
    project.mkdir(parents=True)

    url = dash.snapshot_url(project)

    assert url == (
        "https://hub.berdl.kbase.us/user/bill/files/"
        "repo/projects/demo/dashboard.html"
    )
    assert "files//" not in url, "absolute path after files/ — this is the 404"
    assert str(tmp_path) not in url, "leaked a filesystem path into the URL"


def test_a_snapshot_carries_neither_the_redirect_nor_the_poll(tmp_path):
    """REGRESSION, and the more dangerous half is the redirect.

    POLL_JS opens by appending a trailing slash so relative assets resolve under
    `/proxy/<port>/`. A snapshot is served at `<prefix>files/<rel>/dashboard.html`,
    which has no trailing slash — so on load the page would navigate itself to
    `dashboard.html/` and 404. It would destroy itself in front of the user.

    The poll is merely futile: `files/` responses carry `sandbox allow-scripts`
    with no `allow-same-origin`, so the document's origin is opaque and `fetch`
    cannot send the hub cookie.

    REL_JS must survive both cuts: every timestamp renders client-side, so
    dropping it leaves the readouts blank.
    """
    import tools.dashboard as dash

    project = _project(tmp_path, {"WORKLOG.md": WORKLOG})
    state = dash.scan(project)

    live = dash.render(state, "", live=True)
    snap = dash.render(state, "", live=False)

    assert "location.replace" in live and "function tick" in live
    assert "location.replace" not in snap, "the snapshot would navigate itself to a 404"
    assert "function tick" not in snap, "a poll that can only fail, silently"
    assert "function relTimes" in snap, "timestamps are client-side — this must stay"


def test_a_snapshot_says_it_is_one_and_how_to_get_live(tmp_path):
    """The instructions used to be five lines on stdout, which the status line
    redirected into a gitignored `.dash.log`. Nobody had a reason to open it, so
    the observed failure was a dashboard that silently never appeared.

    They belong on the page the reader is actually looking at, and the command
    must be the checkout's — `beril` on the image is a pinned copy under an
    overlay mount that a user cannot update.
    """
    import tools.dashboard as dash

    project = _project(tmp_path, {"WORKLOG.md": WORKLOG})
    state = dash.scan(project)

    assert '<div class="d-setup">' not in dash.render(state, "", live=True)

    snap = dash.render(state, "", live=False)
    assert '<div class="d-setup">' in snap
    assert dash.SETUP_CMD in snap
    # Was the reverse: the banner deliberately avoided `beril`, because the image
    # ships a pinned copy under /opt/conda that could predate this feature. That is
    # being fixed by shipping a newer beril, so one entry point beats two.
    assert "beril setup" in snap and "tools/dashboard.py --setup" not in snap
    for step in dash.RESTART_STEPS:
        assert dash.inline_md(step) in snap, f"missing restart step: {step}"


def _waiting(project: Path, **over) -> Path:
    """Drop an `.agent-state.json` shaped like the hook's own output."""
    import time as _time

    record = {
        "state": "waiting",
        "detail": "Bash: sw_vers",
        "since": _time.time(),
        "session_id": "sess-1",
    }
    record.update(over)
    (project / ".agent-state.json").write_text(json.dumps(record), encoding="utf-8")
    return project


def test_the_waiting_detail_is_escaped_like_every_other_agent_string(tmp_path):
    """Same trust boundary as the worklog, and it moved: this string is a tool
    argument the agent chose, or a question it wrote, and it lands in HTML.

    It goes through `inline_md` for the same reason the worklog prose does —
    agents write backticks — and `inline_md` escapes *first*, so the only tags
    that can survive are the three it emits itself.
    """
    import tools.dashboard as dash

    project = _waiting(
        _project(tmp_path), detail="Bash: rm <img src=x onerror=alert(1)> `db.sql`"
    )

    page = dash.render(dash.scan(project), "")

    assert "<img src=x" not in page, "agent text reached the page as live markup"
    assert "&lt;img src=x onerror=alert(1)&gt;" in page
    assert "<code>db.sql</code>" in page, "escaped, but no longer readable as markdown"


def test_a_waiting_claim_expires_rather_than_outliving_the_agent(tmp_path):
    """"A human is blocked on this **right now**" is the one present-tense claim
    the page makes, and nothing on disk ever retracts it: a culled pod or a
    SIGKILL mid-prompt leaves `waiting` behind with nobody left to answer.

    Two independent ways to stop believing it, because they catch different
    deaths — a session that hung around too long, and one `runtime.json` has
    never heard of. `turn_ended` is exempt on purpose: it describes the past, so
    it cannot become false.
    """
    import time

    import tools.dashboard as dash

    fresh = _waiting(_project(tmp_path, name="fresh"))
    assert dash.read_agent_state(fresh)["state"] == "waiting"

    old = _waiting(_project(tmp_path, name="old"), since=time.time() - dash.WAIT_TTL - 1)
    assert dash.read_agent_state(old)["state"] == "unknown"

    orphan = _waiting(_project(tmp_path, name="orphan"), session_id="ghost")
    (orphan / "runtime.json").write_text(
        json.dumps({"project": "orphan", "sessions": [{"session_id": "someone-else"}]})
    )
    assert dash.read_agent_state(orphan)["state"] == "unknown"

    past = _waiting(
        _project(tmp_path, name="past"), state="turn_ended", since=time.time() - 90000
    )
    assert dash.read_agent_state(past)["state"] == "turn_ended", "a fact about the past"


def test_the_expiry_reaches_a_polling_page(tmp_path, monkeypatch):
    """REGRESSION-in-waiting, and the subtle half of expiring at all.

    Nothing on disk changes when a `waiting` ages out, so an etag built only
    from file mtimes keeps answering 304 — and 304 means the browser keeps
    showing the page it already has. The stale "waiting for you" would survive
    the very expiry meant to remove it, which is exactly the failure the design
    doc records for server-rendered timestamps.

    Folding the *resolved* state into the fingerprint is what fixes it: the
    expiry invalidates its own cache entry.

    Only the clock moves here. Rewriting the file to age it would change its
    mtime and pass on the strength of that alone — which is the version of this
    test that was written first, and it agreed with a build that had no expiry
    in the etag at all.
    """
    import time

    import tools.dashboard as dash

    born = time.time()
    project = _waiting(_project(tmp_path), since=born)
    before = dash.scan(project)
    assert before.agent["state"] == "waiting"

    fingerprint = sorted((project / ".agent-state.json").stat().st_mtime_ns for _ in "x")
    monkeypatch.setattr(dash.time, "time", lambda: born + dash.WAIT_TTL + 1)
    after = dash.scan(project)

    assert after.agent["state"] == "unknown"
    assert after.etag != before.etag, "a polling browser would be served a 304 forever"
    # The 304 gate reads `fingerprint`, the 200 body carries `scan().etag`. They
    # are one expression today only because `scan` calls `fingerprint`; if they
    # ever drift the browser is handed a 304 for a page it does not have.
    assert dash.fingerprint(project)[0] == after.etag, "the gate and the body disagree"
    assert fingerprint == [(project / ".agent-state.json").stat().st_mtime_ns], (
        "the file changed, so this proved nothing about the clock"
    )


def test_the_alert_strip_and_button_are_anchored_outside_root(tmp_path):
    """Both would work inside #root. Both would also be destroyed and rebuilt
    every 4s, and that is the bug:

    - the strip's 600ms pulse would restart on every poll, so a banner that is
      supposed to flash once on a transition would flash forever — WCAG 2.3.1,
      and intolerable to sit beside;
    - the button's click handler would need re-binding after each swap, and
      `Notification.requestPermission` only works from a real user gesture.
    """
    import tools.dashboard as dash

    page = dash.render(dash.scan(_waiting(_project(tmp_path))), "")
    before_root, _, after_root = page.partition('<div id="root">')

    assert 'id="d-wait"' in before_root, "the pulse would restart every 4s"
    assert 'id="d-alert"' in before_root, "the permission gesture would lose its handler"
    assert 'id="d-state"' in after_root, "the state itself must come from the poll"


def test_the_title_marker_and_favicon_are_client_side(tmp_path):
    """The same rule as relative times, for the same reason: a 304 freezes
    anything the server wrote, and these two are the only channels that reach a
    reader whose tab is in the background. A `<title>` baked with a marker would
    keep claiming the agent needs you long after it stopped.

    This is the server's half: an unmarked title, and a `<link>` for the client
    to retarget (a browser will not adopt one that appears after it has painted).
    The client half — that STATE_JS actually writes both — is asserted from the
    node harness in `test_when_a_system_notification_actually_fires`, because the
    source-string greps this used to carry broke on a variable rename and passed
    on a behaviour-preserving one, which is backwards. That harness is
    node-gated, so on a box without node this assertion is the only half of the
    contract left standing — a green run there is not the whole story.
    """
    import tools.dashboard as dash

    page = dash.render(dash.scan(_waiting(_project(tmp_path))), "")

    assert "<title>demo</title>" in page, "the marker was baked into the response"
    assert '<link rel="icon" id="d-favicon"' in page, "nothing for STATE_JS to retarget"


def test_a_snapshot_gets_the_state_but_never_the_alert_button(tmp_path):
    """A snapshot is a point-in-time render, so it is honest about a prompt that
    was open when it was written. It cannot poll, though, so it can never see a
    *transition* — and a permission prompt for notifications that could never
    fire one is a button that only costs trust."""
    import tools.dashboard as dash

    snap = dash.render(dash.scan(_waiting(_project(tmp_path))), "", live=False)

    assert 'data-state="waiting"' in snap
    assert 'id="d-alert"' not in snap
    assert "function mark" in snap, "the title and favicon still work on a snapshot"


# Enough DOM for STATE_JS and not one property more. Stubbed rather than mocked
# through a real browser because the whole point is to drive the clock and the
# visibility flag by hand — the two inputs a headless page will not let you set.
NOTIFY_HARNESS = """
const fired = [];
let now = 1000000, hidden = false;
const listeners = {};
const nodes = {
  'd-wait': {innerHTML:'', hidden:true, offsetWidth:1,
             classList:{_s:new Set(), add(c){this._s.add(c)}, remove(c){this._s.delete(c)},
                        has(c){return this._s.has(c)}}},
  'd-alert': {hidden:true, addEventListener(){}},
  'd-favicon': {href:''}, 'd-state': null, 'd-detail': null,
};
globalThis.document = {
  title: 'demo',
  get hidden(){ return hidden; },
  getElementById: id => nodes[id] || null,
  addEventListener: (k,f) => (listeners[k] ||= []).push(f),
};
globalThis.window = globalThis;
globalThis.Notification = function(t,o){ fired.push(o.body); };
Notification.permission = 'granted';
globalThis.Date = {now: () => now};

await import('./state.mjs');

const set = (state, since, detail) => {
  nodes['d-state'] = state ? {dataset:{state, since:String(since)}} : null;
  nodes['d-detail'] = detail ? {innerHTML: detail, textContent: detail} : null;
  dashMark();
};
const out = {};
const go = (label, fn) => { fired.length = 0; fn(); out[label] = fired.slice(); };

go('waiting_visible', () => set('waiting', 1, 'Bash: sw_vers'));
go('waiting_rerendered', () => set('waiting', 1, 'Bash: sw_vers'));
go('ended_visible', () => set('turn_ended', 2, 'all done'));
hidden = true; (listeners.visibilitychange || []).forEach(f => f());
go('ended_hidden_10s', () => { now += 10000; set('turn_ended', 3, 'done'); });
go('ended_hidden_70s', () => { now += 70000; set('turn_ended', 4, 'done'); });
go('waiting_hidden', () => set('waiting', 5, 'AskUserQuestion: which?'));
set('waiting', 9, 'x');
out.pulsed = nodes['d-wait'].classList.has('pulse');
out.strip_shown = !nodes['d-wait'].hidden;
// Read while the state is still `waiting`: the two channels a background tab has.
out.title_marked = document.title;
out.favicon_href = nodes['d-favicon'].href;
// `unknown` has no ICON entry and is reached by every expired `waiting`.
set('unknown', 7, '');
out.favicon_unknown = nodes['d-favicon'].href;
set('', 0, '');
out.strip_cleared = nodes['d-wait'].hidden;
out.title_restored = document.title;
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs node to execute STATE_JS")
def test_when_a_system_notification_actually_fires(tmp_path):
    """The one piece of real logic on the client, so it is run rather than read.

    `Stop` fires at the end of **every** turn. Notifying on each one is how a
    feature gets muted inside a day, so `turn_ended` only speaks when the reader
    has genuinely been away — the case where they cannot already see it happen.
    `waiting` always speaks, because being blocked is the whole point.

    And nothing fires twice for one event: a re-render is not a transition, so
    the `(state, since)` pair gates it. Without that gate the 4s poll would
    notify fifteen times a minute about a single permission prompt.

    The title marker and the favicon dot are asserted here too, from the same
    run: they are the only two channels that reach a reader whose tab is in the
    background, and they used to be pinned by grepping the source for
    `document.title = (MARK[s] || '') + BASE;`. That grep failed on a rename that
    changed nothing and passed on a hoist that could have broken it. Reading the
    values back out of the harness is the check that was actually meant.

    `favicon_unknown` is the `|| ICON['']` fallback, and it is not hypothetical:
    `ICON` maps `waiting` and `turn_ended` only, while `AGENT_LABELS` also emits
    `unknown` — the resolved state of every `waiting` that aged past `WAIT_TTL`
    and of every orphaned record. Without the fallback the href becomes the
    literal string `undefined` and the browser 404s for a file of that name,
    with nothing in the console to say so.

    Node stands in for a browser because the two inputs that matter — the clock
    and the visibility flag — are exactly what a real headless page will not let
    a test set.
    """
    import tools.dashboard as dash

    (tmp_path / "state.mjs").write_text(dash.STATE_JS, encoding="utf-8")
    (tmp_path / "harness.mjs").write_text(NOTIFY_HARNESS, encoding="utf-8")
    done = subprocess.run(
        ["node", "harness.mjs"], cwd=tmp_path, capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)

    assert result["waiting_visible"] == ["Bash: sw_vers"]
    assert result["waiting_hidden"] == ["AskUserQuestion: which?"]
    assert result["waiting_rerendered"] == [], "a re-render is not a transition"
    assert result["ended_visible"] == [], "you are looking straight at it"
    assert result["ended_hidden_10s"] == [], "briefly away is not away"
    assert result["ended_hidden_70s"] == ["done"]

    assert result["pulsed"] and result["strip_shown"]
    assert result["strip_cleared"] and result["title_restored"] == "demo"

    assert result["title_marked"] == "● demo", "no marker on a backgrounded tab"
    assert result["favicon_href"].startswith("data:image/svg+xml,")
    assert "d29922" in result["favicon_href"], "the favicon dot never turned amber"
    assert result["favicon_unknown"].startswith("data:image/svg+xml,"), (
        "an unmapped state left the favicon href as the string 'undefined'"
    )


ASSET_DIR = ROOT / "tools" / "dashboard_assets"
JS_FILES = ("rel.js", "state.js", "poll.js", "lightbox.js")


SCOPE_HARNESS = """
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const DIR = process.argv[2];
const src = {};
const out = {parsed: {}, exported: {}, calls: [], hidden_calls: [], threw: null,
             rescheduled: [], cleared: 0};

// `new vm.Script` is the parser a classic inline <script> uses. `node --check`
// is not: on a .js file it falls back to the module goal, so `import`,
// `export`, top-level `await` and top-level `return` all pass there and are
// hard SyntaxErrors in the page render() actually emits.
for (const f of ['rel.js', 'state.js', 'poll.js', 'lightbox.js']) {
  src[f] = fs.readFileSync(path.join(DIR, f), 'utf8');
  try {
    new vm.Script(src[f]);
    out.parsed[f] = true;
  } catch (e) {
    out.parsed[f] = String(e);
  }
}
if (Object.values(out.parsed).some((v) => v !== true)) {
  console.log(JSON.stringify(out));
  process.exit(0);
}

const el = () => ({
  innerHTML: '', hidden: true, offsetWidth: 1, href: '', dataset: {},
  classList: {add() {}, remove() {}},
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
});
const ctx = {
  console,
  document: {
    // Derived, not a second flag: a guard that reads either one is then caught.
    get visibilityState() { return this.hidden ? 'hidden' : 'visible'; },
    title: 'demo', hidden: false, getElementById: el,
    querySelectorAll: () => [], addEventListener() {},
  },
  location: {pathname: '/proxy/9000/', replace() {}},
  setInterval: () => 0,
  setTimeout: (f, ms) => { out.rescheduled.push(ms); return 1; },
  clearTimeout() { out.cleared += 1; },
  CSS: {escape: (s) => s},
  DOMParser: class {
    parseFromString() { return {getElementById: () => ({innerHTML: 'swapped'})}; }
  },
  fetch: () => Promise.resolve({
    status: 200, headers: {get: () => 'W/"etag"'},
    text: () => Promise.resolve('<html></html>'),
  }),
};
ctx.window = ctx;
vm.createContext(ctx);

// Exactly what render() emits in live mode: three files, one <script>.
new vm.Script(src['rel.js'] + src['state.js'] + src['poll.js']).runInContext(ctx);

// Both are global bindings a *sibling file* created, so read them before
// spying — a spy would paper over the binding having gone missing.
out.exported = {relTimes: typeof ctx.relTimes, dashMark: typeof ctx.dashMark};
let calls = [];
ctx.relTimes = () => calls.push('relTimes');
ctx.dashMark = () => calls.push('dashMark');
out.rescheduled.length = 0;
try { ctx.tick(); } catch (e) { out.threw = String(e); }
await new Promise((r) => setTimeout(r, 20));
out.calls = calls;

// ...then the same tick with the tab backgrounded. It must still fetch and
// repaint, only on the slower cadence.
calls = [];
ctx.document.hidden = true;
try { ctx.tick(); } catch (e) { out.threw = String(e); }
await new Promise((r) => setTimeout(r, 20));
out.hidden_calls = calls;
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(not shutil.which("node"), reason="needs node to run the scripts")
def test_the_live_scripts_parse_and_share_one_scope(tmp_path):
    """The extracted scripts have no bundler, no eslint and no build step behind
    them, deliberately, so this is the whole lint story — and reading each file
    is not enough of one.

    `rel.js`, `state.js` and `poll.js` are concatenated into a single
    `<script>`, which is the only reason `poll.js` can see `rootEl`, `tag`,
    `relTimes` and `dashMark`. Nothing in the language records that. Splitting
    one blob into four separately editable files is exactly what makes it easy
    to sever — wrap `rel.js` in an IIFE and every file still parses, so a
    per-file check stays green while the page renders once and then stops
    updating. So the three are compiled together and driven through one `tick()`
    against a stub browser.

    Parsing is `vm.Script`, not `node --check`: `--check` on a `.js` file falls
    back to the module goal and accepts `import`, `export` and top-level
    `await`, all of which kill a classic inline `<script>` stone dead.

    The tick is then driven a second time with the tab backgrounded, which pins
    the poll's other three properties. `poll.js` used to wrap its `fetch` in
    `visibilityState === 'visible'`, so a backgrounded tab fetched nothing at
    all — and that is exactly the tab that needs to learn the agent is blocked:
    the title marker, the favicon dot and any notification are all painted from
    a response, so none of them can sit on a transport that stops when nobody
    is looking. So a hidden tick must still repaint (`hidden_calls`), must
    reschedule at 15s rather than 4s, and must `clearTimeout` first — `tick`
    schedules the next tick *and* the visibilitychange listener calls `tick`
    directly, so without that clear every return to the tab left another chain
    running forever. Free when hidden ticks did nothing; a compounding
    multiplier on real requests now.
    """
    (tmp_path / "harness.mjs").write_text(SCOPE_HARNESS, encoding="utf-8")
    done = subprocess.run(
        ["node", str(tmp_path / "harness.mjs"), str(ASSET_DIR)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)

    assert result["parsed"] == dict.fromkeys(JS_FILES, True)
    assert result["exported"] == {"relTimes": "function", "dashMark": "function"}
    assert result["threw"] is None, "poll.js lost a sibling's global"
    assert result["calls"] == ["relTimes", "dashMark"], "the swap repainted nothing"
    assert result["hidden_calls"] == ["relTimes", "dashMark"], (
        "a backgrounded tab stopped fetching — the one tab that cannot see the page"
    )
    assert result["rescheduled"] == [4000, 15000], (
        "the poll did not schedule its next tick at the visible, then hidden, cadence"
    )
    assert result["cleared"] == 2, "tab returns would stack poll chains"


def test_the_page_inlines_its_scripts_instead_of_linking_them(tmp_path):
    """The page is one file, in both transports, and that is what makes a
    `<script src=>` wrong rather than merely different.

    A snapshot is opened through Jupyter's `files/` route or double-clicked off
    disk, so a relative src resolves next to the *project*, not next to
    `tools/`. Live is no better: the server hands every unrecognised path to
    `SimpleHTTPRequestHandler(directory=project)`. Both 404, and a 404 script
    fails silently.

    `test_render_has_no_absolute_urls` does not cover this — a *relative* src
    passes it cleanly.

    `dash.css` is the same bargain in the other tag, so it is checked here too.

    Inlining is also what makes the moved prose dangerous in a way it was not
    inside a Python string: a `</script` or a `<!--` in a comment ends the tag
    early and silently truncates the page, so the file bodies are checked for
    both.
    """
    import tools.dashboard as dash

    state = dash.scan(_project(tmp_path, {"WORKLOG.md": WORKLOG}))
    live = dash.render(state, "", live=True)
    snap = dash.render(state, "", live=False)

    css = (ASSET_DIR / "dash.css").read_text(encoding="utf-8")
    assert "</style" not in css, "dash.css would truncate the page"
    for page in (live, snap):
        # A literal `"<script src="` misses `<script defer src=`; a bare
        # `" src="` would hit the lightbox's real <img>.
        assert not re.search(r"<script[^>]*\ssrc=", page)
        # The favicon <link> is real and stays; a stylesheet one never is.
        assert not re.search(r"<link[^>]*stylesheet", page)
        assert css in page, "dash.css is not inlined verbatim"
    for name in JS_FILES:
        body = (ASSET_DIR / name).read_text(encoding="utf-8")
        assert "</script" not in body and "<!--" not in body, f"{name} would truncate the page"
        assert body.endswith("\n"), f"{name} would glue onto the next file"
        assert body in live, f"{name} is not inlined verbatim"
        if name != "poll.js":  # live only, by design
            assert body in snap, f"{name} is not inlined verbatim in a snapshot"


def test_the_gallery_wins_the_thumbnail_width_tie():
    """REGRESSION. The figure gallery is `class="d-links d-figs"`, so both
    `.d-links img` and `.d-figs img` match its tiles at specificity (0,1,1) and
    source order alone decides the width. `.d-figs img` was written *above*
    `.d-links img`, so every gallery tile rendered at the timeline's 104px inside
    a 230px-minimum grid — from the file's first commit (3b7e36ec) until this
    one, silently, because nothing errors and the page still looks deliberate.

    A comment in dash.css says the order is load-bearing; a comment does not
    survive the next tidy-up of a stylesheet that has no other ordering
    constraint. This is the only thing that fails if the two rules swap back.

    Matched as `^selector{` rather than by substring: that same comment quotes
    `.d-links img`, so a plain `.index()` compares the comment's position and
    passes however the rules are ordered.
    """
    import tools.dashboard as dash

    links = re.search(r"^\.d-links img\{", dash.DASH_CSS, re.M)
    figs = re.search(r"^\.d-figs img\{", dash.DASH_CSS, re.M)
    assert links and figs, "one of the two thumbnail width rules is gone"
    assert links.start() < figs.start(), "gallery tiles are back to 104px"


def _dropin(cfg_dir: Path, name: str, enabled: bool) -> None:
    d = cfg_dir / "jupyter_server_config.d"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(
        json.dumps({"ServerApp": {"jpserver_extensions": {"jupyter_server_proxy": enabled}}}),
        encoding="utf-8",
    )


def test_proxy_detection_replicates_the_real_config_merge(tmp_path, monkeypatch):
    """REGRESSION, both directions, both reproduced against a real install.

    False negative: a `pip --user` install enables the proxy only under
    ~/.local/etc/jupyter, which `jupyter server extension list` structurally
    cannot see. Trusting the CLI fell back to a snapshot while the running
    server had the proxy loaded.

    False positive: `jupyter server extension disable` writes a *second* file,
    `jupyter_server_proxy.json` (underscore), holding false into the same dir.
    `_` sorts after `-`, so it wins the real merge. Reading only the shipped
    hyphenated file reported enabled and printed a URL that 404s.
    """
    import tools.dashboard as dash

    monkeypatch.setattr(dash, "_jupyter_config_dirs", lambda: [tmp_path])

    # shipped drop-in alone -> enabled, with no CLI involved
    _dropin(tmp_path, "jupyter-server-proxy.json", True)
    assert dash.proxy_enabled() is True

    # ...until `extension disable` adds the underscore file, which sorts last
    _dropin(tmp_path, "jupyter_server_proxy.json", False)
    assert dash.proxy_enabled() is False

    # no config anywhere -> snapshot, and no subprocess involved
    monkeypatch.setattr(dash, "_jupyter_config_dirs", lambda: [tmp_path / "nothing"])
    assert dash.proxy_enabled() is False

    # The first directory with an opinion decides: a ~/.local enable must not
    # resurrect an extension that /opt/conda disabled.
    high, low = tmp_path / "high", tmp_path / "low"
    monkeypatch.setattr(dash, "_jupyter_config_dirs", lambda: [high, low])
    _dropin(low, "jupyter-server-proxy.json", True)
    assert dash.proxy_enabled() is True
    _dropin(high, "jupyter_server_proxy.json", False)
    assert dash.proxy_enabled() is False


def test_markdown_is_escaped_in_both_renderer_tiers(monkeypatch):
    """The same trust boundary as the worklog, one layer deeper. The agent writes
    REPORT.md, and the overlay injects the rendered result with innerHTML into a
    page served under the hub's own origin — so a <script> here would run with the
    reader's Jupyter session cookies, not in a sandbox."""
    from tools.dashboard import render_markdown

    evil = "# H\n\n<script>alert(1)</script>\n\n<img src=x onerror=1>\n"

    try:
        import mistune  # noqa F401
        html = render_markdown(evil)
        assert "<script>" not in html
        assert "onerror=1>" not in html
        assert "&lt;script&gt;" in html
        assert "<h1>" in html          # still actually rendering, not just escaping
    except ImportError:
        print("warning - mistune is not installed")

    # Fallback tier: mistune absent. Still a working popup, just unstyled — and
    # still escaped, which is the part that matters.
    _without(monkeypatch, "mistune")
    plain = render_markdown(evil)
    assert plain.startswith("<pre>") and "# H" in plain
    assert "<script>" not in plain


def _without(monkeypatch, *blocked: str) -> None:
    """Make `import <name>` fail for the named modules, so a lower tier of
    render_markdown runs. Every tier must be exercised explicitly: mistune is
    installed here and always wins, so without this the fallbacks are dead code
    that no assertion ever reaches."""
    import builtins

    real = builtins.__import__

    def fake(name, *args, **kwargs):
        if name in blocked:
            raise ImportError(f"no {name} for this test")
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake)


def test_doc_route_serves_only_markdown_inside_the_project(tmp_path):
    """The overlay's fetch route is the one place this read-only server takes a
    caller-supplied path and reads a file with it. Clicking a link can never
    probe it, so the guard needs a test: no climbing out of the project, and no
    turning `/_doc/` into a general file reader for the CSVs and notebooks that
    sit next to the reports."""
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    from tools.dashboard import DOC_ROUTE, _handler_factory

    project = _project(tmp_path, {"REPORT.md": "# Title\n", "data/out.csv": "a,b\n"})
    outside = tmp_path / "outside.md"
    outside.write_text("# Secret\n", encoding="utf-8")
    (project / "escape.md").symlink_to(outside)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(project, "body{}"))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}{DOC_ROUTE}"

    def status(suffix: str) -> int:
        try:
            with urllib.request.urlopen(base + suffix, timeout=5) as response:
                return response.status
        except urllib.error.HTTPError as err:
            return err.code

    try:
        assert status("REPORT.md") == 200
        # Climbing out, plainly and percent-encoded. translate_path already drops
        # these segments; asserted so that stays true if the route stops using it.
        assert status("../outside.md") == 404
        assert status("%2e%2e%2foutside.md") == 404
        # A symlink is the case textual path-checking cannot see, and the only one
        # the resolve()/is_relative_to guard uniquely catches. Without it this is a
        # .md file, inside the project by name, that reads from anywhere.
        assert status("escape.md") == 404
        # A real file in the project that is simply not a document.
        assert status("data/out.csv") == 404
        assert status("beril.yaml") == 404
        assert status("nonexistent.md") == 404
    finally:
        server.shutdown()
        server.server_close()


def test_every_markdown_link_opens_the_overlay_not_a_new_tab(tmp_path):
    """REGRESSION. The overlay shipped wired to `_link_html` only, which the
    worklog chips use — the § Documents cards build their own anchor and kept
    `target="_blank"`. Since removing the Jupyter markdown route also made
    `_open_href` fall back to the plain relative path, the most obvious link on the
    page opened raw markdown source in a new tab, which is worse than what it
    replaced. The chips were verified and the cards were assumed.

    So: assert over *every* anchor pointing at a `.md`, not one call site.

    The plan needs a Research Question or `_plan_html` returns "" and the plan
    card — the third emitter of a markdown anchor — never renders, which is how
    this swept only the chips and the cards for its first year."""
    import re

    html = _render(
        tmp_path,
        {
            "WORKLOG.md": WORKLOG,
            "RESEARCH_PLAN.md": "# Plan\n\n## Research Question\nQ?\n\n" + PLAN,
            "REPORT.md": "# R\n",
            "figures/a.png": "x",
        },
    )

    anchors = re.findall(r"<a\b[^>]*>", html)
    md_anchors = [a for a in anchors if re.search(r'href="[^"]*\.md"', a)]
    assert md_anchors, "no markdown links rendered — test would pass vacuously"

    for anchor in md_anchors:
        assert "doc-trigger" in anchor, f"markdown link is not a trigger: {anchor}"
        assert "data-doc=" in anchor, f"trigger has no path to fetch: {anchor}"
        assert "_blank" not in anchor, f"markdown link still leaves the page: {anchor}"


def test_an_interrupted_write_leaves_the_previous_snapshot_intact(tmp_path, monkeypatch):
    """The snapshot is rewritten every turn, and its own banner tells the reader to
    reload — so a reload landing mid-write is the expected interleaving, not a rare
    one. Writing in place truncates first, which serves half a page.

    Stands in for that window by interrupting the write itself, not the render: a
    raising `render` proves nothing, because it is evaluated before `write_text`
    truncates anything.
    """
    import tools.dashboard as dash

    project = _project(tmp_path, {"WORKLOG.md": WORKLOG})
    snapshot = dash._write_snapshot(project, "")
    original = snapshot.read_text()
    assert "</html>" in original

    real_write = Path.write_text

    def half_a_write(self, data, *args, **kwargs):
        real_write(self, data[: len(data) // 2], *args, **kwargs)
        raise OSError("disk full, halfway through")

    monkeypatch.setattr(Path, "write_text", half_a_write)
    with pytest.raises(OSError):
        dash._write_snapshot(project, "")
    monkeypatch.undo()

    assert snapshot.read_text() == original, "a half-written page replaced a good one"


class _Ok:
    returncode = 0


def _fake_jupyter(tmp_path, monkeypatch, shebang: str):
    """A `jupyter` launcher on PATH, and nothing else on it."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    launcher = bindir / "jupyter"
    launcher.write_text(f"{shebang}\nprint('jupyter')\n")
    launcher.chmod(0o755)
    monkeypatch.setenv("PATH", str(bindir))
    return bindir


def test_setup_targets_the_interpreter_jupyter_runs_on(tmp_path, monkeypatch):
    """`sys.executable` is the wrong target and can fail *silently*.

    Inside a venv built with system site-packages, `pip install --user` is
    permitted: the module lands in `~/.local/lib/python3.<venv-version>/`, which
    the server's interpreter never reads, while the enable step still writes the
    drop-in that makes `proxy_enabled()` return True. Live mode then starts and
    every URL 404s — the state the probe exists to prevent.

    Lives in `beril setup` now; the probe it checks against still lives here, so
    the wizard and the dashboard cannot disagree about whether live mode works.
    """
    import tools.dashboard as dash
    from beril_cli import setup_cmd

    conda = tmp_path / "opt" / "conda" / "bin"
    conda.mkdir(parents=True)
    (conda / "python3").write_text("")
    (conda / "python3").chmod(0o755)

    _fake_jupyter(tmp_path, monkeypatch, f"#!{conda / 'python3'}")
    assert jupyter_python() == str(conda / "python3")
    assert jupyter_python() != sys.executable

    monkeypatch.setattr(dash, "proxy_enabled", lambda: False)
    argvs = []
    monkeypatch.setattr(setup_cmd.subprocess, "run",
                        lambda argv, **k: argvs.append(argv) or _Ok())
    setup_cmd._install_server_proxy(ROOT, assume_yes=True)
    pip = next(a for a in argvs if "pip" in a)
    assert pip[0] == str(conda / "python3"), f"installed against {pip[0]}"
    assert pip[0] != sys.executable


def test_setup_refuses_rather_than_installing_against_the_wrong_python(tmp_path, monkeypatch, capsys):
    """No `jupyter` on PATH means no way to know which interpreter matters, and
    guessing installs into an environment the server never reads. Refuse instead —
    a bare `pip` failure is what this replaces."""
    import tools.dashboard as dash
    from beril_cli import setup_cmd

    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    monkeypatch.setattr(dash, "proxy_enabled", lambda: False)
    ran = []
    monkeypatch.setattr(setup_cmd.subprocess, "run", lambda *a, **k: ran.append(a))

    assert setup_cmd._install_server_proxy(ROOT, assume_yes=True) == 1
    assert not ran, "ran an install with no idea which interpreter to target"
    assert "jupyter" in capsys.readouterr().err.lower()


# --------------------------------------------------------------------------
# Agent cost — a floor over one harness, and the page must say so
# --------------------------------------------------------------------------

LEDGER = """project_id: demo
status: analysis
agent_cost:
  observed_by: claude-code
  note: "Agent cost observed by Claude Code only."
  stages:
    - stage: exploration
      ended_at: "2026-08-05T12:00:00Z"
      usd: 4.12
      sessions_observed: 1
    - stage: proposed
      ended_at: "2026-08-05T15:30:00Z"
      usd: 5.68
      sessions_observed: 2
    - stage: active
      ended_at: "2026-08-06T09:14:00Z"
      sessions_observed: 0
"""


def test_agent_cost_parses_the_ledger_and_keeps_unobserved_distinct(tmp_path):
    """`None` is not a parse failure — it is "nobody watched this stage", which
    has to survive all the way to the page as something other than 0.00."""
    project = _project(tmp_path, {"beril.yaml": LEDGER})
    assert agent_cost(project) == {"exploration": 4.12, "proposed": 5.68, "active": None}

    # 61 of 78 projects have no beril.yaml at all, and older ones have no ledger.
    assert agent_cost(_project(tmp_path, name="bare")) == {}
    assert agent_cost(_project(tmp_path, {"beril.yaml": "status: active\n"}, "old")) == {}


def test_a_repeated_stage_sums_rather_than_overwrites(tmp_path):
    """/synthesize and /berdl-review demote `reviewed` back to `analysis`, so a
    stage legitimately appears twice. Taking the last entry would silently drop
    the first pass's spend."""
    project = _project(
        tmp_path,
        {"beril.yaml": LEDGER + '    - stage: exploration\n      usd: 1.00\n'},
    )
    assert agent_cost(project)["exploration"] == 5.12


def test_the_rail_shows_a_stage_cost_but_never_invents_a_zero(tmp_path):
    html = _rail("analysis", {"exploration": 4.12, "proposed": 5.68, "active": None})
    assert "$4.12" in html and "$5.68" in html
    assert "$0.00" not in html, "an unobserved stage must not read as free"
    assert "—" in html
    assert "no agent cost observed for this stage" in html
    assert "floor" in html, "the page must not present this as the project total"
    # Stages the ledger never named carry no figure at all.
    assert _rail("exploration", {}).count("d-cost") == 0


def test_the_header_total_sums_only_what_was_observed(tmp_path):
    """The rail says where the money went; this says how much, which is the
    question asked before re-running an expensive notebook round."""
    html = _cost_readout({"exploration": 4.12, "proposed": 5.68, "active": None})
    assert "$9.80" in html
    assert "agent cost" in html
    assert "floor" in html, "the most prominent number on the page must be qualified"
    assert "1 further stage(s) had no observation" in html


def test_no_observation_shows_no_total_at_all(tmp_path):
    """A project finished before this shipped, or worked by a human, must not
    get a confident $0.00 in the header."""
    assert _cost_readout({}) == ""
    assert _cost_readout({"exploration": None, "proposed": None}) == ""
