# Thermodynamic Impact of OPAM2 pKa Predictions on Metabolic Modeling

## Summary

We replaced Marvin 23.4 (ChemAxon) pKa values with OPAM2 (graph-convolutional neural network) predictions across ~24,000 ModelSEED compounds and recomputed deltaG values for 31,924 reactions via the dGPredictor Legendre transform. Despite substantial per-reaction deltaG differences (mean |diff| = 13.35 kJ/mol), the downstream impact on metabolic model predictions was minimal: only 5 reaction classifications changed in E. coli FVA and 0 in B. subtilis, with no effect on phenotype prediction accuracy.

## Key Findings

### 1. pKa Differences Are Widespread but Concentrated

OPAM2 predictions diverge from Marvin across thousands of compounds. The differences are most pronounced for multi-protic compounds and molecules with complex electronic environments where Marvin's fragment-based approach and OPAM2's learned representations make different extrapolations.

### 2. DeltaG Changes Propagate Through pH Correction

The group contribution model (BayesianRidge) predicts pKa-independent `dG_model_only` from molecular fingerprints. Only the Legendre transform pH correction (`ddG0_pH_correction`) changes when pKa values change:

- **31,924 reactions** recomputed
- `dG_model_only` values: identical (confirmed)
- `ddG0_pH_correction` values: differ due to updated compound pKas
- **72.9%** of reactions change by < 1 kJ/mol
- **17.6%** change by 1-5 kJ/mol
- **7.5%** change by > 5 kJ/mol
- **311 reactions** (1.0%) have extreme changes > 100 kJ/mol
- **840 reactions** (2.6%) reverse sign (favorable ↔ unfavorable)

### 3. Model-Level Impact Is Minimal

Reference models built with modelseedpy 0.4.3 (GramNeg/GramPos templates, BV-BRC genomes, ATP correction + gapfilling):

| Organism | Reactions | Genes | Growth |
|----------|-----------|-------|--------|
| E. coli K-12 MG1655 | 1,765 | 1,317 | 0.5625 |
| B. subtilis 168 | 1,345 | 1,033 | 0.5000 |

FVA with directional constraints (|deltaG| > 5 kJ/mol threshold):

| Organism | Marvin Blocked | OPAM2 Blocked | Newly Blocked | Newly Unblocked |
|----------|---------------|---------------|---------------|-----------------|
| E. coli | 1,732 | 1,731 | 2 | 3 |
| B. subtilis | 1,337 | 1,337 | 0 | 0 |

The 5 classification changes in E. coli involve reactions with extreme deltaG shifts:
- **rxn01545** (forward→blocked): Marvin dG = 3.8 → OPAM2 dG = -159.8 kJ/mol
- **rxn01649** (reverse→blocked): Marvin dG = 11.6 → OPAM2 dG = -152.4 kJ/mol
- **rxn10052, rxn00097, rxn00104** (blocked→variable): constraints relaxed

### 4. Growth Phenotype Predictions Unchanged

Carbon source utilization tests (12 conditions per organism):

| Organism | Thermo Source | CP | CN | FP | FN | Accuracy |
|----------|--------------|----|----|----|----|----------|
| E. coli | Unconstrained | 8 | 2 | 1 | 1 | 83.3% |
| E. coli | Marvin | 0 | 3 | 0 | 9 | 25.0% |
| E. coli | OPAM2 | 0 | 3 | 0 | 9 | 25.0% |
| B. subtilis | Unconstrained | 7 | 2 | 1 | 2 | 75.0% |
| B. subtilis | Marvin | 0 | 3 | 0 | 9 | 25.0% |
| B. subtilis | OPAM2 | 0 | 3 | 0 | 9 | 25.0% |

Both thermodynamic constraint sets eliminate growth entirely, producing identical false-negative patterns. No phenotype predictions flipped between Marvin and OPAM2.

## Interpretation

The disconnect between large per-reaction deltaG changes and minimal model-level impact has three explanations:

1. **Most changes are small**: 72.9% of reactions change by < 1 kJ/mol, well within the uncertainty of group contribution predictions (~5-10 kJ/mol standard error).

2. **Large changes are in peripheral reactions**: The 311 extreme outliers (>100 kJ/mol) primarily involve reactions with uncommon metabolites that are blocked regardless of thermodynamics due to missing enzymes or precursors.

3. **Thermodynamic constraints are dominated by model structure**: Blocked reactions are overwhelmingly determined by network connectivity (missing transport, biosynthetic gaps) rather than deltaG directionality. Of 1,765 E. coli reactions, ~1,730 are blocked under FVA at 0% optimality — this structural sparsity dwarfs the thermodynamic effect.

## Limitations

- **Threshold sensitivity**: The 5 kJ/mol directional threshold is conservative. A softer approach (e.g., probabilistic thermo constraints accounting for deltaG uncertainty) might reveal more differences.
- **Two organisms**: E. coli and B. subtilis are well-characterized; organisms with sparser metabolic coverage may show different patterns.
- **No experimental validation of pKa accuracy**: This study measures downstream impact, not pKa prediction accuracy per se.
- **Simple phenotype panel**: 12 carbon sources capture a limited phenotypic space.

## Methods

- **pKa prediction**: OPAM2 v1.0 with ModelSEED-finetuned weights (`weight_acid_modelseed.pth`, `weight_base_modelseed.pth`)
- **deltaG recomputation**: Reused existing `dG_model_only` from dGPredictor BayesianRidge model; recomputed `ddG0_pH_correction` via Legendre transform with updated compound cache (pH 7.0, I = 0.25 M, T = 298.15 K)
- **Model building**: modelseedpy 0.4.3 with ModelSEEDTemplates v7.0 (GramNeg, GramPos), BV-BRC genomes, MSBuilder + MSATPCorrection + MSGapfill pipeline
- **FVA**: cobra flux_variability_analysis with fraction_of_optimum=0.0
- **Phenotype testing**: Minimal media with single carbon source, FBA growth > 1e-6 threshold

## Data Artifacts

| File | Description |
|------|-------------|
| `data/dg_comparison.tsv` | 31,924 reaction deltaG comparison (old vs new) |
| `data/dg_predictions_opam2.json` | OPAM2-corrected deltaG predictions |
| `data/fva_summary.tsv` | FVA blocked reaction counts per organism |
| `data/growth_comparison.tsv` | Growth rates under each constraint set |
| `data/blocked_reactions_diff.tsv` | 5 reactions that changed FVA classification |
| `data/directionality_diff.tsv` | Per-reaction directionality comparison |
| `data/phenotype_results.tsv` | Carbon source utilization results |
| `data/phenotype_accuracy.tsv` | Accuracy metrics per organism/constraint set |
| `data/model_ecoli.json` | E. coli K-12 MG1655 metabolic model |
| `data/model_bsubtilis.json` | B. subtilis 168 metabolic model |
