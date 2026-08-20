# Research Plan: Community Composition Prediction

## Core question

Does high-dimensional microbial taxonomy (CLR-transformed genus relative abundances) predict soil metal concentrations, and do genus-weighted functional features (preserving genus-level resolution) improve beyond CLR composition alone?

---

## Pre-specified hypotheses and success criteria

### H1 — CLR taxonomy improves prediction beyond cheap geochem

**Comparison**: B1 (CLR only, XGBoost) vs B2 (pH + lat/lon, ridge)  
**Test**: Bootstrap ΔRMSE CI, B2 − B1 (positive = B1 is better)  
**Success**: ΔRMSE CI excludes 0 in the positive direction for ≥2 of 4 target metals  
**Fallback**: Report conditional — CLR adds nothing once spatial location + pH known  
**Interpretation**: If H1 fails, microbial composition at genus level does not encode metal load beyond the geochemical gradient; community assembly is reactive, not predictive

---

### H2 — Genus-weighted functional features improve beyond CLR + geochem

**Comparison**: M1 (CLR + genus-weighted functional) vs B3 (CLR + pH + lat/lon)  
**Test**: Bootstrap ΔRMSE CI, B3 − M1  
**Success**: CI excludes 0 in the positive direction for ≥2 of 4 metals  
**Fallback**: Genus-weighted functional densities add no information beyond what genus identity encodes; functional load is already implicit in taxonomic composition  
**Interpretation**: H2 passage would mean functional gene investment (at genus resolution) is predictive beyond which genera are present — i.e., gene content predicts metal load independently of taxonomy

---

### H3 — Genus-weighted representation outperforms CWM

**Comparison**: M2 (CLR + genus-weighted + env) vs M3 (CLR + CWM + env)  
**Test**: Direct RMSE comparison (spatial block CV); no bootstrap required  
**Success**: M2 RMSE < M3 RMSE for ≥3 of 4 metals  
**Fallback**: CWM is sufficient; genus-level functional resolution adds no information beyond the category aggregate  
**Interpretation**: M2 > M3 would mean the identity of which genera contribute most to functional load is predictive — not just the total community-level load. This would have implications for pangenome curation: high-resolution genus×function matrices are worth maintaining

---

### H4 — Genus-weighted functional categories rank above CLR taxonomy in SHAP

**Comparison**: Sum of GW SHAP importance vs sum of CLR SHAP importance for M2  
**Test**: Category aggregation of mean |SHAP| values from TreeExplainer  
**Success**: Sum GW SHAP > Sum CLR SHAP for ≥2 of 4 metals  
**Interpretation**: Positive result means functional gene content (encoded at genus level) dominates over mere genus identity in driving metal prediction. Negative result (CLR > GW) means taxonomy encodes most of the predictive signal, and functional annotation adds little

---

### H5 — CLR models generalise to AusMicrobiome holdout

**Comparison**: M2 holdout RMSE vs M2 training RMSE (spatial block CV)  
**Holdout**: AusMicrobiome + NGSA (1,019 Australian soil samples)  
**Test**: Holdout/training RMSE ratio ≤ 1.1  
**Success**: Ratio ≤ 1.1 for ≥2 of 4 metals  
**Fallback**: If ratio > 1.5, geographic domain shift is catastrophic; evaluate whether CLR coverage (fraction of Australian genera in training set) predicts per-sample error  
**Caveat**: AusMicrobiome CLR features are restricted to the top-200 training genera; genera unique to Australia will be absent. Coverage gap differs from `hybrid_metal_prediction` (pangenome gap) in that all genera can be CLR-transformed — the gap only affects genus-weighted features

---

## Analysis plan by notebook

### NB00: Feature matrix — **SCAFFOLDED**

1. Load `hmp_feature_matrix.parquet` from `hybrid_metal_prediction` as base (env features + CWM + targets for 42,037 samples)
2. Load genus RA from Spark (`arkinlab.microbeatlas.otu_counts_long` × `otu_metadata`), restricted to base sample IDs
3. Select top-200 genera by mean RA; CLR-transform → 200 `clr_{genus}` features
4. Compute genus-weighted functional features (top-20 per category + 10 PCA components)
5. Join CLR + GW features to base by sample_id
6. Save `feature_matrix.parquet`, `genus_ra.parquet`, `coverage_report.csv`

**Expected shape**: 42,037 × ~340 columns (200 CLR + 110 GW + ~30 env/CWM/target cols)

### NB01: Taxonomy baseline — **SCAFFOLDED**

1. Load feature matrix + spatial_blocks.csv
2. B0 spatial block CV (intercept-only)
3. B1 (CLR, XGBoost), B2 (pH+lat/lon, ridge), B3 (CLR+pH+lat/lon, XGBoost) spatial block CV
4. Bootstrap ΔRMSE for H1 (B2 − B1)
5. Save `cv_results_baselines.csv`, `bootstrap_h1.csv`
6. RMSE comparison plot

### NB02: Functional augmentation — **SCAFFOLDED**

1. Load feature matrix + spatial_blocks.csv + baseline results
2. B4 (CWM, XGBoost), M1 (CLR+GW, XGBoost), M2 (CLR+GW+env, XGBoost), M3 (CLR+CWM+env, XGBoost) spatial block CV
3. Bootstrap ΔRMSE for H2 (B3 − M1)
4. H3: direct M2 vs M3 comparison
5. Collect OOF predictions for all models
6. Save `cv_results_models.csv`, `bootstrap_h2.csv`, `oof_predictions.parquet`

### NB03: External validation — **SCAFFOLDED**

1. Fit final models on full training data: B0, B1, M1, M2
2. AusMicrobiome holdout:
   - Load OTU counts → genus RA (via BASE_16S_taxonomy.csv)
   - CLR transform restricted to training top-200 genera
   - Genus-weighted features aligned to training GW columns
   - CSU mobility features via Spark
   - NGSA metal targets
3. Evaluate models; H5 transfer ratio test
4. Save `holdout_results.csv`, holdout feature matrix

### NB04: Interpretation — **SCAFFOLDED**

1. Fit M2 on full training for each target; compute SHAP (TreeExplainer)
2. Aggregate SHAP by category (CLR, GW_*, Env_*, Geochem)
3. H4: GW SHAP vs CLR SHAP sum comparison
4. Top-20 CLR genera per metal (discovery)
5. SHAP category bar plots
6. Threshold metrics at regulatory cutoffs
7. Save `shap_importance.csv`, `shap_by_category.csv`, `threshold_metrics.csv`

---

## Data access notes

- **MicrobeAtlas OTU table**: `arkinlab.microbeatlas.otu_counts_long` (JupyterHub Spark)
- **OTU metadata**: `arkinlab.microbeatlas.otu_metadata` (genus_lower column)
- **Base feature matrix**: `data/hmp_feature_matrix.parquet` (symlink to hybrid_metal_prediction)
- **Spatial blocks**: `data/spatial_blocks.csv` (symlink to hybrid_metal_prediction)
- **AusMicrobiome data**: `microbeatlas_metal_ecology/data/aus_microbiome/`
- **CSU mobility grid**: `arkinlab.envdbs.csu_metal_mobility_grid` (Spark only)

---

## Caveats pre-specified

1. CLR transform of sparse data (many zero genera) requires a pseudocount. All genus-RA columns use uniform pseudocount 1e-6 before CLR. This is consistent across training and holdout.
2. Restricting to top-200 genera by mean RA in the training set introduces selection bias: genera only present in Australian soils will have no CLR features in the holdout. This limits H5 generalisability to the shared taxonomic space.
3. Genus-weighted features use the same top-N selection as training — holdout genera not in the training top-20 per category will be absent. Coverage gap affects genus-weighted but not CLR features.
4. The `hybrid_metal_prediction` feature matrix does not include genus RA — only CWM. NB00 must re-load from Spark and join. Spark job may be slow for 42k samples.
5. OOF predictions for B3 are needed for H2 bootstrap but B3 is run in NB01. If OOF saving fails in NB01, re-run with `return_oof=True` before running NB02.

---

## Output files

| File | Content |
|------|---------|
| `data/feature_matrix.parquet` | Sample × [CLR + GW + env + CWM + targets] |
| `data/genus_ra.parquet` | Sample × genus RA (raw, for reuse) |
| `data/coverage_report.csv` | CWM coverage fraction per sample |
| `data/cv_results_baselines.csv` | B0–B3 per-fold spatial CV RMSE |
| `data/cv_results_models.csv` | B4, M1–M3 per-fold spatial CV RMSE |
| `data/bootstrap_h1.csv` | H1 bootstrap ΔRMSE CI |
| `data/bootstrap_h2.csv` | H2 bootstrap ΔRMSE CI |
| `data/oof_predictions.parquet` | OOF predictions for all models |
| `data/holdout_results.csv` | AusMicrobiome+NGSA holdout RMSE |
| `data/shap_importance.csv` | Mean |SHAP| per feature per target (M2) |
| `data/shap_by_category.csv` | SHAP summed by category |
| `data/threshold_metrics.csv` | Sensitivity/specificity at regulatory thresholds |
| `data/mobility_prediction_results.csv` | NB06: spatial CV RMSE for mobility and total targets |
| `data/kriging_residual_results.csv` | NB05: kriging OOF and hybrid RMSE |
| `data/regional_classification_results.csv` | NB07: within-region and cross-region AUC |
| `data/metagenomic_prediction_results.csv` | NB08: MAG-derived vs 16S-inferred GW spatial CV RMSE |

---

## Advanced prediction strategies (post-hoc exploratory)

These four directions were added after completing NB00–NB04. All are explicitly **exploratory and post-hoc**: they were motivated by observed results (spatial heterogeneity dominates, total metal is a noisy microbial signal, env features dominate SHAP). They are not pre-registered confirmatory hypotheses. Positive results warrant a separate pre-registered follow-up.

---

### H6 — Kriging-omics hybrid outperforms both components (NB05)

**Motivation**: Spatial block CV fails because between-block distributional shift dominates error. Ordinary kriging captures the spatial trend from nearby samples; the omics model only needs to predict the local residual deviation.

**Design**:
- Ordinary kriging per metal (pykrige, or IDW fallback): spatial block LOO
- Kriging residual = observed − kriging block prediction
- M1 (CLR + GW) spatial block CV on residuals
- Hybrid = kriging prediction + M1 residual prediction

**Success criterion**: Hybrid RMSE < min(kriging RMSE, M2 RMSE) for ≥2 of 4 metals.

**If null**: Document the decomposition RMSE table. Note whether kriging alone beats M2 alone (implication: spatial interpolation is the dominant signal).

**Notebook**: `notebooks/05_kriging_hybrid.ipynb`

---

### H7 — Omics predicts bioavailable metal fractions better than total ppm (NB06)

**Motivation**: Total metal concentration is dominated by mineral-bound fractions that microbes cannot access. The CSU PF1 mobility fractions (already in feature_matrix as `mob_cu`, `mob_pb`, `mob_as`, `mob_cd`, `mob_cr`, `mob_hg`) represent the mobile/exchangeable fraction microbes respond to.

**Design**:
- Targets A: `mob_cu`, `mob_pb`, `mob_as`, `mob_cd`, `mob_cr`, `mob_hg` (PF1 fractions, 0–0.5)
- Targets B: `log_Cu_ppm`, `log_Zn_ppm`, `log_Pb_ppm`, `log_Ni_ppm`
- Feature sets: B0, B1 (CLR), M1 (CLR+GW), M2_soil (CLR+GW+soil/climate, no mob_*)
- mob_* columns are EXCLUDED as predictors when predicting mob_* targets

**Success criterion**: Relative RMSE improvement (B0 − model) / B0 is larger for mobility than total concentration for ≥2 of 2 overlapping metals (Cu, Pb) using M1.

**Notebook**: `notebooks/06_bioavailable_targets.ipynb`

---

### H8 — Within-region binary classification of contaminated vs reference (NB07)

**Motivation**: Regression of total metal concentration fails under spatial distributional shift. Binary classification (contaminated vs reference) is a coarser signal that may be more robust within biogeographic regions. Contamination labels from `metal_contamination_response` project (proximity-based: mine/TRI/NPL).

**Design**:
- Labels: `../metal_contamination_response/data/00_site_classification.csv`
- Regions: k-means (k=8–12) on lat/lon; select k maximising usable region count
- Models: B0 (class prior), CLR-only, M1 (CLR+GW), M2 (CLR+GW+env)
- Within-region: 5-fold stratified CV per region
- Cross-region: train on N-1 regions, test on held-out

**Success criterion**: ≥2 regions with within-region AUC > 0.70 for M1 or M2, AND GW adds ≥0.02 AUC over CLR-only in ≥1 region.

**Notebook**: `notebooks/07_regional_classification.ipynb`

---

### H9 — Direct metagenomic functional profiles outperform 16S-inferred genus-weighted features (NB08)

**Motivation**: GW features (NB02) use a 16S-to-pangenome bridge that introduces three sources of noise: (1) OTU → genus mapping error, (2) genus → pangenome representativeness, (3) aggregation over pan-genome rather than actual MAGs in each sample. SPIRE MAGs with eggNOG annotations can provide direct per-sample functional profiles.

**Design**:
- Source: `arkinlab.spire.eggnog_annotations_spire` (per-MAG eggNOG annotations)
- Per-Mb gene density per functional category per sample, abundance-weighted
- Models: B0, GW (16S-inferred, NB02), MAG (direct), MAG+CLR
- Same spatial block CV as NB01–NB02
- Restricted to samples with both SPIRE shotgun coverage and HMP 16S data

**Success criterion**: MAG-derived functional model RMSE < GW-only RMSE for ≥2 of 4 metals.

**Important caveat**: SPIRE coverage may be a biased subset. Report the intersection size and its geographic/environmental distribution relative to the full training set.

**Notebook**: `notebooks/08_metagenomic_profiles.ipynb`
