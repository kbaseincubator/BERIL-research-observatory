---
id: claim.metal-specific-genes-core-enriched
title: Metal-specific genes remain core-enriched
type: claim
status: draft
summary: Metal-specific genes are functionally distinct from general stress genes but remain enriched in the core genome.
source_projects:
  - metal_specificity
  - metal_fitness_atlas
  - conservation_vs_fitness
source_docs:
  - docs/discoveries.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - data.metal-tolerance-scores
  - conflict.metal-specificity-vs-general-stress
evidence:
  - source: metal_specificity
    support: Metal-important records passing a non-metal sick-rate screen remain enriched for core-genome genes.
  - source: metal_fitness_atlas
    support: Cross-organism metal fitness effects provide the base gene-metal evidence set.
order: 10
---

# Metal-specific genes remain core-enriched

## Claim

Genes classified as metal-specific are not merely general stress genes, but they still remain strongly core-enriched relative to baseline genes.

## Review Brief

What changed: this claim is now reused by critical-minerals, AMR co-selection, and metal ecology pages, so reviewers need a precise view of threshold and coverage caveats.

Why review matters: this is one of the most important premises for engineering target selection. If it is too broad, downstream pages may over-prioritize conserved stress genes.

Evidence to inspect:

- `metal_specificity` for non-metal sick-rate thresholds.
- `metal_fitness_atlas` for cross-organism metal fitness evidence.
- `conservation_vs_fitness` for conservation and measured consequence.
- [Metal specificity versus general stress](/atlas/conflicts/metal-specificity-vs-general-stress) for unresolved controls.

Questions for reviewers:

- Is the 5% non-metal sick-rate threshold appropriate for claim reuse?
- Are core-enriched targets being separated from generic housekeeping stress?
- Which missing organisms or locus-ID gaps could change the claim?
- Should this claim require counter-ion evidence before promotion?

## Evidence

`metal_specificity` reports that 54.9% of analyzable metal-important records are metal-specific under the 5% non-metal sick-rate threshold, and that metal-specific genes retain high core fractions.

## Why It Matters

This keeps the core-genome robustness model alive while still identifying specialized gene targets. It changes engineering expectations: useful tolerance determinants may be conserved housekeeping-adjacent systems, not only accessory resistance islands.

## Caveats

Coverage gaps, threshold choices, essential-gene invisibility, and counter-ion effects should travel with this claim.
