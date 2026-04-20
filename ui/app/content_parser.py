"""Stateless content parsing functions for project markdown and notebooks.

Extracted from RepositoryParser so that the same logic can be used both
during the repo migration (importer.py) and on the upload path (routes/data.py).

All functions take raw string content or file paths and return plain dicts or
dataclasses — no DB access, no app state.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Collection IDs we scan for in project text
# ---------------------------------------------------------------------------

KNOWN_COLLECTION_IDS: list[str] = [
    "kbase_ke_pangenome",
    "kescience_fitnessbrowser",
    "kbase_msd_biochemistry",
    "kbase_genomes",
    "enigma_coral",
    "kbase_phenotype",
    "nmdc_arkin",
    "phagefoundry",
    "planetmicrobe",
    "protect_genomedepot",
    "kbase_uniprot",
    "kbase_uniref",
]

_KNOWN_REPORT_SECTIONS = {
    "Key Findings",
    "Results",
    "Interpretation",
    "Limitations",
    "Future Directions",
    "Data",
    "References",
    "Supporting Evidence",
    "Revision History",
}

# File extensions recognised as visualizations vs data
_VIZ_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".html"}
_DATA_SUFFIXES = {".csv", ".tsv", ".json", ".parquet"}


# ---------------------------------------------------------------------------
# Simple result dataclasses (no ORM dependency)
# ---------------------------------------------------------------------------


@dataclass
class ParsedContributor:
    name: str
    orcid: str | None = None
    affiliation: str | None = None
    roles: list[str] = field(default_factory=list)


@dataclass
class ParsedProjectFields:
    """All structured fields extractable from README / RESEARCH_PLAN / REPORT."""

    title: str = ""
    research_question: str | None = None
    overview: str | None = None
    hypothesis: str | None = None
    approach: str | None = None
    findings: str | None = None
    results: str | None = None
    interpretation: str | None = None
    limitations: str | None = None
    future_directions: str | None = None
    data_section: str | None = None
    references_text: str | None = None
    revision_history: str | None = None
    other_sections: list[tuple[str, str]] = field(default_factory=list)
    # Status inferred from content
    status: str = "proposed"  # proposed | in_progress | completed
    # Raw source texts
    raw_readme: str = ""
    research_plan_raw: str | None = None
    report_raw: str | None = None
    has_research_plan: bool = False
    has_report: bool = False
    # Related collections detected in text
    related_collections: list[str] = field(default_factory=list)
    # Contributors parsed from ## Authors section
    contributors: list[ParsedContributor] = field(default_factory=list)


@dataclass
class ParsedNotebook:
    filename: str
    title: str
    description: str | None = None


@dataclass
class ParsedFile:
    """A file found in the project directory."""

    filename: str
    relative_path: str  # relative to the project dir
    size_bytes: int
    mtime: datetime
    file_type: str  # notebook | visualization | data | readme | research_plan | report | other
    content_type: str | None = None


# ---------------------------------------------------------------------------
# Section extraction helpers
# ---------------------------------------------------------------------------


def extract_section(content: str, section_name: str) -> str | None:
    """Extract content between a ## section header and the next ## header."""
    pattern = rf"^## {re.escape(section_name)}\s*$\n(.*?)(?=^## (?!#)|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip() or None
    return None


def extract_other_sections(content: str, known_sections: set[str]) -> list[tuple[str, str]]:
    """Return (name, body) tuples for ## sections not in known_sections."""
    others = []
    for match in re.finditer(
        r"^## (.+?)\s*$\n(.*?)(?=^## (?!#)|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        name = match.group(1).strip()
        if name not in known_sections:
            body = match.group(2).strip()
            if body:
                others.append((name, body))
    return others


def extract_collection_refs(text: str) -> list[str]:
    """Return known collection IDs found anywhere in text."""
    return [cid for cid in KNOWN_COLLECTION_IDS if cid in text]


def rewrite_md_links(content: str | None, project_id: str) -> str | None:
    """Rewrite bare .md links and image paths to be project-relative.

    Mirrors RepositoryParser._rewrite_md_links so stored content renders
    correctly in the browser without depending on the repo filesystem layout.
    """
    if not content:
        return content

    def _replace_img(m: re.Match) -> str:
        alt, path = m.group(1), m.group(2)
        if path.startswith(("http://", "https://", "/", "#")):
            return m.group(0)
        return f"![{alt}](/project-assets/{project_id}/{path})"

    def _replace_link(m: re.Match) -> str:
        text, path = m.group(1), m.group(2)
        if path.startswith(("http://", "https://", "/", "#")):
            return m.group(0)
        if path.endswith(".md"):
            return f"[{text}](/projects/{project_id})"
        return m.group(0)

    content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _replace_img, content)
    content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace_link, content)
    return content


# ---------------------------------------------------------------------------
# Contributor parsing
# ---------------------------------------------------------------------------


def parse_contributors(readme_content: str, project_id: str) -> list[ParsedContributor]:
    """Parse contributors from ## Authors or ## Contributors section."""
    section = extract_section(readme_content, "Authors")
    if section is None:
        section = extract_section(readme_content, "Contributors")
    if not section:
        return []

    contributors = []
    for line in section.split("\n"):
        line = line.strip()
        # Bold format: - **Name** (Affiliation) | ORCID: id | role
        bold_match = re.match(r"^-\s+\*\*(.+?)\*\*\s*(.*)", line)
        if bold_match:
            name = bold_match.group(1).strip()
            rest = bold_match.group(2).strip()
            orcid = None
            affiliation = None
            roles = []

            orcid_paren = re.match(
                r"\(ORCID:\s*\[?([\d-]+)\]?(?:\([^)]*\))?\)\s*[-—]+\s*(.*)", rest
            )
            if orcid_paren:
                orcid = orcid_paren.group(1)
                affiliation = orcid_paren.group(2).strip() or None
            else:
                paren_match = re.match(r"\(([^)]+)\)\s*(.*)", rest)
                if paren_match:
                    affiliation = paren_match.group(1).strip()
                    rest = paren_match.group(2).strip()
                if rest:
                    for segment in [s.strip() for s in rest.split("|") if s.strip()]:
                        om = re.match(r"ORCID:\s*([\d-]+)", segment)
                        if om:
                            orcid = om.group(1)
                        else:
                            roles.append(segment)

            contributors.append(ParsedContributor(name=name, orcid=orcid, affiliation=affiliation, roles=roles))
            continue

        # Plain format: - Name, Affiliation (https://orcid.org/id)
        plain = re.match(r"^-\s+(.+)", line)
        if not plain:
            continue
        plain_text = plain.group(1).strip()
        orcid = None

        orcid_paren_match = re.search(r"\(ORCID:\s*\[?([\d-]+)\]?(?:\([^)]*\))?\)", plain_text)
        if orcid_paren_match:
            orcid = orcid_paren_match.group(1)
            plain_text = (plain_text[: orcid_paren_match.start()] + plain_text[orcid_paren_match.end():]).strip().strip(",").strip()
        else:
            orcid_url_match = re.search(r"\(https://orcid\.org/([\d-]+)\)", plain_text)
            if orcid_url_match:
                orcid = orcid_url_match.group(1)
                plain_text = (plain_text[: orcid_url_match.start()] + plain_text[orcid_url_match.end():]).strip().strip(",").strip()

        parts = [p.strip() for p in plain_text.split(",", 1)]
        name = parts[0]
        affiliation = parts[1] if len(parts) > 1 else None
        contributors.append(ParsedContributor(name=name, orcid=orcid, affiliation=affiliation))

    return contributors


# ---------------------------------------------------------------------------
# Main project field parser
# ---------------------------------------------------------------------------


def parse_project_fields(
    readme: str,
    plan: str | None = None,
    report: str | None = None,
    project_id: str = "",
) -> ParsedProjectFields:
    """Extract all structured fields from the three project markdown files.

    Args:
        readme: Contents of README.md (required).
        plan: Contents of RESEARCH_PLAN.md (optional).
        report: Contents of REPORT.md (optional).
        project_id: Used to rewrite internal links; pass the slug.

    Returns:
        A ParsedProjectFields dataclass with all extracted values.
    """
    has_plan = plan is not None
    has_report = report is not None

    # --- README fields ---
    title_match = re.search(r"^#\s+(.+)$", readme, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else project_id

    research_question = extract_section(readme, "Research Question")
    overview = extract_section(readme, "Overview")

    # --- RESEARCH_PLAN fields ---
    revision_history = None
    if has_plan:
        hypothesis = extract_section(plan, "Hypothesis")
        approach = extract_section(plan, "Approach")
        revision_history = extract_section(plan, "Revision History")
    else:
        hypothesis = extract_section(readme, "Hypothesis")
        approach = extract_section(readme, "Approach")

    # --- REPORT fields ---
    findings = results = interpretation = limitations = None
    future_directions = data_section = references_text = None
    other_sections: list[tuple[str, str]] = []

    if has_report:
        findings = extract_section(report, "Key Findings")
        results = extract_section(report, "Results")
        interpretation = extract_section(report, "Interpretation")
        limitations = extract_section(report, "Limitations")
        future_directions = extract_section(report, "Future Directions")
        data_section = extract_section(report, "Data")
        references_text = extract_section(report, "References")
        other_sections = extract_other_sections(report, _KNOWN_REPORT_SECTIONS)
    else:
        findings = extract_section(readme, "Key Findings")

    # --- Infer status ---
    if findings and "to be filled" not in findings.lower() and "tbd" not in findings.lower():
        status = "completed"
    elif has_plan:
        status = "in_progress"
    elif research_question and approach:
        status = "in_progress"
    else:
        status = "proposed"

    # --- Collection refs ---
    all_text = readme + ("\n" + plan if plan else "") + ("\n" + report if report else "")
    related_collections = extract_collection_refs(all_text)

    # --- Contributors ---
    contributors = parse_contributors(readme, project_id)

    # --- Rewrite links ---
    def _rw(s: str | None) -> str | None:
        return rewrite_md_links(s, project_id) if project_id else s

    return ParsedProjectFields(
        title=title,
        research_question=research_question,
        overview=_rw(overview),
        hypothesis=hypothesis,
        approach=approach,
        findings=_rw(findings),
        results=_rw(results),
        interpretation=_rw(interpretation),
        limitations=_rw(limitations),
        future_directions=_rw(future_directions),
        data_section=_rw(data_section),
        references_text=_rw(references_text),
        revision_history=revision_history,
        other_sections=[(n, _rw(b) or b) for n, b in other_sections],
        status=status,
        raw_readme=readme,
        research_plan_raw=plan,
        report_raw=report,
        has_research_plan=has_plan,
        has_report=has_report,
        related_collections=related_collections,
        contributors=contributors,
    )


# ---------------------------------------------------------------------------
# Notebook metadata parser
# ---------------------------------------------------------------------------


def parse_notebook_metadata(path: Path) -> ParsedNotebook:
    """Extract title and description from a Jupyter notebook.

    Title is taken from the first Markdown H1 cell if present, falling
    back to the filename stem.  Description comes from the first non-heading
    markdown paragraph.
    """
    filename = path.name
    default_title = path.stem.replace("_", " ").title()

    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ParsedNotebook(filename=filename, title=default_title)

    title = default_title
    description: str | None = None

    for cell in data.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue

        # Look for H1
        h1 = re.match(r"^#\s+(.+)", source, re.MULTILINE)
        if h1 and title == default_title:
            title = h1.group(1).strip()
            # First non-heading paragraph as description
            rest = source[h1.end():].strip()
            paras = [p.strip() for p in re.split(r"\n{2,}", rest) if p.strip() and not p.strip().startswith("#")]
            if paras:
                description = paras[0]
            break
        elif title == default_title:
            # Non-H1 markdown cell — use as description if short enough
            paras = [p.strip() for p in re.split(r"\n{2,}", source) if p.strip() and not p.strip().startswith("#")]
            if paras:
                description = paras[0][:500]
            break

    return ParsedNotebook(filename=filename, title=title, description=description)


# ---------------------------------------------------------------------------
# Project directory file scanner
# ---------------------------------------------------------------------------

_CONTENT_TYPE_MAP: dict[str, str] = {
    ".ipynb": "application/x-ipynb+json",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
    ".json": "application/json",
    ".parquet": "application/octet-stream",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".gif": "image/gif",
    ".html": "text/html",
    ".txt": "text/plain",
    ".py": "text/x-python",
    ".sh": "text/x-sh",
    ".pdf": "application/pdf",
}

_FILENAME_FILE_TYPE: dict[str, str] = {
    "README.md": "readme",
    "RESEARCH_PLAN.md": "research_plan",
    "REPORT.md": "report",
    "REVIEW.md": "other",
}


def _file_type_for(path: Path) -> str:
    """Map a file path to a ProjectFile.file_type enum value."""
    if path.name in _FILENAME_FILE_TYPE:
        return _FILENAME_FILE_TYPE[path.name]
    suffix = path.suffix.lower()
    if suffix == ".ipynb":
        return "notebook"
    if suffix in _VIZ_SUFFIXES:
        return "visualization"
    if suffix in _DATA_SUFFIXES:
        return "data"
    return "other"


def scan_project_files(project_dir: Path) -> list[ParsedFile]:
    """Walk a project directory and return metadata for every importable file.

    Skips hidden files/dirs and the ``__pycache__`` / ``.git`` directories.
    Returns paths relative to project_dir.
    """
    results: list[ParsedFile] = []
    _SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "node_modules"}

    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        # Skip hidden files and ignored dirs
        if any(part.startswith(".") or part in _SKIP_DIRS for part in path.parts):
            continue
        # Skip the compiled pickle cache if someone left one in the project
        if path.suffix in {".pkl", ".pyc"}:
            continue

        stat = path.stat()
        relative = str(path.relative_to(project_dir))
        suffix = path.suffix.lower()

        results.append(ParsedFile(
            filename=path.name,
            relative_path=relative,
            size_bytes=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            file_type=_file_type_for(path),
            content_type=_CONTENT_TYPE_MAP.get(suffix),
        ))

    return results
