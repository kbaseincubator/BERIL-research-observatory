---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-06-29
project: enigma_general_essentiality
---

# Review: Cross-Stressor Conditional Essentiality Prediction in ENIGMA Isolates

## Summary

This project is a clean, well-executed methodological correction of a prior flawed implementation
(`projects/refocus/`). All three notebooks ran to completion with outputs saved, all key artifacts
are committed, and the five corrected flaws are explicitly documented. The pipeline is appropriately
scoped to local execution (no Spark required), and the numbers in REPORT.md trace directly to
notebook cell outputs and `data/model_metrics.json`. The main areas for improvement are operational
rather than scientific: there is no `requirements.txt`, no `## Reproduction` section in the README,
and the positional row-alignment assumption in NB02 is verified only by row count, not by protein
ID. One methodological note warrants attention: the reported threshold (0.521, labeled "max F1")
appears to have been tuned on the test set, which inflates the MCC metric; AUC is unaffected.
The "genus-level LOGO" framing in the headline is partially accurate but needs a more prominent
caveat — 25 of 32 folds hold out exactly one organism (effectively LOOO), and only 5 folds are
genuinely multi-organism.

## Methodology

**Research question and hypotheses**: H1 is clearly stated and testable (LOGO AUC > 0.55 for
union binary label on held-out organisms). H0 is the explicit null. H2 is appropriately flagged
as exploratory. The union binary label derivation (fitness < −2 in ANY tested condition) is
biologically sensible and the expected positive rate (~4–8% per plan; observed 12.58% total,
which is within the published 5–25% range for conditional essentiality definitions) is plausible.

**Methodological corrections**: The five corrections from the prior `refocus/` implementation are
clearly documented in the README and REPORT. The train/test organism overlap is programmatically
verified (`Organism overlap: 0 ✓`, NB01 cell 4). The genus mapping is explicitly manual and
transparent, with a 60-organism table committed in NB01 cell 2. The derivation of `scale_pos_weight`
from the training-set negative/positive ratio (6.44) is correct and matches `model_metrics.json`.

**H2 evaluation**: The comparison of union LOGO AUC (0.618) to enigma_stress_phenotype_ml per-metal
LOGO AUC range (0.53–0.62) is confounded by evaluation methodology differences — the predecessor
project used organism-level LOGO while this project uses genus-level LOGO. The REPORT acknowledges
this caveat, but H2 is stated as "consistent with" the hypothesis rather than "untestable without
matched evaluation." A more direct comparison (re-running per-stressor models under genus-level LOGO)
would make H2 testable; as-is, the claim is suggestive but not confirmatory.

**Reproducibility of data lineage**: The project reuses pre-computed feature files from
`enigma_stress_phenotype_ml/data/`, which is appropriate (avoids redundant computation). However,
this inter-project dependency is not flagged as a prerequisite in the README, and no Spark session
is needed because NB01 simply reads a parquet file rather than querying FitnessBrowser directly.
This is correct per the stated approach but means the project cannot be run in isolation without
the sibling project's data artifacts.

## Code Quality

**Notebook organization**: The three-notebook structure (data → features → model) is logical and
clean. Each notebook has a clear purpose and all 26 code cells across the three notebooks have
saved outputs.

**Organism-stratified split**: Correctly implemented with `GroupShuffleSplit` and a programmatic
assertion that organism overlap is zero (NB01 cell 4, `Organism overlap: 0 ✓`).

**Genus-level LOGO implementation**: `LeaveOneGroupOut` with `groups = genera_train` is correctly
applied to the training set only (NB03 cell 5), each fold holds out ALL proteins from ALL organisms
of one genus, and folds with fewer than 5 positive proteins are flagged and excluded from
aggregates. This is methodologically correct.

**Positional alignment in NB02 (medium concern)**: Features are sliced with `aa.iloc[train_ids]`,
where `train_ids` are row positions from `labeled_pd.parquet`. The alignment check in NB02 cell 2
verifies only that `features_aa.parquet` has 215,051 rows — it does not verify that the row
ordering of the feature file matches `labeled_pd.parquet`. If row ordering ever diverges (e.g.,
a future re-export of features with sorting), the mapping would be silently corrupted. Adding a
protein-ID–level assertion (e.g., `assert (aa['protein_id'].values == labeled_pd['protein_id'].values).all()`) would close this gap and make the pipeline robust across regenerations of the feature files.

**Threshold tuning (mild concern)**: The Results table labels the threshold as "Test threshold
(max F1)" at 0.521. Based on NB03 cell 3's output showing the confusion matrix computed at that
threshold *on the test set*, the threshold appears to have been found by optimizing F1 over the
test set rather than a held-out validation portion of training (as specified in the RESEARCH_PLAN:
"Threshold-tune on validation set, not test set"). This is a minor issue because AUC-ROC is
threshold-independent and is the headline metric; the MCC of 0.149 may be slightly inflated by
test-set threshold selection. Reporting MCC at a fixed threshold (0.5) or tuning on a
cross-validation split of training would make this metric fully clean.

**`catboost_info/` location**: CatBoost training artifacts (`catboost_info/learn_error.tsv`,
`catboost_info/time_left.tsv`, etc.) are saved inside `notebooks/` rather than `data/`. These
are intermediate artifacts and should be excluded via `.gitignore` or moved to `data/` to keep
the notebooks directory clean.

**Pitfall awareness**: The project correctly avoids the ENIGMA short-strain-name collision pitfall
by using a manual genus mapping table rather than `str.split().str[0]` (documented in
`docs/pitfalls.md` under `[genotype_to_phenotype_enigma]`). The "Commit Notebooks Alongside
Their Artifacts" pitfall is also addressed — all three notebooks are committed with outputs.
No Spark queries are issued, so the `get_spark_session()` and REST API pitfalls are not applicable.

## Findings Assessment

**Numerical consistency**: All key numbers in REPORT.md are traceable to notebook outputs and
`model_metrics.json`:
- Test AUC 0.659 → NB03 cell 3 output `AUC-ROC: 0.6594`, model_metrics.json `0.6594182...` ✓
- LOGO AUC 0.618 ± 0.037 → NB03 cell 7 output `AUC: 0.6180 ± 0.0369` ✓
- Positive rate 12.58% (27,061 / 215,051) → NB01 cell 3 output `Essential: 27,061 (12.58%)` ✓
- Per-genus LOGO table in REPORT matches NB03 cell 5 fold-by-fold outputs (values rounded
  to 3 decimal places)

**Minor framing issue — positive rate context**: The REPORT Key Findings paragraph states
"positive rate of 12.58%... requiring `scale_pos_weight = 6.44`." The scale_pos_weight of 6.44
was computed from the *training set* positive rate (13.44%), not the total rate (12.58%). If
computed from 12.58% the weight would be ~6.95. The values in `model_metrics.json` confirm
6.44 came from the training set; the paragraph should say "training-set positive rate of 13.44%"
or explicitly note both rates to avoid implying 6.44 was derived from 12.58%.

**LOGO qualification**: The headline "mean AUC of 0.618 ± 0.037... across 27 reliable folds" is
factually correct but the "genus-level" label overstates generalization. Of the 27 reliable folds:
5 are genuinely multi-organism (Pseudomonas n=10, Ralstonia n=4, Dickeya n=2, Methanococcus n=2,
Bacteroides n=2) and 22 hold out exactly one organism (i.e., LOOO). Only the 5 multi-organism
folds test whether organisms from a *new genus* can be predicted from data that excludes all
same-genus organisms. The Limitations section acknowledges this ("25 of 32 LOGO folds contain
only one organism"), but this caveat should appear in the Key Findings section alongside the
headline AUC, not only in Limitations.

**Conclusions are supported**: H1 is clearly supported. The biological interpretation (housekeeping
proteins have distinctive sequence composition regardless of stressor) is reasonable and consistent
with cited literature. Limitations are thorough and honest. The comparison to Ning et al. (2014)
and Deng & Lu (2011) is appropriate with explicit acknowledgment of evaluation strictness
differences.

**Figures**: Both figures are present and described. Figure labels/axes are not visible to the
reviewer from markdown, but the REPORT descriptions (`nb03_logo_auc.png`: "LOGO AUC distribution
by genus (rank-ordered bars) and n_positives vs. AUC scatter"; `nb03_feature_importance.png`:
"Top 30 CatBoost feature importances") are informative.

### Discoveries Assessment

The REPORT includes three entries under `## Discoveries`:

1. **"Sequence composition (aa + kmer2) carries cross-stressor essentiality signal transferable across
   phylogenetically distant ENIGMA taxa (LOGO AUC = 0.618 ± 0.037 across 27 genera, range
   0.543–0.686)"** — Well-supported by NB03 results. Scope is appropriately bounded to ENIGMA
   RB-TnSeq. Claim is accurate with the caveat noted above (22/27 folds are LOOO). Consider
   rephrasing to "across 27 LOGO folds (5 genuinely multi-organism genera)."

2. **"Deep-branching taxa with highly specialized lifestyles (Mycobacterium, Bifidobacterium,
   Synechococcus) show the poorest cross-genus generalization"** — Well-supported by per-genus
   LOGO results (AUC 0.543, 0.545, 0.561 respectively vs. median ~0.618). The biological
   interpretation (phylogenetically idiosyncratic essentiality) is plausible and consistent with
   Deng & Lu (2011). Scope is appropriately ENIGMA-specific.

3. **"ENIGMA strain codes do not follow binomial nomenclature; `str.split().str[0]` is a silent
   LOOO masquerading as LOGO"** — Accurate and important, but this is a **methodological
   pitfall**, not a cross-project scientific discovery. It belongs in `docs/pitfalls.md` under
   `[enigma_general_essentiality]` (it is currently absent from that file). Removing it from
   Discoveries and adding it to pitfalls.md would ensure it is surfaced for future ENIGMA
   projects without inflating the scientific discoveries count.

## Suggestions

1. **[Reproducibility, high priority]** Add a `requirements.txt` with pinned versions of
   `catboost`, `scikit-learn`, `pandas`, `numpy`, and `pyarrow` used in NB01–NB03. The README
   mentions the packages needed but does not pin versions; CatBoost model serialization (`.cbm`)
   can be version-sensitive.

2. **[Reproducibility, high priority]** Add a `## Reproduction` section to the README documenting:
   (a) the prerequisite that `enigma_stress_phenotype_ml/data/` must exist (i.e., that sibling
   project must have been run first); (b) that all three notebooks run locally (no Spark needed);
   and (c) the expected execution order and approximate runtimes (NB03 trains CatBoost + 32 LOGO
   folds, likely 5–15 minutes).

3. **[Correctness, medium priority]** Strengthen the row-alignment check in NB02 cell 2 to
   verify protein ID ordering, not just row count. Example: load `labeled_pd.parquet` into NB02
   and assert `(aa.index == labeled_pd.index).all()` or equivalent. This guards against future
   regeneration of feature files with different row ordering silently corrupting the mapping.

4. **[Correctness, medium priority]** Clarify threshold tuning. If the test threshold (0.521)
   was found by optimizing F1/MCC over the test set, note this explicitly in the REPORT: "MCC
   is reported at the threshold that maximized F1 over the test set; AUC is threshold-independent
   and not affected." Consider also reporting MCC at threshold=0.5 as a no-tuning baseline for
   comparison.

5. **[Findings clarity, medium priority]** Move the "genus-level" LOGO qualification out of
   the Limitations section and into the Key Findings paragraph. Suggest: "Genus-level LOGO AUC
   = 0.618 ± 0.037 (27 reliable folds; 5 multi-organism genera, 22 single-organism folds
   equivalent to LOOO)." This avoids overstating generalization in the headline while keeping
   the legitimate result.

6. **[Pitfall documentation, low priority]** Move Discovery #3 (ENIGMA strain codes as LOOO
   trap) from the Discoveries section into `docs/pitfalls.md` under a new
   `[enigma_general_essentiality]` entry. This pitfall applies to any future project that
   attempts genus-level LOGO over ENIGMA FitnessBrowser organisms and should be surfaced through
   the pitfall archive rather than the per-project discoveries channel.

7. **[Correctness, low priority]** In REPORT Results table, the `scale_pos_weight` row and the
   preceding sentence about "positive rate of 12.58%" are adjacent in a way that implies 6.44
   was computed from 12.58%. Clarify that 6.44 = 144,299 / 22,406 (training-set negatives /
   positives), not from the overall 12.58% rate (which would give ~6.95).

8. **[Housekeeping, low priority]** Move `notebooks/catboost_info/` to `data/catboost_info/`
   or add it to `.gitignore`. CatBoost training artifacts (learn_error.tsv, time_left.tsv,
   events.out.tfevents) are intermediate outputs that clutter the notebooks directory and
   are not needed for reproducibility (the `.cbm` model in `data/` is sufficient).

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-06-29
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, beril.yaml, references.md, 3 notebooks
  (26 code cells with outputs), 16 data files, 2 figures, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input,
  not a definitive assessment.

<!-- report_hash: sha256:85f89aecfe6c5b1142884c29fc25ddd9b437ce9d0b7cdb22ce0153a8e6ad1c6d -->
