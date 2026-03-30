---
reviewer: BERIL Automated Review
date: 2026-03-14
project: truly_dark_genes
---

# Review: Truly Dark Genes -- What Remains Unknown After Modern Annotation?

## Summary

This is a well-structured and scientifically rigorous project that takes the 57,011 "dark" genes from the `functional_dark_matter` project and refines them into a tractable set of 6,427 genuinely unknown genes by leveraging bakta v1.12.0 reannotation to separate annotation lag from true biological novelty. The project excels at hypothesis-driven analysis with pre-registered statistical thresholds, honest reporting of negative results (H2 rejection), thorough data reuse from prior projects, and a clearly written report with proper limitations. The 6-notebook pipeline progresses logically from census through enrichment, annotation mining, concordance, genomic context, and prioritization, producing a well-justified top-100 candidate list. Areas for improvement include a minor code quality issue (regex warning in NB05), an incomplete concordance validation in NB03, the GC deviation analysis using only dark genes rather than genome-wide GC to compute organism means, and a scoring system that may over-weight essentiality relative to functional clues. Overall, this is one of the stronger observatory projects in terms of methodological rigor and clear reporting.

## Methodology

**Research question**: Clearly stated, testable, and appropriately scoped. The decomposition of 57,011 dark genes into annotation-lag (33,105), truly dark (6,427), and unlinked (17,479) is well-motivated by the parent project's NB12 finding that 83.7% of linked dark genes gain bakta annotations.

**Hypotheses**: Four hypotheses (H0/H1 on structural distinctiveness, H2 on stress enrichment, H3 on accessory genome/HGT, H4 on partial annotation clues) are precisely stated with pre-registered effect size thresholds (Cohen's d >= 0.2 or OR >= 1.5). The honest rejection of H2 is a strength -- many projects would downplay or ignore a negative result.

**Data sources**: Well documented in both README.md and RESEARCH_PLAN.md. The data reuse strategy (loading parent project outputs rather than re-querying) is efficient and reduces opportunities for inconsistency. Five BERDL tables and four prior observatory projects are leveraged.

**Statistical framework**: Appropriate -- Mann-Whitney U for continuous variables, Fisher's exact for categorical, with Benjamini-Hochberg FDR correction across all comparisons (NB01 cell 30). Effect sizes are reported alongside p-values, which is good practice given the large sample sizes where even trivial effects can be "significant."

**Reproducibility**: The README includes a Reproduction section with clear steps. Dependencies are in `requirements.txt` (6 packages). The Spark/local separation is documented (NB01-NB02 need Spark, NB03-NB06 run locally). All intermediate data is saved to `data/`, enabling re-running downstream notebooks without Spark access.

## Code Quality

**SQL correctness**: The Spark queries in NB02 are well-constructed. The project correctly uses temp view JOINs rather than IN clauses for the 5,870 gene cluster IDs (as recommended in RESEARCH_PLAN.md and consistent with `docs/pitfalls.md` guidance on large ID lists). The `eggnog_mapper_annotations` query correctly joins on `query_name` (not `gene_cluster_id`), avoiding the foreign key pitfall documented in `docs/pitfalls.md`. The `CAST(g.begin AS INT)` and `CAST(g.end AS INT)` in the gene properties query correctly handles the string-typed numeric column pitfall.

**Notebook organization**: Each notebook follows a clean structure: markdown header with goal/input/output, imports, data loading, analysis, visualization, save, and summary. The progression from NB01 through NB06 is logical and each notebook's outputs feed into the next.

**Known pitfall awareness**: The project addresses several `docs/pitfalls.md` issues:
- String-typed numeric columns: CAST used correctly in NB02 (cell 11)
- Gene clusters are species-specific: Not compared across species
- `eggnog_mapper_annotations.query_name` join key: Used correctly in NB02 (cell 9)
- Temp view approach for large ID lists: Used correctly in NB02

**Issues identified**:

1. **NB05 cell 5: Invalid regex escape sequence warning**: The line `mobile_keywords = ['transpos', 'integrase', 'recombinase', 'phage', 'IS\d', ...]` uses a non-raw string containing `\d`, which produces a `SyntaxWarning: invalid escape sequence '\d'`. This should be `r'IS\d'` or `'IS\\d'`. The warning appears in the output but the code still works because Python currently passes unrecognized escape sequences through, though this behavior is deprecated. This is a minor code quality issue, not a correctness bug.

2. **NB04 cell 12: GC deviation computed from dark genes only**: The organism mean GC is computed from `gene_props`, which contains only truly dark + annotation-lag genes (39,532 genes), not all genes in each organism. This means the "genome mean GC" is actually the "dark gene mean GC" for each organism. This biases the deviation calculation -- the true organism-wide GC mean from all ~228K FB genes could differ, especially for organisms with few dark genes. The effect on H3's conclusion is likely small (the comparison is still TD vs AL within the same reference frame), but the description of the metric as "organism mean GC" is not quite accurate.

3. **NB03 cell 19: Concordance-clue validation incomplete**: The concordance data uses `ogId` as its key (not `orgId`/`locusId`), so the matching attempt fails. The notebook correctly notes this ("Concordance columns: ['ogId', ...]") and defers to NB04, but NB04 does not actually perform the clue-concordance validation either. The RESEARCH_PLAN specified "validate that clue combinations are informative by testing whether genes with more clues have higher cross-organism concordance rates" -- this was not completed. Given that only 3 OGs contain truly dark genes, the sample size would be too small for a meaningful test anyway, which could be stated explicitly.

4. **NB06 scoring: Essential genes may be over-weighted**: Essential genes receive score_fitness=3 regardless of whether they have any measured fitness phenotype (many essential genes show `max_abs_fit=nan` because they have no insertions). This means essential genes with no measured fitness data (e.g., rank #3 Putida/PP_2706 with `|f|=nan`) score the same as genes with extremely strong measured phenotypes. The scoring treats absence of data (no insertions) the same as strong evidence of function. This is a valid design choice but worth acknowledging -- 34 of the top 100 candidates are essential with nan fitness, and their "importance" is inferred from essentiality rather than observed phenotypes.

5. **NB01 cell 12: Gene length estimated from molecular weight**: Protein length is estimated as `molecular_weight / 110` (110 Da per amino acid). This is a reasonable approximation but the actual average amino acid molecular weight is ~111-113 Da depending on composition. The estimate introduces ~1-3% systematic error, which is negligible for the statistical comparisons but could be noted.

6. **NB03 cell 8: Pfam and eggNOG clue counts differ from NB02**: NB02 reports 235 clusters with Pfam hits and 2,551 with eggNOG, but NB03's clue matrix shows `has_pfam=288` and `has_eggnog=2,934`. The discrepancy arises because NB03 merges on `gene_cluster_id` (6,427 genes but only 5,870 unique clusters), so multiple genes mapping to the same cluster each get counted. NB02 counts unique clusters while NB03 counts genes. Both are correct but the difference is not explained in the notebooks. The REPORT.md uses both numbers in different places (4.0% for clusters in Finding 3, 4.5% for genes in Finding 4), which could cause confusion.

## Findings Assessment

**Conclusions well-supported**: The findings are generally well-supported by the data shown:
- H1 (structural distinctiveness): Strong evidence across multiple metrics with large effect sizes. The core genome fraction OR of 0.284 and ortholog breadth Cohen's d of -1.072 are particularly compelling.
- H3 (accessory/HGT): Supported by GC deviation, mobile element proximity, and reduced ortholog breadth, though the GC deviation effect size (d=0.247) is modest.
- H4 (partial clues): The 96.2% coverage with at least one clue is clear and well-visualized.
- H2 (stress enrichment): Honestly rejected with OR=0.53 in the opposite direction.

**Limitations acknowledged**: The REPORT.md has a thorough Limitations section covering pangenome linkage gap, bakta false negatives, ortholog coverage, GC deviation caveats, gene length confound, and fitness artifacts. The gene length confound (d = -0.432) is particularly important because shorter genes are inherently harder to annotate, and this could partially explain many of the other observed differences. The report acknowledges this but does not perform length-stratified analyses to quantify how much of the H1 signal survives after controlling for length.

**Incomplete analysis**: The clue-concordance validation (whether more clues predict higher concordance) was planned but not completed, as noted above. This is acknowledged implicitly by the project moving on.

**REPORT.md quality**: Well-organized with clear findings, a detailed results section, thoughtful interpretation including literature context, and specific future directions. The references are appropriate and properly cited.

**Condition enrichment interpretation**: The REPORT.md claims truly dark genes are enriched in "mixed community" and "iron" conditions, and the data supports this (7.5% vs 0% for mixed community). However, some of the extreme enrichment ratios (e.g., 181x for "nutrient t2") appear driven by a single organism's contribution to the truly dark set and the small denominator in the annotation-lag set. No formal statistical test (e.g., Fisher's exact per condition class with FDR correction) was applied to the condition enrichment -- only descriptive percentages are reported.

## Suggestions

1. **Fix the regex warning in NB05**: Change `'IS\d'` to `r'IS\d'` in cell 5. This is a trivial fix that prevents the SyntaxWarning and future-proofs the code against Python's planned deprecation of unrecognized escape sequences.

2. **Compute organism GC means from all FB genes, not just dark genes**: In NB04 cell 12, the "genome mean GC" should ideally be computed from the full `kescience_fitnessbrowser.gene` table (all 228K genes), not the 39,532-gene dark subset. This could be done with a single Spark query in NB02 or by loading the full gene table. Add a comment if the current approach is kept, noting that the baseline is dark-gene-only.

3. **Add length-stratified analysis for H1**: The gene length difference (d = -0.432) is a potential confound for other comparisons. Add a brief analysis in NB01 that repeats key comparisons (conservation, ortholog breadth) within matched length bins (e.g., 50-150 aa, 150-300 aa, 300+ aa). This would strengthen the H1 conclusion by showing which effects persist after controlling for length.

4. **Apply statistical tests to condition enrichment**: The condition enrichment analysis in NB05 (cell 11-12) uses only descriptive percentages. Add Fisher's exact tests with BH-FDR correction for individual condition classes to identify which specific enrichments are statistically significant. The current analysis only tests stress vs non-stress as a group, missing the opportunity to formally test individual conditions.

5. **Clarify Pfam/eggNOG count discrepancies**: Add a brief note in NB03 or the REPORT explaining why the clue matrix gene counts (288 with Pfam, 2,934 with eggNOG) differ from the NB02 unique cluster counts (235 and 2,551). The distinction between "genes" and "clusters" is important and currently left to the reader to figure out.

6. **Acknowledge incomplete concordance-clue validation**: Add an explicit note in NB04 or the REPORT stating that the planned clue-concordance validation could not be completed due to insufficient sample size (only 3 truly dark OGs with concordance data). This is a minor gap given the data constraint, but should be documented rather than silently dropped.

7. **Consider revising the scoring for essential genes with no fitness data**: The current scoring gives essential genes with `max_abs_fit=nan` the same fitness score (3) as genes with extreme measured phenotypes. Consider either (a) splitting essentiality into its own scoring axis rather than bundling it with fitness magnitude, or (b) adding a bonus for genes that are essential AND have measured phenotypes in specific conditions. Many of the top-100 candidates (particularly the DvH essential genes ranked #21-30) have no functional clues and no measured phenotype -- their high ranking is driven entirely by essentiality + tractability + orthologs.

8. **Document the 41% hypothetical neighbor finding more prominently**: The "dark islands" finding (41% of neighbors are hypothetical) is one of the most interesting results and gets good coverage in the REPORT's interpretation section, but the analysis in NB05 only reports the aggregate mean. A figure showing the distribution of per-gene hypothetical neighbor fraction, or examples of the longest dark islands, would strengthen this finding.

9. **Minor: Add `statsmodels` to the requirements.txt description**: The `requirements.txt` correctly lists `statsmodels`, but the README's Dependencies section only mentions `numpy, pandas, matplotlib, seaborn, scipy` -- `statsmodels` is missing from that list.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-14
- **Scope**: README.md, 6 notebooks, 15 data files, 9 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
