---
reviewer: BERIL Automated Review
date: 2026-02-15
project: costly_dispensable_genes
---

# Review: The 5,526 Costly + Dispensable Genes

## Summary

This is one of the strongest projects in the observatory. It asks a crisp, well-motivated question — what characterizes genes that are simultaneously burdensome and not conserved? — and answers it convincingly with convergent evidence from functional annotation enrichment, ortholog breadth, gene length, and singleton analysis. The three-notebook pipeline is logically structured, fully reproducible from cached data without Spark, and all notebooks include saved outputs (text tables and figures). The REPORT.md is exemplary: thorough findings, explicit hypothesis testing (H1–H4 all addressed), an unusually detailed limitations section, well-chosen literature context, and concrete future directions. The central finding — that costly+dispensable genes are overwhelmingly mobile genetic element debris rather than degrading metabolic pathways — is a clean, interpretable result. Areas for improvement are minor: the annotation rate numbers in REPORT.md don't exactly match the notebook outputs, the singleton enrichment is partly structural, and a few additional analyses could further strengthen the interpretation.

## Methodology

**Research question and hypotheses**: Clearly stated and testable. The four hypotheses (H1–H4) are specific, each addressed by dedicated analyses, and the null hypothesis (H0) is explicitly defined. The RESEARCH_PLAN.md is among the best-structured in the observatory.

**Data sources**: Thoroughly documented in both README.md and RESEARCH_PLAN.md with source project, expected row counts, and key columns for each upstream dataset. The query strategy clearly states no Spark is needed.

**Approach**: The 2×2 selection signature matrix (costly/neutral × conserved/dispensable) is a natural and effective framework. Fisher exact tests with BH-FDR correction are appropriate for categorical enrichment. Mann-Whitney U tests are appropriate for the non-normal continuous comparisons (ortholog breadth, gene length). Effect sizes (rank-biserial correlation) are reported for both Mann-Whitney tests — a commendable practice given the large sample sizes.

**Reproducibility**: Excellent. The README includes a complete `## Reproduction` section with exact `nbconvert` commands, notes that all data is pre-cached (no Spark needed), and provides a `requirements.txt`. All three notebooks have saved outputs (text tables and inline figures), so results are fully visible without re-execution. The pipeline is linear (NB01 → NB02/NB03) with a single intermediate data file (`gene_quadrants.tsv`).

**Known pitfalls addressed**: The RESEARCH_PLAN.md documents four relevant pitfalls from docs/pitfalls.md (string booleans in `is_core`/`is_auxiliary`, essential gene exclusion, `fillna(False)` dtype, mixed `gene` column types). NB01 cell-3 implements all four correctly: `.map({'True': True, 'False': False}).astype(bool)` for boolean conversion and `dtype={'gene': str}` for the gene column. The `fillna(False).astype(bool)` pattern is used as the fallback path.

## Code Quality

**NB01 (Define Quadrants)**: Clean and correct. The quadrant counts exactly match expectations (28,017 / 5,526 / 86,761 / 21,886 / total 142,190). The `assign_quadrant` function uses row-wise `.apply()`, which docs/pitfalls.md flags as slow for large DataFrames, but at 142K rows this is not a practical issue. The gene metadata merge is a left join that preserves the correct row count. Output file saved as TSV with all columns documented.

**NB02 (Functional Characterization)**: Well-constructed. The SEED annotation merge correctly deduplicates before joining (`drop_duplicates(subset=['orgId', 'locusId'], keep='first')`) and asserts no row inflation (`assert len(genes_seed) == len(genes)`). The enrichment analysis in cell-9 computes Fisher exact tests for all 29 SEED top-level categories with BH-FDR correction — the methodology is sound. The mobile element keyword analysis (cell-12) uses an appropriate set of keywords and correctly operates on the original `genes` DataFrame. One minor note: the keyword list includes `IS\\d` as a regex pattern, which is good for catching IS element names like "IS3", "IS200", etc.

**NB03 (Evolutionary Context)**: Clean and correct. The ortholog breadth analysis properly distinguishes between genes with and without OG assignments (orphans). The singleton analysis includes a thoughtful note that the CD-vs-CC comparison is structurally determined (core genes cannot be singletons by definition) and provides the more informative within-dispensable comparison (costly vs neutral dispensable: OR=1.09, p=0.02). Both Mann-Whitney tests report rank-biserial correlation as an effect size measure. The specific phenotype analysis adds a valuable dimension.

**Statistical methods**: Appropriate throughout. Fisher exact tests with BH-FDR for categorical enrichment, Mann-Whitney U for non-parametric continuous comparisons, rank-biserial correlation for effect sizes. The singleton structural confound is correctly identified and handled.

## Findings Assessment

**Conclusions supported by data**: All four hypotheses are supported by convergent evidence. The 7.45x mobile element keyword enrichment (OR=7.45, p=4.6e-71) and the SEED category enrichments (Phage/Transposon 11.7x, Virulence 26.7x) are strong and consistent. The ortholog breadth difference (median 15 vs 31, r=0.233) and orphan gene fraction (44.5% vs 13.1%) consistently support the "recent acquisition" interpretation. The gene length difference (median 615 vs 765 bp, r=0.170) is consistent with IS elements and gene fragments.

**Minor numeric discrepancies in REPORT.md**: The REPORT.md states "55% vs 79%" for SEED annotation rates (rounding of 50.8% and 74.9% from NB02) and "OR=7.4" for the Phage/Transposon SEED category (the notebook shows OR=11.7 for "Phages, Prophages, Transposable elements, Plasmids" and 26.7 for "Virulence"). The REPORT.md text stating "7.4x enriched (FDR=1.5e-15)" for the Phage category doesn't match the notebook's OR=11.7 / FDR=1.26e-17. These appear to be from an earlier notebook run or a transcription error. The direction and conclusion are unaffected, but the exact numbers should be reconciled.

**Limitations acknowledged**: The REPORT.md has an unusually thorough limitations section covering seven specific concerns: noise sensitivity of max_fit > 1, annotation coverage gaps, binary core/auxiliary classification, DIAMOND threshold effects, the psRCH2 outlier, ortholog scope, and condition-specific phenotype bias. This is exemplary.

**Visualizations**: Six figures are generated and saved, covering all major analysis dimensions. They are clear, properly labeled, and use a consistent color scheme across notebooks. The SEED enrichment forest plot effectively communicates both direction and magnitude.

**Literature context**: Four references cited with full bibliographic details, PMIDs, and DOIs. The references.md documents search queries used to find them. The connections to the Black Queen Hypothesis, selfish genetic elements, and strain-dependent essentiality are well-drawn.

## Suggestions

1. **Reconcile REPORT.md numbers with notebook outputs** (moderate impact): Several statistics in REPORT.md don't exactly match the notebook outputs. SEED annotation rates are reported as "55% vs 79%" but notebooks show 50.8% vs 74.9%. The Phage/Transposon SEED enrichment is reported as "OR=7.4, FDR=1.5e-15" but the notebook shows OR=11.7, FDR=1.26e-17. Either the REPORT was written from an earlier run or the numbers were rounded inconsistently. A pass through the REPORT.md to verify all quoted statistics against the current notebook outputs would ensure accuracy.

2. **Clarify the "Virulence" SEED category enrichment** (minor impact): The REPORT.md highlights the Virulence category as 29.9x enriched — but the notebook shows this is based on only 21 vs 4 genes (cell-9). While the Fisher exact test is valid for small counts, such a high odds ratio from few observations is fragile. Adding a note about the small sample size would help readers calibrate the strength of this specific finding versus the more robust Phage/Transposon enrichment (39 vs 17 genes).

3. **Consider comparing costly+dispensable to neutral+dispensable, not just costly+conserved** (minor impact): The primary comparison throughout is costly+dispensable vs costly+conserved. While this isolates the effect of conservation status within costly genes, comparing costly+dispensable to neutral+dispensable would isolate the effect of burden within dispensable genes. NB03 does this for singletons (OR=1.09, p=0.02) — extending this to functional enrichment and ortholog breadth would help distinguish features of "dispensable genes in general" from features specific to "costly dispensable genes."

4. **Document the Miya organism outlier** (minor impact): Miya (67 genes total, 19.4% costly+dispensable) has the second-highest percentage after psRCH2, but with a very small gene count that suggests it may be an incomplete dataset or a small genome. A brief note would help readers assess whether this is a meaningful biological signal or a sample size artifact.

5. **Add a summary figure combining key dimensions** (nice-to-have): A single multi-panel figure or radar chart comparing the four quadrants across all dimensions (annotation rate, mobile element %, orphan fraction, median OG breadth, median gene length, % with specific phenotypes) would provide a useful visual abstract. This could serve as Figure 1 in a potential publication.

6. **Consider genomic clustering analysis** (nice-to-have, noted in future directions): As the REPORT.md already suggests, testing whether costly+dispensable genes cluster near scaffold edges, tRNA genes, or in consecutive runs would strengthen the mobile element / genomic island interpretation. If scaffold position data is available in the upstream datasets, this could be a high-value addition.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-15
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, 3 notebooks, 1 data file (21 MB), 6 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
