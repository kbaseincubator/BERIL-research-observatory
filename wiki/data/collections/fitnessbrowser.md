---
id: data.fitnessbrowser-collection
title: Fitness Browser Collection
type: data_collection
status: draft
summary: RB-TnSeq fitness evidence used to validate gene function, stress response, essentiality, cofitness, and pathway dependency.
source_projects:
  - essential_genome
  - metal_fitness_atlas
  - fitness_modules
source_docs:
  - ui/config/collections.yaml
  - docs/schemas/fitnessbrowser.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
  - kbase_phenotype
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - data.fitness-phenotypes
  - data.genome-fitness-pangenome-join
order: 50
---

# Fitness Browser Collection

## What It Enables

Fitness Browser connects genes to measured phenotypes across conditions. It is the primary collection for turning annotation hypotheses into condition-specific evidence.

## Reuse Pattern

Agents should join fitness records to pangenome identifiers, pathway mappings, and module assignments when proposing functional claims.

## Caveats

Missing genes, essential genes, locus-ID mismatches, and condition coverage all affect interpretation.
