# Functional Dark Matter — Experimentally Prioritized Novel Genetic Systems

## Research Question

Which genes of unknown function across 48 bacteria have strong fitness phenotypes, and can biogeographic patterns, pathway gap analysis, and cross-organism fitness concordance — combined with existing function predictions and conservation data — prioritize them for experimental follow-up?

## Status

Complete — all 5 notebooks executed, 100 prioritized candidates produced. See [Report](REPORT.md) for findings.

## Overview

Nearly one in four bacterial genes lacks functional annotation ("hypothetical protein"), yet many have experimentally measured fitness effects in the Fitness Browser's 27M measurements across 7,552 conditions. Previous observatory projects have already: predicted function for 6,691 hypothetical proteins via ICA modules (`fitness_modules`), identified 1,382 hypothetical essentials (`essential_genome`), and linked 177,863 FB genes to pangenome conservation status (`conservation_vs_fitness`).

This project builds on those foundations with genuinely new analyses: (1) GapMind pathway gap-filling to find dark genes encoding missing enzymatic steps, (2) cross-organism fitness concordance testing whether orthologs of the same dark gene show the same phenotypes, (3) biogeographic analysis using AlphaEarth satellite embeddings and NCBI metadata to test whether carrier environments match lab fitness conditions, and (4) integrated experimental prioritization producing a ranked candidate list.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

This project explicitly builds on completed projects:
- [`conservation_vs_fitness`](../conservation_vs_fitness/) — FB-pangenome link table (177,863 gene-cluster mappings, 44 organisms)
- [`fitness_modules`](../fitness_modules/) — ICA fitness modules (1,116 modules, 32 organisms, 6,691 function predictions)
- [`essential_genome`](../essential_genome/) — Essential gene families (17,222 ortholog groups, 1,382 predictions)
- [`module_conservation`](../module_conservation/) — Module conservation patterns (86% core, 48 accessory modules)

## Reproduction

**Prerequisites**: BERDL JupyterHub access with `get_spark_session()` available (NB01–NB04 require Spark). NB05 runs locally on pandas only.

**Dependencies**: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `statsmodels`, `scikit-learn`, `umap-learn`

**Steps**:
1. Ensure prior project data exists: `conservation_vs_fitness/data/fb_pangenome_link.tsv`, `fitness_modules/data/modules/`, `essential_genome/data/`
2. Execute notebooks in order: `jupyter nbconvert --to notebook --execute --inplace notebooks/01_integration_census.ipynb`
3. Repeat for NB02 through NB05 (NB05 does not require Spark)
4. All intermediate data is saved to `data/`; figures to `figures/`

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory
