---
id: data.metal-tolerance-scores
title: Metal Tolerance Scores
type: derived_product
status: draft
summary: Reusable species and gene-level metal tolerance signals derived from metal fitness projects and environmental validation work.
source_projects:
  - metal_fitness_atlas
  - metal_specificity
  - bacdive_metal_validation
  - bacdive_phenotype_metal_tolerance
source_docs:
  - docs/discoveries.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - topic.critical-minerals
  - direction.rare-earth-cross-metal-inference
evidence:
  - source: metal_fitness_atlas
    support: Metal fitness screens provide the primary gene-condition signal used to derive tolerance scores.
  - source: bacdive_metal_validation
    support: BacDive validation connects derived scores to phenotype and isolation context.
order: 80
---

# Metal Tolerance Scores

## Reusable Object

Metal tolerance scores convert thousands of gene-condition fitness effects into a research primitive: candidate tolerant taxa, genes, and families that can be compared to environments or engineered systems.

## Source Collections

- Fitness Browser for RB-TnSeq metal effects.
- Pangenome collection for conservation and species mapping.
- ENIGMA and BacDive-linked metadata for validation.

## Why It Is High Value

It compresses noisy raw experiments into a score and candidate set that many projects can reuse: bioleaching targets, contaminated-site ecology, AMR co-selection, and rare-earth prediction.

## High-Value Joins

- Join species-level scores to BacDive isolation and phenotype metadata to validate environmental enrichment.
- Join gene-family scores to pangenome conservation classes to distinguish core robustness from accessory resistance.
- Join metal tolerance scores to AMR mechanism profiles to test co-selection at contaminated sites.

## Reuse Signals

This product already supports critical-mineral directions, field-validation hypotheses, and rare-earth experiment design. It should be promoted whenever a project needs a compact representation of metal robustness rather than raw gene-condition matrices.

## Missing Complementary Data

Rare-earth fitness experiments, complete counter-ion controls, and richer site geochemistry would make the score more predictive and less caveat-heavy.

## Caveats

Scores should retain metal identity, organism coverage, counter-ion caveats, and validation status.
