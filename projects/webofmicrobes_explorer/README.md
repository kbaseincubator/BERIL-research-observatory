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

Both notebooks require an active Spark session on the BERDL JupyterHub (`berdl_notebook_utils` for Spark/MinIO access). NB01 queries `kescience_webofmicrobes` and `kescience_fitnessbrowser`. NB02 additionally queries `kbase_msd_biochemistry` and `kbase_ke_pangenome`.

```
NB01 (database overview, FB overlap, heatmap)
  └─► data/*.csv + figures/enigma_metabolite_heatmap.png
       └─► NB02 (cross-collection linking: ModelSEED, GapMind, pangenome)
            └─► data/modelseed_*.csv
```

**Prerequisites**: Active Spark session on BERDL JupyterHub.

**Note**: The RESEARCH_PLAN described a third notebook (NB03: Metabolite Interaction Profiles) which was deferred. The absence of consumption data in this 2018 WoM snapshot made organism-comparison heatmaps less informative than planned — the data only records production, so cross-feeding analysis is not possible with this version.

## Authors
Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
