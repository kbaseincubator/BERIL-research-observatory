---
id: data.protect-mind
title: Protect Mind
type: data_collection
status: draft
summary: Live BERDL collection in the PROTECT tenant with 30 discovered tables.
source_projects: []
source_docs:
- ui/config/berdl_collections_snapshot.json
related_collections:
- protect_mind
confidence: low
generated_by: Codex GPT-5
last_reviewed: '2026-04-29'
related_pages:
- data.genes-proteins-annotations
order: 300
---

# Protect Mind

## Why This Collection Matters

`protect_mind` is a live BERDL database in the PROTECT tenant. This scaffold page makes the collection visible to humans and agents even before a domain-specific curator has written a richer interpretation.

## What It Contains

The live Spark inventory records 30 tables. Key tables include: `mind_alignment_stats_metag`, `mind_alignment_stats_metars`, `mind_candidate_prebiotics`, `mind_feature_counts_genus`, `mind_feature_counts_genus_stratified`, `mind_feature_counts_species`, `mind_feature_counts_species_stratified`, `mind_gene_annotations`, `mind_genome_coverage`, `mind_importer_genes`, `mind_importer_substrate_scores`, `mind_kegg_assignments`, and 18 more.

## Best Uses

Use this page as an entry point for deciding whether the database should be promoted into a curated collection, linked to a data-type page, or used as a source for a derived product.

## High-Value Joins

Start by inspecting stable identifiers in the table schemas, then connect through the linked data-type page. For user, staging, or imported namespaces, write a join recipe before using the collection as evidence for a claim.

## Reuse And Gaps

High-value reuse would turn this raw collection into a documented mapping table, benchmark, feature matrix, annotation layer, or caveat label. Missing complementary data should be recorded as a `data_gap` page once the blocker is clear.

## Caveats

- The live Phase 1 refresh used Spark SQL table inventory and intentionally skipped per-table schemas to avoid long-running DESCRIBE calls across user and staging namespaces.
