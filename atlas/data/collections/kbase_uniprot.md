---
id: data.kbase-uniprot
title: UniProt
type: data_collection
status: draft
summary: UniProt protein identifier cross-references
source_projects:
  []
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - ui/config/berdl_collections_snapshot.json
  - docs/schema.md
related_collections:
  - kbase_uniprot
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.genes-proteins-annotations
order: 104
---

# UniProt

## Why This Collection Matters

`kbase_uniprot` is a BERDL database in the KBase tenant. UniProt protein identifier cross-references

## What It Contains

The snapshot records 1 table. Key tables include: `uniprot_identifier`.

## Best Uses

Use this page as the collection-level orientation before writing SQL, designing joins, or asking an agent to reuse this data in a hypothesis. Prefer project-backed examples and schema docs when they exist.

## High-Value Joins

Start with stable identifiers named in the schema, then connect through the data-type pages linked below. For sparse or staging databases, record the join recipe before depending on it in claims.

## Reuse And Gaps

Reuse is high value when a project turns this raw database into a stable score, mapping table, label set, benchmark, or caveat. Missing complementary data should be recorded as a `data_gap` page when it blocks interpretation.

## Caveats

This page is generated from the current discovery snapshot and should be deepened when a project starts to rely on this database.
