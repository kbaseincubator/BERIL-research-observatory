"""Non-mutating lint checks for the markdown Atlas corpus."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml


@dataclass
class WikiLintIssue:
    """A single Atlas lint finding."""

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
    "conflict",
    "opportunity",
    "claim",
    "direction",
    "hypothesis",
    "person",
    "method",
    "meta",
}

REQUIRED_SECTION_INDEXES = {
    "topics": "topics/index",
    "data": "data/index",
    "claims": "claims/index",
    "conflicts": "conflicts/index",
    "opportunities": "opportunities/index",
    "directions": "directions/index",
    "hypotheses": "hypotheses/index",
}

EVIDENCE_REQUIRED_TYPES = {
    "claim",
    "direction",
    "hypothesis",
    "derived_product",
    "opportunity",
}
DERIVED_PRODUCT_REQUIRED_FIELDS = {
    "product_kind",
    "reuse_status",
    "produced_by_projects",
    "used_by_projects",
    "output_artifacts",
    "review_routes",
}
VALID_REUSE_STATUS = {"candidate", "promoted", "reviewed", "deprecated"}
CONFLICT_REQUIRED_FIELDS = {
    "conflict_status",
    "evidence_sides",
    "resolving_work",
    "affected_pages",
}
VALID_CONFLICT_STATUS = {"unresolved", "partially_resolved", "resolved", "deprecated"}
OPPORTUNITY_REQUIRED_FIELDS = {
    "opportunity_status",
    "opportunity_kind",
    "impact",
    "feasibility",
    "readiness",
    "evidence_strength",
    "linked_conflicts",
    "linked_products",
    "target_outputs",
    "review_routes",
}
VALID_OPPORTUNITY_STATUS = {"candidate", "active", "blocked", "completed", "deprecated"}
VALID_OPPORTUNITY_KIND = {
    "analysis",
    "experiment",
    "benchmark",
    "validation",
    "productization",
    "curation",
}
VALID_OPPORTUNITY_SCORE = {"high", "medium", "low"}


def lint_wiki(repo_path: Path | str | None = None) -> list[WikiLintIssue]:
    """Validate Atlas frontmatter, provenance, and links."""
    repo = Path(repo_path) if repo_path else Path(__file__).resolve().parents[2]
    wiki_dir = repo / "wiki"
    issues: list[WikiLintIssue] = []

    if not wiki_dir.exists():
        return [WikiLintIssue("error", "wiki", "Atlas corpus directory does not exist")]

    raw_pages = _load_raw_pages(wiki_dir, issues)
    page_ids: dict[str, _RawWikiPage] = {}
    titles: dict[str, str] = {}
    route_paths = {page.path for page in raw_pages}
    canonical_route_paths = route_paths | {
        path.removesuffix("/index") for path in route_paths if path.endswith("/index")
    }
    project_ids = {
        p.name
        for p in (repo / "projects").iterdir()
        if p.is_dir() and not p.name.startswith(".")
    } if (repo / "projects").exists() else set()
    snapshot_collection_ids = _load_snapshot_collection_ids(repo)
    collection_ids = snapshot_collection_ids or _load_collection_ids(repo)
    data_collection_coverage: set[str] = set()

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
                issues.append(WikiLintIssue("error", rel_file, f"duplicate Atlas id: {page_id}"))
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
        if page_type == "data_collection":
            data_collection_coverage.update(
                collection_id
                for collection_id in related_collections
                if collection_id in collection_ids
            )
        if page_type == "data_type" and len(set(related_collections) & collection_ids) < 2:
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    "data_type pages must reference at least 2 known collections",
                )
            )

        for source_doc in _as_list(fm.get("source_docs")):
            if source_doc.startswith(("https://", "http://")):
                continue
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

        if page_type in EVIDENCE_REQUIRED_TYPES and not _has_evidence(fm):
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    f"{page_type} pages require evidence metadata",
                )
            )

        if page_type == "derived_product":
            _check_derived_product_metadata(fm, project_ids, repo, rel_file, issues)

        if page_type == "conflict":
            _check_conflict_metadata(fm, page_ids, raw_pages, rel_file, issues)

        if page_type == "opportunity":
            _check_opportunity_metadata(fm, project_ids, raw_pages, rel_file, issues)

        if page_type == "topic" and not _as_list(fm.get("related_pages")):
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    "topic pages need related_pages for generated overview maps",
                )
            )

        for href in _markdown_links(page.body):
            _check_link(
                href, page.file, wiki_dir, canonical_route_paths, issues, rel_file
            )

    for missing_collection_id in sorted(snapshot_collection_ids - data_collection_coverage):
        issues.append(
            WikiLintIssue(
                "error",
                "wiki/data",
                f"missing data_collection page for discovered collection: {missing_collection_id}",
            )
        )

    for section, index_path in sorted(REQUIRED_SECTION_INDEXES.items()):
        has_section_pages = any(
            page.path.startswith(f"{section}/") for page in raw_pages
        )
        if has_section_pages and index_path not in route_paths:
            issues.append(
                WikiLintIssue(
                    "error",
                    "wiki",
                    f"missing Atlas section index page: {index_path}",
                )
            )

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


def _load_snapshot_collection_ids(repo: Path) -> set[str]:
    snapshot_path = repo / "ui" / "config" / "berdl_collections_snapshot.json"
    if not snapshot_path.exists():
        return set()
    try:
        data = json.loads(snapshot_path.read_text())
    except json.JSONDecodeError:
        return set()
    return {
        str(collection.get("id"))
        for tenant in data.get("tenants", [])
        for collection in tenant.get("collections", [])
        if collection.get("id")
    }


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _has_evidence(frontmatter: dict) -> bool:
    evidence = frontmatter.get("evidence")
    if isinstance(evidence, list):
        return any(isinstance(item, dict) and item.get("support") for item in evidence)
    return bool(evidence)


def _check_derived_product_metadata(
    frontmatter: dict,
    project_ids: set[str],
    repo: Path,
    rel_file: str,
    issues: list[WikiLintIssue],
) -> None:
    missing = DERIVED_PRODUCT_REQUIRED_FIELDS - set(frontmatter)
    for field in sorted(missing):
        issues.append(
            WikiLintIssue("error", rel_file, f"derived_product missing field: {field}")
        )

    reuse_status = str(frontmatter.get("reuse_status", ""))
    if reuse_status and reuse_status not in VALID_REUSE_STATUS:
        issues.append(
            WikiLintIssue("error", rel_file, f"invalid reuse_status: {reuse_status}")
        )

    for field in ("produced_by_projects", "used_by_projects", "review_routes"):
        for project_id in _as_list(frontmatter.get(field)):
            if project_id not in project_ids:
                issues.append(
                    WikiLintIssue(
                        "error",
                        rel_file,
                        f"unknown {field} project: {project_id}",
                    )
                )

    artifacts = frontmatter.get("output_artifacts")
    if "output_artifacts" in frontmatter and not _as_artifact_list(artifacts):
        issues.append(
            WikiLintIssue(
                "error",
                rel_file,
                "derived_product output_artifacts must list at least one artifact",
            )
        )
    for artifact in _as_artifact_list(artifacts):
        path = artifact.get("path", "")
        if not path or _is_external_artifact(path):
            continue
        if not (repo / path).exists():
            issues.append(
                WikiLintIssue("error", rel_file, f"missing output artifact: {path}")
            )


def _check_conflict_metadata(
    frontmatter: dict,
    page_ids: dict[str, _RawWikiPage],
    raw_pages: list[_RawWikiPage],
    rel_file: str,
    issues: list[WikiLintIssue],
) -> None:
    missing = CONFLICT_REQUIRED_FIELDS - set(frontmatter)
    for field in sorted(missing):
        issues.append(WikiLintIssue("error", rel_file, f"conflict missing field: {field}"))

    status = str(frontmatter.get("conflict_status", ""))
    if status and status not in VALID_CONFLICT_STATUS:
        issues.append(WikiLintIssue("error", rel_file, f"invalid conflict_status: {status}"))

    sides = frontmatter.get("evidence_sides")
    if not isinstance(sides, list) or len(sides) < 2:
        issues.append(
            WikiLintIssue(
                "error",
                rel_file,
                "conflict pages require at least two evidence_sides",
            )
        )
    else:
        for idx, side in enumerate(sides, start=1):
            if not isinstance(side, dict) or not side.get("support"):
                issues.append(
                    WikiLintIssue(
                        "error",
                        rel_file,
                        f"conflict evidence_sides[{idx}] needs support text",
                    )
                )

    resolving_work = frontmatter.get("resolving_work")
    if not isinstance(resolving_work, list) or not resolving_work:
        issues.append(
            WikiLintIssue(
                "error",
                rel_file,
                "conflict pages require resolving_work entries",
            )
        )

    known_ids = set(page_ids) | {
        str(page.frontmatter.get("id"))
        for page in raw_pages
        if page.frontmatter.get("id")
    }
    for affected_id in _as_list(frontmatter.get("affected_pages")):
        if affected_id not in known_ids:
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    f"unknown affected Atlas page id: {affected_id}",
                )
            )


def _check_opportunity_metadata(
    frontmatter: dict,
    project_ids: set[str],
    raw_pages: list[_RawWikiPage],
    rel_file: str,
    issues: list[WikiLintIssue],
) -> None:
    missing = OPPORTUNITY_REQUIRED_FIELDS - set(frontmatter)
    for field in sorted(missing):
        issues.append(WikiLintIssue("error", rel_file, f"opportunity missing field: {field}"))

    status = str(frontmatter.get("opportunity_status", ""))
    if status and status not in VALID_OPPORTUNITY_STATUS:
        issues.append(WikiLintIssue("error", rel_file, f"invalid opportunity_status: {status}"))

    kind = str(frontmatter.get("opportunity_kind", ""))
    if kind and kind not in VALID_OPPORTUNITY_KIND:
        issues.append(WikiLintIssue("error", rel_file, f"invalid opportunity_kind: {kind}"))

    for field in ("impact", "feasibility", "readiness", "evidence_strength"):
        value = str(frontmatter.get(field, ""))
        if value and value not in VALID_OPPORTUNITY_SCORE:
            issues.append(WikiLintIssue("error", rel_file, f"invalid {field}: {value}"))

    for project_id in _as_list(frontmatter.get("review_routes")):
        if project_id not in project_ids:
            issues.append(
                WikiLintIssue(
                    "error",
                    rel_file,
                    f"unknown review_routes project: {project_id}",
                )
            )

    known_pages = {
        str(page.frontmatter.get("id")): page
        for page in raw_pages
        if page.frontmatter.get("id")
    }
    for conflict_id in _as_list(frontmatter.get("linked_conflicts")):
        linked = known_pages.get(conflict_id)
        if not linked:
            issues.append(
                WikiLintIssue("error", rel_file, f"unknown linked conflict id: {conflict_id}")
            )
        elif linked.frontmatter.get("type") != "conflict":
            issues.append(
                WikiLintIssue("error", rel_file, f"linked_conflicts is not a conflict: {conflict_id}")
            )

    for product_id in _as_list(frontmatter.get("linked_products")):
        linked = known_pages.get(product_id)
        if not linked:
            issues.append(
                WikiLintIssue("error", rel_file, f"unknown linked product id: {product_id}")
            )
        elif linked.frontmatter.get("type") != "derived_product":
            issues.append(
                WikiLintIssue("error", rel_file, f"linked_products is not a derived_product: {product_id}")
            )

    if "target_outputs" in frontmatter and not _as_list(frontmatter.get("target_outputs")):
        issues.append(
            WikiLintIssue("error", rel_file, "opportunity target_outputs must list at least one output")
        )

    if not (
        _as_list(frontmatter.get("linked_conflicts"))
        or _as_list(frontmatter.get("linked_products"))
        or _as_list(frontmatter.get("related_pages"))
    ):
        issues.append(
            WikiLintIssue(
                "error",
                rel_file,
                "opportunity pages need linked_conflicts, linked_products, or related_pages",
            )
        )


def _as_artifact_list(value) -> list[dict[str, str]]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    artifacts = []
    for item in items:
        if isinstance(item, dict):
            artifacts.append({"path": str(item.get("path", ""))})
        else:
            artifacts.append({"path": str(item)})
    return artifacts


def _is_external_artifact(path: str) -> bool:
    return path.startswith(
        ("https://", "http://", "minio://", "s3://", "external:", "planned:")
    )


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
    if path.startswith(("/wiki/", "/atlas/")):
        route = path.removeprefix("/wiki/").removeprefix("/atlas/").strip("/")
        if route.endswith(".md"):
            route = route[:-3]
        if route and route not in route_paths:
            issues.append(
                WikiLintIssue("error", rel_file, f"broken Atlas link: {href}")
            )
        return
    if path.endswith(".md"):
        target = (source_file.parent / path).resolve()
        try:
            route = target.relative_to(wiki_dir.resolve()).with_suffix("").as_posix()
        except ValueError:
            return
        if route not in route_paths:
            issues.append(WikiLintIssue("error", rel_file, f"broken relative Atlas link: {href}"))


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
        print("atlas lint passed")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
