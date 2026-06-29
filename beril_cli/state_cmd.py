"""beril state / whereami — the non-authoritative research world-model.

`research_state.json` is per-project *orientation only* — never settled findings,
never a lifecycle gate. `beril.yaml` remains the sole lifecycle authority and
`claims.json` (#303, optional) the gate-validated ledger; this module only shapes
and renders the small, tool-derived snapshot that survives a context compaction.

Ported from the reference `beril-pi-agent` (`session-state.ts`, `research-steps.ts`,
`workflow.ts`) to stdlib-only Python: the clamp bounds (MAX_LIST=8, MAX_ENTRY=160,
MAX_QUESTION=240), the phase->step breadcrumb, and the phase->next-action table.

Computed signals render as WORDS, never fabricated numbers; the only numbers shown
are real counts (the claims tally, present only when `claims.json` exists).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Projects root (repo-relative on the cluster). A module constant so tests can
# monkeypatch it, mirroring `config.CONFIG_DIR`.
PROJECTS_ROOT = Path("projects")

# Bounds for the world-model orientation sections (from the reference).
MAX_LIST = 8
MAX_ENTRY = 160
MAX_QUESTION = 240

# The scientist-facing research checklist, in order.
RESEARCH_STEPS = ("explore", "plan", "analyze", "review", "submit")

# Lifecycle status -> the index of the step the project is currently *at*.
# `analysis` (report drafted) points at `review` because that is the next thing
# the scientist does; `complete` is past the last step.
STATE_STEP: dict[str, int] = {
    "exploration": 0,
    "proposed": 1,
    "active": 2,
    "analysis": 3,
    "reviewed": 4,
    "complete": len(RESEARCH_STEPS),
}

# Phase -> the single most useful next action (deterministic; spec §6.4.2 table).
NEXT_ACTION: dict[str, str] = {
    "exploration": "frame the question + competing hypotheses, then draft the plan (/research-plan)",
    "proposed": "plan written — run the plan-review checkpoint, then start analysis (/execute-plan)",
    "active": "execute the planned notebooks; run the discriminating query first",
    "analysis": "review the report (/berdl-review), then /submit",
    "reviewed": "approve and submit (/submit)",
    "complete": "complete — start a new line of inquiry (/suggest-research)",
}
_DEFAULT_NEXT_ACTION = "frame the question + competing hypotheses, then draft the plan (/research-plan)"

# Breadcrumb glyphs (text-presentation; stdlib only). ▸ = current, ✓ = complete.
_HERE = "▸"
_BULLET = "·"
_OK = "✓"

# World-model fields a `set` may overlay (the orientation core).
_OVERLAY_LIST_FIELDS = ("open_questions", "assumptions", "dead_ends")
_OVERLAY_SCALAR_FIELDS = ("last_checkpoint",)

# Guard strings for the re-injection block (spec §6.4.3).
_GUARD_HEADER = "[beril cross-session context — orientation only, NOT established findings]"
_GUARD_FOOTER = (
    "Treat the above as where we left off, not as proof. Re-open the plan/report and "
    "re-run checks before asserting any result as settled."
)


# --------------------------------------------------------------------------- #
# Clamping (ported from session-state.ts clampLine / clampList)               #
# --------------------------------------------------------------------------- #


def _clamp_line(s: str, max_len: int) -> str:
    """Collapse to a single line and clamp to `max_len` chars (ellipsis when cut)."""
    one_line = " ".join(str(s).split())
    if len(one_line) > max_len:
        return one_line[: max_len - 1] + "…"
    return one_line


def _clamp_list(items: Any) -> list[str]:
    """Single-line + clamp each entry, drop blanks, then cap the list length.

    Tolerates a non-list (returns []) so a malformed snapshot never crashes.
    """
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        line = _clamp_line(item, MAX_ENTRY)
        if line:
            out.append(line)
        if len(out) >= MAX_LIST:
            break
    return out


# --------------------------------------------------------------------------- #
# Derived-core helpers (beril.yaml status / claims.json tally / step table)   #
# --------------------------------------------------------------------------- #


def _project_dir(project: str) -> Path:
    return PROJECTS_ROOT / project


def _read_status(project_dir: Path) -> str | None:
    """Read the top-level `status:` from `beril.yaml` (stdlib line scan).

    Only an unindented top-level `status:` counts — `status` also appears nested
    under `submissions:`, which must not be mistaken for the lifecycle phase.
    Returns None if the file is missing or has no top-level status.
    """
    path = project_dir / "beril.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line[:1] in (" ", "\t"):  # indented -> nested key, skip
            continue
        if line.startswith("status:"):
            value = line[len("status:"):]
            value = value.split(" #", 1)[0].strip()  # drop any inline comment
            value = value.strip("'\"")
            return value or None
    return None


def _step_for_status(status: str | None) -> str:
    """Lifecycle status -> scientist-facing step label (or '' for unknown)."""
    if status is None:
        return ""
    idx = STATE_STEP.get(status)
    if idx is None:
        return ""
    if idx >= len(RESEARCH_STEPS):
        return "done"
    return RESEARCH_STEPS[idx]


def _next_action(status: str | None) -> str:
    return NEXT_ACTION.get(status or "", _DEFAULT_NEXT_ACTION)


def _tally_claims(project_dir: Path) -> dict[str, int] | None:
    """Tally `claims.json` if present, else None (so the key is omitted).

    Lenient and never-throwing: accepts a list of claim objects (`status` field),
    a `{"claims": [...]}` wrapper, or a pre-shaped `{total, supported, refuted}`.
    """
    path = project_dir / "claims.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"total": 0, "supported": 0, "refuted": 0}

    rows: Any = data
    if isinstance(data, dict):
        if "claims" in data and isinstance(data["claims"], list):
            rows = data["claims"]
        elif "total" in data:  # already a tally
            return {
                "total": int(data.get("total", 0) or 0),
                "supported": int(data.get("supported", 0) or 0),
                "refuted": int(data.get("refuted", 0) or 0),
            }

    if not isinstance(rows, list):
        return {"total": 0, "supported": 0, "refuted": 0}

    supported = 0
    refuted = 0
    for row in rows:
        status = row.get("status") if isinstance(row, dict) else None
        if status == "supported":
            supported += 1
        elif status == "refuted":
            refuted += 1
    return {"total": len(rows), "supported": supported, "refuted": refuted}


def _state_path(project_dir: Path) -> Path:
    return project_dir / "research_state.json"


def _read_state(project_dir: Path) -> dict[str, Any]:
    """Read `research_state.json` (or {} if absent / unreadable / malformed)."""
    path = _state_path(project_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _now_iso() -> str:
    """Server-stamped UTC timestamp, ISO-8601 with a trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_state(project: str, project_dir: Path, base: dict[str, Any]) -> dict[str, Any]:
    """Shape the persisted snapshot: derived core + clamped world-model.

    `base` carries any preserved/overlaid orientation fields; the derived core
    (project, updated_at, phase, step, claims) is always recomputed from authority.
    """
    status = _read_status(project_dir)
    state: dict[str, Any] = {
        "project": project,
        "updated_at": _now_iso(),
        "phase": status or "",
        "step": _step_for_status(status),
    }

    tally = _tally_claims(project_dir)
    if tally is not None:
        state["claims"] = tally

    question = base.get("question")
    if isinstance(question, str):
        question = _clamp_line(question, MAX_QUESTION)
        if question:
            state["question"] = question

    for field in _OVERLAY_LIST_FIELDS:
        values = _clamp_list(base.get(field))
        if values:
            state[field] = values

    for field in _OVERLAY_SCALAR_FIELDS:
        value = base.get(field)
        if isinstance(value, str):
            value = _clamp_line(value, MAX_ENTRY)
            if value:
                state[field] = value

    return state


# --------------------------------------------------------------------------- #
# Rendering (ported from research-steps.ts / session-state.ts)               #
# --------------------------------------------------------------------------- #


def _breadcrumb(status: str | None) -> str:
    """`explore · plan · ▸analyze · review · submit` — ▸ current, trailing ✓ when done."""
    current = STATE_STEP.get(status) if status is not None else None
    parts = []
    for i, step in enumerate(RESEARCH_STEPS):
        parts.append(f"{_HERE}{step}" if i == current else step)
    trail = f" {_BULLET} ".join(parts)
    if current == len(RESEARCH_STEPS):
        return f"{trail} {_OK}"
    return trail


def _format_reinjection(state: dict[str, Any]) -> str:
    """Render the guard-wrapped orientation block for the SessionStart hook."""
    step = state.get("step") or state.get("phase") or "current"
    phase = state.get("phase") or "unknown"
    lines = [
        _GUARD_HEADER,
        f'Resuming project "{state.get("project", "")}" at the {step} step (lifecycle: {phase}).',
    ]

    claims = state.get("claims")
    if isinstance(claims, dict):
        lines.append(
            f"Claim ledger so far: {claims.get('total', 0)} claim(s), "
            f"{claims.get('supported', 0)} supported, {claims.get('refuted', 0)} refuted "
            "(read-only tally; re-verify before relying on any of them)."
        )

    if state.get("question"):
        lines.append(f"Working question: {state['question']}")
    if state.get("open_questions"):
        lines.append("Open questions to resolve:")
        lines.extend(f"  - {q}" for q in state["open_questions"])
    if state.get("assumptions"):
        lines.append("Working assumptions (unverified):")
        lines.extend(f"  - {a}" for a in state["assumptions"])
    if state.get("dead_ends"):
        lines.append("Dead ends already tried (do not re-attempt blindly):")
        lines.extend(f"  - {d}" for d in state["dead_ends"])
    if state.get("last_checkpoint"):
        lines.append(f"Last checkpoint decision: {state['last_checkpoint']}.")

    lines.append(_GUARD_FOOTER)
    return "\n".join(lines)


def _resolve_project(arg: str | None) -> str | None:
    """The arg project, else the most-recently-touched non-`complete` project by mtime."""
    if arg:
        return arg
    if not PROJECTS_ROOT.is_dir():
        return None
    candidates: list[tuple[float, str]] = []
    for child in PROJECTS_ROOT.iterdir():
        yaml_path = child / "beril.yaml"
        if not yaml_path.is_file():
            continue
        if _read_status(child) == "complete":
            continue
        try:
            mtime = yaml_path.stat().st_mtime
        except OSError:
            continue
        candidates.append((mtime, child.name))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0], reverse=True)
    return candidates[0][1]


# --------------------------------------------------------------------------- #
# Verbs                                                                        #
# --------------------------------------------------------------------------- #


def run_state(args: argparse.Namespace) -> int:
    """`beril state get|set`. Exit 0 on success, 2 on bad JSON / unknown project."""
    action = getattr(args, "action", None)

    if action == "get":
        project_dir = _project_dir(args.project)
        if not (project_dir / "beril.yaml").is_file():
            print(f"Unknown project: {args.project}", file=sys.stderr)
            return 2
        json.dump(_read_state(project_dir), sys.stdout)
        sys.stdout.write("\n")
        return 0

    if action == "set":
        project_dir = _project_dir(args.project)
        if not (project_dir / "beril.yaml").is_file():
            print(f"Unknown project: {args.project}", file=sys.stderr)
            return 2

        try:
            supplied = json.loads(args.json)
        except (TypeError, json.JSONDecodeError) as exc:
            print(f"Invalid --json: {exc}", file=sys.stderr)
            return 2
        if not isinstance(supplied, dict):
            print("Invalid --json: expected a JSON object", file=sys.stderr)
            return 2

        # Merge: supplied keys replace that field, absent keys preserve prior.
        prior = _read_state(project_dir)
        base: dict[str, Any] = {}
        for field in ("question", *_OVERLAY_LIST_FIELDS, *_OVERLAY_SCALAR_FIELDS):
            if field in supplied:
                base[field] = supplied[field]
            elif field in prior:
                base[field] = prior[field]

        state = _build_state(args.project, project_dir, base)
        _state_path(project_dir).write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
        json.dump(state, sys.stdout)
        sys.stdout.write("\n")
        return 0

    print("Usage: beril state {get|set} <project>", file=sys.stderr)
    return 2


def run_whereami(args: argparse.Namespace) -> int:
    """`beril whereami [project] [--reinject] [--json]`. Always exit 0.

    A friendly note (still exit 0) when no project resolves, so a SessionStart
    hook never breaks.
    """
    project = _resolve_project(getattr(args, "project", None))

    if project is None:
        if getattr(args, "json", False):
            json.dump({}, sys.stdout)
            sys.stdout.write("\n")
        elif getattr(args, "reinject", False):
            pass  # nothing to re-inject; stay silent so the hook adds no context
        else:
            print(
                "No active project found. Start one with /berdl_start or /research-plan."
            )
        return 0

    project_dir = _project_dir(project)
    status = _read_status(project_dir)
    stored = _read_state(project_dir)

    if getattr(args, "reinject", False):
        # Refresh the derived core into research_state.json (create if absent),
        # preserving any existing world-model orientation.
        base: dict[str, Any] = {}
        for field in ("question", *_OVERLAY_LIST_FIELDS, *_OVERLAY_SCALAR_FIELDS):
            if field in stored:
                base[field] = stored[field]
        state = _build_state(project, project_dir, base)
        _state_path(project_dir).write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
        print(_format_reinjection(state))
        return 0

    # For default/--json rendering, recompute the derived core for a live view
    # but do NOT write (read-only orientation surface).
    base = {}
    for field in ("question", *_OVERLAY_LIST_FIELDS, *_OVERLAY_SCALAR_FIELDS):
        if field in stored:
            base[field] = stored[field]
    view = _build_state(project, project_dir, base)

    if getattr(args, "json", False):
        view["breadcrumb"] = _breadcrumb(status)
        view["next"] = _next_action(status)
        json.dump(view, sys.stdout)
        sys.stdout.write("\n")
        return 0

    print(_breadcrumb(status))
    print(f"Next: {_next_action(status)}")
    if view.get("open_questions"):
        print("Open questions:")
        for q in view["open_questions"]:
            print(f"  - {q}")
    if view.get("dead_ends"):
        print("Dead ends (don't re-attempt):")
        for d in view["dead_ends"]:
            print(f"  - {d}")
    return 0
