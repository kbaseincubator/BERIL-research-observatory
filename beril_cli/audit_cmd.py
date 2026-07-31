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
from beril_cli.journal import QUERY_LOCATOR, append_event
from beril_cli.project_resolution import resolve_project

RUNTIME_FILE = "runtime.json"
RUNTIME_SCHEMA_VERSION = "2.0"

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
        existing = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except (json.JSONDecodeError, ValueError):
                existing = {}
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
        if prior_index is not None:
            if _effective_session(sessions[prior_index]) == _effective_session(
                snapshot
            ):
                return 0
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
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        os.replace(tmp, path)
    except Exception:
        # Best-effort: snapshotting must never block a session.
        return 0
    return 0


def run_capture_event(args: argparse.Namespace) -> int:
    """Append one evidence event to the project journal. Always returns 0.

    Agent-invoked from the ``berdl-query`` / ``synthesize`` skills, so every
    failure warns on stderr and still exits 0: losing an evidence record must
    never derail the analysis that produced it. The warning goes to the model,
    which is the one party that can retry with a corrected locator.

    Queries are the only kind this verb writes. ``kind`` stays in the record
    because the journal is a general evidence log, but exposing it as a flag
    would let an unvalidated locator in under a kind nothing reads yet — a
    record no resolver could ever use. A second kind can add the flag along
    with the grammar that validates it.
    """
    try:
        locator = (args.locator or "").strip()
        if not QUERY_LOCATOR.fullmatch(locator):
            print(
                f"beril capture-event: '{locator}' is not a q:<id> locator — "
                "nothing recorded",
                file=sys.stderr,
            )
            return 0
        # Checked here rather than as an argparse ``required``, which would exit
        # 2 before this function runs and make "always exits 0" true except in
        # one case. A record with no SQL resolves a pointer to nothing
        # re-runnable, which is worse than leaving the query unregistered.
        if not (args.payload or "").strip():
            print(
                "beril capture-event: --payload is the SQL that ran and cannot "
                "be empty — nothing recorded",
                file=sys.stderr,
            )
            return 0
        # resolve_project reads cwd from the payload (it is built for hooks), so
        # an agent-invoked call has to supply it or the documented cwd fallback
        # silently never fires.
        project_dir = _project_dir(
            {"project": args.project} if args.project else {"cwd": os.getcwd()}
        )
        if project_dir is None:
            print(
                "beril capture-event: no project resolved — nothing recorded",
                file=sys.stderr,
            )
            return 0
        append_event(
            project_dir,
            kind="query",
            locator=locator,
            payload=args.payload,
            session_id=args.session or os.environ.get("CLAUDE_CODE_SESSION_ID"),
        )
    except Exception as exc:
        print(f"beril capture-event: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0
