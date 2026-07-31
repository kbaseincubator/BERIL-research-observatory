"""Build and inspect the versioned per-project claims projection.

The author writes confidence and status in REPORT.md. This CLI preserves those
assertions, resolves local evidence conservatively, and separately computes
resolved artifact support. It does not independently prove a claim's status.

The ``## Claims`` micro-format (one ``###`` heading per claim)::

    ## Claims

    ### <claim sentence>
    - confidence: high            # the WORD the author wrote
    - status: supported
    - supports:
      - notebook: notebooks/NB03.ipynb#cell-12 [stream: field-cohort] — "p=0.003, n=412"
      - query: q:enrichment_by_ecotype — "OR 2.4"
    - refutes:
      - paper: PMID:111 — "no enrichment in marine taxa"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from beril_cli.journal import QUERY_LOCATOR, find_query
from beril_cli.science import (
    ARTIFACT_SUPPORT_LEVELS,
    CLAIM_STATUSES,
    EVIDENCE_KINDS,
    claim_id,
    confidence_mismatch,
    confidence_from,
    resolved_artifact_support,
    status_from,
)

_CLAIMS_HEADER = re.compile(r"^##\s+Claims\b", re.IGNORECASE)
_H2 = re.compile(r"^##\s")
_CLAIM_HEADING = re.compile(r"^###\s+(.*)$")
_FIELD = re.compile(
    r"^\s*-\s*(confidence|status|supports|refutes)\s*:\s*(.*)$", re.IGNORECASE
)
_POINTER = re.compile(
    rf"^\s*-\s*({'|'.join(EVIDENCE_KINDS)})\s*:\s*(.*)$", re.IGNORECASE
)
#: A pointer written inline on the ``supports:``/``refutes:`` line (no leading dash).
_INLINE_POINTER = re.compile(
    rf"^({'|'.join(EVIDENCE_KINDS)})\s*:\s*(.*)$", re.IGNORECASE
)
#: An em dash (optionally space-padded) separates a pointer's locator from its exact text.
_EM_DASH = re.compile(r"\s*—\s*")
_STREAM_SUFFIX = re.compile(
    r"\s+\[stream:\s*([A-Za-z0-9][A-Za-z0-9._-]*)\]\s*$", re.IGNORECASE
)
_CELL_ANCHOR = re.compile(r"cell-([1-9][0-9]*)$")
SCHEMA_VERSION = "2.0"


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md (repo marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def _parse_pointer(kind: str, rest: str) -> dict:
    parts = _EM_DASH.split(rest.strip(), maxsplit=1)
    locator = parts[0].strip()
    exact = parts[1].strip() if len(parts) == 2 else ""
    stream_match = _STREAM_SUFFIX.search(locator)
    pointer = {"kind": kind.lower(), "locator": locator, "exact": exact}
    if stream_match:
        pointer["stream"] = stream_match.group(1)
        pointer["locator"] = locator[: stream_match.start()].rstrip()
    return pointer


def _append_inline_pointer(claim: dict, bucket: str, value: str) -> None:
    """Parse a pointer written inline on the ``supports:``/``refutes:`` line.

    Without this, ``- supports: notebook: nb.ipynb#cell-2 — "x"`` would silently
    drop the pointer (only the indented sub-list form would be parsed), wrongly
    dropping evidence from the generated projection.
    """
    m = _INLINE_POINTER.match(value.strip())
    if m:
        claim[bucket].append(_parse_pointer(m.group(1), m.group(2)))


def parse_claims_block(report_md: str) -> list[dict]:
    """Parse the ``## Claims`` section into raw claim dicts (no computation).

    Returns ``[]`` when there is no Claims section. Each claim is
    ``{claim, confidence, status, supports, refutes}``; confidence/status default
    to ``low``/``open`` when the author omits them (nothing to overrun, so no
    mismatch). Sections after the next ``##`` heading are not parsed.
    """
    lines = report_md.splitlines()
    start = next((i for i, ln in enumerate(lines) if _CLAIMS_HEADER.match(ln)), None)
    if start is None:
        return []

    claims: list[dict] = []
    current: dict | None = None
    bucket: str | None = None  # "supports" | "refutes"

    for ln in lines[start + 1 :]:
        if _H2.match(ln):  # next top-level section ends the Claims block
            break
        m = _CLAIM_HEADING.match(ln)
        if m:
            current = {
                "claim": m.group(1).strip(),
                "confidence": "low",
                "status": "open",
                "supports": [],
                "refutes": [],
            }
            claims.append(current)
            bucket = None
            continue
        if current is None:
            continue
        field = _FIELD.match(ln)
        if field:
            key, value = field.group(1).lower(), field.group(2)
            if key == "confidence":
                current["confidence"] = confidence_from(value) or "low"
            elif key == "status":
                current["status"] = status_from(value) or "open"
            elif key == "supports":
                bucket = "supports"
                _append_inline_pointer(current, "supports", value)
            elif key == "refutes":
                bucket = "refutes"
                _append_inline_pointer(current, "refutes", value)
            continue
        pointer = _POINTER.match(ln)
        if pointer:
            current[bucket or "supports"].append(
                _parse_pointer(pointer.group(1), pointer.group(2))
            )

    return claims


def resolve_evidence_pointer(project_dir: Path | None, pointer: dict) -> dict:
    """Return a pointer annotated with a conservative resolution result.

    Notebook locators are project-relative. ``#cell-N`` means the one-based
    ordinal in the notebook's ``cells`` array. Query locators resolve against
    the project's ``journal.jsonl`` — a query grounds a claim only if it was
    captured while it ran.
    """
    resolved = dict(pointer) if isinstance(pointer, dict) else {}
    kind = resolved.get("kind")
    locator = resolved.get("locator")
    if not isinstance(locator, str) or not locator.strip():
        resolved["resolution"] = {"status": "invalid", "reason": "empty-locator"}
        return resolved

    locator = locator.strip()
    resolved["locator"] = locator
    if kind == "query":
        if not QUERY_LOCATOR.fullmatch(locator):
            resolved["resolution"] = {
                "status": "invalid",
                "reason": "malformed-query-locator",
            }
        elif project_dir is None:
            resolved["resolution"] = {
                "status": "unresolved",
                "reason": "project-directory-unavailable",
            }
        else:
            record = find_query(project_dir, locator)
            resolved["resolution"] = (
                {
                    "status": "resolved",
                    "query_id": locator[len("q:") :],
                    "recorded_at": record["ts"],
                }
                if record
                else {"status": "unresolved", "reason": "query-not-recorded"}
            )
        return resolved

    if kind != "notebook":
        resolved["resolution"] = {
            "status": "not-checked",
            "reason": "not-a-local-computed-artifact",
        }
        return resolved

    path_text, separator, anchor = locator.partition("#")
    cell_match = _CELL_ANCHOR.fullmatch(anchor) if separator else None
    if not path_text or "#" in anchor:
        resolved["resolution"] = {
            "status": "invalid",
            "reason": "malformed-notebook-locator",
        }
        return resolved
    if separator and cell_match is None:
        resolved["resolution"] = {
            "status": "invalid",
            "reason": "malformed-cell-reference",
        }
        return resolved
    if project_dir is None:
        resolved["resolution"] = {
            "status": "unresolved",
            "reason": "project-directory-unavailable",
        }
        return resolved

    relative = Path(path_text)
    project_root = project_dir.resolve()
    if relative.is_absolute():
        resolved["resolution"] = {
            "status": "invalid",
            "reason": "notebook-path-must-be-project-relative",
        }
        return resolved
    target = (project_root / relative).resolve()
    if not target.is_relative_to(project_root):
        resolved["resolution"] = {
            "status": "invalid",
            "reason": "notebook-path-outside-project",
        }
        return resolved
    if target.suffix.lower() != ".ipynb":
        resolved["resolution"] = {
            "status": "invalid",
            "reason": "notebook-path-must-end-in-ipynb",
        }
        return resolved
    if not target.is_file():
        resolved["resolution"] = {
            "status": "unresolved",
            "reason": "notebook-not-found",
        }
        return resolved

    result = {
        "status": "resolved",
        "path": target.relative_to(project_root).as_posix(),
    }
    if cell_match is not None:
        cell_number = int(cell_match.group(1))
        try:
            notebook = json.loads(target.read_text(encoding="utf-8"))
            cells = notebook.get("cells") if isinstance(notebook, dict) else None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            cells = None
        if not isinstance(cells, list):
            resolved["resolution"] = {
                "status": "unresolved",
                "reason": "notebook-cells-unreadable",
            }
            return resolved
        if cell_number > len(cells):
            resolved["resolution"] = {
                "status": "unresolved",
                "reason": "cell-not-found",
            }
            return resolved
        result["cell"] = cell_number
    resolved["resolution"] = result
    return resolved


def _evidence_resolution_counts(pointers: list[dict]) -> dict[str, int]:
    counts = {
        status: 0 for status in ("resolved", "unresolved", "invalid", "not-checked")
    }
    for pointer in pointers:
        resolution = pointer.get("resolution") if isinstance(pointer, dict) else None
        status = resolution.get("status") if isinstance(resolution, dict) else "invalid"
        if status in counts:
            counts[status] += 1
    return counts


def _claims_from_state(state: dict | None) -> list[dict]:
    if not isinstance(state, dict):
        return []
    claims = state.get("claims")
    if isinstance(claims, list):
        return [claim for claim in claims if isinstance(claim, dict)]
    return []


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_claim_state(
    project: str,
    report_md: str,
    prior: dict | None = None,
    project_dir: Path | None = None,
) -> dict:
    """Build claims.json v2 from REPORT.md while preserving prior reviewer notes."""
    prior_notes = {
        row.get("claim_id"): row.get("reviewer_notes")
        for row in _claims_from_state(prior)
        if row.get("reviewer_notes")
    }

    claims: list[dict] = []
    for c in parse_claims_block(report_md):
        supports = [
            resolve_evidence_pointer(project_dir, pointer) for pointer in c["supports"]
        ]
        refutes = [
            resolve_evidence_pointer(project_dir, pointer) for pointer in c["refutes"]
        ]
        artifact_support = resolved_artifact_support(supports)
        cid = claim_id(c["claim"])
        claim = {
            "claim_id": cid,
            "claim": c["claim"],
            "author_assertions": {
                "status": c["status"],
                "confidence": c["confidence"],
                "source": "REPORT.md",
            },
            "computed": {
                "resolved_artifact_support": artifact_support,
                "confidence_mismatch": confidence_mismatch(
                    c["confidence"], artifact_support
                ),
                "evidence_resolution": _evidence_resolution_counts(supports + refutes),
            },
            "supports": supports,
            "refutes": refutes,
        }
        if cid in prior_notes:
            claim["reviewer_notes"] = prior_notes[cid]
        claims.append(claim)

    state = {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "updated_at": _now_iso(),
        "report_hash": "sha256:"
        + hashlib.sha256(report_md.encode("utf-8")).hexdigest(),
        "claims": claims,
    }
    state["summary"] = summarize(state)
    return state


def summarize(state: dict) -> dict:
    """Return a stable tally; status counts are explicitly author assertions."""
    claims = _claims_from_state(state)
    author_status = {status: 0 for status in CLAIM_STATUSES}
    artifact_support = {level: 0 for level in ARTIFACT_SUPPORT_LEVELS}
    resolutions = {
        status: 0 for status in ("resolved", "unresolved", "invalid", "not-checked")
    }
    mismatches = 0
    for claim in claims:
        assertions = claim.get("author_assertions")
        status = assertions.get("status") if isinstance(assertions, dict) else None
        if status in author_status:
            author_status[status] += 1
        computed = claim.get("computed")
        computed = computed if isinstance(computed, dict) else {}
        level = computed.get("resolved_artifact_support")
        if level not in artifact_support:
            # Harden against a partial or malformed computed block.
            level = "none"
        artifact_support[level] += 1
        if computed.get("confidence_mismatch"):
            mismatches += 1
        for pointer in [*claim.get("supports", []), *claim.get("refutes", [])]:
            resolution = (
                pointer.get("resolution") if isinstance(pointer, dict) else None
            )
            resolution_status = (
                resolution.get("status") if isinstance(resolution, dict) else None
            )
            if resolution_status in resolutions:
                resolutions[resolution_status] += 1
    return {
        "total": len(claims),
        "author_status": author_status,
        "resolved_artifact_support": artifact_support,
        "confidence_mismatch": mismatches,
        "evidence_resolution": resolutions,
    }


def _print_summary(summary: dict) -> None:
    statuses = summary["author_status"]
    print(
        f"{summary['total']} author-declared claim(s): "
        f"{statuses['supported']} author-marked supported, "
        f"{statuses['refuted']} author-marked refuted"
    )
    if summary["confidence_mismatch"]:
        print(
            f"⚠ {summary['confidence_mismatch']} claim(s) assert high/medium confidence "
            "without multiple explicitly labeled resolved artifact support streams"
        )


def run_claims(args: argparse.Namespace) -> int:
    root = _find_repo_root()
    if root is None:
        print("Error: not inside a BERIL repo (no PROJECT.md found)", file=sys.stderr)
        return 1

    project_dir = root / "projects" / args.project
    if not project_dir.is_dir():
        print(
            f"Error: project directory '{project_dir}' does not exist", file=sys.stderr
        )
        return 1

    report_path = project_dir / "REPORT.md"
    if not report_path.exists():
        print(
            f"Error: REPORT.md not found at {report_path} — run /synthesize first",
            file=sys.stderr,
        )
        return 1

    report_md = report_path.read_text()
    claims_path = project_dir / "claims.json"
    prior = None
    if claims_path.exists():
        try:
            prior = json.loads(claims_path.read_text())
        except json.JSONDecodeError:
            prior = None

    state = build_claim_state(args.project, report_md, prior, project_dir)
    summary = summarize(state)

    if args.action == "build":
        claims_path.write_text(json.dumps(state, indent=2) + "\n")
        _print_summary(summary)
        return 0

    # summary: read-only, never writes claims.json
    if getattr(args, "json", False):
        print(json.dumps(summary))
    else:
        _print_summary(summary)
    return 0
