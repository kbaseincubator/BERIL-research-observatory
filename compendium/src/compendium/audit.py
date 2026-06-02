"""Phase-0 corpus audit.

Deterministic, read-only inventory of a BERIL project corpus: which canonical files exist,
what markdown headings each REPORT.md carries, and how much of the required top-level section
structure is present. Drives the "is this corpus ready to extract?" gate before any KG build.
"""

from __future__ import annotations

import re
from pathlib import Path

_HEADING = re.compile(r"^(#{1,3})\s+(.*)")

# Canonical BERIL files, keyed by the audit field name.
_FILES = {
    "report": "REPORT.md",
    "research_plan": "RESEARCH_PLAN.md",
    "readme": "README.md",
    "beril": "beril.yaml",
    "review": "REVIEW.md",
}

# Required level-2 sections (matched case-insensitively).
REQUIRED_SECTIONS = ("Key Findings", "Data", "Future Directions", "References")


def parse_headings(md_text: str) -> list[dict]:
    """Parse ATX headings (levels 1-3) from markdown.

    Each result is ``{level, text, line, char}`` where ``line`` is 1-based and ``char`` is the
    character offset of the start of the heading's line within ``md_text``.
    """
    headings: list[dict] = []
    offset = 0
    for lineno, line in enumerate(md_text.splitlines(keepends=True), start=1):
        m = _HEADING.match(line)
        if m:
            headings.append({
                "level": len(m.group(1)),
                "text": m.group(2).strip(),
                "line": lineno,
                "char": offset,
            })
        offset += len(line)
    return headings


def audit_project(project_dir: Path) -> dict:
    """Audit a single project directory for canonical files, headings, and section coverage."""
    project_dir = Path(project_dir)
    files = {key: (project_dir / name).is_file() for key, name in _FILES.items()}

    headings: list[dict] = []
    if files["report"]:
        headings = parse_headings((project_dir / _FILES["report"]).read_text())

    metadata_source = "beril.yaml" if files["beril"] else "readme"

    if files["report"]:
        present = {h["text"].lower() for h in headings if h["level"] == 2}
        n_present = sum(1 for s in REQUIRED_SECTIONS if s.lower() in present)
        coverage = n_present / len(REQUIRED_SECTIONS)
    else:
        coverage = 0.0

    return {
        "id": project_dir.name,
        "files": files,
        "headings": headings,
        "metadata_source": metadata_source,
        "coverage": coverage,
    }


def audit_corpus(projects_dir: Path) -> dict:
    """Audit every immediate sub-directory of ``projects_dir`` and roll up corpus-level stats."""
    projects_dir = Path(projects_dir)
    pids = sorted(p.name for p in projects_dir.iterdir() if p.is_dir())
    projects = {pid: audit_project(projects_dir / pid) for pid in pids}

    n = len(projects)
    has_report = sum(1 for a in projects.values() if a["files"]["report"])
    mean_coverage = (sum(a["coverage"] for a in projects.values()) / n) if n else 0.0
    file_presence = {
        key: sum(1 for a in projects.values() if a["files"][key]) for key in _FILES
    }

    return {
        "projects": projects,
        "rollup": {
            "n_projects": n,
            "has_report": has_report,
            "mean_coverage": mean_coverage,
            "file_presence": file_presence,
        },
    }
