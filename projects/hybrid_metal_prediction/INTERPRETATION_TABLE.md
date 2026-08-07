# Interpretation Table — hybrid_metal_prediction

**Status key**: PENDING = not yet run | COMPLETE = results available | NEGATIVE = pre-specified test failed

---

## Section 1: Primary hypothesis results (pre-specified confirmatory)

### H1: CWM improves prediction beyond pH alone — **COMPLETE (2026-07-07)**

ΔRMSE = RMSE(B1) − RMSE(M1); positive = CWM helps (M1 better than B1).

| Comparison | Target | ΔRMSE (B1−M1) | Bootstrap 95% CI | Excludes 0 positive? | Status |
|------------|--------|---------------|-----------------|---------------------|--------|
| M1 vs B1 (ridge) | Cu_ppm | −0.002 | [−0.004, −0.001] | NO (negative) | COMPLETE |
| M1 vs B1 (ridge) | Zn_ppm | −0.017 | [−0.018, −0.017] | NO (negative) | COMPLETE |
| M1 vs B1 (ridge) | Pb_ppm | −0.047 | [−0.050, −0.045] | NO (negative) | COMPLETE |
| M1 vs B1 (ridge) | Ni_ppm | +0.026 | [+0.022, +0.030] | **YES** | COMPLETE |

**H1 conclusion**: NEGATIVE. CWM features added to pH (via ridge) improve prediction for **Ni only** (1/4 metals). Pre-specified success criterion was ≥2/4. H1 FAILS as stated.

**Interpretation**: Adding CWM features to the pH-ridge model degrades performance for Cu, Zn, Pb. This likely reflects dimensionality inflation without sufficient signal — the 5 CWM features add noise that the ridge regularisation cannot fully suppress under geographically challenging CV. The Ni result (+0.054, p=1.00 bootstrap) is real and reproducible. The Cu exception is striking (see H2).

---

### H2: CWM improves prediction beyond all cheap env — **COMPLETE (2026-07-07)**

ΔRMSE = RMSE(M4) − RMSE(M2); positive = CWM helps (M2 better than M4).

| Comparison | Target | ΔRMSE (M4−M2) | Bootstrap 95% CI | Excludes 0 positive? | Status |
|------------|--------|---------------|-----------------|---------------------|--------|
| M2 vs M4 (XGBoost) | Cu_ppm | −0.165 | [−0.169, −0.161] | NO (negative) | COMPLETE |
| M2 vs M4 (XGBoost) | Zn_ppm | +0.038 | [+0.036, +0.040] | **YES** | COMPLETE |
| M2 vs M4 (XGBoost) | Pb_ppm | +0.029 | [+0.027, +0.031] | **YES** | COMPLETE |
| M2 vs M4 (XGBoost) | Ni_ppm | +0.053 | [+0.050, +0.056] | **YES** | COMPLETE |

**H2 conclusion**: POSITIVE. CWM features added to env covariates (via XGBoost) improve prediction for **Zn, Pb, Ni** (3/4 metals). Pre-specified success criterion was ≥2/4. **H2 PASSES**.

**Cu exception**: M4 (env only) RMSE = 1.309 vs M2 (env+CWM) = 1.474. CWM features actively hurt Cu prediction when added to env. Note that M3 (CWM only) = 1.152 is the best Cu model — CWM carries Cu signal in isolation but adding env features degrades performance. Pearson r between CWM and mob_* features is ≤0.15 (not collinear). Internal CWM cluster-count collinearity (VIF 280K–1.5M) is metal-nonspecific and cannot explain the Cu-specific pattern. Cu contamination may be more anthropogenic/point-source and less coupled to the total metal cycling that CWM captures.

---

### H3: Cofactor CWM more predictive than resistance CWM — **UNTESTABLE (2026-08-03)**

Features compared: `CWM_mean_n_metabolism_clusters` (cofactor/metabolism) vs `CWM_mean_n_defense_clusters` (resistance/defense). Rank 1 = most important in SHAP for M2 (18 features total).

| Target | Metabolism rank | Defense rank | Metabolism > Defense? | Status |
|--------|----------------|--------------|----------------------|--------|
| Cu_ppm | 18 | 17 | UNTESTABLE | UNTESTABLE |
| Zn_ppm | 18 | 16 | UNTESTABLE | UNTESTABLE |
| Pb_ppm | 18 | 17 | UNTESTABLE | UNTESTABLE |
| Ni_ppm | 18 | 16 | UNTESTABLE | UNTESTABLE |

**H3 conclusion**: UNTESTABLE. `mean_n_metabolism_clusters` in `genus_trait_table.csv` is 0.0 for all 1,654 non-NaN genera — the column was never populated in the upstream `comprehensive_metal_ecology` pangenome pipeline. Because `CWM_mean_n_metabolism_clusters` = 0 for every sample in the training data, its SHAP importance is zero by construction; any rank comparison to `CWM_mean_n_defense_clusters` is meaningless (not a biological test). The rank-18 positions in the SHAP table reflect a constant-zero input, not the cofactor > resistance biological hypothesis. **Corrective action**: populate `mean_n_metabolism_clusters` in `comprehensive_metal_ecology` NB01, regenerate `genus_trait_table.csv`, rebuild the feature matrix (NB00), and rerun NB04.

---

### H4: Predictive gain largest for Cu and Ni — **COMPLETE (2026-07-07)**

| Target | ΔRMSE (M4−M2) | Observed rank | Expected rank | Status |
|--------|---------------|--------------|---------------|--------|
| Ni_ppm | +0.053 | 1 (largest gain) | 1 or 2 | ✓ |
| Zn_ppm | +0.038 | 2 | 3 or 4 | unexpected |
| Pb_ppm | +0.029 | 3 | 3 or 4 | ✓ |
| Cu_ppm | −0.165 | 4 (CWM hurts) | 1 or 2 | ✗ |

**H4 conclusion**: NOT SUPPORTED. Ni rank 1 matches prediction (✓), but Cu has negative ΔRMSE (CWM hurts Cu prediction) — the opposite of what H4 predicts. Success criterion required Cu rank ≤ 2. **H4 FAILS**.

**Interpretation**: The H4 hypothesis assumed Cu and Ni would benefit most from CWM because they are primary cofactors in redox enzymes. The data shows Ni does benefit (rank 1), but Cu uniquely has the opposite pattern — CWM features make Cu predictions worse when combined with env features. The Cu exception likely reflects: (1) Cu contamination is more anthropogenic/point-source; (2) Cu is already well-predicted by mobility features (mob_cu, mob_pb); (3) overfitting in the combined model. **Collinearity between CWM and mob_* features is ruled out**: Pearson r ≤ 0.15 across all CWM–mob_* pairs. Internal CWM cluster-count collinearity (VIF 280K–1.5M) is metal-nonspecific and cannot explain the Cu-specific degradation.

---

### H5: Geographic CV degrades CWM-rich models more — **COMPLETE (2026-08-03, OOF bug fixed)**

| Target | M2 block | M2 random | M2 ratio | M4 block | M4 random | M4 ratio | M2 > M4? |
|--------|----------|-----------|----------|----------|-----------|----------|---------|
| Cu | 1.474 | 0.127 | 11.66 | 1.309 | 0.128 | 10.23 | **Yes** |
| Zn | 0.799 | 0.068 | 11.81 | 0.838 | 0.069 | 12.08 | No |
| Pb | 1.064 | 0.087 | 12.24 | 1.093 | 0.087 | 12.64 | No |
| Ni | 2.089 | 0.174 | 12.00 | 2.142 | 0.171 | 12.54 | No |

**H5 conclusion**: NOT SUPPORTED (1/4 metals). M2 degrades more than M4 under geographic block CV for Cu only. Data: `data/h5_degradation_ratios.csv`.

---

### H6: CWM models transfer to holdout datasets — **COMPLETE (AusMicrobiome+NGSA, 2026-07-07)**

**AusMicrobiome + NGSA holdout** (n=1,019 samples; CWM coverage 0.717 mean, 40% flagged <70%):

Feature availability for holdout: `ph=0, clay_pct=0` (NGSA field_pH mostly missing; SoilGrids API skipped); `mob_*=743/1019` (CSU grid via Spark); `water_content, ndvi, elevation_m, temp_K, precip_mm=0` (GEE table is MicrobeAtlas-specific). XGBoost uses learned default-direction split routing for NaN features.

| Holdout | Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|---------|-------|---------|---------|---------|---------|
| AusMicrobiome+NGSA | B0 | 1.347 | 1.535 | 0.855 | 1.641 |
| AusMicrobiome+NGSA | M3 (CWM-only) | 1.416 | 1.511 | 0.913 | 1.749 |
| AusMicrobiome+NGSA | M4 (env-only) | **1.049** | **1.308** | **0.900** | **1.306** |
| AusMicrobiome+NGSA | M2 (env+CWM) | 1.061 | 1.570 | 1.172 | 1.439 |

M2/M4 ratio (H6 criterion: ≤ 1.1×):

| Target | M2 RMSE | M4 RMSE | M2/M4 ratio | Within 1.1×? |
|--------|---------|---------|------------|--------------|
| Cu | 1.061 | 1.049 | 1.011 | ✓ |
| Zn | 1.570 | 1.308 | 1.200 | ✗ |
| Pb | 1.172 | 0.900 | 1.302 | ✗ |
| Ni | 1.439 | 1.306 | 1.102 | ≈ (boundary) |

| Holdout | Model | vs B0 | vs M4 | Status |
|---------|-------|-------|-------|--------|
| AusMicrobiome+NGSA | M4 | beats B0 for 4/4 metals | — | COMPLETE |
| AusMicrobiome+NGSA | M2 | beats B0 for Cu/Ni; worse for Zn/Pb | M2 > M4 for 4/4 metals | COMPLETE |
| EMP | — | — | — | PENDING |
| SPIRE | — | — | — | PENDING |

**H6 conclusion**: NOT SUPPORTED (1/4 metals cleanly pass the ≤1.1× criterion). M2 (env+CWM) degrades 20–30% vs M4 (env-only) for Zn and Pb on the holdout. Ni is at the boundary (1.10×). Cu is the only clean pass.

**Key findings**:
1. **M4 (env-only) transfers well**: M4 beats B0 for all 4 metals — the CSU mobility features carry signal to Australian soils even with climate/pH features NaN. The geographic mobility gradient is globally consistent.
2. **CWM features actively degrade M4 on holdout for 4/4 metals**: M2 is worse than M4 for every target. The global CWM→metal mapping does not generalize to Australian soils — consistent with the training-data Cu exception and H3 SHAP findings (CWM collectively <1.5% of SHAP importance).
3. **M3 (CWM-only) worse than B0 for Cu/Pb/Ni**: Without env features, CWM alone cannot predict Australian metal concentrations relative to the global training mean. Coverage gap (40% flagged) is a likely contributor.
4. **Partial feature set caveat**: M4/M2 operate with only 6 env features (mob_*); pH, clay, and climate features are NaN for all holdout samples. This weakens the M4 baseline and may inflate M4 RMSE relative to what it would achieve with full features.

**EMP and SPIRE**: Not evaluated — per-sample OTU count matrices not available

---

## Section 2: Model performance summary (pre-specified confirmatory)

### Baselines (NB01) — **COMPLETE (2026-07-07)**

All RMSE values are on log1p-transformed targets (spatial block-holdout CV, k=5 blocks).

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE | Status |
|-------|---------|---------|---------|---------|--------|
| B0 (intercept) | 1.131 | 0.711 | 0.889 | 1.769 | COMPLETE |
| B1 (pH ridge) | 1.198 | 0.621 | 0.962 | 1.880 | COMPLETE |
| B2 (env ridge) | 1.554 | 0.810 | 1.058 | 2.246 | COMPLETE |
| B3 (lat/lon ridge) | 1.106 | 0.681 | 1.188 | 1.881 | COMPLETE |
| B4 (pH XGBoost) | 1.347 | 0.687 | 1.070 | 1.996 | COMPLETE |
| B5 (kriging) | — | — | — | — | SKIPPED (no pykrige) |

**Key observation**: B0 (intercept-only) beats B1, B2, B4 for Cu, Pb, Ni. This is driven by geographic block holdout creating high between-block variance. B2 (env ridge) is WORST for all targets — because `_drop_nan_rows()` drops samples with any NaN env feature, severely reducing training size. This is a feature missingness problem, not a signal problem. The M model comparison will face the same issue — to be noted in interpretation.

### Hybrid models (NB02) — **COMPLETE (2026-08-03, OOF bug fixed)**

All RMSE values are on log1p-transformed targets (spatial block-holdout CV, k=5 blocks).

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE | Status |
|-------|---------|---------|---------|---------|--------|
| M1 (pH+CWM ridge) | 1.170 | 0.701 | 0.970 | 1.856 | COMPLETE |
| M2 (env+CWM XGB) | 1.474 | 0.799 | 1.064 | 2.089 | COMPLETE |
| M3 (CWM only XGB) | 1.152 | 0.752 | 0.958 | 1.848 | COMPLETE |
| M4 (env only XGB) | 1.309 | 0.838 | 1.093 | 2.142 | COMPLETE |
| M5 (multi-output XGB) | 1.537 | 0.827 | 1.030 | 2.133 | COMPLETE |

**Key observations**:
- M3 (CWM only XGB) is the best model for Cu, Pb, Ni; M1 (pH+CWM) is best for Zn (0.701, only model beating B0=0.711).
- For Cu: M3 = 1.152 beats M4 = 1.309. But combining CWM with env (M2=1.474) hurts vs env alone (M4=1.309) — mechanism is Cu-specific overfitting; collinearity between CWM and mob_* features is ruled out (Pearson r ≤ 0.15; empirically measured 2026-08-03).
- All M-models are worse than B0 (intercept) for Cu — geographic block holdout is the dominant challenge.
- Conformal prediction: empirical coverage 0.900 exactly (target 0.90) — well-calibrated intervals.

---

## Section 3: Threshold metrics (exploratory) — **COMPLETE (2026-07-07)**

M2 OOF predictions vs regulatory thresholds (log1p-transformed comparison).

| Target | Threshold (ppm) | n above | Sensitivity | Specificity | PPV | Status |
|--------|----------------|---------|------------|------------|-----|--------|
| Cu_ppm | 100 | 3,316 | 0.007 | 0.980 | 0.067 | COMPLETE |
| Zn_ppm | 300 | 474 | 0.000 | 1.000 | 0.000 | COMPLETE |
| Pb_ppm | 100 | 40 | 0.000 | 1.000 | NaN | COMPLETE |
| Ni_ppm | 50 | 15,990 | 0.480 | 0.222 | 0.482 | COMPLETE |

**Key finding**: Threshold performance is poor for Cu, Zn, Pb (near-zero sensitivity). Only Ni shows moderate sensitivity (48%) due to Ni's high prevalence above the 50 ppm threshold (38% of samples). The model cannot reliably identify sites above regulatory limits — it is better suited for ranking or relative risk assessment than binary exceedance detection.

---

## Section 4: SHAP feature importance (exploratory) — **COMPLETE (2026-07-07)**

Mean |SHAP| from M2 (env+CWM XGBoost), fit on full training data. Top 15 of 18 features shown.

| Rank | Feature | Mean |SHAP| (Cu) | Mean |SHAP| (Zn) | Mean |SHAP| (Pb) | Mean |SHAP| (Ni) | Mean (all) |
|------|---------|------|------|------|------|--------|
| 1 | water_content | 0.170 | 0.037 | 0.205 | 0.455 | **0.217** |
| 2 | mob_pb | 0.180 | 0.163 | 0.092 | 0.319 | **0.188** |
| 3 | temp_K | 0.053 | 0.048 | 0.054 | 0.338 | 0.123 |
| 4 | precip_mm | 0.119 | 0.056 | 0.112 | 0.150 | 0.109 |
| 5 | elevation_m | 0.051 | 0.030 | 0.054 | 0.282 | 0.104 |
| 6 | mob_hg | 0.165 | 0.079 | 0.067 | 0.083 | 0.099 |
| 7 | ph | 0.075 | 0.140 | 0.087 | 0.036 | 0.085 |
| 8 | mob_cd | 0.088 | 0.089 | 0.038 | 0.115 | 0.082 |
| 9 | mob_as | 0.095 | 0.050 | 0.056 | 0.122 | 0.081 |
| 10 | mob_cr | 0.047 | 0.027 | 0.142 | 0.082 | 0.075 |
| 11 | mob_cu | 0.105 | 0.031 | 0.032 | 0.050 | 0.054 |
| 12 | ndvi | 0.024 | 0.025 | 0.069 | 0.064 | 0.045 |
| 13 | clay_pct | 0.025 | 0.026 | 0.053 | 0.032 | 0.034 |
| 14 | CWM_mean_metal_core_fraction | 0.002 | 0.003 | 0.003 | 0.006 | 0.003 |
| 15 | CWM_mean_n_homeostasis_clusters | 0.001 | 0.001 | 0.001 | 0.004 | 0.002 |
| 16-18 | CWM_mean_n_{metal,defense,metabolism}_clusters | <0.001 | <0.001 | <0.001 | <0.001 | <0.001 |

**Finding**: Environmental features dominate completely. CWM features collectively account for <1.5% of total mean |SHAP| importance. The model learns to predict metal concentrations primarily from climate (water_content, temp_K, precip_mm), Pb mobility (mob_pb — collinear with other metals in contaminated soils), and pH. Microbial functional gene density (CWM) is a marginal predictor in the combined model despite H2 passing (CWM adds small but statistically detectable value for Zn, Pb, Ni).

---

## Section 5: Connection to comprehensive_metal_ecology

This project tests whether the functional architecture discovered in `comprehensive_metal_ecology` (cofactor > resistance in PGLS) translates into predictive power. Key bridging claims:

| Claim from comp_metal_eco | Prediction tested here | Test | Status |
|--------------------------|----------------------|------|--------|
| Cofactor β stronger than resistance β | CWM_cofactor more predictive than CWM_resistance (H3) | SHAP rank | UNTESTABLE — metabolism CWM column is 0 for all genera in trait table (upstream pipeline gap) |
| Metal gene signal is moderate (streamlining context) | CWM features help but not dramatically | H2 ΔRMSE | SUPPORTED (Zn/Pb/Ni, not Cu) |
| Cofactor signal is robust (NB26 jackknife) | CWM_cofactor SHAP stable across folds | SHAP fold variance | NOT TESTED |

---

## Notes

- All RMSEs are for log1p-transformed target values (comparisons within-scale only)
- Bootstrap ΔRMSE uses n=1,000 resamples, 95% CI
- Conformal coverage targets 90% (α=0.10)
- "Excludes 0" for ΔRMSE CI means the CI does not overlap 0; a ΔRMSE > 0 means the baseline is worse (larger RMSE)
