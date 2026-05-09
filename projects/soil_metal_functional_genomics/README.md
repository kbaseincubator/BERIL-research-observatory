# Soil Metal Concentrations Drive Functional Gene Shifts in the Environmental Microbiome

## Research Question

Which microbial functional gene categories (COGs) are significantly associated with soil
metal concentrations at global scale, and do these associations reflect metabolic adaptation,
resistance, or passive environmental filtering?

## Status

**Active** — Large-scale Spearman correlation analysis complete. db-RDA and PGLS
multivariate models complete. Manuscript figures pending.

Initiated: 2026-05-02. Source notebooks: `projects/misc_exploratory/exploratory/`.

## Key Findings (Preliminary)

- **2,355 significant COG-metal associations** (FDR < 0.05) across 9 metals (Cu, Co,
  Cr, Ni, Zn, Pb, As, Cd, Hg) in the primary analysis (51,748 soil samples).
- **Chromium and Lead** drive the strongest signals; transporters (ABC, RND) and
  biosynthesis genes dominate the top associations.
- **Copper-specific analysis** (Untitled1): 116 COG categories significantly correlated
  with Cu (FDR < 0.05); top positives include cell division and nucleotide transport
  (BQ, FQ, FK, CF); top negatives include energy production (DI, CE) suggesting
  energetic trade-offs under copper stress.
- **db-RDA** (Untitled3): R² = 0.799, p = 0.005 (permutation test) — metal
  concentrations explain 80% of variance in community COG profiles after conditioning
  on batch/project effects.
- **Biome-stratified PGLS** (Untitled3): soil, marine, and wastewater show distinct
  metal-COG relationships, indicating environment-specific functional responses.

## Notebooks Consolidated

This project merges analyses from four source notebooks that address the same question
at different scales and with different statistical approaches:

| NB | Source Notebook | Status | Description |
|---|---|---|---|
| NB01 | `Soil_Metals_vs_Microbial_COG_Functions.ipynb` | ✅ Done | 51,748 samples; 9 metals; 435 COG categories; community-weighted Spearman; 2,355 significant associations |
| NB02 | `Soil_Metals_Microbiome_COG_Functions_v1.ipynb` | ✅ Done | Earlier iteration; order-level taxonomic matching; Cr, Cu, Pb as top drivers |
| NB03 | `Untitled1.ipynb` | ✅ Done | Copper-specific analysis; 116 significant COGs; 7,566 samples with nearby KBase genomes (10 km) |
| NB04 | `Untitled3.ipynb` | ✅ Done | db-RDA (R²=0.799, p=0.005); biome-stratified PGLS; HGT network integration; rRNA copy number control |
| NB05 | `notebooks/05_validation.ipynb` | 🔲 Todo | Effect size reporting; spatial autocorrelation test; single-metal vs. multi-metal models |
| NB06 | `notebooks/06_figures.ipynb` | 🔲 Todo | Manuscript figures |

### NB05 — Validation Analyses

1. **Effect size audit**
   — The 2,355 significant associations were identified via FDR < 0.05, but effect sizes
   (Spearman ρ) are not yet systematically reported. Compute ρ distribution; report
   median and 90th percentile. Associations with ρ < 0.05 should be flagged as
   statistically but not biologically significant.

2. **Spatial autocorrelation control**
   — Soil samples within the same region share geology and land use. Test for spatial
   autocorrelation in COG-metal associations using Moran's I on residuals. If significant,
   apply spatial eigenvector filtering (SEVM) to the Spearman analysis.

3. **Multi-metal vs. single-metal model**
   — Are COG associations metal-specific or driven by co-contamination? Fit a partial
   correlation model: COG ~ Cr | Cu + Zn + Pb. Identify COGs with metal-specific
   associations vs. those responding to any metal stress.

4. **Mechanistic classification**
   — Classify each significant COG into: (a) known metal resistance (e.g., CzcA,
   MerR family), (b) oxidative stress response, (c) membrane remodelling, (d) energy
   metabolism, (e) unknown. Provides biological interpretation beyond the correlation.

## Reproduction

**Prerequisites**: JupyterHub Spark access for NB01–NB04; Python ≥ 3.10 with packages
in `requirements.txt`; R ≥ 4.0 with `vegan`, `ape`, `nlme` for PGLS steps in NB04.

| Step | Where | Command / Action | Output |
|---|---|---|---|
| 1. Spearman COG-metal correlations | JupyterHub | Run `notebooks/01_spearman_cog_metal.ipynb` — queries `arkinlab_microbeatlas` via Spark; 51,748 samples | Spearman ρ table, FDR values |
| 2. FDR associations (earlier iteration) | JupyterHub | Run `notebooks/02_fdr_associations.ipynb` | Order-level summary; Cr, Cu, Pb drivers |
| 3. Copper-specific analysis | JupyterHub | Run `notebooks/03_copper_specific.ipynb` — 7,566 samples with nearby genomes (10 km) | 116 significant COGs |
| 4. db-RDA and PGLS | JupyterHub | Run `notebooks/04_dbrda_pgls.ipynb` — `vegan::capscale` conditioned on project accession; biome-stratified PGLS | R²=0.799 (conditional); PGLS coefficients |
| 5. Validation | Local | `jupyter nbconvert --to notebook --execute notebooks/05_validation.ipynb` | Effect size distribution; Moran's I |
| 6. Figures | Local | `jupyter nbconvert --to notebook --execute notebooks/06_figures.ipynb` | `figures/fig_*` |

**Notes**:
- NB01–NB04 require JupyterHub Spark. Export intermediate Spearman ρ values and
  model residuals to `data/` CSVs so NB05–NB06 can run locally without re-querying.
- **PGLS row-ordering (NB04)**: before calling `gls(..., correlation=corPagel(...))`,
  confirm data rows are sorted to match `tree$tip.label`. Add
  `dat <- dat[tree_sub$tip.label, ]` immediately after `keep.tip()`. A silent
  misalignment produces wrong λ estimates with no error (see `docs/pitfalls.md`).
- The db-RDA R²=0.799 is conditional on project accession. The unconditional R²
  (metals alone, without conditioning) has not yet been computed — run
  `vegan::capscale(COG_matrix ~ metals, data=df)` without the conditioning term
  and report alongside the conditional figure.
- NB05 and NB06 are planned but not yet implemented.

## Data Sources

| Database | Tables Used | Access |
|---|---|---|
| BERIL Observatory | 16S OTU counts, soil sample metadata, geochemistry | REST API + local CSVs |
| `kbase_ke_pangenome` | COG annotations (bakta), GTDB taxonomy | JupyterHub Spark |
| GeoROC | Rock geochemical compositions (metal concentrations) | Local CSV |

## Source Data

```
misc_exploratory/exploratory/data/
  mgnify_geochemistry_mags.csv
  mgnify_mag_metal_traits.csv
```

## Relationship to Other Projects

| Project | Relationship |
|---|---|
| `microbeatlas_metal_ecology` | That project tests OTU diversity vs. mine proximity; this project tests functional gene content vs. soil metal concentrations — mechanistically complementary |
| `metal_diversity_niche_breadth` | Functional gene shifts (this project) may explain the niche breadth signal (that project) |

## Authors

Heather MacGregor
