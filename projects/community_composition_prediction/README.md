# community_composition_prediction

**Does high-dimensional microbial taxonomy (CLR-transformed genus RA) predict soil metal concentrations, and do genus-weighted functional features improve beyond composition alone?**

## Overview

This project uses CLR-transformed genus-level relative abundances (high-dimensional microbiome composition) plus genus-weighted per-megabase functional gene densities to predict soil metal concentrations (Cu, Zn, Pb, Ni).

Unlike `hybrid_metal_prediction` (which uses CWM — one scalar per functional category), this project preserves genus-level resolution in both the taxonomy (via CLR) and the functional features (via genus-weighted contributions). This tests whether genus identity carries predictive information beyond community-aggregate functional load.

**Genus-weighted functional features**: for each functional category k, the per-genus contribution is RA_g × density_gk. The top-N most-contributing genera per category are retained as features, plus PCA components of the full genus×category contribution matrix.

## Hypotheses

| Code | Hypothesis | Test |
|------|-----------|------|
| H1 | CLR taxonomy (B1) beats cheap geochem (B2) | ΔRMSE CI (B2 − B1), spatial block CV |
| H2 | Genus-weighted functional features improve beyond CLR+geochem (M1 vs B3) | ΔRMSE CI (B3 − M1) |
| H3 | Genus-weighted (M2) outperforms CWM (M3) | M2 vs M3 RMSE comparison (≥3 metals) |
| H4 | Genus-weighted functional categories rank above CLR taxonomy in SHAP | Sum GW SHAP > CLR SHAP (≥2 metals) |
| H5 | M2 generalises to AusMicrobiome holdout (RMSE ≤ 1.1× training) | Holdout/training RMSE ratio |

See `RESEARCH_PLAN.md` for success criteria and fallback criteria.

## Models

| Code | Description |
|------|-------------|
| B0 | Intercept-only (training mean) |
| B1 | CLR-transformed genus RA only (XGBoost) |
| B2 | pH + lat + lon only (ridge) |
| B3 | CLR + pH + lat/lon (XGBoost) |
| B4 | CWM only (XGBoost) |
| M1 | CLR + genus-weighted functional (XGBoost) |
| M2 | CLR + genus-weighted functional + env (XGBoost) |
| M3 | CLR + CWM + env (XGBoost) |

## Feature design

### CLR transformation
Standard centered log-ratio with uniform pseudocount (1e-6). Applied to top-200 genera by mean RA across training samples. Produces 200 `clr_{genus}` features.

### Genus-weighted functional features
For each of the 5 functional categories in `genus_trait_table.csv` (metal_clusters, defense_clusters, metabolism_clusters, homeostasis_clusters, metal_core_fraction):
- Compute RA_g × density_gk for each genus g (sample × genus contribution matrix)
- Retain top-20 genera by mean contribution → 5 × 20 = 100 `gw_{cat}_{genus}` features
- PCA of full genus×category contribution matrix → 10 `gw_pca_{i}` features
- Total GW features: 110

### Environmental features
Same 13 env features as `hybrid_metal_prediction`: ph, clay_pct, water_content, ndvi, elevation_m, temp_K, precip_mm, mob_cu, mob_pb, mob_as, mob_cd, mob_cr, mob_hg.

## Directory structure

```
community_composition_prediction/
├── data/
│   ├── genus_trait_table.csv         → symlink (comprehensive_metal_ecology)
│   ├── otu_pangenome_link_v2.csv     → symlink (microbeatlas_metal_ecology)
│   ├── 03_category_pgls_results.csv  → symlink (comprehensive_metal_ecology)
│   ├── hmp_feature_matrix.parquet    → symlink (hybrid_metal_prediction)
│   └── spatial_blocks.csv            → symlink (hybrid_metal_prediction)
├── scripts/
│   ├── composition_utils.py   # CLR transform, genus-weighted features, Spark OTU loader
│   ├── env_utils.py           → symlink (hybrid_metal_prediction)
│   ├── soilgrids_api.py       → symlink (hybrid_metal_prediction)
│   ├── cwm_utils.py           → symlink (hybrid_metal_prediction)
│   ├── modelling.py           # Model definitions, spatial CV
│   └── evaluation.py         # SHAP, threshold metrics, plots
├── notebooks/
│   ├── 00_feature_matrix.ipynb         # CLR + GW + env feature assembly
│   ├── 01_taxonomy_baseline.ipynb      # B0–B3 baselines + H1
│   ├── 02_functional_augmentation.ipynb # M1–M3 + H2/H3
│   ├── 03_external_validation.ipynb    # AusMicrobiome holdout + H5
│   └── 04_interpretation.ipynb         # SHAP + H4 + threshold metrics
├── figures/
├── README.md
├── RESEARCH_PLAN.md
└── INTERPRETATION_TABLE.md
```

## Notebooks

| NB | Title | Status | Key outputs |
|----|-------|--------|-------------|
| 00 | Feature matrix | **Complete (2026-07-07)** | 42,037 × 354 matrix (200 CLR + 110 GW + 44 base); `genus_ra.parquet` (42k × 2,781 genera) |
| 01 | Taxonomy baseline | **Complete (2026-07-07)** | H1 SUPPORTED (3/4): CLR beats geochem for Zn/Pb/Ni; B1 RMSE Cu/Zn/Pb/Ni = 1.136/0.707/0.954/1.830 |
| 02 | Functional augmentation | **Complete (2026-07-07)** | H2 SUPPORTED (4/4): GW beats B3; H3 NOT SUPPORTED (1/4): CWM beats GW for Zn/Pb/Ni |
| 03 | External validation | **Complete (2026-07-08)** | H5 SUPPORTED (2/4): Cu ratio=0.86 ✓, Ni ratio=0.97 ✓; Zn/Pb degrade; `data/holdout_results.csv` |
| 04 | Interpretation | **Complete (2026-07-08)** | H4 NOT SUPPORTED (0/4): env features dominate SHAP; CLR>GW for all metals; Pb threshold sensitivity=25% |
| 05 | Kriging-omics hybrid | **Complete (2026-07-08)** | H6 NOT SUPPORTED: hybrid worse than kriging alone; kriging beats M2 for 3/4 metals (spatial proximity > microbiome signal) |
| 06 | Bioavailable metal targets | **Complete (2026-07-08)** | H7 NOT SUPPORTED: CLR/GW degrade vs B0 for both mobility and total targets; M2_soil improves mob_cd/mob_hg (soil/climate, not microbiome, drives mobility) |
| 07 | Regional contamination classification | **Complete (2026-07-08)** | H8 NOT SUPPORTED: CLR alone achieves AUC≥0.99 within regions (no GW gain); cross-region collapses to 0.17; only 2 usable regions |
| 08 | Direct metagenomic profiles | **Untestable (2026-07-08)** | H9 UNTESTABLE: `arkinlab.spire` has only one table (`eggnog_annotations_spire`); mag_id is opaque (`spire_mag_XXXXXXXX`); no sample→MAG coverage table exists. Requires SPIRE data team to provide `sample_mag_coverage` table. |

## Evaluation

- **Primary metric**: RMSE on log1p-transformed metal concentrations (Cu, Zn, Pb, Ni)
- **CV strategy**: Spatial leave-one-block-out (k=5 geographic blocks, same blocks as `hybrid_metal_prediction`)
- **Hypothesis tests**: Bootstrap ΔRMSE 95% CI (n=1,000) for H1/H2; direct comparison for H3/H4
- **Holdout**: AusMicrobiome + NGSA (1,019 Australian soil samples)

## Relationship to other projects

| Project | Key difference |
|---------|---------------|
| `hybrid_metal_prediction` | Uses CWM (5 scalars); no genus-level taxonomy features; XGBoost |
| `comprehensive_metal_ecology` | PGLS + PERMANOVA on metal gene categories across biomes; no prediction |
| `community_composition_prediction` (this) | High-dimensional CLR + genus-weighted functional features; tests taxonomy vs function |

## Branch

`hrm-projects-v3`
