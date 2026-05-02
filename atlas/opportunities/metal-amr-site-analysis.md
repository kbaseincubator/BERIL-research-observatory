---
id: opportunity.metal-amr-site-analysis
title: Metal-AMR Site Co-Selection Analysis
type: opportunity
status: draft
summary: Test whether metal contamination at BER-relevant sites co-selects antibiotic resistance mechanisms using metal fitness, AMR profiles, and environmental metadata.
source_projects:
  - metal_fitness_atlas
  - metal_specificity
  - resistance_hotspots
  - amr_environmental_resistome
  - enigma_sso_asv_ecology
source_docs:
  - docs/discoveries.md
  - docs/research_ideas.md
related_collections:
  - kescience_fitnessbrowser
  - enigma_coral
  - kbase_ke_pangenome
  - nmdc_metadata
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topic.critical-minerals
  - topic.amr-resistance-ecology
  - direction.metal-amr-co-selection
  - hypothesis.metal-amr-co-selection
  - data.amr-fitness-profiles
  - data.metal-tolerance-scores
opportunity_status: candidate
opportunity_kind: analysis
impact: high
feasibility: high
readiness: high
evidence_strength: medium
linked_conflicts:
  - conflict.metal-amr-co-selection-readiness
linked_products:
  - data.amr-fitness-profiles
  - data.metal-tolerance-scores
target_outputs:
  - Site-by-site metal tolerance and AMR enrichment matrix.
  - Matched null model separating taxonomy, environment, and metal signal.
  - Shortlist of sites or taxa needing experimental confirmation.
review_routes:
  - resistance_hotspots
  - amr_environmental_resistome
  - metal_specificity
evidence:
  - source: resistance_hotspots
    support: AMR mechanism composition is already structured by environmental context.
  - source: metal_fitness_atlas
    support: Metal tolerance can be represented as reusable gene and taxon scores.
order: 20
---

# Metal-AMR Site Co-Selection Analysis

## Why It Matters

The Atlas currently treats metal-AMR co-selection as plausible but unresolved. This opportunity turns the tension into a concrete analysis: do metal-associated taxa, genes, or environments also show enriched AMR mechanisms after controlling for taxonomy and habitat?

## Evidence Base

The analysis can reuse [AMR Fitness Profiles](/atlas/data/derived-products/amr-fitness-profiles), [Metal Tolerance Scores](/atlas/data/derived-products/metal-tolerance-scores), ENIGMA site ecology, and environmental metadata. The key is not to show that metals and AMR both occur in the same broad environment, but to test whether the co-occurrence remains after stronger controls.

## Work Package

Build matched site or sample groups by environment, taxonomy, and metadata completeness. Compute AMR burden, metal tolerance score, and mechanism composition for each group. Test whether metal signal explains AMR variation beyond confounders and record where metadata gaps prevent interpretation.

## Decision Use

If supported, [metal-AMR co-selection](/atlas/directions/metal-amr-co-selection) becomes a stronger DOE-relevant direction. If not supported, the Atlas should preserve the negative result and narrow co-selection claims to specific taxa, metals, or sites.
