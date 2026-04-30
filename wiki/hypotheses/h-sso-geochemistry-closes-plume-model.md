---
id: hypothesis.sso-geochemistry-closes-plume-model
title: SSO geochemistry closes the plume model
type: hypothesis
status: draft
summary: Ingested SSO geochemistry will align microbial community gradients with measured metal, redox, and nutrient chemistry.
source_projects:
  - enigma_sso_asv_ecology
  - genotype_to_phenotype_enigma
  - enigma_contamination_functional_potential
source_docs:
  - docs/discoveries.md
  - docs/schemas/enigma.md
related_collections:
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - data.missing-sso-geochemistry
  - topic.microbial-ecotypes-environment
evidence:
  - source: enigma_sso_asv_ecology
    support: SSO community gradients exist, but geochemistry ingestion is needed to separate spatial and chemical drivers.
  - source: docs/schemas/enigma.md
    support: ENIGMA schema documentation defines the expected join context for site-level validation.
order: 80
---

# SSO geochemistry closes the plume model

## Hypothesis

When SSO geochemistry is ingested, measured chemistry will explain community similarity and functional gradients better than spatial position alone.

## Testable With

SSO sample IDs, geochemistry assays, ASV/community tables, and spatial well metadata.

## Why It Matters

This is a concrete missing-data experiment that can turn a strong ecological narrative into a validated site model.
