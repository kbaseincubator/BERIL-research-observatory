# Fitness Effects vs Conservation -- Quantitative Analysis

## Research Question

Is there a continuous gradient from essential genes (core) to dispensable genes (accessory) across the full fitness spectrum, and what does the fitness landscape of novel genes look like?

## Status

Completed -- 16pp fitness-conservation gradient established; core genes are more functionally active, not more inert.

## Overview

This project moves beyond the binary essential/non-essential classification to ask quantitative questions about how fitness importance relates to pangenome conservation. It reveals a clear gradient from essential genes (82% core) to always-neutral genes (66% core), shows that fitness breadth predicts conservation, and finds that core genes are MORE likely to be burdens and have condition-specific effects -- suggesting they are the most functionally active part of the genome.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) -- Findings, interpretation, supporting evidence

## Reproduction

**Prerequisites**: Python 3.10+, pandas, numpy, matplotlib, scipy. BERDL Spark Connect for data extraction.

1. **Extract fitness stats** (Spark): `python3 src/extract_fitness_stats.py`
2. **Run NB02** (local): `jupyter nbconvert --execute notebooks/02_fitness_vs_conservation.ipynb`
3. **Run NB03** (local): `jupyter nbconvert --execute notebooks/03_breadth_vs_conservation.ipynb`

Requires `conservation_vs_fitness` project data (link table, essential genes) at `../conservation_vs_fitness/data/`.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
