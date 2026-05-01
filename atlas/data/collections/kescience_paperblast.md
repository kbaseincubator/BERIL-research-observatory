---
id: data.kescience-paperblast
title: PaperBLAST
type: data_collection
status: draft
summary: Gene-to-literature links and curated sequence annotation coverage from PaperBLAST.
source_projects:
  []
source_docs:
  - docs/collections.md
  - ui/config/berdl_collections_snapshot.json
  - docs/schemas/paperblast.md
related_collections:
  - kescience_paperblast
confidence: low
generated_by: Codex GPT-5
last_reviewed: 2026-04-29
related_pages:
  - data.literature-reference-ontology
order: 115
---

# PaperBLAST

## Why This Collection Matters

`kescience_paperblast` is a BERDL database in the KE Science tenant. Gene-to-literature links and curated sequence annotation coverage from PaperBLAST.

## What It Contains

The snapshot records 14 tables. Key tables include: `genepaper`, `gene`, `snippet`, `curatedgene`, `curatedpaper`, `generif`, `uniq`, `site`.

## Best Uses

Use this page when a question depends on literature support, protein-family attention, curated functional evidence, or dark-matter prioritization. It is especially useful as a caveat layer for claims about novelty.

## High-Value Joins

Join through protein accessions, duplicate sequence mappings, curated database identifiers, and PDB-linked structural fields. Record the exact accession vocabulary before joining to pangenome or structure collections.

## Reuse And Gaps

High-value derived products include literature-coverage scores, understudied-family lists, and protein-to-paper evidence bundles. Missing complementary data include clearer bridges from PaperBLAST proteins into BERDL pangenome cluster identifiers.

## Caveats

Discovery caveat: included from schema docs; absent from the 2026-03-14 `docs/collections.md` seed snapshot. Refresh from live BERDL discovery before treating this page as complete.
