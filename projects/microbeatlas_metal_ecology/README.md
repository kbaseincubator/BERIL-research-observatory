# Metal Resistance Ecology: Phylogenetic Conservation vs. Environmental Selection

## Research Question

Do metal-resistance functions in the global microbiome reflect phylogenetic constraint (conserved
in lineages) or environmental selection (enriched in metal-contaminated habitats)? We test this
using Pagel's λ to quantify phylogenetic signal, characterise whether metal-resistant lineages are
ecological generalists or specialists in a 464K-sample atlas, and use nitrification as a
metabolic-specialist positive control.

## Status

**Complete (core)** — see [Report](REPORT.md) for findings. NB01–NB06 executed; synthesis figures and REPORT.md generated. 2026-04-01: experimental validation framework added (candidate OTU list n=435, 8-OTU shortlist, ENIGMA field validation fully completed). 2026-06-30: chapters 07–11 appended to REPORT.md following project consolidation — COG-metal functional genomics (Ch.08), OTU-level GeoROC associations (Ch.09), global MAG biogeography (Ch.10a–c), biome-stratified Pagel's λ (Ch.10d), gene × biome enrichment (Ch.10e), and AlphaEarth embedding synthesis (Ch.11). NB08d (db-RDA) PENDING re-execution on Spark cluster after circular-predictor fix.

## Overview

Uses `arkinlab_microbeatlas` (98,919 OTUs, 464K samples) linked to `kbase_ke_pangenome`
(bakta_amr, GTDB taxonomy) via genus-level taxonomy matching. Analytical modules:

**Core (Ch.01–06)**
1. **Metal AMR extraction** (NB01, JupyterHub) — species-level metal resistance gene counts from AMRFinderPlus
2. **Niche breadth** (NB02, JupyterHub) — Levins' B from 260M OTU × sample observations
3. **Taxonomy bridge** (NB03, local) — OTU genus → GTDB species → metal AMR proxy
4. **Pagel's λ** (NB04, local) — phylogenetic signal of metal AMR per metal type
5. **Environmental selection test** (NB05, local) — niche breadth vs metal AMR, PGLS
6. **Figures** (NB06, local) — summary visualisations

**Extensions (Ch.07–11; consolidated 2026-06-30)**
7. **Environmental metadata PGLS** (NB07, local) — pH, temperature, organic carbon as PGLS covariates
8. **COG-metal functional genomics** (NB08a–d) — Spearman, BH-FDR, copper-specific, db-RDA across ~51K soil samples
9. **OTU-level GeoROC associations** (NB09a–b) — partial Spearman (CLR, 9,999 perms) between OTU abundance and measured soil metal concentrations
10. **Global MAG biogeography** (NB10a–c) — 260K MGnify MAGs; hotspot identification (Fisher's exact, 11 significant grid cells); biome stratification
11. **Biome-stratified Pagel's λ** (NB10d) — within-biome phylogenetic signal; all biomes λ=0.83–0.90
12. **Gene × biome enrichment** (NB10e) — seven focal genes (merA, arsC, silA, …) × five biomes; Fisher's exact + BH-FDR
13. **AlphaEarth embedding synthesis** (NB11c) — PERMANOVA of NCBI reference genome embeddings by hotspot label; PC12 dose-response

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [Report](REPORT.md)

**Core notebooks**
- [NB01 — Metal AMR extraction](notebooks/01_metal_amr_species.ipynb) *(JupyterHub)*
- [NB02 — Niche breadth](notebooks/02_niche_breadth.ipynb) *(JupyterHub)*
- [NB03 — Taxonomy bridge](notebooks/03_taxonomy_bridge.ipynb)
- [NB04 — Pagel's λ](notebooks/04_pagel_lambda.ipynb)
- [NB05 — PGLS regression](notebooks/05_pgls_regression.ipynb)
- [NB06 — Synthesis figures](notebooks/06_synthesis_figures.ipynb)
- [Supplementary — Clade-specific sensitivity](notebooks/clade_specific_sensitivity.ipynb) *(standalone; run after NB04)*

**Extension notebooks**
- [NB07 — Environmental metadata PGLS](notebooks/07_env_metadata_pgls.ipynb)
- [NB08a — COG-metal Spearman](notebooks/08a_spearman_cog_metal.ipynb)
- [NB08b — BH-FDR associations](notebooks/08b_fdr_associations.ipynb)
- [NB08c — Copper-specific analysis](notebooks/08c_copper_specific.ipynb)
- [NB08d — db-RDA PGLS](notebooks/08d_dbrda_pgls.ipynb) *(PENDING re-execution on Spark)*
- [NB09a — OTU × GeoROC associations](notebooks/09a_otu_georoc_associations.ipynb)
- [NB09b — OTU sensitivity](notebooks/09b_otu_sensitivity.ipynb)
- [NB10a — Global MAG distribution](notebooks/10a_global_mag_distribution.ipynb)
- [NB10b — Spatial hotspot analysis](notebooks/10b_spatial_analysis.ipynb)
- [NB10c — MAG figures](notebooks/10c_mag_figures.ipynb)
- [NB10d — Pagel's λ by biome](notebooks/10d_pagels_biome.ipynb)
- [NB10e — Gene × biome enrichment](notebooks/10e_gene_level_biome.ipynb)
- [NB11c — AlphaEarth embedding synthesis](notebooks/11c_alphaearth_metal_synthesis.ipynb)

**Reference**
- [R session info](sessionInfo_r.txt)
- [ENIGMA predictions](ENIGMA_PREDICTIONS.md)
- [Metal resistance table](METAL_RESISTANCE_TABLE.md)
- [Analysis notes](notes/)

## Data Sources

| Database | Tables | Access |
|---|---|---|
| `arkinlab_microbeatlas` | `otu_metadata`, `otu_counts_long`, `sample_metadata` | REST API + CLI Spark |
| `kbase_ke_pangenome` | `bakta_amr`, `gene_cluster`, `gtdb_species_clade` | JupyterHub Spark only |

## Reproduction

**Prerequisites**: JupyterHub Spark access for NB01–NB02; R 4.5.2 with `ape` and `phytools`
for NB04–NB05 (see `sessionInfo_r.txt`); Python ≥ 3.10 with packages in `requirements.txt`.

Run steps in this order:

**Core pipeline (Ch.01–06)**

| Step | Where | Command / Action | Output |
|---|---|---|---|
| 1. Metal AMR extraction | JupyterHub | Open and run `notebooks/01_metal_amr_species.ipynb` | `data/species_metal_amr.csv`, `data/gtdb_genus_taxonomy.csv` |
| 2. Niche breadth | JupyterHub | Open and run `notebooks/02_niche_breadth.ipynb` | `data/genus_niche_breadth.csv` |
| 3. Taxonomy bridge | Local | `jupyter nbconvert --to notebook --execute notebooks/03_taxonomy_bridge.ipynb` | `data/species_traits_for_pgls.csv` |
| 4. Pagel's λ | Local (R) | `Rscript scripts/h1_pagel_lambda_survivor.R` | `data/pagel_lambda_results.csv` |
| 5. PGLS regression | Local | `jupyter nbconvert --to notebook --execute notebooks/05_pgls_regression.ipynb` | `data/pgls_results.csv` |
| 6. Synthesis figures | Local | `jupyter nbconvert --to notebook --execute notebooks/06_synthesis_figures.ipynb` | `figures/fig_*` |
| 7. ENIGMA validation | Local | `python scripts/enigma_validation.py` | `figures/fig_enigma_validation_3panel.png` |

**Extension notebooks (Ch.07–11; all local unless noted)**

| Step | Notebook | Command / Action | Output |
|---|---|---|---|
| 8. Env metadata PGLS | NB07 | `jupyter nbconvert --execute notebooks/07_env_metadata_pgls.ipynb` | `data/env_pgls_results.csv` |
| 9. COG-metal Spearman | NB08a–c | `jupyter nbconvert --execute notebooks/08a_spearman_cog_metal.ipynb` etc. | `data/cog_metal_spearman.csv`, figures |
| 10. db-RDA (PENDING) | NB08d | Requires Spark cluster; fix `project_accession` SELECT + `sample_limit≥2000` | `data/dbrda_results.csv` |
| 11. OTU-GeoROC | NB09a–b | `jupyter nbconvert --execute notebooks/09a_otu_georoc_associations.ipynb` | `data/otu_georoc_*.csv`, figures |
| 12. MAG distribution | NB10a | `jupyter nbconvert --execute notebooks/10a_global_mag_distribution.ipynb` | `figures/nb10a_global_mag_distribution.png` |
| 13. Spatial hotspots | NB10b | `jupyter nbconvert --execute notebooks/10b_spatial_analysis.ipynb` | `data/hotspots_5grid.csv`, figures |
| 14. MAG figures | NB10c | `jupyter nbconvert --execute notebooks/10c_mag_figures.ipynb` | `figures/nb10c_*.png` |
| 15. Pagel by biome | NB10d | `jupyter nbconvert --execute notebooks/10d_pagels_biome.ipynb` (calls R via subprocess) | `data/pagel_lambda_by_biome.csv`, `figures/nb04d_*.png` |
| 16. Gene × biome | NB10e | `jupyter nbconvert --execute notebooks/10e_gene_level_biome.ipynb` | `data/gene_biome_enrichment.csv`, `figures/nb04e_*.png` |
| 17. AlphaEarth synthesis | NB11c | `jupyter nbconvert --execute notebooks/11c_alphaearth_metal_synthesis.ipynb` | `data/alphaearth_hotspot_comparison.csv`, `figures/nb11c_*.png` |

**Notes**:
- NB01–02 require `kbase_ke_pangenome` / `arkinlab_microbeatlas` access (JupyterHub only). Pre-computed outputs in `data/` allow local re-running from step 3 onward.
- NB04 calls R via `subprocess`; the notebook handles pre/post-processing.
- NB08d is PENDING: the circular-predictor bug (random project IDs) has been fixed in Cell 9 but the corrected version requires Spark cluster re-execution.
- NB10d calls `scripts/pagel_lambda_by_biome.R` (new wrapper, distinct from NB04's R script).
- Large files (`dir6_georoc_global_pca.csv` at 594 MB, some figures >100 MB) are excluded from git tracking. Zenodo DOI pending.
- `clade_specific_sensitivity.ipynb` is a standalone supplementary analysis (clade-specific Pagel's λ); run independently after step 4.

**Large files**: `data/dir6_georoc_global_pca.csv` (594 MB) and several figures exceed practical git file size limits. These are not tracked in the repository. A Zenodo deposit (DOI pending) will host derived data artifacts for long-term sharing. In the interim, regenerate them by re-running the relevant scripts in `scripts/dir6_*.py`.

## Authors

Heather MacGregor
