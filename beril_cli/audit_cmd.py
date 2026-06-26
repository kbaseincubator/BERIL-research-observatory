"""beril trace-append / provenance-snapshot — best-effort runtime provenance.

Two writers driven by settings.json hooks (PostToolUse / SessionStart). Each
reads the hook's JSON payload from stdin, resolves the active project from a
``projects/<id>/`` path in the payload, and writes a per-project artifact:

- ``trace-append``       appends one secret-redacted JSON line to TRACE.jsonl.
- ``provenance-snapshot`` writes/merges a runtime block into provenance.json.

Both are STRICTLY best-effort: they swallow every error and always return 0, so
a failed audit never blocks a turn. Ported from beril-pi-agent
lib/project-audit.ts (redaction, append, snapshot/merge).

Neither artifact is authoritative and neither feeds a trust tier — they are an
inspectable record of what ran, alongside beril.yaml (authoritative) and
claims.json (gate-validated).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from beril_cli import __version__

#: Object keys matching this are replaced with ``[redacted]`` before any write.
SECRET_KEY = re.compile(r"(token|secret|password|authorization|api[_-]?key|credential)", re.IGNORECASE)
#: Secrets embedded inside ordinary string VALUES (a Bash command, a .env file's
#: contents) — a ``<secret-name>=value`` / ``: value`` assignment, or a bearer/basic
#: auth token. Best-effort heuristic, NOT a guarantee (a bare keyword-less token
#: cannot be detected without false positives); the value is redacted up to the
#: next shell/quote/newline delimiter.
_SECRET_ASSIGN = re.compile(
    r"(?i)([\w.\-]*(?:token|secret|password|authorization|api[_-]?key|credential)[\w.\-]*\s*[:=]\s*)"
    r"([^\n\r\"';&|]+)"
)
_BEARER = re.compile(r"(?i)\b(bearer|basic)\s+([^\s\"';&|]+)")
MAX_STRING = 240
MAX_ARRAY = 50
#: Find a ``projects/<id>`` segment at a path-segment boundary — start of string,
#: a slash (``/repo/projects/p1``), or whitespace (``ls projects/p1``). This
#: rejects glued tokens like ``myprojects/`` and ``x-projects/`` that are not a
#: real path segment.
_PROJECT_PATH = re.compile(r"(?:^|[\s/])projects/([^/\s]+)")

TRACE_FILE = "TRACE.jsonl"
PROVENANCE_FILE = "provenance.json"


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md (repo marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scrub_secrets(text: str) -> str:
    """Redact secrets embedded in a string value (best-effort heuristic)."""
    text = _SECRET_ASSIGN.sub(lambda m: m.group(1) + "[redacted]", text)
    text = _BEARER.sub(lambda m: m.group(1) + " [redacted]", text)
    return text


def redact_for_trace(value):
    """Recursively redact secrets and cap payload size before writing.

    Object keys matching :data:`SECRET_KEY` become ``"[redacted]"``; secrets
    embedded inside string VALUES (``KEY=secret`` / bearer tokens in a command or
    a written ``.env``) are scrubbed via :func:`_scrub_secrets`; arrays are capped
    at 50 elements; strings longer than 240 chars are truncated with an ellipsis.
    Mirrors the reference (array-first, then object, then string), with the added
    value-level scrubbing so a non-secret-named field can't leak a credential.
    """
    if isinstance(value, list):
        return [redact_for_trace(v) for v in value[:MAX_ARRAY]]
    if isinstance(value, dict):
        return {
            k: "[redacted]" if SECRET_KEY.search(str(k)) else redact_for_trace(v)
            for k, v in value.items()
        }
    if isinstance(value, str):
        scrubbed = _scrub_secrets(value)
        return scrubbed if len(scrubbed) <= MAX_STRING else scrubbed[:MAX_STRING] + "..."
    return value


def _iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _iter_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _iter_strings(v)


def resolve_project(payload: dict) -> str | None:
    """Resolve the active project id from a ``projects/<id>/`` path in the payload.

    Prefers a path in ``tool_input`` (most specific) over ``cwd``. Returns None
    when no project path is present — the caller then writes nothing.
    """
    candidates = list(_iter_strings(payload.get("tool_input")))
    cwd = payload.get("cwd")
    if isinstance(cwd, str):
        candidates.append(cwd)
    for s in candidates:
        m = _PROJECT_PATH.search(s)
        if m:
            return m.group(1)
    return None


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
    project = resolve_project(payload)
    if not project:
        return None
    root = _find_repo_root()
    if root is None:
        return None
    project_dir = root / "projects" / project
    return project_dir if project_dir.is_dir() else None


def run_trace_append(args: argparse.Namespace) -> int:
    """PostToolUse hook: append one redacted trace row. Always returns 0."""
    try:
        payload = _read_payload()
        if payload is None:
            return 0
        project_dir = _project_dir(payload)
        if project_dir is None:
            return 0
        row = redact_for_trace(
            {
                "at": _now_iso(),
                "project": project_dir.name,
                "event": payload.get("hook_event_name") or "PostToolUse",
                "tool": payload.get("tool_name"),
                "tool_call_id": payload.get("tool_use_id"),
                "input": payload.get("tool_input"),
            }
        )
        with (project_dir / TRACE_FILE).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception:
        # Best-effort audit trail; never interrupt the turn.
        return 0
    return 0


def _build_provenance(project: str, payload: dict) -> dict:
    runtime = {"beril_package_version": __version__}
    mode = payload.get("permission_mode")
    if mode:
        runtime["permission_mode"] = mode
    session_id = payload.get("session_id")
    if session_id:
        runtime["session_id"] = session_id
    model = payload.get("model") or payload.get("model_id")
    if model:
        runtime["model_id"] = model
    return {"project": project, "updated_at": _now_iso(), "runtime": runtime}


def run_provenance_snapshot(args: argparse.Namespace) -> int:
    """SessionStart hook: write/merge the runtime provenance block. Returns 0."""
    try:
        payload = _read_payload()
        if payload is None:
            return 0
        project_dir = _project_dir(payload)
        if project_dir is None:
            return 0
        path = project_dir / PROVENANCE_FILE
        existing = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except (json.JSONDecodeError, ValueError):
                existing = {}
        snapshot = _build_provenance(project_dir.name, payload)
        merged = {**existing, **snapshot}
        # Deep-merge the runtime block so a later snapshot that lacks a field
        # (e.g. model_id) does not clobber one an earlier snapshot captured.
        existing_runtime = existing.get("runtime")
        if isinstance(existing_runtime, dict):
            merged["runtime"] = {**existing_runtime, **snapshot["runtime"]}
        path.write_text(json.dumps(merged, indent=2) + "\n")
    except Exception:
        return 0
    return 0
