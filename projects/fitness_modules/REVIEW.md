---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This is an ambitious and well-executed project that decomposes RB-TnSeq fitness compendia from 32 bacteria into 1,116 stable ICA modules, aligns them across organisms via ortholog fingerprints into 156 cross-organism families, and generates 6,691 function predictions for hypothetical proteins. The pipeline is logically structured across 7 notebooks with clean separation of concerns, substantial cached intermediate data, a standalone benchmark script, and thorough documentation. The project's strongest quality is its intellectual honesty: it benchmarks Module-ICA against baselines, reports near-zero strict KO precision, and explains *why* that is expected (granularity mismatch between gene-level KOs and process-level modules) rather than hiding the result. Validation is compelling — 94.2% of modules show significantly elevated within-module cofitness and 22.7× genomic adjacency enrichment. The main areas for improvement are: an inconsistency between the README summary (878 predictions) and the actual output (6,691), the absence of saved outputs in the two Spark-dependent notebooks (NB01–02), and the remaining work to resolve PFam/TIGRFam IDs to human-readable function descriptions in predictions.

## Methodology

**Research question**: Clearly stated, testable, and well-motivated. The three-part question — decompose fitness data into modules, align across organisms, predict function — maps directly to notebooks 03–06, with NB07 providing formal evaluation.

**Approach**: Sound and methodologically rigorous. The pipeline follows the Borchert et al. (2019) framework with meaningful extensions: Marchenko-Pastur eigenvalue thresholding for component selection, 30–50× FastICA restarts with DBSCAN stability filtering, Fisher exact enrichment with BH FDR correction across four annotation databases (KEGG, SEED, TIGRFam, PFam), ortholog-group fingerprinting via connected components, and hierarchical clustering into module families. The extension from a single organism to a 32-organism pan-bacterial framework with cross-organism alignment is a genuine advance over the original method.

**Data sources**: Clearly identified in the README with a table mapping each `kescience_fitnessbrowser` table to its use. The SQL queries throughout correctly apply documented pitfalls — proper KEGG join paths, `CAST(... AS FLOAT)` for string-typed columns, and `seedannotation` instead of `seedclass`.

**Reproducibility**:
- **Reproduction guide**: The README includes a thorough `## Reproduction` section (lines 127–152) with prerequisites, step-by-step `nbconvert` commands, clear Spark/local separation, and runtime estimates. The standalone benchmark command (`python src/run_benchmark.py`) enables independent validation.
- **Notebook outputs**: NB03–07 all have saved outputs across all code cells — text tables, progress logs, and embedded figures. NB01–02 have zero saved outputs across 18 code cells. This is documented with a header note ("outputs are not saved in git"), which is understandable for Spark notebooks, but means a reader cannot see the organism selection rationale without JupyterHub access.
- **Figures**: 8 substantive PNG files in `figures/` cover all major analysis stages: PCA eigenvalues, module sizes, enrichment summary, module families, prediction summary, validation summary, and both benchmark charts (strict and neighborhood).
- **Dependencies**: A `requirements.txt` with 7 packages and minimum version constraints is present.
- **Caching**: All notebooks implement file-existence checks for idempotent re-execution. All 32 organisms have ICA parameter JSON files recording exact hyperparameters.
- **Spark/local separation**: Clearly documented and well-implemented. NB04 and NB05 even separate Spark (Part 1) and local (Part 2) sections within a single notebook.

## Code Quality

**SQL correctness**: All queries are correct and demonstrate awareness of documented pitfalls:
- String-to-numeric casting consistently applied: `CAST(cor12 AS FLOAT)` in NB01 cell 9, `CAST(fit AS FLOAT)` in NB02 cell 8.
- The KEGG join path in NB04 cell 4 correctly routes through `besthitkegg` with proper composite keys (`bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId`), matching the `docs/pitfalls.md` warning about `keggmember` lacking `orgId`/`locusId` columns.
- SEED annotations use `seedannotation.seed_desc` (NB04 cell 4), correctly avoiding the misleading `seedclass` table.
- The `ecnum` column name is correctly used for `kgroupec`.
- Experiment quality filtering (`cor12 >= 0.1`) and gene missingness filtering (`≤50% missing`) in NB02 cell 9 are reasonable data quality controls.

**Statistical methods**: Appropriate throughout:
- Fisher exact test with BH FDR correction for module enrichment (NB04 cell 6) — the contingency table is correctly constructed with `alternative='greater'`.
- Mann-Whitney U test for within-module cofitness validation (`run_benchmark.py` lines 613–623).
- Marchenko-Pastur eigenvalue thresholding for component selection (`ica_pipeline.py` lines 50–57), with a sensible 40% cap on components relative to experiments.
- The confidence score in NB06 (`|gene_weight| × -log10(FDR) × (1 + cross_org_bonus)`) is a reasonable ranking heuristic, though uncalibrated.

**ICA pipeline (`src/ica_pipeline.py`)**: Clean, well-documented (295 lines), and technically correct:
- Cosine distance clipping (`np.clip(cos_dist, 0, 1, out=cos_dist)`, line 146) correctly addresses the documented floating-point pitfall.
- Component sign alignment within DBSCAN clusters (lines 159–163) is properly handled via dot-product with a reference vector before centroid averaging.
- Zero-variance genes handled in `standardize_matrix` (line 292: `stds[stds == 0] = 1`).
- The `threshold_membership` function correctly implements the adaptive approach: keep all genes above `min_weight`, cap at `max_members` by taking highest |weight|.

**Benchmark script (`src/run_benchmark.py`)**: Comprehensive (749 lines) and well-structured:
- Proper train/test separation (20% holdout, `random_state=42`) prevents data leakage.
- Four methods evaluated at two levels (strict KO match and neighborhood set overlap).
- Vectorized Pearson correlation matrix computation for cofitness is efficient.
- Both cofitness validation and genomic adjacency validation included as separate sections.
- All outputs saved to CSV for reproducibility.

**Pitfall awareness**: Outstanding. The project has contributed 7 fitness-browser-specific pitfalls to `docs/pitfalls.md` (all tagged `[fitness_modules]`), including: `fitbyexp_*` long-format discovery, KEGG join path, `seedclass` schema correction, cosine distance clipping, D'Agostino K² thresholding failure, ortholog scope requirement, enrichment `min_annotated` threshold, and ICA component ratio cap.

**Potential issues identified**:
1. In `run_benchmark.py`, `ortholog_predict` (line 174–196) takes the first BBH hit found with a KEGG annotation (`break` on line 196), meaning prediction depends on arbitrary row ordering rather than ortholog quality (the `ratio` column is available but unused for sorting). This is unlikely to materially affect the 95.8% precision result but is imprecise.
2. The cofitness validation uses p < 0.05 per module without multiple-testing correction across ~1,114 modules. Given the 94.2% pass rate, FDR correction would likely not change the conclusion, but it would be methodologically consistent with the BH correction used in NB04's enrichment analysis.
3. NB02 cell 8's `extract_fitness_matrix_fitbyexp` function attempts to use `fitbyexp_*` tables as pre-pivoted wide format, but the documented pitfall notes these are long format. The function would fail silently, triggering the correct `genefitness` fallback. This dead code path is misleading but harmless.

**Notebook organization**: Excellent. Each notebook follows a consistent pattern: markdown header with scope/requirements → imports/setup → numbered analysis sections → summary/save. The Part 1/Part 2 pattern in NB04 and NB05 (Spark extraction vs. local analysis) is practical. Progress messages are informative.

## Findings Assessment

**Conclusions supported by data**: Yes, strongly.
- **1,116 stable modules** across 32 organisms — verified by NB03 cell 8 output showing 1,117 stable modules with 1,116 having members, consistent with 32 JSON parameter files.
- **94.2% cofitness enrichment** — backed by `cofitness_validation.csv` (1,049/1,114 modules enriched, Mann-Whitney p < 0.05). Per-organism results in NB07 cell 9 show 100% enrichment for 17 organisms and >75% for all but 3.
- **22.7× genomic adjacency enrichment** — backed by `adjacency_validation.csv` with per-organism values from 4.1× to 66.8× (NB07 cell 11).
- **156 cross-organism families** (28 spanning 5+, 7 spanning 10+, 1 spanning 21) — verified by NB05 cell 9 output and `module_families.csv`.
- **6,691 function predictions** (2,455 family-backed, 4,236 module-only) — verified by NB06 cell 6 output and `all_predictions_summary.csv` (6,692 lines including header).
- **Benchmark results** — ortholog transfer at 95.8% precision, domain at 29.1%, Module-ICA and cofitness at <1% — confirmed in NB07 cell 3 with per-organism standard deviations.

**Limitations well-acknowledged**:
- The KO-level precision limitation is explicitly discussed (README lines 107–108, NB07 cell 6 markdown) with a clear quantitative explanation: ~1.2 genes per unique KO means P(match) ≈ 1/20 for a typical module.
- The D'Agostino K² thresholding failure is documented in README Key Findings #1, with the specific problem (100–280 genes/module, 59% enrichment) and solution (absolute weight threshold giving 5–50 genes, 94% enrichment).
- Module-ICA is explicitly characterized as "complementary" to sequence-based methods, not a replacement (README line 125, NB07 cell 13).
- TIGRFam/PFam ID resolution listed as remaining work (README line 86).

**Inconsistency**: The README summary section (line 83) states "6,691 function predictions for hypothetical proteins (2,455 family-backed, 4,236 module-only)" which matches NB06 output. However, the same README also mentions "878 predictions" on line 3 of the Status section — this appears to be a stale number from an earlier pipeline iteration. The NB07 summary cell (cell 13) references "878 function predictions" which is also outdated. These should be reconciled to 6,691.

**Incomplete analysis**: The top-10 highest-confidence predictions in NB06 cell 6 display raw PFam IDs (e.g., "PF00356", "PF00460") without human-readable descriptions. Similarly, family annotations in NB05 cell 11 show PFam IDs. This is acknowledged as remaining work but does limit the reader's ability to assess biological plausibility of predictions.

**Visualizations**: All 8 figures are present, properly generated, and cover key analysis stages. The validation summary figure (NB07 cell 12) is particularly effective, showing within-module vs. background cofitness with color-coding and adjacency enrichment side by side. The enrichment summary (NB04 cell 9) shows both per-organism annotation rates and database breakdown.

## Suggestions

1. **[Critical] Reconcile prediction counts in README and NB07.** The README Status section (line 83) and NB07 summary (cell 13) reference "878 predictions" while the actual output is 6,691. Update all references to the current count. The 878 number appears to be from an earlier iteration before PFam was added and `min_annotated` was lowered.

2. **[High] Resolve TIGRFam/PFam IDs to human-readable descriptions.** This is already acknowledged as remaining work. The `genedomain` extraction in NB04 cell 4 already captures `domainName` and `definition` columns — a join in NB06 from `domainId` to `definition` would make the predictions interpretable (e.g., "PF00460" → "Disulfide isomerase" rather than a cryptic ID).

3. **[Medium] Add outputs or summaries to NB01–02.** These 18 code cells have zero saved outputs. Options: (a) re-run and save with `nbconvert --execute --inplace`, (b) add markdown cells with key tabular results (e.g., "48 organisms surveyed, 32 selected with ≥100 experiments"), or (c) include representative screenshots. This would let readers understand the data landscape without cluster access.

4. **[Medium] Add confidence threshold guidance for predictions.** The 6,691 predictions span a wide confidence range (0.41–14.77, median 1.32). No guidance is provided on which predictions are most trustworthy. A brief analysis — e.g., precision vs. confidence threshold on the held-out benchmark set — would help downstream users filter predictions appropriately.

5. **[Medium] Apply FDR correction to cofitness validation.** The 94.2% enrichment uses per-module p < 0.05 across ~1,114 tests without multiple-testing correction. Applying BH correction (as already done in NB04) would be methodologically consistent and preempt reviewer concerns. The result is almost certainly robust given the effect sizes.

6. **[Low] Sort ortholog hits by ratio in `run_benchmark.py`.** The `ortholog_predict` function takes the first BBH hit with a KEGG annotation. Sorting `org_bbh` by the `ratio` column (descending) before iteration would ensure the highest-quality ortholog is used first.

7. **[Low] Rename `pilot_organisms.csv` and `pilot_ids` variable.** The file now contains all 32 organisms. Renaming to `selected_organisms.csv` and updating `pilot_ids` to `org_ids` (as NB07 already uses) would reduce confusion. The README still refers to "pilot organisms" in the project structure.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks (NB01–07), 2 source files (`src/ica_pipeline.py`, `src/run_benchmark.py`), `requirements.txt`, ~500 data files across 6 subdirectories, 8 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
