---
reviewer: BERIL Automated Review
date: 2026-02-14
project: fitness_effects_conservation
---

# Review: Fitness Effects vs Conservation — Quantitative Analysis

## Summary

This is a well-executed quantitative analysis that extends the companion project's binary essential/non-essential framing into a continuous fitness spectrum, asking whether genes with stronger or broader fitness effects are more conserved in the pangenome. The project demonstrates strong scientific reasoning, clean notebook organization, and thoughtful inclusion of essential genes as the extreme fitness category. The key finding — a 16-percentage-point gradient from 82% core (essential) to 66% core (always neutral) across 194,000 genes — is clearly supported by the data. Several counter-intuitive findings (core genes are more likely to be burden genes; condition-specific genes are more core, not more accessory) are honestly reported and thoughtfully interpreted. The main areas for improvement are minor: the README numbers for some categories show small discrepancies with notebook outputs, the `t`-statistic from the `genefitness` table is not used for quality filtering, and a `requirements.txt` exists but lacks version pinning for reproducibility.

## Methodology

**Research question**: Clearly stated and testable — the project asks whether the fitness-conservation relationship is a continuous gradient (not just binary), and tests this from multiple angles (magnitude, breadth, condition type, novel gene landscape, ephemeral niche genes). The multi-faceted approach is a strength.

**Essential gene inclusion**: The decision to include essential genes (no viable transposon mutants) as the most extreme fitness category is well-justified and explicitly motivated in the NB02 header. This is a critical design choice — without it, the analysis would miss 14.3% of genes and the strongest signal. The README and notebooks are transparent that this is an upper bound on true essentiality.

**Statistical methods**: Appropriate throughout. Spearman correlation for the ordinal/continuous relationship, Fisher's exact test for 2×2 contingency tables, and odds ratios for effect sizes. The Spearman rho values (−0.092 for min_fit vs is_core; 0.086 for breadth vs is_core) are small but highly significant given the sample size (~140K mapped non-essential genes), and the project does not overclaim their magnitude.

**Data sources**: Clearly identified in the README table. The dependency on the companion project's shared link table (`fb_pangenome_link.tsv`) and essential gene classifications (`essential_genes.tsv`) is explicitly documented.

**Reproducibility**: Strong. The project has:
- A clear three-step reproduction guide (extract → NB02 → NB03) distinguishing Spark vs local steps
- A `requirements.txt` with minimum versions
- A standalone extraction script (`src/extract_fitness_stats.py`) with checkpointing (skips if output exists)
- Notebooks that load from cached TSV files rather than requiring live Spark access
- All 15 code cells across both notebooks have saved outputs (9/9 in NB02, 6/6 in NB03), including 9 figures
- 9 figures in the `figures/` directory covering all major analysis stages

## Code Quality

**SQL queries** (in `src/extract_fitness_stats.py`): Correct and follow BERDL best practices:
- All numeric comparisons use `CAST(fit AS FLOAT)` — correctly addressing the pitfall that all `kescience_fitnessbrowser` columns are strings (documented in `docs/pitfalls.md`)
- Queries filter by `orgId` per iteration, avoiding full-table scans of the 27M-row `genefitness` table
- The join between `genefitness` and `experiment` for condition-type breakdown uses proper key columns (`orgId` + `expName`)

**Extraction script design**: Well-structured with three independent extraction phases, each with checkpointing. The use of `berdl_notebook_utils.setup_spark_session.get_spark_session` for CLI execution is consistent with the documented approach in `docs/pitfalls.md`.

**Notebook organization**: Both notebooks follow a clean structure: setup → analysis sections (A, B, C, D) → summary. Each section has a markdown header, analysis code, and printed results. The summary cells at the end of each notebook provide a quick reference.

**Potential issues**:

1. **No `t`-statistic filtering**: The `genefitness` table includes a `t` column (t-statistic for the fitness score). The extraction script computes fitness thresholds (e.g., `fit < -1`) without filtering on `|t| > 2` or similar quality cutoffs. While not wrong — this is a deliberate choice to include all data — it means low-confidence fitness scores are included in the counts. A brief note justifying this choice would strengthen the methodology.

2. **SQL injection pattern**: The extraction script uses f-string interpolation for `orgId` values (`WHERE orgId = '{orgId}'`). Since these values come from a trusted internal TSV file rather than user input, this is safe in practice, but parameterized queries would be more robust.

3. **Minor README vs notebook discrepancy**: The README states ephemeral niche genes are "3.0% in core" and "1.7% in auxiliary," but the NB02 output shows 2.5% core and 1.5% auxiliary. The notebook output is the authoritative source; the README appears to use slightly different numbers (possibly from an earlier run or from mapped-only denominators).

4. **Conservation classification logic**: In both notebooks, the `is_core` and `is_singleton` boolean comparison uses `== True` rather than `== 1`. Since the link table comes from a pandas merge with boolean-typed columns, this works correctly, but it's worth noting since the upstream pangenome data stores these as integers (0/1) per `docs/pitfalls.md`.

5. **Ephemeral gene definition**: The definition (|mean_fit| < 0.3, min_fit < −2, n_sick ≤ 3) is reasonable but somewhat arbitrary. The thresholds are stated clearly in both the README and the notebook code, which is good practice, but the project doesn't test sensitivity to these thresholds.

## Findings Assessment

**Conclusions supported by data**: Yes. Each major finding in the README has corresponding notebook output:
- The fitness magnitude gradient (essential 82% → neutral 66%) is shown in both the `min_fit_bin` crosstab and the fitness profile analysis
- The breadth-conservation correlation (Spearman rho=0.086) is computed and visualized in NB03
- The burden gene analysis uses Fisher's exact tests with reported odds ratios
- The specific phenotype enrichment (OR=1.78) is directly computed in NB03

**Limitations acknowledged**: Yes, thoroughly. The README's Interpretation section explicitly addresses three counter-intuitive findings rather than glossing over them. The companion project's limitations (essentiality upper bound, pangenome coverage variation, E. coli exclusion) are referenced by dependency.

**Incomplete analysis**: None detected. All six analysis threads listed in the Approach section are carried out in the notebooks.

**Visualizations**: 9 figures covering fitness magnitude, burden genes, fitness distributions, fitness profiles, novel gene landscape, cost-benefit portrait, fitness breadth, condition type, and broad-vs-specific heatmap. All are properly saved to `figures/` and embedded in notebook outputs. Axis labels and titles are clear. The cost-benefit portrait (hexbin 2D density) is a particularly effective visualization.

## Suggestions

1. **Reconcile README numbers with notebook outputs** (minor): The ephemeral gene percentages in the README (3.0% core, 1.7% auxiliary, 1.6% singleton) differ from NB02 output (2.5% core, 1.5% auxiliary, 1.4% singleton). Update the README to match the notebook's authoritative output, or document if the README intentionally uses mapped-only denominators.

2. **Document the t-statistic filtering decision** (minor): Add a brief note in NB02's header markdown or the README explaining why no `t`-statistic quality filter is applied to fitness scores. Even a one-sentence justification ("We include all fitness measurements regardless of t-statistic to maximize coverage; quality filtering by |t| > 2 reduces coverage by X% but does not change the direction of results") would strengthen the methodology.

3. **Test ephemeral gene threshold sensitivity** (nice-to-have): The ephemeral niche gene definition uses three arbitrary thresholds. A brief sensitivity analysis (e.g., varying min_fit threshold from −1.5 to −3) would demonstrate robustness or reveal that the pattern is threshold-dependent.

4. **Add per-organism effect heterogeneity analysis** (nice-to-have): The companion project analyzed per-organism odds ratios with a forest plot. A similar per-organism breakdown for the fitness magnitude gradient would show whether the pattern is universal or driven by a subset of organisms. This would complement the cross-organism Spearman correlations.

5. **Pin exact dependency versions** (minor): The `requirements.txt` specifies minimum versions (`pandas>=1.5`) but not exact versions. For full reproducibility, consider adding a `requirements-frozen.txt` with pinned versions from the analysis environment (e.g., via `pip freeze`).

6. **Add literature references to the README** (nice-to-have): Unlike the companion project, this README has no References section. The findings about burden genes and condition-specific fitness effects could benefit from citations to relevant literature on gene dispensability and trade-off evolution (e.g., Kuo & Ochman 2009 on genome streamlining; Basan et al. 2015 on growth-rate trade-offs).

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-14
- **Scope**: README.md, 2 notebooks (15 code cells total), 1 extraction script, 3 data files (87 MB), 9 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
