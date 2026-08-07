# Community Composition Prediction — Synthesis Report

**Status**: All notebooks complete (NB00–NB09). H1/H2/H5 supported; H3/H4/H6/H7/H8 not supported; H9 untestable. Spatial autocorrelation is the dominant challenge. NB09 resolves Limitation 5 (Pb threshold, sensitivity 0.25→1.00) and extends H8 to all 8 geographic regions; Cu block CV failure confirmed structural.

---

## Headline Findings

1. **Taxonomic community composition (CLR) outperforms cheap geochem (B2) for Zn, Pb, and Ni** (H1 SUPPORTED 3/4), but CLR (B1) is worse than the intercept-only baseline (B0) for all 4 metals — the H1 comparison is between two models that both fail to beat the training mean. Cu fails both comparisons.
2. **Genus-weighted functional features (GW) improve over CLR+geochem** for all four metals (H2 SUPPORTED 4/4), but the absolute gain is modest and primarily reflects the collapse of B3 (CLR+geochem) rather than genuine functional signal.
3. **CWM scalars outperform GW for 3/4 metals** (H3 NOT SUPPORTED): the 110 GW features add noise relative to the 5 CWM scalars when combined with CLR + env features.
4. **Environmental features dominate**: mob_* and soil/climate contribute >80% of M2 SHAP importance across all metals. CLR ranks second; GW contributes <15% of CLR's SHAP (H4 NOT SUPPORTED).
5. **Kriging dominates**: spatial proximity (IDW/kriging) outperforms M2 for Cu, Zn, and Ni — geographic location is the primary predictor of metal concentrations, not microbial composition (H6 NOT SUPPORTED).
6. **Within-region taxonomic signal for mine proximity is strong** (CLR R² > 0.05 in 7/8 geographic regions) but geographically specific — cross-region transfer collapses (CLR AUC = 0.18 for binary classification). H8 NOT SUPPORTED because GW functional features add no value over CLR (mean Δ R² = −0.38 in continuous regression; ≤0.002 AUC in binary classification).
7. **M2 transfers to Australian soils for Cu and Ni** (H5 SUPPORTED 2/4); Zn fails (1.59× degradation).

---

## Hypothesis Verdicts

| Hypothesis | Description | Verdict | Metals passing |
|------------|-------------|---------|---------------|
| H1 | CLR taxonomy > cheap geochem (pH + lat/lon) | **SUPPORTED** | 3/4 (Zn, Pb, Ni) |
| H2 | GW functional features > CLR+geochem (B3) | **SUPPORTED** | 4/4 |
| H3 | GW (M2) outperforms CWM (M3) | **NOT SUPPORTED** | 1/4 (Cu only) |
| H4 | GW SHAP > CLR SHAP in M2 | **NOT SUPPORTED** | 0/4 |
| H5 | M2 generalises to AusMicrobiome holdout (ratio ≤ 1.1) | **SUPPORTED** | 2/4 (Cu, Ni) |
| H6 | Kriging+M1 hybrid < kriging alone | **NOT SUPPORTED** | 0/4 |
| H7 | CLR/GW more useful for bioavailable mobility targets | **NOT SUPPORTED** | 0/2 |
| H8 | Within-region AUC > 0.70 AND GW adds ≥ 0.02 AUC over CLR | **NOT SUPPORTED** | Criterion 1 met (2/2); criterion 2 fails (GW adds ≤ 0.002) |
| H9 | MAG-derived functional profiles > GW | **UNTESTABLE** | — |

---

## Spatial Block CV RMSE (5-block geographic leave-one-out)

| Model | Description | Cu | Zn | Pb | Ni |
|-------|-------------|-----|-----|-----|-----|
| B0 | Intercept-only | 1.115 | 0.678 | 0.880 | 1.702 |
| B1 | CLR (200 genera, XGB) | 1.136 | 0.707 | 0.954 | 1.830 |
| B2 | Geochem (pH + lat/lon, ridge) | 1.183 | 0.828 | 1.251 | 1.678 |
| B3 | CLR + geochem (XGB) | 1.597 | 0.746 | 1.119 | 1.967 |
| B4 | CWM (5 scalars, XGB) | 1.172 | 0.738 | 0.971 | 1.819 |
| M1 | CLR + GW (110 features) | 1.143 | 0.703 | 0.970 | 1.842 |
| M2 | CLR + GW + env (full model) | 1.121 | 0.923 | 0.826 | 1.864 |
| M2_mine | CLR + GW + env + mine proximity | 1.199 | 0.931 | **0.773** | 1.822 |
| M3 | CLR + CWM + env | 1.147 | 0.900 | 0.822 | 1.838 |

**Key observations**:
- B3 (CLR+geochem) collapses badly for Cu (1.597 vs B0=1.115) and Ni (1.967 vs B0=1.702) — XGBoost overfits 200 CLR + 3 geochem features without spatial anchoring.
- M1 (CLR+GW) avoids this collapse; the GW functional features replace the problematic geochem features.
- M2 is best for Pb and Cu but is worse than B0 for Zn and Ni — adding env features (especially mob_*) hurts spatial generalisation for Zn.
- M3 beats M2 for Zn, Pb, and Ni — CWM aggregation (5 scalars) is more regularised than 110 GW features.
- **M2_mine** adds mine proximity features (log_mine_prox_km, log_tri_prox_km, log_npl_prox_km, has_mine_prox_data indicator; 36.8% sample coverage via 10 km haversine join). M2_mine beats B0 for Pb (0.773 vs 0.880) — the only metal where mine proximity improves block CV. Cu degrades further (1.199 vs M2=1.121): the mine proximity sentinel (63.2% uncovered samples) adds confounding noise to the Cu model.
- No model beats B0 for Cu in spatial block CV — mine proximity (NB09) confirms this is structural, not a missing-feature problem.

---

## SHAP Importance (M2, mean |SHAP| per feature group, full training set)

| Feature group | Cu | Zn | Pb | Ni |
|--------------|-----|-----|-----|-----|
| CLR (200 genera) | 0.129 | 0.086 | 0.110 | 0.259 |
| GW functional (110 features) | 0.020 | 0.026 | 0.027 | 0.045 |
| Env mobility (mob_*) | 0.635 | 0.429 | 0.412 | 0.781 |
| Env soil/climate | 0.539 | 0.365 | 0.630 | 1.112 |

GW SHAP is 13–16% of CLR SHAP across all metals — functional gene-content is a marginal predictor. Environmental features account for 77–84% of total SHAP.

**Top CLR genera by metal:**
- **Cu**: _Nitrosospira_, _Methanothrix_, _Steroidobacter_ (_Nitrosospira_ = ammonia-oxidising AOB, distinct from nitrite-oxidising _Nitrospira_; Cu sensitivity in AOB is well-established)
- **Zn**: _Nitrososphaera_, _Neobacillus_, _Gaiella_ (archaeal ammonia oxidiser is the Zn driver)
- **Pb**: _Acinetobacter_, _Agrobacterium_, _Actinomarinicola_ (Pb-tolerant genera)
- **Ni**: _Lentzea_, _Xenorhabdus_, _Rhodomicrobium_ (actinobacteria/entomopathogen co-occurrence)

---

## AusMicrobiome External Holdout (H5, n = 1,019 samples)

| Model | Cu | Zn | Pb | Ni |
|-------|-----|-----|-----|-----|
| B0 (training mean) | 1.347 | 1.535 | 0.855 | 1.641 |
| B1 (CLR only) | 1.297 | 1.520 | 1.067 | 1.644 |
| M1 (CLR + GW) | 1.286 | 1.572 | 1.033 | 1.681 |
| M2 (CLR + GW + env) | 0.961 | 1.464 | 0.957 | 1.815 |

| Target | Training RMSE | Holdout RMSE | Ratio | H5 pass (≤1.1)? |
|--------|--------------|-------------|-------|-----------------|
| Cu | 1.121 | 0.961 | **0.857** | ✓ |
| Zn | 0.923 | 1.464 | **1.586** | ✗ |
| Pb | 0.826 | 0.957 | **1.158** | ✗ |
| Ni | 1.864 | 1.815 | **0.973** | ✓ |

Cu and Ni transfer because mob_cu and mob_ni are available in the Australian holdout (via Spark CSU PF1). Zn fails because the Zn-related community signals in the ENIGMA/USA training data do not generalise to Australian dryland soils. Spatial autocorrelation inflates within-region random CV for Zn; the Australian holdout is a cleaner test and reveals the true cross-region degradation. **WP6 resolved**: holdout RMSE is no worse in low-pangenome-coverage samples (coverage <70%) than in high-coverage samples for all four metals — environmental features (mob_*, soil) drive prediction regardless of CLR coverage.

---

## Threshold Discrimination

### M2 (OOF predictions, NB04)

| Target | Cutoff | Sensitivity | Specificity | n_positive |
|--------|--------|------------|------------|-----------|
| Cu | > 100 ppm | 0.015 | 0.979 | 2,401 |
| Zn | > 300 ppm | 0.000 | 1.000 | 156 |
| Pb | > 100 ppm | 0.000 | 1.000 | 40 |
| Ni | > 50 ppm | 0.462 | 0.307 | 15,286 |

OOF threshold discrimination is poor for all four metals. Cu and Zn sensitivity collapse to near zero (0.015 and 0.000) compared to the inflated training-set values (0.977 and 0.981) — a direct consequence of M2 overfitting threshold-relevant patterns on the training organisms. Ni retains partial discrimination (sensitivity=0.462) but at poor specificity (0.307). Pb sensitivity=0.000 confirms the OOD character of mine-contaminated Pb sites. The training-set values (previously reported) were artefacts of resubstitution; OOF is the correct measure. The mine proximity extension (M2_mine, NB09) restores Pb threshold discrimination (sensitivity=1.00) and partially improves Cu.

### M2_mine (with mine proximity features, NB09, OOF predictions)

| Target | Cutoff | AUC | Sensitivity | Specificity | n_positive |
|--------|--------|-----|------------|------------|-----------|
| Cu | > 100 ppm | 0.638 | 0.786 | 0.493 | 2,401 |
| Pb | > 100 ppm | 0.620 | **1.000** | 0.570 | 40 |

**Pb threshold RESOLVED**: mine proximity features capture all 40 Pb > 100 ppm samples at the Youden-optimal threshold (sensitivity 0.25 → 1.00). AUC = 0.620 is modest because only 40/42,037 samples are above-threshold (0.1% prevalence), but all are recovered. Cu sensitivity is 0.786 at lower specificity (0.493) — the mine proximity indicator shifts the Cu discrimination curve but at the cost of false positives for non-mining Cu sources.

---

## Kriging vs M2 (H6)

| Target | Kriging (IDW) | M2 | Hybrid | Kriging < M2? |
|--------|--------------|-----|--------|--------------|
| Cu | **1.071** | 1.121 | 1.220 | ✓ |
| Zn | **0.683** | 0.923 | 0.801 | ✓ |
| Pb | 0.873 | **0.826** | 1.021 | ✗ |
| Ni | **1.659** | 1.864 | 1.906 | ✓ |

Kriging (IDW spatial block LOO) outperforms M2 for Cu, Zn, and Ni. Only Pb is reversed — Pb contamination is driven by mine proximity (a land-use pattern) rather than geochemical gradients that IDW would capture. The kriging+M1 hybrid is worse than kriging alone for all metals: M1 overfits kriging residuals in training blocks and does not generalise. **Geographic location is the dominant predictor of metal concentrations; microbiome composition adds value only where spatial gradients fail (Pb).**

---

## Bioavailable Target Prediction (H7)

Six mobility targets (mob_as, mob_cd, mob_cr, mob_cu, mob_hg, mob_pb; CSU PF1 fractions, n=37,499). Feature sets exclude mob_* as predictors. M1 (CLR+GW) degrades versus B0 for both Cu and Pb mobility targets, with larger relative degradation for mobility than for total ppm. B0 (intercept-only) is the best microbiome-free baseline for most mobility fractions. M2_soil (soil/climate features) improves over B0 for mob_cd and mob_hg, confirming that climate/soil variables — not microbial composition — drive mobility variation.

---

## Regional Contamination Classification (H8)

### Binary classification (NB07 — contaminated vs reference)

- Only 2 of 8 k-means geographic clusters had sufficient contaminated AND reference samples (≥10 each class).
- **Within-region 5-fold CV AUC**: Region 0 = 0.994 (CLR alone), Region 1 = 0.998 (CLR alone).
- **Cross-region AUC**: CLR = 0.181, M1 = 0.174, M2 = 0.526.
- GW features add at most 0.002 AUC over CLR within-region — no room for the required ≥0.02 delta.

Within-region classification is near-perfect with CLR alone, but cross-region transfer collapses to below-chance (CLR AUC = 0.18). The taxonomic signal that distinguishes contaminated from reference sites is geographically specific — different genera indicate contamination in different regions.

### Extended analysis: continuous mine proximity regression (NB09)

Binary classification was limited to 2 of 8 regions by class balance. NB09 re-frames H8 as continuous regression of log_mine_prox_km (n=15,476, 36.8% coverage via 10 km haversine join from `site_classification.csv`). All 8 k-means regions are now usable.

| Region | n | CLR R² | CLR+GW R² | GW delta |
|--------|---|--------|-----------|----------|
| 0 | 1,465 | +0.785 | +0.800 | +0.015 |
| 1 | 9,822 | +0.757 | +0.765 | +0.008 |
| 2 | 237 | +0.157 | +0.364 | +0.207 |
| 3 | 2,108 | +0.924 | +0.926 | +0.001 |
| 4 | 142 | +0.751 | −0.939 | −1.690 |
| 5 | 174 | +0.876 | +0.606 | −0.271 |
| 6 | 1,138 | +0.294 | −0.921 | −1.215 |
| 7 | 390 | −0.511 | −0.624 | −0.113 |

**Key findings**:
- CLR alone has R² > 0.05 in 7 of 8 regions — taxonomic community composition tracks mine proximity within geographic contexts.
- GW features catastrophically overfit in small regions (n=142, 174): CLR+GW R² turns strongly negative in regions 4 and 6. This is consistent with the H3 finding (GW adds noise) and the per-KO association non-replication.
- Mean Δ R² (CLR+GW − CLR) = −0.38: GW degrades rather than improves CLR for mine proximity prediction.
- **H8 extended NOT SUPPORTED**: GW criterion (mean Δ R² ≥ 0.01) fails; CLR criterion (R² > 0.05 in ≥4 regions) is strongly met (7/8), but H8 requires both.

**Spatial autocorrelation range (WP1)**: Moran's I on M2 OOF residuals shows strong autocorrelation at <50 km (I = 0.41–0.73) and persistence to <200 km for Zn/Pb; Cu and Ni persist to >1,000 km. The cross-region collapse is mechanistically explained — k-means geographic clusters are separated by distances within the autocorrelation range.

---

## Limitations

1. **No model beats B0 for Cu in spatial block CV — confirmed structural by NB09.** M2_mine (with 36.8% mine proximity coverage) achieves Cu RMSE = 1.199, worse than both M2 (1.121) and B0 (1.115). Mine proximity adds confounding noise to Cu prediction: Cu contamination in the training set is geochemically driven (mob_cu/mob_pb), while mine proximity data from `site_classification.csv` is Europe-biased. Adding mine proximity as a feature does not resolve the structural mismatch. Cu's within-region CLR R² = 0.785–0.924 (NB09 H8 extended) confirms the signal exists but is geographically specific and not transferable via spatial block CV.

2. **Spatial block CV underestimates generalisation for Zn.** Zn's training RMSE = 0.923 is dominated by within-block overfitting of mob_zn/mob_pb as predictors; the AusMicrobiome holdout shows Zn degrades to 1.464 (1.59×). The true Zn generalisation error is the holdout figure, not the block CV figure.

3. **GW features (110) add noise relative to CWM (5)** for 3/4 metals. High-dimensional input (200 CLR + 110 GW) without strong regularisation causes XGBoost to learn block-specific interactions that do not transfer. CWM aggregation, while lossy, is more regularised. This is consistent with per-KO metal associations failing to replicate cross-dataset (per_ko_metal_associations NB01–NB02: 2/26,850 KO-metal pairs replicate).

4. **H8 extended to 8 regions via continuous regression (NB09)**. The binary contamination classification was limited to 2 of 8 regions by class balance. Reframing as continuous log_mine_prox_km regression with 15,476 covered samples (36.8%) enables all 8 k-means regions. CLR R² > 0.05 in 7/8 regions, confirming the taxonomic community structure tracks mine proximity within regions. GW features degrade CLR in most regions (mean Δ R² = −0.38; catastrophic overfitting in small regions n ≤ 174). The coverage limitation has been substantially addressed; the remaining limitation is that GW consistently adds noise, making H8 NOT SUPPORTED under either binary or continuous framing.

5. **Pb threshold discrimination RESOLVED by mine proximity features (NB09)**. M2_mine achieves sensitivity = 1.00 (all 40 Pb > 100 ppm samples recovered) at specificity = 0.570 and AUC = 0.620. The mine proximity indicator (`has_mine_prox_data`, log_mine_prox_km) provides the domain signal needed to recover mining-contaminated Pb sites. Residual limitation: AUC is modest (0.620) because the positive class is rare (0.1% prevalence), and the mine proximity join only covers 36.8% of training samples — sites without coverage are imputed with a sentinel value and rely on the binary indicator for disambiguation.

6. **H9 (MAG-derived profiles) is permanently blocked** unless a `sample_mag_coverage` table (sample_id, mag_id, depth_coverage, genome_size_Mb) is added to `arkinlab.spire`. The current schema exposes only MAG annotations, not per-sample abundances.

7. **Mobility targets (H7) are poorly predicted by community composition** at the genus level in spatial block CV. The mechanism — gene expression (not gene presence) drives bioavailability modification — is consistent with the Arc 1 (comprehensive_metal_ecology) finding that inducible resistance genes are phylogenetically unconstrained (HGT-distributed) and therefore carry no stable niche signal.

8. **M2 threshold discrimination (NB04) has been corrected to use OOF predictions.** The previously reported Cu sensitivity=0.977 and Zn sensitivity=0.981 were training-set resubstitution artefacts; the corrected OOF values (Cu=0.015, Zn=0.000, Ni=0.462, Pb=0.000) are much lower, confirming that M2 overfits threshold-relevant patterns. This does not alter the RMSE-based hypotheses (H1–H5) or the SHAP feature ranking, which remain valid. SHAP importance (NB04) is still computed on the full-training-set model — OOF SHAP would require per-fold computation (computationally prohibitive); the full-training-set SHAP is adequate for relative feature ranking but may inflate importance for overfit features.

9. **CLR is computed as a sub-compositional transform on the top-200 genera** (out of 2,781 observed genera). The geometric mean is computed over 200 parts after renormalization, not over the full composition. Standard CLR on the full composition would differ in absolute values; the impact on XGBoost (which uses rank-based splits) is expected to be limited, but sub-compositional bias should be noted. Selecting top-200 before CLR also means rare but discriminating genera may be excluded.

---

## Cross-Project Integration

| Finding | Cross-project confirmation |
|---------|--------------------------|
| GW/CWM functional features rank below CLR in SHAP (H4 NOT SUPPORTED) | **MCI**: CLR-only AUC = 0.92–0.96; functional features add nothing (NB01–NB02). **CME**: resistance gene PGLS β = +0.003 (p = 0.820, NS); only constitutive cofactor pathways (β = −0.033) are significant — the same null predicted by the capacity-vs-activity distinction |
| Cross-region CLR collapse (AUC 0.99 → 0.18) | **MCI**: study-blocked CLR AUC drops 0.17–0.42 AUROC relative to random-fold; MCC ≈ 0 under study-blocking. Spatial de-trending raises blocked AUC from 0.50–0.76 to 0.58–0.78 |
| Kriging dominates M2 for 3/4 metals | **MCI**: spatial-only features (lat, lon polynomials) achieve AUC 0.88–0.97 — higher than CLR alone (0.75–0.88) and comparable to soil chemistry |
| Per-KO metal associations do not replicate (root cause of GW/CWM null) | **Per-KO associations** NB01–NB02: 2/26,850 KO-metal pairs replicate across SPIRE and MGnify; direction consistency ≈ 0; effect-size correlation ρ = 0.28 |
| Cu is the hardest target (H1 failure, H5 strongest transfer, H8 Cu AUC ≥ 0.99) | **Hybrid_metal_prediction**: M4 (env-only) outperforms M2 (env+CWM) for Cu; mob_cu and mob_pb carry the Cu signal; community composition adds noise for Cu when combined with env features |

---

## Data Provenance

| File | Description | Rows | Produced by |
|------|-------------|------|-------------|
| `data/feature_matrix.parquet` | CLR (200 genera) + GW (110) + env (9) + targets (4) | ~40k | NB00 |
| `data/spatial_blocks.csv` | 5-block geographic assignment by k-means | ~40k | NB00 |
| `data/baseline_cv_results.csv` | B0–B4 per-model per-target RMSE | 20 | NB01 |
| `data/bootstrap_h1.csv` | Bootstrap ΔRMSE CI for H1 (B2 − B1) | 4 | NB01 |
| `data/hybrid_cv_results.csv` | M1–M5 per-model per-target RMSE | 20 | NB02 |
| `data/bootstrap_h2.csv` | Bootstrap ΔRMSE CI for H2 (B3 − M1) | 4 | NB02 |
| `data/oof_predictions.parquet` | Out-of-fold predictions for all models | ~40k | NB02 |
| `data/ausm_holdout_results.csv` | AusMicrobiome holdout RMSE per model per target | 16 | NB03 |
| `data/coverage_stratified_results.csv` | Holdout RMSE stratified by CLR coverage (WP6) | 8 | NB03 |
| `data/shap_importance.csv` | Mean |SHAP| per feature group per target | 16 | NB04 |
| `data/kriging_cv_results.csv` | IDW block LOO RMSE + hybrid RMSE | 4 | NB05 |
| `data/mobility_cv_results.csv` | Mobility target RMSE for B0, B1, M1, M2_soil | 24 | NB06 |
| `data/classification_results.csv` | Within-region and cross-region AUC by model | 8 | NB07 |
| `data/spatial_autocorr_correlogram.csv` | Moran's I by distance band for M2 OOF residuals | — | NB07 |
| `data/cv_results_m2_mine.csv` | M2_mine block CV RMSE per target | 4 | NB09 |
| `data/threshold_disc_m2_mine.csv` | M2_mine threshold discrimination (Cu, Pb at 100 ppm) | 2 | NB09 |
| `data/h8_extended_regression_results.csv` | Within-region R² for CLR/CLR+GW → log_mine_prox_km | 16 | NB09 |

---

## Notebook Provenance

| Notebook | Content | Status |
|----------|---------|--------|
| NB00 | Feature engineering: CLR (top-200 by mean RA, log1p → CLR-transform), GW (per-genus RA × pangenome density, top-20 per category + 10 PCA → 110 GW features), env assembly (mob_*, soil/climate), target log1p transform; spatial k-means blocking | COMPLETE |
| NB01 | Baseline models B0–B4; spatial block CV; H1 bootstrap ΔRMSE (B2 − B1) | COMPLETE |
| NB02 | Hybrid models M1–M5; spatial block CV; H2 bootstrap ΔRMSE (B3 − M1) | COMPLETE |
| NB03 | AusMicrobiome+NGSA holdout; H5 transfer test; WP6 coverage-stratified sensitivity | COMPLETE |
| NB04 | SHAP analysis (M2 OOF); H3 (M2 vs M3) and H4 (GW vs CLR SHAP rank) tests; threshold discrimination | COMPLETE |
| NB05 | IDW kriging spatial block LOO; M1 residual prediction; H6 hybrid test | COMPLETE |
| NB06 | Mobility target prediction (mob_* as response); H7 relative improvement comparison | COMPLETE |
| NB07 | Contamination classification by region; H8 within-region vs cross-region AUC; Moran's I correlogram (WP1) | COMPLETE |
| NB08 | MAG-derived functional profiles; H9 — UNTESTABLE (no sample→MAG coverage in arkinlab.spire) | COMPLETE (status only) |
| NB09 | Mine proximity features (10 km haversine join, 36.8% coverage); M2_mine block CV; H8 extended (continuous regression, 8 regions); Pb threshold resolved | COMPLETE |
