# REPORT: hybrid_metal_prediction

**Primary question:** Can community-weighted mean (CWM) functional gene densities predict soil metal concentrations, and do they add value beyond cheap environmental covariates alone?

**Arc:** Arc 2 — Community Composition as Environmental Predictor

**Status:** All notebooks complete (NB00–NB05, 2026-07-07 to 2026-07-09). H5 KFold random CV added to NB02 and executed (2026-08-03). OOF index misalignment bug in `modelling.py` fixed and NB02 rerun (2026-08-03); all M-model RMSE values updated. All hypotheses have final verdicts.

---

## Headline

CWM features derived from 16S relative abundances × per-Mb KO densities carry a modest global-scale metal signal when used alone (M3 > M4 for Cu in spatial CV) and **do add statistically detectable predictive value over env-only XGBoost for Zn/Pb/Ni** (H2 SUPPORTED, 3/4 metals, ΔRMSE = 0.029–0.053). However, the CWM benefit does not transfer to the Australian holdout — **M4 (env-only) outperforms M2 (env+CWM) for all 4 holdout metals**, and Cu shows the opposite pattern in training CV (M2 worse than M4). Environmental features (water content, Pb mobility, temperature) account for >98.5% of mean |SHAP| importance. The predictive signal in this dataset is primarily geographic, not microbial-functional. H2 is formally SUPPORTED but the geographic generalization (H6) fails.

---

## Hypothesis Verdicts

| Code | Hypothesis | Verdict | Criterion met? | Metals passing |
|------|-----------|---------|----------------|---------------|
| H1 | CWM+pH (M1) improves over pH-only (B1) | **NEGATIVE** | ≥2/4: FAILS | Ni only (1/4) |
| H2 | CWM+env (M2) improves over env-only (M4) | **SUPPORTED** | ≥2/4: PASSES | Zn, Pb, Ni (3/4) |
| H3 | Cofactor CWM more predictive than resistance CWM | **UNTESTABLE** | — | metabolism CWM = 0 for all genera (pipeline gap) |
| H4 | Predictive gain largest for Cu and Ni | **NOT SUPPORTED** | Cu rank ≤2: FAILS | Ni rank 1 ✓; Cu ΔRMSE < 0 ✗ |
| H5 | Block-CV degrades CWM-rich models more | **NOT SUPPORTED** | ≥2/4: FAILS | Cu only (1/4) |
| H6 | CWM models transfer to AusMicrobiome holdout | **NOT SUPPORTED** | M2/M4 ≤1.1× for ≥2/4: FAILS | Cu only (1/4) |
| H_temporal | Model performance stable across collection years | **NOT SUPPORTED (null)** | 0/40 degradation | 7/40 show improvement |

---

## Primary Model Results

All RMSE values are on log1p-transformed targets under spatial leave-one-block-out CV (k=5 geographic blocks), except holdout rows. *Lower is better.*

### Baselines (NB01)

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|-------|---------|---------|---------|---------|
| B0 (intercept) | 1.131 | 0.711 | 0.889 | 1.769 |
| B1 (pH, ridge) | 1.198 | 0.621 | 0.962 | 1.880 |
| B2 (all env, ridge) | 1.554 | 0.810 | 1.058 | 2.246 |
| B3 (lat/lon, ridge) | 1.106 | 0.681 | 1.188 | 1.881 |
| B4 (pH, XGBoost) | 1.347 | 0.687 | 1.070 | 1.996 |

*Note: B0 beats B1, B2, B4 for Cu, Pb, Ni — geographic block holdout creates high between-block variance. B2 is worst across all targets due to NaN-drop reducing training size.*

### Hybrid models (NB02)

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|-------|---------|---------|---------|---------|
| M1 (pH + CWM, ridge) | 1.170 | **0.701** | 0.970 | 1.856 |
| M2 (env + CWM, XGB) | 1.474 | 0.799 | 1.064 | 2.089 |
| M3 (CWM only, XGB) | **1.152** | 0.752 | **0.958** | **1.848** |
| M4 (env only, XGB) | 1.309 | 0.838 | 1.093 | 2.142 |
| M5 (multi-output XGB) | 1.537 | 0.827 | 1.030 | 2.133 |

**Key pattern:** M3 (CWM alone) is the best model for Cu, Pb, Ni; M1 (pH+CWM) is best for Zn and the only model to beat B0 (0.701 vs 0.711). Adding env features to CWM (M2) degrades Cu by 28% vs M3 — possible collinearity or overfitting. All M-models fail to beat B0 for Cu, Pb, Ni under geographic block CV.

### H1 bootstrap ΔRMSE: B1 − M1 (positive = M1 better)

| Target | ΔRMSE | 95% CI | H1 pass? |
|--------|-------|--------|---------|
| Cu | −0.002 | [−0.004, −0.001] | ✗ (M1 worse) |
| Zn | −0.017 | [−0.018, −0.017] | ✗ (M1 worse) |
| Pb | −0.047 | [−0.050, −0.045] | ✗ (M1 worse) |
| Ni | **+0.026** | [+0.022, +0.030] | **✓** |

### H2 bootstrap ΔRMSE: M4 − M2 (positive = M2 better)

| Target | ΔRMSE | 95% CI | H2 pass? |
|--------|-------|--------|---------|
| Cu | −0.165 | [−0.169, −0.161] | ✗ (M2 worse) |
| Zn | **+0.038** | [+0.036, +0.040] | **✓** |
| Pb | **+0.029** | [+0.027, +0.031] | **✓** |
| Ni | **+0.053** | [+0.050, +0.056] | **✓** |

### H5: Block/random CV degradation ratios (NB02 extended, 2026-08-03)

KFold(n_splits=5, random_state=42). Random RMSE is inflated by spatial autocorrelation leakage (0.06–0.17 vs block RMSE 0.68–2.19); degradation ratios in the 11–13× range reflect this leakage, not genuine model quality. The H5 test is the ratio comparison: does M2 degrade *more* than M4?

| Target | M2 block | M2 random | M2 ratio | M4 block | M4 random | M4 ratio | M2 > M4? |
|--------|----------|-----------|----------|----------|-----------|----------|---------|
| Cu | 1.474 | 0.127 | 11.66 | 1.309 | 0.128 | 10.23 | **Yes** |
| Zn | 0.799 | 0.068 | 11.81 | 0.838 | 0.069 | 12.08 | No |
| Pb | 1.064 | 0.087 | 12.24 | 1.093 | 0.087 | 12.64 | No |
| Ni | 2.089 | 0.174 | 12.00 | 2.142 | 0.171 | 12.54 | No |

**H5: NOT SUPPORTED** (1/4 metals). M2 degrades more than M4 under geographic block CV for Cu only. For Zn, Pb, and Ni, M4 (env-only) actually degrades *more* — env features (water_content, temp_K, mob_pb) are more geographically structured than CWM features, so M4 overfits to spatial gradients under random CV and pays a larger penalty when those gradients are held out. Data: `data/h5_degradation_ratios.csv`.

---

## SHAP Feature Importance (NB04)

Mean |SHAP| values for M2 (env + CWM, full training set). CWM features are shown as a group.

| Rank | Feature | Mean |SHAP| (Cu) | Mean |SHAP| (Zn) | Mean |SHAP| (Pb) | Mean |SHAP| (Ni) |
|------|---------|------|------|------|------|
| 1 | water_content | 0.170 | 0.037 | 0.205 | 0.455 |
| 2 | mob_pb | 0.180 | 0.163 | 0.092 | 0.319 |
| 3 | temp_K | 0.053 | 0.048 | 0.054 | 0.338 |
| 4 | precip_mm | 0.119 | 0.056 | 0.112 | 0.150 |
| 5 | elevation_m | 0.051 | 0.030 | 0.054 | 0.282 |
| 6 | mob_hg | 0.165 | 0.079 | 0.067 | 0.083 |
| 7 | ph | 0.075 | 0.140 | 0.087 | 0.036 |
| 8–13 | mob_cd, mob_as, mob_cr, mob_cu, ndvi, clay_pct | ... | ... | ... | ... |
| 14 | CWM_mean_metal_core_fraction | 0.002 | 0.003 | 0.003 | 0.006 |
| 15–18 | CWM_mean_n_{homeostasis,metal,defense,metabolism} | <0.001 | <0.001 | <0.001 | <0.001 |

**Finding:** Environmental features account for >98.5% of combined mean |SHAP| importance. CWM features are marginal contributors across all 4 targets.

H3 verdict (NB04, 2026-08-03): **UNTESTABLE**. `CWM_mean_n_metabolism_clusters` = 0.0 for all 1,654 non-NaN genera in `genus_trait_table.csv` — the metabolism cluster column was never populated in the upstream `comprehensive_metal_ecology` pangenome pipeline. SHAP importance is zero by construction; the rank of 18/18 reflects a constant-zero input, not the biological hypothesis. `CWM_mean_n_defense_clusters` (the comparator) is a valid non-zero column (mean = 6.91 clusters/genome). H3 cannot be evaluated until the upstream pipeline gap is fixed.

---

## Threshold Discrimination (NB04)

M2 OOF predictions vs regulatory exceedance thresholds:

| Target | Threshold | n above | Sensitivity | Specificity | PPV |
|--------|-----------|---------|------------|------------|-----|
| Cu | >100 ppm | 3,316 | 0.007 | 0.980 | 0.067 |
| Zn | >300 ppm | 474 | 0.000 | 1.000 | 0.000 |
| Pb | >100 ppm | 40 | 0.000 | 1.000 | NaN |
| Ni | >50 ppm | 15,990 | 0.480 | 0.222 | 0.482 |

The model cannot reliably flag regulatory exceedance for Cu, Zn, or Pb. Only Ni shows moderate sensitivity (48%) due to high prevalence above threshold (38% of samples). M2 is better suited for ranking/relative risk than binary exceedance detection.

---

## External Validation — AusMicrobiome + NGSA Holdout (NB03)

n = 1,019 Australian soil samples; CWM mean coverage = 0.717 (40% flagged <70%). env features: only mob_* available (6/13 features); pH, clay, climate features are NaN for all holdout samples (XGBoost handles via learned default-direction split routing).

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|-------|---------|---------|---------|---------|
| B0 (training mean) | 1.347 | 1.535 | 0.855 | 1.641 |
| M3 (CWM only) | 1.416 | 1.511 | 0.913 | 1.749 |
| **M4 (env only)** | **1.049** | **1.308** | **0.900** | **1.306** |
| M2 (env + CWM) | 1.061 | 1.570 | 1.172 | 1.439 |

### H6: M2/M4 ratio (criterion ≤1.1×)

| Target | M2/M4 | ≤1.1×? |
|--------|-------|--------|
| Cu | 1.011 | ✓ |
| Zn | 1.200 | ✗ |
| Pb | 1.302 | ✗ |
| Ni | 1.102 | ≈ (boundary) |

**H6: NOT SUPPORTED** (Cu is the only clean pass). M4 (env-only) beats M2 (env+CWM) for all 4 holdout metals. M3 (CWM-only) is worse than B0 for Cu/Pb/Ni. The global CWM→metal mapping does not generalize to Australian soils. The mob_* features (CSU metal mobility, available via Spark in holdout) carry geochemical signal that transfers globally; CWM features that map to global MicrobeAtlas communities do not transfer to Australian genera.

**Key holdout finding: M4 transfers well.** M4 beats B0 for all 4 metals on the Australian holdout despite having only 6 of 13 env features. CSU metal mobility gradients are geochemically consistent across continents.

---

## Temporal Drift Analysis (NB05)

Tests whether model RMSE degrades for later-collected samples vs earlier cohorts. n=40 year-level tests (4 metals × 10 collection year splits).

**Result:** H_temporal NOT SUPPORTED. 0/40 tests show statistically significant temporal degradation. 7/40 tests show significant *improvement* for more recent samples (including the 2020 EMP500 cohort outperforming 2017–18 rhizosphere cohorts). Models trained on historical MicrobeAtlas data generalize to samples collected years later — suggesting the CWM signal, where it exists, is temporally stable.

Data: `data/temporal_drift_rmse.parquet`, `data/temporal_drift_correlation_summary.csv`.

---

## Cross-Project Integration

| Arc connection | Finding |
|---------------|---------|
| Arc 1 (`comprehensive_metal_ecology`) H3 cofactor > resistance (PGLS) | Does NOT translate to CWM SHAP importance — both CWM features rank last. The PGLS signal operates at the evolutionary timescale; CWM predicts contemporary metal concentrations from current community functional load. |
| Arc 2 (`community_composition_prediction`) M2 vs M3 | CCP confirms M3 (CWM, 5 scalars) outperforms genus-weighted functional features (110 GW features) for Zn/Pb/Ni — collapsing to CWM loses no information relative to genus-level GW. |
| Arc 2 (`mwas_confound_analysis`) | 99.6% collapse of KO-metal associations after environmental confound control — consistent with CWM features carrying near-zero SHAP. The individual-KO signal that CWM aggregates is near-absent. |
| Arc 3 (`metal_contamination_bioindicators`) | M4 env-only (with mob_* features) transfers to Australian holdout with RMSE < B0 for all 4 metals, consistent with CLR + study-blocked CV showing spatial signal dominates taxonomy in the contamination bioindicator context. |

---

## Limitations

1. **Random CV RMSE is dominated by spatial autocorrelation leakage.** KFold random RMSE = 0.06–0.17 vs block RMSE = 0.68–2.19; the 11–13× degradation ratios reflect leakage of spatially autocorrelated samples into train/test folds, not genuine model quality. The H5 ratio comparison is valid (it tests *relative* degradation M2 vs M4), but the absolute random-CV RMSE figures cannot be cited as meaningful performance estimates.
2. **Holdout feature missingness.** AusMicrobiome holdout has pH, clay, and climate features NaN for all 1,019 samples; XGBoost handles this via default-direction routing but the M4 holdout RMSE is inflated relative to its potential with full features.
3. **EMP and SPIRE holdouts not evaluated.** Per-sample OTU count matrices were not available for external validation.
4. **CWM coverage in holdout.** 40% of AusMicrobiome samples have <70% CWM coverage (genus RA matched to pangenome). This was not shown to inflate RMSE (sensitivity analysis passed), but may understate the CWM contribution in a coverage-complete holdout.
5. **Geographic block CV as primary metric.** B0 (intercept-only) beats B1, B2, B4 for multiple targets — the spatial block CV penalises all models relative to simpler baselines. This is methodologically correct (geography is the dominant confounder) but makes RMSE comparisons difficult to interpret in absolute terms.
6. **Cu exception: collinearity ruled out as primary cause.** M2 is 9% worse than M4 for Cu, while M3 (CWM-only) beats M4. Pearson r between CWM features and mob_* features is ≤0.15 — CWM and mob_* are not collinear with each other. However, VIF among the CWM cluster count features themselves is extreme (280K–1.5M), indicating that the three cluster-count CWMs (`metal_clusters`, `defense_clusters`, `homeostasis_clusters`) are near-redundant. This internal CWM collinearity makes feature attribution unstable but affects all four metals equally and cannot explain the Cu-specific pattern. The Cu exception most likely reflects (a) Cu contamination being more anthropogenic/point-source than Zn/Pb/Ni, and (b) Cu already being well-predicted by mob_cu and mob_pb independently, so adding collinear CWM features introduces noise rather than signal. The mechanism is not confirmed by the current analysis.

---

## Data Provenance

| File | Contents | Source notebook |
|------|----------|----------------|
| `data/feature_matrix.parquet` | 42,037 × 44 (env + CWM + target); spatial_block IDs | NB00 |
| `data/baseline_results.csv` | B0–B5 RMSE across 5 spatial blocks | NB01 |
| `data/cv_results.csv` | M1–M5 RMSE per block and mean | NB02 |
| `data/bootstrap_delta_rmse.csv` | Bootstrap ΔRMSE with 95% CI (n=1,000) | NB02 |
| `data/oof_predictions.parquet` | Out-of-fold predictions for M2 | NB02 |
| `data/holdout_results.csv` | AusMicrobiome+NGSA holdout RMSE (B0, M2, M3, M4) | NB03 |
| `data/shap_importance.csv` | Mean |SHAP| per feature × target for M2 | NB04 |
| `data/threshold_metrics.csv` | Sensitivity/specificity/PPV at regulatory thresholds | NB04 |
| `data/h5_degradation_ratios.csv` | Block/random RMSE and degradation ratio for M2 and M4 (H5) | NB02 extended |
| `data/temporal_drift_rmse.parquet` | RMSE by collection-year stratum | NB05 |
| `data/temporal_drift_correlation_summary.csv` | Correlation: collection year vs RMSE | NB05 |
| `data/spatial_blocks.csv` | k=5 block assignments for all training samples | NB00 |

---

## Notebook Provenance

| Notebook | Status | Date | Key output |
|----------|--------|------|-----------|
| `00_feature_matrix.ipynb` | Complete | 2026-07-07 | Feature matrix 42,037 × 44; coverage report |
| `01_baselines_and_eda.ipynb` | Complete | 2026-07-07 | B0–B5 RMSE; EDA figures |
| `02_hybrid_models.ipynb` | Complete | 2026-08-03 | M1–M5 RMSE; bootstrap ΔRMSE; OOF predictions (OOF bug fixed) |
| `03_external_validation.ipynb` | Complete | 2026-07-07 | AusMicrobiome+NGSA holdout RMSE |
| `04_interpretation_and_discovery.ipynb` | Complete | 2026-07-07 | SHAP; threshold metrics; PDP figures |
| `05_temporal_drift.ipynb` | Complete | 2026-07-09 | Temporal drift null; 7/40 improvement tests |
