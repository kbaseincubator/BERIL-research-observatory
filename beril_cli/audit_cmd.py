"""Best-effort, per-session runtime provenance.

A SessionStart hook resolves a project conservatively and records one atomic
session in ``runtime.json`` (schema 2, non-authoritative). Fields are omitted
when absent, never fabricated, and the writer always returns 0. See
``docs/provenance-and-trust.md`` for the model, field list, and rationale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from beril_cli import __version__
from beril_cli.project_resolution import resolve_project

RUNTIME_FILE = "runtime.json"
RUNTIME_SCHEMA_VERSION = "2.0"

#: Who observed a cost figure. There is exactly one candidate: no hook payload
#: carries cost (verified against SessionStart, PostToolUse and Stop — all three
#: omit it), and the session transcript records token counts, not dollars, so
#: deriving USD would mean shipping and maintaining a per-model price table.
#: ``.claude/statusline.sh`` receives ``cost.total_cost_usd`` and calls
#: ``record_session_cost`` below; this module owns the file it writes into.
COST_OBSERVER = "claude-code-statusline"

#: Part of the record, not documentation: the figure is a floor over one
#: harness, and it says so in the file a reviewer opens at PR time.
AGENT_COST_NOTE = (
    "Agent cost observed by Claude Code only. Work done by a human or by "
    "another agent is not counted, so this is a floor, not a project total."
)

#: The lifecycle ``status:`` of a project, read the same way ``_actor`` reads
#: the ORCID out of the same file — by regex, for the reasons in ``block_span``.
_STATUS = re.compile(r"^status:\s*[\"']?([A-Za-z][\w-]*)", re.MULTILINE)

#: The observatory's fixed lakehouse warehouse (per tools/lakehouse_upload.py) —
#: a default label for this observatory, not an observed per-project fact.
TENANT = "tenant-general-warehouse/microbialdiscoveryforge"

#: The ``## Data`` section of a REPORT.md (up to the next ``##`` heading).
_DATA_SECTION = re.compile(
    r"^##\s+Data\b.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL | re.IGNORECASE
)
_BACKTICKED = re.compile(r"`([^`]+)`")


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md (repo marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_info(root: Path, ignored_path: Path | None = None) -> dict | None:
    """Best-effort git sha + dirty flag of the code that produced the record."""
    try:
        sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if sha.returncode != 0:
            return None
        status_command = ["git", "-C", str(root), "status", "--porcelain", "--", "."]
        if ignored_path is not None:
            relative = ignored_path.resolve().relative_to(root.resolve()).as_posix()
            status_command.append(f":(exclude){relative}")
        status = subprocess.run(
            status_command,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {"git_sha": sha.stdout.strip(), "git_dirty": bool(status.stdout.strip())}
    except Exception:
        return None


def _actor(project_dir: Path) -> dict | None:
    """Best-effort actor: the shell USER + the ORCID from the project's beril.yaml."""
    actor: dict = {}
    user = os.environ.get("USER")
    if user:
        actor["user"] = user
    try:
        text = (project_dir / "beril.yaml").read_text()
        m = re.search(r"orcid:\s*[\"']?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", text)
        if m:
            actor["orcid"] = m.group(1)
    except Exception:
        pass
    return actor or None


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _datasets_from_report(project_dir: Path) -> list[dict] | None:
    """Parse the BERDL collections + tables the author documented in REPORT.md.

    Best-effort and honest: reads the first table under ``## Data`` whose header
    has a collection/dataset/source column (skipping the ``### Generated Data``
    outputs table). It captures only what the author WROTE UP in REPORT.md — not
    execution-time truth — and returns None for projects using a different table
    format (~1/3). It never runs or parses SQL.
    """
    try:
        text = (project_dir / "REPORT.md").read_text()
    except Exception:
        return None
    section = _DATA_SECTION.search(text)
    if not section:
        return None
    lines = section.group(0).splitlines()
    name_i = tbl_i = rows_start = None
    for idx, ln in enumerate(lines):
        if not ln.lstrip().startswith("|"):
            continue
        cells = [c.lower() for c in _split_row(ln)]
        ni = next(
            (
                i
                for i, c in enumerate(cells)
                if re.search(r"collection|dataset|database|source", c)
            ),
            None,
        )
        if ni is not None:
            name_i = ni
            tbl_i = next((i for i, c in enumerate(cells) if "table" in c), None)
            rows_start = idx + 1
            break
    if name_i is None:
        return None
    datasets = []
    for ln in lines[rows_start:]:
        if not ln.lstrip().startswith("|"):
            break  # table ended
        cells = _split_row(ln)
        if all(set(c) <= set("-: ") for c in cells):
            continue  # header separator row
        if name_i >= len(cells):
            continue
        m = _BACKTICKED.search(cells[name_i])
        collection = (m.group(1) if m else cells[name_i]).strip()
        if not collection:
            continue
        tables = (
            _BACKTICKED.findall(cells[tbl_i])
            if tbl_i is not None and tbl_i < len(cells)
            else []
        )
        datasets.append({"collection": collection, "tables": tables})
    return datasets or None


def _agent_signals_from_transcript(payload: dict) -> dict:
    """Best-effort model + permission mode from the session transcript.

    The SessionStart hook payload carries neither the model nor the permission
    mode — both are recorded only in the session's JSONL transcript. Read the
    LAST ``assistant`` record's ``message.model`` (the model in effect now, so a
    mid-session ``/model`` switch is reflected on the next SessionStart re-fire)
    and the LAST ``permission-mode`` record's ``permissionMode``. Returns an
    empty dict for a fresh session whose transcript has no turns yet, and never
    raises — snapshotting must not block a session.
    """
    transcript = payload.get("transcript_path")
    if not isinstance(transcript, str) or not transcript.strip():
        return {}
    signals: dict = {}
    try:
        with Path(transcript).open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(record, dict):
                    continue
                if record.get("type") == "assistant":
                    message = record.get("message")
                    model = message.get("model") if isinstance(message, dict) else None
                    if isinstance(model, str) and model.strip():
                        signals["model_id"] = model.strip()
                elif record.get("type") == "permission-mode":
                    mode = record.get("permissionMode")
                    if isinstance(mode, str) and mode.strip():
                        signals["permission_mode"] = mode.strip()
    except OSError:
        pass
    return signals


def _read_payload() -> dict | None:
    try:
        raw = sys.stdin.read()
    except Exception:
        return None
    if not raw or not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _project_dir(payload: dict) -> Path | None:
    root = _find_repo_root()
    if root is None:
        return None
    project = resolve_project(payload, repo_root=root)
    if not project:
        return None
    project_dir = root / "projects" / project
    return project_dir if project_dir.is_dir() else None


def _documented_datasets_snapshot(project_dir: Path, observed_at: str) -> dict | None:
    """Snapshot datasets documented in REPORT.md, never execution-time truth."""
    report_path = project_dir / "REPORT.md"
    try:
        report_bytes = report_path.read_bytes()
    except OSError:
        return None
    datasets = _datasets_from_report(project_dir)
    if not datasets:
        return None
    return {
        "observed_at": observed_at,
        "report_hash": "sha256:" + hashlib.sha256(report_bytes).hexdigest(),
        "datasets": datasets,
    }


def _build_runtime(session_id: str, payload: dict, project_dir: Path) -> dict:
    """Build one atomic, best-effort observation for one session."""
    observed_at = _now_iso()
    # The SessionStart payload omits model + permission mode; recover them from
    # the transcript. Payload values still win when present (tests inject them,
    # and a future hook may supply them directly).
    transcript_signals = _agent_signals_from_transcript(payload)
    agent = {"beril_version": __version__}
    model = (
        payload.get("model")
        or payload.get("model_id")
        or transcript_signals.get("model_id")
    )
    if model:
        agent["model_id"] = model
    effort = payload.get("effort")
    effort = (
        effort.get("level")
        if isinstance(effort, dict)
        else (effort or os.environ.get("CLAUDE_EFFORT"))
    )
    if effort:
        agent["effort"] = effort

    activity: dict = {}
    source = payload.get("source")
    if source:
        activity["source"] = source
    mode = payload.get("permission_mode") or transcript_signals.get("permission_mode")
    if mode:
        activity["permission_mode"] = mode

    snapshot = {
        "session_id": session_id,
        "observed_at": observed_at,
        "tenant": TENANT,
        "agent": agent,
        "activity": activity,
    }
    code = _git_info(project_dir.parent.parent, project_dir / RUNTIME_FILE)
    if code:
        snapshot["code"] = code
    actor = _actor(project_dir)
    if actor:
        snapshot["actor"] = actor
    datasets = _documented_datasets_snapshot(project_dir, observed_at)
    if datasets:
        snapshot["documented_datasets_snapshot"] = datasets
    return snapshot


def block_span(manifest_text: str, key: str) -> tuple[int, int] | None:
    """Character span of a top-level ``<key>:`` block, or None if it is absent.

    A span rather than a rewrite, because `beril.yaml` has two writers that want
    opposite things from the same boundary: `approve_cmd._drop_plan_approval`
    deletes the block, and `_append_stage` below inserts a new list entry at its
    end. Shared so the two can never disagree about where a block stops.

    A hand-rolled scanner rather than a YAML round-trip because `pyyaml` is not
    a core dependency (httpx and certifi are the only two) and `beril.yaml`
    carries inline comments a dumper would eat.

    It lives in THIS module, not next to the approve-time caller, because the
    runtime hook falls back to a bare `python3` when there is no venv — the
    BERDL pod — and `approve_cmd` reaches `tomllib` through its config import,
    which needs 3.11+. Importing it from there made `_append_stage` raise
    ModuleNotFoundError straight into this module's blanket `except`, so every
    stage silently went unstamped on exactly the image the fallback exists for.
    Pinned by `test_audit_cmd_does_not_import_the_cli_modules`.

    Blank and comment lines carry no indentation meaning in YAML, so they cannot
    end the block on their own: absorbed when more block lines follow, excluded
    when the next real line is top-level (they belong to whatever comes after).
    """
    if not key.endswith(":"):
        key += ":"
    offset = 0
    start = end = None
    for line in manifest_text.splitlines(keepends=True):
        if start is not None:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                offset += len(line)  # undecided; `end` stays put unless absorbed
                continue
            if line.startswith((" ", "\t")):
                offset += len(line)
                end = offset  # absorbs any undecided lines passed over above
                continue
            break  # a top-level line — the block ended
        if line.startswith(key):
            start = offset
            offset += len(line)
            end = offset
            continue
        offset += len(line)
    return None if start is None else (start, end)


def _read_runtime(path: Path) -> dict | None:
    """The runtime state at ``path``, or None if it is missing or unreadable."""
    try:
        state = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def _write_runtime(path: Path, state: dict) -> None:
    """Atomic, because the status line and the hook both write this file."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    os.replace(tmp, path)


def record_session_cost(project_dir: Path, session_id: str | None, usd) -> None:
    """Record the status line's session-to-date USD on this session's record.

    Called from ``.claude/statusline.sh`` — see ``COST_OBSERVER`` for why that is
    the only caller there can be. The harness sums this across every API call in
    the session, subagents included; this only stores it.

    **A zero is never recorded.** An unobserved session has no ``cost`` key at
    all, which is what lets a genuinely free stage be told apart from an
    unwatched one when the ledger is stamped. That is the same rule the rest of
    this module follows: fields are omitted when absent, never fabricated.

    Writes only when the *cents* value changed, so an ordinary turn costs one
    small read and no write — the status line renders every turn, and this file
    is also written by the hook.
    """
    if not isinstance(session_id, str) or not session_id.strip():
        return
    try:
        usd = round(float(usd), 2)
    except (TypeError, ValueError):
        return
    if usd <= 0:
        return
    session_id = session_id.strip()

    project_dir = Path(project_dir)
    path = project_dir / RUNTIME_FILE
    state = _read_runtime(path) or {}
    sessions = state.get("sessions")
    if state.get("schema_version") != RUNTIME_SCHEMA_VERSION or not isinstance(
        sessions, list
    ):
        # Same rule as the snapshot writer: a missing, corrupt, or non-schema-2
        # file starts a fresh v2 history rather than being merged into.
        state, sessions = {}, []
    sessions = [item for item in sessions if isinstance(item, dict)]

    record = next(
        (item for item in sessions if item.get("session_id") == session_id), None
    )
    if record is None:
        # The status line resolves a project by signals the hook does not have
        # (cwd at launch, /add-dir), so it can be first to know about a session.
        record = {"session_id": session_id, "observed_at": _now_iso()}
        sessions.append(record)

    prior = record.get("cost")
    prior = prior if isinstance(prior, dict) else {}
    if prior.get("usd") == usd:
        return
    record["cost"] = {
        "usd": usd,
        # Preserved, never reset: it is the portion already attributed to a
        # closed stage, and a session outlives the stage it started in.
        "counted_usd": prior.get("counted_usd", 0.0),
        "observed_at": _now_iso(),
        "observer": COST_OBSERVER,
    }
    state.update(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "project": project_dir.name,
            "sessions": sessions,
        }
    )
    _write_runtime(path, state)


def _project_status(project_dir: Path) -> str | None:
    """The lifecycle ``status:`` from beril.yaml, or None if absent."""
    try:
        text = (project_dir / "beril.yaml").read_text()
    except OSError:
        return None
    match = _STATUS.search(text)
    return match.group(1) if match else None


def _stage_entry(sessions: list[dict], stage: str, ended_at: str) -> dict:
    """The ledger entry for a stage that just ended.

    The stage's cost is the *uncounted remainder* of every session's spend, not
    the spend of sessions that started inside it. A session outlives the stage
    it started in, so a window would misattribute a long research session's
    later work — and a fresh worktree (whose ``counted_usd`` starts at zero for
    its own new sessions only) would double-count under any running total.
    """
    total = 0.0
    observed = 0
    for session in sessions:
        cost = session.get("cost")
        if not isinstance(cost, dict):
            continue
        try:
            # max(): the harness total is monotonic within a session, but a
            # remainder must never go negative if that ever stops being true.
            delta = max(
                0.0, float(cost.get("usd") or 0) - float(cost.get("counted_usd") or 0)
            )
        except (TypeError, ValueError):
            continue
        if delta > 0:
            total += delta
            observed += 1
    entry = {"stage": stage, "ended_at": ended_at, "sessions_observed": observed}
    if observed:
        # Omitted, never zeroed, when nothing was observed: `usd: 0.00` reads as
        # "this stage was free", a missing key reads as "nobody watched".
        entry["usd"] = round(total, 2)
    return entry


def _append_stage(manifest: Path, entry: dict) -> bool:
    """Append one entry to beril.yaml's ``agent_cost`` block. True if written.

    Appended in place rather than rebuilt from the runtime history, because
    ``runtime.json`` is gitignored — the manifest is the durable record, and
    rebuilding it would need to read YAML back. ``block_span`` is shared with
    ``beril approve``, the only other writer of this file.
    """
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return False
    rendered = f"    - stage: {entry['stage']}\n"
    rendered += f'      ended_at: "{entry["ended_at"]}"\n'
    if "usd" in entry:
        rendered += f"      usd: {entry['usd']:.2f}\n"
    rendered += f"      sessions_observed: {entry['sessions_observed']}\n"

    span = block_span(text, "agent_cost:")
    if span is None:
        if text and not text.endswith("\n"):
            text += "\n"
        text += (
            "agent_cost:\n"
            "  observed_by: claude-code\n"
            f'  note: "{AGENT_COST_NOTE}"\n'
            "  stages:\n"
        ) + rendered
    else:
        text = text[: span[1]] + rendered + text[span[1] :]
    try:
        manifest.write_text(text, encoding="utf-8")
    except OSError:
        return False
    return True


def _stamp_stage_boundary(project_dir: Path, state: dict, sessions: list[dict]) -> bool:
    """Close the stage that just ended when beril.yaml's status has changed.

    The boundary is detected here rather than by the skills that perform it
    because there is nowhere else to put it: ``approve_cmd`` is the only code in
    the repo that writes ``beril.yaml``, and it records ``plan_approval``, not
    ``status`` — ``research-plan/SKILL.md`` says outright that "Setting
    ``status: active`` records nothing". All six lifecycle transitions are
    agent-written YAML with no code path, so a stamp hung off an existing writer
    would cover one boundary out of six. The PostToolUse hook fires on the very
    edit that performs a transition, and so witnesses all six.

    Mutates ``state`` and ``sessions`` in place; the caller writes runtime.json
    once. Returns True when it changed something.

    ponytail: last-writer-wins across concurrent sessions in one clone. Each
    file stays valid (os.replace), but two simultaneous stamps could duplicate
    an entry or lose a counted_usd update. Per-project locking if it is ever
    actually observed.
    """
    status = _project_status(project_dir)
    if not status:
        return False
    last = state.get("last_status")
    if last == status:
        return False
    state["last_status"] = status
    if not last:
        # Nothing to close. runtime.json is gitignored, so this is also what a
        # fresh worktree does on its first snapshot — spend earned in another
        # clone was either already stamped there or was never observed here.
        return True
    if not _append_stage(
        project_dir / "beril.yaml", _stage_entry(sessions, last, _now_iso())
    ):
        state["last_status"] = last  # nothing recorded — retry on the next write
        return False
    for session in sessions:
        cost = session.get("cost")
        if isinstance(cost, dict) and "usd" in cost:
            cost["counted_usd"] = cost["usd"]
    return True


def _effective_session(session: dict) -> dict:
    """Remove observation timestamps before idempotency comparison."""
    effective = {key: value for key, value in session.items() if key != "observed_at"}
    datasets = effective.get("documented_datasets_snapshot")
    if isinstance(datasets, dict):
        effective["documented_datasets_snapshot"] = {
            key: value for key, value in datasets.items() if key != "observed_at"
        }
    return effective


def run_runtime_snapshot(args: argparse.Namespace) -> int:
    """SessionStart hook: append or replace one atomic session record. Always 0."""
    try:
        payload = _read_payload()
        if payload is None:
            return 0
        session_id = payload.get("session_id") or os.environ.get(
            "CLAUDE_CODE_SESSION_ID"
        )
        if not isinstance(session_id, str) or not session_id.strip():
            return 0
        project_dir = _project_dir(payload)
        if project_dir is None:
            return 0
        path = project_dir / RUNTIME_FILE
        existing = _read_runtime(path) or {}
        snapshot = _build_runtime(session_id.strip(), payload, project_dir)
        if existing.get("schema_version") == RUNTIME_SCHEMA_VERSION and isinstance(
            existing.get("sessions"), list
        ):
            state = dict(existing)
            sessions = [item for item in existing["sessions"] if isinstance(item, dict)]
        else:
            # A missing, corrupt, or non-schema-2 file starts a fresh v2 history.
            state = {}
            sessions = []

        prior_index = next(
            (
                index
                for index, item in enumerate(sessions)
                if item.get("session_id") == session_id.strip()
            ),
            None,
        )
        changed = True
        if prior_index is not None:
            # Cost is the one field this writer cannot observe (see
            # COST_OBSERVER), so carry it across the replace rather than
            # dropping it. The value is identical, so the idempotency check
            # below is unaffected by having done so.
            prior_cost = sessions[prior_index].get("cost")
            if isinstance(prior_cost, dict):
                snapshot["cost"] = prior_cost
            if _effective_session(sessions[prior_index]) == _effective_session(
                snapshot
            ):
                changed = False
            else:
                sessions[prior_index] = snapshot
        else:
            sessions.append(snapshot)

        state.update(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "project": project_dir.name,
                "updated_at": snapshot["observed_at"],
                "sessions": sessions,
            }
        )
        # Runs even when the session record is unchanged — which is the normal
        # case here, not an edge one. Nothing in a snapshot depends on lifecycle
        # status, so the very edit that performs a transition produces a
        # byte-identical record, and returning early on that would mean the
        # boundary is never witnessed at all.
        if _stamp_stage_boundary(project_dir, state, sessions):
            changed = True
        if not changed:
            return 0
        _write_runtime(path, state)
    except Exception:
        # Best-effort: snapshotting must never block a session.
        return 0
    return 0
