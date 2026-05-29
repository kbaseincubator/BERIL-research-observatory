---
id: conflict.metal-specificity-vs-general-stress
title: Metal specificity versus general stress
type: conflict
status: draft
summary: Metal fitness hits include both specific metal biology and broad stress response, so engineering targets need specificity filters and counter-ion controls.
source_projects:
  - metal_fitness_atlas
  - metal_specificity
  - counter_ion_effects
  - lanthanide_methylotrophy_atlas
  - soil_metal_functional_genomics
source_docs:
  - docs/discoveries.md
  - projects/lanthanide_methylotrophy_atlas/REPORT.md
  - projects/soil_metal_functional_genomics/REPORT.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - claim.metal-specific-genes-core-enriched
  - claim.lanthanide-methylotrophy-widespread
  - data.metal-tolerance-scores
conflict_status: partially_resolved
affected_pages:
  - topic.critical-minerals
  - claim.metal-specific-genes-core-enriched
  - claim.lanthanide-methylotrophy-widespread
  - data.metal-tolerance-scores
evidence_sides:
  - side: conserved_metal_signal
    sources:
      - metal_fitness_atlas
      - metal_specificity
    support: Conserved families retain metal-associated fitness phenotypes even after specificity filtering.
  - side: broad_stress_and_counter_ion
    sources:
      - metal_specificity
      - counter_ion_effects
      - soil_metal_functional_genomics
    support: Some apparent metal hits reflect general sickness, counter-ion effects, osmotic stress, co-contamination, or assay context rather than metal-specific mechanism.
  - side: marker_source_uncertainty
    sources:
      - lanthanide_methylotrophy_atlas
    support: Rare-earth marker interpretation can change by annotation source; lanmodulin and xoxJ require calibrated marker choices before functional claims are reused.
resolving_work:
  - Pair each metal condition with counter-ion and osmotic controls.
  - Report non-metal sick-rate for every candidate family.
  - Promote only candidates with specificity, conservation, and independent annotation or structural support.
  - For field associations, report partial metal models and effect sizes rather than only FDR-ranked COG-metal links.
  - For rare-earth markers, record marker-source choice and known false-positive modes.
order: 30
---

# Metal Specificity Versus General Stress

## Tension

Metal screens are rich, but not every metal hit is metal biology. The useful synthesis depends on separating conserved metal-specific mechanisms from broad stress or assay context.

## Review Brief

What changed: this conflict now covers not only RB-TnSeq specificity and counter-ion effects, but also rare-earth marker uncertainty and field-scale co-contamination from soil metal analyses.

Why review matters: metal targets are only useful if reviewers trust that they are not generic stress artifacts. This page should define the minimum evidence needed before a candidate becomes an engineering target or promoted claim.

Evidence to inspect:

- Non-metal sick-rate filtering from `metal_specificity`.
- Counter-ion and osmotic-control needs from `counter_ion_effects`.
- Marker-source uncertainty from `lanthanide_methylotrophy_atlas`.
- Co-contaminating metals and conditional R2 interpretation from `soil_metal_functional_genomics`.

Questions for reviewers:

- Is the current specificity filter strict enough for engineering target prioritization?
- Which counter-ion or osmotic controls should be mandatory for new metal assays?
- Should rare-earth marker calibration be handled here, or split into a separate conflict?
- What evidence is required to promote a field metal-function association to a reusable claim?

## Current Interpretation

Metal tolerance scores should be reused with specificity labels and counter-ion caveats attached. The strongest engineering candidates survive both filters.

## Resolving Analysis

The decisive analysis is a paired-condition design that measures metal salt, matched counter-ion, osmotic control, and non-metal stress response in the same scoring framework.
