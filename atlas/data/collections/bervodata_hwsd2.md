---
id: data.bervodata-hwsd2
title: Bervodata Hwsd2
type: data_collection
status: draft
summary: Live BERDL collection in the Bervodata tenant with 25 discovered tables.
source_projects: []
source_docs:
- ui/config/berdl_collections_snapshot.json
related_collections:
- bervodata_hwsd2
confidence: low
generated_by: Codex GPT-5
last_reviewed: '2026-04-29'
related_pages:
- data.environment-geochemistry-ecology
order: 300
---

# Bervodata Hwsd2

## Why This Collection Matters

`bervodata_hwsd2` is a live BERDL database in the Bervodata tenant. This scaffold page makes the collection visible to humans and agents even before a domain-specific curator has written a richer interpretation.

## What It Contains

The live Spark inventory records 25 tables. Key tables include: `d_add_prop`, `d_awc`, `d_coverage`, `d_drainage`, `d_fao90`, `d_il`, `d_koppen`, `d_phase`, `d_root_depth`, `d_roots`, `d_swr`, `d_texture`, and 13 more.

## Best Uses

Use this page as an entry point for deciding whether the database should be promoted into a curated collection, linked to a data-type page, or used as a source for a derived product.

## High-Value Joins

Start by inspecting stable identifiers in the table schemas, then connect through the linked data-type page. For user, staging, or imported namespaces, write a join recipe before using the collection as evidence for a claim.

## Reuse And Gaps

High-value reuse would turn this raw collection into a documented mapping table, benchmark, feature matrix, annotation layer, or caveat label. Missing complementary data should be recorded as a `data_gap` page once the blocker is clear.

## Caveats

- The live Phase 1 refresh used Spark SQL table inventory and intentionally skipped per-table schemas to avoid long-running DESCRIBE calls across user and staging namespaces.
