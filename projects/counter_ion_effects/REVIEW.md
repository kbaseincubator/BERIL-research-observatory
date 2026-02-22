---
reviewer: BERIL Automated Review
date: 2026-02-22
project: counter_ion_effects
---

# Review: Counter Ion Effects on Metal Fitness Measurements

## Summary

This is a well-conceived and thoroughly executed project that addresses a genuinely important methodological question: does chloride delivered by metal chloride salts confound genome-wide fitness measurements in the Fitness Browser? The analysis spans 5 notebooks, 25 organisms, and 14 metals, reaching a clear, well-supported conclusion — counter ions are NOT the primary confound, and the ~40% metal–NaCl gene overlap reflects shared stress biology rather than methodological artifact. The use of zinc sulfate as a zero-chloride natural control is the strongest piece of evidence and is elegantly presented. Documentation is excellent across the README, RESEARCH_PLAN, and REPORT, with all key numerical claims now matching notebook outputs. The main areas for improvement are: (1) the NaCl-importance threshold is not adjusted for experiment count, which makes SynE a dramatic outlier that warrants discussion; (2) the RESEARCH_PLAN still describes a threshold ("fit < -1, |t| > 4") that differs from the implementation; and (3) the conservation analysis in NB04 silently loses 2 organisms relative to the overlap analysis.

## Methodology

**Research question**: Clearly stated, scientifically important, and testable. The four sub-hypotheses (H1a–d) have explicit, quantitative predictions — a model for how to structure hypothesis-driven data analysis. The honest acknowledgment that H1d was dropped (with rationale in the RESEARCH_PLAN revision history) is good practice.

**Approach**: The strategy of comparing metal-important gene sets with NaCl-important gene sets is sound and appropriate. Three independent lines of evidence converge on the same conclusion (zinc sulfate control, no Cl⁻ dose-response, psRCH2 comparison), making the argument robust. Statistical methods (Fisher exact test, Spearman correlation, Mann-Whitney U) are appropriate for the data types.

**Data sources**: Clearly identified in both the README and RESEARCH_PLAN, including cross-project dependencies (metal_fitness_atlas, fitness_modules, conservation_vs_fitness, essential_genome). The project runs entirely locally from cached data — no Spark needed — which is well-documented in the Reproduction section.

**Reproducibility**: Strong. The README provides step-by-step `nbconvert` commands, documents that no Spark is required, and estimates runtime at under 1 minute. A `requirements.txt` with appropriate package versions is provided. Each notebook declares its inputs and outputs in the header markdown cell.

**Threshold concern**: The NaCl-importance threshold (`mean_fit < -1 OR n_sick >= 1`) is not adjusted for the number of NaCl experiments per organism. This creates a systematic bias: organisms with more NaCl experiments are more likely to have any given gene classified as NaCl-important (because `n_sick >= 1` is easier to satisfy with 12 experiments than with 1). SynE has 12 NaCl dose-response experiments (0.5–250 mM) and consequently flags 620 genes (32.6%) as NaCl-important — 3× higher than the next organism (psRCH2, 10.5%). In the overlap analysis, SynE shows 88.6% shared-stress — an extreme outlier. The REPORT doesn't discuss this organism-level variability or whether the overall 39.8% overlap changes meaningfully if SynE is excluded or the threshold is made consistent.

## Code Quality

**Notebook organization**: All 5 notebooks follow a clean, consistent structure: markdown header with inputs/outputs, imports and paths, numbered analysis sections, visualizations, and a summary. Data flows clearly from NB01 → NB02 → NB03 → NB04, with NB05 as a standalone comparison. Each notebook saves intermediate outputs for downstream use.

**Pandas operations**: Clean and efficient throughout. Set operations for gene overlap (NB02 cell 3), groupby aggregations for per-metal summaries, and proper use of merge operations. No unnecessary row-wise iteration on large DataFrames.

**Statistical methods**: Appropriate. Fisher exact tests for enrichment, Spearman for the non-linear dose-response test, Mann-Whitney for group comparisons. P-values are reported alongside effect sizes.

**Pitfall awareness**: The project elegantly avoids the most common BERDL pitfalls by using pre-cast cached fitness matrices from the fitness_modules project, eliminating Spark entirely. This sidesteps the REST API reliability issues, `.toPandas()` memory concerns, and the "all columns are strings" casting problem documented in `docs/pitfalls.md`. The essential genes invisibility pitfall is correctly acknowledged in the REPORT's limitations section.

**Specific code notes**:

- NB01 cell 9: The `classify_counter_ion` function produces `NaN` for cadmium's Cl⁻ concentration (because `conc` is NaN). This propagates correctly through downstream analysis but an explicit comment would aid readability.

- NB02 cell 3: The Fisher exact test contingency table sets `d = max(0, total_genes - |metal ∪ nacl|)`. The `max(0, ...)` guard is defensive coding — good practice even though `d` should always be non-negative.

- NB04 cell 4: The merge with conservation data drops from 10,821 classified gene records (19 organisms) to 8,924 (17 organisms). Two organisms lack FB-pangenome links in the `conservation_vs_fitness` data, but this is not logged or discussed. The REPORT's conservation tables silently reflect 17 organisms without noting the discrepancy with the 19-organism overlap analysis.

## Findings Assessment

**Conclusions are well-supported**: The central claim — counter ions are NOT the primary confound — rests on three independent lines of evidence, each compelling on its own:

1. Zinc sulfate (0 mM Cl⁻) showing the highest DvH NaCl correlation (r=0.715) and 4th-highest gene overlap (44.6%)
2. No significant Spearman correlation between Cl⁻ concentration and overlap (rho=-0.122, p=0.338)
3. psRCH2 CuSO₄ correlating more with NaCl (r=0.450) than CuCl₂ (r=0.212)

**Numerical accuracy**: All key numbers in the REPORT now match their source notebook outputs: 39.8% overall overlap (NB02 cell 4), DvH gene classification of 73 shared-stress / 422 metal-specific (NB03 cell 4), SEED annotation rates of 78.1% / 90.5% (NB03 cell 6), per-metal corrected conservation deltas (NB04 cell 6), and psRCH2 correlation values (NB05 cell 2). This is a significant improvement over the previous review's findings.

**Limitations are thorough**: The REPORT acknowledges NaCl ≠ pure Cl⁻, threshold sensitivity, essential gene exclusion, single-organism metals, the psRCH2 aerobic/anaerobic confound, and the lack of formal functional enrichment testing. These are the correct limitations to flag.

**Gaps**:

- **SynE outlier not discussed**: SynE's 88.6% shared-stress rate is a dramatic outlier driven by its 12 NaCl dose-response experiments (vs 1–6 for most organisms). The per-metal and overall statistics include SynE without flagging its unusual behavior. A sensitivity analysis excluding SynE (or using a consistent threshold like requiring n_sick >= 2) would strengthen confidence in the 39.8% figure.

- **Iron statistical power**: Iron has only 9 metal-important genes (6 after correction), yet appears in the REPORT's corrected conservation table with a corrected delta of +0.182 (100% core). This is statistically meaningless but isn't flagged the way Cadmium (n=92) is. Both should carry caveats.

- **Conservation analysis organism loss**: NB04 retains 17 of 19 organisms due to missing pangenome links. The REPORT doesn't document which 2 organisms were lost or whether this affects the overall conclusions.

**RESEARCH_PLAN threshold discrepancy**: The RESEARCH_PLAN (Notebook 1 method, line 121) specifies NaCl-importance as "fit < -1, |t| > 4", but the implementation uses "mean_fit < -1 OR n_sick >= 1" because cached matrices lack t-scores. The REPORT correctly documents the actual threshold in the Limitations section, but the RESEARCH_PLAN was not updated to reflect the change.

## Suggestions

1. **[Important] Discuss SynE's outlier behavior**: SynE has 12 NaCl dose-response experiments spanning 0.5–250 mM, resulting in 32.6% of genes flagged as NaCl-important (vs ~2–11% for other organisms). Its 88.6% shared-stress rate could inflate the overall 39.8% overlap. Either (a) report the overall overlap with and without SynE, or (b) use a threshold that accounts for experiment count (e.g., requiring n_sick >= 2 or mean_fit < -1 without the n_sick alternative). Even a brief note acknowledging the organism-level variability would help.

2. **[Important] Flag Iron alongside Cadmium for low statistical power**: The corrected conservation table shows Iron jumping from delta -0.040 to +0.182 based on 6 genes. Add a parenthetical caveat similar to the Cadmium note: "(n=9, 1 organism)".

3. **[Minor] Document the 2 organisms lost in NB04**: Note in the REPORT or NB04 which organisms lack FB-pangenome links, and confirm that the per-metal results aren't materially affected. A one-line log statement in NB04 cell 4 showing which organisms are dropped would also help reproducibility.

4. **[Minor] Update the RESEARCH_PLAN threshold**: Change the NB01 method from "fit < -1, |t| > 4" to "mean_fit < -1 or n_sick >= 1" to match the implementation. The revision history already documents analysis changes — this would be a minor addition.

5. **[Nice-to-have] Add a threshold sensitivity analysis**: The REPORT's limitations correctly note threshold dependence. A brief check with stricter (mean_fit < -2) and more permissive (mean_fit < -0.5) thresholds — even as a single summary sentence — would demonstrate robustness and address the SynE concern simultaneously.

6. **[Nice-to-have] Visualize functional enrichment**: NB03's annotation comparison (shared-stress 78.1% vs metal-specific 90.5%) is text-only. A simple bar chart of the top SEED categories in each class would make Finding #5 more accessible and strengthen the biological interpretation.

7. **[Nice-to-have] Add formal enrichment testing for gene classes**: The REPORT acknowledges the absence of hypergeometric tests for functional categories. Even a simple Fisher test for a few key categories (cell envelope, ion transport, DNA repair) would add statistical rigor to the gene classification narrative.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-22
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, previous REVIEW.md, 5 notebooks, 9 data files, 7 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
