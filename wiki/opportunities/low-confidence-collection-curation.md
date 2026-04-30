---
id: opportunity.low-confidence-collection-curation
title: Low-Confidence Collection Curation
type: opportunity
status: draft
summary: Reduce Atlas caveat load by upgrading high-value low-confidence collection pages with schemas, reuse examples, and missing-data labels.
source_projects:
  - paperblast_explorer
  - bacdive_metal_validation
  - env_embedding_explorer
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - docs/pitfalls.md
  - docs/performance.md
related_collections:
  - kescience_bacdive
  - kescience_paperblast
  - kescience_alphafold
  - kescience_webofmicrobes
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - data.index
  - data.literature-reference-ontology
  - data.genes-proteins-annotations
  - meta.metrics-to-watch
opportunity_status: candidate
opportunity_kind: curation
impact: medium
feasibility: high
readiness: high
evidence_strength: medium
linked_conflicts: []
linked_products: []
target_outputs:
  - Curation patches for the highest-value low-confidence collection pages.
  - Collection reuse examples linked to existing projects and Atlas topics.
  - Updated caveat labels distinguishing missing schemas from missing scientific validation.
review_routes:
  - paperblast_explorer
  - bacdive_metal_validation
  - env_embedding_explorer
evidence:
  - source: ui/config/berdl_collections_snapshot.json
    support: Snapshot-backed collections reveal which databases have schema context but limited Atlas curation.
  - source: meta.metrics-to-watch
    support: Caveat load and dark-matter metadata are already tracked as Atlas maintenance metrics.
order: 120
---

# Low-Confidence Collection Curation

## Why It Matters

Inventory currently reports many low-confidence Atlas pages, especially collection pages that were generated from discovery snapshots. Not all low confidence is scientific uncertainty; some is missing curation. This opportunity separates those cases.

## Evidence Base

The BERDL snapshot gives canonical collection existence and schema status. Project references and existing collection pages show which collections are already useful enough to deserve better curation.

## Work Package

Select high-value low-confidence collections by reuse, topic relevance, and schema availability. Add plain-language utility, sample joins, caveats, and missing complementary data. Record whether confidence improved because the collection is now better described or because stronger scientific evidence exists.

## Decision Use

This reduces caveat load without pretending that every collection is scientifically validated. It also gives future Atlas opportunities better data context.
