# Core Gene Paradox -- Why Are Core Genes More Burdensome?

## Research Question

Why are core genome genes MORE likely to show positive fitness effects when deleted, and what functions and conditions drive this burden paradox?

## Status

Completed -- Burden paradox dissected by function; trade-off genes 1.29x enriched in core; 28,017 genes identified under purifying selection.

## Overview

This project dissects why core genes are more burdensome than accessory genes -- a finding from `fitness_effects_conservation` that contradicts the "streamlining" model. It reveals that the paradox is function-specific (driven by motility, RNA metabolism, protein metabolism), that trade-off genes (important in some conditions, costly in others) are enriched in core, and constructs a selection-signature matrix identifying genes under purifying selection in natural environments.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) -- Findings, interpretation, supporting evidence

## Reproduction

All local -- no Spark needed. Requires data from `fitness_effects_conservation` and `conservation_vs_fitness` projects.

```bash
cd projects/core_gene_tradeoffs
jupyter nbconvert --execute notebooks/01_burden_anatomy.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
