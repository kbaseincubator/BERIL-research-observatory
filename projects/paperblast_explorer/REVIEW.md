---
reviewer: BERIL Automated Review
date: 2026-02-22
project: paperblast_explorer
---

# Review: PaperBLAST Data Explorer

## Summary

This is a well-executed data characterization project that thoroughly profiles the `kescience_paperblast` collection on BERDL. The three notebooks flow logically from a database inventory (NB01) through literature concentration analysis (NB02) to sequence-level clustering (NB03), and all key findings are clearly documented in a comprehensive REPORT.md. The analysis uncovers genuinely interesting patterns — H. sapiens accounts for 46.7% of all gene-paper records, 65.6% of genes have exactly one paper, and 5,218 multi-member protein families have zero literature coverage — with appropriate caveats and strong literature framing. The main technical concerns are a Gini coefficient computation that requires ascending sort but receives descending-sorted data, a eukaryote (soybean, *Glycine max*) that slips into the top-20 bacteria list due to an incomplete exclusion filter, and a RESEARCH_PLAN that does not describe the sequence clustering notebook. These issues are fixable and do not invalidate the project's core findings.

---

## Methodology

**Research question**: Clearly stated and appropriately scoped as a characterization study rather than a hypothesis test. The framing in RESEARCH_PLAN.md is honest about this distinction, which is appropriate.

**Approach**: Sound. Covering all 14 tables, measuring temporal currency, taxonomic breadth, literature concentration, and sequence-level redundancy gives a thorough portrait of the collection. The addition of MMseqs2 clustering (NB03) goes beyond the stated plan to useful effect.

**Data sources**: All 14 `kescience_paperblast` tables are used and cross-referenced. The CTS job ID (`c10c4a0f-3d57-4219-9329-501b74c8f29a`) for the MMseqs2 clustering run is documented, which aids reproducibility of NB03.

**Gap — NB03 not in RESEARCH_PLAN**: The sequence clustering analysis is a substantive third notebook that adds Finding 5 (345K protein families) and Finding 6 (dark families). It is not described in RESEARCH_PLAN.md at all. The plan should be updated to include it, or a note should explain that it was added after the initial plan was written.

**Reproducibility gap in README**: The `## Reproduction` section only shows how to run NB01. NB02 is straightforward (loads NB01 outputs from `data/`), but NB03 requires the cluster TSV files (`clusters_{30,50,90}pct.tsv`) which are either pre-generated locally or must be downloaded from MinIO (`cts/io/psdehal/...`). A reader following the README would have no idea NB02 and NB03 exist or how to run them. The REPORT.md does document the dependency chain and CTS job, but that information belongs (at least summarized) in the README reproduction guide.

---

## Code Quality

**Spark usage**: Excellent. All notebooks aggregate in Spark before calling `.toPandas()`. No full-table pulls. The `COUNT(DISTINCT ...)` aggregations, `GROUP BY` patterns, and use of direct `spark.sql()` are all appropriate. String-typed columns are handled correctly (e.g., `CAST(year AS INT)`, `CAST(protein_length AS INT)`) — a pitfall that is documented in `docs/pitfalls.md` and properly avoided here.

**Spark import**: `from berdl_notebook_utils.setup_spark_session import get_spark_session` is used throughout, which is the correct import for JupyterHub notebooks. ✓

**NB03 local execution**: NB03 cleverly separates concerns — the heavy Spark queries (cluster representative lookups) are isolated to cells 7–8 and 15, while the main cluster analysis runs locally from TSV files. This allows downstream review without Spark access.

**Bug — Gini coefficient computed on incorrectly sorted data (NB02, Cell 17)**: The Gini formula used requires values sorted in *ascending* order (smallest to largest), but `org_papers_sorted` and `ppg_sorted` are both sorted *descending* (largest first). For a distribution as skewed as this one, the formula will produce a negative value rather than a value near 1.0. The Lorenz curves themselves are also effectively inverted (anti-Lorenz: cumulative share starting from the richest) rather than the conventional form (starting from the poorest). The REPORT's prose conclusions about inequality (e.g., "1% of organisms receive the vast majority") remain valid because they derive from the cumulative-sum columns (`cum_pct`) rather than the Gini value, but the Gini numbers and the Lorenz curve shape in `lorenz_curves.png` should be reviewed and corrected. Fix: add `.sort_values('n_papers', ascending=True).reset_index(drop=True)` before computing Gini in both panels.

**Bug — *Glycine max* misclassified as bacterium (NB02, Cell 19)**: The `is_bacterium()` heuristic excludes common eukaryotes by keyword but does not include `'glycine'` in its exclusion list. As a result, *Glycine max* (soybean, rank 23 overall with 1,147 papers) appears at rank 16 in the top-20 bacterial list. This is a eukaryote, not a bacterium, and its presence inflates the top-20 list by displacing the actual 20th-ranked bacterium. The REPORT states "the top 3 bacteria are all well-known pathogens or model organisms" which is correct, but the top-20 figure and table contain an erroneous entry. Fix: add `'glycine '` to the euk exclusion keywords in `is_bacterium()`.

**Minor numerical inconsistency (NB03, Cells 10 vs 18)**: Cell 10 reports "Clusters with ≥100 papers: 2,638" (using `>=`), while the summary in Cell 18 uses `> 100` (strictly greater) and prints 2,607. The REPORT cites 2,638, matching Cell 10. The discrepancy is small but the threshold definition (`≥100` vs `>100`) should be made consistent, and the figure legend in `literature_coverage_landscape.png` should match the prose.

**Notebook organization**: All three notebooks follow a clean setup → query → analysis → visualization pattern with markdown section headers. The use of `DATA_OUT` and `FIG_OUT` path constants is good practice.

**`requirements.txt`**: Only `pandas`, `numpy`, and `matplotlib` are listed. This covers NB03 but omits the cluster-level dependency `berdl_notebook_utils` (needed for NB01/NB02) and does not specify Python version. The file is better than nothing but would benefit from a comment explaining that NB01/NB02 also require the BERDL JupyterHub environment.

---

## Findings Assessment

**Finding 1 (H. sapiens = 46.7%)**: Directly supported by Cell 3 of NB02 output. ✓

**Finding 2 (65.6% of genes have 1 paper)**: Directly supported by Cell 12 of NB01 histogram output. ✓

**Finding 3 (Lorenz curves)**: Qualitatively supported — the extreme concentration is real and visible. However, as noted under Code Quality, the Lorenz curve implementation uses descending-sorted data, which produces an anti-Lorenz form, and the Gini values need verification. The stated conclusions about inequality are directionally correct.

**Finding 4 (bacterial research concentrated on pathogens)**: Directionally correct and well-supported, but *Glycine max* should not appear in the top-20 list (see bug above).

**Finding 5 (345K protein families)**: Directly supported by NB03 cluster count outputs. ✓

**Finding 6 (55% dark or dim families)**: Numbers add up: 9.2% dark + 46.1% dim = 55.3%. Consistent with Cell 16 output. ✓

**Limitations**: The REPORT's limitations section is thorough and honest — text-mining false positives, PMC open-access bias, heuristic domain classification, and arbitrary clustering thresholds are all acknowledged. This is one of the stronger limitations sections seen in BERIL projects.

**Future directions**: The 5 proposed directions are specific, feasible, and grounded in the data. The VIMSS cross-reference link to the Fitness Browser (Finding 5 → "high-impact understudied genes") is a particularly actionable follow-on.

**Incomplete analysis**: None detected. All cells have output, all figures exist, all data files listed in the REPORT are present in `data/`.

---

## Suggestions

1. **[Critical] Fix Gini computation sort order (NB02, Cell 17)**: Sort `papers_arr` and `papers_arr_g` ascending before computing Gini. Regenerate `lorenz_curves.png` and update any quoted Gini values. The Lorenz curve x-axis framing should also be reconsidered — conventional Lorenz curves start from the poorest, not the richest.

2. **[High] Remove *Glycine max* from the bacterial filter (NB02, Cell 19)**: Add `'glycine '` (with trailing space to avoid matching "Streptolysin/glycine") to the eukaryote exclusion list in `is_bacterium()`. Regenerate `top20_bacteria.png` and update the REPORT accordingly.

3. **[High] Update RESEARCH_PLAN.md to include NB03**: Add a "Notebook 3: Sequence Clustering Analysis" section describing the MMseqs2 clustering approach, thresholds, and analysis goals. This brings the plan into alignment with what was actually done.

4. **[Medium] Expand README reproduction section**: Add steps for NB02 and NB03. Note that NB03 depends on the cluster TSV files that are either already in `data/` (if working from this repo) or must be downloaded from MinIO path `cts/io/psdehal/...`. A brief dependency diagram (NB01 → NB02, CTS job → NB03) would help a new reader.

5. **[Medium] Reconcile ≥100 vs >100 threshold (NB03)**: Make the cutoff for "heavily studied" clusters consistent between Cells 10 and 18. Update the REPORT and figure caption to match. The difference is 31 clusters, so it won't change any narrative conclusions, but consistency matters.

6. **[Low] Annotate requirements.txt**: Add a comment that `berdl_notebook_utils` is also required for NB01/NB02, with a pointer to the BERDL JupyterHub environment. Consider specifying `python>=3.10` or equivalent.

7. **[Low] Add RESEARCH_PLAN.md and references.md to README Quick Links**: The Quick Links section currently only links to `notebooks/`. Linking to the research plan and references file would improve navigability for readers using the README as an entry point.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-22
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 3 notebooks, 20 data files, 12 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
