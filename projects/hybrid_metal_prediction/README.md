# hybrid_metal_prediction

**Can community-weighted mean (CWM) omics features predict soil metal concentrations beyond cheap geochemistry alone?**

## Overview

This project tests whether microbiome-derived community-weighted mean (CWM) functional gene densities — derived from MicrobeAtlas OTU tables and BERDL pangenome databases — improve prediction of soil metal concentrations (Cu, Zn, Pb, Ni) beyond what cheap environmental covariates (pH, organic carbon, clay, CEC, bulk density, EC) explain on their own.

CWMs are computed as:

> CWM_category = Σ_genus (RA_genus × density_genus_category)

where RA is genus-level relative abundance from 16S data and density is per-Mb KO count from the BERDL pangenome database.

## Hypotheses

| Code | Hypothesis | Test |
|------|-----------|------|
| H1 | CWM features improve metal prediction beyond pH alone | ΔRMSE CI (M2 vs M1) |
| H2 | CWM features improve metal prediction beyond all cheap env | ΔRMSE CI (M2 vs M4) |
| H3 | Cofactor CWM is more predictive than resistance CWM | SHAP importance rank comparison |
| H4 | Predictive gain is largest for Cu and Ni (redox-active metals) | ΔRMSE by target metal |
| H5 | Geographic CV degrades CWM-rich models more than env-only models | RMSE ratio block-CV vs random-CV |
| H6 | CWM models transfer to independent holdout datasets (AusMicrobiome+NGSA, EMP, SPIRE) | Holdout RMSE vs naive baseline |

See `RESEARCH_PLAN.md` for success criteria and fallback criteria.

## Directory structure

```
hybrid_metal_prediction/
├── data/
│   ├── functional_landscape_results.csv  → symlink
│   ├── 03_category_pgls_results.csv      → symlink
│   ├── genus_trait_table.csv             → symlink
│   ├── otu_pangenome_link_v2.csv         → symlink
│   ├── 00_site_classification.csv        → symlink
│   └── soilgrids_cache.json              (generated at runtime)
├── scripts/
│   ├── cwm_utils.py         # CWM computation from OTU+density tables
│   ├── env_utils.py         # Environmental covariate extraction (Spark + SoilGrids)
│   ├── soilgrids_api.py     # SoilGrids REST API client with JSON cache
│   ├── spatial_utils.py     # Spatial block CV, haversine, kriging baseline
│   ├── modelling.py         # Model builders, nested spatial CV, conformal prediction
│   └── evaluation.py        # SHAP, PDP, threshold metrics, scatter plots
├── notebooks/
│   ├── 00_feature_matrix.ipynb           # CWM + env feature assembly
│   ├── 01_baselines_and_eda.ipynb        # EDA + baselines B0–B5
│   ├── 02_hybrid_models.ipynb            # Models M1–M5 with nested spatial CV
│   ├── 03_external_validation.ipynb      # Holdout evaluation (AusMicrobiome, EMP, SPIRE)
│   └── 04_interpretation_and_discovery.ipynb  # SHAP, PDP, discovery analyses
├── figures/
├── README.md
├── RESEARCH_PLAN.md
└── INTERPRETATION_TABLE.md
```

## Notebooks

| NB | Title | Status | Key outputs |
|----|-------|--------|-------------|
| 00 | Feature matrix | **Complete** (2026-07-07) | `data/feature_matrix.parquet` (42,037 × 44), coverage report, spatial_blocks.csv |
| 01 | Baselines and EDA | **Complete** (2026-07-07) | `data/baseline_results.csv`, EDA figures (eda_target_distributions.png, eda_feature_target_correlations.png, eda_spatial_blocks.png) |
| 02 | Hybrid models | **Complete** (2026-07-07) | `data/cv_results.csv`, `data/bootstrap_delta_rmse.csv`, `data/oof_predictions.parquet`, M2 scatter plots |
| 03 | External validation | **Complete** (2026-07-07) | `data/holdout_results.csv` (AusMicrobiome+NGSA B0/M2/M3/M4); EMP/SPIRE pending |
| 04 | Interpretation and discovery | **Complete** (2026-07-07) | `data/shap_importance.csv`, `data/threshold_metrics.csv`, 12+ figures |

## Data sources

| Dataset | Use | Join key |
|---------|-----|----------|
| `arkinlab.microbeatlas.otu_counts_long` | OTU relative abundances | sample_id, otu_id |
| `arkinlab.microbeatlas.otu_metadata` | OTU→genus bridge | otu_id |
| `arkinlab.microbeatlas.sample_metadata` | Lat/lon, pH, biome | sample_id |
| `arkinlab.microbeatlas.enriched_metadata` | Metal concentrations (GeoROC) | sample_id |
| `arkinlab.microbeatlas.enriched_metadata_gee` | OLM pH, EC (GEE) | sample_id |
| `arkinlab.envdbs.soilgrids` | Pre-computed SoilGrids (BERDL) | sample_id |
| `arkinlab.envdbs.csu_metal_mobility_grid` | CSU metal mobility indices (Cu, Zn, Pb, Ni) | sample_id |
| `genus_trait_table.csv` | Per-Mb KO density per category | genus_lower |
| `otu_pangenome_link_v2.csv` | OTU→genus bridge | otu_id |
| SoilGrids REST API | Holdout sample SoilGrids values | lat, lon |

## Targets

Log-transformed (log1p) metal concentrations from GeoROC columns in `enriched_metadata`:
- Cu_ppm, Zn_ppm, Pb_ppm, Ni_ppm

## Models

| Code | Description |
|------|-------------|
| B0 | Intercept-only (mean) |
| B1 | pH only (ridge) |
| B2 | All cheap env (ridge) |
| B3 | Lat/lon only (ridge) |
| B4 | pH only (XGBoost) |
| B5 | Ordinary kriging on lat/lon |
| M1 | pH + CWM (ridge) |
| M2 | All cheap env + CWM (XGBoost) |
| M3 | CWM only (XGBoost) |
| M4 | Env only (XGBoost) |
| M5 | Multi-output XGBoost (Cu, Zn, Pb, Ni jointly) |

## Evaluation

- **Primary metric**: RMSE on log-transformed targets
- **CV strategy**: Nested spatial leave-one-block-out (k=5 geographic blocks)
- **Uncertainty**: Conformal prediction intervals (split conformal, α=0.10)
- **Hypothesis tests**: Bootstrap ΔRMSE 95% CI (n=1,000)
- **Threshold metrics**: Sensitivity/specificity at regulatory thresholds (Cu >100 ppm, Zn >300 ppm, Pb >100 ppm, Ni >50 ppm)

## Branch

`hrm-projects-v3`
