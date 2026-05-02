---
id: data.genomes-and-pangenomes
title: Genomes and Pangenomes
type: data_type
status: draft
summary: Data type lens for genome metadata, pangenome structure, annotations, and species-level comparative genomics.
source_projects:
  - pangenome_openness
  - openness_functional_composition
  - plant_microbiome_ecotypes
source_docs:
  - docs/schemas/pangenome.md
  - docs/schemas/genomes.md
related_collections:
  - kbase_ke_pangenome
  - kbase_genomes
  - kbase_uniref100
  - kbase_uniprot
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - topic.pangenome-architecture
  - data.pangenome-collection
order: 60
---

# Genomes and Pangenomes

## Why This Lens Exists

Tenant and collection boundaries do not always match how scientists ask questions. This data-type lens groups genome and pangenome resources by analytical use.

## Best Uses

- Conservation and openness analyses.
- Core/accessory/singleton functional enrichment.
- Species-level metadata and taxonomy stratification.
- Stable join keys for downstream derived products.

## Watch For

Sampling depth and clade imbalance can mimic biology. Agents should include genome-count and taxonomy controls in any pangenome-scale proposal.
