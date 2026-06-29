---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-06-29
project: enigma_stress_phenotype_ml
---

# Review: Per-Stressor CatBoost ML Pipeline for Predicting Metal/Antibiotic Stress Phenotypes

## Summary

This project trains per-stressor CatBoost classifiers and regression models to predict metal/antibiotic stress phenotypes in ENIGMA bacterial isolates using protein sequence composition features alone. The pipeline is well-conceived and scientifically sound at its core: organism-aware train/test splitting (GroupShuffleSplit) prevents within-organism data leakage, the shift from binary classification to regression is a principled response to extreme class imbalance, and the REPORT is unusually candid about limitations including sparse training data for Cd/Mn, the feature-selection contamination caveat, and the modest absolute effect sizes (ρ=0.05–0.23). A prior adversarial review (ADVERSARIAL_REVIEW_ROUND1.md) identified several critical concerns, most of which the REPORT has now addressed. The main remaining gaps are: (1) the figures/ directory is empty — no saved visualizations exist in the project; (2) NB07 and NB08 have zero executed outputs; (3) NB04 feature evaluation demonstrably ran without organism filtering (code confirmed), yet the REPORT's caveat buries this; and (4) NB06 LOGO cross-validation is acknowledged as incomplete. These are addressable issues that stop short of invalidating the core findings, but should be resolved before submission.

---

## Methodology

**Research question**: The question is clearly stated and testable — can protein sequence composition predict metal/antibiotic stress fitness phenotypes across ENIGMA isolates? The progression from binary classification to regression is well-motivated and the per-stressor modelling structure is appropriate for the data.

**Organism-aware splitting**: NB05's `train_stressor()` function correctly implements GroupShuffleSplit to keep all proteins from a given organism in the same fold. This is the right design choice and prevents the most common form of data leakage in this setting.

**Missing-data contamination fix**: The org-filter (restricting each stressor model to organisms that actually ran RB-TnSeq experiments for that stressor) is correctly implemented in NB05. The REPORT's "Missing-Data Contamination Fix" section explains the issue and fix clearly, with a supporting table showing true vs. apparent positive rates.

**Feature selection (NB04) — confirmed without org-filter**: Code inspection of `04_Feature_Evaluation.ipynb` Cell 4 shows no organism filtering before the train/test split:

```python
groups = labeled_pd['organism']
gss = GroupShuffleSplit(n_splits=1, test_size=CONFIG['TEST_SIZE'], random_state=CONFIG['SEED'])
train_idx, test_idx = next(gss.split(labeled_pd, labeled_pd[test_stressors[0]], groups=groups))
```

This operates on the global `labeled_pd`, not a stressor-filtered subset. File timestamps confirm NB04 ran on June 26 before the org-filter fix was applied in NB05 on June 29. The REPORT acknowledges this in Limitations #4 ("NB04 ran on contaminated labels"), but presents it as a minor caveat rather than a material concern. The direction of bias — whether simpler features (aa+kmer2) were artificially favoured by the false-negative pattern — is unknown and not characterized. The AUC margin between best and second-best feature combination is only 0.002, making this uncertainty consequential.

**Mn and Cd edge cases**: The Mn (ρ=0.050, 4 organisms) and Cd (2 organisms, AUC=0.556) limitations are disclosed in the REPORT. The Mn caveat is present but appears only as a parenthetical footnote in the results table rather than in the Limitations list. Cd's speculative nature for the 58 untested organisms is acknowledged explicitly.

**LOGO cross-validation (NB06)**: `06_Model_Evaluation.ipynb` has 4 of 6 code cells executed and the LOGO loop is running (cells 4–5 have logged output), but results are not included in the REPORT — listed as Limitation #7 and Future Direction #1. This means phylogenetic generalization has not been formally quantified.

**Reproduction guide**: The README Reproduction section lists which notebooks require Spark (NB01 only) and which run locally — sufficient for basic orientation. A single orchestration script and explicit runtimes would strengthen this further.

---

## Code Quality

**NB05 `train_stressor()` function**: Well-written with appropriate guard conditions (`MIN_POSITIVES=30`, `n_orgs < 3` skip). Platt calibration handles the case where the calibration set is too small. `auto_class_weights='Balanced'` addresses class imbalance at the model level. The threshold sweep (Cell 8) is post-hoc on test predictions — correct. This is the cleanest code in the pipeline.

**NB04 feature evaluation**: Technically correct for evaluating features on the full dataset, but lacks the org-filter introduced in NB05. Only 1 of 8 code cells has saved output (a pair of INFO-level log timestamps), which is insufficient to confirm the evaluation completed successfully or to show AUC values inline without re-running.

**NB09 (Isolate Prediction) — fully executed**: All 7 code cells have saved outputs. This is the most important notebook for the novel-candidate deliverable and is the only core notebook that is fully reproducible from file inspection.

**src/ utilities**: `src/utils.py` and `src/feature_extraction.py` provide clean helper functions. The notebooks use `sys.path.insert` to load them — functional but fragile if the working directory changes. No `__init__.py` is present so this is not importable as a package.

**Pitfall adherence**: The project correctly avoids several relevant BERDL pitfalls: Spark is used only for NB01 (database queries); fitness data is read from downloaded TSV files, sidestepping the `CAST(fit AS DOUBLE)` string-type pitfall in `kescience_fitnessbrowser`; GroupShuffleSplit prevents within-organism leakage. The short ENIGMA strain-name collision pitfall (docs/pitfalls.md §1) is not directly applicable since protein sequences are sourced from the genome depot rather than linked via GTDB strain identifiers.

**No requirements.txt**: There is no `requirements.txt` in the project directory. CatBoost, scikit-learn, scipy, pandas, pyarrow, and matplotlib are all used. A future collaborator cannot determine the required dependency versions from the project files alone.

**Untitled.ipynb**: An `Untitled.ipynb` is present in the notebooks directory and should be removed before submission.

---

## Findings Assessment

**Finding 1 (regression outperforms classification)**: Well-supported. Binary F1 values for metals are near-zero (Cr F1=0.000, Zn F1=0.030) confirmed in `final_model_performance.csv`, while regression Spearman correlations are positive and significant for 10 of 11 metals. The REPORT correctly frames regression output as "relative ranking" rather than "prediction of positives."

**Finding 2 (aa+kmer2 feature selection)**: Directionally supported by `feature_evaluation_results.csv`, but the 0.002 AUC margin between aa+kmer2 (0.656) and the next-best combination (0.654) is near-noise, and the evaluation used contaminated labels. The conclusion that "coarse amino acid composition drives the signal" is plausible but the supporting evidence is weaker than the REPORT implies.

**Finding 3 (abiotic stressors more predictable)**: Well-supported. UV (AUC=0.824), Ethanol (AUC=0.804), and Acid (AUC=0.771) are substantially higher than the best metal model. The table directly supports the comparison.

**Finding 4 (novel candidate ranking)**: The interpretation is appropriately conservative — the REPORT explicitly states "only relative ordering within each organism is meaningful" and that 99% of novel candidates do not cross the binary-positive threshold. The adversarial review flagged `acidovorax_3H11|Ac3H11_638` (L(+)-tartrate dehydratase beta subunit) as overclaimed for multi-metal essentiality; the REPORT now frames it as "broad stress essentiality" — still speculative. The data shows Co_fit=−2.82 (strong Co signal) but other metal fitness values are −0.29 to −1.07, none crossing −2.0. A metabolic enzyme ranking top-50 for all 11 metals is more likely to reflect general sequence-composition bias than metal-specific resistance.

**Per-organism validation (TEST organisms only)**: The REPORT now explicitly labels this section "TEST Organisms Only" and discloses notable failures (PS/Ni ρ=−0.142, Caulo/Zn ρ=−0.013). This addresses the primary concern raised in the adversarial review.

**Discoveries section**:
- *Mercury resistance signature (AUC=0.774)*: Directly traceable to `regression_model_metrics.csv`. Hg ranks first by AUC despite 9 training organisms. The biological rationale (*mer* operon conservation) is well-supported in the literature cited.
- *Amino acid composition sufficiency*: Supported by `feature_evaluation_results.csv`. The claim's scope (limited to this dataset scale and feature space) is accurate. The contamination caveat should be noted alongside this discovery.

Both discoveries are legitimate cross-project candidates and the applies-to scopes are not overgeneralized.

**Limitations acknowledged**: The REPORT's 7-item Limitations section is thorough and honest. The most important concerns (class imbalance, sparse Cd/Mn, feature selection bias, LOGO pending, OOD Cd predictions, calibration of novel predictions) are all present. The Mn model caveat needs elevation from a table footnote to an explicit Limitations bullet.

**Figures**: The figures/ directory is empty. No visualizations are saved anywhere in the project hierarchy. All visual results (AUC comparisons, per-organism ρ distributions, feature-evaluation plots) would need to be regenerated from scratch by any reader verifying the findings. This is a significant reproducibility gap for a project at the "analysis complete" stage.

---

## Suggestions

1. **[Critical] Populate the figures/ directory.** The `figures/` directory is completely empty. A project at "analysis complete" status should have key visualizations saved. At minimum generate: (a) bar chart of AUC-from-ranking per metal (easy from `regression_model_metrics.csv`), (b) predicted vs. actual fitness scatter for Hg and Co TEST organisms, (c) feature-combination AUC comparison from NB04. Without figures, the reader must re-run the full pipeline to see any result.

2. **[Critical] Elevate the NB04 contamination caveat in Finding 2.** Currently Limitations #4 is buried in the Limitations list. Finding 2 in the REPORT should include a highlighted note: *"Note: feature ranking was performed on training data that included ~100K false-negative proteins from untested organisms. The AUC margin between the best combination (0.656) and the next-best (0.654) is 0.002, within potential bias range. Feature selection should be re-run on org-filtered data before treating aa+kmer2 as a definitive conclusion."*

3. **[Critical] Add requirements.txt.** List at minimum: `catboost`, `scikit-learn`, `scipy`, `pandas`, `pyarrow`, `matplotlib`, `seaborn`, `numpy`. This is a baseline reproducibility requirement.

4. **[Important] Elevate the Mn model caveat to the Limitations list.** Mn (ρ=0.050, 4 organisms, single test organism DvH) currently appears only as a table footnote. Add a Limitations bullet: *"Mn model (ρ=0.050, 4 training organisms, single test organism): statistically marginal (p=0.009, fails Bonferroni correction at α=0.0045) and potentially unstable. Mn rankings for untested organisms should be treated with high skepticism."*

5. **[Important] Resolve NB07 and NB08 ambiguity.** Both notebooks have zero executed cells. If these are intentionally out of scope, add a markdown cell at the top of each stating they are exploratory and not part of the submitted pipeline. If they are expected outputs, execute them. Leaving zero-output code notebooks in the project directory implies they were run and produced nothing, which is confusing.

6. **[Important] Qualify the multi-metal candidate interpretation.** The description of `acidovorax_3H11|Ac3H11_638` as showing "broad stress essentiality" is not supported by the actual fitness values (Co_fit=−2.82; all other metals −0.29 to −1.07). Revise to: *"This protein shows confirmed Co essentiality (fitness=−2.82) and ranks top-50 by model score for all 11 metals. However, actual fitness values for non-Co metals are weak (all above −1.1), suggesting Co-specific rather than broad-metal essentiality. The multi-metal ranking may reflect general sequence-composition bias."*

7. **[Moderate] Complete NB06 LOGO cross-validation and include results in the REPORT.** NB06 is already partially executed. LOGO AUC would materially strengthen or qualify the generalizability claims. If LOGO AUC for metals is substantially lower than single-split AUC, the novel candidate rankings need additional caveats. This is listed as Future Direction #1 and should be resolved before the project is submitted for archival.

8. **[Moderate] Apply multiple-testing correction to Spearman p-values.** The REPORT evaluates 11 regression models simultaneously. With α=0.05, one false positive is expected by chance. The Mn result (p=0.009) fails Bonferroni-corrected α=0.0045. Either note this or adjust α. The REPORT currently implies all 11 models show "statistically significant" results without qualification.

9. **[Minor] Remove Untitled.ipynb** from the notebooks directory before submission.

10. **[Minor] Add expected runtime estimates to the README Reproduction section.** NB03 (ESM-2 embeddings) requires GPU or high-memory CPU; NB05 (46 stressors + 11 regression models, CatBoost) takes several hours on CPU. Stating these helps future reproducers plan resources.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-06-29
- **Scope**: README.md, REPORT.md, ADVERSARIAL_REVIEW_ROUND1.md, beril.yaml, references.md, 9 notebooks (NB01–NB09 + Untitled.ipynb), ~30 data files, 0 figures, src/ utilities, scripts/, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:93e0fe6d6cfb7a59d49975ee786fed50296d10155d208ea91e1bc3426b549c30 -->
