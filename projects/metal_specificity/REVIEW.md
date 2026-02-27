# Review: Metal-Specific vs General Stress Genes

**Reviewer**: Automated BERIL Reviewer
**Date**: 2026-02-27
**Verdict**: ACCEPT WITH REVISIONS

## Summary

This project asks whether the surprising 87.4% core-genome enrichment of metal-important genes (from the Metal Fitness Atlas) is an artifact of general stress genes masquerading as metal tolerance genes. Through a well-designed specificity classification pipeline across 22 organisms and 6,504 experiments, it demonstrates that 54% of metal-important genes are metal-specific (sick rate <5% under non-metal conditions), yet these metal-specific genes remain 88% core-enriched -- strengthening the "core genome robustness" model. The analysis is methodologically sound overall but contains several numerical discrepancies between notebook outputs and the REPORT, a failed ICA module analysis, and incomplete validation steps that should be corrected before finalization.

## Strengths

1. **Well-structured hypothesis testing.** The research plan lays out five testable sub-hypotheses (H1a-H1e) with clear expected outcomes for both H0 and H1 scenarios. The project faithfully tests each and honestly reports when the data contradict expectations (H1b rejected, H1d reversed). This is exemplary scientific practice.

2. **Robust sensitivity analysis.** The threshold sensitivity analysis across six sick-rate thresholds (1%-20%) in `02_gene_specificity.ipynb` (cell 9) demonstrates that the qualitative conclusions are stable even though the exact fraction of metal-specific genes ranges from 37% to 75%. The threshold_sensitivity.png figure clearly communicates this.

3. **Thorough pitfall awareness.** The RESEARCH_PLAN.md explicitly documents five known confounders (experiment-count bias, essential gene invisibility, core denominator matching, general sick artifacts, threshold sensitivity) and addresses each with specific methodological choices. This reflects careful integration of lessons from `docs/pitfalls.md` and prior projects.

4. **Clean experiment classification with full cross-validation.** NB01 classifies all 6,504 experiments and achieves exact 559/559 agreement with the Metal Atlas metal experiment set (cell 7), providing confidence in the upstream classification.

5. **Surprising null result handled well.** The finding that metal-specific genes are ALSO core-enriched (88.0%) is a genuine scientific surprise. The REPORT offers three plausible mechanistic explanations (ancient metal stress, essential cofactor dual-function, HGT-into-core) and appropriately revises the two-tier model from the Metal Atlas rather than forcing the data to fit the original hypothesis.

## Issues

### Critical

1. **Numerical discrepancies between REPORT and notebook outputs for conservation analysis.** The REPORT states metal-specific genes are "88.0% core" but NB03 cell 5 computes 84.1% (2551/3034). The REPORT states general sick genes are "89.6% core" but NB03 computes 89.5% (1928/2153). The REPORT states baseline is "81.9%" but NB03 computes 80.5% (68239/84717). The REPORT's numbers (88.0%, 89.6%, 81.9%) appear to come from the per-organism *mean* of core fractions (cell 7), while the notebook's pooled values (84.1%, 89.5%, 80.5%) come from cell 5. These are two different statistical summaries (organism-weighted mean vs pooled count), and the REPORT conflates them. The "Conservation by Specificity" table in REPORT.md reports "Mean Core Fraction" of 88.0%, which matches the organism-mean, but the text uses these as if they were pooled fractions. The REPORT should clarify which metric is being used and report both, since the pooled metal-specific core fraction (84.1%) is notably lower than the organism-mean (88.0%) and closer to the baseline, weakening the claimed +6.1% delta.

2. **CMH test does not support the REPORT's claim.** The REPORT states "The Cochran-Mantel-Haenszel test confirms a statistically significant difference between metal-specific and general-sick genes in their core enrichment across organisms." However, NB03 cell 9 shows CMH chi-squared = 2.55, p = 0.110 -- this is NOT statistically significant at any conventional threshold. The REPORT's claim of a confirmed significant difference is directly contradicted by the notebook output. This must be corrected.

3. **Missing 9 organisms between atlas (31) and analysis (22).** The atlas covers 31 organisms with metal experiments, but only 22 have fitness matrices available for the specificity analysis. Notably, DvH (the most deeply profiled organism with 757 experiments including 149 metal) and Btheta (519 experiments) are both SKIPPED in NB02 (cell 6) because their fitness matrices were not found. This is a major data loss: DvH alone accounts for a large fraction of metal-important genes in the atlas, especially for essential metals (Mo, W, Se, Mn). The REPORT discusses the "DvH bias" at length (Section: "The DvH Bias and Per-Metal Specificity") but does not acknowledge that DvH is actually MISSING from the analysis entirely. The 0% specificity for essential metals is thus not a DvH experiment-count bias as stated -- it appears those metals simply have no data in the analysis at all, or are tested only in the remaining organisms. This needs investigation and correction.

4. **REPORT misattributes the Fisher exact OR for H1c.** The REPORT states the functional enrichment Fisher exact test yields "OR=1.64, p=1.0e-7" for metal-resistance keywords in metal-specific vs general-sick genes. NB04 cell 7 confirms this value. However, the final summary cell (cell 15) of NB04 prints "H1c (metal-resistance enrichment in metal-specific): OR=0.64, p=8.42e-03" -- this is actually the H1d result (novel vs annotated Fisher exact), not H1c. The variable `odds` in cell 15 was overwritten by the H1d computation in cell 9. While the REPORT happens to cite the correct OR=1.64 for H1c (from cell 7), the notebook's final summary is misleading and should be fixed.

### Important

5. **ICA module analysis completely failed.** NB04 cell 13 reports "No metal-responsive modules found." The REPORT acknowledges this but attributes it to a threshold calibration issue. The right panel of `functional_comparison.png` simply displays "No module data" -- an empty plot that provides no information. This was a planned analysis component (RESEARCH_PLAN.md, Notebook 4, bullet 5) and an expected output (`data/module_metal_specificity.csv`). The file was never generated. Either the module analysis should be fixed (the REPORT suggests using pre-computed z-scores from Metal Atlas NB05) or it should be explicitly removed from the analysis plan rather than left as a silent failure.

6. **Cross-validation against counter_ion_effects is weak.** NB02 cell 12 finds only 14.7% of metal-important genes are sick under osmotic stress, compared to the 39.8% overlap found by the counter_ion_effects project. The notebook attributes this to "stricter threshold" but does not quantify the effect of the threshold difference or attempt to match the counter_ion_effects methodology. A 2.7x discrepancy is substantial and undermines confidence in the cross-validation. The notebook should either replicate the counter_ion_effects threshold (fit < -1 without the |t|>4 requirement) to show convergence, or explicitly document why the methods are expected to diverge.

7. **Per-metal specificity table in REPORT is incomplete.** The REPORT's per-metal breakdown (Finding 1) lists only Cadmium, Copper, Cobalt, Zinc, and Aluminum, stating essential metals show "0% specificity." But NB02 cell 15 shows the per-metal table includes Chromium (61.1%), Uranium (55.1%), Nickel (43.5%), and Iron (21.5%) in addition to the ones listed. Mercury, Manganese, Molybdenum, Selenium, and Tungsten are absent from this table entirely -- they do not appear because they have no gene records in `metal_with_spec` after the merge (since DvH was skipped). The REPORT's statement about "0% specificity" for essential metals is misleading when those metals simply have no data.

8. **Gene record count discrepancy.** The REPORT states "6,838 metal-important gene records with fitness matrix data across 22 organisms" but the original atlas has 12,838 records. Only 6,838 were successfully processed (53.2%), meaning nearly half of the metal-important gene records are excluded. The REPORT mentions "12,838" in the metal_genes_with_specificity.csv description but does not prominently address this ~47% attrition rate or analyze whether the excluded genes differ systematically from the included ones in their conservation or functional properties.

9. **DUF1043/YhcB and DUF39 missing from novel candidate table.** The REPORT's novel candidate table (Finding 4) shows "--" for DUF1043/YhcB and DUF39 specificity data. However, NB04 cell 10 shows DUF1043/YhcB has 3/6 genes metal-specific (50%, mean sick rate 0.054) and DUF39 has 0/1 (0%, sick rate 0.758). These values should be filled in rather than left as dashes.

### Minor

10. **`specificphenotype` table validation never performed.** The RESEARCH_PLAN.md (NB02 method, bullet 7) states genes should be compared against the Fitness Browser `specificphenotype` table "as an independent validation." This validation does not appear in any notebook. While listed as optional ("if available"), it was a planned validation step and its omission should be noted in the REPORT's Limitations section.

11. **`statsmodels` in requirements.txt but never imported.** The requirements.txt lists `statsmodels>=0.14` but none of the four notebooks import it. This is a minor packaging issue.

12. **Hardcoded absolute paths.** All notebooks use `MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'` as a hardcoded absolute path. While acceptable for internal use, this breaks reproducibility for anyone else. The README reproduction instructions do not mention this path dependency.

13. **The per-organism scatter plot (conservation_by_specificity.png, panel 3)** shows most organisms cluster above the diagonal, meaning general-sick genes tend to have higher core fractions than metal-specific genes in the same organism. This is consistent with the CMH test (p=0.11, trending toward general-sick being more core), but the REPORT does not discuss this visual pattern.

14. **The REPORT's YebC discussion cites "Ignatov et al. 2025" with PMID 40624002.** The paper describes YebC as a translation factor for proline-rich proteins, which is a general cellular function. The connection between this role and metal-specific tolerance is not explained. If YebC's metal specificity is its strongest evidence for a dedicated metal role, the proposed mechanism should be discussed.

## Scientific Assessment

The central scientific question is well-formulated and the negative result (H1 not supported -- metal-specific genes are still core-enriched) is an important finding that strengthens the Metal Atlas's core genome robustness model. The hypothesis testing framework is rigorous, with appropriate statistical tests (Fisher exact, CMH) and sensitivity analyses.

However, the statistical interpretation needs correction. The CMH test (p=0.110) does not reach significance, yet the REPORT claims it "confirms a statistically significant difference." This is a factual error that must be fixed. The correct interpretation is that there is a trend toward metal-specific genes being slightly less core-enriched than general-sick genes, but this difference is not statistically significant after stratifying by organism.

The functional enrichment analysis (H1c) is convincing: the 1.64x enrichment of metal-resistance keywords in metal-specific genes (p=1.0e-7) provides strong evidence that the specificity classification captures biologically meaningful categories, even if it does not separate core from accessory genes.

The H1d result (novel candidates are LESS metal-specific than annotated ones, OR=0.64, p=0.008) is a genuine surprise that the REPORT handles well, attributing it to the organism-level experiment-count bias rather than dismissing it.

The loss of DvH and Btheta from the analysis is the most serious scientific concern. These are two of the most deeply profiled organisms and their absence may systematically bias the results. DvH in particular is the sole representative for several essential metals. The REPORT's discussion of the "DvH bias" appears to be written as if DvH were included but biased, when in fact it is entirely absent.

## Reproducibility

The project meets most BERIL reproducibility standards. All four notebooks are committed with saved outputs, five figures are saved to `figures/`, five data files are generated to `data/`, and the README includes step-by-step reproduction instructions. The requirements.txt is present.

Key reproducibility gaps:
- **Hardcoded absolute paths** to the main repo (`/home/psdehal/...`) prevent anyone else from running the notebooks without modification.
- **Missing fitness matrices** for DvH and Btheta are not explained. Are these matrices simply not generated by the fitness_modules project, or is there a path issue? This is not documented.
- **No expected runtime** is provided in the README reproduction section, as recommended by PROJECT.md.
- **Cross-project data dependencies** are documented in RESEARCH_PLAN.md but rely on local file paths rather than lakehouse references as recommended by PROJECT.md.

## Documentation Quality

**README.md**: Good. Covers research question, status, reproduction instructions, and quick links. The status line is accurate and informative. Missing: expected runtime, path configuration instructions.

**RESEARCH_PLAN.md**: Excellent. One of the strongest research plans in the observatory. Clear hypotheses with null and alternative, detailed data source inventory, explicit pitfall documentation, revision history showing iterative improvement. The plan correctly downgrades H1e to exploratory and adds the essential gene bias caveat based on plan review feedback.

**REPORT.md**: Good structure and interpretation, but contains the numerical discrepancies and CMH mischaracterization detailed above. The Interpretation section is thoughtful, particularly the revision of the two-tier model. The Limitations section is honest but should include the DvH/Btheta exclusion and the missing specificphenotype validation. The Future Directions section is well-targeted.

Overall, the documentation tells a coherent scientific story with appropriate caveats, but the factual errors in the REPORT must be corrected before the project can be considered finalized.
