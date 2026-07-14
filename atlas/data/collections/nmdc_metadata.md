---
id: data.nmdc-metadata
title: Nmdc Metadata
type: data_collection
status: draft
summary: Live BERDL collection in the NMDC tenant with 47 discovered tables.
source_projects: []
source_docs:
- ui/config/berdl_collections_snapshot.json
related_collections:
- nmdc_metadata
confidence: low
generated_by: Codex GPT-5
last_reviewed: '2026-04-29'
related_pages:
- data.environment-geochemistry-ecology
order: 300
---

# Nmdc Metadata

## Why This Collection Matters

`nmdc_metadata` is a live BERDL database in the NMDC tenant. This scaffold page makes the collection visible to humans and agents even before a domain-specific curator has written a richer interpretation.

## What It Contains

The live Spark inventory records 47 tables. Key tables include: `biosample_set`, `biosample_set_agrochem_addition`, `biosample_set_air_temp_regm`, `biosample_set_associated_studies`, `biosample_set_chem_administration`, `biosample_set_fertilizer_regm`, `biosample_set_gaseous_environment`, `biosample_set_host_diet`, `biosample_set_humidity_regm`, `biosample_set_misc_param`, `biosample_set_perturbation`, `biosample_set_phaeopigments`, and 35 more.

## Best Uses

Use this page as an entry point for deciding whether the database should be promoted into a curated collection, linked to a data-type page, or used as a source for a derived product.

## High-Value Joins

Start by inspecting stable identifiers in the table schemas, then connect through the linked data-type page. For user, staging, or imported namespaces, write a join recipe before using the collection as evidence for a claim.

## Reuse And Gaps

High-value reuse would turn this raw collection into a documented mapping table, benchmark, feature matrix, annotation layer, or caveat label. Missing complementary data should be recorded as a `data_gap` page once the blocker is clear.

## Caveats

- The live Phase 1 refresh used Spark SQL table inventory and intentionally skipped per-table schemas to avoid long-running DESCRIBE calls across user and staging namespaces.
