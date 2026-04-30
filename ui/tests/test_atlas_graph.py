"""Tests for deterministic Atlas graph helpers."""

from app.atlas_graph import (
    build_atlas_reuse_edges,
    build_derived_product_contexts,
    build_opportunity_contexts,
    build_topic_overview_map,
    conflicts_for_page,
    opportunities_for_page,
    review_routes_for_page,
)


def test_reuse_graph_edges_include_project_and_product_edges(repository_data):
    edges = build_atlas_reuse_edges(repository_data)
    edge_keys = {
        (
            edge.source_type,
            edge.source_id,
            edge.target_type,
            edge.target_id,
            edge.relationship,
        )
        for edge in edges
    }

    assert (
        "project",
        "test_project",
        "derived_product",
        "data.test-product",
        "produces",
    ) in edge_keys
    assert (
        "derived_product",
        "data.test-product",
        "project",
        "completed_project",
        "reused_by",
    ) in edge_keys
    assert (
        "opportunity",
        "opportunity.test",
        "conflict",
        "conflict.test",
        "addresses_conflict",
    ) in edge_keys
    assert (
        "opportunity",
        "opportunity.test",
        "derived_product",
        "data.test-product",
        "uses_product",
    ) in edge_keys


def test_derived_product_context_resolves_projects(repository_data):
    products = build_derived_product_contexts(repository_data)
    product = next(item for item in products if item["page"].id == "data.test-product")

    assert product["product_kind"] == "score"
    assert product["produced_by_projects"][0].id == "test_project"
    assert product["used_by_projects"][0].id == "completed_project"
    assert product["review_routes"][0]["project_id"] == "test_project"


def test_review_routes_and_conflicts_resolve_for_topic(repository_data):
    topic = repository_data.wiki_index.get_page_by_id("topic.test")

    assert review_routes_for_page(topic, repository_data)
    assert conflicts_for_page(topic, repository_data)[0].id == "conflict.test"
    assert opportunities_for_page(topic, repository_data)[0]["page"].id == "opportunity.test"


def test_topic_overview_map_uses_related_metadata(repository_data):
    topic = repository_data.wiki_index.get_page_by_id("topic.test")
    overview = build_topic_overview_map(topic, repository_data)

    assert overview is not None
    labels = {column["label"] for column in overview["columns"]}
    assert "Projects" in labels
    assert "Collections" in labels
    assert "Tensions" in labels
    assert "Opportunities" in labels


def test_opportunity_context_resolves_conflicts_products_and_reviewers(repository_data):
    opportunities = build_opportunity_contexts(repository_data)
    opportunity = next(item for item in opportunities if item["page"].id == "opportunity.test")

    assert opportunity["impact"] == "high"
    assert opportunity["linked_conflicts"][0].id == "conflict.test"
    assert opportunity["linked_products"][0]["page"].id == "data.test-product"
    assert opportunity["review_routes"][0]["project_id"] == "test_project"
