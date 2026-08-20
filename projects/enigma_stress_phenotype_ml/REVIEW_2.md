---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-06-29
project: enigma_stress_phenotype_ml
---

# Review: Per-Stressor CatBoost ML Pipeline for Predicting Metal/Antibiotic Stress Phenotypes

## Summary

This is a re-review of the project following REVIEW_1. The author has resolved several previously flagged items: the `figures/` directory now contains four key visualizations, NB07 and NB08 have markdown scope declarations explaining they are intentionally out-of-scope, and `requirements.txt` has been added with correct dependencies. NB06 (LOGO cross-validation) is now fully executed across all 49+ stressors, with checkpoints in `data/logo_checkpoints/` and aggregate results in `data/adaptive_metrics.csv`. These are genuine improvements. The main remaining gap — and the most important one — is that the LOGO results are not incorporated anywhere in the REPORT or README. The REPORT still describes NB06 as "planned, not yet reported" and the README pipeline overview lists NB06 as "(planned, not yet reported)." Yet the LOGO results contain a material finding: metal binary classifiers have near-random phylogenetic generalization (AUC 0.51–0.65) while abiotic classifiers are substantially stronger (0.73–0.88). This contrast reinforces Finding 3 and adds important context around the novel candidate confidence for metals — context that is missing from the submitted report. `Untitled.ipynb` also remains in the notebooks directory. Overall, the core science is sound and the analysis is largely reproducible; the project can reach a strong submission state by incorporating the LOGO results and updating the README status.

---

## What Changed Since REVIEW_1

The following REVIEW_1 suggestions were addressed:

| Suggestion | Status |
|---|---|
| Populate figures/ directory | ✅ Resolved — 4 figures present |
| NB07/NB08 scope declarations | ✅ Resolved — markdown headers label both as "Exploratory / Not Part of Submitted Pipeline" |
| Add requirements.txt | ✅ Resolved — catboost, scikit-learn, scipy, pandas, numpy, pyarrow, matplotlib, seaborn listed with version bounds |
| Complete NB06 LOGO | ✅ Executed — all 49 stressors complete (logo_checkpoints/ + adaptive_metrics.csv) |
| Qualify multi-metal candidate | ✅ REPORT already frames Ac3H11_638 as "Co-specific rather than broad-metal essentiality" |
| Mn caveat elevation | ✅ Mn model appears as Limitation #8 with Bonferroni-corrected α discussed |
| Remove Untitled.ipynb | ❌ Still present in notebooks/ |
| NB04 re-run on filtered labels | ❌ Not re-run; remains acknowledged as Limitation #4 |
| LOGO results in REPORT | ❌ Not incorporated despite NB06 being complete |
| Runtime estimates in README | ❌ Not added |

---

## Methodology

**Research question and approach**: Unchanged from REVIEW_1 — clearly stated and sound. Organism-aware GroupShuffleSplit splitting (NB05) prevents within-organism leakage. The regression-over-binary decision is well-motivated and backed by the near-zero binary F1 values for metals.

**LOGO cross-validation now executed**: NB06 is fully run. The loop progressed through all 49+ stressors from June 28 19:52 to 20:18, and per-stressor LOGO AUC values are saved in `data/adaptive_metrics.csv`. The key results:

| Metal | LOGO Binary AUC (NB06) | Regression AUC-from-ranking (NB05) |
|-------|----------------------|-------------------------------------|
| Hg | 0.513 | 0.774 |
| Co | 0.559 | 0.679 |
| Cr | 0.536 | 0.671 |
| Zn | 0.588 | 0.688 |
| Fe | 0.536 | 0.627 |
| Se | 0.533 | 0.699 |
| Mn | 0.505 | 0.623 |
| Ni | 0.618 | 0.663 |
| Al | 0.570 | 0.640 |
| Cu | 0.650 | 0.655 |
| Cd | 0.604 | 0.556 |

Metal binary classifiers have near-random LOGO AUC (0.51–0.65), confirming poor phylogenetic generalization. Abiotic and antibiotic stressors maintain strong LOGO performance: Ampicillin 0.876, Trimethoprim 0.805, UV 0.773, Sucrose 0.820, Cold 0.758, Spectinomycin 0.744. This is a material finding that both reinforces Finding 3 and raises questions about the confidence of metal novel-candidate predictions.

**Caution on direct comparison**: The two AUC columns measure different things — binary LOGO AUC is from a binary classifier tested on left-out genera, while regression AUC-from-ranking reflects how well the regression model ranks proteins within test-set organisms (20% of organism groups, not genus-stratified). The comparison is not apples-to-apples. The gap for Hg (0.513 vs 0.774) does not necessarily mean the regression model fails on new genera. However, the LOGO result does indicate that the *binary* signal is near-random across genera, and the features are shared — this warrants an explanation in the REPORT rather than silence.

**Sparse LOGO folds**: NB06 cell 2 contains pervasive sklearn warnings: `"A single label was found in 'y_true' and 'y_pred'"` and `"ROC AUC score is not defined in that case."` These occur when a left-out genus contains no positive examples for a given stressor. This means some LOGO fold AUC values are imputed or unreliable, and the average LOGO AUC for rare-stressor metals may be biased. The adaptive_metrics.csv does not flag which stressor-genus combinations triggered these warnings.

**Feature selection (NB04)**: Unchanged from REVIEW_1. Still executed on unfiltered `labeled_pd` (confirmed from cell structure: Cell 4 splits on `labeled_pd` without stressor-based org filtering). Still acknowledged as Limitation #4. No re-run performed.

---

## Code Quality

**New issues since REVIEW_1**: None in the core pipeline.

**Existing resolved**: requirements.txt correctly covers all library dependencies. The ESM-2 and PySpark requirements are correctly commented out with environment notes (NB03/NB01 only).

**NB06 single-class fold warnings**: Cell 2 of NB06 generates 9 warning outputs, all stemming from LOGO folds where one class is absent. This is an expected edge case for rare stressors (As, Pb, Ag have only 1 organism), but it is unhandled: the LOGO code does not filter out folds where positives are absent before computing AUC. The downstream adaptive_metrics.csv AUC values for those stressors (As, Pb, Ag are absent from the table — confirming they were skipped) are not affected, but for near-zero-positive stressors the LOGO metrics should be interpreted cautiously.

**NB06 output completeness**: Cell 5 (the LOGO loop) shows only INFO-level timestamps per stressor — the loop logged start times but did not log per-stressor AUC. The aggregated AUC is saved to `data/adaptive_metrics.csv` via cell 3, which is the authoritative source. However, a reader inspecting NB06 output inline would not see numeric AUC values in the cell stream; they must know to look at the CSV. Adding a summary `print(results_df)` to the end of the LOGO loop cell would improve notebook readability.

**Untitled.ipynb**: Still present in `notebooks/`. Should be removed before submission. Note: `untitled.txt` (project tree diagram in the root directory) is a harmless documentation aid.

**src/ utilities**: Unchanged from REVIEW_1. The `sys.path.insert` pattern is functional but fragile; no new issues.

**No new pitfall violations**: The project continues to avoid relevant BERDL pitfalls (Spark used only in NB01, GroupShuffleSplit for leakage prevention, fitness data read from TSVs not Spark for type-safe access).

---

## Findings Assessment

**Finding 1 (regression outperforms classification)**: Well-supported and unchanged. Binary metal F1 values confirmed near-zero in both `final_model_performance.csv` and NB06 adaptive thresholds output. The LOGO results add independent corroborating evidence: metal binary classifiers generalize very poorly across genera (AUC 0.51–0.65), confirming that regression-based ranking is the only viable approach. This finding would be stronger if the REPORT cited the LOGO evidence.

**Finding 2 (aa+kmer2 feature selection)**: Unchanged from REVIEW_1. The 0.002 AUC margin between aa+kmer2 and the next-best combination remains within potential label-contamination bias range. Limitation #4 acknowledges this. No re-run occurred. The Discoveries entry for this finding appropriately notes the contamination caveat.

**Finding 3 (abiotic stressors more predictable)**: The LOGO data strongly reinforces this finding. Abiotic/antibiotic LOGO AUC (0.73–0.88) is dramatically higher than metal LOGO AUC (0.51–0.65). This is exactly the expected result and it cross-validates the NB05 single-split comparison. The REPORT does not reference the LOGO evidence because it pre-dates the NB06 completion.

**Finding 4 (novel protein candidates)**: The multi-metal candidate (Ac3H11_638) is now correctly framed as Co-specific. The "relative ranking" caveat for novel predictions is present and appropriate. One additional consideration from the LOGO results: if metal binary classifiers generalize near-randomly across genera, the novel predictions may rank proteins within untested organisms no better than a random sequence-composition baseline. The REPORT should briefly note that LOGO evaluation of binary classifiers showed near-random genus-level generalization for metals and explain why the regression models may still provide useful cross-organism rankings despite this (different model, different evaluation).

**Discoveries section**:
- *Mercury resistance signature*: The Discovery claim ("AUC-from-ranking=0.774, consistent with *mer* operon conservation") is confirmed by the data and the biological rationale is sound. However, the LOGO binary AUC for Hg is 0.513 — barely above random. These measure different things (the discovery concerns the regression model's ranking ability on test organisms, not genus-level binary classification), but the contrast should be at minimum noted somewhere to preempt misinterpretation. The Discovery as written is scientifically defensible if the scope is explicitly the regression ranking metric on held-out organisms (not generalization to unseen genera).
- *Amino acid composition sufficiency*: Appropriately caveated. No change from REVIEW_1.

**REPORT status inconsistency**: The REPORT's Limitations #7 states "NB06 LOGO cross-validation: Binary classifier phylogenetic generalization (Leave-One-Genus-Out) is implemented but results are not yet reported." NB06 is fully executed and results are in `data/adaptive_metrics.csv`. The REPORT is factually incorrect; the results exist and should be incorporated.

---

## Suggestions

1. **[Critical] Incorporate LOGO results into the REPORT.** NB06 is complete. Add a "Finding 5: LOGO Cross-Validation" section (or incorporate into Findings 1 and 3) reporting per-metal LOGO AUC from `data/adaptive_metrics.csv`. At minimum: a table of LOGO AUC for metals (0.51–0.65) and for top abiotic stressors (0.73–0.88). Update the REPORT Limitations #7 to remove "not yet reported" and add any observations about failure modes. This is the largest gap between REVIEW_1 and a submission-ready state.

2. **[Critical] Update README NB06 status.** README.md line 27 lists NB06 as "Leave-One-Genus-Out evaluation (planned, not yet reported)." Update to reflect that NB06 is complete and results are in `data/adaptive_metrics.csv`.

3. **[Important] Address the Hg AUC contrast in the Discoveries section or Limitations.** The mercury resistance Discovery claims the highest AUC-from-ranking (0.774) as evidence for a strong sequence signature, citing *mer* operon conservation. However, the LOGO binary classifier AUC for Hg is 0.513 (near-random). Briefly note this contrast and explain that the two metrics assess different models and evaluation designs: the regression AUC-from-ranking reflects within-test-organism protein ranking; the LOGO binary AUC reflects genus-level binary classification. Both can be true simultaneously (a regression model can rank proteins usefully within training-adjacent organisms while a binary classifier fails on left-out genera). Clarifying this prevents misreading the Discovery claim.

4. **[Important] Note metal LOGO AUC near-random baseline in novel candidate caveats.** Finding 4 / Limitations #6 discusses calibration of novel predictions but does not mention the genus-level generalization problem surfaced by LOGO. Add a brief note: "LOGO binary classification AUC for metals (0.51–0.65) indicates that binary protein-level predictions do not generalize reliably across genera. While regression-based ranking may still provide useful within-organism prioritization, novel candidate rankings for phylogenetically distant organisms should be treated with additional caution."

5. **[Moderate] Acknowledge single-class LOGO fold warnings in NB06.** Cell 2 of NB06 has 9 warning outputs about single-class folds. Note in a markdown cell (or code comment) which stressor-genus combinations triggered these, and confirm that the adaptive_metrics.csv values for affected stressors reflect reliable averages. For As/Pb/Ag this is expected (1 organism, can't do LOGO); for other stressors it signals that some genera have no positives.

6. **[Moderate] Add NB06 summary output to the notebook.** The LOGO loop (cell 5) logs only start-time timestamps per stressor; the AUC results are only visible via `data/adaptive_metrics.csv`. Add `print(logo_summary_df.sort_values('AUC', ascending=False).to_string())` to the end of the cell so that a reader reviewing the notebook inline can see the summary without loading a CSV.

7. **[Minor] Remove `Untitled.ipynb`** from `notebooks/` before submission. (Note: `untitled.txt` in the project root is a project-tree diagram and can stay.)

8. **[Minor] Add runtime estimates to README Reproduction section.** NB03 (ESM-2 embeddings for 215K proteins) requires GPU or high-memory CPU — this is likely multi-hour on CPU. NB05 (46 binary stressors + 11 regression models, each with GroupShuffleSplit + CatBoost training) and NB06 (49+ LOGO folds × stressor count) are also substantial. Stating estimated runtimes and any parallelism flags helps future users plan.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-06-29
- **Scope**: README.md, REPORT.md, ADVERSARIAL_REVIEW_ROUND1.md, REVIEW_1.md, beril.yaml, requirements.txt, untitled.txt, 9 notebooks (NB01–NB09 + Untitled.ipynb), data/ (feature parquets, model metrics CSVs, predictions/), data/logo_checkpoints/ (44 per-stressor parquets), figures/ (4 figures), src/, scripts/, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:a1cf89ea482c936e40b10da54cf2295e1c017c7b229e650cf012fab1ff3cb619 -->
