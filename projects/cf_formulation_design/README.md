# CF Protective Microbiome Formulation Design

## Research Question

Can we build a multi-criterion framework that explains measured *P. aeruginosa* PA14 inhibition from metabolic competition, growth kinetics, and patient ecology data, and use it to design optimal 1–5 organism commensal formulations for competitive exclusion in CF lungs?

## Status

Complete — see [Report](REPORT.md) for findings. Eight notebooks executed, 23 figures generated, 13 data files produced. Key result: a 5-organism FDA-safe formulation (*N. mucosa* + *S. salivarius* + *M. luteus* + *R. dentocariosa* + *G. sanguinis*) achieves 100% PA14 niche coverage with 78% mean inhibition.

## Overview

This project integrates experimental data from the PROTECT CF Synbiotic Cocktail Study (4,949 isolates, 175 patient samples, planktonic inhibition assays, carbon source utilization, growth kinetics) with BERDL genomic resources (GapMind metabolic predictions, BacDive phenotypes, PhageFoundry pathogen genomes) to design and rank probiotic formulations that competitively exclude *P. aeruginosa* from CF airways.

The design theory is **metabolic competitive exclusion** — commensal organisms that consume the same carbon sources as PA14 (especially amino acids: proline, histidine, ornithine, glutamate, aspartate, arginine) can starve the pathogen. Formulations are optimized for complementary niche coverage, engraftability across patients, growth rate advantage, and FDA safety. Prebiotics that selectively feed the probiotics but not PA14 complete the synbiotic design.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, data sources, analysis plan
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

- **PROTECT Gold Tables** (`~/protect/gold/`): 23 tables, 30M rows — isolate catalog, inhibition scores, carbon utilization, growth curves, patient metagenomics, KEGG pathways
- **BERDL**: `protect_genomedepot`, `kbase_ke_pangenome` (GapMind), `phagefoundry_paeruginosa_genome_browser`, `kescience_bacdive`, `kbase_msd_biochemistry`

## Reproduction

### Prerequisites
- Python 3.10+, pandas, pyarrow, numpy, scipy, scikit-learn, matplotlib, seaborn
- BERDL access (KBASE_AUTH_TOKEN) for NB07 genomic extension
- Data files in `~/protect/gold/` (parquet format)

### Steps
1. Run notebooks in order: NB01 → NB02 → NB03 → NB04 → NB05 → NB06 → NB07
2. NB01–NB06 run locally from cached parquet files
3. NB07 requires BERDL Spark access for GapMind queries

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)) — U.C. Berkeley / Lawrence Berkeley National Laboratory
