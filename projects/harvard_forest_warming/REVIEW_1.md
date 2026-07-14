---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
date: 2026-05-07
project: harvard_forest_warming
---

# Review: Harvard Forest Long-Term Warming — DNA vs RNA Functional Response

## Summary

This project presents a rigorous and well-executed comparative analysis of DNA versus RNA functional responses to 25-year soil warming at the Harvard Forest Barre Woods site. The work successfully demonstrates that DNA and RNA functional pools respond comparably to warming (~10-13% R²), contrary to the original hypothesis that transcript pools would be more sensitive. The project reproduces known compositional signals (Actinobacteria up, Acidobacteria down) and identifies novel RNA-level responses including methanotrophy (pmoA/pmoB) upregulation and glyoxylate cycle activation in heated mineral soils. The analysis is methodologically sound, well-documented, and provides meaningful insights into soil microbial responses to chronic warming. The documentation quality is exemplary, with comprehensive research plan, detailed notebooks with saved outputs, thorough literature context, and clear interpretation of findings.

## Methodology

**Strengths:**
- **Clear research question and testable hypotheses**: The three main hypotheses (H1: RNA shifts more than DNA; H2: C-cycling enrichment; H3: horizon-specific responses) are well-formulated and directly testable with available data.
- **Appropriate analytical approach**: Uses PERMANOVA for beta-diversity comparisons, Welch t-tests for per-KO differential abundance, and Fisher's exact tests for categorical enrichment - all well-suited to the data structure and research questions.
- **Data source clarity**: Excellent documentation of NMDC tables used, with specific study ID (`nmdc:sty-11-8ws97026`) and clear exclusion criteria (only `nmdc` tenant, no `nmdc_arkin`).
- **Reproducibility framework**: The 8-notebook pipeline is clearly structured with intermediate data files, making reproduction straightforward. The README provides clear step-by-step reproduction instructions including runtime estimates.
- **Sensitivity analysis**: The H1 sensitivity check in NB05 addressing the horizon × incubation confound demonstrates careful attention to potential artifacts.

**Areas for consideration:**
- **Single timepoint limitation**: The 2017-05-24 sampling date restricts temporal generalizability, though this is acknowledged in limitations.
- **Sample size constraints**: While adequate for community-level analyses, the n=11-14 per group limits statistical power for individual KO detection after FDR correction across 14K KOs.

## Code Quality

**Strengths:**
- **SQL best practices**: Proper filtering by workflow_run_id, correct join keys (using `parent_id` in biosample associations), and awareness of NMDC-specific pitfalls from docs/pitfalls.md.
- **Statistical rigor**: Appropriate use of FDR correction, log-ratio transformations for compositional data, and non-parametric methods (PERMANOVA) for community analysis.
- **Notebook organization**: Each notebook has a clear purpose, logical flow from setup → analysis → visualization → output, and comprehensive markdown documentation.
- **Error handling**: The analysis properly handles edge cases (e.g., samples without both DNA and RNA data) and provides clear diagnostic output.
- **Code quality**: Clean pandas operations, appropriate data transformations, and well-structured figure generation.

**Areas for improvement:**
- The notebooks use hardcoded parameters in some places (e.g., pseudocount values, FDR thresholds) that could be moved to configuration variables for better maintainability.

## Reproducibility

**Excellent:**
- **Notebook outputs**: All 8 notebooks contain saved outputs (ranging from 50-65% of cells with outputs), providing clear examples of expected results without requiring re-execution.
- **Figure coverage**: Strong figure coverage with 9 high-quality figures spanning all major analysis stages from design matrix through synthesis.
- **Reproduction guide**: The README includes a comprehensive reproduction section with prerequisites, step-by-step instructions, runtime estimates (~15-20 min), and clear separation of Spark-dependent vs. local steps.
- **Dependencies**: While no explicit requirements.txt exists, the analysis uses standard scientific Python libraries (pandas, numpy, scipy, matplotlib) that are available in the default JupyterHub kernel.
- **Data lineage**: Clear separation between committed inputs (notebooks, curated KO list) and regenerable outputs (all data/*.tsv* files are gitignored).
- **Intermediate outputs**: Well-structured data pipeline with clear intermediate files that can be reused across notebooks.

## Findings Assessment

**Strengths:**
- **Conclusions well-supported**: All major findings are backed by appropriate statistical tests and effect sizes. The rejection of H1 is supported by careful sensitivity analysis removing confounding factors.
- **Limitations acknowledged**: The report thoroughly discusses single-timepoint constraints, sample size limitations, and potential biases (assembly quality, compositional effects).
- **Novel insights**: The methanotrophy and glyoxylate cycle findings provide new mechanistic insights beyond the expected CAZyme responses.
- **Literature integration**: Excellent contextualization of findings within the broader Harvard Forest warming literature, with specific comparison to relevant studies (DeAngelis et al. 2015, Roy Chowdhury et al. 2021).

**Complete analysis**: No obvious gaps or incomplete sections. The bonus metabolite analysis adds valuable additional perspective.

## Suggestions

### High Priority
1. **Add explicit dependency documentation**: Create a `requirements.txt` or `environment.yml` file listing specific versions of key packages (pandas, numpy, scipy, matplotlib) to ensure long-term reproducibility.

2. **Expand H1 discussion**: The rejection of H1 (RNA not more sensitive than DNA) contradicts initial expectations and some literature. Consider adding a brief discussion of why this might occur after 25 years of warming (e.g., community adaptation, regulatory vs. compositional timescales).

### Medium Priority
3. **Quantify effect sizes for top hits**: For the significant methanotrophy (pmoA/pmoB) and glyoxylate cycle findings, consider reporting Cohen's d or similar effect size measures alongside p-values to better communicate biological significance.

4. **Cross-reference with soil chemistry**: While `abiotic_features` is noted to be all zeros, consider whether other NMDC studies at Harvard Forest have usable soil chemistry data that could provide environmental context for the functional responses.

### Low Priority (Nice-to-haves)
5. **Interactive figure development**: Consider providing code for interactive versions of key figures (e.g., volcano plots with hover information for KO identification).

6. **MAG-level analysis**: As suggested in future directions, linking the pmoA/pmoB signals to specific MAGs would strengthen the mechanistic interpretation.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
- **Date**: 2026-05-07
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 8 notebooks, 15 data files, 9 figures, references.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.