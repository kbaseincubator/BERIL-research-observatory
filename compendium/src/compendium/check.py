"""Deterministic integrity check for the rendered Markdown wiki.

Pure-Python, no LLM. Two checks, returning a list of human-readable problem strings
(empty == clean):

- **dangling links:** every relative Markdown link target in ``wiki/**/*.md`` (excluding the
  ``.manifests/`` dir) must resolve to an existing file relative to the linking page.
- **orphan citations:** every ``[stmt:<id>; <project>]`` citation in a page must have its ``<id>``
  listed in that page's manifest ``cited_statement_ids``. Pages without a manifest are skipped.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_MANIFEST_DIR = ".manifests"
_LINK_RE = re.compile(r"\]\(([^)]+)\)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:")
_CITATION_RE = re.compile(r"\[(stmt:[^;\]\s]+);[^\]]+\]")


def check_wiki(wiki_dir: Path) -> list[str]:
    """Return a list of integrity problems for ``wiki_dir`` (empty == clean).

    Parameters
    ----------
    wiki_dir
        Root of the rendered Markdown wiki (containing ``index.md``, ``topics/``, the
        ``.manifests/`` dir, ...).

    Returns
    -------
    list of str
        One human-readable string per dangling link or orphan citation, sorted.
    """
    wiki_path = Path(wiki_dir)
    pages = sorted(
        path
        for path in wiki_path.rglob("*.md")
        if _MANIFEST_DIR not in path.relative_to(wiki_path).parts
    )
    problems: list[str] = []
    for page in pages:
        rel = page.relative_to(wiki_path).as_posix()
        text = page.read_text(encoding="utf-8", errors="replace")
        problems.extend(_dangling_links(text, page, rel))
        problems.extend(_orphan_citations(text, page, wiki_path, rel))
    return sorted(problems)


def _dangling_links(text: str, page: Path, rel: str) -> list[str]:
    problems: list[str] = []
    for target in _LINK_RE.findall(text):
        target = target.strip()
        if not target or _is_external(target) or target.startswith("#"):
            continue
        path_part = target.split("#", 1)[0].split("?", 1)[0]
        if not path_part:
            continue
        resolved = (page.parent / path_part).resolve()
        if not resolved.is_file():
            problems.append(f"{rel}: dangling link target {target!r}")
    return problems


def _orphan_citations(text: str, page: Path, wiki_path: Path, rel: str) -> list[str]:
    manifest = _manifest_for(page, wiki_path)
    if manifest is None:
        return []
    cited = set(_load_cited_ids(manifest))
    problems: list[str] = []
    for statement_id in sorted(set(_CITATION_RE.findall(text))):
        if statement_id not in cited:
            problems.append(f"{rel}: orphan citation {statement_id!r} not in manifest")
    return problems


def _manifest_for(page: Path, wiki_path: Path) -> Path | None:
    rel = page.relative_to(wiki_path)
    manifest = wiki_path / _MANIFEST_DIR / rel.with_suffix(".manifest.json")
    return manifest if manifest.is_file() else None


def _load_cited_ids(manifest: Path) -> list[str]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    cited = data.get("cited_statement_ids", [])
    return cited if isinstance(cited, list) else []


def _is_external(target: str) -> bool:
    return target.lower().startswith(_EXTERNAL_PREFIXES)
