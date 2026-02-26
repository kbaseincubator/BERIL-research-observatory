# Metabolic Consistency of Pseudomonas FW300-N2E3

## Research Question
For *Pseudomonas fluorescens* FW300-N2E3 (ENIGMA groundwater isolate), how consistent are exometabolomic outputs (Web of Microbes), genome-wide gene fitness (Fitness Browser), species-level utilization phenotypes (BacDive), and computational pathway predictions (GapMind)?

## Status
Complete — three-notebook analysis finished. See [Report](REPORT.md) for findings. Key result: 94% mean concordance across databases, with tryptophan overflow metabolism as the strongest biologically meaningful discordance.

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

### Prerequisites
- Python 3.10+ with `pandas`, `numpy`, `matplotlib`
- BERDL Spark access via JupyterHub (for NB01 and NB02; NB03 runs from cached TSV files)
- On BERDL JupyterHub: `spark = get_spark_session()` is available in the notebook kernel without imports

### Steps
1. Run `01_data_extraction.ipynb` — extracts data from 4 BERDL databases, writes TSV files to `data/` (~30s, requires Spark)
2. Run `02_wom_fb_integration.ipynb` — queries gene fitness data, writes gene tables to `data/` (~15s, requires Spark)
3. Run `03_consistency_matrix.ipynb` — reads cached TSV files, computes concordance and permutation test, generates figures (~5s, no Spark needed)

All notebooks can be executed with papermill:
```bash
cd projects/fw300_metabolic_consistency/notebooks
papermill 01_data_extraction.ipynb 01_data_extraction.ipynb --kernel python3
papermill 02_wom_fb_integration.ipynb 02_wom_fb_integration.ipynb --kernel python3
papermill 03_consistency_matrix.ipynb 03_consistency_matrix.ipynb --kernel python3
```

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497))
- Claude (AI assistant, Anthropic)
