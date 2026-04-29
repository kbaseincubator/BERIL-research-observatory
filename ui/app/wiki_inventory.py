"""Wiki maintenance inventory and coverage reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .models import RepositoryData, WikiPage


def build_wiki_inventory(repo_data: RepositoryData) -> dict[str, Any]:
    """Build deterministic wiki coverage and maintenance signals."""
    collection_ids = {collection.id for collection in repo_data.collections}
    tenant_ids = {
        collection.tenant_id
        for collection in repo_data.collections
        if collection.tenant_id
    }
    pages = repo_data.wiki_index.pages
    pages_by_type = _pages_by_type(pages)
    related_page_ids = {
        related_id
        for page in pages
        for related_id in page.related_pages
    }
    linked_page_ids = {
        link.target_id
        for link in repo_data.wiki_index.links
    } | related_page_ids

    data_collection_pages = pages_by_type.get("data_collection", [])
    data_type_pages = pages_by_type.get("data_type", [])
    covered_collections = {
        collection_id
        for page in data_collection_pages
        for collection_id in page.related_collections
        if collection_id in collection_ids
    }
    low_confidence_pages = [
        page for page in pages if page.confidence.lower() in {"low", "very low"}
    ]
    orphaned_pages = [
        page
        for page in pages
        if page.type != "atlas"
        and page.id not in linked_page_ids
        and not page.related_pages
    ]
    multi_collection_projects = [
        project
        for project in repo_data.projects
        if len(set(project.related_collections)) >= 2
    ]
    collection_reuse = {
        collection_id: sum(
            1 for project in repo_data.projects if collection_id in project.related_collections
        )
        for collection_id in collection_ids
    }
    dark_matter_collections = [
        collection.id
        for collection in repo_data.collections
        if collection.curation_status == "discovered"
        or collection.schema_status in {"missing", "partial"}
    ]

    return {
        "counts": {
            "tenants": len(tenant_ids),
            "collections": len(collection_ids),
            "wiki_pages": len(pages),
            "data_collection_pages": len(data_collection_pages),
            "covered_collections": len(covered_collections),
            "missing_collection_pages": len(collection_ids - covered_collections),
            "data_type_pages": len(data_type_pages),
            "multi_collection_projects": len(multi_collection_projects),
            "low_confidence_pages": len(low_confidence_pages),
            "orphaned_pages": len(orphaned_pages),
        },
        "missing_collection_pages": sorted(collection_ids - covered_collections),
        "low_confidence_pages": [_page_ref(page) for page in low_confidence_pages],
        "orphaned_pages": [_page_ref(page) for page in orphaned_pages],
        "metrics_to_watch": [
            {
                "label": "Collection Coverage",
                "value": f"{len(covered_collections)}/{len(collection_ids)}",
                "detail": "Canonical BERDL databases with data_collection wiki pages.",
            },
            {
                "label": "Cross-Collection Reuse",
                "value": len(multi_collection_projects),
                "detail": "Projects that combine two or more BERDL collections.",
            },
            {
                "label": "Under-Explored Collections",
                "value": sum(1 for count in collection_reuse.values() if count == 0),
                "detail": "Collections with no parsed project references yet.",
            },
            {
                "label": "Dark-Matter Metadata",
                "value": len(dark_matter_collections),
                "detail": "Collections needing stronger curation or complete schema discovery.",
            },
            {
                "label": "Caveat Load",
                "value": len(low_confidence_pages),
                "detail": "Low-confidence wiki pages that need review before heavy reuse.",
            },
        ],
    }


def inventory_to_markdown(inventory: dict[str, Any]) -> str:
    counts = inventory["counts"]
    lines = [
        "# Wiki Inventory",
        "",
        "## Coverage",
        "",
        f"- Tenants: {counts['tenants']}",
        f"- Collections: {counts['collections']}",
        f"- Data collection pages: {counts['data_collection_pages']}",
        f"- Covered collections: {counts['covered_collections']}",
        f"- Missing collection pages: {counts['missing_collection_pages']}",
        f"- Data type pages: {counts['data_type_pages']}",
        f"- Cross-collection projects: {counts['multi_collection_projects']}",
        "",
        "## Metrics To Watch",
        "",
    ]
    for metric in inventory["metrics_to_watch"]:
        lines.append(f"- **{metric['label']}**: {metric['value']} — {metric['detail']}")
    if inventory["missing_collection_pages"]:
        lines.extend(["", "## Missing Collection Pages", ""])
        lines.extend(f"- `{collection_id}`" for collection_id in inventory["missing_collection_pages"])
    return "\n".join(lines) + "\n"


def _pages_by_type(pages: list[WikiPage]) -> dict[str, list[WikiPage]]:
    grouped: dict[str, list[WikiPage]] = {}
    for page in pages:
        grouped.setdefault(page.type, []).append(page)
    return grouped


def _page_ref(page: WikiPage) -> dict[str, str]:
    return {"id": page.id, "title": page.title, "path": page.path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default="..")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args(argv)

    from .dataloader import RepositoryParser

    repo_data = RepositoryParser(Path(args.repo)).parse_all()
    inventory = build_wiki_inventory(repo_data)
    if args.format == "json":
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(inventory_to_markdown(inventory), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
