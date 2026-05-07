# Research Plan: Thermodynamic Impact of OPAM2 pKa Predictions

## Research Question

How do OPAM2-predicted pKa values — propagated through the dGPredictor Legendre transform to reaction deltaG — affect downstream metabolic model predictions compared to the current Marvin 23.4 (ChemAxon) pKa values?

## Hypothesis

**H0**: Replacing Marvin pKa with OPAM2 pKa produces negligible changes in reaction deltaG values and no measurable impact on metabolic model predictions (blocked reactions, directionality, phenotype accuracy).

**H1**: OPAM2 pKa predictions, particularly for functional groups where Marvin and OPAM2 diverge (e.g., guanidines, amidines, heterocyclic bases), produce meaningful deltaG shifts that alter reaction feasibility constraints, change blocked/unblocked reaction counts, shift reaction directionalities, and affect growth phenotype predictions in genome-scale models.

## Literature Context

- pKa values enter metabolic thermodynamics through the Legendre transform, which corrects standard Gibbs free energy (deltaG0) to transformed values (deltaG'0) at physiological pH, ionic strength, and temperature.
- Prior OPAM2 benchmarking against ModelSEED compounds shows: acid R^2=0.692 (MAE=1.94), base R^2=0.243 (MAE=3.33). Carboxylic acids predict well (MAE=0.68); guanidines/amidines are worst (MAE=6.52).
- The group contribution method in dGPredictor decomposes molecules into substructure groups for deltaG prediction. pKa changes affect only the Legendre transform correction, not the group decomposition or trained model weights.

## Approach

### Phase 1: pKa Comparison and Database Update

1. **Compare OPAM2 vs Marvin pKa** (NB01): Load Marvin pKa/pkb from ModelSEEDDatabase compound TSVs. Run OPAM2 on all compounds with .mol structures (~24K). Align by atom index (OPAM2 0-based -> Marvin 1-based). Quantify differences by magnitude and functional group.

2. **Update ModelSEEDDatabase** (NB02): Write OPAM2 pKa values into compound TSVs using the `fragment:atom:value` format. Regenerate JSON.

### Phase 2: deltaG Recomputation

3. **Recompute deltaG** (NB03): Point dGPredictor at updated ModelSEEDDatabase. Reuse existing trained model (group fingerprints unchanged). Rebuild compound cache with new pKas. Recompute Legendre transform correction for all reactions (~32K).

4. **Update database deltaG** (NB04): Write new deltaG/deltagerr into reaction TSVs. Regenerate JSON.

### Phase 3: Model Building and Impact Evaluation

5. **Build reference models** (NB05): Use KBUtilLib `MSReconstructionUtils.build_metabolic_model()` to build models for E. coli (GN), B. subtilis (GP), P. putida (GN), and an archaeal reference. Each goes through genome classification, template selection, ATP correction, and gapfilling.

6. **Blocked reactions** (NB06): Run FVA with `FullThermoPkg` on each model using old vs new deltaG. Count newly blocked/unblocked reactions. Analyze affected subsystems.

7. **Directionality and loops** (NB07): Compare reaction direction (Forward/Reverse/Reversible) before and after. Detect thermodynamic loops using `SimpleThermoPkg` + `RevBinPkg`.

8. **Phenotype impact** (NB08): Simulate growth phenotypes with `MSGrowthPhenotypes`. Compare CP/CN/FP/FN rates before vs after thermodynamic update.

## Data Sources

| Source | Location | Usage |
|--------|----------|-------|
| OPAM2 weights | `/tmp/OPAM2/models/weight_{acid,base}_modelseed.pth` | pKa prediction |
| OPAM2 mol files | `/tmp/OPAM2/src/datasets/Unique_MS_Structures/` | Compound structures |
| ModelSEEDDatabase | `/tmp/ModelSEEDDatabase/Biochemistry/` | pKa/deltaG storage |
| dGPredictor model | `/tmp/dGPredictor/model/modelseed_M12_model_BR.pkl` | deltaG prediction |
| KBUtilLib | `/global_share/KBaseUtilities/KBUtilLib/` | Model building |

## Query Strategy

This project is primarily computation-based (no BERDL lakehouse queries). All data flows through local file-system repos and the KBase API for genome retrieval.

## Analysis Plan

| Metric | Method | Expected Output |
|--------|--------|-----------------|
| pKa difference distribution | Per-atom |delta pKa| across compounds | Histogram, summary stats |
| deltaG change distribution | Per-reaction |delta deltaG| | Histogram, summary stats |
| Blocked reaction count | FVA min=0, max=0 | Count per model, before/after |
| Directionality changes | FVA sign analysis | Count per model |
| Loop participants | Loopless vs standard FBA | Reaction sets |
| Phenotype accuracy | CP/CN/FP/FN classification | Accuracy, sensitivity, specificity |

## Expected Outcomes

- Quantified pKa differences across ~24K compounds with functional group breakdown
- deltaG changes for ~32K reactions, identifying those most affected
- Per-model counts of blocked reaction changes, directionality shifts, and loop modifications
- Net phenotype prediction accuracy comparison

## Revision History

- **v1** (2026-05-07): Initial plan covering full pipeline from pKa to phenotype impact
