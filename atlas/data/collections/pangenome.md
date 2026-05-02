---
id: data.pangenome-collection
title: Pangenome Collection
type: data_collection
status: draft
summary: Genome and pangenome tables for comparative genomics, conservation, openness, annotation, and cross-project derived products.
source_projects:
  - pangenome_openness
  - cog_analysis
  - conservation_vs_fitness
source_docs:
  - ui/config/collections.yaml
  - docs/schemas/pangenome.md
related_collections:
  - kbase_ke_pangenome
  - kbase_genomes
  - kbase_uniref100
  - kbase_uniprot
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - data.genomes-and-pangenomes
  - data.genome-fitness-pangenome-join
order: 40
---

# Pangenome Collection

## What It Enables

This collection lets agents ask which genes are core, accessory, singleton, annotated, conserved, open-clade associated, or linked to pathways across microbial species.

## Reuse Pattern

Most high-value reuse starts by selecting stable genome, species, gene, or gene-cluster identifiers, then joining to fitness, environment, biochemistry, or annotation collections.

## Caveats

Pangenome metrics require controls for genome count, clade composition, assembly quality, and sampling bias.
