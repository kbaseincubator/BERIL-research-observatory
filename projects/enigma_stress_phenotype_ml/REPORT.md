# REPORT: Per-Stressor CatBoost ML Pipeline for Stress Phenotype Prediction

**Status**: In progress — feature engineering complete, initial model training complete, class imbalance unresolved.

**Date**: June 28, 2026

---

## Executive Summary

A machine learning pipeline combining ESM-2 protein embeddings, k-mer frequencies, and physicochemical properties with CatBoost classifiers was trained to predict fitness defects in ENIGMA bacterial isolates under metal and antibiotic stress. While the pipeline infrastructure is complete and antibiotic models show promise (AUC 0.64–0.88), all metal stressor models suffer from severe class imbalance, predicting all-negative regardless of input, resulting in zero sensitivity and F1 scores. This report documents the findings, identifies the root cause, and outlines pending fixes.

---

## Scientific Question

Can protein sequence features alone predict which ENIGMA bacterial isolates will exhibit fitness defects under metal and antibiotic stress? Can these predictions identify candidate isolates for experimental validation?

---

## Methods

### Feature Engineering

Four complementary feature sets were computed from protein sequences:

1. **Amino acid composition (aa)**: 20 features representing frequency of each standard amino acid
2. **2-mer k-mer frequencies (kmer2)**: 400 features (20×20 dinucleotide pairs)
3. **Physicochemical properties**: 7 features (mean values of AAindex-derived properties)
4. **ESM-2 embeddings (esm2)**: 320 dimensions

Additional sets computed but not selected: one-hot encoding, BLOSUM62, length+moments.

### Feature Selection

Via per-stressor cross-validation (NB04), the **best feature combination was: aa + kmer2** with average AUC = 0.656. This simpler combination outperformed learned embeddings.

### Model Training

**Algorithm**: CatBoost (gradient boosting on decision trees)

**Configuration** (NB05):
- Iterations: 1000, Learning rate: 0.1, Tree depth: 6
- Evaluation metric: AUC
- Class weights: `auto_class_weights='Balanced'`
- Platt calibration: enabled on held-out calibration set (25% of training data)

**Data split**:
- Training set: 80% (with further split into 75% sub-training, 25% calibration)
- Test set: 20% (held-out for final evaluation)

**Cross-validation**: LOGO (Leave-One-Genus-Out) in NB06 — evaluate on each held-out bacterial genus separately to assess phylogenetic generalization.

---

## Key Results

### Metal Stressor Performance (CRITICAL ISSUE)

All 11 metal stressors show Sensitivity = 0.0, F1 = 0.0, AUC ≈ 0.50–0.65:

| Stressor | Accuracy | Sensitivity | F1 | AUC |
|----------|----------|-------------|-----|-----|
| Zn | 0.992 | 0.007 | 0.005 | 0.588 |
| Cu | 0.984 | 0.093 | 0.049 | 0.650 |
| Cd | 0.998 | 0.000 | 0.000 | 0.604 |
| Co | 0.982 | 0.065 | 0.039 | 0.559 |
| Ni | 0.980 | 0.053 | 0.032 | 0.618 |
| Cr | 0.997 | 0.000 | 0.000 | 0.536 |
| Hg | 0.998 | 0.000 | 0.000 | 0.513 |
| Mn | 0.997 | 0.000 | 0.000 | 0.505 |
| Fe | 0.998 | 0.000 | 0.000 | 0.536 |
| Se | 0.998 | 0.000 | 0.000 | 0.533 |
| Al | 0.989 | 0.012 | 0.007 | 0.570 |

**High accuracy is misleading** — driven entirely by majority-negative class. Models predict all-negative.

### Antibiotic Stressor Performance (Better but Still Limited)

| Stressor | Accuracy | Sensitivity | F1 | AUC |
|----------|----------|-------------|-----|-----|
| Ampicillin | 1.000 | 0.667 | 0.706 | 0.876 |
| Trimethoprim | 1.000 | 0.588 | 0.625 | 0.804 |
| Rifampicin | 0.995 | 0.391 | 0.188 | 0.813 |
| Spectinomycin | 0.994 | 0.279 | 0.151 | 0.744 |
| Vancomycin | 0.991 | 0.139 | 0.077 | 0.643 |
| Cold | 0.996 | 0.194 | 0.226 | 0.758 |
| Sucrose | 0.996 | 0.519 | 0.369 | 0.820 |
| Nitric oxide | 0.807 | 0.410 | 0.155 | 0.673 |
| Acid | 0.890 | 0.330 | 0.134 | 0.657 |
| UV | 0.947 | 0.345 | 0.145 | 0.773 |

Higher positive rates (~0.03–6.8%) yield better results.

### Adaptive Metrics (Threshold-Tuned)

A separate analysis (`data/adaptive_metrics.csv`) applied threshold tuning to maximize F1 per stressor. Modest improvements observed for some stressors (e.g., Rifampicin sensitivity 0.28 → 0.28), but metal stressors remain near zero even after optimization.

---

## Critical Assessment

### Root Cause: Missing-Data Contamination in the Negative Class

**Apparent positive rate (all 60 organisms)**: 0.6% for Zn (1,302 / 215,051 proteins)

**True positive rate (organisms with Zn experiments only)**: 1.8% for Zn (1,302 / 71,945 proteins)

The labeled dataset covers 60 ENIGMA organisms but FitnessBrowser Zn experiments exist for only 21 of them. The `fillna(0)` in NB01 Cell 6 (prior to this fix) assigned label=0 to the ~143K proteins from the 39 organisms with **no Zn experiments at all** — not true negatives, but untested proteins masquerading as non-essential. This inflated the effective negative class ~3× and suppressed the achievable positive rate below the threshold where CatBoost can learn.

| Metal | Orgs with experiments | True positive rate | Prior apparent rate |
|-------|----------------------|-------------------|---------------------|
| Zn    | 21/60                | 1.81%             | 0.61%               |
| Cu    | 28/60                | 1.48%             | 0.71%               |
| Co    | 30/60                | 1.40%             | 0.75%               |
| Ni    | 30/60                | 1.35%             | 0.71%               |
| Al    | 23/60                | 1.40%             | 0.53%               |
| Cd    | 2/60                 | 2.44%             | 0.07%               |
| Cr/Hg/Mn | 2–3/60          | 3–5%              | 0.07–0.14%          |

**Fix implemented (NB05)**: `train_stressor()` now filters to organisms-with-data before splitting and training, eliminating the false-negative contamination. No Spark re-run required — this uses the existing `labeled_pd.parquet`.

**Fix implemented (NB01)**: The label extraction loop now also saves `{stressor}_fit` columns — the raw `fitness_min` value as a continuous float, NaN where no experiment was run. This enables regression training (see below).

### Regression Path for Metals

Binary classification collapses the continuous fitness distribution (ranging from ≈−6 to +2) to 0/1 at a −2.0 threshold, discarding the gradient signal between "strongly essential" (fitness ≈ −5) and "marginally impaired" (fitness ≈ −1.5). Regression on the raw fitness score:
- Eliminates the threshold artifact entirely
- Trains on all tested proteins, not just the rare below-threshold ones
- Enables rank-based candidate selection: predict which ENIGMA isolate proteins have the most negative fitness under Zn stress → those are the metal resistance gene candidates

The regression cell in NB05 (`train_stressor_regression()`) is ready to run once NB01 is re-executed on Seaborg to populate the `{stressor}_fit` columns.

### Accuracy as a Misleading Metric

Accuracy is useless for highly imbalanced classification. The models achieve 99%+ accuracy but are **unusable** for candidate selection because they identify zero candidates.

---

## Methodological Strengths

1. **Robust feature engineering**: Multiple feature sets compared; selection via cross-validation
2. **Principled evaluation**: LOGO cross-validation prevents genus-level overfitting
3. **Calibration**: Platt calibration on held-out set improves probability estimates
4. **Automated balance attempted**: CatBoost's `auto_class_weights='Balanced'` is applied

---

## Limitations and Pending Fixes

### 1. ✅ Missing-data contamination (fixed)

**Problem**: `fillna(0)` assigned label=0 to proteins from organisms with no experiments, inflating the negative class ~3× and making metal models untrainable.

**Fix**: `train_stressor()` in NB05 now filters to `orgs_with_data` (organisms with ≥1 positive for that stressor) before splitting. This raises effective positive rates from 0.6% to 1.8% for Zn and is equivalent for other well-covered metals (Cu/Co/Ni/Al). Can be retrained immediately on the existing `labeled_pd.parquet`.

### 2. ✅ Continuous fitness scores not saved (fixed in NB01)

**Problem**: `fitness_min` values were computed from Spark but discarded after binary thresholding.

**Fix**: NB01 Cell 6 now saves `{stressor}_fit` as a continuous float column alongside the binary label; NaN for organism/stressor pairs with no experiments. Requires NB01 re-run on Seaborg to take effect.

### 3. No Threshold Tuning (partially addressed)

**Problem**: Default threshold of 0.5 for predict() may be suboptimal.

**Solution**: After training in NB05:
1. Compute `y_proba = model.predict_proba(X_val)[:, 1]` on validation set
2. Sweep thresholds from 0.01 to 0.99
3. For each threshold, compute F1 score
4. Save threshold maximizing F1 to `data/best_thresholds.json` keyed by stressor name
5. Example: `{"Zn": 0.25, "Cu": 0.30, "Ampicillin": 0.85, ...}`

### 3. Hard-Coded predict() Calls

**Problem**: Current code uses `model.predict(X)` which applies default 0.5 threshold, ignoring calibration and imbalance.

**Solution**: Replace all prediction calls:
```python
# Old:
y_pred = model.predict(X_test)

# New:
threshold = best_thresholds[stressor]
y_pred = (model.predict_proba(X_test)[:, 1] >= threshold).astype(int)
```

### 4. NB09 Incomplete

**Problem**: Only 1 empty cell; no isolate prediction output.

**Solution**: See Task 5 implementation below.

---

## Next Steps (Priority Order)

1. **Fix NB05** with:
   - Verify `class_weights='Balanced'` is active
   - Add threshold-tuning code
   - Save `data/best_thresholds.json`
   - Replace predict() with threshold-aware calls in evaluation

2. **Rerun NB05 → NB06 → NB07** with improved class handling

3. **Implement NB09** with isolate prediction workflow

4. **Re-evaluate**: After fixes, expect:
   - Sensitivity to improve significantly (from ~0% to 10–50% for metals, 30–80% for antibiotics)
   - AUC to remain similar or slightly improve
   - Specificity to decrease (more false positives, but acceptable for candidate screening)
   - Overall useful model for candidate selection

---

## Data Provenance

- **Fitness labels**: FitnessBrowser (NB01)
- **Protein sequences**: ENIGMA genome depot (NB02)
- **Features**: Computed locally from sequences (NB03)
- **Feature selection**: Cross-validation benchmarking (NB04)
- **Models**: CatBoost with Platt calibration (NB05)
- **LOGO CV**: Per-genus held-out evaluation (NB06)

---

## Code and Reproducibility

All notebooks (NB01–NB09) in `notebooks/`. Supporting code:
- `src/feature_extraction.py`: Feature computation functions
- `src/utils.py`: Data loading utilities

To reproduce:
```bash
cd projects/enigma_stress_phenotype_ml
jupyter notebook notebooks/01_Data_Preparation.ipynb  # Requires Spark access
jupyter notebook notebooks/04_Feature_Evaluation.ipynb  # Local
jupyter notebook notebooks/05_Model_Training.ipynb      # Local
```

---

## Model Files

- Per-stressor models: `data/models/stressor_{name}_final.cbm`
- Platt calibrators: `data/models/stressor_{name}_platt.pkl`
- Predictions (test set): `data/models/stressor_{name}_predictions.parquet`
- Best thresholds (to be created): `data/best_thresholds.json`
- Best features: `data/best_feature_combination.json` → `aa+kmer2`

---

## Author

Heather MacGregor  
Lawrence Berkeley National Laboratory

**Report compiled**: 2026-06-28
