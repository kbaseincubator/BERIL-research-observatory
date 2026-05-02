---
id: data.environment-harmonization
title: Environment Harmonization Labels
type: derived_product
status: draft
summary: Reusable environment category and coordinate-quality labels that make cross-collection ecology joins safer.
source_projects:
  - env_embedding_explorer
  - ecotype_env_reanalysis
  - enigma_sso_asv_ecology
source_docs:
  - projects/env_embedding_explorer/REPORT.md
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - nmdc_metadata
  - nmdc_arkin
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topic.microbial-ecotypes-environment
  - data.environment-geochemistry-ecology
  - conflict.lab-fitness-field-generalization
product_kind: label_set
reuse_status: promoted
produced_by_projects:
  - env_embedding_explorer
used_by_projects:
  - ecotype_env_reanalysis
  - enigma_sso_asv_ecology
output_artifacts:
  - path: projects/env_embedding_explorer/data/coverage_stats.csv
    description: Coverage summary for environment and coordinate metadata.
    status: table
  - path: projects/env_embedding_explorer/figures/umap_by_env_category.png
    description: Overview figure for environment categories on AlphaEarth embeddings.
    status: figure
review_routes:
  - env_embedding_explorer
  - ecotype_env_reanalysis
evidence:
  - source: env_embedding_explorer
    support: The project created reusable environment categories and metadata coverage diagnostics.
  - source: ecotype_env_reanalysis
    support: The reanalysis demonstrates why environment-only checks need stable category labels.
order: 95
---

# Environment Harmonization Labels

## Reusable Object

This product turns free-text environment and coordinate metadata into a reusable set of categories, coverage flags, and quality caveats. It is most useful when a project needs to compare ecology across BERDL collections without treating raw isolation strings as stable labels.

## Why It Is High Value

Many observatory questions depend on environment context: metal tolerance, ecotypes, AMR structure, plant compartments, and field/lab validation. A shared label layer prevents each project from rebuilding a slightly different environment mapping.

## High-Value Joins

- Join species or genome records to harmonized environment labels before testing field enrichment.
- Join AlphaEarth embeddings to labels to check whether geography, environment, and metadata completeness are confounded.
- Join ENIGMA or NMDC samples to the same label vocabulary before comparing community structure.

## Caveats

Environment labels are analytical conveniences, not ground truth. Reuse should preserve coordinate quality, missingness, and source-field provenance.
