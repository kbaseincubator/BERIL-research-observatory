---
id: data.functional-innovation-ko-atlas
title: Functional Innovation KO Atlas
type: derived_product
status: draft
summary: Reusable clade-level functional innovation and acquisition-depth outputs from the ecological agora project.
source_projects:
  - gene_function_ecological_agora
  - pangenome_pathway_ecology
  - pangenome_pathway_geography
source_docs:
  - projects/gene_function_ecological_agora/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kbase_msd_biochemistry
  - kbase_uniref50
  - nmdc_metadata
  - kescience_bacdive
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topic.pangenome-architecture
  - topic.metabolic-capability-community-design
product_kind: atlas_table
reuse_status: candidate
produced_by_projects:
  - gene_function_ecological_agora
used_by_projects: []
output_artifacts:
  - path: projects/gene_function_ecological_agora/data/p2_ko_extraction_log.json
    description: KO extraction log for the full-scale functional substrate.
    status: diagnostic
  - path: projects/gene_function_ecological_agora/figures/p4_synthesis_H1_innovation_tree.png
    description: Topic-level synthesis figure for functional innovation structure.
    status: figure
review_routes:
  - gene_function_ecological_agora
evidence:
  - source: gene_function_ecological_agora
    support: Produces multi-resolution clade-level functional innovation outputs and diagnostics.
order: 97
---

# Functional Innovation KO Atlas

## Reusable Object

This product captures clade-level functional innovation and acquisition-depth patterns. It is intended as a reusable substrate for projects asking where gene function is conserved, exchanged, recently gained, or ecologically anchored.

## Why It Is High Value

The analysis combines UniRef, KO, Pfam architecture, environmental anchoring, and phenotype checks. That makes it valuable as a map of where function varies across the tree and which claims are robust to resolution changes.

## High-Value Joins

- Join KO-level prevalence to pangenome openness and clade rank.
- Join acquisition-depth calls to environment or phenotype metadata.
- Join functional innovation classes to candidate genes or pathway gaps.

## Caveats

This is a candidate derived product until stable exported tables and downstream consumers are promoted into the Atlas.
