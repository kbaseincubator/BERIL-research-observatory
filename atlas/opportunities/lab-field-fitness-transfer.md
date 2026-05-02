---
id: opportunity.lab-field-fitness-transfer
title: Lab-to-Field Fitness Transfer Audit
type: opportunity
status: draft
summary: Audit where laboratory fitness effects predict field ecology and where geochemistry, taxonomy, or metadata completeness blocks transfer.
source_projects:
  - lab_field_ecology
  - field_vs_lab_fitness
  - metal_fitness_atlas
  - bacdive_metal_validation
source_docs:
  - docs/discoveries.md
  - docs/pitfalls.md
related_collections:
  - kescience_fitnessbrowser
  - enigma_coral
  - kescience_bacdive
  - nmdc_metadata
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topic.fitness-validated-function
  - topic.microbial-ecotypes-environment
  - topic.critical-minerals
  - claim.lab-fitness-predicts-field-ecology
  - hypothesis.lab-field-metal-tolerance
  - data.environment-harmonization
opportunity_status: candidate
opportunity_kind: validation
impact: high
feasibility: medium
readiness: medium
evidence_strength: medium
linked_conflicts:
  - conflict.lab-fitness-field-generalization
linked_products:
  - data.environment-harmonization
  - data.metal-tolerance-scores
target_outputs:
  - Transferability matrix by phenotype class, environment, and metadata completeness.
  - List of field covariates that most improve or block interpretation.
  - Revised caveat labels for lab-derived field claims.
review_routes:
  - lab_field_ecology
  - field_vs_lab_fitness
  - bacdive_metal_validation
evidence:
  - source: lab_field_ecology
    support: Lab fitness can predict field ecology, but transfer depends on metadata and ecological context.
  - source: conflict.lab-fitness-field-generalization
    support: The Atlas preserves unresolved scope limits around field generalization.
order: 40
---

# Lab-to-Field Fitness Transfer Audit

## Why It Matters

The Atlas increasingly uses laboratory fitness to support ecological interpretation. That is valuable, but it needs an audit trail: which fitness signals transfer, under what metadata conditions, and where field covariates dominate?

## Evidence Base

The strongest starting point is the combination of lab-field ecology, metal validation, BacDive phenotypes, and environment harmonization. The audit should distinguish support for a narrow claim from evidence for broad field prediction.

## Work Package

Create a matrix of lab phenotype classes, field environments, available covariates, and predictive performance. Label each claim as supported, conditionally supported, blocked by metadata, or contradicted. Capture the missing data that would most improve each blocked case.

## Decision Use

This gives future Atlas pages a clear standard for using lab fitness as ecological evidence. It also identifies which new BERDL joins or field metadata would unlock the most claims.
