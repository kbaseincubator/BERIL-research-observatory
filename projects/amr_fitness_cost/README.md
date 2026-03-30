# Fitness Cost of Antimicrobial Resistance Genes

## Research Question

Do antimicrobial resistance (AMR) genes impose a fitness cost in the absence of antibiotic selection pressure? Using genome-wide RB-TnSeq fitness data from 28 bacteria, we test whether transposon knockouts of AMR genes show systematically positive fitness (mutant grows better than wildtype) under standard growth conditions, indicating the intact AMR gene is a metabolic burden.

## Status

Complete — see [Report](REPORT.md) for findings. AMR genes impose a universal +0.086 fitness cost across 25 organisms (25/25 positive, p ~ 0). Cost is mechanism-independent but antibiotic importance is mechanism-dependent (efflux > enzymatic, p = 0.007).

## Overview

This project combines three BERDL data assets to test the "cost of resistance" hypothesis at pangenome scale:
- **bakta_amr** (83K AMR gene clusters) identifies resistance genes across 132.5M pangenome clusters
- **Fitness Browser** (48 organisms, 27M fitness measurements) provides genome-wide transposon fitness data
- **fb_pangenome_link** (177K gene-to-cluster links) bridges fitness browser genes to pangenome clusters

We identify 1,352 AMR genes across 28 organisms with fitness data, compute their fitness under non-antibiotic conditions, and compare to non-AMR background using a random-effects meta-analysis. Validation uses antibiotic experiments as positive controls.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy, statistical methods
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

**BERDL collections**: `kbase_ke_pangenome` (bakta_amr, bakta_annotations), `kescience_fitnessbrowser` (genefitness, gene, experiment)

**Cross-project data from**:
- `conservation_vs_fitness` (Dehal, 2026) — FB-pangenome link table
- `fitness_modules` (Dehal, 2026) — cached fitness matrices and experiment metadata
- `essential_genome` (Dehal, 2026) — SEED annotations

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, scipy, matplotlib, seaborn
- BERDL JupyterHub access (for Spark queries in src/extract_amr_data.py)

**Pipeline:**
1. `python src/extract_amr_data.py` — extract bakta_amr data for FB-linked clusters (requires Spark)
2. Execute `notebooks/01_data_assembly.ipynb` — AMR gene identification + experiment classification
3. Execute `notebooks/02_fitness_cost_analysis.ipynb` — core fitness cost analysis + exploratory QC
4. **Checkpoint**: review NB02 results before proceeding
5. Execute `notebooks/03_antibiotic_validation.ipynb` — positive control validation
6. Execute `notebooks/04_stratification.ipynb` — stratification by class, conservation, organism
7. Execute `notebooks/04b_followup_analyses.ipynb` — mechanism × conservation interaction, narrow vs broad spectrum validation

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
