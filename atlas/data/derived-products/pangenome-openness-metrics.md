---
id: data.pangenome-openness-metrics
title: Pangenome Openness Metrics
type: derived_product
status: draft
summary: Reusable openness and conservation metrics that connect gene-content architecture to function and ecology.
source_projects:
  - pangenome_openness
  - openness_functional_composition
  - conservation_vs_fitness
source_docs:
  - projects/pangenome_openness/REPORT.md
  - projects/openness_functional_composition/RESEARCH_PLAN.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.pangenome-architecture
  - claim.pangenome-openness-shapes-function
product_kind: metric_table
reuse_status: candidate
produced_by_projects:
  - pangenome_openness
  - openness_functional_composition
used_by_projects:
  - conservation_vs_fitness
output_artifacts:
  - path: projects/pangenome_openness/figures/pangenome_vs_effects.png
    description: Relationship between pangenome openness and fitness effects.
    status: figure
  - path: projects/openness_functional_composition/figures/enrichment_by_quartile_heatmap.png
    description: Functional enrichment across openness quartiles.
    status: figure
review_routes:
  - pangenome_openness
  - openness_functional_composition
evidence:
  - source: pangenome_openness
    support: Establishes openness as a reusable pangenome architecture measurement.
  - source: openness_functional_composition
    support: Connects openness strata to functional composition differences.
order: 99
---

# Pangenome Openness Metrics

## Reusable Object

This product packages species and clade-level openness, conservation, and functional enrichment metrics for later reuse.

## Review Brief

What changed: openness metrics are now connected to broader topic synthesis and to confounder-audit opportunities.

Why review matters: openness is attractive as a single number, but reviewers should confirm that sampling and phylogeny controls are included before downstream pages treat it as a biological driver.

Evidence to inspect:

- `pangenome_openness` for metric construction.
- `openness_functional_composition` for function-by-openness enrichment.
- `conservation_vs_fitness` for links to measured consequence.
- [Pangenome Openness Confounder Audit](/atlas/opportunities/pangenome-openness-confounder-audit) for required controls.

Questions for reviewers:

- Which openness metric should be canonical across Atlas pages?
- Are genome count, assembly quality, and phylogenetic imbalance represented in the product?
- Should this stay candidate until table artifacts are more explicit?
- Which downstream analyses already consume the metric and can validate reuse?

## Why It Is High Value

Pangenome openness shapes how much gene content can vary within a species. Reusing stable openness metrics lets later analyses test whether functional, ecological, or fitness patterns are really about gene-content architecture.

## High-Value Joins

- Join openness metrics to COG or pathway enrichment.
- Join openness metrics to fitness conservation and essentiality.
- Join openness metrics to AMR, phage, or mobile-element profiles.

## Caveats

Openness is sensitive to genome count, sampling imbalance, and species delimitation. Reuse should carry sampling controls.
