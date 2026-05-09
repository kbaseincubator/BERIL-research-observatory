---
id: claim.lab-fitness-predicts-field-ecology
title: Lab fitness can predict field ecology
type: claim
status: draft
summary: Several projects suggest that lab-measured fitness signals can align with environmental abundance or isolation context when validation data are available.
source_projects:
  - lab_field_ecology
  - field_vs_lab_fitness
  - bacdive_metal_validation
  - enigma_sso_asv_ecology
source_docs:
  - docs/discoveries.md
related_collections:
  - kescience_fitnessbrowser
  - enigma_coral
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.microbial-ecotypes-environment
  - hypothesis.lab-field-metal-tolerance
  - conflict.lab-fitness-field-generalization
evidence:
  - source: lab_field_ecology
    support: Lab fitness signals were compared against environmental abundance or field context.
  - source: bacdive_metal_validation
    support: Metal tolerance predictions were checked against BacDive phenotype and isolation metadata.
order: 20
---

# Lab fitness can predict field ecology

## Claim

Lab fitness signals can sometimes predict field ecology or isolation environments, especially when linked to well-structured environmental metadata.

## Review Brief

What changed: this claim now supports multiple field, metal, and community-design pages, while newer environmental projects add more caveats around metadata and design.

Why review matters: reviewers should decide where lab fitness is validated evidence and where it should be framed only as a prior.

Evidence to inspect:

- `lab_field_ecology` and `field_vs_lab_fitness` for transfer tests.
- `bacdive_metal_validation` for phenotype and isolation metadata.
- `enigma_sso_asv_ecology` for site-level ecology.
- [Lab fitness signals versus field ecology](/atlas/conflicts/lab-fitness-field-generalization) for scope limits.

Questions for reviewers:

- Which field variables were predicted, and under what metadata quality?
- Should the claim be split by metal tolerance, abundance, isolation context, and community composition?
- What missing geochemistry or covariate would most reduce confidence?
- Is "can predict" appropriately cautious, or should the claim be narrower?

## Evidence

The field/lab ecology projects and metal-validation projects use measured fitness or tolerance-derived scores against field or phenotype contexts.

## Why It Matters

This is a central bridge from controlled experiments to BERDL-scale environmental inference.

## Caveats

This claim should not be generalized without metadata quality checks, site-specific covariates, and validation against independent field measurements.
