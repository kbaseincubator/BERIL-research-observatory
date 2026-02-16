---
reviewer: BERIL Automated Review
date: 2026-02-16
project: env_embedding_explorer
---

# Review: AlphaEarth Embeddings, Geography & Environment Explorer

## Summary

This is a well-executed exploratory characterization of the AlphaEarth environmental embeddings in BERDL. The project clearly defines its scope, implements a logical multi-stage pipeline (extraction, QC, harmonization, dimensionality reduction, distance analysis), and produces several genuinely useful outputs — notably the environment harmonization mapping, coordinate quality flags, and the stratified geographic-distance analysis showing 3.4x stronger signal for environmental vs human-associated samples. Documentation is excellent: the three-file structure (README, RESEARCH_PLAN, REPORT) is fully realized and internally consistent, the REPORT includes literature context and thoughtful limitations, and the notebooks are well-narrated with markdown explanations. The main gaps are a reproducibility issue with the headline finding's missing code, a minor numeric inconsistency, and the absence of statistical tests for the distance-decay relationship.

## Methodology

**Research question**: Clearly stated as exploratory — "What do AlphaEarth environmental embeddings capture?" — with four specific sub-questions (E1–E4) that structure the analysis. The framing as characterization rather than hypothesis testing is appropriate and honestly communicated.

**Approach**: Sound and well-sequenced. The pipeline moves logically from data extraction (NB01) through QC and exploration (NB02). The choice to L2-normalize embeddings before UMAP (using Euclidean as a proxy for cosine distance) is well-motivated and correctly justified. The coordinate QC heuristic (>50 genomes AND >10 species at the same location) is simple but reasonable for a first pass, and the authors explicitly acknowledge its limitations.

**Data sources**: Clearly identified with table names, row counts, and join keys documented in both the RESEARCH_PLAN and README.

**Reproducibility**: The Spark/local separation is clearly documented — NB01 requires JupyterHub, NB02 runs locally from cached CSVs. The README includes a step-by-step reproduction guide with prerequisites. A `requirements.txt` is provided. However, there are two reproducibility concerns:

1. **Missing code for headline finding**: The stratified distance analysis (`geo_vs_embedding_by_env_group.png`) — which produces the project's headline result (3.4x vs 2.0x ratio) — has no corresponding code cell in the notebook. The figure exists on disk and appears in the notebook's final file listing, but the code that generated it is absent. This means the most important analysis cannot be reproduced from the notebook alone.

2. **UMAP coordinate mismatch**: The pre-computed `umap_coords.csv` contains 79,449 rows (per the REPORT), but the notebook's merge step reports "Loaded pre-computed UMAP coordinates for 79,779 genomes" and subsequently operates on 79,779 genomes. This suggests either (a) the UMAP coordinates file was regenerated after the REPORT was written, or (b) the left join on `genome_id` created unexpected matches. The discrepancy (330 genomes) is small but should be investigated and documented.

**Notebook outputs**: Both notebooks have saved outputs (text, tables, plotly figure renderings), which is excellent. The project explicitly documented the "notebooks without outputs" pitfall in `docs/pitfalls.md` and addressed it.

## Code Quality

**SQL queries** (NB01): Correct and well-structured. The EAV pivot query uses `MAX(CASE WHEN ...)` as recommended in `docs/pitfalls.md`. The biosample ID temp view approach for the join is efficient. The `SELECT *` on the AlphaEarth table is acceptable given the small table size (83K rows), which is noted in the RESEARCH_PLAN.

**Pandas operations** (NB01–NB02): Clean and idiomatic. The merge uses `how='left'` correctly to preserve all AlphaEarth genomes. Coverage flags are computed vectorially rather than with row-wise apply.

**Environment harmonization** (NB02, cell 14): The keyword-matching approach is clearly documented with category definitions and keyword lists. The ordered matching (first match wins) is a reasonable strategy. The "Other" and "Unknown" categories are properly separated (missing/null vs unmatched text), and the residual "Other" values are explicitly inspected (cell 15).

**UMAP implementation** (NB02, cell 22): Correctly handles the known pitfall about cosine metric being slow — uses L2-normalization + Euclidean as documented in `docs/pitfalls.md`. The subsample-fit/full-transform approach is a good performance optimization. Pre-computed coordinates are cached and loaded on subsequent runs, which is the recommended checkpointing pattern.

**Distance computation** (NB02, cell 32): The Haversine distance calculation is correctly vectorized with NumPy. Cosine distance is computed from raw (non-normalized) embeddings, which is correct for measuring actual cosine similarity.

**Pitfall awareness**: The project addresses several documented pitfalls: EAV pivot for `ncbi_env`, NaN embedding filtering, UMAP cosine metric performance, kaleido version compatibility (deprecation warning visible but functional). The kaleido warning (cells 4, 5, 12, etc.) suggests kaleido 0.2.1 is installed as recommended.

**Minor issues**:
- The DBSCAN `eps=0.5` on UMAP coordinates produces 320 clusters, which the authors themselves note is "likely too fine-grained" (REPORT Limitations). This is acknowledged but not explored further.
- The `valid_mask` in cell 21 correctly drops 3,838 NaN-embedding genomes, but the subsequent merge with `umap_coords.csv` uses a left join that brings some back (resulting in the 79,779 count), and the code does not re-filter afterward. Downstream cells operate on `df_clean` which may contain rows with UMAP coordinates but NaN embeddings if the UMAP file was generated from a different data version.

## Findings Assessment

**Finding 1 (3.4x geographic signal for environmental samples)**: The headline finding is compelling and well-interpreted. The explanation that hospitals worldwide have similar satellite imagery is intuitive and testable. However, the code producing this analysis is missing from the notebook, so the exact methodology (how "environmental" and "human-associated" groups were defined, whether the same 50K-pair sampling was used, etc.) cannot be verified from the notebooks alone.

**Finding 2 (monotonic distance-decay)**: Well-supported by the binned analysis (cell 34). The data table in the REPORT matches the notebook output. The interpretation about plateau above 5,000 km is reasonable. One concern: the analysis uses only "good" quality coordinates (47,551 genomes), which is appropriate, but excludes some legitimate field sites flagged as "suspicious" — this could bias the result if environmental samples are disproportionately at those sites. A sensitivity analysis including suspicious-but-legitimate sites would strengthen this finding.

**Finding 3 (clinical sampling bias)**: Well-documented with exact counts. The observation that clinical isolates have good geographic metadata due to epidemiological tracking is a plausible mechanism.

**Finding 4 (coordinate QC)**: Honest and nuanced — the authors explicitly list false positives (Rifle, Saanich Inlet) and acknowledge the heuristic needs refinement. The table of specific flagged locations with context is very useful.

**Finding 5 (UMAP structure)**: The UMAP visualizations colored by environment category and phylum are informative. The cluster-environment cross-tabulation is a nice addition. The 320-cluster DBSCAN result is presented with appropriate caveats.

**Finding 6 (taxonomic structure)**: Appropriately cautious about the environment-taxonomy confound.

**Literature context**: The REPORT cites four relevant papers on distance-decay in microbial ecology and correctly frames the findings in context. The self-citation to the `ecotype_analysis` project is appropriate and the suggestion to re-run with environmental-only samples is a concrete, actionable future direction.

**Limitations**: Comprehensive and honest — seven specific limitations are listed, including coverage bias, QC heuristic false positives, harmonization long tail, UMAP parameter sensitivity, and NaN embeddings.

**No statistical tests**: The distance-decay relationship (Finding 2) is presented descriptively (mean cosine distance by bin) without a formal statistical test (e.g., Mantel test, permutation test, or regression). While the monotonic trend is visually clear, a p-value or confidence interval would strengthen the claim, especially for the stratified comparison (3.4x vs 2.0x).

## Suggestions

1. **[Critical] Add the stratified distance analysis code to the notebook**. The `geo_vs_embedding_by_env_group` figure is the project's most important result but has no source code in NB02. Either add the code as a new cell after the binned distance analysis (cell 34), or create a brief NB03 for the stratified analysis. Re-execute the notebook to capture outputs.

2. **[Important] Resolve the 79,449 vs 79,779 genome count discrepancy**. After the UMAP coordinate merge in cell 21, verify that `df_clean` contains exactly the expected number of valid-embedding genomes. Add a post-merge assertion: `assert df_clean['umap_x'].isna().sum() == 0` or document why the counts differ.

3. **[Important] Add a statistical test for the distance-decay relationship**. A Mantel test (geographic distance matrix vs embedding distance matrix) or a simple Spearman correlation on the paired distances would provide a p-value for the geographic signal. For the stratified comparison, a permutation test or bootstrap confidence intervals on the near/far ratio would quantify whether the 3.4x vs 2.0x difference is statistically significant.

4. **[Moderate] Expand the "Other" category**. Cell 15 identifies several easily capturable terms: "cerebrospinal fluid", "lung", "throat swab", "nasopharynx" → Human clinical; "pork", "tissue" → Food/Animal; "Aspo HRL", "Olkiluoto" → Extreme (underground); "water" → could be split by `env_broad_scale` fallback. This could reduce the "Other" category from 17% to ~10%.

5. **[Moderate] Try a coarser clustering**. The REPORT notes that 320 clusters is "likely too fine-grained." Running DBSCAN with `eps=1.0` or `eps=1.5`, or using HDBSCAN (which selects eps adaptively), would likely produce 20-50 clusters that map more cleanly onto environment categories and would be more interpretable.

6. **[Minor] Pin kaleido version in requirements.txt**. The requirements file specifies `kaleido>=0.2.1` which could pull kaleido 1.x (requiring Chrome). Per the documented pitfall, pin to `kaleido==0.2.1` for headless compatibility.

7. **[Minor] Add the `global_map_by_env` figure to the REPORT**. The geographic map colored by environment category is generated (cell 30) and saved to `figures/`, but is not referenced in the REPORT's Figures table or embedded in any finding. It would complement Finding 3 (sampling bias) by showing the geographic distribution of the clinical vs environmental samples.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-16
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 2 notebooks (28 + 43 cells), 5 data files, 14 figures (PNG + HTML pairs), requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
