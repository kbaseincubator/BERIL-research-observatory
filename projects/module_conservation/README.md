# Fitness Modules x Pangenome Conservation

## Research Question

Are ICA fitness modules enriched in core pangenome genes, and do cross-organism module families map to the core genome?

## Status

Completed -- Module genes are 86% core (OR=1.46); 59% of modules are >90% core; family breadth does not predict conservation.

## Overview

This project connects ICA fitness modules (1,116 co-regulated gene modules across 32 bacteria) with pangenome conservation status to ask whether functionally coherent gene groups preferentially reside in the conserved core genome. It finds that module genes are enriched in core (+4.5pp over baseline), most modules are predominantly core, but module family breadth across organisms does not predict conservation -- a surprising null result explained by the high baseline core rate.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) -- Findings, interpretation, supporting evidence

## Reproduction

All analysis runs locally -- no Spark needed.

Requires data from:
- `projects/fitness_modules/data/modules/` and `data/module_families/`
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` and `essential_genes.tsv`

```bash
cd projects/module_conservation
jupyter nbconvert --execute notebooks/01_module_conservation.ipynb
jupyter nbconvert --execute notebooks/02_family_conservation.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
