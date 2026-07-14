---
id: data.kescience-pubmed
title: Kescience Pubmed
type: data_collection
status: draft
summary: Live BERDL collection in the KE Science tenant with 4 discovered tables.
source_projects: []
source_docs:
- ui/config/berdl_collections_snapshot.json
related_collections:
- kescience_pubmed
confidence: low
generated_by: Codex GPT-5
last_reviewed: '2026-04-29'
related_pages:
- data.literature-reference-ontology
order: 300
---

# Kescience Pubmed

## Why This Collection Matters

`kescience_pubmed` is a live BERDL database in the KE Science tenant. This scaffold page makes the collection visible to humans and agents even before a domain-specific curator has written a richer interpretation.

## What It Contains

The live Spark inventory records 4 tables. Key tables include: `pubmed_article_chemical_fact`, `pubmed_article_id_fact`, `pubmed_article_mesh_fact`, `pubmed_article_wide`

## Best Uses

Use this page as an entry point for deciding whether the database should be promoted into a curated collection, linked to a data-type page, or used as a source for a derived product.

## High-Value Joins

Start by inspecting stable identifiers in the table schemas, then connect through the linked data-type page. For user, staging, or imported namespaces, write a join recipe before using the collection as evidence for a claim.

## Reuse And Gaps

High-value reuse would turn this raw collection into a documented mapping table, benchmark, feature matrix, annotation layer, or caveat label. Missing complementary data should be recorded as a `data_gap` page once the blocker is clear.

## Caveats

- The live Phase 1 refresh used Spark SQL table inventory and intentionally skipped per-table schemas to avoid long-running DESCRIBE calls across user and staging namespaces.
