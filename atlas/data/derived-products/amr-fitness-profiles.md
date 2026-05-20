---
id: data.amr-fitness-profiles
title: AMR Fitness Profiles
type: derived_product
status: draft
summary: Reusable AMR mechanism, conservation, environment, and fitness-cost signals for resistance ecology questions.
source_projects:
  - amr_pangenome_atlas
  - amr_environmental_resistome
  - amr_fitness_cost
source_docs:
  - projects/amr_pangenome_atlas/REPORT.md
  - projects/amr_fitness_cost/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - nmdc_metadata
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.amr-resistance-ecology
  - direction.metal-amr-co-selection
  - conflict.metal-amr-co-selection-readiness
product_kind: profile_table
reuse_status: promoted
produced_by_projects:
  - amr_pangenome_atlas
  - amr_fitness_cost
used_by_projects:
  - amr_environmental_resistome
output_artifacts:
  - path: projects/amr_pangenome_atlas/figures/fig1_amr_overview.png
    description: Overview of AMR families and conservation structure.
    status: figure
  - path: projects/amr_fitness_cost/figures/stratification_overview.png
    description: Fitness-cost stratification by mechanism and conservation.
    status: figure
review_routes:
  - amr_pangenome_atlas
  - amr_fitness_cost
evidence:
  - source: amr_pangenome_atlas
    support: Provides AMR family, mechanism, conservation, and environment summaries.
  - source: amr_fitness_cost
    support: Adds fitness-cost evidence that changes how resistance profiles should be reused.
order: 98
---

# AMR Fitness Profiles

## Reusable Object

This product brings AMR gene family, mechanism, conservation, environment, and no-antibiotic fitness evidence into one reusable profile concept.

## Review Brief

What changed: AMR profiles now need to interoperate with metal tolerance, prophage density, and environmental metadata rather than serving only as AMR summaries.

Why review matters: this product is central to co-selection work. Reviewers should check that it preserves mechanism class, conservation, environment, and cost instead of collapsing them into a single resistance score.

Evidence to inspect:

- `amr_pangenome_atlas` for AMR family and mechanism structure.
- `amr_fitness_cost` for cost and stratification evidence.
- [Metal-AMR co-selection readiness](/atlas/conflicts/metal-amr-co-selection-readiness) for the main downstream tension.

Questions for reviewers:

- Which fields are mandatory before AMR profiles can be joined to metal tolerance scores?
- Should mobile-element context be part of this product or a separate derived product?
- Are antibiotic-free fitness costs being kept distinct from resistance mechanism prevalence?
- What consumer project should be added before the product status moves beyond promoted draft?

## Why It Is High Value

AMR is not just presence/absence. Reuse needs to preserve whether a mechanism is core or accessory, how it distributes across environments, and whether it carries measurable fitness cost.

## High-Value Joins

- Join AMR profiles to metal tolerance scores to test co-selection.
- Join AMR profiles to environment labels to find structured resistome niches.
- Join AMR mechanisms to fitness-cost estimates before proposing intervention or persistence claims.

## Caveats

Profiles remain context dependent. Antibiotic-free fitness costs, contaminated-site enrichment, and mechanism labels should not be collapsed into one undifferentiated resistance score.
