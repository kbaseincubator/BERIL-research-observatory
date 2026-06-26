"""beril claims — build and inspect the per-project claims ledger.

Parses a ``## Claims`` block from a project's REPORT.md, computes each claim's
groundedness and tier_mismatch deterministically (``beril_cli.science``), and
writes/inspects ``projects/<id>/claims.json``. The author writes the confidence
WORD; this CLI computes the rest and renders WORDS only — never a numeric
confidence. Ported from the beril-pi-agent reference (lib/claim-state.ts).

The ``## Claims`` micro-format (one ``###`` heading per claim)::

    ## Claims

    ### <claim sentence>
    - confidence: high            # the WORD the author wrote
    - status: supported
    - supports:
      - notebook: notebooks/NB03.ipynb#cell-12 — "p=0.003, n=412"
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

from beril_cli.science import (
    EVIDENCE_KINDS,
    claim_id,
    confidence_from,
    groundedness_for_evidence,
    status_from,
    tier_mismatch,
)

_CLAIMS_HEADER = re.compile(r"^##\s+Claims\b", re.IGNORECASE)
_H2 = re.compile(r"^##\s")
_CLAIM_HEADING = re.compile(r"^###\s+(.*)$")
_FIELD = re.compile(r"^\s*-\s*(confidence|status|supports|refutes)\s*:\s*(.*)$", re.IGNORECASE)
_POINTER = re.compile(rf"^\s*-\s*({'|'.join(EVIDENCE_KINDS)})\s*:\s*(.*)$", re.IGNORECASE)
#: A pointer written inline on the ``supports:``/``refutes:`` line (no leading dash).
_INLINE_POINTER = re.compile(rf"^({'|'.join(EVIDENCE_KINDS)})\s*:\s*(.*)$", re.IGNORECASE)
#: An em dash (optionally space-padded) separates a pointer's locator from its exact text.
_EM_DASH = re.compile(r"\s*—\s*")


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
    return {"kind": kind.lower(), "locator": locator, "exact": exact}


def _append_inline_pointer(claim: dict, bucket: str, value: str) -> None:
    """Parse a pointer written inline on the ``supports:``/``refutes:`` line.

    Without this, ``- supports: notebook: nb.ipynb#cell-2 — "x"`` would silently
    drop the pointer (only the indented sub-list form would be parsed), wrongly
    downgrading the claim's groundedness.
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
            current[bucket or "supports"].append(_parse_pointer(pointer.group(1), pointer.group(2)))

    return claims


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_claim_state(project: str, report_md: str, prior: dict | None = None) -> dict:
    """Compute the full claims ledger (ClaimState) from REPORT.md text.

    Confidence/status are READ from the report; groundedness and tier_mismatch
    are COMPUTED from the supporting evidence pointers. ``reviewer_notes`` from a
    prior ledger are carried forward by claim_id.
    """
    prior_notes = {
        row.get("claim_id"): row.get("reviewer_notes")
        for row in (prior or {}).get("rows", [])
        if row.get("reviewer_notes")
    }

    rows: list[dict] = []
    for c in parse_claims_block(report_md):
        confidence = c["confidence"]
        groundedness = groundedness_for_evidence(c["supports"])
        cid = claim_id(c["claim"])
        row = {
            "claim_id": cid,
            "claim": c["claim"],
            "status": c["status"],
            "confidence": confidence,
            "groundedness": groundedness,
            "tier_mismatch": tier_mismatch(confidence, groundedness),
            "supports": c["supports"],
            "refutes": c["refutes"],
        }
        if cid in prior_notes:
            row["reviewer_notes"] = prior_notes[cid]
        rows.append(row)

    return {
        "project": project,
        "updated_at": _now_iso(),
        "report_hash": "sha256:" + hashlib.sha256(report_md.encode("utf-8")).hexdigest(),
        "rows": rows,
    }


def summarize(state: dict) -> dict:
    """A compact tally for the advisory surface (words/counts only)."""
    rows = state.get("rows", [])
    supported = sum(1 for r in rows if r.get("status") == "supported")
    refuted = sum(1 for r in rows if r.get("status") == "refuted")
    return {
        "total": len(rows),
        "supported": supported,
        "refuted": refuted,
        "unsupported": len(rows) - supported - refuted,
        "tier_mismatch": sum(1 for r in rows if r.get("tier_mismatch")),
    }


def _print_summary(summary: dict) -> None:
    print(
        f"{summary['total']} claim(s): {summary['supported']} supported, "
        f"{summary['refuted']} refuted, {summary['unsupported']} unsupported"
    )
    if summary["tier_mismatch"]:
        print(
            f"⚠ {summary['tier_mismatch']} claim(s) assert high/medium confidence "
            "on a single/no re-runnable source"
        )


def run_claims(args: argparse.Namespace) -> int:
    root = _find_repo_root()
    if root is None:
        print("Error: not inside a BERIL repo (no PROJECT.md found)", file=sys.stderr)
        return 1

    project_dir = root / "projects" / args.project
    if not project_dir.is_dir():
        print(f"Error: project directory '{project_dir}' does not exist", file=sys.stderr)
        return 1

    report_path = project_dir / "REPORT.md"
    if not report_path.exists():
        print(f"Error: REPORT.md not found at {report_path} — run /synthesize first", file=sys.stderr)
        return 1

    report_md = report_path.read_text()
    claims_path = project_dir / "claims.json"
    prior = None
    if claims_path.exists():
        try:
            prior = json.loads(claims_path.read_text())
        except json.JSONDecodeError:
            prior = None

    state = build_claim_state(args.project, report_md, prior)
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
