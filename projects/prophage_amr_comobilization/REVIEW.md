---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
date: 2026-05-01
project: prophage_amr_comobilization
---

# Review: Prophage-AMR Co-mobilization Atlas

## Summary

This is an exemplary pangenome-scale study investigating the relationship between prophage markers and antibiotic resistance genes across 293K genomes and 27K species. The project successfully demonstrates that prophage density is a strong species-level predictor of AMR repertoire breadth (H2), while gene-level co-localization shows more modest effects (H1). The methodology is sound, the statistical analyses are appropriate, and the findings are well-supported by comprehensive data analysis. The work makes a novel contribution to understanding AMR mobilization mechanisms at unprecedented scale. The main limitation is the use of Python scripts instead of Jupyter notebooks, which reduces immediate reproducibility for readers.

## Methodology

The research approach is scientifically rigorous with clearly stated, testable hypotheses. The use of BERDL databases is appropriate, with thoughtful handling of the limitation that genomad_mobile_elements is not available (addressed through keyword + Pfam-domain prophage detection). The statistical methods are well-chosen: Fisher's exact test for H1, Spearman correlation and regression for H2, with proper controls for confounders like genome size and phylogeny.

Data sources are clearly identified and the sampling strategy (top-100 species, 20 genomes per species) balances computational feasibility with representativeness. The threshold sensitivity analysis (3-50 genes) for proximity definition shows methodological sophistication. The authors appropriately acknowledge when H3 could not be tested due to limited fitness data overlap.

## Code Quality

The SQL queries are well-structured and appropriate for the BERDL database schema. The Python code demonstrates good practices with clear documentation, proper error handling for different Spark session contexts, and logical organization. Statistical analyses use appropriate libraries (scipy.stats, statsmodels) and methods.

The code appropriately handles known BERDL pitfalls, such as using species-level filtering for large tables and avoiding `.toPandas()` on large intermediate results. The prophage detection strategy using both bakta_annotations keywords and bakta_pfam_domains is well-implemented with comprehensive pattern matching.

However, there is one significant code organization issue: all notebooks are in Python script format (.py) rather than Jupyter notebook format (.ipynb). While the scripts are well-documented and functional, this means readers cannot see cell-by-cell outputs and must re-run the entire analysis to examine intermediate results.

## Findings Assessment

The conclusions are strongly supported by the presented data. The H2 finding (prophage density predicts AMR breadth: Spearman rho=0.572, R²=0.30) is robust and consistent across phylogenetic groups. The H1 result is more nuanced but appropriately interpreted - the modest overall effect (OR=1.10) combined with threshold dependence and species heterogeneity suggests a complex relationship rather than a simple linear association.

The literature context is excellent, positioning findings relative to Rendueles et al. (2018) and Chen et al. (2018), while acknowledging mechanistic support from Bearson & Brunelle (2015) and Fisarova et al. (2021). The authors appropriately distinguish correlation from causation and acknowledge limitations around prophage detection methods and gene position proxies.

Visualizations are comprehensive and well-designed, with 8 figures covering the full analysis pipeline from census through hypothesis testing to synthesis. All key results are supported by both tabular data and graphical presentation.

## Suggestions

1. **Convert to Jupyter notebook format**: The most important improvement would be converting the .py scripts to .ipynb format with saved outputs. This would allow readers to see intermediate results, figures, and data summaries without re-running the computationally intensive Spark queries.

2. **Add notebook runtime documentation**: Include expected execution times for each notebook in the README reproduction section, noting which require Spark access vs local execution.

3. **Expand H3 analysis**: Consider testing fitness effects in the subset of organisms where pangenome and fitness data overlap, even if limited. This could provide preliminary insights for the fitness hypothesis.

4. **Add prophage detection validation**: Compare keyword/Pfam results against a subset analyzed with dedicated prophage prediction tools (PHASTER, geNomad) to estimate false positive/negative rates.

5. **Base-pair resolution analysis**: For a high-priority subset of species, re-analyze using actual genomic coordinates from scaffold sequences rather than ordinal gene positions.

6. **Document sampling representativeness**: Add analysis comparing the top-100 species sample to the full species set on key properties (genome size, AMR burden, taxonomy) to demonstrate representativeness.

## Review Metadata
- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
- **Date**: 2026-05-01
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks, 10 data files, 8 figures, references.md, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.