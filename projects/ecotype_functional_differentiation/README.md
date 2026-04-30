# Ecotype Functional Differentiation

## Research Question
Do gene-content ecotypes within bacterial species differ in their COG functional profiles, showing differentiation in adaptive functions while sharing core metabolism?

## Status
Complete — see [Report](REPORT.md) for findings.

**Key result**: H1 partially supported. Adaptive COG categories (defense, transport, secondary metabolism) show 2.1x larger effect sizes between ecotypes than housekeeping categories (p = 2.53 x 10^-6), though both category types differentiate frequently. 12 of 15 species produced valid gene-content ecotypes (mean 3.7 ecotypes/species). Data: `kbase_ke_pangenome`.

## Overview
The `ecotype_analysis` project showed that within-species gene-content clusters (ecotypes) exist across 224 bacterial species, though their correlation with environment is weak. The `cog_analysis` project revealed a universal "two-speed genome" with novel genes enriched in mobile elements and defense. This project bridges those findings: do ecotypes defined by accessory gene content differ in *which* functional categories they carry? If defense (V), transport (P, G, E), and secondary metabolism (Q) differ between ecotypes while translation (J) and energy (C) are shared, it would demonstrate that within-species variation reflects functional ecological specialization, not random drift.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction

**Prerequisites**: BERDL JupyterHub access with Spark session (`berdl_notebook_utils`).

1. Run `notebooks/NB01_species_selection.ipynb` to generate `data/target_species.csv`
2. Run `python src/run_clustering.py` (requires Spark; ~66 min) to generate ecotype assignments and COG profiles
3. Run `notebooks/NB03_differential_enrichment.ipynb` for statistical tests and figures

## Authors
- Justin Reese (https://orcid.org/0000-0002-2170-2250), Lawrence Berkeley National Laboratory
