---
id: data.environment-geochemistry-ecology
title: Environment, Geochemistry, and Ecology
type: data_type
status: draft
summary: Environmental samples, coordinates, geochemistry, sample metadata, and ecology-facing observations used to validate laboratory predictions in the field.
source_projects:
  - harvard_forest_warming
  - microbeatlas_metal_ecology
  - metal_resistance_global_biogeography
  - soil_frontier_genomics
  - soil_metal_functional_genomics
source_docs:
  - ui/config/berdl_collections_snapshot.json
  - projects/harvard_forest_warming/REPORT.md
  - projects/microbeatlas_metal_ecology/REPORT.md
  - projects/metal_resistance_global_biogeography/REPORT.md
  - projects/soil_frontier_genomics/REPORT.md
  - projects/soil_metal_functional_genomics/REPORT.md
related_collections:
  - enigma_coral
  - planetmicrobe_planetmicrobe
  - planetmicrobe_planetmicrobe_raw
  - nmdc_ncbi_biosamples
  - nmdc_metadata
  - nmdc_results
  - arkinlab_microbeatlas
  - kescience_mgnify
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - data.index
  - topic.microbial-ecotypes-environment
  - claim.metal-type-diversity-predicts-niche-breadth
order: 73
---

# Environment, Geochemistry, and Ecology

## Why This Lens Exists

Tenant and database boundaries do not match how scientists or agents plan analyses. This data-type lens groups collections by the kind of evidence they provide and the questions they make easier to ask.

## Collections In This Lens

- `enigma_coral`
- `planetmicrobe_planetmicrobe`
- `planetmicrobe_planetmicrobe_raw`
- `nmdc_ncbi_biosamples`
- `kbase_ke_pangenome`

## Best Uses

Use this lens to find reusable source data before choosing a specific collection. It is especially useful for agents that need to identify complementary data, select join keys, or explain why a derived product is reusable across projects.

Recent project use: Harvard Forest warming uses NMDC metadata/results to expose omics-layer and design confounds; MicrobeAtlas metal ecology uses global 16S ecology to estimate niche breadth; MGnify and soil metal projects expose coordinate coverage, geochemistry joins, and spatial-validation requirements.

## Metrics To Watch

- Evidence traces: which projects already used these collections.
- Reuse: whether derived products exist beyond a single project.
- Under-explored combinations: collection pairs with obvious scientific value but few projects.
- Caveat load: schema gaps, identifier mismatches, sampling bias, and staging status.
- Field validation quality: coordinate coverage, spatial blocking, project effects, confound structure, and effect-size reporting.

## Caveats

Do not treat collection co-membership as proof that a join is valid. A join recipe should name stable identifiers, filtering rules, and failure modes before it supports a claim.
