---
reviewer: BERIL Automated Review
date: 2026-02-19
project: aromatic_catabolism_network
---

# Review: Aromatic Catabolism Support Network in ADP1

## Summary

This is a well-executed project that investigates why aromatic catabolism in *Acinetobacter baylyi* ADP1 requires Complex I, iron acquisition, and PQQ biosynthesis genes beyond the 6 core degradation enzymes. The analysis is methodologically sound, progressing logically from FBA-based metabolic dependency mapping through genomic organization and co-fitness network analysis to cross-species validation. The project produces a clear, biologically coherent answer: aromatic catabolism requires a 51-gene support network organized into 4 biochemically rational subsystems, with Complex I as the dominant component (41%). The cross-species analysis adds an important nuance — the Complex I dependency is on high-NADH-flux substrates generally, not aromatics exclusively. All four notebooks have saved outputs, 9 figures are generated, 7 data files are produced, and the documentation (README, RESEARCH_PLAN, REPORT) is thorough. The main areas for improvement are methodological: the co-fitness confidence thresholds need better justification, the keyword-based gene categorization function is fragile and duplicated across notebooks, and some statistical claims would benefit from stronger controls.

## Methodology

**Research question**: Clearly stated and testable, with explicit null and alternative hypotheses (RESEARCH_PLAN.md, lines 7-8). The hypothesis structure is a strength — H0 (artifact of growth assay) vs H1 (specific metabolic dependency network) provides a clear framework for interpreting results.

**Approach**: The four-aim structure is well-designed and builds progressively:
1. FBA predictions establish the metabolic logic (NB01)
2. Genomic organization tests physical linkage (NB02)
3. Co-fitness networks provide functional grouping (NB03)
4. Cross-species validation tests generality (NB04)

This multi-evidence approach is appropriate for the question. Each aim contributes independently, and the convergence of evidence strengthens the conclusion.

**Data sources**: Clearly identified in both the README and RESEARCH_PLAN. The project primarily uses a local SQLite database (`berdl_tables.db`) derived from prior work, supplemented by ortholog-transferred fitness data. The dependency on `projects/adp1_deletion_phenotypes/` for the initial 51-gene list is documented.

**Reproducibility**: Good. The README includes a Reproduction section with exact `nbconvert` commands. All notebooks run locally (no Spark required), which eliminates a major reproducibility barrier. A `requirements.txt` is provided with appropriate version constraints.

**Concern — gene categorization fragility**: The `categorize_gene()` function (NB01, cell 1) uses keyword matching on RAST function descriptions. This misclassifies ACIAD1710 (4-carboxymuconolactone decarboxylase, EC 4.1.1.44) as "Other" despite it being a core pca pathway enzyme — the keyword list checks for "muconate" but not "muconolactone." The co-fitness analysis in NB03 correctly recovers this gene (r=0.978 with Aromatic pathway), but the initial miscategorization propagates through NB01 and NB02 analyses. More importantly, this same function is copy-pasted identically into all 4 notebooks, creating a maintenance risk.

## Code Quality

**Notebook organization**: Each notebook follows a clear setup-analysis-visualization-summary pattern with markdown section headers. The cell-level documentation is good, and each notebook ends with a summary cell printing key results.

**SQL queries**: The FBA queries against the SQLite database are straightforward and correct. The NB04 cross-species query correctly uses `CAST(fitness_avg AS FLOAT)` for the string-typed fitness browser columns, consistent with the pitfall documented in `docs/pitfalls.md` (lines 63-69).

**Code duplication**: The `categorize_gene()` function is duplicated verbatim in NB01 (cell 1), NB02 (cell 1), NB03 (cell 1), and referenced indirectly in NB04 via the saved `final_network_model.csv`. This should be extracted to a shared utility module.

**Statistical methods**:
- Pearson correlation for co-fitness (NB03) is appropriate for the 8-condition growth profiles.
- Mann-Whitney U test (NB04, cell 10) for Complex I aromatic specificity is correctly applied as a non-parametric test. However, the same test on background (non-network) genes also shows p<0.0001, indicating that ALL genes — not just Complex I — show worse fitness on aromatics. The Complex I-specific interpretation needs this context stated more prominently.
- No multiple testing correction is applied across the 13 per-condition comparisons (NB04, cell 12). Given the small number of tests, this is acceptable but should be acknowledged.

**Co-fitness confidence thresholds** (NB03, cell 11): The confidence scheme requires r>0.7 AND a >0.15 gap to the second-best category for "High" confidence. This means ACIAD3137 (r=0.988 with Complex I, gap=0.098 to Aromatic pathway) gets "Medium" while ACIAD1818 (r=0.977, gap>0.15) gets "High." The thresholds are reasonable but the gap criterion should be documented with a rationale — with only 8 conditions, many genes will correlate moderately with multiple subsystems simply due to the shared quinate defect.

**Operon prediction** (NB02, cell 6): The method (<100 bp intergenic distance, same strand) is a standard heuristic and is well-suited for this analysis. The results match published data (Dal et al. 2005 pca/qui operon structure).

**Pitfall awareness**: The project correctly handles string-typed fitness browser columns. Since most analysis is done locally on the SQLite database rather than via BERDL Spark queries, most BERDL-specific pitfalls are not applicable. The cross-species analysis in NB04 uses pre-computed ortholog-transferred scores from the SQLite rather than querying BERDL directly — the methodology of this ortholog transfer (which organisms contributed, what thresholds were used) is not documented in this project, relying instead on the upstream `adp1_deletion_phenotypes` project.

## Findings Assessment

**Conclusions supported by data**:
- The 4-subsystem model (Aromatic pathway, Complex I, Iron, PQQ) is well-supported by the convergence of FBA predictions, genomic organization, and co-fitness correlations.
- The FBA blind spot finding (30/51 genes with no reaction mappings, 0% essentiality for Complex I despite 1.76x higher flux) is clearly demonstrated in NB01 cells 3 and 8.
- The genomic independence of subsystems (NB02) is convincingly shown — no cross-category operons exist except within the aromatic pathway itself.
- Co-fitness within Complex I (r=0.992) and Aromatic pathway (r=0.961) is very high, consistent with their operon structure.

**Nuanced cross-species finding**: The NB04 finding that Complex I defects are largest on acetate (-1.55) and succinate (-1.39), not aromatics, is an important nuance. The interpretation — that ADP1's quinate-specificity reflects NDH-2 compensation on simpler substrates — is reasonable and well-supported. This partially supports H0 (the dependency is not exclusively aromatic).

**Limitations acknowledged**: Yes, the REPORT.md Limitations section (lines 116-121) identifies four key limitations: the 8-condition resolution limit, mixed signals from multiple FB organisms, indirect co-fitness evidence, and PQQ's shared glucose dependency. These are honest and appropriate.

**Count discrepancies between report and data**: The REPORT.md states the network has "8 genes" in the Aromatic pathway and "7 genes" in Iron acquisition (Table in Key Finding 1), reflecting the final co-fitness-updated categories from NB03. The NB01 analysis uses the initial keyword-based categories (6 Aromatic, 4 Iron). The progression from initial to final categories is explained but could be clearer — a reader looking only at NB01 output sees different numbers than the REPORT summary.

**PQQ/Iron cross-species data is thin**: NB04 cell 6 shows only 4 aromatic fitness entries from 1 gene in the PQQ/Iron category. The REPORT wisely focuses the cross-species story on Complex I, but the PQQ/Iron gap should be noted as a limitation.

**Missing analysis**: The RESEARCH_PLAN Aim 3 mentions using `kbase_ke_pangenome.eggnog_mapper_annotations` for cross-species pangenome comparison of pca pathway and Complex I co-occurrence. This was not performed — NB04 uses ortholog-transferred fitness from the SQLite instead. This is a reasonable scope reduction, and it is listed as Future Direction #4 in the REPORT.

## Suggestions

1. **Extract `categorize_gene()` to a shared module** (high impact, easy fix): Create a `utils.py` or `common.py` in the notebooks directory and import the function. Fix the keyword list to include "muconolactone" so ACIAD1710 is correctly classified from the start. This eliminates 4 copies of the same code.

2. **Strengthen the Complex I aromatic-specificity statistical claim** (high impact): NB04 cell 10 shows both Complex I *and* background genes have significantly worse fitness on aromatics (both p<0.0001). The biologically meaningful test is whether Complex I's aromatic deficit is *disproportionately larger* than background — i.e., an interaction test. Consider a two-way comparison: compute the aromatic-vs-non-aromatic difference for Complex I genes and for background genes, then test whether these differences differ (e.g., permutation test on the interaction term). The per-condition analysis in cell 12 partially addresses this, but a formal interaction test would be more rigorous.

3. **Document the ortholog transfer methodology** (medium impact): NB04 uses `fitness_match = 'has_score'` and `fitness_avg` from the SQLite database without explaining how these ortholog-transferred scores were computed. Add a brief methods note: which FB organisms contributed, what ortholog detection method was used, and how scores were aggregated. This is critical for reproducibility since the analysis depends entirely on these transferred scores.

4. **Add a transition figure or table showing initial → final categorization** (medium impact, easy fix): The jump from NB01's keyword-based categories (10 Complex I, 4 Iron) to the REPORT's co-fitness-updated categories (21 Complex I, 7 Iron) would benefit from a Sankey diagram or simple before/after table showing which genes moved. NB03 cell 13 has this as a text table, but a visual would strengthen the narrative.

5. **Acknowledge that within/between co-fitness difference is modest overall** (low-medium impact): NB03 cell 5 shows within-category mean r=0.552 vs between-category r=0.518 — a small difference. The very high within-category values for Complex I (0.992) and Aromatic pathway (0.961) are driven by their tight operon co-regulation. The "Other" and "Unknown" categories have low within-category correlations (0.425, 0.342), which is expected since they are heterogeneous groupings. This context would help readers interpret the co-fitness assignments correctly.

6. **Apply multiple testing correction to per-condition comparisons** (low impact, easy fix): NB04 cell 12 compares Complex I vs background fitness across 13 conditions without correction. While the number of tests is small, applying Bonferroni or BH-FDR would strengthen the claim that specific conditions (acetate, succinate, ferulate, vanillin) show disproportionate Complex I defects.

7. **Consider adding the planned pangenome comparison as future work** (nice-to-have): The RESEARCH_PLAN describes using BERDL's `eggnog_mapper_annotations` to test whether genomes carrying pca pathway KOs are more likely to retain Complex I. This was deferred to Future Direction #4 in the REPORT, which is appropriate — but it would be the strongest test of H1 and is worth flagging as a high-priority follow-up.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, 4 notebooks, 7 data files, 9 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
