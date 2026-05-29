"""Tests for Atlas inventory maintenance reporting."""

import json

from app.models import AtlasPage
from app.atlas_inventory import build_atlas_inventory, inventory_to_markdown


def test_inventory_reports_missing_collection_pages(repository_data):
    inventory = build_atlas_inventory(repository_data)

    assert inventory["counts"]["collections"] == 1
    assert inventory["counts"]["missing_collection_pages"] == 1
    assert inventory["missing_collection_pages"] == ["kbase_ke_pangenome"]


def test_inventory_counts_data_collection_coverage(repository_data):
    repository_data.atlas_index.pages.append(
        AtlasPage(
            id="data.kbase-ke-pangenome",
            title="Pangenome",
            type="data_collection",
            status="draft",
            summary="Pangenome data.",
            path="data/collections/kbase_ke_pangenome",
            body="# Pangenome",
            related_collections=["kbase_ke_pangenome"],
        )
    )

    inventory = build_atlas_inventory(repository_data)

    assert inventory["counts"]["covered_collections"] == 1
    assert inventory["counts"]["missing_collection_pages"] == 0


def test_inventory_markdown_and_json_are_serializable(repository_data):
    inventory = build_atlas_inventory(repository_data)
    markdown = inventory_to_markdown(inventory)

    assert "Atlas Inventory" in markdown
    assert "Reuse edges" in markdown
    assert json.loads(json.dumps(inventory))["counts"]["collections"] == 1


def test_inventory_reports_reuse_and_conflict_metrics(repository_data):
    inventory = build_atlas_inventory(repository_data)

    assert inventory["counts"]["derived_product_pages"] == 1
    assert inventory["counts"]["derived_products_with_consumers"] == 1
    assert inventory["counts"]["conflict_pages"] == 1
    assert inventory["counts"]["unresolved_conflicts"] == 1
    assert inventory["counts"]["opportunity_pages"] == 1
    assert inventory["counts"]["blocked_opportunities"] == 0
    assert inventory["counts"]["reuse_edges"] > 0
