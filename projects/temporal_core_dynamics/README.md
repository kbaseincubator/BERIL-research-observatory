# Temporal Core Genome Dynamics

## Research Question

How does core genome composition change over sampling time, and do genes transition in and out of core status?

## Status

Proposed — Analysis pipeline designed for P. aeruginosa and A. baumannii; execution pending.

## Overview

This project investigates whether the core genome is static or dynamic over time by analyzing genomes with collection dates for two semi-environmental species (P. aeruginosa and A. baumannii). Using sliding window and cumulative expansion approaches across multiple core thresholds (90%, 95%, 99%), it tracks core erosion, gene turnover rates, and the functional enrichment of early-leaving genes to distinguish genuine population dynamics from sampling bias effects.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — Detailed hypothesis, approach, query strategy
- [Review](REVIEW.md) — Automated review (if submitted)

## Reproduction

**Prerequisites**: Run notebooks on the BERDL JupyterHub where Spark is available.

```bash
cd projects/temporal_core_dynamics/notebooks
jupyter notebook
```

Execute notebooks in order (01 -> 02 -> 03 -> 04). Each notebook saves intermediate results to `../data/`.

## Authors
- **Paramvir S. Dehal** (Lawrence Berkeley National Lab) | ORCID: 0000-0001-5810-2497 | Author
