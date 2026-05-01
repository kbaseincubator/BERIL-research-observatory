---
id: data.pangenome-bakta
title: Pangenome Bakta
type: data_collection
status: draft
summary: Live BERDL collection in the Pangenome tenant; no tables were visible in
  the latest table-only discovery.
source_projects: []
source_docs:
- ui/config/berdl_collections_snapshot.json
related_collections:
- pangenome_bakta
confidence: low
generated_by: Codex GPT-5
last_reviewed: '2026-04-29'
related_pages:
- data.genomes-and-pangenomes
order: 300
---

# Pangenome Bakta

## Why This Collection Matters

`pangenome_bakta` is a live BERDL database in the Pangenome tenant. This scaffold page makes the collection visible to humans and agents even before a domain-specific curator has written a richer interpretation.

## What It Contains

The live Spark inventory records 0 tables. Key tables include: No tables were returned by the live table inventory.

## Best Uses

Use this page as an entry point for deciding whether the database should be promoted into a curated collection, linked to a data-type page, or used as a source for a derived product.

## High-Value Joins

Start by inspecting stable identifiers in the table schemas, then connect through the linked data-type page. For user, staging, or imported namespaces, write a join recipe before using the collection as evidence for a claim.

## Reuse And Gaps

High-value reuse would turn this raw collection into a documented mapping table, benchmark, feature matrix, annotation layer, or caveat label. Missing complementary data should be recorded as a `data_gap` page once the blocker is clear.

## Caveats

- The live Phase 1 refresh used Spark SQL table inventory and intentionally skipped per-table schemas to avoid long-running DESCRIBE calls across user and staging namespaces.
