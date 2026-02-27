# Review: Metal-Specific vs General Stress Genes (Revision 1)

**Reviewer**: Automated BERIL Reviewer
**Date**: 2026-02-27
**Verdict**: ACCEPT WITH REVISIONS

## Summary

This project classifies 7,609 metal-important genes across 24 organisms as metal-specific (55%), metal+stress (7%), or general sick (38%) based on their fitness profiles across 5,945 non-metal experiments, then tests whether metal-specific genes show distinct conservation patterns. The revision successfully addresses most critical issues from the prior review -- DvH is now included, the per-metal table is complete with all 14 metals, the novel candidate table is filled in, and the NB04 summary cell variable overwrite is fixed. However, a new numerical discrepancy has been introduced in the CMH test result, and several minor issues remain.

## Prior Issues Addressed

### Critical Issues

1. **Numerical discrepancies between REPORT and notebooks (Prior Critical 1)**: FIXED. The REPORT table now explicitly labels values as "Organism-Mean Core Fraction" and the text in Finding 2 opens with "**Organism-mean** core fractions across the 22 organisms." This eliminates the ambiguity between pooled and organism-weighted statistics. The pooled values (84.8%, 94.3%, 90.2%, 79.8% from NB03 cell 5) are not reported alongside the organism means (88.0%, 93.6%, 90.2%, 81.1% from cell 7), which is acceptable since the labeling is now clear, though reporting both would strengthen the analysis.

2. **CMH test mischaracterized as significant (Prior Critical 2)**: PARTIALLY FIXED, BUT NEW ERROR INTRODUCED. The prior review flagged that the REPORT claimed the CMH test was statistically significant when the notebook showed p=0.110. The authors corrected the REPORT text to say "does not reach statistical significance (p=0.11)." However, the underlying data has changed because DvH was added to the analysis (fixing Prior Critical 3). NB03 cell 9 now outputs CMH chi-squared = 6.42, p = 1.13e-02, which IS statistically significant at p < 0.05. The REPORT still states p=0.11 and concludes non-significance. The authors appear to have copied the reviewer's correction language without checking the updated notebook output. The REPORT's CMH p-value and its interpretation must be updated to reflect the current notebook results (p=0.011, significant). See Critical Issue 1 below.

3. **Missing DvH and other organisms (Prior Critical 3)**: FIXED. NB02 cell 6 now successfully processes DvH (495 genes, 608 non-metal experiments, median sick rate 0.016) along with 23 other organisms, for a total of 24 organisms and 7,609 gene records (up from 22 organisms and 6,838 records). The REPORT correctly documents that 7 organisms remain excluded due to locusId format mismatches (ANA3, Dino, Keio, MR1, Miya, PV4, SB2B) and lists them by name.

4. **Fisher exact OR misattribution in NB04 cell 15 (Prior Critical 4)**: FIXED. NB04 cell 15 now uses distinct variable names (`h1c_or`/`h1c_p` and `h1d_or`/`h1d_p`) and correctly prints both H1c (OR=1.64, p=2.40e-08) and H1d (OR=0.60, p=0.003) without variable overwriting.

### Important Issues

5. **ICA module analysis failed (Prior Important 5)**: NOT FIXED. NB04 cell 13 still reports "No metal-responsive modules found." The right panel of `functional_comparison.png` still displays "No module data." The `data/module_metal_specificity.csv` file is still not generated. However, the REPORT now clearly documents this failure in Finding 6, explains the methodological reason (z-normalization produces max |z| < 2.0 for metal experiments), and identifies the fix (use pre-computed z-scores from Metal Atlas NB05). This is appropriately handled as a documented limitation rather than a silent failure.

6. **Cross-validation against counter_ion_effects is weak (Prior Important 6)**: PARTIALLY ADDRESSED. The discrepancy is now 13.7% vs 39.8% (2.9x, slightly wider than the prior 14.7% vs 39.8%). The REPORT's Finding 7 now documents this discrepancy with a clear explanation of the methodological differences (stricter threshold, partial organism set overlap). However, the suggestion to replicate the counter_ion_effects threshold (fit < -1 without |t| > 4) was not implemented. Listed as a Future Direction (#4), which is acceptable.

7. **Per-metal specificity table incomplete (Prior Important 7)**: FIXED. The REPORT now shows all 14 metals with data, including essential metals: Manganese (60.6%), Molybdenum (60.5%), Tungsten (56.5%), Selenium (46.4%), and Iron (21.9%). The prior claim of "0% specificity" for essential metals is removed. The inclusion of DvH resolved this issue, as DvH contributes data for Mo, W, Se, and Mn.

8. **Gene record count discrepancy (Prior Important 8)**: FIXED. The REPORT now correctly states 7,609 gene records (not 6,838) and explicitly documents the 59.3% coverage (7,609 of 12,838), the 7 excluded organisms, and notes that the exclusion is not expected to introduce systematic bias.

9. **DUF1043/YhcB and DUF39 missing from candidate table (Prior Important 9)**: FIXED. The REPORT's Finding 4 table now includes full data for all 9 candidates: DUF1043/YhcB (3/6, 50%, mean sick rate 0.054) and DUF39 (0/2, 0%, sick rate 0.637). The table is complete with no missing entries.

### Minor Issues

10. **`specificphenotype` validation not performed (Prior Minor 10)**: ACKNOWLEDGED. Still not performed. Now listed in the REPORT Limitations section and as Future Direction #2. Acceptable.

11. **`statsmodels` in requirements.txt but never imported (Prior Minor 11)**: NOT FIXED. The `requirements.txt` still lists `statsmodels>=0.14` but no notebook imports it. Minor packaging issue.

12. **Hardcoded absolute paths (Prior Minor 12)**: NOT FIXED. All notebooks still use `MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'`. The README reproduction instructions do not mention this path dependency.

13. **Per-organism scatter plot pattern not discussed (Prior Minor 13)**: PARTIALLY ADDRESSED. The REPORT does not directly discuss the scatter plot pattern, but the CMH test result (which now shows significance) would be the appropriate place to discuss the systematic trend of general-sick genes being more core-enriched than metal-specific genes per organism.

14. **YebC mechanism not explained (Prior Minor 14)**: NOT FIXED. The REPORT still cites Ignatov et al. 2025 describing YebC as a translation factor for proline-rich proteins, but does not explain why this function would confer metal-specific tolerance. The connection between proline-rich protein translation and metal stress remains unexplored.

## Remaining Issues

### Critical

1. **CMH test p-value in REPORT contradicts notebook output.** The REPORT states "The Cochran-Mantel-Haenszel test comparing metal-specific vs general-sick core enrichment across organisms does not reach statistical significance (p=0.11)" (Finding 2 and the Results table showing "0.11 (ns)"). However, NB03 cell 9 now outputs CMH chi-squared = 6.42, p = 1.13e-02. This is statistically significant at p < 0.05. The discrepancy arose because the authors added DvH to the analysis (fixing Prior Critical 3), which changed the CMH result from non-significant (p=0.110 with 22 organisms) to significant (p=0.011 with 22 organisms including DvH). The REPORT text and table must be updated to report the correct p-value (0.011) and revised interpretation. Notably, this result now provides statistical support for the trend that metal-specific genes are less core-enriched than general-sick genes -- strengthening the paper's narrative. The Interpretation section's statement "The CMH test does not reach significance (p=0.11)" should be revised accordingly.

### Important

2. **Pooled core fractions not reported.** While the organism-mean values are now clearly labeled, the pooled core fractions (NB03 cell 5: metal-specific 84.8%, metal+stress 94.3%, general-sick 90.2%, baseline 79.8%) should also be reported, as they represent a complementary statistical summary. The pooled metal-specific core fraction (84.8%) is notably lower than the organism-mean (88.0%), and the +5.0% pooled delta vs +6.9% organism-mean delta provides important context about how organism weighting affects the conclusion. A table or parenthetical note reporting both would strengthen the transparency of the analysis.

3. **ICA module analysis remains unresolved.** While now properly documented as a limitation, the module analysis was a planned component of the research (RESEARCH_PLAN.md, Notebook 4, bullet 5) with an expected output file (`data/module_metal_specificity.csv`). The REPORT identifies the fix (use pre-computed z-scores from Metal Atlas NB05) but does not implement it. This leaves a gap in the analysis: the module-level view would provide a threshold-independent complement to the per-gene specificity classification. This should either be fixed or the RESEARCH_PLAN.md should be updated to mark it as deferred.

### Minor

4. **`statsmodels` listed in requirements.txt but never used.** Remove from requirements.txt to avoid unnecessary dependency installation.

5. **Hardcoded absolute paths.** All four notebooks use `MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'`. The README should note this path dependency, or the notebooks should use a relative path or environment variable.

6. **YebC metal-specificity mechanism.** The REPORT highlights YebC as the second-strongest novel candidate (58% metal-specific across 11 organisms and 6 metals) and cites Ignatov et al. 2025 describing it as a translation factor for proline-rich proteins. A brief sentence hypothesizing why this function might confer metal-specific tolerance (e.g., metal-induced ribosome stalling on proline-rich sequences, or metal-dependent misfolding of proline-rich proteins) would strengthen the candidate discussion.

7. **Counter-ion cross-validation threshold replication.** The 2.9x discrepancy between this analysis (13.7% osmotic overlap) and the counter_ion_effects project (39.8%) is documented but not resolved. The Future Directions suggest matching the threshold, which is appropriate, but a brief sensitivity test using fit < -1 without |t| > 4 for osmotic experiments only could be added to NB02 to quantify how much of the gap is threshold-driven vs organism-set-driven.

## Scientific Assessment

The central scientific finding is robust and important: 55% of metal-important genes are metal-specific (sick under metals but not other stresses), yet these metal-specific genes remain core-enriched (88% organism-mean, 85% pooled) rather than showing the expected accessory-genome enrichment. This definitively rules out the hypothesis that the Metal Atlas's 87.4% core enrichment was inflated by pleiotropic general-stress genes. The functional enrichment analysis (H1c: OR=1.64, p=2.4e-8) convincingly demonstrates that the specificity classification captures biologically meaningful categories. The inclusion of DvH in this revision substantially strengthens the analysis, adding 495 genes and providing coverage for essential metals (Mo, W, Se, Mn) that were previously absent. The CMH test, which now reaches significance (p=0.011 in NB03, though the REPORT incorrectly states p=0.11), provides statistical support for a modest but real difference in core enrichment between metal-specific (88.0%) and general-sick (90.2%) genes. The H1d result -- that novel candidates are LESS metal-specific than annotated ones (OR=0.60, p=0.003) -- is a genuine surprise that is appropriately attributed to experiment-count bias in deeply-profiled organisms. Overall, the analysis supports a revised model where both general stress response and specialized metal resistance are core genome functions, with metal-specific genes being slightly but significantly less core-enriched.

## Reproducibility

The project meets BERIL reproducibility standards with minor gaps. All four notebooks (`01_experiment_classification.ipynb`, `02_gene_specificity.ipynb`, `03_conservation_analysis.ipynb`, `04_functional_enrichment.ipynb`) are committed with saved outputs, and the five generated data files (`data/experiment_classification.csv`, `data/gene_specificity_classification.csv`, `data/metal_genes_with_specificity.csv`, `data/specificity_conservation.csv`, `data/og_specificity.csv`) and five figures are present. The README provides step-by-step reproduction instructions. The `requirements.txt` lists dependencies, though `statsmodels>=0.14` is unused. The main reproducibility concern is the hardcoded absolute path (`/home/psdehal/pangenome_science/BERIL-research-observatory`) in all notebooks, which prevents execution by anyone without modifying the path. The cross-project data dependencies (metal_fitness_atlas, fitness_modules, conservation_vs_fitness, essential_genome) are documented in the RESEARCH_PLAN.md. No expected runtime is provided in the README. The `data/module_metal_specificity.csv` file listed in the RESEARCH_PLAN.md expected outputs was never generated due to the failed ICA module analysis.
