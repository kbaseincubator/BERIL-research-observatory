---
id: data.nmdc-arkin
title: NMDC Multi-omics
type: data_collection
status: draft
summary: Multi-omics analysis data (annotations, embeddings, metabolomics, proteomics, traits)
source_projects:
  []
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - ui/config/berdl_collections_snapshot.json
  - docs/schema.md
related_collections:
  - nmdc_arkin
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.multi-omics-embeddings
order: 117
---

# NMDC Multi-omics

## Why This Collection Matters

`nmdc_arkin` is a BERDL database in the NMDC tenant. Multi-omics analysis data (annotations, embeddings, metabolomics, proteomics, traits)

## What It Contains

The snapshot records 45 tables. Key tables include: `annotation_terms_unified`, `annotation_crossrefs`, `annotation_hierarchies_unified`, `cog_categories`, `cog_hierarchy_flat`, `ec_terms`, `ec_hierarchy_flat`, `go_terms`.

## Best Uses

Use this page as the collection-level orientation before writing SQL, designing joins, or asking an agent to reuse this data in a hypothesis. Prefer project-backed examples and schema docs when they exist.

## High-Value Joins

Start with stable identifiers named in the schema, then connect through the data-type pages linked below. For sparse or staging databases, record the join recipe before depending on it in claims.

## Reuse And Gaps

Reuse is high value when a project turns this raw database into a stable score, mapping table, label set, benchmark, or caveat. Missing complementary data should be recorded as a `data_gap` page when it blocks interpretation.

## Caveats

This page is generated from the current discovery snapshot and should be deepened when a project starts to rely on this database.
