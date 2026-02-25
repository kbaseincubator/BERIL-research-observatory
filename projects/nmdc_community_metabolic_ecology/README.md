# Community Metabolic Ecology via NMDC × Pangenome Integration

## Research Question

Do the GapMind-predicted pathway completeness profiles of community resident taxa predict or
correlate with observed metabolomics profiles in NMDC environmental samples across diverse
habitat types?

## Status

Complete — see [Report](REPORT.md) for findings.

All five notebooks have been executed (corrected run post-bug-fix). Key results:
BQH signal detected in leucine (r = −0.390, q = 0.022) and arginine (r = −0.297,
q = 0.049) biosynthesis; 11/13 (85%) tested aa pathways trend in BQH direction
(binomial p = 0.011). Community metabolic potential separates strongly by ecosystem
type (PC1 = 49.4% variance; Soil vs. Freshwater Mann-Whitney p < 0.0001).

## Overview

This project performs the first integration of NMDC multi-omics data with the BERDL pangenome
collection to test whether genome-predicted metabolic potential explains observed community
chemistry. For each NMDC sample with both taxonomic profiles and metabolomics measurements, we
compute a community-weighted GapMind pathway completeness score — the mean pathway
completeness across resident taxa weighted by their relative abundance — and test whether these
scores correlate with metabolomics profiles.

The central hypothesis is that **Black Queen dynamics are detectable at community scale**:
communities with more complete amino acid biosynthesis pathways will show lower ambient amino
acid concentrations, because those communities produce and internally consume amino acids
rather than importing them. A secondary test asks whether community metabolic potential
clusters by habitat type (soil, sediment, marine) more strongly than taxonomic composition
alone.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy, GapMind queries
- [Report](REPORT.md) — findings, interpretation, supporting evidence *(created by /synthesize)*

## Data Sources

| Collection | Tables | What it provides |
|---|---|---|
| `nmdc_arkin` | `taxonomy_features`, `kraken_gold`, `centrifuge_gold`, `metabolomics_gold`, `abiotic_features`, `study_table` | Community taxonomic profiles (6,365 samples), metabolomics (3.1M records), 48 studies |
| `kbase_ke_pangenome` | `gapmind_pathways`, `gtdb_species_clade`, `pangenome` | Per-species pathway completeness (305M rows), GTDB taxonomy bridge |

**Prior project data referenced** (via MinIO lakehouse, not copied):
- `projects/enigma_contamination_functional_potential` — taxonomy bridge methodology
- `projects/pangenome_pathway_geography` — GapMind two-stage aggregation query patterns
- `projects/essential_metabolome` — amino acid prototrophy baseline expectations

## Notebook Pipeline

| Notebook | Requires Spark | Description |
|---|---|---|
| `01_nmdc_exploration.ipynb` | Yes (JupyterHub) | NMDC schema exploration, sample inventory |
| `02_taxonomy_bridge.ipynb` | Yes (JupyterHub) | Map NMDC taxa to GTDB pangenome species |
| `03_pathway_completeness.ipynb` | Yes (JupyterHub) | Community-weighted GapMind completeness matrix |
| `04_metabolomics_processing.ipynb` | No (local) | Metabolomics normalization and merge |
| `05_statistical_analysis.ipynb` | No (local) | Correlation tests, BH-FDR, Black Queen signal |

## Reproduction

### Prerequisites

- Python ≥ 3.10 with packages from `requirements.txt`:
  ```
  pip install -r requirements.txt
  ```
- **NB01–NB04**: BERDL JupyterHub with `get_spark_session()` injected into the kernel
- **NB05**: Runs locally — no Spark required (reads cached CSVs from `data/`)

### Step-by-step

1. **NB01** `01_nmdc_exploration.ipynb` — Run on JupyterHub. ~5 min.
   Produces: `data/nmdc_sample_inventory.csv`, `data/nmdc_classifier_comparison.csv`

2. **NB02** `02_taxonomy_bridge.ipynb` — Run on JupyterHub. ~10 min.
   Produces: `data/taxon_bridge.tsv`, `data/bridge_quality.csv`, `data/nmdc_sample_inventory.csv` (updated with 221-sample bridge)

3. **NB03** `03_pathway_completeness.ipynb` — Run on JupyterHub. ~15–20 min (160M-row GapMind aggregation).
   Produces: `data/species_pathway_completeness.csv`, `data/community_pathway_matrix.csv`, `figures/pathway_completeness_heatmap.png`

4. **NB04** `04_metabolomics_processing.ipynb` — Run on JupyterHub or locally. ~5 min.
   Produces: `data/metabolomics_matrix.csv`, `data/amino_acid_metabolites.csv`, `data/analysis_ready_matrix.csv`

5. **NB05** `05_statistical_analysis.ipynb` — Run locally. ~1 min.
   Produces: `data/h1_bqh_correlations.csv`, `data/h2_pca_scores.csv`, `data/h2_pca_loadings.csv`, all `figures/`

Notebooks 01–03 require BERDL JupyterHub access (`get_spark_session()`).
Notebooks 04–05 run locally from cached CSV outputs.

## Authors

- **Christopher Neely** | ORCID: 0000-0002-2620-8948 | Author
