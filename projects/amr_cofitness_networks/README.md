# AMR Co-Fitness Support Networks

## Research Question

What genes are co-regulated with antimicrobial resistance (AMR) genes across growth conditions, and do these "support networks" explain the uniform fitness cost of resistance? Using cofitness data and ICA fitness modules from 25 bacteria, we identify the functional context in which AMR genes operate.

## Status

In Progress — research plan created.

## Overview

The `amr_fitness_cost` project established that AMR genes impose a universal +0.086 fitness cost that is mechanism-independent. This follow-up asks *why* the cost is uniform: are AMR genes embedded in larger co-regulated networks whose functional composition explains the cost? We use pairwise cofitness correlations (13.6M pairs) and ICA-derived fitness modules (1,116 modules) to map the "support network" around each AMR gene — the genes whose fitness phenotypes track with resistance across hundreds of experimental conditions.

**BERDL collections**: `kescience_fitnessbrowser` (cofit, genefitness, gene, ortholog), `kbase_ke_pangenome` (bakta_amr, bakta_annotations)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

This project builds on data from:
- `amr_fitness_cost` (Dehal, 2026) — AMR gene catalog and fitness measurements
- `fitness_modules` (Dehal, 2026) — ICA modules, module families, fitness matrices
- `aromatic_catabolism_network` (Dehal, 2026) — methodological template for co-fitness network analysis

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
