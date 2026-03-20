# Carbon Source Utilization Predicts Ecology and Lifestyle in Pseudomonas

## Research Question
Among free-living *Pseudomonas* clades, does the carbon source utilization profile predict the soil ecosystem type from which strains were isolated — and do clades that have transitioned to host-associated lifestyles show predictable losses of specific carbon pathways?

## Status
Complete — see [Report](REPORT.md) for findings.

## Overview
The *Pseudomonas* genus spans an extraordinary ecological range, from versatile soil saprophytes (*P. fluorescens*, *P. putida*) to chronic lung pathogens (*P. aeruginosa*). Using GapMind carbon pathway predictions for 12,727 genomes across 433 species clades, we test whether carbon utilization profiles are predictive of isolation environment among free-living clades, and whether host-associated clades show convergent loss of specific carbon pathways. The GTDB r214 classification splits the genus into subgenera (Pseudomonas sensu stricto vs Pseudomonas_E) that naturally capture the host-associated vs free-living divide, providing a phylogenetic framework for the comparison.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- **BERDL pangenome**: 433 Pseudomonas species clades, 12,727 genomes (`kbase_ke_pangenome`)
- **GapMind pathways**: 62 carbon source utilization pathways per genome
- **NCBI environment metadata**: Isolation source for 67% of genomes

## Reproduction

### Prerequisites
- Access to BERDL JupyterHub (for NB01 — Spark SQL queries)
- Python 3.10+ with packages in `requirements.txt`

### Steps
1. Run `01_data_extraction.ipynb` on BERDL JupyterHub to extract data from `kbase_ke_pangenome`
2. Run `02_environment_harmonization.ipynb` locally to classify isolation sources
3. Run `03_pathway_lifestyle_analysis.ipynb` locally to test pathway differences between subgenera
4. Run `04_ecology_prediction.ipynb` locally to test environment prediction from pathway profiles

## Authors
- Mar Andrew Miller ([ORCID: 0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066))
