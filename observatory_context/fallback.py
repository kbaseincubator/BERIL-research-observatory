"""Local keyword-search fallback for when OpenViking is unreachable.

Searches exactly the corpus the server would hold — the project/doc files
selected by ``selection.py`` — so local and server results can't drift. There
are no embeddings here: ``local_find`` ranks by query-term coverage, so callers
should prefer exact tokens and treat recall as partial. Results carry
``degraded: True`` / ``source: "local"`` and reuse the same ``viking://`` URIs
as the server, so a skill reads them identically either way.
"""

from __future__ import annotations

import re
from pathlib import Path

from .config import ContextConfig, DOCS_TARGET_URI, PROJECTS_TARGET_URI
from .selection import (
    iter_project_dirs,
    select_central_docs,
    select_project_files,
    select_project_memories,
)

BANNER = (
    "⚠ knowledge layer unavailable at {url} — used local keyword search; "
    "recall may be less complete."
)

DEGRADED_NOTICE = (
    "{command} is unavailable in degraded mode (knowledge layer unreachable). "
    "Start OpenViking, or use find/grep/read which fall back to local search."
)

_RESOURCES_PREFIX = "viking://resources/"
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def file_uri(config: ContextConfig, path: Path) -> str:
    """Map a repo-relative corpus file to its server-equivalent file URI."""
    rel = Path(path).resolve().relative_to(config.repo_root.resolve())
    parts = rel.parts
    if parts[0] == "projects":
        return f"{PROJECTS_TARGET_URI}{'/'.join(parts[1:])}"
    if parts[0] == "docs":
        slug = rel.stem
        return f"{DOCS_TARGET_URI}{slug}/{rel.name}"
    return f"{_RESOURCES_PREFIX}{rel.as_posix()}"


def uri_to_path(config: ContextConfig, uri: str) -> Path | None:
    """Reverse ``file_uri`` for both directory- and file-form resource URIs."""
    if not uri.startswith(_RESOURCES_PREFIX):
        return None
    rest = uri[len(_RESOURCES_PREFIX):]
    if rest.startswith("projects/"):
        sub = rest[len("projects/"):].rstrip("/")
        return config.projects_dir / sub if sub else config.projects_dir
    if rest.startswith("docs/"):
        sub = rest[len("docs/"):].strip("/")
        if not sub:
            return config.docs_dir
        parts = sub.split("/")
        # dir form (docs/<slug>/) -> docs/<slug>.md; file form -> docs/<file>
        return config.docs_dir / (f"{parts[0]}.md" if len(parts) == 1 else parts[-1])
    return None


def _corpus(config: ContextConfig) -> list[Path]:
    files: list[Path] = []
    for project_dir in iter_project_dirs(config.projects_dir):
        files.extend(select_project_files(project_dir))
        files.extend(select_project_memories(project_dir))
    files.extend(select_central_docs(config.repo_root))
    return files


def _scoped(config: ContextConfig, target_uri: str) -> list[tuple[Path, str]]:
    return [
        (path, uri)
        for path in _corpus(config)
        for uri in [file_uri(config, path)]
        if uri.startswith(target_uri)
    ]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def local_find(
    config: ContextConfig, query: str, target_uri: str, limit: int
) -> dict:
    terms = set(_TOKEN_RE.findall(query.lower()))
    scored: list[dict] = []
    for path, uri in _scoped(config, target_uri):
        text = _read(path)
        lowered = text.lower()
        present = {term for term in terms if term in lowered}
        if not present:
            continue
        coverage = round(len(present) / len(terms), 3) if terms else 0.0
        occurrences = sum(lowered.count(term) for term in present)
        scored.append(
            {
                "uri": uri,
                "score": coverage,
                "abstract": _snippet(text, present),
                "_occurrences": occurrences,
            }
        )
    scored.sort(key=lambda r: (r["score"], r["_occurrences"]), reverse=True)
    resources = [{k: v for k, v in r.items() if k != "_occurrences"} for r in scored[:limit]]
    return {
        "resources": resources,
        "total": len(resources),
        "degraded": True,
        "source": "local",
    }


def _snippet(text: str, terms: set[str]) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and any(term in stripped.lower() for term in terms):
            return stripped[:300]
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:300]
    return ""


def local_grep(
    config: ContextConfig,
    pattern: str,
    uri: str,
    *,
    case_insensitive: bool = False,
    exclude_uri: str | None = None,
    node_limit: int | None = None,
) -> dict:
    needle = pattern.lower() if case_insensitive else pattern
    matches: list[dict] = []
    for path, resource_uri in _scoped(config, uri):
        if exclude_uri and resource_uri.startswith(exclude_uri):
            continue
        for number, line in enumerate(_read(path).splitlines(), start=1):
            haystack = line.lower() if case_insensitive else line
            if needle in haystack:
                matches.append({"uri": resource_uri, "line": number, "text": line.strip()[:300]})
                if node_limit is not None and len(matches) >= node_limit:
                    return {"matches": matches, "degraded": True, "source": "local"}
    return {"matches": matches, "degraded": True, "source": "local"}


def local_read(config: ContextConfig, uri: str) -> str:
    path = uri_to_path(config, uri)
    if path is None or not path.is_file():
        return DEGRADED_NOTICE.format(command="read") if path is None else _read(path)
    return _read(path)


def local_overview(config: ContextConfig, uri: str) -> str:
    path = uri_to_path(config, uri)
    if path is None:
        return DEGRADED_NOTICE.format(command="overview")
    if path.is_dir():
        readme = path / "README.md"
        return "\n".join(_read(readme).splitlines()[:40]) if readme.is_file() else ""
    return _read(path)
