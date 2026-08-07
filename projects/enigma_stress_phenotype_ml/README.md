# Per-Stressor CatBoost ML Pipeline for Predicting Metal/Antibiotic Stress Phenotypes

## Research Question

Can protein sequence composition features alone predict which ENIGMA bacterial isolates exhibit fitness defects under metal and antibiotic stress? Can regression on continuous fitness scores (rather than binary classification) provide actionable candidate rankings for untested organisms?

## Status

Completed — Regression models predict metal stress phenotype from sequence composition (AUC 0.556–0.774); LOGO cross-validation confirms poor phylogenetic generalization for metals vs. strong generalization for abiotic stressors; 7,840 novel protein candidates ranked across untested ENIGMA organisms.

## Authors

Heather MacGregor (ORCID: 0000-0003-1112-3009)  
Lawrence Berkeley National Laboratory

## Pipeline Overview

The complete pipeline comprises 9 Jupyter notebooks executed sequentially:

1. **NB01 — Data Preparation**: Extract labeled fitness data from the FitnessBrowser Spark database for 11 metal stressors (Zn, Cu, Cd, Co, Ni, Cr, Hg, Mn, Fe, Se, Al) and abiotic compounds across ENIGMA isolates.

2. **NB02 — Sequence Integration**: Download and integrate protein sequences for all ENIGMA isolates from the genome depot.

3. **NB03 — Feature Engineering**: Compute complementary feature sets (aa, kmer2, kmer3, physicochemical, ESM-2).

4. **NB04 — Feature Evaluation**: Cross-validate feature combinations; aa+kmer2 selected (mean AUC=0.656).

5. **NB05 — Per-Stressor Model Training**: Train independent CatBoost binary classifiers and CatBoostRegressor models per stressor using organism-aware GroupShuffleSplit.

6. **NB06 — LOGO Cross-Validation**: Leave-One-Genus-Out binary classification across 49+ stressors; complete. Metal LOGO AUC: 0.51–0.65 (near-random). Abiotic/antibiotic: 0.67–0.88. Aggregate results in `data/adaptive_metrics.csv`.

7. **NB07 — Ensemble Model Training**: Optional ensemble model.

8. **NB08 — General Essentiality Model**: Optional multi-label model.

9. **NB09 — Isolate Prediction**: Apply regression models to all 215,051 proteins; rank novel candidates in untested organisms.

## Key Results

- Regression models trained for 11/14 metals (Spearman ρ=0.050–0.230, AUC-from-ranking 0.556–0.774)
- Hg has the strongest sequence-fitness signal (AUC=0.774, 9 organisms)
- As/Pb/Ag: only 1 organism in FitnessBrowser; cannot train
- Abiotic stressors (UV, Ethanol, Acid): binary AUC=0.771–0.824
- 7,840 novel top-ranked candidate proteins across 18–58 untested organisms per metal

## Data Sources

- `fitnessbrowser` (fit.genomics.lbl.gov): RB-TnSeq fitness data, 60 ENIGMA isolates
- `enigma.genome_depot_enigma`: Protein sequences

## Requirements

- **NB01**: Spark access (queries FitnessBrowser)
- **NB03**: GPU or high-memory CPU for ESM-2 embeddings
- **NB04–NB09**: Local execution; CatBoost + scikit-learn

## Reproduction

```bash
cd projects/enigma_stress_phenotype_ml
jupyter notebook notebooks/01_Data_Preparation.ipynb   # Requires Spark (~hours)
jupyter notebook notebooks/04_Feature_Evaluation.ipynb  # ~30 min
jupyter notebook notebooks/05_Model_Training.ipynb      # ~45 min (binary classifiers)
python scripts/run_regression_only.py                   # ~20 min (regression models; powers Finding 1)
jupyter notebook notebooks/06_Model_Evaluation.ipynb    # ~26 min (LOGO across 49+ stressors)
jupyter notebook notebooks/09_Isolate_Prediction.ipynb  # ~10 min
```

> **Note**: NB03 (ESM-2 embeddings) requires GPU or high-memory CPU and is multi-hour. NB01 requires Spark cluster access. All other notebooks run locally with dependencies in `requirements.txt`.

## References

- Price et al. (2018) Nature 557: FitnessBrowser RB-TnSeq data
- Arkin et al. (2018) Nature Biotechnology 36: KBase/ENIGMA
- Lin et al. (2023) Science 379: ESM-2 language model
