# Review: Metal-Specific vs General Stress Genes (Revision 2)

**Reviewer**: Automated BERIL Reviewer
**Date**: 2026-02-28
**Verdict**: ACCEPT WITH REVISIONS

## Summary

This project classifies 7,609 metal-important genes across 24 organisms as metal-specific (55%), metal+stress (7%), or general sick (38%) based on fitness profiles across 5,945 non-metal experiments, then tests whether metal-specific genes show distinct conservation and functional enrichment patterns. All critical issues from the prior review have been resolved: the CMH p-value now correctly reads 0.011 (matching NB03 cell 9 output), the Fisher exact tests use distinct variables and report correct values, DvH is included, and the novel candidate table is complete. Only minor issues remain.

## Prior Issues Status

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Numerical discrepancies between REPORT and notebooks | Critical | RESOLVED (Revision 1) |
| 2 | CMH test p-value mismatch (REPORT said p=0.11, notebook showed p=0.011) | Critical | RESOLVED. REPORT now correctly states p=0.011 and interprets the result as statistically significant. NB03 cell 9 confirms: CMH chi-squared=6.42, p=1.13e-02. |
| 3 | Missing DvH and other organisms | Critical | RESOLVED (Revision 1) |
| 4 | Fisher exact OR misattribution in NB04 (variable overwrite) | Critical | RESOLVED (Revision 1). NB04 cell 15 uses distinct `h1c_or`/`h1c_p` and `h1d_or`/`h1d_p` variables. |
| 5 | ICA module analysis failed | Important | UNCHANGED. Still reports "No metal-responsive modules found." Now documented as a limitation in REPORT Finding 6 with methodological explanation. Acceptable as documented limitation. |
| 6 | Cross-validation against counter_ion_effects is weak | Important | UNCHANGED. 2.7x discrepancy documented in Finding 7 with methodological explanation. Threshold replication listed as Future Direction #4. Acceptable. |
| 7 | Per-metal specificity table incomplete | Important | RESOLVED (Revision 1) |
| 8 | Gene record count discrepancy | Important | RESOLVED (Revision 1) |
| 9 | DUF1043/YhcB and DUF39 missing from candidate table | Important | RESOLVED (Revision 1) |
| 10 | `specificphenotype` validation not performed | Minor | ACKNOWLEDGED. Listed as Future Direction #2. |
| 11 | `statsmodels` in requirements.txt but never imported | Minor | NOT FIXED. `requirements.txt` still lists `statsmodels>=0.14` but no notebook imports it. |
| 12 | Hardcoded absolute paths | Minor | NOT FIXED. All notebooks still use `MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'`. |
| 13 | Per-organism scatter plot pattern not discussed | Minor | PARTIALLY ADDRESSED. The CMH test result (now correctly reported as significant, p=0.011) provides the statistical summary of this pattern, but the scatter plot in NB03 cell 11 panel 3 is not discussed in the REPORT text. |
| 14 | YebC mechanism not explained | Minor | NOT FIXED. No hypothesis linking proline-rich protein translation to metal-specific tolerance. |

## Remaining Issues

### Critical

None. All critical issues from the prior review have been resolved. The CMH p-value (0.011), Fisher exact H1c (OR=1.64, p=2.4e-8), and Fisher exact H1d (OR=0.60, p=0.003) in the REPORT all match the corresponding notebook outputs exactly.

### Important

1. **Pooled core fractions not reported alongside organism-means.** The REPORT exclusively reports organism-mean core fractions (88.0%, 93.6%, 90.2%, 81.1% baseline). The pooled values from NB03 cell 5 (metal-specific 84.8%, metal+stress 94.3%, general-sick 90.2%, baseline 79.8%) provide a complementary view. The pooled metal-specific core fraction (84.8%) is notably lower than the organism-mean (88.0%), and reporting both would strengthen transparency. This was flagged in the prior review (Important #2) and has not been addressed.

2. **ICA module analysis remains a gap.** The module analysis was a planned deliverable (RESEARCH_PLAN.md Notebook 4, bullet 5) with an expected output file (`data/module_metal_specificity.csv`) that was never generated. The failure is well-documented in the REPORT (Finding 6), the methodological explanation is sound, and the fix is identified (use pre-computed z-scores from Metal Atlas NB05). This is acceptable as a documented limitation but leaves a gap in the threshold-independent validation of specificity classifications.

### Minor

3. **`statsmodels>=0.14` in requirements.txt but never imported.** No notebook uses statsmodels. Remove to avoid unnecessary dependency installation.

4. **Hardcoded absolute paths.** All four notebooks set `MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'`. The README reproduction instructions do not mention this path dependency. Either add a note to the README or refactor to use a relative path or environment variable.

5. **YebC metal-specificity mechanism unexplained.** YebC is highlighted as the second-strongest novel candidate (58% metal-specific, 11 organisms, 6 metals) and the REPORT cites Ignatov et al. 2025 describing it as a translation factor for proline-rich proteins. A brief hypothesis connecting this function to metal-specific tolerance (e.g., metal-induced ribosome stalling on proline-rich sequences, or metal-dependent misfolding of proline-rich proteins) would strengthen the candidate discussion.

6. **Novel candidate table header says "64%" for YebC in README but REPORT shows 58%.** The README Status line states "YebC is the most metal-specific novel candidate (64%)" but the REPORT Finding 4 table and NB04 cell 10 both show YebC at 7/12 = 58%. The README should be corrected to match.

## Scientific Assessment

The analysis is scientifically sound and the central findings are well-supported. The key result -- that 55% of metal-important genes are metal-specific yet remain 88% core-enriched -- definitively answers the research question and confirms the Metal Atlas's core genome robustness model. The CMH test (p=0.011) now provides statistical support for a modest but real difference in core enrichment between metal-specific (88.0%) and general-sick (90.2%) genes, adding nuance to the conclusion: metal-specific genes are significantly less core-enriched than general stress genes, but still overwhelmingly core. The functional enrichment (H1c: OR=1.64, p=2.4e-8) convincingly validates the specificity classification as biologically meaningful. The surprising H1d result (novel candidates are less metal-specific, OR=0.60, p=0.003) is appropriately attributed to experiment-count bias in deeply-profiled organisms. The threshold sensitivity analysis (1-20% sick rate) demonstrates classification robustness. The candidate prioritization -- elevating UCP030820, YebC, and DUF1043 while deprioritizing YfdZ and Mla/Yrb -- provides actionable guidance for follow-up experiments. The essential gene bias caveat is appropriately noted throughout.

## Reproducibility

The project meets BERIL reproducibility standards. All four notebooks are committed with saved outputs, and the numerical claims in the REPORT match the notebook outputs verified during this review (CMH p=0.011 in NB03 cell 9; H1c OR=1.64, p=2.4e-8 in NB04 cell 7; H1d OR=0.60, p=0.003 in NB04 cell 9). Five generated data files and five figures are present. The README provides step-by-step reproduction instructions. The main reproducibility gap is the hardcoded absolute path (`/home/psdehal/pangenome_science/BERIL-research-observatory`) in all notebooks, which requires modification by anyone reproducing the analysis on a different machine. The `requirements.txt` includes an unused dependency (`statsmodels`). Cross-project data dependencies are documented in the RESEARCH_PLAN.md. The `data/module_metal_specificity.csv` file listed in the RESEARCH_PLAN.md expected outputs was not generated due to the ICA module analysis failure, which is documented. No expected runtime is provided in the README.
