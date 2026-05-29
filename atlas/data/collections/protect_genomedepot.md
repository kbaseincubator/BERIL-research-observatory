---
id: data.protect-genomedepot
title: PROTECT
type: data_collection
status: draft
summary: Pathogen genome browser (GenomeDepot format)
source_projects:
  []
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - ui/config/berdl_collections_snapshot.json
  - docs/schema.md
related_collections:
  - protect_genomedepot
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.phage-mobile-defense
order: 126
---

# PROTECT

## Why This Collection Matters

`protect_genomedepot` is a BERDL database in the PROTECT tenant. Pathogen genome browser (GenomeDepot format)

## What It Contains

The snapshot records 2 tables. Key tables include: `browser_genome`, `browser_gene_sampled`.

## Best Uses

Use this page as the collection-level orientation before writing SQL, designing joins, or asking an agent to reuse this data in a hypothesis. Prefer project-backed examples and schema docs when they exist.

## High-Value Joins

Start with stable identifiers named in the schema, then connect through the data-type pages linked below. For sparse or staging databases, record the join recipe before depending on it in claims.

## Reuse And Gaps

Reuse is high value when a project turns this raw database into a stable score, mapping table, label set, benchmark, or caveat. Missing complementary data should be recorded as a `data_gap` page when it blocks interpretation.

## Caveats

This page is generated from the current discovery snapshot and should be deepened when a project starts to rely on this database.
