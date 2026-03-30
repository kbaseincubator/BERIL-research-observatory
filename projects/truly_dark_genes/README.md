# Truly Dark Genes — What Remains Unknown After Modern Annotation?

## Research Question

Among the ~6,400 Fitness Browser genes that remain functionally unannotated even after bakta v1.12.0 reannotation, what distinguishes them from "annotation-lag" dark matter, and can their fitness phenotypes, genomic context, and sparse annotations prioritize them for experimental characterization?

## Status

Complete — see [Report](REPORT.md) for findings.

## Overview

The `functional_dark_matter` project identified 57,011 "dark" genes across 48 Fitness Browser organisms. However, NB12 (bakta enrichment) revealed that 83.7% of linked dark genes are annotated by bakta v1.12.0 — meaning most "dark matter" is actually an annotation vintage problem, not genuinely unknown biology. This project focuses on the residual ~6,400 genes where both the Fitness Browser's original annotation AND bakta's current UniProt-based pipeline agree: these proteins are hypothetical. These are the truly dark genes — the hardest cases that resist annotation by all current methods.

The key reframe: instead of 57,011 candidates, we now have ~6,400 genuinely unknown genes to characterize. This is a tractable number. We ask: What makes them resist annotation? Are they still biologically important? What sparse clues exist (UniRef50, Pfam HMMER hits, fitness modules)? And which ones should be studied first?

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

### BERDL Collections

- `kescience_fitnessbrowser` — Fitness phenotypes for all 48 organisms
- `kbase_ke_pangenome` — Pangenome conservation, bakta annotations, eggNOG annotations

### Prior Observatory Projects

- [`functional_dark_matter`](../functional_dark_matter/) — Parent project: 57,011 dark gene census, darkness tiers, prioritized candidates, bakta enrichment (NB12)
- [`conservation_vs_fitness`](../conservation_vs_fitness/) — FB-pangenome link table (177,863 mappings)
- [`fitness_modules`](../fitness_modules/) — ICA fitness modules (1,116 modules, 6,142 dark genes in modules)
- [`essential_genome`](../essential_genome/) — Essential gene families (1,382 predictions)

## Reproduction

**Prerequisites**: BERDL JupyterHub access with `get_spark_session()` available for NB01-NB02. NB03+ run locally on pandas/scipy.

**Dependencies**: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`

**Steps**:
1. Ensure prior project data exists: `functional_dark_matter/data/bakta_dark_gene_annotations.tsv`, `functional_dark_matter/data/dark_gene_census_full.tsv`, `functional_dark_matter/data/updated_darkness_tiers.tsv`
2. Execute notebooks in order: `jupyter nbconvert --to notebook --execute --inplace notebooks/01_truly_dark_census.ipynb`
3. Repeat for NB02 through NB06
4. All intermediate data is saved to `data/`; figures to `figures/`

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory
