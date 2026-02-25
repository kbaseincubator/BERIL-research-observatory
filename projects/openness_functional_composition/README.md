# Openness vs Functional Composition

## Research Question

Do species with open pangenomes show different COG functional enrichment patterns than species with closed pangenomes?

## Hypothesis

- **H0**: COG enrichment patterns (core vs novel) are independent of pangenome openness
- **H1**: Open pangenomes show higher L (mobile element) and V (defense) enrichment in novel genes; closed pangenomes show higher metabolic diversity (E, C, G) in core genes

## Status

In Progress -- notebooks created, awaiting execution on BERDL JupyterHub.

## Overview

The `cog_analysis` project found a universal "two-speed genome" pattern: novel genes are enriched in mobile elements (L: +10.88%) and defense (V: +2.83%). This project tests whether that enrichment **scales with pangenome openness** -- do species that acquire more novel genes also show stronger L/V enrichment? This would link genome fluidity to functional specialization of the accessory genome.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [Report](REPORT.md) *(after analysis)*

## Notebooks

| Notebook | Purpose |
|----------|---------|
| [`01_openness_stratification.ipynb`](notebooks/01_openness_stratification.ipynb) | Extract pangenome stats, compute openness, stratify into quartiles |
| [`02_cog_enrichment_by_openness.ipynb`](notebooks/02_cog_enrichment_by_openness.ipynb) | COG enrichment analysis per openness quartile |
| [`03_statistical_analysis.ipynb`](notebooks/03_statistical_analysis.ipynb) | Statistical tests, phylogenetic controls, publication figures |

## Reproduction

1. Clone repo and checkout this branch
2. On BERDL JupyterHub, run notebooks 01-03 in order
3. Outputs saved to `data/` and `figures/`

## Authors

- **Justin Reese** (Lawrence Berkeley National Lab)
