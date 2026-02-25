# Metabolic Consistency of Pseudomonas FW300-N2E3

## Research Question
For *Pseudomonas fluorescens* FW300-N2E3 (ENIGMA groundwater isolate), how consistent are exometabolomic outputs (Web of Microbes), genome-wide gene fitness (Fitness Browser), species-level utilization phenotypes (BacDive), and computational pathway predictions (GapMind)?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
FW300-N2E3 is one of very few organisms with data in all four major BERDL metabolic databases: Web of Microbes (58 metabolites produced on R2A), Fitness Browser (211 RB-TnSeq experiments including 82 carbon sources), BacDive (83 compounds tested for P. fluorescens), and the KE pangenome (GapMind pathways, eggNOG annotations). No published study has directly integrated exometabolomics with fitness data. This project triangulates across these databases to test whether they paint a coherent metabolic picture or reveal informative discordances (e.g., overflow metabolism, strain-vs-species differences, prediction gaps).

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- `kescience_webofmicrobes` — exometabolomic profile (Kosina et al. 2018)
- `kescience_fitnessbrowser` — RB-TnSeq fitness (Price et al. 2018)
- `kescience_bacdive` — metabolite utilization phenotypes (DSMZ)
- `kbase_ke_pangenome` — GapMind pathways, eggNOG annotations (GTDB r214)
- `kbase_msd_biochemistry` — ModelSEED reactions/compounds

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497))
- Claude (AI assistant, Anthropic)
