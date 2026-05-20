---
id: conflict.metal-amr-co-selection-readiness
title: Metal-AMR co-selection readiness
type: conflict
status: draft
summary: BERIL has the pieces to test metal-AMR co-selection, but the current evidence is a strong opportunity rather than a resolved result.
source_projects:
  - metal_fitness_atlas
  - metal_specificity
  - amr_environmental_resistome
  - amr_pangenome_atlas
  - amr_fitness_cost
  - enigma_sso_asv_ecology
  - microbeatlas_metal_ecology
  - prophage_amr_comobilization
  - soil_metal_functional_genomics
  - t4ss_cazy_environmental_hgt
source_docs:
  - docs/discoveries.md
  - projects/microbeatlas_metal_ecology/REPORT.md
  - projects/prophage_amr_comobilization/REPORT.md
  - projects/soil_metal_functional_genomics/REPORT.md
  - projects/t4ss_cazy_environmental_hgt/REPORT.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
  - nmdc_metadata
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - topic.amr-resistance-ecology
  - topic.mobile-elements-phage
  - direction.metal-amr-co-selection
  - hypothesis.metal-amr-co-selection
  - data.amr-fitness-profiles
conflict_status: unresolved
affected_pages:
  - topic.critical-minerals
  - topic.amr-resistance-ecology
  - topic.mobile-elements-phage
  - direction.metal-amr-co-selection
  - hypothesis.metal-amr-co-selection
  - data.amr-fitness-profiles
evidence_sides:
  - side: opportunity
    sources:
      - metal_fitness_atlas
      - amr_environmental_resistome
      - enigma_sso_asv_ecology
      - microbeatlas_metal_ecology
    support: Metal tolerance, AMR profiles, and contaminated-site ecology are present in the observatory and can be joined.
  - side: not_yet_resolved
    sources:
      - amr_fitness_cost
      - metal_specificity
      - soil_metal_functional_genomics
    support: Co-selection requires distinguishing direct metal selection, AMR mechanism ecology, fitness cost, linkage, co-contamination, and site covariates.
  - side: mobile_context
    sources:
      - prophage_amr_comobilization
      - t4ss_cazy_environmental_hgt
    support: Mobile-element burden predicts AMR breadth and appears linked to some metal-associated environmental HGT hubs, but this can confound selection claims unless modeled explicitly.
resolving_work:
  - Build a site-level join of metal/geochemistry, AMR mechanism profiles, metal tolerance scores, taxonomy, and metadata quality.
  - Test metal-AMR association after controlling for phylogeny, environment label, and sampling depth.
  - Prioritize cases where AMR and metal-tolerance signals are genetically linked or co-occur in the same taxa.
  - Add prophage density, plasmid/ICE/T4SS markers, metal co-contamination, and spatial proximity sensitivity as covariates.
order: 40
---

# Metal-AMR Co-selection Readiness

## Tension

The Atlas can now formulate the co-selection question, but formulation is not proof. The current evidence says the test is high value, not that the result is already known.

## Review Brief

What changed: new project evidence added metal type diversity, prophage density, soil metal-function associations, and T4SS/CAZy/metal co-enrichment to the co-selection question.

Why review matters: this conflict is the guardrail against turning a good DOE-site analysis into a premature claim. Reviewers should decide whether the resolving analysis has the right covariates and whether any side of the tension is missing.

Evidence to inspect:

- Metal tolerance and specificity evidence from `metal_fitness_atlas` and `metal_specificity`.
- AMR environment and fitness-cost evidence from the AMR project set.
- Mobile-context evidence from `prophage_amr_comobilization` and `t4ss_cazy_environmental_hgt`.
- Site and chemistry covariates from ENIGMA, NMDC, and soil metal projects.

Questions for reviewers:

- Are the proposed controls sufficient: taxonomy, habitat, sampling depth, metal co-contamination, mobile-element burden, and metadata quality?
- Should mobile-element burden be treated as a covariate, a mediator, or a separate mechanism?
- Which site or collection is ready enough for the first co-selection benchmark?
- What result would resolve the conflict rather than merely add another correlation?

## Current Interpretation

Use this as a direction and hypothesis seed. Do not cite it as a resolved co-selection finding until site-level joins and controls are complete.

## Resolving Analysis

The resolving analysis is a controlled contaminated-site benchmark that joins metal exposure, AMR profiles, metal tolerance scores, mobile-element context, and environmental covariates.
