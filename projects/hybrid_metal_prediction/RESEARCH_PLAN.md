# Research Plan: Hybrid Metal Prediction

## Core question

Do community-weighted mean (CWM) omics features improve prediction of soil metal concentrations beyond cheap environmental covariates alone?

---

## Pre-specified hypotheses and success criteria

### H1 — CWM improves prediction beyond pH alone

**Comparison**: M1 (pH + CWM ridge) vs B1 (pH only ridge)  
**Test**: Bootstrap ΔRMSE CI (1,000 samples)  
**Success**: ΔRMSE(B1 − M1) CI excludes 0 in the positive direction for ≥2 of 4 target metals  
**Fallback**: If ΔRMSE CI overlaps 0, report conditional: CWM adds nothing once pH is known  
**Interpretation**: pH is the dominant driver of metal solubility; CWM adds information only if the microbial community encodes metal load beyond what pH alone captures

---

### H2 — CWM improves prediction beyond all cheap env

**Comparison**: M2 (env + CWM, XGBoost) vs M4 (env only, XGBoost)  
**Test**: Bootstrap ΔRMSE CI  
**Success**: ΔRMSE(M4 − M2) CI excludes 0 in the positive direction for ≥2 of 4 metals  
**Fallback**: If ΔRMSE overlaps 0, report that microbiome adds no predictive signal above geochemistry; proceed with discovery analysis for secondary insights  
**Interpretation**: If H2 fails, the community tracks geochemistry rather than independently predicting it (which is also a finding)

---

### H3 — Cofactor CWM is more predictive than resistance CWM

**Comparison**: SHAP importance of CWM_cofactor vs CWM_resistance in M2  
**Test**: SHAP importance rank; t-test on |SHAP values| (cofactor vs resistance features)  
**Success**: CWM_cofactor ranks higher than CWM_resistance in M2 SHAP for ≥3 of 4 metals  
**Interpretation**: Consistent with comprehensive_metal_ecology finding that cofactor biosynthesis signal is stronger than resistance signal; extends that finding from PGLS to ML prediction

---

### H4 — Predictive gain largest for Cu and Ni (redox-active metals)

**Comparison**: Rank ΔRMSE(M4 − M2) by target metal  
**Test**: Visual rank comparison (no formal test pre-specified; too many comparisons)  
**Success**: Cu and Ni show largest ΔRMSE among the 4 targets  
**Rationale**: Cu and Ni are primary cofactors in redox enzymes; cofactor biosynthesis genes should be most predictive for metals that are constitutively incorporated vs. transiently toxic

---

### H5 — Geographic CV degrades CWM-rich models more than env-only models

**Comparison**: RMSE ratio (block-CV / random-5-fold) for M2 vs M4  
**Test**: Compare degradation ratios  
**Success**: M2 degradation ratio > M4 degradation ratio by >10%  
**Interpretation**: CWM features track local microbial communities that are geographically structured; environmental features are less spatially autocorrelated and therefore degrade less under geographic holdout

---

### H6 — CWM models transfer to independent holdout datasets

**Holdout sets**:
1. AusMicrobiome + NGSA (Australian soils, independent 16S + metal data)
2. EMP (Earth Microbiome Project, global subset with metal annotations)
3. SPIRE (SPIRE soil microbiome compendium)

**Test**: Compare holdout RMSE of M2 vs B0 (intercept-only) and M4 (env-only)  
**Success**: M2 holdout RMSE ≤ 1.1× M4 holdout RMSE (M2 does not catastrophically degrade vs. env-only)  
**Fallback**: If M2 degrades badly, evaluate whether CWM coverage fraction explains the degradation

---

## Analysis plan by notebook

### NB00: Feature matrix — **COMPLETE (2026-07-07)**

**Coverage summary (actual)**:
- Soil samples with lat/lon: 261,803
- GEE env features (OLM pH, clay, water content, NDVI, elevation, temp, precip): 217,662 samples
- CSU mobility features (mob_cu, mob_pb, mob_as, mob_cd, mob_cr, mob_hg): 220,296 / 261,803 matched
- GeoROC spatial join (50 km radius): 43,081 samples with ≥1 geochemical match
- CWM matrix: 42,037 samples × 2,781 genera → 5 CWM features; 0 low-coverage samples
- **Final feature matrix: 42,037 samples × 44 columns**
- pH source: olm=30,105, insitu=6,588, missing=5,344
- 5 geographic blocks (k-means): N. America (n=15,630), Africa/Middle East (n=11,649), Europe (n=8,374), China (n=5,204), Australia/S. Pacific (n=1,180)

**Per-target sample counts**:
- log_Cu_ppm: 34,613 | log_Zn_ppm: 37,283 | log_Pb_ppm: 36,381
- log_Ni_ppm: 39,211 | log_Co_ppm: 32,508 | log_Cr_ppm: 34,322 | log_As_ppm: 6,303

**Data gaps**: log_As_ppm (15% coverage), ph_insitu (16%), log_Co_ppm (77%)

**Steps run**:
1. Filter sample_metadata by soil/terrestrial/rhizosphere/sediment Environments keywords
2. GEE covariates via Sample_ID_Matched join (OLM pH ÷ 10, clay, water content, NDVI, elevation, temp, precip)
3. CSU mobility grid: binned hash join at 0.09° resolution from `arkinlab.envdbs.csu_metal_mobility_grid`
4. GeoROC metal targets: spatial join (50 km haversine, pre-filtered by 0.5° bins) with `enriched_metadata`
5. Genus RA from Spark → CWM via matrix multiply with `genus_trait_table.csv` (5 density columns)
6. Assembled feature matrix, 5 geographic blocks via k-means on lat/lon
7. Saved `feature_matrix.parquet`, `spatial_blocks.csv`, `coverage_report.csv`

### NB01: Baselines and EDA — **COMPLETE (2026-07-07)**

B0=1.131/0.711/0.889/1.769, B1=1.198/0.621/0.962/1.880 (Cu/Zn/Pb/Ni). B5 skipped (no pykrige). B0 beats B1 for Cu/Pb/Ni due to geographic block holdout variance. B2 worst (NaN row-dropping reduces training set). Outputs: `data/baseline_results.csv`, EDA figures.

1. EDA: distributions of targets, covariates, CWM features; bivariate correlations
2. Spatial block assignment (k=5 geographic blocks on lat/lon)
3. Fit baselines B0–B5:
   - B0: intercept-only
   - B1: pH only (ridge, spatial-block CV)
   - B2: all cheap env (ridge, spatial-block CV)
   - B3: lat/lon only (ridge)
   - B4: pH only (XGBoost)
   - B5: ordinary kriging on lat/lon — SKIPPED (pykrige not installed)
4. Report per-fold and overall RMSE for each baseline and target
5. Save `data/baseline_results.csv`

### NB02: Hybrid models — **COMPLETE (2026-07-07)**

**H1 (CWM beyond pH)**: FAILS (1/4 metals). Only Ni: ΔRMSE=+0.054, CI[+0.049,+0.060].
**H2 (CWM beyond env)**: PASSES (3/4 metals). Zn: +0.025, Pb: +0.037, Ni: +0.066. Cu exception: CWM hurts (ΔRMSE=−0.134).
**Best models**: M3 (CWM only XGB) = 1.195/0.698/0.968/1.853 (Cu/Zn/Pb/Ni). CWM alone beats env alone (M4) across all targets.
**Conformal**: 90.0% coverage (target 90%). Outputs: `data/cv_results.csv`, `data/bootstrap_delta_rmse.csv`, `data/oof_predictions.parquet`.

1. Fit models M1–M5 using nested spatial CV (outer=block, inner=3-fold random)
2. Compute bootstrap ΔRMSE for H1 (M1 vs B1) and H2 (M2 vs M4)
3. Fit conformal predictors on calibration set; report empirical coverage
4. Multi-output model (M5): assess whether joint training helps vs. independent
5. Save `data/cv_results.csv`, `data/bootstrap_delta_rmse.csv`, model files
6. Report H1 and H2 conclusions

### NB03: External validation — **COMPLETE (AusMicrobiome+NGSA; 2026-07-07)**

**AusMicrobiome+NGSA result (B0, M3, M4, M2; all via Spark for mobility)**:

| Model | Cu | Zn | Pb | Ni |
|-------|------|------|------|------|
| B0 | 1.347 | 1.535 | 0.855 | 1.641 |
| M3 (CWM only) | 1.416 | 1.511 | 0.913 | 1.749 |
| M4 (env only) | **1.049** | **1.308** | **0.900** | **1.306** |
| M2 (env+CWM) | 1.061 | 1.570 | 1.172 | 1.439 |

Feature availability: `mob_*=743/1019` (CSU Spark); `ph=0` (NGSA field_pH missing for most samples); all other env features NaN (GEE table is MicrobeAtlas-specific). XGBoost routes NaN via learned default-direction.

**H6 NOT SUPPORTED** (1/4 metals pass M2/M4 ≤ 1.1× criterion): M2 degrades vs M4 by 20% (Zn), 30% (Pb), 10% (Ni); Cu just passes (ratio=1.011). M4 beats B0 for all 4 metals — CSU mobility features transfer geographically.

Final models fit on full training data: M2, M3, M4, B0. AusMicrobiome holdout pipeline:
1. `BASE_16S_OTU.csv.gz` (91,929 OTUs × 1,023 samples) loaded from `microbeatlas_metal_ecology/data/aus_microbiome/`
2. `BASE_16S_taxonomy.csv` → OTU→genus map (18,152 OTUs with genus assignment)
3. OTU counts aggregated to genus RA; joined with `aus_sample_ngsa.csv` (1,019 common samples via numeric Sample_ID suffix match)
4. CWM computed (coverage 0.717 mean); metal targets log1p-transformed from NGSA columns
5. CSU mobility features via Spark (`get_csu_mobility_features`; 743/1019 matched)
6. Outputs: `data/holdout_results.csv`, `data/holdout_feature_matrices/AusMicrobiome_NGSA_feature_matrix.parquet`

**EMP**: Per-sample OTU count matrix unavailable — SKIP
**SPIRE**: MAG-based, incompatible OTU format — SKIP

### NB04: Interpretation and discovery — **COMPLETE (2026-07-07)**

**H3 (cofactor > resistance SHAP)**: NOT SUPPORTED (0/4). Both CWM_metabolism and CWM_defense rank 16–18 of 18 features. CWM collectively marginal.
**H4 (Cu/Ni largest gain)**: NOT SUPPORTED. Ni rank 1 (✓), Cu rank 4 (negative ΔRMSE).
**SHAP top features**: water_content, mob_pb, temp_K, precip_mm, elevation_m. CWM < 1.5% of total SHAP.
**Threshold**: Near-zero sensitivity for Cu/Zn/Pb; Ni 48% sensitivity, 22% specificity.
**Discovery**: CWM coverage uncorrelated with prediction error (ρ=0.010). Strong Cu-Pb residual anti-correlation (ρ=−0.615). Outputs: `data/shap_importance.csv`, `data/threshold_metrics.csv`, 12+ figures.

1. SHAP analysis for M2 (per-target TreeExplainer)
2. SHAP feature importance table (all targets)
3. Test H3 (cofactor vs. resistance CWM SHAP ranks)
4. Test H4 (ΔRMSE rank by metal)
5. PDP for top features (pH, CWM_cofactor, CWM_resistance)
6. Threshold metrics at regulatory thresholds (H3 follow-up)
7. Discovery: spatial residual map (where does M2 over/under-predict?)
8. Discovery: metal co-prediction analysis (are Cu and Ni errors correlated?)
9. Discovery: CWM coverage vs. prediction error (does low coverage = high error?)

---

## Data access notes

- **MicrobeAtlas OTU table**: `arkinlab.microbeatlas.otu_counts_long` (JupyterHub Spark only)
- **Metal concentrations**: `arkinlab.microbeatlas.enriched_metadata` (GeoROC columns)
- **SoilGrids BERDL**: `arkinlab.envdbs.soilgrids` (column names may need verification)
- **SoilGrids API**: use `scripts/soilgrids_api.py`; cache stored in `data/soilgrids_cache.json`
- **Holdout 16S data**: confirm availability and schema for AusMicrobiome and EMP before NB03

---

## Caveats pre-specified

1. GeoROC metal concentrations in `enriched_metadata` are spatially matched to sample coordinates, not measured directly from the same sample. Measurement error is unknown.
2. CWM coverage is expected to be lower for holdout datasets (different 16S regions, different OTU clustering). Report and flag.
3. Ordinary kriging (B5) requires positive definite variograms; if fitting fails for a target, fall back to IDW.
4. SoilGrids REST API may be unavailable; fall back to BERDL table and document any missing holdout samples.
5. H5 requires fitting both block-CV and random-CV versions of each model; additional compute cost.

---

## Output files

| File | Content |
|------|---------|
| `data/feature_matrix.parquet` | Sample × feature matrix (CWM + env + targets) |
| `data/spatial_blocks.csv` | Sample ID + block label |
| `data/baseline_results.csv` | B0–B5 RMSE per target and fold |
| `data/cv_results.csv` | M1–M5 nested spatial CV RMSE |
| `data/bootstrap_delta_rmse.csv` | H1/H2 bootstrap CI results |
| `data/holdout_results.csv` | External validation RMSE |
| `data/shap_importance.csv` | Mean |SHAP| per feature per target |
| `data/threshold_metrics.csv` | Sensitivity/specificity at regulatory thresholds |
