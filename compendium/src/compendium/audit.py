"""Phase-0 corpus audit.

Deterministic, read-only inventory of a BERIL project corpus: which canonical files exist,
what markdown headings each REPORT.md carries, and how much of the required top-level section
structure is present. Drives the "is this corpus ready to extract?" gate before any KG build.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_HEADING = re.compile(r"^(#{1,3})\s+(.*)")
_HEADING_MULTILINE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)
_BACKTICK = re.compile(r"`([^`]+)`")
_BERDL = re.compile(r"\bBERDL\s+collection\s+`?([\w./:-]+)`?", re.IGNORECASE)
_NOTEBOOK = re.compile(r"\b[\w./-]+\.ipynb\b")
_FIGURE = re.compile(r"\bfigures/[\w./-]+\.(?:png|jpg|jpeg|svg|pdf)\b", re.IGNORECASE)
_PMID = re.compile(r"\bPMID:?\s*\d+\b", re.IGNORECASE)
_DOI = re.compile(
    r"\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?"
    r"10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)
_MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_PROJECT_PATH = re.compile(r"(?<![\w./-])(?:\.\./)?projects/[\w./-]+/?")
_KO = re.compile(r"\bK\d{5}\b")
_PFAM = re.compile(r"\bPF\d{5}\b")
_COG = re.compile(r"\bCOG\d{3,4}\b")
_GTDB_TAXON = re.compile(r"\b[dpcofgs]__[A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+)?\b")
_GENOME_ID = re.compile(r"\b(?:RS_|GB_)?GC[AF]_\d{9}(?:\.\d+)?\b")
_ARTIFACT = re.compile(r"[/\\]|\.[A-Za-z0-9]{1,5}$")
_SOURCE_CONTEXT_CHARS = 40

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

_CANONICAL_SOURCE_FILES = (
    "REPORT.md",
    "RESEARCH_PLAN.md",
    "REVIEW.md",
    "README.md",
    "beril.yaml",
)


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


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _stable_id(prefix: str, *parts: str) -> str:
    joined = "\x1f".join(parts)
    return f"{prefix}:{hashlib.sha256(joined.encode('utf-8')).hexdigest()[:16]}"


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for match in re.finditer("\n", text):
        starts.append(match.end())
    return starts


def _line_at(line_starts: list[int], char: int) -> int:
    line = 1
    for i, start in enumerate(line_starts, start=1):
        if start > char:
            break
        line = i
    return line


def _line_range(line_starts: list[int], start: int, end: int) -> list[int]:
    if end <= start:
        line = _line_at(line_starts, start)
        return [line, line]
    return [_line_at(line_starts, start), _line_at(line_starts, end - 1)]


def _source_files(project_dir: Path) -> list[dict]:
    files: list[dict] = []
    for name in _CANONICAL_SOURCE_FILES:
        path = project_dir / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({
            "path": name,
            "sha256": _sha256_bytes(data),
            "size_bytes": len(data),
        })
    return files


def _source_sections(project_dir: Path, source_files: list[dict]) -> list[dict]:
    sections: list[dict] = []
    for source_file in source_files:
        source_doc = source_file["path"]
        text = (project_dir / source_doc).read_text(encoding="utf-8")
        if source_doc.endswith(".md"):
            sections.extend(_markdown_sections(source_doc, text))
        else:
            sections.extend(_plain_sections(source_doc, text))
    return sorted(sections, key=lambda section: (section["source_doc"], section["char"], section["id"]))


def _plain_sections(source_doc: str, text: str) -> list[dict]:
    if not text:
        return []
    return [_section_dict(source_doc, None, None, 0, len(text), text, _line_starts(text))]


def _markdown_sections(source_doc: str, text: str) -> list[dict]:
    matches = list(_HEADING_MULTILINE.finditer(text))
    if not matches:
        return _plain_sections(source_doc, text)

    line_starts = _line_starts(text)
    sections: list[dict] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        exact = text[match.start():end]
        if not exact.strip():
            continue
        sections.append(
            _section_dict(
                source_doc,
                match.group(2).strip(),
                len(match.group(1)),
                match.start(),
                end,
                exact,
                line_starts,
            )
        )
    return sections


def _section_dict(
    source_doc: str,
    heading: str | None,
    level: int | None,
    start_char: int,
    end_char: int,
    exact: str,
    line_starts: list[int],
) -> dict:
    line = _line_range(line_starts, start_char, end_char)
    return {
        "id": _stable_id("source_section", source_doc, heading or "", str(start_char), exact),
        "source_doc": source_doc,
        "file": source_doc,
        "heading": heading,
        "level": level,
        "line": line,
        "start_line": line[0],
        "end_line": line[1],
        "char": [start_char, end_char],
        "text_hash": _sha256_text(exact),
        "text": exact,
    }


def _source_anchors(project_dir: Path, source_files: list[dict], sections: list[dict]) -> list[dict]:
    anchors: list[dict] = []
    for source_file in source_files:
        source_doc = source_file["path"]
        text = (project_dir / source_doc).read_text(encoding="utf-8")
        line_starts = _line_starts(text)
        doc_sections = [s for s in sections if s["source_doc"] == source_doc]

        for kind, exact, start, end in _iter_anchor_matches(text):
            section = _containing_section(doc_sections, start)
            anchors.append(
                _anchor_dict(
                    source_doc=source_doc,
                    kind=kind,
                    exact=exact,
                    start=start,
                    end=end,
                    text=text,
                    line_starts=line_starts,
                    section=section,
                )
            )

    return sorted(anchors, key=lambda anchor: (anchor["source_doc"], anchor["char"], anchor["kind"], anchor["exact"], anchor["id"]))


def _iter_anchor_matches(text: str) -> list[tuple[str, str, int, int]]:
    matches: list[tuple[str, str, int, int]] = []

    for match in _BACKTICK.finditer(text):
        token, start, end = _stripped_group(match, 1)
        if _is_dataset_token(token):
            matches.append(("dataset", token, start, end))

    for match in _BERDL.finditer(text):
        token, start, end = _stripped_group(match, 1)
        matches.append(("dataset", token, start, end))

    for kind, regex in (
        ("notebook", _NOTEBOOK),
        ("figure", _FIGURE),
        ("pmid", _PMID),
        ("doi", _DOI),
        ("project_link", _PROJECT_PATH),
        ("ko", _KO),
        ("pfam", _PFAM),
        ("cog", _COG),
        ("gtdb_taxon", _GTDB_TAXON),
        ("genome_id", _GENOME_ID),
    ):
        for match in regex.finditer(text):
            matches.append((kind, match.group(0), match.start(), match.end()))

    for match in _MARKDOWN_LINK.finditer(text):
        target = match.group(1)
        if _is_project_link(target):
            matches.append(("project_link", target, match.start(1), match.end(1)))

    return sorted(set(matches), key=lambda item: (item[2], item[3], item[0], item[1]))


def _stripped_group(match: re.Match, group: int) -> tuple[str, int, int]:
    raw = match.group(group)
    leading = len(raw) - len(raw.lstrip())
    trailing = len(raw) - len(raw.rstrip())
    return raw.strip(), match.start(group) + leading, match.end(group) - trailing


def _is_dataset_token(token: str) -> bool:
    if not token or _ARTIFACT.search(token):
        return False
    if any(regex.fullmatch(token) for regex in (_KO, _PFAM, _COG, _GENOME_ID)):
        return False
    if _NOTEBOOK.fullmatch(token) or _FIGURE.fullmatch(token):
        return False
    return True


def _is_project_link(target: str) -> bool:
    if target.startswith(("#", "http://", "https://", "mailto:")):
        return False
    if target.startswith("../") and target.count("/") >= 1:
        return True
    if target.startswith("projects/"):
        return True
    return target in {"REPORT.md", "RESEARCH_PLAN.md", "REVIEW.md", "README.md", "beril.yaml"}


def _containing_section(sections: list[dict], start: int) -> dict | None:
    for section in sections:
        section_start, section_end = section["char"]
        if section_start <= start < section_end:
            return section
    return None


def _anchor_dict(
    *,
    source_doc: str,
    kind: str,
    exact: str,
    start: int,
    end: int,
    text: str,
    line_starts: list[int],
    section: dict | None,
) -> dict:
    line = _line_range(line_starts, start, end)
    section_id = section["id"] if section else None
    section_heading = section["heading"] if section else None
    prefix_start = max(0, start - _SOURCE_CONTEXT_CHARS)
    suffix_end = min(len(text), end + _SOURCE_CONTEXT_CHARS)
    return {
        "id": _stable_id("source_anchor", source_doc, kind, exact, str(start), section_id or ""),
        "kind": kind,
        "source_doc": source_doc,
        "file": source_doc,
        "source_section": section_id,
        "source_section_heading": section_heading,
        "exact": exact,
        "text_hash": _sha256_text(exact),
        "line": line,
        "start_line": line[0],
        "end_line": line[1],
        "char": [start, end],
        "prefix": text[prefix_start:start],
        "suffix": text[end:suffix_end],
    }


def audit_project(project_dir: Path) -> dict:
    """Audit a single project directory for canonical files, headings, and section coverage."""
    project_dir = Path(project_dir)
    files = {key: (project_dir / name).is_file() for key, name in _FILES.items()}
    source_files = _source_files(project_dir)
    source_sections = _source_sections(project_dir, source_files)
    source_anchors = _source_anchors(project_dir, source_files, source_sections)

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
        "source_files": source_files,
        "source_sections": source_sections,
        "source_anchors": source_anchors,
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
