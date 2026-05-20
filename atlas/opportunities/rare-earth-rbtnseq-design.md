---
id: opportunity.rare-earth-rbtnseq-design
title: Rare-Earth RB-TnSeq Design
type: opportunity
status: draft
summary: Design the first rare-earth fitness experiment by ranking candidate genes from cross-metal specificity, conservation, annotation, and structure evidence.
source_projects:
  - metal_fitness_atlas
  - metal_specificity
  - counter_ion_effects
  - bacdive_metal_validation
source_docs:
  - docs/discoveries.md
  - data/bakta_reannotation/README.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
  - kescience_alphafold
  - kescience_bacdive
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - direction.rare-earth-cross-metal-inference
  - hypothesis.structure-supports-metal-binding
  - hypothesis.bakta-resolves-novel-metal-families
  - data.rare-earth-fitness-gap
  - data.metal-tolerance-scores
opportunity_status: candidate
opportunity_kind: experiment
impact: high
feasibility: medium
readiness: medium
evidence_strength: high
linked_conflicts:
  - conflict.metal-specificity-vs-general-stress
linked_products:
  - data.metal-tolerance-scores
target_outputs:
  - Ranked rare-earth candidate gene families with controls and organism choices.
  - Minimal RB-TnSeq design brief for lanthanum, cerium, neodymium, and yttrium conditions.
  - Counter-ion and general-stress control matrix.
review_routes:
  - metal_fitness_atlas
  - metal_specificity
  - counter_ion_effects
evidence:
  - source: metal_specificity
    support: Cross-metal specificity separates candidate metal biology from broad sickness signals.
  - source: data.rare-earth-fitness-gap
    support: The Atlas currently treats rare-earth fitness as a missing complementary data class.
order: 10
---

# Rare-Earth RB-TnSeq Design

## Why It Matters

The Atlas has metal fitness breadth but not rare-earth direct measurements. That makes rare-earth biology a high-value gap: the first experiment can be designed from existing cross-metal structure rather than starting from an arbitrary gene list.

## Review Brief

What changed: the lanthanide methylotrophy claim adds genomic marker context, so this opportunity can now combine cross-metal inference with rare-earth marker calibration.

Why review matters: this is an experiment-design page. Reviewers should decide whether the candidate ranking and controls are strong enough to justify a concrete RB-TnSeq proposal.

Evidence to inspect:

- [Lanthanide-dependent methylotrophy is widespread and soil-linked](/atlas/claims/lanthanide-methylotrophy-widespread) for marker context.
- [Rare Earth Fitness Data Gap](/atlas/data/gaps/rare-earth-fitness-data) for the missing direct assay.
- [Metal specificity versus general stress](/atlas/conflicts/metal-specificity-vs-general-stress) for controls.
- `metal_specificity`, `counter_ion_effects`, and Bakta/AlphaFold evidence for candidate selection.

Questions for reviewers:

- Which REE conditions and counter-ion controls are most important for a first experiment?
- Which taxa have both relevant biology and usable mutant libraries?
- Should xoxF/lanmodulin marker evidence shape organism choice, candidate genes, or both?
- What minimum result would move rare-earth inference from prediction to validation?

## Evidence Base

The starting evidence is not a single hit table. It combines metal-specific fitness, counter-ion caveats, conserved family context, Bakta reannotation, AlphaFold structure, and field validation logic from BacDive. The opportunity is to turn that combined evidence into a defensible experimental design.

## Work Package

Rank candidate families by metal specificity, conservation, annotation novelty, structural plausibility, and assay caveat load. Select organisms with strong library support and interpretable baseline metal phenotypes. Build controls that separate rare-earth effects from counter-ion, osmotic, and generic stress effects.

## Decision Use

If this opportunity succeeds, [rare-earth cross-metal inference](/atlas/directions/rare-earth-cross-metal-inference) can move from prediction to validation, and [metal tolerance scores](/atlas/data/derived-products/metal-tolerance-scores) can record which candidates are supported by direct rare-earth assays.
