# Environmental Resistome at Pangenome Scale

## Research Question

Do antimicrobial resistance gene profiles differ between ecological niches across 27,000 bacterial species? Using 83K AMR gene clusters mapped to 293K genomes with environmental metadata, we test whether the resistome is structured by ecology — and whether intrinsic (core) and acquired (accessory) resistance show different environmental signatures.

## Status

Complete — see [Report](REPORT.md) for findings. Clinical species carry 2.5× more AMR (median 5 vs 2, p=9.4e-167). Mechanism composition is strongly environment-dependent: efflux peaks in clinical/gut (21%), metal resistance in soil/aquatic (45%). Core vs accessory AMR varies from 43% accessory (soil) to 68% (clinical). Within species, clinical fraction predicts AMR count (rho=0.465, p=2.2e-45). All findings survive phylogenetic control (5/6 phyla, 20/141 families significant).

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

**Prerequisites:**
- Python 3.10+ with pandas, numpy, scipy, matplotlib, seaborn, statsmodels, scikit-learn, scikit-bio
- BERDL JupyterHub access (for NB01 Spark queries, NB03 temp view, NB04 AlphaEarth extraction)

**Pipeline:**
1. Execute `notebooks/01_data_extraction.ipynb` — Spark queries for AMR + environment + taxonomy (~20 min)
2. Execute `notebooks/02_resistome_vs_environment.ipynb` — species-level H1-H3 tests (~5 min, local)
3. Execute `notebooks/03_within_species.ipynb` — clinical enrichment proxy for H4 (~10 min, needs Spark)
4. Execute `notebooks/04_alphaearth_analysis.ipynb` — supplementary embedding analysis (~5 min, needs Spark)

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
