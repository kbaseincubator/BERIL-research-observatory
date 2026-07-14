"""Atlas maintenance inventory and coverage reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .atlas_graph import (
    build_atlas_reuse_edges,
    build_derived_product_contexts,
    build_opportunity_contexts,
)
from .models import RepositoryData, AtlasPage


def build_atlas_inventory(repo_data: RepositoryData) -> dict[str, Any]:
    """Build deterministic Atlas coverage and maintenance signals."""
    collection_ids = {collection.id for collection in repo_data.collections}
    tenant_ids = {
        collection.tenant_id
        for collection in repo_data.collections
        if collection.tenant_id
    }
    pages = repo_data.atlas_index.pages
    pages_by_type = _pages_by_type(pages)
    related_page_ids = {
        related_id
        for page in pages
        for related_id in page.related_pages
    }
    linked_page_ids = {
        link.target_id
        for link in repo_data.atlas_index.links
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
    evidence_required_pages = [
        page
        for page in pages
        if page.type in {"claim", "direction", "hypothesis", "derived_product", "opportunity"}
    ]
    evidence_backed_pages = [
        page for page in evidence_required_pages if _has_evidence_metadata(page)
    ]
    derived_product_pages = pages_by_type.get("derived_product", [])
    conflict_pages = pages_by_type.get("conflict", [])
    opportunity_pages = pages_by_type.get("opportunity", [])
    reuse_edges = build_atlas_reuse_edges(repo_data)
    derived_product_contexts = build_derived_product_contexts(repo_data)
    derived_products_with_consumers = [
        product for product in derived_product_contexts if product["used_by_projects"]
    ]
    derived_products_without_consumers = [
        product for product in derived_product_contexts if not product["used_by_projects"]
    ]
    derived_products_without_owners = [
        product
        for product in derived_product_contexts
        if not product["produced_by_projects"] and not product["review_routes"]
    ]
    unresolved_conflicts = [
        page
        for page in conflict_pages
        if str(page.metadata.get("conflict_status", "unresolved"))
        in {"unresolved", "partially_resolved"}
    ]
    opportunity_contexts = build_opportunity_contexts(repo_data)
    blocked_opportunities = [
        item
        for item in opportunity_contexts
        if item["opportunity_status"] == "blocked"
    ]
    opportunities_without_review_routes = [
        item for item in opportunity_contexts if not item["review_routes"]
    ]
    opportunities_without_conflicts = [
        item for item in opportunity_contexts if not item["linked_conflicts"]
    ]
    opportunities_without_products = [
        item for item in opportunity_contexts if not item["linked_products"]
    ]
    topic_pages = pages_by_type.get("topic", [])
    deep_topic_pages = [
        page
        for page in topic_pages
        if page.body.count("## ") >= 7 and len(page.related_pages) >= 2
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
            "atlas_pages": len(pages),
            "data_collection_pages": len(data_collection_pages),
            "covered_collections": len(covered_collections),
            "missing_collection_pages": len(collection_ids - covered_collections),
            "data_type_pages": len(data_type_pages),
            "multi_collection_projects": len(multi_collection_projects),
            "low_confidence_pages": len(low_confidence_pages),
            "orphaned_pages": len(orphaned_pages),
            "derived_product_pages": len(derived_product_pages),
            "derived_products_with_consumers": len(derived_products_with_consumers),
            "derived_products_without_consumers": len(derived_products_without_consumers),
            "derived_products_without_owners": len(derived_products_without_owners),
            "reuse_edges": len(reuse_edges),
            "conflict_pages": len(conflict_pages),
            "unresolved_conflicts": len(unresolved_conflicts),
            "opportunity_pages": len(opportunity_pages),
            "blocked_opportunities": len(blocked_opportunities),
            "opportunities_without_review_routes": len(opportunities_without_review_routes),
            "opportunities_without_conflicts": len(opportunities_without_conflicts),
            "opportunities_without_products": len(opportunities_without_products),
            "evidence_required_pages": len(evidence_required_pages),
            "evidence_backed_pages": len(evidence_backed_pages),
            "evidence_coverage": f"{len(evidence_backed_pages)}/{len(evidence_required_pages)}",
            "deep_topic_pages": len(deep_topic_pages),
            "topic_visual_coverage": f"{len(deep_topic_pages)}/{len(topic_pages)}",
        },
        "missing_collection_pages": sorted(collection_ids - covered_collections),
        "low_confidence_pages": [_page_ref(page) for page in low_confidence_pages],
        "orphaned_pages": [_page_ref(page) for page in orphaned_pages],
        "derived_products_without_consumers": [
            _page_ref(product["page"]) for product in derived_products_without_consumers
        ],
        "derived_products_without_owners": [
            _page_ref(product["page"]) for product in derived_products_without_owners
        ],
        "unresolved_conflicts": [_page_ref(page) for page in unresolved_conflicts],
        "opportunities": [
            {
                **_page_ref(item["page"]),
                "status": item["opportunity_status"],
                "impact": item["impact"],
                "feasibility": item["feasibility"],
                "readiness": item["readiness"],
                "evidence_strength": item["evidence_strength"],
            }
            for item in opportunity_contexts
        ],
        "blocked_opportunities": [_page_ref(item["page"]) for item in blocked_opportunities],
        "opportunities_without_review_routes": [
            _page_ref(item["page"]) for item in opportunities_without_review_routes
        ],
        "reuse_edges": [
            {
                "source_type": edge.source_type,
                "source_id": edge.source_id,
                "target_type": edge.target_type,
                "target_id": edge.target_id,
                "relationship": edge.relationship,
            }
            for edge in reuse_edges
        ],
        "metrics_to_watch": [
            {
                "label": "Collection Coverage",
                "value": f"{len(covered_collections)}/{len(collection_ids)}",
                "detail": "Canonical BERDL databases with data_collection Atlas pages.",
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
                "detail": "Low-confidence Atlas pages that need review before heavy reuse.",
            },
            {
                "label": "Evidence Coverage",
                "value": f"{len(evidence_backed_pages)}/{len(evidence_required_pages)}",
                "detail": "Claims, directions, hypotheses, derived products, and opportunities with evidence metadata.",
            },
            {
                "label": "Derived Product Reuse",
                "value": f"{len(derived_products_with_consumers)}/{len(derived_product_pages)}",
                "detail": "Promoted derived products with at least one declared downstream project.",
            },
            {
                "label": "Unresolved Tensions",
                "value": len(unresolved_conflicts),
                "detail": "Conflict pages still needing resolving analysis or experiments.",
            },
            {
                "label": "Opportunity Coverage",
                "value": len(opportunity_pages),
                "detail": "Concrete next analyses connected to Atlas evidence, products, and tensions.",
            },
            {
                "label": "Blocked Opportunities",
                "value": len(blocked_opportunities),
                "detail": "Opportunity pages that cannot proceed until prerequisite data or review is available.",
            },
            {
                "label": "Topic Drill-Down Depth",
                "value": f"{len(deep_topic_pages)}/{len(topic_pages)}",
                "detail": "Topic pages with enough sections and related links to support progressive disclosure.",
            },
        ],
    }


def inventory_to_markdown(inventory: dict[str, Any]) -> str:
    counts = inventory["counts"]
    lines = [
        "# Atlas Inventory",
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
        f"- Derived product pages: {counts['derived_product_pages']}",
        f"- Derived products with consumers: {counts['derived_products_with_consumers']}",
        f"- Derived products without consumers: {counts['derived_products_without_consumers']}",
        f"- Reuse edges: {counts['reuse_edges']}",
        f"- Conflict pages: {counts['conflict_pages']}",
        f"- Unresolved conflicts: {counts['unresolved_conflicts']}",
        f"- Opportunity pages: {counts['opportunity_pages']}",
        f"- Blocked opportunities: {counts['blocked_opportunities']}",
        f"- Opportunities without review routes: {counts['opportunities_without_review_routes']}",
        f"- Evidence coverage: {counts['evidence_coverage']}",
        f"- Deep topic pages: {counts['deep_topic_pages']}",
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


def _pages_by_type(pages: list[AtlasPage]) -> dict[str, list[AtlasPage]]:
    grouped: dict[str, list[AtlasPage]] = {}
    for page in pages:
        grouped.setdefault(page.type, []).append(page)
    return grouped


def _page_ref(page: AtlasPage) -> dict[str, str]:
    return {"id": page.id, "title": page.title, "path": page.path}


def _has_evidence_metadata(page: AtlasPage) -> bool:
    evidence = page.metadata.get("evidence")
    if isinstance(evidence, list):
        return any(isinstance(item, dict) and item.get("support") for item in evidence)
    return bool(evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default="..")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args(argv)

    from .dataloader import RepositoryParser

    repo_data = RepositoryParser(Path(args.repo)).parse_all()
    inventory = build_atlas_inventory(repo_data)
    if args.format == "json":
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(inventory_to_markdown(inventory), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
