"""Deterministic author index from project ``README.md`` ``## Authors`` blocks.

Every ``projects/<id>/README.md`` carries a ``## Authors`` block of bullets, one author per
line: ``- name (orcid-url), affiliation``. ORCID and/or affiliation may be absent. This module
parses those bullets and groups projects by author (keyed on ORCID when present, else name) —
a zero-LLM connector for the wiki's author pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Bare ORCID id: 4 groups of 4 chars, last char may be a digit or X.
_ORCID = re.compile(r"\b(\d{4}-\d{4}-\d{4}-\d{3}[\dX])\b")
# A bullet line under a markdown heading.
_BULLET = re.compile(r"^\s*[-*]\s+(.*)$")


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


def _authors_block(readme_text: str) -> list[str]:
    """Return author entries under the ``## Authors`` heading (until the next ``## ``).

    Authors are bullets (``- name ...``); a few projects list them as plain lines instead,
    so fall back to non-empty lines when the block has no bullets.
    """
    bullets: list[str] = []
    plain: list[str] = []
    in_block = False
    for line in readme_text.splitlines():
        if line.startswith("## "):
            if in_block:
                break
            in_block = line.strip().lower() == "## authors"
            continue
        if in_block:
            m = _BULLET.match(line)
            if m:
                bullets.append(m.group(1).strip())
            elif line.strip():
                plain.append(line.strip())
    return bullets or plain


def _parse_bullet(text: str) -> Author:
    """Parse one author bullet into ``Author``, tolerating missing ORCID/affiliation."""
    orcid_match = _ORCID.search(text)
    orcid = orcid_match.group(1) if orcid_match else None

    # Name is the leading run before the first parenthetical, pipe, or comma delimiter.
    name = re.split(r"[(|]|,\s", text, maxsplit=1)[0]
    name = name.replace("**", "").strip(" *—-")

    # Affiliation: the trailing comma-separated remainder, ignoring any ORCID clause.
    affiliation = None
    if "," in text:
        tail = text.split(",", 1)[1]
        tail = re.sub(r"\(?\s*ORCID[^)]*\)?", "", tail, flags=re.IGNORECASE)
        tail = _ORCID.sub("", tail)
        tail = tail.replace("(", "").replace(")", "").replace("**", "")
        tail = tail.strip(" —-,")
        affiliation = tail or None

    return Author(name=name, orcid=orcid, affiliation=affiliation)


def parse_authors(readme_text: str) -> list[Author]:
    """Extract the authors listed under a README's ``## Authors`` heading."""
    return [_parse_bullet(b) for b in _authors_block(readme_text)]


def build_author_index(project_to_readme: dict[str, str]) -> dict[str, AuthorRecord]:
    """Group projects by author across READMEs, keyed by ORCID (else name).

    Keeps the longest-seen name per key and merges projects (sorted, deduped).
    """
    index: dict[str, AuthorRecord] = {}
    for project, readme in project_to_readme.items():
        for author in parse_authors(readme):
            key = author.orcid or author.name
            record = index.get(key)
            if record is None:
                index[key] = AuthorRecord(name=author.name, orcid=author.orcid, projects=[project])
                continue
            if len(author.name) > len(record.name):
                record.name = author.name
            if project not in record.projects:
                record.projects.append(project)

    for record in index.values():
        record.projects.sort()
    return index
