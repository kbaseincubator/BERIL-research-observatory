---
reviewer: BERIL Automated Review
date: 2026-02-22
project: counter_ion_effects
---

# Review: Counter Ion Effects on Metal Fitness Measurements

## Summary

This is an excellent, well-executed project that asks a critical methodological question: does the chloride delivered by metal chloride salts confound genome-wide fitness measurements in the Fitness Browser? The analysis is thorough, covering 5 notebooks across 25 organisms and 14 metals, and reaches a clear, well-supported conclusion — counter ions are NOT the primary confound, and the ~40% metal–NaCl gene overlap reflects shared stress biology. The use of zinc sulfate (zero chloride) as a natural control is particularly compelling. Documentation is strong: the README, RESEARCH_PLAN, and REPORT are detailed and well-structured. The main issues are several numerical discrepancies between notebook outputs and the REPORT text, and the functional annotation finding in the REPORT is reversed relative to what the notebook actually shows.

## Methodology

**Research question**: Clearly stated, testable, and scientifically important. The four sub-hypotheses (H1a–d) have explicit, quantitative predictions.

**Approach**: Sound and well-designed. The strategy of comparing metal-important gene sets with NaCl-important gene sets is straightforward and appropriate. The use of zinc sulfate as a zero-chloride control is a natural experiment that makes the dose-response test (H1b) particularly convincing. Statistical methods (Fisher exact test, Spearman correlation, Mann-Whitney U) are appropriate for the data types.

**Data sources**: Clearly identified in both the README and RESEARCH_PLAN. Dependencies on prior project cached data (fitness_modules, metal_fitness_atlas, conservation_vs_fitness) are documented with specific file paths.

**Reproducibility**: Strong. The README includes a complete `## Reproduction` section with step-by-step commands. All notebooks run locally (no Spark required) and are documented to complete in under 1 minute. A `requirements.txt` is provided with appropriate dependency versions.

**Hypothesis testing**: H1a was supported (39.8% overlap), H1b was rejected (zinc sulfate ranks 4th despite zero Cl⁻), H1c was rejected (core enrichment is robust), and H1d was dropped. The honest reporting of dropped analyses (NB06, NB07) in the RESEARCH_PLAN revision history is good practice.

**One methodological note**: The RESEARCH_PLAN (Notebook 1) specifies NaCl-importance as "fit < -1, |t| > 4", but the cached fitness matrices lack t-scores. The actual implementation in NB01 (cell 6) uses `mean_fit < -1 OR n_sick >= 1`, which is a more permissive threshold. This substitution is reasonable given the data available, but should be documented.

## Code Quality

**Notebook organization**: All 5 notebooks follow a clean structure: markdown header with inputs/outputs → setup → analysis → visualization → summary. Each notebook builds on the previous one's outputs, with clear data flow.

**Pandas operations**: Clean and efficient. No unnecessary loops over large DataFrames. The use of set operations for gene overlap computation (cell 3 of NB02) is appropriate. Groupby aggregations are well-structured.

**Statistical methods**: Appropriate throughout. Fisher exact tests for enrichment, Spearman correlation for the dose-response test (appropriate given the non-linear relationship), Mann-Whitney for group comparisons.

**Pitfall awareness**: The project correctly handles the Fitness Browser "all columns are strings" pitfall by using pre-cast cached matrices from the fitness_modules project. No Spark is needed, avoiding the REST API reliability and `.toPandas()` pitfalls. The `docs/pitfalls.md` entry about essential genes being invisible in genefitness-only analyses is relevant — the REPORT's limitations section correctly notes that "~14.3% of protein-coding genes (putative essentials) lack transposon insertions" and are excluded.

**Potential issue in NB01 cell 9**: The `classify_counter_ion` function handles cadmium chloride but `conc` may be NaN, leading to `cl_conc = valence * NaN = NaN`. The NB01 output confirms this (Cadmium: min_cl=NaN, max_cl=NaN). This is handled gracefully downstream (NaN propagation), but an explicit note would help.

**NB03 cell 6**: The SEED annotation file is loaded from `ESSENTIAL / 'all_seed_annotations.tsv'`, depending on the essential_genome project's data directory. This cross-project dependency is not listed in the README Data Sources section.

## Findings Assessment

**Conclusions are well-supported**: The three lines of evidence for "shared stress biology, not counter ion contamination" (zinc sulfate control, no Cl⁻ dose-response, psRCH2 comparison) are independently compelling and collectively convincing.

**Limitations are thorough**: The REPORT acknowledges NaCl ≠ pure Cl⁻, threshold sensitivity, essential gene exclusion, single-organism metals, psRCH2 confound, and lack of formal functional enrichment testing.

**However, there are numerical discrepancies between notebook outputs and the REPORT:**

1. **DvH gene classification counts (REPORT Finding #5 vs NB03 cell 4)**: The REPORT states "For DvH, 495 unique metal-important genes split into 105 shared-stress (21.2%) and 390 metal-specific (78.8%)." NB03 cell 4 output shows 73 shared-stress and 422 metal-specific. The "105" in the REPORT appears to be the total NaCl-important gene count for DvH (from NB01), not the intersection with metal-important genes.

2. **Functional annotation direction is reversed (REPORT Finding #5 vs NB03 cell 6)**: The REPORT states "shared-stress genes are more functionally annotated (71% have SEED annotations) than metal-specific genes (62%)." NB03 cell 6 output shows the opposite: shared_stress = 78.1% annotated, metal_specific = 90.5% annotated. The direction is reversed and the percentages don't match.

3. **Organism count (REPORT Finding #1)**: The REPORT states "Across 25 organisms and 14 metals" for the overlap analysis. NB02 cell 3 output shows 19 organisms and 14 metals (86 organism × metal pairs). The 25 figure is the number of organisms with NaCl experiments (NB01), but only 19 have metal-important genes in the atlas dataset and contribute to the overlap analysis. The REPORT's "Scale of the Analysis" table correctly lists 86 organism × metal pairs but says "Testable organisms: 25" which is inconsistent.

These are reporting errors rather than analytical errors — the notebooks themselves appear to produce correct results. But they undermine confidence in the REPORT's accuracy and should be corrected.

**Dropped analyses**: H1d (anion-specific signatures) and Notebooks 6–7 were dropped. This is documented in the RESEARCH_PLAN revision history, which is good practice. The rationale is sound — the main findings from NB01–05 clearly resolve the research question.

## Suggestions

1. **[Critical] Fix the DvH gene classification numbers in the REPORT**: Finding #5 reports "105 shared-stress (21.2%) and 390 metal-specific (78.8%)" but the notebook output shows 73 shared-stress and 422 metal-specific. Update the REPORT to match the notebook output.

2. **[Critical] Fix the reversed annotation enrichment in the REPORT**: Finding #5 says shared-stress genes are more annotated (71%) than metal-specific (62%), but NB03 shows the opposite (78.1% vs 90.5%). Correct the direction and percentages. Consider whether the biological interpretation ("consistent with shared-stress genes being core cellular machinery") needs revision.

3. **[Important] Correct the organism count in the REPORT**: Change "Across 25 organisms" in Finding #1 to "Across 19 organisms" (or clarify that 25 organisms have NaCl data while 19 contribute to the overlap analysis). Similarly update the "Testable organisms" row in the Scale table.

4. **[Minor] Document the threshold substitution**: Note in NB01 that the NaCl-importance threshold was simplified from the RESEARCH_PLAN's "fit < -1, |t| > 4" to "mean_fit < -1 or n_sick ≥ 1" because the cached matrices lack t-scores.

5. **[Minor] Add essential_genome dependency to README**: The Data Sources section lists dependencies on metal_fitness_atlas, fitness_modules, and conservation_vs_fitness, but NB03 also reads SEED annotations from the essential_genome project (`all_seed_annotations.tsv`). Add this to the Data Sources list.

6. **[Nice-to-have] Visualize the functional enrichment comparison**: NB03's annotation comparison (shared-stress vs metal-specific genes) is presented only as text output. A simple bar chart or word cloud of the top functional categories in each class would strengthen Finding #5.

7. **[Nice-to-have] Add a sensitivity analysis on the NaCl-importance threshold**: The REPORT's limitations note that the 39.8% overlap depends on the threshold. A brief test with stricter (fit < -2) and more permissive (fit < -0.5) thresholds would demonstrate robustness.

8. **[Nice-to-have] Add NB03 formal enrichment testing**: The REPORT's limitations acknowledge the absence of hypergeometric/Fisher exact tests for functional category enrichment between shared-stress and metal-specific gene classes. Even a simple Fisher test for a few key COG categories would strengthen the functional interpretation.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-22
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks, 11 data files, 7 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
