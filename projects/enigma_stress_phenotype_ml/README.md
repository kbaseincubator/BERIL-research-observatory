# Per-Stressor CatBoost ML Pipeline for Predicting Metal/Antibiotic Stress Phenotypes

## Scientific Goal

Predict which ENIGMA bacterial isolates will exhibit fitness defects under metal and antibiotic stress based on protein sequence features alone. This is Part 4 of a PhD thesis focused on predictive modeling of stress response phenotypes using machine learning.

## Pipeline Overview

The complete pipeline comprises 9 Jupyter notebooks executed sequentially:

1. **NB01 — Data Preparation**: Extract labeled fitness data from the FitnessBrowser Spark database for 10 metal stressors (Zn, Cu, Cd, Co, Ni, Cr, Hg, Mn, Fe, Se, Al) and 17 antibiotic compounds across ENIGMA isolates.

2. **NB02 — Sequence Integration**: Download and integrate protein sequences for all ENIGMA isolates from the genome depot, indexed by protein_id.

3. **NB03 — Feature Engineering**: Compute four complementary feature sets:
   - **ESM-2 embeddings**: 320-dimensional contextual embeddings from a large pre-trained language model (facebook/esm2_t6_8M_UR50D)
   - **k-mer frequencies**: 2-mer and 3-mer compositional features (capturing local sequence patterns)
   - **Physicochemical properties**: Mean values of 7 AAindex properties (hydrophobicity, bulkiness, polarity, charge, isoelectric point, secondary structure propensity, solvent accessibility)
   - **One-hot encoding**: Direct 20-dimensional amino acid composition

4. **NB04 — Feature Evaluation**: Select the best-performing feature combination via cross-validation (currently: aa+kmer2, avg AUC 0.656).

5. **NB05 — Per-Stressor Model Training**: Train independent CatBoost classifiers for each stressor using balanced class weighting and Platt calibration. Use a held-out calibration set for threshold tuning.

6. **NB06 — LOGO Cross-Validation**: Leave-One-Genus-Out evaluation to assess generalization to unseen bacterial taxa.

7. **NB07 — Ensemble Model Training**: Train a meta-model combining predictions from multiple per-stressor models.

8. **NB08 — General Essentiality Model**: Train a single multi-label model for simultaneous prediction across all stressors.

9. **NB09 — Isolate Prediction**: Apply trained models to predict stress phenotypes for new ENIGMA isolates; rank candidates by predicted risk.

## Requirements

- **NB01**: Spark access (requires cluster environment; queries FitnessBrowser)
- **NB03**: GPU or high-memory CPU for ESM-2 embeddings (~6-8 GB RAM per batch)
- **NB04–NB09**: Local execution; CatBoost + scikit-learn sufficient

## Data Files

- `data/labeled_pd.parquet`: ENIGMA isolate × stressor binary fitness labels
- `data/features_*.parquet`: Pre-computed feature matrices (aa, kmer2, kmer3, onehot, physicochemical, blosum62, esm2)
- `data/best_feature_combination.json`: Selected feature set for training
- `data/models/`: Trained per-stressor CatBoost models (.cbm) and Platt calibrators (.pkl)
- `data/best_thresholds.json`: Tuned decision thresholds per stressor (created by fixed NB05)

## Known Issues and Status

**Critical**: All metal stressor models currently predict all-negative (Sensitivity=0.0, F1=0.0, AUC≈0.5–0.6) due to severe class imbalance. High apparent accuracy (~99.7%) is driven entirely by the majority-negative class and does not reflect a useful predictor.

Antibiotic stressors show slightly better performance (AUC 0.65–0.88) but still mostly zero sensitivity.

NB09 isolate prediction cannot produce meaningful results until class imbalance is addressed.

**Pending Fixes**:
- Add `class_weights='Balanced'` to all CatBoostClassifier instantiations in NB05
- Implement threshold tuning using validation set F1 maximization
- Replace hard-coded `predict()` calls with threshold-aware predictions
- Rerun NB05 → NB06 → NB07 after fixes

See `REPORT.md` for detailed analysis and findings.

## Author

Heather MacGregor  
Lawrence Berkeley National Laboratory

## References

- ESM-2: Rao et al. (2023) "Protein language models enable predictive biology on biosafety risks" bioRxiv
- CatBoost: Dorogush et al. (2018) "CatBoost: gradient boosting with categorical features support"
