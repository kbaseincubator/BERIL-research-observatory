---
reviewer: BERIL Automated Review
date: 2026-02-16
project: env_embedding_explorer
---

# Review: AlphaEarth Embeddings, Geography & Environment Explorer

## Summary

This is a strong exploratory project that systematically characterizes the AlphaEarth environmental embeddings in BERDL. The project follows a clean two-notebook pipeline (Spark extraction then local analysis), produces 14 publication-quality figures with both static and interactive versions, and delivers four genuinely useful outputs: a merged embeddings-plus-environment dataset, a coordinate quality classification, a reusable environment harmonization mapping, and a stratified distance-decay analysis showing that environmental samples exhibit 3.65x stronger geographic signal than human-associated samples. Documentation is exemplary — the three-file structure (README, RESEARCH_PLAN, REPORT) is fully realized, the REPORT includes literature context with five cited papers, and limitations are honestly enumerated. Both notebooks are committed with saved outputs, addressing a known pitfall. The main issues are numeric inconsistencies between the REPORT prose and the actual notebook outputs, a genome count discrepancy after the UMAP merge step, and the absence of formal statistical tests for the key comparisons.

## Methodology

**Research question**: Clearly framed as exploratory characterization with four specific expectations (E1-E4 in RESEARCH_PLAN.md) that map directly onto analysis sections. The honest framing as "exploratory/characterization" rather than hypothesis-driven is appropriate and well-communicated.

**Approach**: Logically sequenced. NB01 handles Spark extraction and EAV pivoting; NB02 handles all downstream analysis locally from cached CSVs. Key methodological choices are well-justified:
- L2-normalization before UMAP to approximate cosine distance with Euclidean (cell 22, NB02) — correctly motivated and matches the pitfall documented in `docs/pitfalls.md`.
- Subsample-fit/full-transform UMAP (20K fit, 79K transform) — good performance optimization with cached coordinates for reproducibility.
- Coordinate QC heuristic (>50 genomes AND >10 species) — simple, transparent, with acknowledged limitations and specific false-positive examples.

**Data sources**: Clearly documented in README, RESEARCH_PLAN, and REPORT with table names (`alphaearth_embeddings_all_years`, `ncbi_env`), estimated row counts, and join strategies. The RESEARCH_PLAN includes a query strategy table with filter approaches — a good practice.

**Reproducibility**:
- Spark/local separation is clearly documented with step-by-step reproduction instructions in the README.
- A `requirements.txt` is provided with pinned kaleido version (`kaleido==0.2.1`) per the documented pitfall.
- Both notebooks have saved outputs (text, tables, figure renders), which is excellent — this project explicitly identified the "notebooks without outputs" issue and contributed it to `docs/pitfalls.md`.
- Pre-computed UMAP coordinates are cached in `data/umap_coords.csv`, enabling fast re-runs of NB02 without recomputing UMAP.

## Code Quality

**SQL queries (NB01)**: Correct and well-structured. The EAV pivot uses `MAX(CASE WHEN harmonized_name = ... THEN content END)` as recommended in `docs/pitfalls.md`. The approach of registering biosample IDs as a Spark temp view (`ae_biosamples`) for the join is efficient and avoids building a massive IN clause. The `SELECT *` on the 83K-row AlphaEarth table is acceptable given the documented small size.

**Pandas operations**: Clean and idiomatic throughout. Merges use appropriate join types (`how='left'` to preserve all AlphaEarth genomes). Coverage flags are computed vectorially. The environment harmonization function (cell 14) is well-organized with ordered keyword matching and proper separation of "Unknown" (missing/null) from "Other" (unmatched text).

**Distance computation (NB02, cell 32)**: Haversine distance is correctly vectorized with NumPy. Cosine distance is computed from raw embeddings (not L2-normalized), which is correct — normalization was only needed for UMAP's Euclidean proxy. The addition of `1e-10` to the denominator prevents division-by-zero.

**Pitfall awareness**: The project addresses multiple documented pitfalls: EAV pivot pattern for `ncbi_env`, NaN embedding filtering (3,838 genomes dropped), UMAP cosine metric performance (L2-norm + Euclidean), kaleido version pinning. The project also *contributed* three new pitfalls to `docs/pitfalls.md` (notebooks without outputs, geographic signal dilution, NaN embeddings), which demonstrates strong observatory citizenship.

**Issues identified**:

1. **Genome count discrepancy after UMAP merge**: `data/umap_coords.csv` contains 79,449 rows (verified), matching the REPORT. But NB02 cell 21 reports "Loaded pre-computed UMAP coordinates: 79,779 genomes" after the merge. The `merge(on='genome_id', how='inner')` should produce at most 79,449 rows (the smaller of the two inputs). The 79,779 count suggests either (a) the merge is actually `how='left'` in a different code version, (b) 330 genomes matched multiple UMAP rows, or (c) this is an artifact of a stale notebook output from a previous run with different data. The code shown uses `how='inner'`, so the output should be 79,449 or fewer. This inconsistency is minor but should be resolved.

2. **DBSCAN eps=0.5 produces 320 clusters**: The authors acknowledge this is "likely too fine-grained" in the REPORT's Limitations section. No alternative clustering was attempted, which is a missed opportunity.

3. **The `df_clean` variable may contain rows without valid embeddings post-merge**: Cell 21 filters to valid embeddings, then merges with UMAP coordinates using `how='inner'`. If any genome in `umap_coords.csv` had its embeddings become NaN in a newer data version, it would be included in `df_clean` without valid embeddings. A post-merge assertion would be prudent.

## Findings Assessment

**Finding 1 (stratified geographic signal)**: This is the project's most important result — environmental samples show a much stronger distance-decay than human-associated ones. The code is present in cell 36 (defining `env_groups`, sampling pairs within each group, computing binned distance-decay per group). The explanation (hospitals worldwide have similar satellite imagery) is intuitive and plausible. However, there is a **numeric inconsistency** between the REPORT and the notebook output:

| Metric | REPORT states | Notebook output (cell 36) |
|--------|--------------|--------------------------|
| Environmental near (<100 km) | 0.27 | 0.245 |
| Environmental far (>10K km) | 0.90 | 0.894 |
| Environmental ratio | 3.4x | 3.65x |
| Human-associated near | 0.37 | 0.369 |
| Human-associated far | 0.75 | 0.749 |
| Human-associated ratio | 2.0x | 2.03x |

The README also uses the REPORT's "3.4x" figure. These should be reconciled — the notebook output (3.65x) should be treated as authoritative since it comes from executable code.

**Finding 2 (monotonic distance-decay)**: Well-supported by the binned analysis in cell 34. The REPORT's data table matches the notebook output. The Spearman correlation (rho=0.2288, p<0.001) is computed and reported in cell 36, which provides a formal statistical measure for the overall relationship. The interpretation about the plateau above 5,000 km is reasonable.

**Finding 3 (clinical sampling bias)**: Well-documented with exact counts matching between notebook (cell 14) and REPORT. The 38% human-associated figure is derived from 22.2% Human clinical + 16.1% Human gut + 2.3% Human other = 40.6% — note that the REPORT rounds this to 38% using slightly different category counts (16,390 + 13,466 + 1,669 = 31,525 / 83,287 = 37.8%). The REPORT's per-category counts (e.g., "Human clinical: 16,390") don't exactly match the notebook output ("Human clinical: 18,505"). This is a second numeric inconsistency — likely the REPORT was drafted from an earlier analysis run.

**Finding 4 (coordinate QC)**: Nuanced and honest. The table of specific flagged locations with context (Rifle, Saanich Inlet, Siberian soda lakes) demonstrates domain knowledge. The acknowledgment that the heuristic needs refinement is appropriate.

**Finding 5 (UMAP clusters)**: The cluster-environment cross-tabulation (cell 40) is a nice analysis. The observation that rare environments concentrate in few clusters while common categories spread across many is well-supported by the heatmap.

**Limitations**: Seven specific limitations are listed in the REPORT, covering coverage bias, clinical bias, QC heuristic false positives, harmonization long tail, UMAP parameter sensitivity, NaN embeddings, and DBSCAN granularity. This is comprehensive and honest.

**Missing statistical test for stratified comparison**: While the Spearman correlation is reported for the overall and per-group relationships (cell 36), there is no formal test for whether the Environmental ratio (3.65x) is significantly different from the Human-associated ratio (2.03x). A bootstrap confidence interval on the ratio, or a permutation test shuffling environment labels, would quantify the significance of this difference.

## Suggestions

1. **[Important] Reconcile numeric inconsistencies between REPORT and notebook outputs**. The REPORT states the environmental distance ratio as 3.4x (near=0.27, far=0.90), but the notebook output shows 3.65x (near=0.245, far=0.894). Similarly, per-category counts differ (e.g., Human clinical: 16,390 in REPORT vs 18,505 in notebook). Update the REPORT and README to match the current notebook outputs, which should be treated as the authoritative source.

2. **[Important] Investigate the 79,449 vs 79,779 genome count discrepancy**. The `data/umap_coords.csv` file has 79,449 data rows, but NB02 cell 21 reports 79,779 after the merge. Add a post-merge validation cell: `print(f'Expected: {n_valid}, got: {len(df_clean)}')` and `assert len(df_clean) == n_valid` to catch any mismatch. If the counts legitimately differ, document why.

3. **[Moderate] Add a formal test for the stratified ratio difference**. The claim that environmental samples show "3.4x stronger" signal than human-associated (2.0x) is the headline finding but lacks a significance test. A bootstrap confidence interval on the near/far ratio for each group (resampling genome pairs with replacement, 1000 iterations) would quantify uncertainty and test whether the ratios are significantly different.

4. **[Moderate] Reduce the "Other" category**. Cell 15 shows easily capturable terms in the "Other" bucket: "water" (302 genomes), "tracheal secretion" (103), "stomach" (89), "Nose" (72), "rectal" (72), "sinus" (70), "gut" (68), and the Rifle well descriptions (730+ genomes). Adding keywords for these could reduce "Other" from 12.8% to ~8%. The Rifle well samples in particular should map to "Freshwater" or "Soil" (groundwater research site).

5. **[Moderate] Try HDBSCAN or coarser DBSCAN**. The 320-cluster result with eps=0.5 is acknowledged as too fine-grained. Running HDBSCAN (which selects density thresholds adaptively) or DBSCAN with eps=1.0-1.5 would likely produce 20-50 clusters that map more cleanly onto environment categories and would be more interpretable for downstream use.

6. **[Minor] Add the global map figure to the REPORT**. The `global_map_by_env.png` figure (cell 30) shows the geographic distribution of genomes colored by environment category but is not referenced in the REPORT's text or Figures table. It would complement Finding 3 (sampling bias) by visualizing the spatial distribution of clinical vs environmental samples.

7. **[Minor] Consider a sensitivity analysis on "suspicious" coordinates**. The distance-decay analysis (cells 32-36) uses only "good" quality coordinates (47,551 genomes), excluding 30,469 "suspicious" genomes. Since some flagged sites are legitimate (Rifle, Saanich Inlet), a sensitivity analysis including these sites would show whether the distance-decay findings are robust to the QC filter.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-16
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, 2 notebooks (28 + 44 cells), 5 data files, 14 figures (PNG + HTML pairs), requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
