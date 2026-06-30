"""beril runtime-snapshot — best-effort runtime provenance.

A single writer, driven by a SessionStart hook: it reads the hook's JSON payload
from stdin, resolves the active project from a ``projects/<id>/`` path in the
payload, and writes/merges a per-project ``runtime.json``. Strictly best-effort —
it swallows every error and always returns 0, so a failed snapshot never blocks a
session.

The snapshot is shaped loosely to **W3C PROV** (https://www.w3.org/TR/prov-overview/):
the project is the *entity*, the session is the *activity*, and beril + the model
are the *agent*. This is the passive execution-provenance pattern of
Sumatra/noWorkflow — capture what produced the record without re-running it.

The file is named ``runtime.json`` (not ``provenance.json``) because on main
"provenance" already means source/lineage (e.g. a project's ``data/PROVENANCE.md``
and the Atlas's source frontmatter); this artifact is the narrower *runtime /
execution* facet. It is **non-authoritative** and feeds no trust tier — an
inspectable record of how an analysis was produced, alongside ``beril.yaml``
(authoritative) and ``claims.json`` (the claims ledger).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from beril_cli import __version__

#: Find a ``projects/<id>`` segment at a path-segment boundary — start of string,
#: a slash (``/repo/projects/p1``), or whitespace (``ls projects/p1``). This
#: rejects glued tokens like ``myprojects/`` and ``x-projects/`` that are not a
#: real path segment.
_PROJECT_PATH = re.compile(r"(?:^|[\s/])projects/([^/\s]+)")

RUNTIME_FILE = "runtime.json"


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md (repo marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _build_runtime(project: str, payload: dict) -> dict:
    """A PROV-shaped snapshot: entity (project) + activity (session) + agent."""
    agent = {"beril_version": __version__}
    model = payload.get("model") or payload.get("model_id")
    if model:
        agent["model_id"] = model

    activity: dict = {}
    session_id = payload.get("session_id")
    if session_id:
        activity["session_id"] = session_id
    mode = payload.get("permission_mode")
    if mode:
        activity["permission_mode"] = mode

    return {"project": project, "updated_at": _now_iso(), "agent": agent, "activity": activity}


def run_runtime_snapshot(args: argparse.Namespace) -> int:
    """SessionStart hook: write/merge the project's runtime.json. Always 0.

    The ``agent`` and ``activity`` blocks are deep-merged so a later snapshot that
    lacks a field (e.g. model_id) does not clobber one an earlier snapshot
    captured; sibling keys written by other tools are preserved.
    """
    try:
        payload = _read_payload()
        if payload is None:
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
        snapshot = _build_runtime(project_dir.name, payload)
        merged = {**existing, **snapshot}
        for block in ("agent", "activity"):
            existing_block = existing.get(block)
            if isinstance(existing_block, dict):
                merged[block] = {**existing_block, **snapshot[block]}
        path.write_text(json.dumps(merged, indent=2) + "\n")
    except Exception:
        # Best-effort: snapshotting must never block a session.
        return 0
    return 0
