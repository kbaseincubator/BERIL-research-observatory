# Web of Microbes Data Explorer

## Research Question
What does the `kescience_webofmicrobes` exometabolomics collection contain, which organisms overlap with the Fitness Browser, and how well do metabolite uptake/release profiles connect to pangenome-predicted metabolic capabilities?

## Status
Complete — see [Report](REPORT.md) for findings.

## Overview
Web of Microbes (WoM; Kosina et al. 2018, BMC Microbiology) is a curated exometabolomics database from the Northen lab at LBNL. It records which metabolites microorganisms consume (decrease) or produce (increase) when grown in defined environments. This project characterizes the BERDL-hosted copy (2018 archived snapshot): scale, organism coverage, metabolite composition, Fitness Browser overlap, and cross-collection linking potential to the pangenome and ModelSEED biochemistry.

## Data Sources
- `kescience_webofmicrobes` — 5 tables (compound, environment, organism, project, observation)
- `kescience_fitnessbrowser` — for cross-referencing FB organism overlap
- `kbase_ke_pangenome` — for GapMind pathway predictions
- `kbase_msd_biochemistry` — for metabolite-to-reaction mapping

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — analysis plan and context
- [Report](REPORT.md) — findings and interpretation
- [Notebooks](notebooks/) — exploratory analysis

## Reproduction

Notebooks must be run on the BERDL JupyterHub (requires `berdl_notebook_utils` for Spark access).

```
NB01 (database overview & FB overlap)
  └─► data/*.csv (organism profiles, metabolite summaries)
       └─► NB02 (cross-collection linking: GapMind, ModelSEED)
            └─► figures/ (metabolite heatmaps, overlap diagrams)
```

**Prerequisites**: Active Spark session on BERDL JupyterHub.

## Authors
Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
