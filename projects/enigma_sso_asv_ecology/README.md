# SSO Subsurface Community Ecology — Spatial Structure, Functional Gradients, and Hydrogeological Drivers

## Research Question

Does 16S community similarity across the 9 ENIGMA SSO wells (3x3 grid, ~4 m span at Oak Ridge) recapitulate the spatial arrangement in X, Y, and Z? Where it deviates, can hydrogeological connectivity or environmental gradients explain the pattern? Can we infer functional differences from taxonomy and what they imply about subsurface environmental parameters?

## Status

Complete — see [Report](REPORT.md) for findings.

## Overview

The ENIGMA Subsurface Science Observatory (SSO) at Oak Ridge Reservation Area 3 consists of 9 boreholes in a 3×3 grid (Upper: U1-U3, Middle: M4-M6, Lower: L7-L9) spanning ~6 meters. The SSO sits downhill and southwest of a contamination source delivering high nitrate, low pH, and heavy metals. Each borehole was cored through the vadose zone into saturated rock, yielding depth-resolved 16S amplicon profiles of sediment-associated and groundwater microbial communities.

We find that community similarity tracks the contamination plume rather than hillslope topography. A diagonal corridor of wells (U3-M6-L7) shares community composition along the inferred plume flow path from NE to SW. Depth dominates community structure (PERMANOVA R²=27.5%, p=0.0001), consistent with the plume traveling through the saturated zone. Genus-level functional inference maps the thermodynamic redox ladder (denitrification → iron reduction → fermentation) onto the physical grid, with *Rhodanobacter* denitrification peaking at M5 — the plume mixing zone. Groundwater carries a distinct plume-associated planktonic community enriched in denitrifiers and iron oxidizers.

### Data Collections
- `enigma_coral` — ENIGMA CORAL SSO 16S ASV data, sample metadata, well coordinates

### Data Sources
- **Sediment 16S ASV**: 37 samples across all 9 wells, depths 1.7-9.3 m (Feb-Mar 2023)
- **Groundwater 16S ASV**: 40 samples across 5 wells, 2 depths (Sep 2024)
- **Pump test ASV**: 14 communities from 3 wells (Mar 2024) — available but not yet extracted
- **Well metadata**: Lat/lon, depth, lithological zone, collection date

### Key Constraints
- No geochemistry in BERDL (samples registered, measurements not loaded)
- Species-level taxonomy unavailable (genus best at 35-63%)
- Groundwater covers only 5/9 wells

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction

### Prerequisites
- Python 3.10+
- BERDL access (JupyterHub) for NB01 Spark cells (sections 5-6)
- Packages: see `requirements.txt`

### Notebooks
| Notebook | Spark? | Purpose |
|----------|--------|---------|
| `01_data_integration.ipynb` | Sections 5-6 | Load ASV data, compute well geometry, assign zones, build community matrices |
| `02_sediment_spatial.ipynb` | No | Bray-Curtis, Mantel test, NMDS, Procrustes, residual analysis |
| `03_depth_zonation.ipynb` | No | PERMANOVA (zone vs well), indicator taxa, depth correlations |
| `04_functional_inference.ipynb` | No | Multi-resolution trait mapping (class + genus level), spatial gradients |
| `05_gw_vs_sediment.ipynb` | No | Groundwater vs sediment comparison, plume indicator genera |
| `06_synthesis.ipynb` | No | Contamination plume model, evidence integration |
| `07_hotspot_interactions.ipynb` | No | Well-by-well community profiles, metabolic guilds, co-occurrence |
| `08_temporal_stability.ipynb` | No | GW temporal stability (9-day), filter size effects, variance partitioning |

### Steps
1. **NB01** (requires Spark for sections 5-6): Extract and integrate ASV data → `data/` outputs. Sections 1-4 run locally from pre-extracted parquets.
2. **NB02-NB08** (local): Run sequentially; each reads from `data/` produced by prior notebooks.
3. Execute with saved outputs: `jupyter nbconvert --to notebook --execute --inplace notebooks/<notebook>.ipynb`

## Authors
- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory
