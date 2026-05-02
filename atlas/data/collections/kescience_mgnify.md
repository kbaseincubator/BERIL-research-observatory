---
id: data.kescience-mgnify
title: Kescience Mgnify
type: data_collection
status: draft
summary: Live BERDL collection in the KE Science tenant with 18 discovered tables.
source_projects: []
source_docs:
- ui/config/berdl_collections_snapshot.json
related_collections:
- kescience_mgnify
confidence: low
generated_by: Codex GPT-5
last_reviewed: '2026-04-29'
related_pages:
- data.genes-proteins-annotations
order: 300
---

# Kescience Mgnify

## Why This Collection Matters

`kescience_mgnify` is a live BERDL database in the KE Science tenant. This scaffold page makes the collection visible to humans and agents even before a domain-specific curator has written a richer interpretation.

## What It Contains

The live Spark inventory records 18 tables. Key tables include: `biome`, `gene`, `gene_amr`, `gene_bgc`, `gene_crispr`, `gene_defense`, `gene_eggnog`, `gene_mobilome`, `genome`, `genome_annotation_coverage`, `genome_cazy`, `genome_cog`, and 6 more.

## Best Uses

Use this page as an entry point for deciding whether the database should be promoted into a curated collection, linked to a data-type page, or used as a source for a derived product.

## High-Value Joins

Start by inspecting stable identifiers in the table schemas, then connect through the linked data-type page. For user, staging, or imported namespaces, write a join recipe before using the collection as evidence for a claim.

## Reuse And Gaps

High-value reuse would turn this raw collection into a documented mapping table, benchmark, feature matrix, annotation layer, or caveat label. Missing complementary data should be recorded as a `data_gap` page once the blocker is clear.

## Caveats

- The live Phase 1 refresh used Spark SQL table inventory and intentionally skipped per-table schemas to avoid long-running DESCRIBE calls across user and staging namespaces.
