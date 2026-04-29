---
id: data.index
title: BERDL Data Atlas
type: meta
status: draft
summary: Entry point for BERDL tenants, collections, data types, derived products, join recipes, reuse patterns, and missing complementary data.
source_projects: []
source_docs:
  - ui/config/collections.yaml
  - ui/config/berdl_collections_snapshot.json
  - docs/collections.md
  - docs/schemas/pangenome.md
  - docs/schemas/fitnessbrowser.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - enigma_coral
  - nmdc_arkin
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - data.kbase-tenant
  - data.kescience-tenant
  - data.genes-proteins-annotations
  - data.environment-geochemistry-ecology
  - data.literature-reference-ontology
  - data.metal-tolerance-scores
  - data.genome-fitness-pangenome-join
order: 1
---

# BERDL Data Atlas

## Why This Section Exists

The observatory should not treat data as a passive appendix. Data pages describe what exists, how it is organized, what can be joined, which derived products are reusable, and what missing complementary data would unlock stronger science.

## Facets

- **Tenants** organize infrastructure and ownership.
- **Collections** describe named database resources.
- **Data types** group collections by analytical role.
- **Derived products** identify high-value reusable artifacts created by projects.
- **Joins** preserve cross-collection recipes.
- **Gaps** record missing data that would increase the value of existing work.

## High-Value Derived Data

A derived product is high value when it compresses complex raw collections into a reusable primitive: a score, label, module, mapping table, candidate list, benchmark, or validated join. The best products have stable identifiers, provenance, caveats, and visible downstream reuse.
