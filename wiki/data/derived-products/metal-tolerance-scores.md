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

## Caveats

Scores should retain metal identity, organism coverage, counter-ion caveats, and validation status.
