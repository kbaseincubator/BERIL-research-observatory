"""Deterministic author index from project ``README.md`` ``## Authors`` blocks.

Every ``projects/<id>/README.md`` carries a ``## Authors`` block listing one author per entry.
The real corpus uses several surface forms, all handled here:

  - ``- Name (https://orcid.org/<id>), Affiliation``           (most common)
  - ``- **Name** (ORCID: [<id>](url)) — Affiliation``          (bold, markdown link, em-dash)
  - ``- **Name** | ORCID: <id> | Author``                      (pipe-delimited)
  - ``- Name, Affiliation (ORCID: <id>)``                      (affiliation before ORCID)
  - ``- **Name**`` followed by indented ``  - ORCID: <id>`` /  (nested sub-bullets)
    ``  - Affiliation: ...``
  - plain (non-bulleted) lines when the block has no bullets

ORCID and/or affiliation may be absent. Projects are grouped by author, keyed on ORCID when
present (recovered globally so a name-only mention of someone who has an ORCID elsewhere still
merges) — a zero-LLM connector for the wiki's author pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Bare ORCID id: 4 groups of 4 chars, last char may be a digit or X.
_ORCID = re.compile(r"\b(\d{4}-\d{4}-\d{4}-\d{3}[\dX])\b")
# A bullet line (captures indent, marker, content).
_BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
# Delimiters that end the name run: '(', '|', ',', a spaced dash, or an ORCID/Affiliation label.
_NAME_END = re.compile(r"\(|\||,|\s[—–-]\s|\bORCID\b|\bAffiliation\b", re.IGNORECASE)
_JUNK_NAME = re.compile(r"^(orcid|affiliation)\b", re.IGNORECASE)
_WS = re.compile(r"\s+")


@dataclass
class Author:
    name: str
    orcid: str | None = None
    affiliation: str | None = None


@dataclass
class AuthorRecord:
    name: str
    orcid: str | None
    projects: list[str] = field(default_factory=list)


def _norm(name: str) -> str:
    return _WS.sub(" ", name).strip().casefold()


def _author_entries(readme_text: str) -> list[str]:
    """Return one text entry per author under ``## Authors`` (until the next ``## ``).

    Indented child bullets (``  - ORCID: ...``) are folded into their parent author so a
    nested block yields one entry, not three. When the block has no top-level bullets, each
    non-empty line is treated as a plain author entry.
    """
    lines: list[str] = []
    in_block = False
    for line in readme_text.splitlines():
        if line.startswith("## "):
            if in_block:
                break
            in_block = line.strip().lower().startswith("## authors")
            continue
        if in_block:
            lines.append(line)

    has_top_bullet = any(
        (m := _BULLET.match(ln)) and not m.group(1) for ln in lines
    )
    entries: list[str] = []
    if has_top_bullet:
        for line in lines:
            m = _BULLET.match(line)
            if not m:
                continue  # blank/prose between bullets
            content = m.group(2).strip()
            if not m.group(1):  # top-level bullet -> new author
                entries.append(content)
            elif entries:  # indented child bullet -> fold into parent
                entries[-1] += " " + content
    else:
        entries = [ln.strip() for ln in lines if ln.strip()]
    return entries


def _affiliation(entry: str, name_end: int) -> str | None:
    """Best-effort affiliation: the ``Affiliation:`` value, else the post-name remainder."""
    labelled = re.search(r"Affiliation:\s*(.+)$", entry, flags=re.IGNORECASE)
    rest = labelled.group(1) if labelled else entry[name_end:]
    rest = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", rest)          # markdown links
    rest = re.sub(r"https?://orcid\.org/\S+", " ", rest)       # orcid urls
    rest = re.sub(r"\(?\s*ORCID[^)]*\)?", " ", rest, flags=re.IGNORECASE)
    rest = _ORCID.sub(" ", rest)
    rest = rest.translate(str.maketrans("()|*", "    "))
    rest = _WS.sub(" ", rest).strip(" —–-,\t")
    return rest or None


def _parse_entry(entry: str) -> Author:
    """Parse one author entry into ``Author``, tolerating missing ORCID/affiliation."""
    orcid_match = _ORCID.search(entry)
    orcid = orcid_match.group(1) if orcid_match else None

    end = _NAME_END.search(entry)
    name_end = end.start() if end else len(entry)
    name = entry[:name_end].replace("**", "").strip(" *—–-\t")

    return Author(name=name, orcid=orcid, affiliation=_affiliation(entry, name_end))


def parse_authors(readme_text: str) -> list[Author]:
    """Extract the authors listed under a README's ``## Authors`` heading."""
    authors = [_parse_entry(e) for e in _author_entries(readme_text)]
    return [a for a in authors if a.name and not _JUNK_NAME.match(a.name)]


def build_author_index(project_to_readme: dict[str, str]) -> dict[str, AuthorRecord]:
    """Group projects by author across READMEs, keyed by ORCID (else name).

    An author who carries an ORCID in any project is keyed by that ORCID everywhere their
    (normalized) name appears, so the same person does not fragment into separate records.
    Keeps the longest-seen name per key and merges projects (sorted, deduped). Deterministic:
    projects are visited in sorted order and the result is sorted by key.
    """
    parsed = {project: parse_authors(readme) for project, readme in project_to_readme.items()}

    name_to_orcid: dict[str, str] = {}
    for authors in parsed.values():
        for author in authors:
            if author.orcid:
                name_to_orcid.setdefault(_norm(author.name), author.orcid)

    index: dict[str, AuthorRecord] = {}
    for project in sorted(parsed):
        for author in parsed[project]:
            orcid = author.orcid or name_to_orcid.get(_norm(author.name))
            key = orcid or author.name
            record = index.get(key)
            if record is None:
                index[key] = AuthorRecord(name=author.name, orcid=orcid, projects=[project])
                continue
            if orcid and not record.orcid:
                record.orcid = orcid
            if len(author.name) > len(record.name):
                record.name = author.name
            if project not in record.projects:
                record.projects.append(project)

    for record in index.values():
        record.projects.sort()
    return dict(sorted(index.items()))
