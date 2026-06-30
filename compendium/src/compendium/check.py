"""Deterministic integrity check for the rendered Markdown wiki.

Pure-Python, no LLM. Checks **dangling links**: every relative Markdown link target in
``wiki/**/*.md`` (excluding the ``.manifests/`` dir) must resolve to an existing file relative
to the linking page. Skipped: ``http(s)``/``mailto`` and pure ``#anchor`` targets, and a project
page's link to its source ``REPORT.md`` (which lives outside the wiki tree and is the only
deliberately external link the pipeline emits).

Citation integrity is enforced earlier, at publish time, when ``write_page_artifact`` rewrites
inline ``[stmt:id; project]`` tokens into numbered references — so there is no separate
citation check here.
"""

from __future__ import annotations

import re
from pathlib import Path

_MANIFEST_DIR = ".manifests"
_LINK_RE = re.compile(r"\]\(([^)]+)\)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:")


def check_wiki(wiki_dir: Path) -> list[str]:
    """Return a list of integrity problems for ``wiki_dir`` (empty == clean)."""
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
    return sorted(problems)


def _dangling_links(text: str, page: Path, rel: str) -> list[str]:
    problems: list[str] = []
    for target in _LINK_RE.findall(text):
        target = target.strip()
        if not target or _is_external(target) or target.startswith("#"):
            continue
        path_part = target.split("#", 1)[0].split("?", 1)[0]
        if not path_part or _is_source_report(path_part):
            continue
        resolved = (page.parent / path_part).resolve()
        if not resolved.is_file():
            problems.append(f"{rel}: dangling link target {target!r}")
    return problems


def _is_source_report(path_part: str) -> bool:
    # Project pages link to ``../../../projects/<id>/REPORT.md`` outside the wiki tree.
    return path_part == "REPORT.md" or path_part.endswith("/REPORT.md")


def _is_external(target: str) -> bool:
    return target.lower().startswith(_EXTERNAL_PREFIXES)
