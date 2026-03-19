# AMR Co-Fitness Support Networks

## Research Question

What genes are co-regulated with antimicrobial resistance (AMR) genes across growth conditions, and do these "support networks" explain the uniform fitness cost of resistance? Using cofitness data and ICA fitness modules from 25 bacteria, we identify the functional context in which AMR genes operate.

## Status

Complete — see [Report](REPORT.md) for findings. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (5 organisms, FDR<0.05). Networks are organism-specific (J=0.375) not mechanism-specific (J=0.207, p=4.3e-13). InterProScan GO annotations were critical — old SEED annotations produced a null result.

## Overview

The `amr_fitness_cost` project established that AMR genes impose a universal +0.086 fitness cost that is mechanism-independent. This follow-up asks *why* the cost is uniform: are AMR genes embedded in larger co-regulated networks whose functional composition explains the cost? We use pairwise cofitness correlations (13.6M pairs) and ICA-derived fitness modules (1,116 modules) to map the "support network" around each AMR gene — the genes whose fitness phenotypes track with resistance across hundreds of experimental conditions.

**BERDL collections**: `kescience_fitnessbrowser` (genefitness, gene), `kbase_ke_pangenome` (bakta_amr, bakta_annotations, interproscan_go, interproscan_domains)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

This project builds on data from:
- `amr_fitness_cost` (Dehal, 2026) — AMR gene catalog and fitness measurements
- `fitness_modules` (Dehal, 2026) — ICA modules, module families, fitness matrices
- `aromatic_catabolism_network` (Dehal, 2026) — methodological template for co-fitness network analysis

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, scipy, matplotlib, seaborn, statsmodels
- BERDL JupyterHub access (for InterProScan annotation extraction only)
- Prior projects checked out: `amr_fitness_cost`, `fitness_modules`, `conservation_vs_fitness`

**Pipeline:**
1. Execute `notebooks/01_data_assembly.ipynb` — cofitness computation from cached matrices (~60 min)
2. Execute `notebooks/02_amr_in_modules.ipynb` — ICA module analysis (~5 min)
3. Execute `notebooks/03_support_networks.ipynb` — old SEED enrichment (baseline, ~30 min)
4. Execute `notebooks/03b_enrichment_interproscan.ipynb` — InterProScan GO enrichment (~10 min, requires Spark for data extraction step)
5. Execute `notebooks/04_cross_organism_conservation.ipynb` — old KEGG conservation (baseline, ~5 min)
6. Execute `notebooks/04b_cross_organism_interproscan.ipynb` — InterProScan GO conservation (~5 min)

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
