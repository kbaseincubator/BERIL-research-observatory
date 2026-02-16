# AlphaEarth Embeddings, Geography & Environment Explorer

## Research Question

What do AlphaEarth environmental embeddings capture, and how do they relate to geographic coordinates and NCBI environment labels?

## Status

Complete -- environmental samples show 3.4x stronger geographic signal in AlphaEarth embeddings than human-associated samples. See [Report](REPORT.md) for full findings.

## Overview

The BERDL pangenome database includes 64-dimensional AlphaEarth environmental embeddings derived from satellite imagery for 83,287 genomes (28.4% of 293K total). These embeddings encode environmental context at each genome's sampling location, but their structure and relationship to traditional environment metadata have not been characterized.

This exploratory project asks:
1. What structure exists in the embedding space? Do clusters correspond to known environment types?
2. How trustworthy are the lat/lon coordinates? Do some refer to institutions rather than sampling sites?
3. How do NCBI environment labels (free-text `isolation_source`, ENVO terms) map onto embedding clusters?
4. Does geographic proximity predict embedding similarity?

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- questions, approach, data sources
- [Report](REPORT.md) -- findings and interpretation

## Data Sources

- `kbase_ke_pangenome.alphaearth_embeddings_all_years` -- 83,287 genomes, 64-dim embeddings + cleaned lat/lon
- `kbase_ke_pangenome.ncbi_env` -- 4.1M rows, EAV-format environment metadata
- `kbase_ke_pangenome.gtdb_metadata` -- genome quality and assembly metadata

## Structure

```
notebooks/
  01_data_extraction.ipynb       -- Spark: extract embeddings + env labels (JupyterHub)
  02_interactive_exploration.ipynb -- plotly: UMAP, maps, QC, harmonization (local or JupyterHub)
data/                            -- Extracted CSVs
figures/                         -- Saved visualizations
```

## Reproduction

### Prerequisites
- Python 3.10+
- BERDL JupyterHub access (for NB01)
- `pip install -r requirements.txt` (for NB02)

### Steps
1. Upload `notebooks/01_data_extraction.ipynb` to BERDL JupyterHub
2. Run all cells -- outputs go to `data/`
3. Download `data/*.csv` to local machine
4. Run `notebooks/02_interactive_exploration.ipynb` locally (or on JupyterHub)

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
