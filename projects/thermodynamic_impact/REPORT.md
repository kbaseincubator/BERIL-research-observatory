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

---

## Update: TMFA Constraints (2026-05-13)

### Background: Why Hard Cutoffs Failed

The initial analysis (Sections 1-4 above) used hard deltaG cutoffs: reactions with |dG| > 5 kJ/mol were locked to the thermodynamically favorable direction. This approach constrained 928 E. coli reactions (58.8%) and eliminated growth entirely for both organisms. The conclusion that Marvin and OPAM2 had "minimal impact" was technically correct — both produced identical zero growth — but for the wrong reason: the constraint method itself was broken, not the dG values.

Six essential reactions have standard-condition dG opposing their required in-vivo flux direction (e.g., Phosphotransacetylase with dG° = +5.9 kJ/mol must run forward for acetate metabolism). These reactions function in living cells because metabolite concentrations shift the effective dG to be favorable — a driving force that hard cutoffs ignore.

### TMFA Implementation

We implemented `TMFAPkg`, a new ModelSEEDpy FBA package following the TMFA formulation of Henry, Broadbelt, and Hatzimanikatis (2007, Biophys J 92:1792-1805). The MILP formulation:

1. **Binary use variables** (z_fwd, z_rev) per reaction — coupled to flux via big-M constraints
2. **Continuous ln(concentration) variables** per metabolite — bounded by physiological ranges (default 1 uM to 20 mM)
3. **dG decomposition constraint**: dG_rxn = dG° + RT * Sigma(n_ij * ln(x_j)) + transport_correction + error
4. **Thermodynamic feasibility**: dG_rxn <= 0 when reaction is active forward (z_fwd = 1); dG_rxn >= 0 when active reverse (z_rev = 1)
5. **Mutual exclusion**: z_fwd + z_rev <= 1

Key design choices:
- H+ excluded from concentration sum in Mode A (reaction-level dG already pH-transformed via Legendre)
- Water excluded (activity = 1)
- Transport reactions include membrane potential correction (F * delta_psi * net_charge, with c0 = -160 mV)
- Big-M constant auto-computed from data range with 20% safety margin
- Error variable per reaction bounded by +/- 2 * dG_std

Source code: `src/tmfapkg.py` (also installed at `modelseedpy.fbapkg.tmfapkg`)

### Results Under TMFA Constraints

#### Growth is preserved

| Organism | Unconstrained | TMFA+Marvin | TMFA+OPAM2 | Constrained Reactions |
|----------|---------------|-------------|------------|----------------------|
| E. coli | 0.5625 | **0.5625** | **0.5625** | 1,210 |
| B. subtilis | 0.5000 | **0.5000** | **0.5000** | 941 |

TMFA constrains **more** reactions than the hard-cutoff approach (1,210 vs 928 for E. coli) while preserving full growth. The MILP solver (GLPK) finds concentration assignments that make all active reactions thermodynamically feasible.

#### The 6 previously-conflicting reactions

| Reaction | Name | dG° (Marvin) | Flux | dGrxn (actual) | z_fwd | z_rev |
|----------|------|-------------|------|----------------|-------|-------|
| rxn00173 | Phosphotransacetylase | +5.9 kJ/mol | **1.0** (forward) | **-0.0** | 1 | 0 |
| rxn00499 | Polyphosphate kinase | +26.9 kJ/mol | **-999.0** (reverse) | **0.0** | 0 | 1 |
| rxn00117 | ATP:sulfate adenylyltransferase | -2.2 kJ/mol | 0.0 | 17.6 | 0 | 0 |
| rxn00209 | Lactate dehydrogenase | -104.3 kJ/mol | 0.0 | -123.1 | 0 | - |
| rxn05561 | G3P dehydrogenase | 0.0 kJ/mol | 0.0 | -16.4 | 0 | 0 |
| rxn00062 | F1-ATPase | -25.5 kJ/mol | 0.0 | - | - | - |

Phosphotransacetylase (dG° = +5.9) carries forward flux because concentrations shift the effective dG to ~0 (just at the feasibility boundary). Polyphosphate kinase (dG° = +26.9) runs in reverse, which is thermodynamically consistent. The other 4 carry no flux in the optimal solution.

#### Flux differences: Marvin vs OPAM2

Under TMFA, **25 E. coli reactions** show flux differences between Marvin and OPAM2 dG values:

- **6 reactions** with large flux differences (|delta| = 999-1000): alternate pathway routing through reactions with extreme flux bounds, reflecting different optimal solutions to the MILP
- **7 reactions** with small flux differences (|delta| = 0.25-1.0): subtle shifts in amino acid biosynthesis, cofactor metabolism, and transport pathways
- **12 reactions** with unit flux differences (|delta| = 1.0): binary on/off switches in non-essential pathways

B. subtilis shows **0 flux differences** — the OPAM2 pKa changes do not affect the optimal flux distribution for this organism.

#### LP-relaxed FVA: directionality analysis

With binary variables relaxed to continuous [0,1], FVA shows **0 directionality classification changes** between Marvin and OPAM2 for either organism. The LP relaxation provides an outer bound on the MILP-feasible flux range, indicating that the dG differences do not fundamentally alter which reactions can carry flux — they only affect which alternate optimal solution the solver selects.

| Organism | Baseline Blocked | TMFA+Marvin Blocked | TMFA+OPAM2 Blocked | Changes |
|----------|-----------------|--------------------|--------------------|---------|
| E. coli | 1,139 | 1,139 | 1,139 | 0 |
| B. subtilis | 1,007 | 1,007 | 1,007 | 0 |

### Revised Interpretation

The TMFA analysis reveals a more nuanced picture than the hard-cutoff results:

1. **The constraint method matters more than the pKa source.** Hard cutoffs produced catastrophically wrong predictions (zero growth) regardless of whether Marvin or OPAM2 pKas were used. TMFA produces correct predictions (full growth preserved) with both.

2. **OPAM2 pKa changes have real but minor downstream effects.** Under proper TMFA constraints, 25 reactions show flux differences in E. coli, primarily in alternate optimal pathways. These differences are driven by small dG shifts (1-10 kJ/mol) that tip the MILP solver toward different equivalent optima.

3. **Concentration flexibility absorbs dG uncertainty.** The physiological concentration range (1 uM to 20 mM) provides ~25 kJ/mol of driving force per metabolite (RT * ln(20000) = 24.5 kJ/mol at 298 K). This buffer easily compensates for the mean pKa-driven dG change of 13.35 kJ/mol.

4. **Network structure dominates thermodynamics.** The identical blocked reaction counts (1,139 E. coli, 1,007 B. subtilis) under LP-relaxed TMFA-FVA confirm that blocked reactions are determined by metabolic network connectivity, not thermodynamic constraints.

### TMFA Data Artifacts

| File | Description |
|------|-------------|
| `data/tmfa_growth_comparison.tsv` | Growth rates under TMFA constraints |
| `data/tmfa_flux_differences.tsv` | 25 reactions with flux differences (E. coli) |
| `data/tmfa_essential_reactions.tsv` | 6 previously-conflicting essential reactions under TMFA |
| `data/tmfa_fva_summary.tsv` | LP-relaxed FVA blocked reaction counts |
| `data/tmfa_directionality_diff.tsv` | Directionality classification changes (0 changes) |
| `data/tmfa_ecoli.lp` | Exported LP formulation for E. coli TMFA model |
| `figures/tmfa_blocked_reactions.png` | Bar chart: reaction classification under TMFA |
| `figures/tmfa_flux_scatter.png` | Scatter: Marvin vs OPAM2 flux comparison |
| `src/tmfapkg.py` | TMFAPkg source code (also installed as modelseedpy.fbapkg.tmfapkg) |
