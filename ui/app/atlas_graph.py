"""Deterministic Atlas reuse, review, conflict, and topic-map helpers."""

from __future__ import annotations

from typing import Any

from .models import AtlasReuseEdge, AtlasReviewRoute, RepositoryData, WikiPage


REUSE_STATUS_VALUES = {"candidate", "promoted", "reviewed", "deprecated"}
CONFLICT_STATUS_VALUES = {"unresolved", "partially_resolved", "resolved", "deprecated"}


def build_atlas_reuse_edges(repo_data: RepositoryData) -> list[AtlasReuseEdge]:
    """Build deterministic reuse/provenance edges from parsed repository data."""
    edges: dict[tuple[str, str, str, str, str], AtlasReuseEdge] = {}

    def add(
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relationship: str,
        label: str = "",
        detail: str = "",
    ) -> None:
        if not source_id or not target_id:
            return
        key = (source_type, source_id, target_type, target_id, relationship)
        edges.setdefault(
            key,
            AtlasReuseEdge(
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                relationship=relationship,
                label=label,
                detail=detail,
            ),
        )

    for project in repo_data.projects:
        for ref in project.derived_from:
            add(
                "project",
                ref.source_project,
                "project",
                project.id,
                "derived_input",
                "project data reuse",
                ", ".join(ref.files[:4]),
            )
        for collection_id in project.related_collections:
            add(
                "collection",
                collection_id,
                "project",
                project.id,
                "project_uses_collection",
                "collection use",
            )

    for page in repo_data.wiki_index.pages:
        for project_id in page.source_projects:
            add("project", project_id, "atlas_page", page.id, "source_for", page.title)
        for collection_id in page.related_collections:
            add(
                "collection",
                collection_id,
                "atlas_page",
                page.id,
                "collection_for",
                page.title,
            )
        for related_id in page.related_pages:
            add("atlas_page", page.id, "atlas_page", related_id, "related_page")

        if page.type == "derived_product":
            for project_id in _as_list(page.metadata.get("produced_by_projects")):
                add(
                    "project",
                    project_id,
                    "derived_product",
                    page.id,
                    "produces",
                    page.metadata.get("product_kind", ""),
                )
            for project_id in _as_list(page.metadata.get("used_by_projects")):
                add(
                    "derived_product",
                    page.id,
                    "project",
                    project_id,
                    "reused_by",
                    page.metadata.get("reuse_status", ""),
                )

        if page.type == "conflict":
            for affected_id in _as_list(page.metadata.get("affected_pages")):
                add(
                    "conflict",
                    page.id,
                    "atlas_page",
                    affected_id,
                    "affects",
                    page.metadata.get("conflict_status", ""),
                )

        if page.type == "opportunity":
            for conflict_id in _as_list(page.metadata.get("linked_conflicts")):
                add(
                    "opportunity",
                    page.id,
                    "conflict",
                    conflict_id,
                    "addresses_conflict",
                    page.metadata.get("opportunity_status", ""),
                )
            for product_id in _as_list(page.metadata.get("linked_products")):
                add(
                    "opportunity",
                    page.id,
                    "derived_product",
                    product_id,
                    "uses_product",
                    page.metadata.get("opportunity_kind", ""),
                )

    return sorted(
        edges.values(),
        key=lambda edge: (
            edge.source_type,
            edge.source_id,
            edge.relationship,
            edge.target_type,
            edge.target_id,
        ),
    )


def build_derived_product_context(page: WikiPage, repo_data: RepositoryData) -> dict[str, Any]:
    """Resolve a derived-product Atlas page into UI-friendly context."""
    project_map = {project.id: project for project in repo_data.projects}
    produced_ids = _as_list(page.metadata.get("produced_by_projects"))
    used_ids = _as_list(page.metadata.get("used_by_projects"))
    review_ids = _as_list(page.metadata.get("review_routes")) or produced_ids
    artifacts = _artifact_list(page.metadata.get("output_artifacts"))
    return {
        "page": page,
        "product_kind": str(page.metadata.get("product_kind", "derived product")),
        "reuse_status": str(page.metadata.get("reuse_status", "candidate")),
        "produced_by_projects": [
            project_map[project_id] for project_id in produced_ids if project_id in project_map
        ],
        "used_by_projects": [
            project_map[project_id] for project_id in used_ids if project_id in project_map
        ],
        "missing_produced_by_projects": [
            project_id for project_id in produced_ids if project_id not in project_map
        ],
        "missing_used_by_projects": [
            project_id for project_id in used_ids if project_id not in project_map
        ],
        "output_artifacts": artifacts,
        "review_routes": _review_route_refs(review_ids, repo_data),
    }


def build_derived_product_contexts(repo_data: RepositoryData) -> list[dict[str, Any]]:
    """Resolve all derived products, sorted by visible reuse."""
    contexts = [
        build_derived_product_context(page, repo_data)
        for page in repo_data.wiki_index.pages_by_type("derived_product")
    ]
    return sorted(
        contexts,
        key=lambda item: (
            -len(item["used_by_projects"]),
            item["reuse_status"],
            item["page"].title.lower(),
        ),
    )


def build_opportunity_context(page: WikiPage, repo_data: RepositoryData) -> dict[str, Any]:
    """Resolve an opportunity Atlas page into UI-friendly context."""
    wiki_index = repo_data.wiki_index
    linked_conflicts = [
        conflict
        for conflict_id in _as_list(page.metadata.get("linked_conflicts"))
        if (conflict := wiki_index.get_page_by_id(conflict_id))
    ]
    linked_products = [
        build_derived_product_context(product, repo_data)
        for product_id in _as_list(page.metadata.get("linked_products"))
        if (product := wiki_index.get_page_by_id(product_id))
    ]
    review_ids = _as_list(page.metadata.get("review_routes")) or page.source_projects
    return {
        "page": page,
        "opportunity_status": str(page.metadata.get("opportunity_status", "candidate")),
        "opportunity_kind": str(page.metadata.get("opportunity_kind", "analysis")),
        "impact": str(page.metadata.get("impact", "medium")),
        "feasibility": str(page.metadata.get("feasibility", "medium")),
        "readiness": str(page.metadata.get("readiness", "medium")),
        "evidence_strength": str(page.metadata.get("evidence_strength", "medium")),
        "linked_conflicts": linked_conflicts,
        "linked_products": linked_products,
        "target_outputs": _as_list(page.metadata.get("target_outputs")),
        "review_routes": _review_route_refs(review_ids, repo_data),
    }


def build_opportunity_contexts(repo_data: RepositoryData) -> list[dict[str, Any]]:
    """Resolve all opportunity pages, sorted by transparent categorical priority."""
    contexts = [
        build_opportunity_context(page, repo_data)
        for page in repo_data.wiki_index.pages_by_type("opportunity")
    ]
    score_order = {"high": 0, "medium": 1, "low": 2}
    status_order = {"active": 0, "candidate": 1, "blocked": 2, "completed": 3, "deprecated": 4}
    return sorted(
        contexts,
        key=lambda item: (
            status_order.get(item["opportunity_status"], 9),
            score_order.get(item["impact"], 9),
            score_order.get(item["readiness"], 9),
            score_order.get(item["feasibility"], 9),
            item["page"].title.lower(),
        ),
    )


def build_review_routes(repo_data: RepositoryData) -> list[AtlasReviewRoute]:
    """Suggest review routes using only explicit project and contributor context."""
    routes: list[AtlasReviewRoute] = []
    project_map = {project.id: project for project in repo_data.projects}

    for page in repo_data.wiki_index.pages:
        project_ids = _as_list(page.metadata.get("review_routes"))
        if not project_ids:
            project_ids = _as_list(page.metadata.get("produced_by_projects"))
        if not project_ids:
            project_ids = page.source_projects

        seen: set[tuple[str, str, str]] = set()
        for project_id in project_ids:
            project = project_map.get(project_id)
            if not project:
                continue
            if not project.contributors:
                key = (page.id, project_id, project_id)
                if key not in seen:
                    routes.append(
                        AtlasReviewRoute(
                            page_id=page.id,
                            page_title=page.title,
                            reviewer_id=project_id,
                            reviewer_name=project.title,
                            project_id=project_id,
                            basis="source project owner",
                        )
                    )
                    seen.add(key)
                continue
            for contributor in project.contributors:
                key = (page.id, project_id, contributor.id)
                if key in seen:
                    continue
                routes.append(
                    AtlasReviewRoute(
                        page_id=page.id,
                        page_title=page.title,
                        reviewer_id=contributor.id,
                        reviewer_name=contributor.name,
                        project_id=project_id,
                        basis="explicit project authorship",
                    )
                )
                seen.add(key)

    return routes


def review_routes_for_page(page: WikiPage, repo_data: RepositoryData) -> list[AtlasReviewRoute]:
    """Return review routes for one Atlas page."""
    return [route for route in build_review_routes(repo_data) if route.page_id == page.id]


def conflicts_for_page(page: WikiPage, repo_data: RepositoryData) -> list[WikiPage]:
    """Find conflict/tension pages that explicitly affect a page."""
    if page.type == "conflict":
        return []
    conflicts = []
    for conflict in repo_data.wiki_index.pages_by_type("conflict"):
        affected_ids = set(_as_list(conflict.metadata.get("affected_pages")))
        related_ids = set(conflict.related_pages)
        if page.id in affected_ids or page.id in related_ids:
            conflicts.append(conflict)
    return sorted(conflicts, key=lambda item: (item.metadata.get("conflict_status", ""), item.title))


def opportunities_for_page(page: WikiPage, repo_data: RepositoryData) -> list[dict[str, Any]]:
    """Find opportunity pages that explicitly use or address a page."""
    if page.type == "opportunity":
        return []
    contexts = []
    for opportunity in repo_data.wiki_index.pages_by_type("opportunity"):
        linked_conflicts = set(_as_list(opportunity.metadata.get("linked_conflicts")))
        linked_products = set(_as_list(opportunity.metadata.get("linked_products")))
        related_ids = set(opportunity.related_pages)
        if (
            page.id in linked_conflicts
            or page.id in linked_products
            or page.id in related_ids
        ):
            contexts.append(build_opportunity_context(opportunity, repo_data))
    return contexts


def build_topic_overview_map(topic: WikiPage, repo_data: RepositoryData) -> dict[str, Any] | None:
    """Build a metadata-driven overview map for a top-level topic page."""
    if topic.type != "topic":
        return None

    wiki_index = repo_data.wiki_index
    project_map = {project.id: project for project in repo_data.projects}
    collection_map = {collection.id: collection for collection in repo_data.collections}
    related_pages = [
        page
        for related_id in topic.related_pages
        if (page := wiki_index.get_page_by_id(related_id))
    ]
    conflicts = conflicts_for_page(topic, repo_data)
    opportunities = opportunities_for_page(topic, repo_data)

    def refs(kind: str) -> list[dict[str, str]]:
        return [
            {"title": page.title, "url": page.url, "type": page.type}
            for page in related_pages
            if page.type == kind
        ]

    projects = [
        {"title": project_map[project_id].title, "url": f"/projects/{project_id}"}
        for project_id in topic.source_projects
        if project_id in project_map
    ][:8]
    collections = [
        {"title": collection_map[collection_id].name, "url": f"/collections/{collection_id}"}
        for collection_id in topic.related_collections
        if collection_id in collection_map
    ][:8]

    columns = [
        {"label": "Projects", "items": projects},
        {"label": "Collections", "items": collections},
        {"label": "Claims", "items": refs("claim")},
        {"label": "Directions", "items": refs("direction")},
        {"label": "Hypotheses", "items": refs("hypothesis")},
        {
            "label": "Derived Products",
            "items": [
                {"title": page.title, "url": page.url}
                for page in related_pages
                if page.type == "derived_product"
            ],
        },
        {
            "label": "Tensions",
            "items": [{"title": page.title, "url": page.url} for page in conflicts],
        },
        {
            "label": "Opportunities",
            "items": [
                {"title": item["page"].title, "url": item["page"].url}
                for item in opportunities
            ],
        },
    ]

    non_empty = [column for column in columns if column["items"]]
    return {
        "title": f"{topic.title} Overview",
        "summary": (
            f"{len(projects)} source projects, {len(collections)} collections, "
            f"{sum(len(column['items']) for column in non_empty if column['label'] not in {'Projects', 'Collections'})} drill-down links."
        ),
        "columns": non_empty,
    }


def build_reuse_overview(repo_data: RepositoryData) -> dict[str, Any]:
    """Build compact reuse metrics and product cards for landing/reuse pages."""
    edges = build_atlas_reuse_edges(repo_data)
    products = build_derived_product_contexts(repo_data)
    unowned = [
        product for product in products if not product["produced_by_projects"] and not product["review_routes"]
    ]
    without_consumers = [product for product in products if not product["used_by_projects"]]
    return {
        "edges": edges,
        "products": products,
        "counts": {
            "edges": len(edges),
            "derived_products": len(products),
            "reused_products": sum(1 for product in products if product["used_by_projects"]),
            "products_without_consumers": len(without_consumers),
            "unowned_products": len(unowned),
        },
        "products_without_consumers": without_consumers,
        "unowned_products": unowned,
    }


def project_atlas_reuse(project_id: str, repo_data: RepositoryData) -> dict[str, list[dict[str, Any]]]:
    """Return derived products and conflicts connected to a project."""
    products = build_derived_product_contexts(repo_data)
    produced = [
        product
        for product in products
        if any(project.id == project_id for project in product["produced_by_projects"])
    ]
    used = [
        product
        for product in products
        if any(project.id == project_id for project in product["used_by_projects"])
    ]
    sourced = [
        product
        for product in products
        if project_id in product["page"].source_projects and product not in produced
    ]
    conflicts = [
        conflict
        for conflict in repo_data.wiki_index.pages_by_type("conflict")
        if project_id in conflict.source_projects
    ]
    return {"produced": produced, "used": used, "sourced": sourced, "conflicts": conflicts}


def collection_atlas_reuse(collection_id: str, repo_data: RepositoryData) -> dict[str, list[Any]]:
    """Return derived products and conflicts connected to a collection."""
    products = [
        product
        for product in build_derived_product_contexts(repo_data)
        if collection_id in product["page"].related_collections
    ]
    conflicts = [
        conflict
        for conflict in repo_data.wiki_index.pages_by_type("conflict")
        if collection_id in conflict.related_collections
    ]
    return {"derived_products": products, "conflicts": conflicts}


def _review_route_refs(project_ids: list[str], repo_data: RepositoryData) -> list[dict[str, Any]]:
    project_map = {project.id: project for project in repo_data.projects}
    refs: list[dict[str, Any]] = []
    for project_id in project_ids:
        project = project_map.get(project_id)
        if not project:
            refs.append({"project_id": project_id, "project": None, "contributors": []})
            continue
        refs.append(
            {
                "project_id": project_id,
                "project": project,
                "contributors": project.contributors,
            }
        )
    return refs


def _artifact_list(value: Any) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for item in value if isinstance(value, list) else ([] if value is None else [value]):
        if isinstance(item, dict):
            path = str(item.get("path", ""))
            artifacts.append(
                {
                    "path": path,
                    "description": str(item.get("description", "")),
                    "status": str(item.get("status", "")),
                }
            )
        else:
            artifacts.append({"path": str(item), "description": "", "status": ""})
    return artifacts


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]
