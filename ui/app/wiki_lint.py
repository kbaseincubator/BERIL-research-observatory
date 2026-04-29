"""Non-mutating lint checks for the markdown wiki corpus."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml


@dataclass
class WikiLintIssue:
    """A single wiki lint finding."""

    severity: str
    file: str
    message: str


@dataclass
class _RawWikiPage:
    path: str
    file: Path
    frontmatter: dict
    body: str


REQUIRED_WIKI_FIELDS = {
    "id",
    "title",
    "type",
    "status",
    "summary",
    "source_projects",
    "source_docs",
    "related_collections",
    "confidence",
    "generated_by",
    "last_reviewed",
}

WIKI_PAGE_TYPES = {
    "atlas",
    "topic",
    "data_tenant",
    "data_collection",
    "data_type",
    "derived_product",
    "join_recipe",
    "data_gap",
    "claim",
    "direction",
    "hypothesis",
    "person",
    "method",
    "meta",
}


def lint_wiki(repo_path: Path | str | None = None) -> list[WikiLintIssue]:
    """Validate wiki frontmatter, provenance, and links."""
    repo = Path(repo_path) if repo_path else Path(__file__).resolve().parents[2]
    wiki_dir = repo / "wiki"
    issues: list[WikiLintIssue] = []

    if not wiki_dir.exists():
        return [WikiLintIssue("error", "wiki", "wiki directory does not exist")]

    raw_pages = _load_raw_pages(wiki_dir, issues)
    page_ids: dict[str, _RawWikiPage] = {}
    titles: dict[str, str] = {}
    route_paths = {page.path for page in raw_pages}
    project_ids = {
        p.name
        for p in (repo / "projects").iterdir()
        if p.is_dir() and not p.name.startswith(".")
    } if (repo / "projects").exists() else set()
    collection_ids = _load_collection_ids(repo)

    for page in raw_pages:
        fm = page.frontmatter
        rel_file = _rel(page.file, repo)
        missing = REQUIRED_WIKI_FIELDS - set(fm)
        for field in sorted(missing):
            issues.append(WikiLintIssue("error", rel_file, f"missing required field: {field}"))
        for field in sorted(
            REQUIRED_WIKI_FIELDS
            - {"source_projects", "source_docs", "related_collections"}
        ):
            if field in fm and (fm[field] is None or str(fm[field]).strip() == ""):
                issues.append(WikiLintIssue("error", rel_file, f"empty required field: {field}"))

        page_id = fm.get("id")
        if page_id:
            if page_id in page_ids:
                issues.append(WikiLintIssue("error", rel_file, f"duplicate wiki id: {page_id}"))
            else:
                page_ids[str(page_id)] = page

        page_type = fm.get("type")
        if page_type and page_type not in WIKI_PAGE_TYPES:
            issues.append(WikiLintIssue("error", rel_file, f"invalid page type: {page_type}"))

        title = fm.get("title")
        if title:
            normalized_title = str(title).strip().lower()
            previous_id = titles.get(normalized_title)
            if previous_id and previous_id != page_id:
                issues.append(
                    WikiLintIssue(
                        "error",
                        rel_file,
                        f"duplicate title with conflicting ids: {title}",
                    )
                )
            titles[normalized_title] = str(page_id)

        source_projects = _as_list(fm.get("source_projects"))
        for project_id in source_projects:
            if project_id not in project_ids:
                issues.append(
                    WikiLintIssue("error", rel_file, f"unknown source project: {project_id}")
                )

        related_collections = _as_list(fm.get("related_collections"))
        for collection_id in related_collections:
            if collection_id not in collection_ids:
                issues.append(
                    WikiLintIssue(
                        "error",
                        rel_file,
                        f"unknown related collection: {collection_id}",
                    )
                )

        for source_doc in _as_list(fm.get("source_docs")):
            source_path = source_doc.split("#", 1)[0]
            if source_path and not (repo / source_path).exists():
                issues.append(WikiLintIssue("error", rel_file, f"missing source doc: {source_doc}"))

        for related_id in _as_list(fm.get("related_pages")):
            if related_id not in page_ids and not any(p.frontmatter.get("id") == related_id for p in raw_pages):
                issues.append(WikiLintIssue("error", rel_file, f"unknown related page id: {related_id}"))

        if page_type == "topic" and len(source_projects) < 3 and len(_as_list(fm.get("source_docs"))) < 1:
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    "topic pages need at least 3 source projects or supporting source docs",
                )
            )

        if page_type in {"claim", "direction", "hypothesis"} and not (
            source_projects or _as_list(fm.get("source_docs"))
        ):
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    f"{page_type} pages require project or document provenance",
                )
            )

        for href in _markdown_links(page.body):
            _check_link(href, page.file, wiki_dir, route_paths, issues, rel_file)

    return issues


def _load_raw_pages(wiki_dir: Path, issues: list[WikiLintIssue]) -> list[_RawWikiPage]:
    pages: list[_RawWikiPage] = []
    for wiki_file in sorted(wiki_dir.rglob("*.md")):
        if any(part.startswith(".") for part in wiki_file.relative_to(wiki_dir).parts):
            continue
        raw = wiki_file.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.DOTALL)
        if not match:
            issues.append(WikiLintIssue("error", str(wiki_file), "missing YAML frontmatter"))
            continue
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            issues.append(WikiLintIssue("error", str(wiki_file), f"invalid YAML: {exc}"))
            continue
        if not isinstance(frontmatter, dict):
            issues.append(WikiLintIssue("error", str(wiki_file), "frontmatter must be a mapping"))
            continue
        pages.append(
            _RawWikiPage(
                path=wiki_file.relative_to(wiki_dir).with_suffix("").as_posix(),
                file=wiki_file,
                frontmatter=frontmatter,
                body=raw[match.end() :],
            )
        )
    return pages


def _load_collection_ids(repo: Path) -> set[str]:
    config_path = repo / "ui" / "config" / "collections.yaml"
    if not config_path.exists():
        return set()
    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return {str(c["id"]) for c in data.get("collections", []) if "id" in c}


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _markdown_links(markdown_body: str) -> list[str]:
    return re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", markdown_body)


def _check_link(
    href: str,
    source_file: Path,
    wiki_dir: Path,
    route_paths: set[str],
    issues: list[WikiLintIssue],
    rel_file: str,
) -> None:
    href = href.strip()
    parsed = urlsplit(href)
    if parsed.scheme in {"http", "https", "mailto"} or href.startswith("#"):
        return
    path = parsed.path
    if not path:
        return
    if path.startswith("/wiki/"):
        route = path.removeprefix("/wiki/").strip("/")
        if route.endswith(".md"):
            route = route[:-3]
        if route and route not in route_paths:
            issues.append(WikiLintIssue("error", rel_file, f"broken wiki link: {href}"))
        return
    if path.endswith(".md"):
        target = (source_file.parent / path).resolve()
        try:
            route = target.relative_to(wiki_dir.resolve()).with_suffix("").as_posix()
        except ValueError:
            return
        if route not in route_paths:
            issues.append(WikiLintIssue("error", rel_file, f"broken relative wiki link: {href}"))


def _rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    repo_path = Path(args[0]) if args else Path(__file__).resolve().parents[2]
    issues = lint_wiki(repo_path)
    for issue in issues:
        print(f"{issue.severity}: {issue.file}: {issue.message}")
    if not issues:
        print("wiki lint passed")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
