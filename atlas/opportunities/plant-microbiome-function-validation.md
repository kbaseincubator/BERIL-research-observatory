---
id: opportunity.plant-microbiome-function-validation
title: Plant Microbiome Function Validation
type: opportunity
status: draft
summary: Validate whether plant microbiome functional signals persist across ecotype labels, pangenome context, and environmental metadata.
source_projects:
  - plant_microbiome_ecotypes
  - pgp_pangenome_ecology
  - nmdc_community_metabolic_ecology
  - phb_granule_ecology
source_docs:
  - docs/discoveries.md
  - docs/research_ideas.md
related_collections:
  - nmdc_arkin
  - plantmicrobeinterfaces_gtdb_mapping
  - kbase_ke_pangenome
  - kbase_msd_biochemistry
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.plant-microbiome-function
  - topic.microbial-ecotypes-environment
  - data.ecotype-assignments
  - data.functional-innovation-ko-atlas
  - data.environment-geochemistry-ecology
opportunity_status: candidate
opportunity_kind: validation
impact: medium
feasibility: medium
readiness: medium
evidence_strength: medium
linked_conflicts:
  - conflict.ecotype-translation-leakage
linked_products:
  - data.ecotype-assignments
  - data.functional-innovation-ko-atlas
target_outputs:
  - Cross-study validation table for plant microbiome functional signals.
  - List of functions robust to ecotype, taxonomy, and environment controls.
  - Missing metadata checklist for blocked plant-microbiome claims.
review_routes:
  - plant_microbiome_ecotypes
  - pgp_pangenome_ecology
  - nmdc_community_metabolic_ecology
evidence:
  - source: plant_microbiome_ecotypes
    support: Plant microbiome ecotype analysis provides reusable labels and validation caveats.
  - source: nmdc_community_metabolic_ecology
    support: Community metabolic ecology provides a route to connect function and environment.
order: 100
---

# Plant Microbiome Function Validation

## Why It Matters

Plant microbiome synthesis is useful only if functional signals remain interpretable across study, host, taxonomy, and environment. This opportunity makes that validation explicit.

## Review Brief

What changed: plant microbiome function is now treated as a reviewable validation problem rather than a marker-list topic.

Why review matters: reviewers should decide whether plant-associated functional signals survive ecotype, taxonomy, compartment, and environment controls strongly enough to support reuse.

Evidence to inspect:

- [Plant Microbiome Function and Agriculture](/atlas/topics/plant-microbiome-function) for topic synthesis.
- [Ecotype Assignments](/atlas/data/derived-products/ecotype-assignments) and [Functional Innovation KO Atlas](/atlas/data/derived-products/functional-innovation-ko-atlas) for input products.
- `plant_microbiome_ecotypes`, `pgp_pangenome_ecology`, and `nmdc_community_metabolic_ecology` for source evidence.

Questions for reviewers:

- Which plant function signals are robust after study and taxonomy controls?
- Are PGP/pathogenicity markers being interpreted too literally?
- What metadata is missing for host compartment or environment comparisons?
- Which validated signal should become the first plant-focused derived product?

## Evidence Base

The Atlas connects plant ecotype labels, pangenome pathway ecology, NMDC metabolic ecology, and environmental data types. The unresolved issue is whether the same function claims survive stronger controls.

## Work Package

Select plant-associated studies with enough metadata. Join ecotype labels, pangenome function signals, environmental annotations, and pathway data. Test whether key functions remain associated with plant or environment contexts after controlling for study and taxonomy.

## Decision Use

The result should update the plant microbiome topic and clarify which derived products are safe to reuse for plant-focused research directions.
