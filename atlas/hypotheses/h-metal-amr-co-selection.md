---
id: hypothesis.metal-amr-co-selection
title: Metal contamination co-selects AMR mechanisms
type: hypothesis
status: draft
summary: Metal-contaminated environments carry higher AMR burden or different AMR mechanism composition after controlling for taxonomy and site context.
source_projects:
  - amr_environmental_resistome
  - metal_fitness_atlas
  - enigma_sso_asv_ecology
  - resistance_hotspots
  - microbeatlas_metal_ecology
  - prophage_amr_comobilization
  - soil_metal_functional_genomics
source_docs:
  - docs/discoveries.md
  - projects/microbeatlas_metal_ecology/REPORT.md
  - projects/prophage_amr_comobilization/REPORT.md
  - projects/soil_metal_functional_genomics/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - enigma_coral
  - kescience_fitnessbrowser
confidence: low
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - direction.metal-amr-co-selection
  - conflict.metal-amr-co-selection-readiness
  - claim.prophage-density-predicts-amr-breadth
  - claim.metal-type-diversity-predicts-niche-breadth
evidence:
  - source: amr_environmental_resistome
    support: Environmental AMR composition provides the resistance-response side of the test.
  - source: metal_fitness_atlas
    support: Metal tolerance and gene-metal fitness signals provide the metal-response side of the test.
  - source: microbeatlas_metal_ecology
    support: Metal type diversity predicts niche breadth after phylogenetic control, giving a field-scale covariate for co-selection models.
  - source: prophage_amr_comobilization
    support: Prophage density predicts AMR breadth and should be modeled as a mobile-element confound or mediator.
order: 30
---

# Metal contamination co-selects AMR mechanisms

## Hypothesis

Metal-contaminated environments select for AMR mechanisms directly or indirectly through shared transport, stress response, mobile elements, or ecological filtering.

## Testable With

AMR annotations, metal tolerance scores, metal type diversity, prophage/mobile-element burden, soil or site geochemistry, ENIGMA site context, and phylogenetic controls.

## Failure Mode

Taxonomic composition, mobile-element burden, co-contaminating metals, spatial sampling, or project effects explain the signal. The test must include nulls, stratification, and sensitivity analyses.
