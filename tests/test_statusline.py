"""Tests for `.claude/statusline.sh` — the per-session BERIL status line.

Scoped the way tests/test_dashboard.py is: only what breaks *silently*. Layout is
not tested, because the status line is visible on every turn — if it renders
wrong you see it immediately.

Which **project** it picks is the opposite: a wrong answer looks exactly like a
right one. It has to stay correct when several Claude Code sessions share one
clone on different projects, which is why the two rejected designs (a repo-wide
`BERIL_PROJECT` in settings, and "whichever beril.yaml was touched last") are not
merely less tidy — they hand every session the same answer and flip under them as
each one writes.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATUSLINE = ROOT / ".claude" / "statusline.sh"

ANSI = re.compile(r"\033\[[0-9;]*m")


@pytest.fixture(autouse=True)
def _reap_dashboards(tmp_path):
    """Kill any dashboard *this* test started, whether it passed or failed.

    `_render` runs the real status line, which starts a dashboard as a side
    effect for whichever project resolves, and `port_for` derives the port from
    the *project id* — so a leaked process squats a deterministic port that a
    later test, or the next run of this file, expects to be free. The launcher
    then correctly reports "already running" and writes no snapshot, and the
    failure surfaces somewhere else entirely: `port 8766 already in use`, or
    `the dashboard was killed on a non-exit reason` accusing dash_stop.py of a
    bug it did not commit. A stray can also turn a test green for the wrong
    reason — `_wait_until_listening` is satisfied by the squatter.

    Teardown, not a `finally` in each test, because the case that actually
    leaks is the one after a *failed* assertion, and three tests had no cleanup
    at all.

    Scoped to this test's tmp_path and never `dashboard.py` alone: the
    maintainer runs a real dashboard on this very checkout, whose argv lives
    under the real repo path and so cannot match. Both spawn paths put tmp_path
    immediately after `dashboard.py` in argv — the status line's, and
    `_spawn_dashboard`, which runs the *real* script against a tmp project dir.
    """
    yield
    subprocess.run(["pkill", "-f", f"dashboard.py {tmp_path}"], capture_output=True)


def _wait_until_listening(port: int, timeout: float = 10.0) -> bool:
    """Poll rather than sleep a fixed guess: startup is ~0.1s and the fixed 2s
    waits this replaces were most of the suite's runtime."""
    import socket
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        probe = socket.socket()
        probe.settimeout(0.2)
        up = probe.connect_ex(("127.0.0.1", port)) == 0
        probe.close()
        if up:
            return True
        time.sleep(0.05)
    return False


def _port(project: str) -> int:
    from tools.dashboard import port_for

    return port_for(project)


def _repo(tmp_path: Path, projects: dict) -> Path:
    """A throwaway clone-shaped tree.

    `tools` is symlinked to the real one so the status line resolves stage and
    port through the same import it uses in the repo, rather than silently
    falling into its `except Exception` and testing nothing.
    """
    subprocess.run(["git", "init", "-q", "."], cwd=tmp_path, check=True)
    (tmp_path / "tools").symlink_to(ROOT / "tools")
    # beril_cli and the hook are symlinked in too, so the hook resolves *this*
    # tree as its repo root (it derives it from its own path) and can never
    # write into the real projects/ directory.
    (tmp_path / "beril_cli").symlink_to(ROOT / "beril_cli")
    # audit_cmd._find_repo_root walks up from cwd looking for this marker;
    # without it the snapshot silently declines to resolve any project.
    (tmp_path / "PROJECT.md").write_text("# throwaway\n")
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    (tmp_path / ".claude" / "hooks" / "beril-runtime.sh").symlink_to(
        ROOT / ".claude" / "hooks" / "beril-runtime.sh"
    )
    (tmp_path / ".claude" / "hooks" / "dash_stop.py").symlink_to(
        ROOT / ".claude" / "hooks" / "dash_stop.py"
    )
    for pid, sessions in projects.items():
        pdir = tmp_path / "projects" / pid
        pdir.mkdir(parents=True)
        (pdir / "beril.yaml").write_text(f"project_id: {pid}\nstatus: reviewed\n")
        if sessions is not None:
            (pdir / "runtime.json").write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "project": pid,
                        "sessions": [{"session_id": s} for s in sessions],
                    }
                )
            )
    return tmp_path


def _render(repo: Path, session_id: str = "no-such-session", cwd=None, added=(),
            model=None, cost=None) -> str:
    payload = {
        "session_id": session_id,
        "workspace": {
            "current_dir": str(cwd or repo),
            "added_dirs": [str(a) for a in added],
        },
        "context_window": {"used_percentage": 20},
    }
    if model is not None:
        payload["model"] = model
    if cost is not None:
        payload["cost"] = {"total_cost_usd": cost}
    done = subprocess.run(
        ["bash", str(STATUSLINE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd or repo),
        timeout=30,
    )
    assert done.returncode == 0, done.stderr
    return ANSI.sub("", done.stdout)


def test_simultaneous_sessions_on_one_clone_resolve_to_their_own_project(tmp_path):
    """The requirement that rejected every shared-state design.

    Two sessions, two projects, one clone, no cwd or branch signal for either.
    Each must name *its* project — the mapping is keyed by session id, so there is
    no single value for them to disagree over.
    """
    repo = _repo(tmp_path, {"alpha": ["sid-a"], "beta": ["sid-b"]})

    first = _render(repo, session_id="sid-a")
    second = _render(repo, session_id="sid-b")

    assert "alpha" in first and "beta" not in first
    assert "beta" in second and "alpha" not in second


def test_the_model_shares_the_gauge_cell(tmp_path):
    """Which model is answering is what you check before trusting a surprising
    result, so it earns a place — sharing the context gauge's cell rather than
    taking one of its own, because the two are read in the same glance and a `|`
    between them would claim they are separate readouts.

    Never truncated: "Opus 5 (1M context)", not "Opus 5". The parenthetical is
    the half you would act on — it is why a long run has not compacted yet.
    `display_name`, never `id`, which is what you would paste into an API call.

    The absent case is the one that breaks silently. The status line renders
    every turn in whatever harness drives it, and a missing `model` must leave
    the gauge alone rather than prefix it with a stray space.
    """
    repo = _repo(tmp_path, {"alpha": ["sid-a"]})

    first = _render(
        repo, model={"display_name": "Opus 5 (1M context)", "id": "claude-opus-5[1m]"}
    ).splitlines()[0]

    assert "Opus 5 (1M context)" in first, "the model name was truncated"
    assert "claude-opus-5" not in first, "that is the API id, not a label"
    assert "20%" in first, "the context gauge has to stay"
    # The point of the change: a space between them, not a separator.
    assert re.search(r"Opus 5 \(1M context\) [▓░]", first), "separator still there"

    for missing in (None, {}, {"display_name": ""}, {"display_name": None}):
        bare = _render(repo, model=missing).splitlines()[0]
        assert "Opus 5" not in bare
        assert "|  " not in bare, f"stray space before the gauge for {missing!r}"


def test_no_signal_names_no_project(tmp_path):
    """A session with no cwd, branch, `/add-dir` or recorded provenance must name
    nothing at all.

    This is the guard against a guessing fallback being added later: "newest
    project" would make this pass a name, and the line would then assert a project
    the session is not working on — the exact dishonesty the dashboard itself is
    built to avoid.
    """
    repo = _repo(tmp_path, {"alpha": ["sid-a"], "beta": ["sid-b"]})

    out = _render(repo, session_id="belongs-to-no-project")

    assert "alpha" not in out and "beta" not in out
    assert len(out.strip().splitlines()) == 1


def test_cwd_outranks_recorded_provenance(tmp_path):
    """Ordering is load-bearing: you can sit in projects/<a> while the session has
    provenance against <b>, and the directory you are actually in wins."""
    repo = _repo(tmp_path, {"alpha": ["sid-a"], "beta": []})

    out = _render(repo, session_id="sid-a", cwd=repo / "projects" / "beta")

    assert "beta" in out
    assert "alpha" not in out


# --------------------------------------------------------------------------
# Binding a mid-session project — the PostToolUse hook
# --------------------------------------------------------------------------

def _hook(repo: Path, payload: dict, session_id: str) -> subprocess.CompletedProcess:
    """Run the hook the way Claude Code does, but from inside the throwaway repo.

    Invoked through the symlink in `repo/.claude/hooks/`, because the hook
    derives its root from its own resolved path — running the one in the real
    repo would make every assertion here about the real projects/ tree.
    """
    import os

    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": session_id}
    return subprocess.run(
        ["bash", str(repo / ".claude" / "hooks" / "beril-runtime.sh")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
        timeout=60,
    )


def test_a_tool_write_binds_the_session_to_the_project_it_touched(tmp_path):
    """The gap this closes: a project created *during* a session was never bound.

    None of the other signals can fire — Claude Code was launched before the
    directory existed, `/berdl_start` only *offers* to create the branch, and the
    SessionStart snapshot ran before Phase 0 scaffolded anything. The first write
    into the project is the earliest moment the binding is knowable.
    """
    repo = _repo(tmp_path, {"newproj": None})   # no runtime.json yet
    sid = "sess-posttooluse"

    done = _hook(repo, {
        "session_id": sid,
        "hook_event_name": "PostToolUse",
        "cwd": str(repo),
        "tool_name": "Write",
        "tool_input": {"file_path": str(repo / "projects" / "newproj" / "beril.yaml")},
    }, sid)
    assert done.returncode == 0, done.stderr          # never blocks a tool call

    # Gotcha 1: a guard that reads stdin would eat the payload and this file
    # would never be written.
    recorded = json.loads((repo / "projects" / "newproj" / "runtime.json").read_text())
    assert any(s.get("session_id") == sid for s in recorded["sessions"])

    # ...and the status line now names it, having had no other signal.
    assert "newproj" in _render(repo, session_id=sid)


def test_the_guard_does_not_skip_a_non_tool_payload(tmp_path):
    """Gotcha 2. A SessionStart payload for a session on branch `projects/<id>`
    sitting at the repo root contains no `projects/` string at all — the branch is
    read by shelling out to git. A blanket "skip unless the payload mentions
    projects/" would silently break the path that works today."""
    repo = _repo(tmp_path, {"branchproj": None})
    subprocess.run(["git", "checkout", "-q", "-b", "projects/branchproj"],
                   cwd=repo, check=True)
    sid = "sess-sessionstart"

    done = _hook(repo, {"session_id": sid, "hook_event_name": "SessionStart",
                        "cwd": str(repo), "source": "startup"}, sid)
    assert done.returncode == 0, done.stderr
    assert (repo / "projects" / "branchproj" / "runtime.json").is_file(), (
        "the guard skipped a SessionStart payload whose only project signal is the "
        "git branch, which is never in the payload"
    )


def test_the_guard_does_not_start_the_interpreter_for_a_write_outside_a_project(tmp_path):
    """The other half of the guard — and the only half with an observable effect.

    Its predecessor asserted "a write outside any project records nothing" and
    could not fail: deleting the guard outright left it green. The guard changes
    nothing but *cost*. A write outside any project resolves to no project, so
    nothing is recorded whether or not the interpreter ever started, and the
    assertion was about the outcome the two paths share.

    So make the interpreter itself observable. The hook prefers
    `$root/.venv/bin/python` over PATH, and the throwaway tree has no `.venv`,
    so a shim written there *is* the interpreter the hook will pick; the
    sentinel it touches is the fact "the interpreter started". No wall clock, so
    nothing to be flaky about on a loaded machine.

    Direction three — a SessionStart payload carrying no `projects/` string at
    all — is already pinned by test_the_guard_does_not_skip_a_non_tool_payload
    above, and is not repeated here.
    """
    repo = _repo(tmp_path, {"newproj": None})
    sentinel = tmp_path / "interpreter-started"
    shim = repo / ".venv" / "bin" / "python"
    shim.parent.mkdir(parents=True)
    # Drains stdin so the hook's `printf | py` never takes SIGPIPE.
    shim.write_text(f"#!/bin/sh\ncat >/dev/null\ntouch '{sentinel}'\n")
    shim.chmod(0o755)

    def interpreter_started(file_path: Path) -> bool:
        sentinel.unlink(missing_ok=True)
        done = _hook(repo, {
            "session_id": "s", "hook_event_name": "PostToolUse", "cwd": str(repo),
            "tool_name": "Write", "tool_input": {"file_path": str(file_path)},
        }, "s")
        assert done.returncode == 0, done.stderr
        return sentinel.exists()

    assert not interpreter_started(repo / "NOTES.md"), (
        "an ordinary edit outside every project paid for a Python start-up; the "
        "cost guard is gone and every Write/Edit in the repo now pays it"
    )
    assert interpreter_started(repo / "projects" / "newproj" / "beril.yaml"), (
        "no interpreter for a write *into* a project: either the guard swallowed "
        "it — the same silent break as skipping a SessionStart payload, nothing "
        "would ever be bound — or the hook stopped preferring $root/.venv/bin/"
        "python and never reached the shim"
    )


def test_the_statusline_starts_a_dashboard_that_is_not_running(tmp_path):
    """The launcher moved here because skill prose never fired during
    exploration: the earliest copy sat in `/berdl_start` Phase C, after the plan
    is written *and* approved.

    Bounded on purpose — it fires only when a project resolved and the port is
    closed, so the steady state is one socket check and nothing else.
    """
    import socket

    repo = _repo(tmp_path, {"spawnme": ["sess-spawn"]})
    port = 8700 + __import__("zlib").crc32(b"spawnme") % 100

    probe = socket.socket(); probe.settimeout(0.2)
    assert probe.connect_ex(("127.0.0.1", port)) != 0, f"port {port} already in use"
    probe.close()

    first = _render(repo, session_id="sess-spawn")
    assert "dashboard starting" in first             # nothing to advertise yet

    assert _wait_until_listening(port), "the statusline did not start a dashboard"
    # Through `public_url`, not a hardcoded `:<port>/`. That literal is the
    # off-cluster form only, so this assertion passed in CI and failed on the
    # hub — the one environment the dashboard exists for.
    from tools.dashboard import public_url

    assert public_url(port) in _render(repo, session_id="sess-spawn")


def _no_proxy(tmp_path: Path, repo: Path, monkeypatch) -> None:
    """Bill's pod: an image with no jupyter-server-proxy anywhere.

    JUPYTER_CONFIG_PATH outranks every other config dir and the first directory
    with an opinion decides, so one `false` drop-in there is the whole simulation.
    """
    cfg = tmp_path / "nocfg" / "jupyter_server_config.d"
    cfg.mkdir(parents=True)
    (cfg / "jupyter_server_proxy.json").write_text(
        json.dumps({"ServerApp": {"jpserver_extensions": {"jupyter_server_proxy": False}}})
    )
    monkeypatch.setenv("JUPYTER_CONFIG_PATH", str(tmp_path / "nocfg"))
    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/bill/")
    monkeypatch.setenv("JUPYTER_SERVER_ROOT", str(repo))


def test_without_the_proxy_it_snapshots_instead_of_respawning_forever(tmp_path, monkeypatch):
    """REGRESSION, and the bug this whole branch was reported for.

    The launcher spawned a *server* whenever the port was closed. On an image with
    no jupyter-server-proxy that server cannot bind: it wrote a snapshot, exited 0,
    and left the port closed — so the next turn spawned it again. One process per
    turn, forever, with the install instructions accumulating in a gitignored log.

    The gate belongs inside the not-listening branch, so the steady state still
    costs one socket check and nothing more.
    """
    import socket
    import time

    repo = _repo(tmp_path, {"noproxy": ["sess-np"]})
    _no_proxy(tmp_path, repo, monkeypatch)
    port = _port("noproxy")
    pdir = repo / "projects" / "noproxy"

    for _ in range(3):
        out = _render(repo, session_id="sess-np")

    # No server was ever started — that is the loop, gone.
    probe = socket.socket(); probe.settimeout(0.2)
    assert probe.connect_ex(("127.0.0.1", port)) != 0, "started a server that cannot work"
    probe.close()
    for _ in range(40):
        if not subprocess.run(["pgrep", "-f", f"dashboard.py {pdir}"],
                              capture_output=True).stdout.strip():
            break
        time.sleep(0.05)
    else:
        raise AssertionError("dashboard processes still alive — the loop is back")

    # ...and the user got something instead of nothing.
    assert (pdir / "dashboard.html").is_file(), "no snapshot written"
    assert "files/projects/noproxy/dashboard.html" in out, "no way to find the snapshot"
    assert "beril setup" in out, "no way out of snapshot mode"

    # The instructions must not go back to the log nobody reads.
    log = pdir / ".dash.log"
    assert not log.exists() or log.stat().st_size == 0, "boilerplate is piling up again"


def test_it_does_not_spawn_when_no_project_resolves(tmp_path):
    """A display component with a side effect has to stay bounded: no project,
    no process.

    Two details, both found by mutating the launcher to spawn unconditionally and
    watching this test pass anyway:

    - `pgrep -fc <pat>` with no match exits 2 on Darwin 25.5.0 with empty stdout
      and a usage message on stderr, so the earlier `.stdout.strip() or "0"`
      compared `"0"` to `"0"` whatever happened. Count `pgrep -f` lines instead.
    - The pattern has to name *this* tmp repo. A repo-wide one is masked in a
      full-suite run: `port_for("unbound")` is the same port every time, so a
      stray from an earlier test holds it, the spawn dies on EADDRINUSE, and the
      count matches again. The _reap_dashboards fixture pkills the same way,
      one path segment broader.
    """
    repo = _repo(tmp_path, {"unbound": None})

    def running() -> int:
        found = subprocess.run(["pgrep", "-f", f"dashboard.py {repo}/projects"],
                               capture_output=True, text=True)
        return len(found.stdout.split())

    before = running()
    assert "unbound" not in _render(repo, session_id="no-such-session")
    assert running() == before, "spawned a dashboard with no project resolved"


# --------------------------------------------------------------------------
# Stopping it — the SessionEnd hook
# --------------------------------------------------------------------------

def _stop(repo: Path, payload: dict, session_id: str) -> subprocess.CompletedProcess:
    import os

    return subprocess.run(
        ["python3", str(repo / ".claude" / "hooks" / "dash_stop.py")],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=str(repo), env={**os.environ, "CLAUDE_CODE_SESSION_ID": session_id},
        timeout=60,
    )


def _spawn_dashboard(repo: Path, pid: str):
    import subprocess as sp
    import sys as s

    return sp.Popen(
        [s.executable, str(ROOT / "tools" / "dashboard.py"), str(repo / "projects" / pid)],
        stdout=sp.DEVNULL, stderr=sp.DEVNULL, start_new_session=True,
    )


def test_a_mode_toggle_does_not_stop_the_dashboard(tmp_path):
    """SessionEnd fires for things that end nothing. `bypass_permissions_disabled`
    is a mode toggle — same session, same project — so killing there is pure
    churn. Every other reason, `clear` included, ends the session: /clear starts
    a fresh one that may be a different project, so the old dashboard should go."""
    repo = _repo(tmp_path, {"keepme": ["sess-clear"]})
    proc = _spawn_dashboard(repo, "keepme")
    try:
        import time

        assert _wait_until_listening(_port("keepme")), "dashboard did not start"
        for reason in ("bypass_permissions_disabled",):
            done = _stop(repo, {"session_id": "sess-clear", "reason": reason,
                                "hook_event_name": "SessionEnd", "cwd": str(repo)},
                         "sess-clear")
            assert done.returncode == 0
        time.sleep(0.25)
        assert proc.poll() is None, "the dashboard was killed on a non-exit reason"
    finally:
        proc.kill()


def _bind(repo: Path, project: str, session_id: str, observed_at: str) -> None:
    """Record a session in one project's runtime.json, with a chosen timestamp."""
    (repo / "projects" / project / "runtime.json").write_text(
        json.dumps({"schema_version": "2.0", "project": project,
                    "sessions": [{"session_id": session_id, "observed_at": observed_at}]})
    )


def test_switching_projects_resolves_to_the_one_worked_on_most_recently(tmp_path):
    """REGRESSION. A session that moves between projects is recorded in both files,
    and the lookup took the first hit from a sorted glob — so the answer was
    whichever project sorted earlier, and working in `zeta_current` after
    `alpha_old` displayed `alpha_old` with a live dashboard URL for the project you
    had left.

    Asserted in *both* alphabetical directions: with only one, a first-match-wins
    implementation passes half the time by accident.
    """
    for older, newer in (("alpha_old", "zeta_current"), ("zeta_current", "alpha_old")):
        root = tmp_path / newer
        root.mkdir()
        repo = _repo(root, {older: None, newer: None})
        _bind(repo, older, "moved", "2026-07-31T10:00:00Z")
        _bind(repo, newer, "moved", "2026-07-31T11:00:00Z")

        out = _render(repo, session_id="moved")
        assert newer in out, f"resolved to the stale project, not {newer}"
        assert older not in out


def test_the_exit_hook_stops_every_dashboard_the_session_started(tmp_path):
    """Display picks one project; cleanup has to take all of them.

    The status line starts a dashboard for whichever project the session is on, so
    a session that switched has one running per project it touched, each on its own
    port. Stopping only the current one left the earlier ones alive after Claude
    Code exited, which is the leak this hook exists to prevent — and switching
    projects is now a single pin away, so it is the common case, not a corner.
    """
    repo = _repo(tmp_path, {"alpha_old": None, "zeta_current": None})
    _bind(repo, "alpha_old", "moved", "2026-07-31T10:00:00Z")
    _bind(repo, "zeta_current", "moved", "2026-07-31T11:00:00Z")

    left_behind = _spawn_dashboard(repo, "alpha_old")
    current = _spawn_dashboard(repo, "zeta_current")
    try:
        assert _wait_until_listening(_port("alpha_old"))
        assert _wait_until_listening(_port("zeta_current"))

        done = _stop(repo, {"session_id": "moved", "hook_event_name": "SessionEnd",
                            "cwd": str(repo), "reason": "other"}, "moved")
        assert done.returncode == 0, done.stderr

        assert current.wait(timeout=15) is not None, "left the live dashboard running"
        assert left_behind.wait(timeout=15) is not None, (
            "left a dashboard running for a project the session had switched away from"
        )
    finally:
        for proc in (left_behind, current):
            if proc.poll() is None:
                proc.kill()


def test_writing_the_pin_marker_switches_the_session_to_that_project(tmp_path):
    """How you say "I'm working on X" from the repo root, where no other signal can
    fire: cwd is the checkout, the branch is not `projects/<id>`, and `/add-dir`
    would be adding a subfolder of a directory already in scope.

    The marker needs no new resolution path — writing it *is* a write into the
    project, which the PostToolUse hook already binds on. Asserted in both
    alphabetical orders because `observed_at` is stamped only to the second, so
    two pins land in the same one and a naive tie-break picks a name, not a time.
    """
    def project_line(out: str) -> str:
        """Second line only: the first carries the checkout path, which in a tmp
        tree can contain a project name and match by accident."""
        return next((l for l in out.splitlines() if l.startswith("  ")), "")

    for case, (first, second) in enumerate(
        (("alpha_first", "zeta_second"), ("zeta_first", "alpha_second"))
    ):
        root = tmp_path / f"case{case}"
        root.mkdir()
        repo = _repo(root, {first: None, second: None})

        assert not project_line(_render(repo, session_id="sid"))  # nothing bound yet
        for project in (first, second):                        # pinned back to back
            done = _hook(repo, {
                "session_id": "sid", "hook_event_name": "PostToolUse",
                "cwd": str(repo), "tool_name": "Write",
                "tool_input": {"file_path": str(repo / "projects" / project / ".beril-pin")},
            }, "sid")
            assert done.returncode == 0, done.stderr
        out = _render(repo, session_id="sid")

        line = project_line(out)
        assert second in line, f"pinning {second} did not switch away from {first}"
        assert first not in line


def test_two_sessions_pin_different_projects_in_one_clone(tmp_path):
    """The pin must be session-scoped, not repo-wide.

    `projects/<id>/.beril-pin` is a file in a shared tree, so the obvious worry is
    that one session pinning re-points every other one. It cannot: nothing reads
    the marker. Writing it only triggers the PostToolUse hook, which records *this*
    session's id in that project's runtime.json, and the lookup filters by the
    caller's own session id. A marker left by another session, or by last week, has
    no effect at all.
    """
    repo = _repo(tmp_path, {"metal_cofit": None, "phage_defense": None})

    def pin(session_id: str, project: str) -> None:
        done = _hook(repo, {
            "session_id": session_id, "hook_event_name": "PostToolUse",
            "cwd": str(repo), "tool_name": "Write",
            "tool_input": {"file_path": str(repo / "projects" / project / ".beril-pin")},
        }, session_id)
        assert done.returncode == 0, done.stderr

    def project_of(session_id: str) -> str:
        out = _render(repo, session_id=session_id)
        return next((l for l in out.splitlines() if l.startswith("  ")), "")

    pin("session-A", "metal_cofit")
    pin("session-B", "phage_defense")

    assert "metal_cofit" in project_of("session-A")
    assert "phage_defense" not in project_of("session-A"), "B's pin leaked into A"
    assert "phage_defense" in project_of("session-B")
    assert "metal_cofit" not in project_of("session-B"), "A's pin leaked into B"


def test_using_another_projects_data_does_not_switch_projects():
    """Reading across projects is normal work, not a switch.

    Projects routinely load another project's exported data, so the binding must
    not follow a read. Two things stop it, and this pins the fragile one: only
    `Write|Edit|NotebookEdit` reach the hook at all, so a `Read` or a `Bash` that
    cats another project's CSV never even runs it.

    That is one edit away from breaking — broadening the matcher is a tempting fix
    for "the status line did not notice my project", and it would silently make
    every cross-project read a switch.

    Scoped to the *binding* hook by name, not to everything on `PostToolUse`.
    Other hooks legitimately want every tool call — `agent_state.py` clears an
    answered permission prompt there — and they bind nothing, so a matcher-less
    entry of theirs is not this failure.
    """
    import re

    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    matchers = [
        entry.get("matcher", ".*")
        for entry in settings["hooks"]["PostToolUse"]
        if any("beril-runtime" in hook["command"] for hook in entry["hooks"])
    ]
    assert matchers, "the binding hook is no longer on PostToolUse at all"
    for readonly in ("Read", "Bash", "Grep", "Glob"):
        assert not any(re.fullmatch(m, readonly) for m in matchers), (
            f"{readonly} now reaches the binding hook: reading another project's "
            "data would switch the session to it"
        )


def test_a_write_that_merely_cites_another_project_does_not_rebind(tmp_path):
    """The other half: writing *your* report, which cites another project's export.

    The path is in this project and the content names another, so the payload
    carries two project ids. `resolve_project` refuses on ambiguity rather than
    picking one, which leaves the existing binding standing — the right answer
    here, since the write really was into the project already bound.
    """
    repo = _repo(tmp_path, {"my_work": None, "other_proj": None})
    _hook(repo, {"session_id": "s", "hook_event_name": "PostToolUse", "cwd": str(repo),
                 "tool_name": "Write",
                 "tool_input": {"file_path": str(repo / "projects" / "my_work" / "WORKLOG.md")}}, "s")

    _hook(repo, {"session_id": "s", "hook_event_name": "PostToolUse", "cwd": str(repo),
                 "tool_name": "Write",
                 "tool_input": {
                     "file_path": str(repo / "projects" / "my_work" / "REPORT.md"),
                     "content": "Counts reused from projects/other_proj/data/counts.csv\n",
                 }}, "s")
    line = next((l for l in _render(repo, session_id="s").splitlines()
                 if l.startswith("  ")), "")

    assert "my_work" in line
    assert "other_proj" not in line, "citing another project switched the session to it"



# --- agent cost ------------------------------------------------------------


def test_the_statusline_persists_the_cost_it_displays(tmp_path):
    """It is the only component that can. No hook payload carries cost — probed
    against SessionStart, PostToolUse and Stop, all three omit it — and the
    transcript records token counts, not dollars. An unreported cost writes no
    `cost` key: 0.00 would make an unwatched session look like a free one."""
    repo = _repo(tmp_path, {"demo": ["s1"]})
    pdir = repo / "projects" / "demo"

    assert "$4.12" in _render(repo, session_id="s1", cwd=pdir, cost=4.12)
    cost = json.loads((pdir / "runtime.json").read_text())["sessions"][0]["cost"]
    assert cost["usd"] == 4.12
    assert cost["observer"] == "claude-code-statusline"

    (tmp_path / "second").mkdir()
    repo2 = _repo(tmp_path / "second", {"demo": ["s1"]})
    _render(repo2, session_id="s1", cwd=repo2 / "projects" / "demo")  # no cost key
    assert "cost" not in json.loads(
        (repo2 / "projects" / "demo" / "runtime.json").read_text()
    )["sessions"][0]


def test_the_hook_stamps_a_stage_boundary_end_to_end(tmp_path):
    """The only test that proves the wiring works, because it is the only one
    that runs the real scripts.

    Everything else drives `run_runtime_snapshot` in-process, which cannot see a
    hook that never starts, a guard that eats the payload, or a payload shape
    that stopped matching. Here the status line observes the cost (nothing else
    can), the hook witnesses the beril.yaml edit, and the ledger has to come out
    the far side.

    What this does NOT cover, despite looking like it should: the import-chain
    failure that once left this feature entirely dead behind a green suite
    (`block_span` sourced from `approve_cmd`, which reaches `tomllib` 3.11+,
    against the bare-`python3` fallback the BERDL pod uses). This fixture has no
    venv, so the hook does take that fallback — but under `uv run pytest` the
    project venv is on PATH, so `python3` finds a modern interpreter and the
    import succeeds. Verified by reverting the fix: this test still passed.
    `test_audit_cmd_stays_off_the_cli_import_chain` is what actually catches it,
    deterministically. Neither test replaces the other.
    """
    repo = _repo(tmp_path, {"demo": None})
    pdir, sid = repo / "projects" / "demo", "sess-e2e"
    manifest = pdir / "beril.yaml"
    manifest.write_text("project_id: demo\nstatus: exploration\n")

    def edit(payload_path=manifest):
        """One PostToolUse write into the project, exactly as Claude Code sends it."""
        done = _hook(repo, {
            "session_id": sid,
            "hook_event_name": "PostToolUse",
            "cwd": str(pdir),
            "tool_name": "Edit",
            "tool_input": {"file_path": str(payload_path)},
        }, sid)
        assert done.returncode == 0, done.stderr   # never blocks a tool call
        return done

    _render(repo, session_id=sid, cwd=pdir, cost=4.12)
    edit()

    # The transition. Note the hook payload is byte-identical to the one above:
    # nothing in a session snapshot depends on lifecycle status, so the writer's
    # idempotency short-circuit would swallow this if the stamp sat behind it.
    manifest.write_text(manifest.read_text().replace("exploration", "proposed"))
    edit()

    text = manifest.read_text()
    assert "- stage: exploration" in text, (
        f"the hook witnessed the transition but stamped nothing:\n{text}"
    )
    assert "usd: 4.12" in text
    assert "sessions_observed: 1" in text

    # A second stage, to pin that appending does not clobber the first entry.
    _render(repo, session_id=sid, cwd=pdir, cost=9.80)
    manifest.write_text(manifest.read_text().replace("status: proposed", "status: active"))
    edit()

    text = manifest.read_text()
    assert text.count("agent_cost:") == 1
    assert text.index("- stage: exploration") < text.index("- stage: proposed")
    assert "usd: 5.68" in text, f"delta wrong for the second stage:\n{text}"
