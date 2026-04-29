---
id: data.kescience-tenant
title: KEScience Tenant and Fitness Evidence
type: data_tenant
status: draft
summary: Fitness Browser and related KEScience resources that provide experiment-backed genotype-to-phenotype evidence.
source_projects:
  - essential_genome
  - fitness_modules
  - metal_specificity
source_docs:
  - ui/config/collections.yaml
  - docs/schemas/fitnessbrowser.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - data.fitnessbrowser-collection
  - data.fitness-phenotypes
order: 20
---

# KEScience Tenant and Fitness Evidence

## Role In The Observatory

The KEScience fitness data turns gene presence into tested phenotype. It is the key evidence stream for essentiality, metal stress, metabolic dependency, cofitness, and annotation repair.

## Agent Use

Use this tenant when a claim depends on whether a gene matters under a condition. Do not substitute annotation for fitness when the Fitness Browser has relevant data.

## Caveat

Fitness evidence is condition-specific and organism-specific. Absence of a signal is not proof of absence of function outside the assayed context.
