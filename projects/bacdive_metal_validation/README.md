# BacDive Isolation Environment × Metal Tolerance Prediction

## Research Question
Do bacteria isolated from metal-contaminated environments have higher predicted metal tolerance scores than bacteria from uncontaminated environments?

## Status
Completed — heavy metal contamination isolates have significantly higher metal tolerance scores (d=+1.00, p=0.006). Signal is dose-dependent: heavy metal > waste > contamination > industrial. Holds within Pseudomonadota and Actinomycetota after phylogenetic stratification.

## Overview
The Metal Fitness Atlas scored 27,702 pangenome species for metal tolerance using a genome-based functional signature. This project validates those predictions against BacDive's isolation source metadata for 97K strains. By linking BacDive genome accessions to pangenome species, we test whether organisms from heavy-metal contamination sites, industrial environments, and waste/sludge sites have higher predicted metal tolerance than organisms from host-associated or uncontaminated environments.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- BacDive ingest data in `data/bacdive_ingest/`
- Metal atlas species scores in `projects/metal_fitness_atlas/data/`

### Running the Pipeline
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_bacdive_pangenome_bridge.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_environment_metal_scores.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_metal_utilization.ipynb
```

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
