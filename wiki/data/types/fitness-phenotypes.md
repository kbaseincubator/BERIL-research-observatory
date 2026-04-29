---
id: data.fitness-phenotypes
title: Fitness Phenotypes
type: data_type
status: draft
summary: Data type lens for RB-TnSeq phenotypes, condition-specific gene effects, cofitness, essentiality, and pathway dependency.
source_projects:
  - essential_genome
  - essential_metabolome
  - metal_specificity
  - amr_cofitness_networks
source_docs:
  - docs/schemas/fitnessbrowser.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - topic.fitness-validated-function
  - data.fitnessbrowser-collection
order: 70
---

# Fitness Phenotypes

## Why This Lens Exists

Fitness phenotypes are the observatory's main experimental evidence stream for gene function. They should be treated as reusable evidence, not as one-off project outputs.

## Best Uses

- Essential gene and metabolome inference.
- Stress-specific gene discovery.
- Cofitness support networks.
- Functional hypothesis generation for dark genes.

## Watch For

Fitness phenotypes are condition-specific. Agents should carry organism coverage and experiment coverage into every downstream summary.
