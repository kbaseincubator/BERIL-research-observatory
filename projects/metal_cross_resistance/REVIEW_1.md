---
reviewer: BERIL Automated Review (Codex, gpt-5.4)
date: 2026-04-27
project: metal_cross_resistance
---

# Review: Gene-Resolution Metal Cross-Resistance Across Diverse Bacteria

## Summary
This is a strong, well-documented analysis project with a clear research question, a sensible notebook progression, saved notebook outputs, substantial generated data, and figures that cover the main result areas. H1 and H2 are generally well supported by the materials provided. The main weakness is the H3 validation workflow: the BacDive comparison mixes in organisms that were never scored for cross-resistance, reuses the same species-level BacDive evidence across multiple FB strains, and relies on broad string matching, so the reported null result should be treated as provisional rather than a clean test.

## Methodology
The project states a testable question in [README.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/README.md:3) and expands it into explicit hypotheses in [RESEARCH_PLAN.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/RESEARCH_PLAN.md:3). The overall workflow is logical: NB01 extracts per-organism metal fitness matrices, NB02-NB03 test conservation, NB04 classifies gene tiers, and NB05 attempts validation. Reproducibility is better than average for this repository: the README has a real `## Reproduction` section with Spark/local separation, `requirements.txt` is present, all five notebooks have saved outputs, and the project ships 73 data files plus 11 figures. The main reproducibility gap is not missing artifacts but method drift: the implemented H2 and H3 procedures do not fully match the plan/write-up, which makes it harder for a reader to know which definition should be trusted.

## Code Quality
Notebook organization is good overall, and the implementation reflects several known BERDL pitfalls correctly, especially casting Fitness Browser string fields to numeric in NB01 and NB04. I found four concrete issues.

First, the H3 validation cohort is inconsistent. NB05 cell 6 iterates over every organism in `extraction_summary.csv`, but NB04 only classifies organisms with `n_metals >= 3`, so `azobra` and `BFirm` enter `data/bacdive_metal_environment.csv` with zero-valued scores even though they were never analyzed for cross-resistance tiers. This directly affects the headline `n = 26` null result reported in [REPORT.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/REPORT.md:82). Excluding those two rows changes the shared-fraction correlation from rho = -0.02 to rho = -0.17, so the conclusion remains null but the reported statistic is not based on a consistent analysis set. References: `05_pangenome_prediction.ipynb` cells 6, 9, 10; `data/bacdive_metal_environment.csv`.

Second, the BacDive validation is not independent at the FB-strain level. In `05_pangenome_prediction.ipynb` cell 9, matching is done at genus/species string level, then several distinct FB strains inherit the same BacDive species pool. In the saved output, the five `Pseudomonas fluorescens` strains (`pseudo1_N1B4`, `pseudo3_N2E3`, `pseudo5_N2C3_1`, `pseudo6_N2E2`, `pseudo13_GW456_L13`) all receive identical `n_bacdive_strains`, `n_metal_env`, and `pct_metal_env` values. That duplicates the same environmental evidence across multiple rows and weakens the statistical interpretation of the H3 test. References: `05_pangenome_prediction.ipynb` cells 8-10; `data/bacdive_metal_environment.csv`.

Third, the implemented definition of `general_stress` does not match the research plan. The plan defines it as important in at least 50% of all conditions, metal plus non-metal, but `04_shared_vs_specific_genes.ipynb` cell 4 classifies it solely by `sick_rate_nonmetal >= 0.50`. That may be a reasonable operational definition, but it is a different one, and it affects the H2 tier counts and enrichment claims in [REPORT.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/REPORT.md:54). References: [RESEARCH_PLAN.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/RESEARCH_PLAN.md:149), `04_shared_vs_specific_genes.ipynb` cell 4.

Fourth, NB03 contains a plotting bug in the `consensus_vs_individual` figure logic. In cell 8, the condition `if pair_key in consensus.index` can never be true because `consensus.index` contains metal names, not pair names, so the pooled scatter data are not assembled as intended. This does not invalidate the LOO table saved in `data/loo_consensus_prediction.csv`, but it does weaken one of the supporting visualizations listed in [REPORT.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/REPORT.md:198). Reference: `03_cross_resistance_conservation.ipynb` cell 8.

## Findings Assessment
The core H1 conclusion is supported by the saved outputs: the cross-resistance matrices, pairwise summaries, Mantel results, and leave-one-out table all point in the same qualitative direction. H2 is also reasonably supported, but the reader should be told more explicitly that the implemented tier definition differs from the plan. H3 is the weakest part: the report appropriately calls it inconclusive, but the exact null statistic should not be overinterpreted because the validation table mixes unmatched cohort definitions and duplicated species-level metadata. The visual coverage is strong overall, with 11 figures across the major stages, but documentation consistency needs work: [README.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/README.md:10) and [README.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/README.md:17) still describe 30 organisms, 422 experiments, and 13 metals, while [REPORT.md](/home/psdehal/BERIL-research-observatory/projects/metal_cross_resistance/REPORT.md:92) reports 452 experiments and 14 metals.

## Suggestions
1. Critical: Rebuild the H3 validation table using only organisms that actually received cross-resistance/tier scores, and update the reported `n` and correlation statistics accordingly.
2. Critical: Avoid treating multiple FB strains from the same species as independent BacDive validations when they share the same species-level BacDive pool; collapse to species level or use strain-resolved matching if available.
3. Important: Harmonize the `general_stress` definition across `RESEARCH_PLAN.md`, NB04, and `REPORT.md`, or explicitly justify the implemented non-metal-only rule and restate H2 using that definition.
4. Important: Fix the NB03 cell-8 scatterplot logic so `figures/consensus_vs_individual.png` actually visualizes the pooled consensus-versus-observed comparison.
5. Nice-to-have: Reconcile the project summary numbers across README and REPORT so experiment counts, metal counts, and analyzed-organism counts are consistent everywhere.

## Review Metadata
- **Reviewer**: BERIL Automated Review (Codex, gpt-5.4)
- **Date**: 2026-04-27
- **Scope**: README.md, 5 notebooks, 73 data files, 11 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
