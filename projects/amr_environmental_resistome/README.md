# Environmental Resistome at Pangenome Scale

## Research Question

Do antimicrobial resistance gene profiles differ between ecological niches across 27,000 bacterial species? Using 83K AMR gene clusters mapped to 293K genomes with environmental metadata, we test whether the resistome is structured by ecology — and whether intrinsic (core) and acquired (accessory) resistance show different environmental signatures.

## Status

In Progress — research plan created.

## Overview

Prior work established that resistomes cluster by ecology in ~6,000 genomes (Gibson et al. 2015). We extend this analysis by 50× to the full BERDL pangenome (293K genomes, 27K species), asking whether AMR gene profiles differ between clinical, host-associated, soil, and aquatic environments. We separately analyze intrinsic (core) and acquired (accessory) resistance, testing whether intrinsic resistance reflects long-term niche adaptation while acquired resistance is more mobile across environments. The analysis controls for phylogenetic confounding and includes within-species environment comparisons for deeply-sampled species.

**BERDL collections**: `kbase_ke_pangenome` (bakta_amr, gene_cluster, pangenome, ncbi_env, genome, gtdb_taxonomy_r214v1, alphaearth_embeddings_all_years, interproscan_go)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

This project builds on data from:
- `amr_strain_variation` (Dehal, 2026) — species-level environment classification (91% coverage)
- `env_embedding_explorer` (Dehal, 2026) — AlphaEarth environmental embeddings
- `amr_fitness_cost` (Dehal, 2026) — AMR mechanism × conservation patterns

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
