---
id: data.genome-fitness-pangenome-join
title: Genome-Fitness-Pangenome Join
type: join_recipe
status: draft
summary: Reusable join pattern that connects gene families, genome conservation, and RB-TnSeq fitness phenotypes.
source_projects:
  - conservation_vs_fitness
  - essential_genome
  - metal_specificity
  - metabolic_capability_dependency
source_docs:
  - docs/schema.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - topic.fitness-validated-function
  - data.fitness-phenotypes
order: 100
---

# Genome-Fitness-Pangenome Join

## Join Purpose

This join turns three separate questions into one: where is a gene in the pangenome, what is it annotated to do, and what happens when it is disrupted?

## Reuse Cases

- Essential gene conservation.
- Metal-specific gene classification.
- Metabolic capability versus dependency.
- Dark gene prioritization.

## Join-Key Discipline

Agents should preserve the exact identifier mapping used by the producing project. Locus ID format mismatches are a known failure mode and should not be silently repaired.
