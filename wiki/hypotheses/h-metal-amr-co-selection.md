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
source_docs:
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - enigma_coral
  - kescience_fitnessbrowser
confidence: low
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - direction.metal-amr-co-selection
evidence:
  - source: amr_environmental_resistome
    support: Environmental AMR composition provides the resistance-response side of the test.
  - source: metal_fitness_atlas
    support: Metal tolerance and gene-metal fitness signals provide the metal-response side of the test.
order: 30
---

# Metal contamination co-selects AMR mechanisms

## Hypothesis

Metal-contaminated environments select for AMR mechanisms directly or indirectly through shared transport, stress response, mobile elements, or ecological filtering.

## Testable With

AMR annotations, metal tolerance scores, environmental metadata, ENIGMA site context, and phylogenetic controls.

## Failure Mode

Taxonomic composition alone explains the signal. The test must include nulls or stratification.
