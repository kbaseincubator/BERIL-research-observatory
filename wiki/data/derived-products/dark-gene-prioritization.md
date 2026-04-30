---
id: data.dark-gene-prioritization
title: Dark Gene Prioritization Tables
type: derived_product
status: draft
summary: Reusable ranked dark-gene candidates, covering sets, and experiment plans derived from fitness, pangenome, annotation, and ecology evidence.
source_projects:
  - functional_dark_matter
  - truly_dark_genes
  - fitness_modules
source_docs:
  - projects/functional_dark_matter/REPORT.md
  - projects/truly_dark_genes/RESEARCH_PLAN.md
related_collections:
  - kescience_fitnessbrowser
  - kbase_ke_pangenome
  - pangenome_bakta
  - kbase_uniprot
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topic.fitness-validated-function
  - data.genome-fitness-pangenome-join
product_kind: candidate_list
reuse_status: promoted
produced_by_projects:
  - functional_dark_matter
used_by_projects:
  - truly_dark_genes
output_artifacts:
  - path: projects/functional_dark_matter/data/prioritized_candidates.tsv
    description: Ranked candidate table with integrated evidence.
    status: table
  - path: projects/functional_dark_matter/data/experimental_action_plan.tsv
    description: Candidate organisms and actions for experimental follow-up.
    status: table
review_routes:
  - functional_dark_matter
  - truly_dark_genes
evidence:
  - source: functional_dark_matter
    support: Integrates annotation darkness, fitness effects, concordance, conservation, and ecological validation.
  - source: truly_dark_genes
    support: Reuses parent outputs to separate annotation lag from genuinely dark families.
order: 96
---

# Dark Gene Prioritization Tables

## Reusable Object

These tables are ranked candidate lists for unknown or poorly annotated genes. They compress multi-source evidence into reusable priorities for characterization, module interpretation, and experiment design.

## Why It Is High Value

The product lets later projects start from a reviewed candidate universe instead of repeating raw extraction and scoring. It also carries caveats about annotation lag, ortholog coverage, fitness artifacts, and taxonomic breadth.

## High-Value Joins

- Join candidates to Bakta and UniProt updates to detect annotation repair.
- Join candidates to ICA modules and cofitness neighbors to move from genes to systems.
- Join candidate carrier taxa to environment labels to test ecological relevance.

## Caveats

Prioritization is not functional validation. Reuse should preserve the score components and avoid treating a high rank as a discovered mechanism.
