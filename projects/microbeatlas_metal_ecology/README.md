# Metal Resistance Ecology: Phylogenetic Conservation vs. Environmental Selection

## Research Question

Do metal-resistance functions in the global microbiome reflect phylogenetic constraint (conserved
in lineages) or environmental selection (enriched in metal-contaminated habitats)? We test this
using Pagel's λ to quantify phylogenetic signal, characterise whether metal-resistant lineages are
ecological generalists or specialists in a 464K-sample atlas, and use nitrification as a
metabolic-specialist positive control.

## Status

Complete — see [Report](REPORT.md) for findings. NB01–NB06 all executed; synthesis figures and REPORT.md generated. 2026-04-01: experimental validation framework added — candidate OTU list (n=435), refined metal resistance table, 8-OTU priority shortlist with testable hypotheses, feasibility assessment, and interactive dashboard. 2026-04-02: ENIGMA field validation fully completed — Track A (1,624 BERDL groundwater samples, ρ=+0.112, p=0.0019) and Track B (PRJNA1084851, 133 samples, 24,295 OTUs; CWM metal diversity significantly higher in contamination-plume wells and increases post-carbon amendment).

## Overview

Uses `arkinlab_microbeatlas` (98,919 OTUs, 464K samples) linked to `kbase_ke_pangenome`
(bakta_amr, GTDB taxonomy) via genus-level taxonomy matching. Four analytical modules:

1. **Metal AMR extraction** (NB01, JupyterHub) — species-level metal resistance gene counts from AMRFinderPlus
2. **Niche breadth** (NB02, JupyterHub) — Levins' B from 260M OTU × sample observations
3. **Taxonomy bridge** (NB03, local) — OTU genus → GTDB species → metal AMR proxy
4. **Pagel's λ** (NB04, local) — phylogenetic signal of metal AMR per metal type
5. **Environmental selection test** (NB05, local) — niche breadth vs metal AMR, PGLS
6. **Figures** (NB06, local) — summary visualisations

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [NB01 — Metal AMR extraction](notebooks/01_metal_amr_species.ipynb) *(run on JupyterHub)*
- [NB02 — Niche breadth](notebooks/02_niche_breadth.ipynb) *(run on JupyterHub)*
- [NB03 — Taxonomy bridge](notebooks/03_taxonomy_bridge.ipynb)
- [NB04 — Pagel's λ](notebooks/04_pagel_lambda.ipynb)
- [NB05 — PGLS regression](notebooks/05_pgls_regression.ipynb)
- [NB06 — Synthesis figures](notebooks/06_synthesis_figures.ipynb)
- [Supplementary — Clade-specific sensitivity](notebooks/clade_specific_sensitivity.ipynb) *(standalone; run after NB04)*
- [R session info](sessionInfo_r.txt)

## Data Sources

| Database | Tables | Access |
|---|---|---|
| `arkinlab_microbeatlas` | `otu_metadata`, `otu_counts_long`, `sample_metadata` | REST API + CLI Spark |
| `kbase_ke_pangenome` | `bakta_amr`, `gene_cluster`, `gtdb_species_clade` | JupyterHub Spark only |

## Reproduction

**Prerequisites**: JupyterHub Spark access for NB01–NB02; R 4.5.2 with `ape` and `phytools`
for NB04–NB05 (see `sessionInfo_r.txt`); Python ≥ 3.10 with packages in `requirements.txt`.

Run steps in this order:

| Step | Where | Command / Action | Output |
|---|---|---|---|
| 1. Metal AMR extraction | JupyterHub | Open and run `notebooks/01_metal_amr_species.ipynb` — connects to `kbase_ke_pangenome` via Spark | `data/species_metal_amr.csv`, `data/gtdb_genus_taxonomy.csv` |
| 2. Niche breadth | JupyterHub | Open and run `notebooks/02_niche_breadth.ipynb` — queries `arkinlab_microbeatlas` (260M rows) via CLI Spark | `data/genus_niche_breadth.csv` |
| 3. Taxonomy bridge | Local | `jupyter nbconvert --to notebook --execute notebooks/03_taxonomy_bridge.ipynb` | `data/species_traits_for_pgls.csv` |
| 4. Pagel's λ | Local (R) | `Rscript scripts/h1_pagel_lambda_survivor.R` | `data/pagel_lambda_results.csv` |
| 5. PGLS regression | Local | `jupyter nbconvert --to notebook --execute notebooks/05_pgls_regression.ipynb` | `data/pgls_results.csv`, console output |
| 6. Synthesis figures | Local | `jupyter nbconvert --to notebook --execute notebooks/06_synthesis_figures.ipynb` | `figures/fig_*` |
| 7. ENIGMA validation | Local | `python scripts/enigma_validation.py` | `figures/fig_enigma_validation_3panel.png` |

**Notes**:
- NB01 requires `kbase_ke_pangenome` access (JupyterHub only). Pre-computed outputs are in `data/` and local steps 3–7 can be run without re-running NB01–NB02.
- NB04 (Pagel's λ) is implemented as an R script called from within NB04 using `subprocess`; the notebook handles the Python pre/post-processing steps.
- Large files (`dir6_georoc_global_pca.csv` at 594 MB, some figures >100 MB) are present locally but excluded from git tracking. See the note below on large files.
- `clade_specific_sensitivity.ipynb` is a standalone supplementary analysis (clade-specific Pagel's λ); run it independently after step 4.

**Large files**: `data/dir6_georoc_global_pca.csv` (594 MB) and several figures exceed practical git file size limits. These are not tracked in the repository. A Zenodo deposit (DOI pending) will host derived data artifacts for long-term sharing. In the interim, regenerate them by re-running the relevant scripts in `scripts/dir6_*.py`.

## Authors

Heather MacGregor
