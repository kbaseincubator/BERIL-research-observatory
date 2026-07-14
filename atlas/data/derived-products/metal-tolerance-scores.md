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
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - direction.rare-earth-cross-metal-inference
  - conflict.metal-specificity-vs-general-stress
product_kind: score
reuse_status: promoted
produced_by_projects:
  - metal_fitness_atlas
  - metal_specificity
used_by_projects:
  - bacdive_metal_validation
  - bacdive_phenotype_metal_tolerance
  - metal_cross_resistance
output_artifacts:
  - path: projects/metal_fitness_atlas/figures/species_metal_score_distribution.png
    description: Species-level score distribution used to summarize reusable tolerance signal.
    status: figure
  - path: projects/metal_fitness_atlas/figures/bioleaching_species_scores.png
    description: Candidate taxa scored for bioleaching and biorecovery relevance.
    status: figure
review_routes:
  - metal_fitness_atlas
  - metal_specificity
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

## Review Brief

What changed: this product is already promoted, but newer rare-earth and field-scale metal ecology pages now depend on it as a reusable evidence layer.

Why review matters: reviewers should confirm that the score can support cross-project reuse without hiding metal identity, organism coverage, specificity filters, or counter-ion caveats.

Evidence to inspect:

- `metal_fitness_atlas` and `metal_specificity` for score construction and specificity filtering.
- `bacdive_metal_validation` and `bacdive_phenotype_metal_tolerance` for validation.
- [Metal specificity versus general stress](/atlas/conflicts/metal-specificity-vs-general-stress) for caveats that must travel with reuse.

Questions for reviewers:

- Are the output artifacts sufficient for reuse, or does this need a table artifact in addition to figures?
- Should every score expose metal, organism, specificity, and validation-status fields?
- Are rare-earth extrapolations clearly labeled as predictions until direct REE fitness exists?
- What downstream page should own score-version changes?

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
