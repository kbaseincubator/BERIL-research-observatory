# Cross-Stressor Conditional Essentiality Prediction in ENIGMA Isolates

## Research Question

Can amino acid composition and k-mer features alone predict whether a protein is conditionally essential (fitness < −2 under any tested condition) across phylogenetically diverse ENIGMA bacterial isolates, and does this cross-stressor signal generalize across genera?

## Status

Completed — Sequence composition features predict cross-stressor conditional essentiality in ENIGMA isolates (test AUC=0.659, LOGO AUC=0.618±0.037 across 27 genera, supporting genus-level generalization of housekeeping essentiality signals).

(Submission pending; see SUBMISSION_FAILED.md.)

## Authors

Heather MacGregor (ORCID: 0000-0003-1112-3009)  
Lawrence Berkeley National Laboratory

## Relationship to enigma_stress_phenotype_ml

This project is distinct from `enigma_stress_phenotype_ml` in three ways:
1. **Label**: binary union (essential in ANY stressor) vs. per-stressor continuous fitness regression
2. **Model**: single cross-stressor classifier vs. 11 separate metal models
3. **Question**: cross-stressor integration of fitness vulnerability vs. metal-specific ranking

Both use the same FitnessBrowser source and organism-stratified/genus-level LOGO evaluation.

## Methodological Corrections from refocus

A prior implementation in `projects/refocus/` had five critical flaws (documented in audit 2026-06-29):
1. Train/test split was protein-level, not organism-stratified — organisms appear in both sets
2. LOGO was leave-one-**organism**-out (LOOO), not leave-one-**genus**-out as claimed
3. Positive rate claimed as 71% (biologically implausible); actual rate is ~4% for union label
4. Claimed LOGO AUC=0.960, MCC=0.722 — not found in any executed notebook output
5. "General essentiality model" (EG_Prediction.ipynb) was never executed to completion

This project corrects all five issues.

## Pipeline Overview

1. **NB01 — Data Preparation** (local): Loads `enigma_stress_phenotype_ml/data/labeled_pd.parquet`
   (215,051 proteins, 60 ENIGMA organisms); derives union binary label (fitness < −2 in any stressor);
   applies manual genus mapping (ENIGMA strain codes don't use binomial names); organism-stratified
   80/20 split (48 train / 12 test organisms, zero organism overlap verified).

2. **NB02 — Feature Loading** (local): Loads precomputed aa (20 cols) + kmer2 (400 cols) features
   from `enigma_stress_phenotype_ml/data/` via positional alignment (row-aligned with labeled_pd);
   fits standardization scaler on training set only; saves `.npy` arrays.

3. **NB03 — Model Training and LOGO Evaluation** (local): Trains CatBoost binary classifier with
   `scale_pos_weight = 6.44` class balancing; true genus-level LeaveOneGroupOut (32 genera, 27
   reliable with ≥5 positive proteins); test set AUC = 0.659; LOGO AUC = 0.618 ± 0.037.

## Data Sources

- Reuses `enigma_stress_phenotype_ml/data/labeled_pd.parquet` (FitnessBrowser RB-TnSeq, 60 ENIGMA isolates)
- Reuses `enigma_stress_phenotype_ml/data/features_aa.parquet` and `features_kmer2.parquet`

## Requirements

- All notebooks: local execution; see `requirements.txt` for pinned package versions
- CatBoost model files (`.cbm`) are version-sensitive — `requirements.txt` pins CatBoost to the exact version used to train the model (1.2.10)

## Reproduction

All three notebooks can be run locally in order (NB01 → NB02 → NB03):

```bash
cd projects/enigma_general_essentiality/notebooks
jupyter nbconvert --to notebook --execute 01_Data_Extraction.ipynb --output 01_Data_Extraction.ipynb
jupyter nbconvert --to notebook --execute 02_Feature_Engineering.ipynb --output 02_Feature_Engineering.ipynb
jupyter nbconvert --to notebook --execute 03_General_Essentiality_Model.ipynb --output 03_General_Essentiality_Model.ipynb
```

Note: use `--output <name>` not `--inplace` — the latter silently drops all cell outputs on this JupyterHub (see `docs/pitfalls.md` line 872).

**Prerequisites**: `enigma_stress_phenotype_ml/data/` must be present (contains `labeled_pd.parquet`,
`features_aa.parquet`, `features_kmer2.parquet`). These files are loaded by NB01 and NB02 via
relative path (`../../enigma_stress_phenotype_ml/data/`). No Spark or remote access is required.

**Inter-project dependency**: NB02 uses positional row alignment between `labeled_pd.parquet` and
the feature files — all three source files must be from the same `enigma_stress_phenotype_ml` run.
Do not mix feature files generated from different data versions.
