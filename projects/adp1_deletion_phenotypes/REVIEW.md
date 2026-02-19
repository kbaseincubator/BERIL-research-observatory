---
reviewer: BERIL Automated Review
date: 2026-02-19
project: adp1_deletion_phenotypes
---

# Review: ADP1 Deletion Collection Phenotype Analysis

## Summary

This is a well-executed phenotype-first analysis of the *Acinetobacter baylyi* ADP1 single-gene deletion collection across 8 carbon sources. The project is mature and complete: all five notebooks have saved outputs with figures, the three-file documentation structure (README, RESEARCH_PLAN, REPORT) is properly used, and conclusions are well-supported by the data shown. The strongest results are the condition-specificity analysis (NB04), which maps top genes per carbon source to precisely the expected metabolic pathways, and the TnSeq gap analysis (NB05), which reveals that missing dispensable genes are shorter, less conserved, and enriched for hypotheticals. The main area for improvement is the gene module analysis (NB03), where hierarchical clustering with K=3 produces two oversized modules (1,160 and 850 genes) that are too large to yield functional enrichments — the project correctly reports this negative result but could explore alternative decomposition methods mentioned in the research plan.

## Methodology

**Research question**: Clearly stated and testable. The hypothesis (H0 vs H1) is well-framed, and the four aims are logically structured from broad (condition structure) to specific (TnSeq gaps).

**Approach**: Sound overall. The decision to exclude FBA predictions is well-justified by the prior project's finding (p=0.63). Z-score normalization per condition before clustering and PCA is appropriate given the 3.3-fold range in mean growth ratios across conditions. The condition specificity score (|z_i| - mean(|z_j|) for j != i) is a reasonable and interpretable metric.

**Data sources**: Clearly identified — a user-provided SQLite database (136 MB) with cross-references to BERDL pangenome data. The symlink dependency on `projects/acinetobacter_adp1_explorer/user_data/` is documented but could be fragile for reproduction by others.

**Statistical rigor**: Benjamini-Hochberg FDR correction is applied consistently across all enrichment analyses (NB03 RAST/PFAM enrichment, NB05 gap functional enrichment). Fisher's exact test is appropriate for the contingency tables used. The chi-squared test for pangenome core status (p=1.4e-20) is correctly applied to a 2x2 table with adequate cell counts.

**Reproducibility**: The README includes a clear `## Reproduction` section with exact `nbconvert` commands. All notebooks run locally (no Spark required), which is explicitly documented. The `requirements.txt` lists all Python dependencies with minimum versions.

**Minor concern**: The RESEARCH_PLAN (Aim 4) estimated "370 dispensable genes" lacking growth data, but the actual analysis found 272. This is expected for a pre-analysis estimate, and the correct number is used throughout the notebooks and REPORT. However, the RESEARCH_PLAN was not updated to reflect the actual count.

## Code Quality

**Notebook organization**: All five notebooks follow a consistent structure: markdown header with goal/inputs/outputs, numbered sections, inline interpretation, and a summary cell at the end. This makes each notebook self-contained and easy to follow.

**SQL queries**: The SQLite queries in NB01 are straightforward `SELECT` statements on the `genome_features` table. No performance issues expected given the small table size (~5,852 rows).

**Statistical methods**:
- PCA implementation (NB02) is correct: StandardScaler followed by full PCA with variance reporting.
- Hierarchical clustering uses Ward's method with Euclidean distance on z-scores (NB03), which is the appropriate pairing. However, the condition dendrogram in NB02 uses Ward's method on `1 - |Pearson correlation|` distance, which is technically non-Euclidean. Ward's method assumes Euclidean distance; using it on correlation-based distances can produce suboptimal merges. In practice the results here appear reasonable, but this is a methodological imprecision worth noting.
- The silhouette analysis (NB03, cell 6) tests K=2 through K=25, which is thorough for 2,034 genes.

**Pitfall awareness**: The project addresses several relevant pitfalls from `docs/pitfalls.md`:
- Uses `pd.notna()` checks before string operations on annotation columns (addressed in RESEARCH_PLAN and code).
- Correctly handles NaN in pangenome_is_core with `.fillna(False).astype(bool)` (NB05, cell 10).
- No Spark-related pitfalls apply since all analysis is local SQLite + pandas.
- The `fillna(False).astype(bool)` pattern in NB05 correctly avoids the object-dtype boolean pitfall documented in `docs/pitfalls.md`.

**Code issues**:
1. In NB03 (cell 14), `rast_clean` splits on `' / '` to take the first function, which is a reasonable heuristic but discards multi-function annotations. The threshold of `>=5` genes for testable functions reduces the number of testable categories to only 19 out of 1,446 RAST categories. With module sizes of 1,160 and 850, even real enrichments would be diluted below detection. This is a design limitation, not a bug.
2. In NB03 (cell 17), PFAM parsing assumes comma-separated domains but only produces 2,012 gene-domain pairs for 2,012 genes — exactly 1 domain per gene. This suggests the PFAM column may not actually contain multi-domain entries, or the parsing is capturing only the first match. Worth verifying.
3. In NB05 (cell 5), the markdown header says "370 dispensable genes" but the analysis correctly finds 272. The markdown text should be updated for consistency.

## Findings Assessment

**Conclusions supported by data**: Yes, comprehensively. Each key finding is directly traceable to specific notebook outputs:
- The three-tier condition structure (Finding 1) is supported by the box plots and defect fraction tables in NB01.
- The ~5 independent dimensions (Finding 2) follows directly from the PCA scree plot showing 5 PCs for 82% variance.
- The continuum vs module conclusion (Finding 3) is well-supported by the low silhouette score (0.24) and absence of enrichments after FDR.
- The condition-specific gene lists (Finding 4) are biologically compelling — urease subunits for urea, protocatechuate degradation for quinate, Entner-Doudoroff for glucose.
- The TnSeq gap characterization (Finding 5) is quantitative and statistically supported (chi-squared p=1.4e-20 for core status difference).

**Limitations acknowledged**: Yes, four substantive limitations are listed in the REPORT, covering measurement noise, ascertainment bias, condition panel size, and pangenome resolution. These are appropriate and honest.

**Incomplete analysis**: The RESEARCH_PLAN mentioned NMF decomposition as an alternative to hierarchical clustering (Aim 2), but this was not attempted. Given that hierarchical clustering produced uninformative modules, trying NMF or ICA (mentioned in Future Directions) would strengthen the negative finding or potentially reveal latent structure. The REPORT's Future Directions section appropriately flags ICA as a next step.

**Visualizations**: All 15 figures are properly labeled with titles, axis labels, and legends. The figures span all analysis stages (exploration: growth distributions/boxplots; analysis: PCA/correlation/clustering; results: condition-specific heatmap; validation: TnSeq gap plots). The clustermap in NB02 and condition-specific heatmap in NB04 are particularly effective.

## Suggestions

1. **Try ICA or NMF for gene module discovery** (high impact). The hierarchical clustering with K=3 produces two mega-modules (1,160 and 850 genes) that are too diffuse for functional enrichment. ICA, as mentioned in Future Directions, could extract condition-specific latent factors from the growth matrix and would likely recover the quinate and urea signals as independent components. This would transform the "no modules found" result into a positive finding about the structure of the phenotype landscape.

2. **Lower the enrichment threshold for RAST functions** (medium impact). Testing only functions with >=5 genes in NB03 reduces testable categories from 1,446 to 19. With BH-FDR correction, a threshold of >=3 would still be statistically valid and would test many more categories. Alternatively, use broader functional categories (e.g., RAST subsystem level) rather than individual function strings, which would aggregate genes into larger functional groups more amenable to enrichment testing.

3. **Update RESEARCH_PLAN with actual counts** (low impact, documentation). The plan estimates 370 missing dispensable genes and 1,179 total TnSeq genes without growth data, but the actual numbers are 272 and 1,081. While the revision history notes reviewer feedback was addressed, the gene counts in Aim 4 were not corrected. Similarly, NB05 cell 5 markdown still says "370 dispensable genes."

4. **Verify PFAM multi-domain parsing** (low impact, correctness). NB03 cell 17 reports exactly 2,012 gene-domain pairs for 2,012 genes with PFAM annotations, suggesting each gene has exactly one domain entry. If the PFAM column contains multi-domain annotations (e.g., "PF00106,PF03466"), the comma-split logic should produce more pairs. Verify whether PFAM entries are genuinely single-domain or if the parsing needs adjustment.

5. **Document the SQLite database provenance more explicitly** (low impact, reproducibility). The database is described as "symlinked from `projects/acinetobacter_adp1_explorer/user_data/`" but its original construction method is not documented in this project. A sentence in the README noting how `berdl_tables.db` was built (which BERDL tables were exported, what processing was done) would help someone reproduce the full pipeline from scratch.

6. **Add a Mann-Whitney U test for gene length comparison** (nice-to-have). NB05 reports mean/median gene lengths for present vs missing dispensable genes but does not include a formal statistical test for the length difference. Adding a Wilcoxon rank-sum test would complement the chi-squared test already done for pangenome core status.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks, 7 data files, 15 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
