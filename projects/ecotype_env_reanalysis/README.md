# Ecotype Reanalysis: Environmental-Only Samples

## Research Question

Does the environment effect on gene content become stronger when analysis is restricted to genuinely environmental samples, excluding human-associated genomes whose AlphaEarth embeddings reflect hospital satellite imagery rather than ecological habitat?

## Status

Complete — H0 not rejected (p=0.83). Clinical bias does not explain the weak environment signal. See [Report](REPORT.md) for findings.

## Prior Work

This project extends two previous analyses:
- [Ecotype Correlation Analysis](../ecotype_analysis/) -- found that phylogeny dominates environment in predicting gene content (median partial correlation 0.003 for environment vs 0.014 for phylogeny, 172 species)
- [AlphaEarth Embedding Explorer](../env_embedding_explorer/) -- discovered that 38% of AlphaEarth genomes are human-associated, with 3.4x weaker geographic signal than environmental samples

## Overview

The original ecotype analysis tested whether environmental similarity (from AlphaEarth embeddings) predicts gene content similarity after controlling for phylogeny. It found weak effects for most species. However, we subsequently discovered that 38% of the genomes used had human-associated isolation sources (clinical, gut), and their AlphaEarth embeddings carry much weaker geographic signal because hospitals worldwide look similar from satellite imagery.

This project re-examines the ecotype question by classifying species according to their dominant isolation environment and comparing the environment–gene content correlation between environmental and human-associated species.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- hypothesis, approach, expected outcomes
- [Report](REPORT.md) -- findings and interpretation

## Data Sources

No new BERDL queries -- reuses data from parent projects:
- `ecotype_analysis/notebooks/02_ecotype_correlation_analysis.ipynb` -- partial correlation results (in notebook outputs)
- `env_embedding_explorer/data/alphaearth_with_env.csv` -- harmonized env_category per genome

## Structure

```
notebooks/
  01_environmental_only_reanalysis.ipynb  -- Main analysis (runs locally)
data/                                     -- Generated data
figures/                                  -- Visualizations
```

## Reproduction

### Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`
- Parent project data: `env_embedding_explorer/data/alphaearth_with_env.csv` must exist

### Steps
1. Run `notebooks/01_environmental_only_reanalysis.ipynb`

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
