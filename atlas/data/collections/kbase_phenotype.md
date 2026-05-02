---
id: data.kbase-phenotype
title: Phenotype
type: data_collection
status: draft
summary: Experimental phenotype data (growth conditions and measurements)
source_projects:
  []
source_docs:
  - docs/collections.md
  - ui/config/berdl_collections_snapshot.json
  - docs/schemas/phenotype.md
related_collections:
  - kbase_phenotype
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.phenotypes-assays
order: 103
---

# Phenotype

## Why This Collection Matters

`kbase_phenotype` is a BERDL database in the KBase tenant. Experimental phenotype data (growth conditions and measurements)

## What It Contains

The snapshot records 2 tables. Key tables include: `experiment`, `experimental_context`.

## Best Uses

Use this page as the collection-level orientation before writing SQL, designing joins, or asking an agent to reuse this data in a hypothesis. Prefer project-backed examples and schema docs when they exist.

## High-Value Joins

Start with stable identifiers named in the schema, then connect through the data-type pages linked below. For sparse or staging databases, record the join recipe before depending on it in claims.

## Reuse And Gaps

Reuse is high value when a project turns this raw database into a stable score, mapping table, label set, benchmark, or caveat. Missing complementary data should be recorded as a `data_gap` page when it blocks interpretation.

## Caveats

This page is generated from the current discovery snapshot and should be deepened when a project starts to rely on this database.
