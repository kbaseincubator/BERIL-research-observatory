---
reviewer: BERIL Automated Review
date: 2026-02-15
project: field_vs_lab_fitness
---

# Review: Field vs Lab Gene Importance in *Desulfovibrio vulgaris* Hildenborough

## Summary

This is a well-designed and honestly reported project that asks whether genes important under environmentally-realistic conditions (uranium, mercury, sulfate reduction) show different pangenome conservation patterns than genes important under lab-only conditions (antibiotics, rich media). The analysis pipeline is clean and logically structured across four notebooks, the condition classification scheme is thoughtfully grounded in DvH ecology at the Oak Ridge FRC, and the statistical analyses are mostly appropriate. The project arrives at a nuanced answer: field-stress genes are modestly more conserved (83.6% core, OR=1.58, FDR q=0.026), but fitness magnitude matters more than condition type for predicting conservation (CV-AUC 0.52-0.55 for condition-type models vs 0.65 with gene length). Documentation is exemplary -- the README, RESEARCH_PLAN, and REPORT form a coherent three-file structure with clear data provenance, thorough limitations, and honest reporting of largely null results. The main areas for improvement are: (1) a missing data-saving step for `gene_fitness_conservation.csv`, (2) `statsmodels` is an undeclared dependency, and (3) the module-level correlation analysis in NB04 is inherently limited by the ceiling effect (median core fraction = 1.0 across 52 modules).

## Methodology

**Research question**: Clearly stated and testable. Three hypotheses (H1-H3) are explicitly articulated alongside a null hypothesis (H0), which is a strong practice. The two-level approach (gene-level in NB03 and module-level in NB04) provides complementary perspectives.

**Approach**: Sound overall. The six-category condition classification (NB02) is well-designed with 52 pattern-matching rules and sensible fallback logic using `expGroup`. The classification is validated with a cross-tabulation (NB02 cell 8) showing that field-core aligns with `respiratory growth` and `stress`, while lab categories align with `nutrient` and `nitrogen source`. The specificity analysis (field-specific vs lab-specific vs universal genes) is a valuable addition that reveals the counter-intuitive finding that lab-specific genes are 96% core.

**Data sources**: All upstream data is clearly identified and properly attributed to prior projects (`conservation_vs_fitness`, `fitness_modules`). The ENIGMA CORAL discovery (NB01) is a responsible first step that documents the absence of DvH data in that database, avoiding incorrect assumptions.

**Reproducibility concerns**:
- The condition classification rules are embedded in code (NB02 cell 3) rather than an external configuration file. This is acceptable for a one-off analysis but makes it harder to version or modify the classification independently.
- Edge cases in classification (e.g., "zinc sulfate" as metal vs sulfate) are handled by rule ordering but documented only implicitly through the code structure.

**Essential genes handling**: NB03 correctly acknowledges that 678 essential genes are excluded from fitness analyses (cell 8 prints a detailed note explaining why and reports their 80.1% core fraction). They are also included as a separate bar in Figure 1 and as a row in the condition importance table (cell 10). This is a significant strength -- the analysis is transparent about what it cannot measure.

## Reproducibility

**Notebook outputs**: All four notebooks have saved outputs (text tables, printed summaries, and figure outputs). NB02, NB03, and NB04 all have execution outputs preserved in cells, making the results visible without re-running. NB01 has a detailed execution summary in its header markdown cell but the code cells themselves lack saved outputs (expected, since NB01 requires Spark Connect). This is clearly documented in the reproduction guide.

**Figures**: The `figures/` directory contains 6 PNG files covering all major analysis stages: condition classification results (fig 1), field-vs-lab scatter (fig 2), ROC curves (fig 3), condition importance heatmap (fig 4), module conservation scatter (fig 5), and ecological vs lab module comparison (fig 6). This is comprehensive coverage for the 3 analysis notebooks.

**Dependencies**: A `requirements.txt` is present with 6 packages (pandas, numpy, matplotlib, seaborn, scipy, scikit-learn). However, `statsmodels` is imported in NB03 cell 10 (`from statsmodels.stats.multitest import multipletests`) but not listed in `requirements.txt`. This would cause a failure on a fresh environment.

**Reproduction guide**: The README includes a clear `## Reproduction` section with prerequisites, Spark/local separation, and executable commands. NB01 (Spark) is noted as already run, and NB02-04 can be run locally with `jupyter nbconvert`.

**Spark/local separation**: Clearly documented. NB01 requires Spark; NB02-04 run locally from cached data. Each notebook header states its execution environment.

**Missing data-saving step**: The REPORT lists `gene_fitness_conservation.csv` as a data file output, and the file exists on disk (922KB), but no notebook cell contains code to save it. It was likely saved during an interactive session or from a cell that was later removed. This breaks full automated reproducibility via `nbconvert`.

## Code Quality

**Notebook organization**: All four notebooks follow a clean setup → data loading → analysis → visualization → summary flow. Markdown headers and summary cells at the end of each notebook consolidate key findings. NB03 is particularly well-structured with 8 clearly delineated analysis sections.

**Statistical methods**:
- Fisher exact tests with BH-FDR correction (NB03 cell 10) are appropriate for the 6 condition-class comparisons. The multiple testing correction is a strength.
- Logistic regression with 10-fold cross-validated AUC (NB03 cell 18) is properly implemented using `sklearn.model_selection.cross_val_score`. Both in-sample and CV-AUC are reported, and the CV results confirm the weak signal (0.517-0.548) is not an artifact of overfitting.
- Spearman correlation (NB04 cell 10) is appropriate for the module-level analysis given the non-normal distribution of core fractions.
- The threshold sensitivity analysis (NB03 cell following cell 23) strengthens the results by showing the pattern holds across thresholds from -1 to -3.

**Condition classification (NB02)**: The rule-based system is carefully ordered (e.g., "persulfate" and "zinc sulfate" before "sulfate") with comments explaining why. The "heavy-metals" → "field" broad classification is debatable for some metals (aluminum, rubidium) but is discussed in the REPORT interpretation section.

**Pitfall awareness**:
- `fillna(False).astype(bool)` pattern correctly used in NB03 cell 4 and NB04 cell 5, per `docs/pitfalls.md`.
- String-to-boolean conversion for TSV columns is explicitly handled in NB03 cell 4.
- Essential gene exclusion from genefitness analyses is acknowledged, per the pitfall "Essential Genes Are Invisible in genefitness-Only Analyses."
- The `.apply()` on 757 rows in NB02 cell 5 is fine — the performance pitfall about row-wise apply only matters for large DataFrames.

**Module classification (NB04)**: The classification in cell 13 uses the mean core fraction (0.886) rather than the median (1.000) as the threshold, which avoids the ceiling effect that would make the "ecological" category empty. This produces a reasonable distribution: 21 ecological, 17 conserved-quiet, 5 field-variable, and 9 lab modules. However, the underlying issue remains that 52 modules with a median core fraction of 1.0 leaves limited dynamic range for correlation analysis (Spearman rho=0.071, p=0.62).

**Minor issues**:
- NB03 cell 8 reports `Auxiliary: 645` while the `gene_info` table has 583 auxiliary genes. The discrepancy (62 genes) is because genes without pangenome links (from the outer merge in cell 4) are counted as non-core in the `gene_data` table. The report summary correctly uses the 645 figure, but a clarifying comment would help.

## Findings Assessment

**Conclusions supported by data**: Yes, thoroughly. The REPORT accurately represents the statistical results. H1 is honestly reported as "partially supported" — field-stress enrichment is significant (q=0.026) but the field-specific vs lab-specific comparison is not (p=0.27, n=50-52 per group). The key insight that fitness magnitude matters more than condition type is well-supported by the logistic regression results (gene length AUC=0.645 vs field/lab fitness AUC=0.517-0.548).

**Limitations acknowledged**: Exceptionally thorough. Eight specific limitations are listed in the REPORT, including the essential gene exclusion, single-organism caveat, coarse core/auxiliary classification, subjective condition mapping, and the correlation between field and lab fitness effects (r~0.7). The gene length confound is explicitly noted.

**Counter-intuitive results honestly reported**: The finding that lab-specific genes are 96% core (vs 88.5% for field-specific) is counter to H1 but is reported prominently. The interpretation that "any fitness importance predicts conservation" is well-reasoned, though the small sample sizes (n=50-52) warrant the caveat about limited statistical power.

**Incomplete analysis**: None. The REPORT's `gene_fitness_conservation.csv` is listed as a data file and exists on disk, but the save step is missing from the notebooks. All other analyses are complete.

**Visualizations**: Six figures are well-labeled with axes, titles, and legends. The bar chart (fig 1) clearly shows conservation gradients with sample sizes. The ROC curves (fig 3) effectively demonstrate weak predictive power. The module scatter plots (figs 5-6) honestly display the null result. Figures are saved at 150 DPI — adequate for screen use.

**Literature context**: Strong. Eight references are cited in the REPORT with specific connections to findings (e.g., Rosconi et al. 2022 linked to the magnitude-over-context conclusion; Huang et al. 2022 linked to accessory genome metal resistance). The `references.md` file lists 12 references with full bibliographic details and PubMed search queries, enabling others to reproduce the literature search.

## Suggestions

1. **Add `statsmodels` to `requirements.txt`** (Critical): NB03 imports `from statsmodels.stats.multitest import multipletests` but `statsmodels` is not listed in `requirements.txt`. Add `statsmodels>=0.13` to avoid a `ModuleNotFoundError` on fresh installs.

2. **Add the missing save step for `gene_fitness_conservation.csv`** (Important): The file exists on disk and is listed in the REPORT, but no notebook cell writes it. Add a cell at the end of NB03's section 6 or 7 to save `gene_data` to `data/gene_fitness_conservation.csv`. This ensures full reproducibility via `nbconvert --execute`.

3. **Add NB01 code cell outputs or a summary data file** (Moderate): NB01 code cells lack saved outputs since it requires Spark, which is expected. The markdown header has an execution summary, but saving a small summary file (e.g., `data/enigma_summary.json` with table names and row counts) would let downstream notebooks or readers verify the discovery results without Spark access.

4. **Consider a quantitative conservation metric** (Moderate): The binary core/auxiliary classification creates a high baseline (76.3% core) and a ceiling effect at the module level (median 1.0). Using the fraction of genomes carrying each gene cluster as a continuous variable would increase statistical power, as noted in the REPORT's Future Directions. This is the single change most likely to strengthen the results if the pangenome data supports it.

5. **Clarify the auxiliary gene count discrepancy** (Minor): NB03 cell 8 reports 645 auxiliary genes, while cell 4 shows 583 in the `gene_info` table. A brief comment explaining that the difference comes from genes without pangenome links being counted as non-core after the inner merge would prevent confusion.

6. **Consider showing ROC curves with CV-AUC values** (Minor): NB03 cell 19 plots ROC curves using in-sample probabilities but the legend labels show the in-sample AUC values (e.g., "Field-only (AUC=0.516)"). Since 10-fold CV-AUC values are computed in cell 18, updating the legend to show CV-AUC (e.g., "Field-only (CV-AUC=0.517)") would be more rigorous, though the difference is negligible here.

7. **Document the heavy-metals broad classification rationale earlier** (Minor): The README and RESEARCH_PLAN classify heavy-metals as "field" without explanation. The REPORT discusses this in the Interpretation section, but adding a one-line note in NB02's markdown header or classification scheme table would make the rationale visible at the point of decision.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-15
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 4 notebooks, 3 data files, 6 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
