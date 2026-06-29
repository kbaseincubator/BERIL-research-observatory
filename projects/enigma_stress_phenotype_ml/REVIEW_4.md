---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-06-29
project: enigma_stress_phenotype_ml
---

# Review: Per-Stressor CatBoost ML Pipeline for Predicting Metal/Antibiotic Stress Phenotypes

## Summary

This is the fourth review of the project, following REVIEW_3 (also dated 2026-06-29). Since REVIEW_3, the author has resolved the two highest-priority items: the README Reproduction section now correctly lists `python scripts/run_regression_only.py` as the step that generates the regression models powering Finding 1, and runtime estimates have been added for all pipeline steps (`~hours`, `~30 min`, `~45 min`, `~20 min`, `~26 min`, `~10 min`). The project's science is sound, all five findings are well-supported by the data files, and limitations are thoroughly documented. Two moderate readability gaps remain before submission: (1) NB06 Cell 6 — which contains the LOGO summary table code — has no saved outputs, so the AUC table from `data/logo_auc_summary.csv` is not visible in any notebook; and (2) NB04 Cell 6 logs only INFO timestamps per feature combination, with the final `Best: aa+kmer2 avg AUC=0.6564` result being the only quantitative output visible in the notebook — the per-stressor AUC table is present in `data/feature_evaluation_results.csv` but not echoed to a notebook output. Neither gap invalidates the science, but both require a reader to load CSV files to see results that could appear directly in the notebook.

---

## What Changed Since REVIEW_3

| REVIEW_3 Suggestion | Status |
|---|---|
| [Important] Add `scripts/run_regression_only.py` to README Reproduction | ✅ Resolved — README now lists `python scripts/run_regression_only.py # ~20 min (regression models; powers Finding 1)` |
| [Minor] Add runtime estimates to README Reproduction | ✅ Resolved — all six pipeline steps now have runtime annotations |
| [Moderate] Add summary print to NB06 Cell 6 | ❌ Not resolved — Cell 6 has the summary code (`logo_summary_df.to_string()`) but has not been executed; `outputs` array is empty |
| [Moderate] Document which stressor-genus LOGO folds triggered single-class warnings | ⚠️ Partially addressed — the LOGO loop (Cell 5) now explicitly skips single-class folds via `if y_te.nunique()<2 or y_tr.nunique()<2: continue` with `log.debug()` output, replacing prior sklearn warnings; but since Cell 6 has no output, the per-stressor coverage summary is not visible in the notebook |

---

## Methodology

**Research question and approach**: Unchanged and sound. Organism-aware GroupShuffleSplit prevents within-organism data leakage for regression models; LeaveOneGroupOut by genus for LOGO. The regression-over-binary pivot remains well-motivated by the near-zero binary metal F1 values.

**README Reproduction section**: Now accurate and complete. The six-step sequence correctly identifies NB01 as Spark-only, NB03 as GPU-intensive, `run_regression_only.py` as the regression model generator (Finding 1), and NB06 as the 26-minute LOGO evaluation. A reader following the README can now reproduce all five findings.

**NB05 Cell 9 (regression training cell)**: Still empty, as in REVIEW_3. However, this is now a non-issue because: (a) the README explicitly directs users to `scripts/run_regression_only.py` for regression training, (b) the script exists and is self-contained, and (c) Cell 7 contains the `train_stressor_regression()` function definition showing the implementation. The empty cell is vestigial but harmless given the README update.

**Feature selection (NB04)**: Unchanged from prior reviews. NB04 was run on pre-org-filter labels. The Finding 2 ⚠️ warning block prominently flags the 0.002 AUC margin as within potential bias range. No re-run performed. The visible output in NB04 Cell 6 (`Best: aa+kmer2 avg AUC=0.6564`) matches Finding 2's reported value (`mean AUC=0.656`), confirming the result is consistent.

**LOGO folds (NB06)**: The Cell 5 LOGO loop now explicitly skips single-class folds via conditional check before model fitting. The per-genus `log.debug()` messages distinguish between test-set and training-set single-class cases. This is cleaner than relying on sklearn warning suppression, but the downstream effect on per-stressor AUC estimates is still not visible in the notebook since Cell 6 has no saved outputs. The `data/logo_auc_summary.csv` file confirms 44 stressors are represented; stressors excluded due to insufficient genera (As, Pb, Ag) are absent from the CSV as expected.

---

## Code Quality

**No new issues identified.** The core pipeline (NB01–NB05, NB09) and `src/` utilities are unchanged from REVIEW_3.

**NB06 LOGO loop (Cell 5)**: The single-class fold handling is improved — the explicit `continue` before model fitting is more reliable than tolerating sklearn's undefined-AUC path. The Cell 5 output confirms all 49 stressors were reached (50 INFO lines over 2026-06-28 19:52–20:18, ~26 minutes total — consistent with the README estimate).

**NB06 summary (Cell 6)**: Code is present: `logo_summary_df.to_csv(DATA_DIR / 'logo_auc_summary.csv')` and `print(logo_summary_df.to_string(index=False))`. The CSV file exists and contains valid data (44 stressors, LOGO AUC ranging 0.470–0.754, matching REPORT Finding 5 table). The cell has simply not been run. A single kernel execution would close this gap.

**NB04 feature evaluation (Cell 6)**: The visible output is only INFO timestamps per combination + the final `Best: aa+kmer2 avg AUC=0.6564` line. The per-combination, per-stressor AUC breakdown visible in `data/feature_evaluation_results.csv` (85 rows) is not echoed to any notebook output. Adding `print(results_df.groupby('combo')['auc'].mean().sort_values(ascending=False).to_string())` before the CSV save in Cell 7 would surface the Finding 2 table in the notebook.

**NB07 and NB08**: Correctly marked as out-of-scope with Cell 0 markdown declarations. No output expected or required.

**NB09 (Isolate Prediction)**: All 7 cells have saved outputs. The deliverable notebook is fully readable without re-execution.

**Requirements.txt**: Present and accurate. ESM-2 and PySpark dependencies are correctly commented out with environment notes.

**Pitfall adherence**: No violations found. The project continues to avoid the FitnessBrowser string-typed numeric columns pitfall by using downloaded TSV files rather than Spark SQL for fitness values. GroupShuffleSplit correctly handles organism-level data leakage. The Spark session is used only in NB01.

---

## Findings Assessment

**Finding 1 (regression outperforms classification)**: Well-supported. The `data/regression_model_metrics.csv` confirms ρ=0.050–0.230 for 11 metals; the Mn caveat (p=0.009, fails Bonferroni at α=0.0045) is elevated to Limitation #8 and noted in the Finding 1 table. The regression results are traceable to `scripts/run_regression_only.py` (now discoverable via README).

**Finding 2 (aa+kmer2 feature selection)**: The ⚠️ warning block is prominently placed. The contamination caveat is clear. NB04 Cell 6 output confirms `Best: aa+kmer2 avg AUC=0.6564`, consistent with the REPORT value.

**Finding 3 (abiotic > metal predictability)**: Well-supported by NB05 binary AUC values and independently corroborated by LOGO AUC (Finding 5). The mutual reinforcement from two evaluation designs is the strongest argument for this finding.

**Finding 4 (novel protein candidates)**: The LOGO generalization caveat is present and appropriately conservative. The multi-metal candidate (`acidovorax_3H11|Ac3H11_638`) is correctly described as Co-specific.

**Finding 5 (LOGO cross-validation)**: The REPORT table is traceable to `data/logo_auc_summary.csv`. Values verified: Co LOGO AUC = 0.618 (CSV: 0.6175), UV = 0.736 (CSV: 0.7356), Ciprofloxacin = 0.483 (CSV: 0.4827) — all round to the REPORT values. Low-n stressors (Hg n=2, Se n=2, Cd n=2, Cr n=3) are correctly flagged with asterisks in the REPORT. The biological interpretation (broad-mechanism stressors generalize across genera; genus-specific resistance pathways do not) is plausible and consistent with the literature cited.

**Discoveries section**: Both entries are defensible as cross-project candidates:
- *Mercury resistance sequence signature*: Supported by regression AUC=0.774; LOGO binary AUC=0.543 (n=2) contrast is present and clearly distinguished.
- *Amino acid composition sufficiency*: Contamination caveat is stated. Scope is not overgeneralized.

**Limitations section**: The 8-item list remains thorough. Limitation #7 (single-class LOGO fold warnings) now partially agrees with the updated code — the code skips these folds deterministically — but a per-stressor count of skipped folds is still absent from the notebooks.

---

## Suggestions

1. **[Moderate] Execute NB06 Cell 6 and save outputs.** The summary table code is present and correct:
   ```python
   logo_summary_df = pd.DataFrame(summary_rows).sort_values('mean_LOGO_AUC', ascending=False)
   logo_summary_df.to_csv(DATA_DIR / 'logo_auc_summary.csv', index=False)
   print(logo_summary_df.to_string(index=False))
   ```
   Running this cell (which depends on `logo_results` dict populated in Cell 5) and saving the notebook output would make Finding 5 traceable directly to a notebook output without requiring the reader to load a separate CSV.

2. **[Minor] Add a per-combination AUC summary output in NB04.** The current Cell 6 output ends with `Best: aa+kmer2 avg AUC=0.6564` but does not show the ranked table. In Cell 7, before the CSV save, add:
   ```python
   print(results_df.groupby('combo')['auc'].mean().sort_values(ascending=False).to_string())
   ```
   This would surface the Finding 2 feature comparison table directly in the notebook, reducing dependence on the external `feature_evaluation_results.csv` for a reader verifying the finding.

3. **[Minor] Update the README Status line.** The README currently reads `Status: Reviewed — REVIEW_2.md drafted; awaiting /submit.` This is stale — REVIEW_3 and REVIEW_4 have now been completed. Update to `Status: Reviewed — REVIEW_4.md drafted; awaiting /submit.`

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-06-29
- **Scope**: README.md, REPORT.md, REVIEW_1.md, REVIEW_2.md, REVIEW_3.md, ADVERSARIAL_REVIEW_ROUND1.md, beril.yaml, requirements.txt, 9 notebooks (NB01–NB09), data/ (feature parquets, regression_model_metrics.csv, final_model_performance.csv, feature_evaluation_results.csv, logo_auc_summary.csv, predictions/, logo_checkpoints/), figures/ (4 figures), src/, scripts/ (run_regression_only.py and 3 other scripts), docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:f8ef38dd8072ac11eb5b541ec25d7291809e19cdf775c7cedd829c22c19c1e67 -->
