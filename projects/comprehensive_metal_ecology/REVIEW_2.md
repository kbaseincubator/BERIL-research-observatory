---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-07-15
project: comprehensive_metal_ecology
---

# Review: Metal-Gene Density Predicts Ecological Niche Breadth in Prokaryotes

*This is a second independent review. REVIEW_1.md was dated 2026-07-14. This review assesses changes since that review and evaluates the substantial new analyses added to the project.*

## Summary

The project has made real progress since REVIEW_1: the most critical gap (NB16 missing entirely) is resolved, NB15 has full outputs, `requirements.txt` is present, and the README now has a Reproduction section. The project has also grown substantially, with six new findings (12–17), three new notebooks (NB27–NB29), and an extensive "Manuscript reviewer response analyses" section (Q1–Q4) covering latitude mechanism tests, cofactor overlap audit, null category PGLS, and per-metal bedrock analysis. The new analyses are methodologically strong — the Q4 per-metal decomposition with VIF diagnostics and the Cr/Co bedrock finding are especially well-executed. However, the confirmatory-notebook execution gap remains the project's most significant weakness: NB03, NB04, and NB17 have only 1–2 outputs each out of 5–6 code cells, making these confirmatory analyses still effectively unreproducible from the committed notebooks. Additionally, the Q1–Q4 manuscript response analyses and Findings 12–17 are backed entirely by standalone scripts — the same pattern flagged in REVIEW_1. One internal inconsistency from REVIEW_1 remains unresolved: `INTERPRETATION_TABLE.md` retrospectively describes cofactor biosynthesis as "Expected strongest negative signal" while `RESEARCH_PLAN.md` section 5.2 explicitly pre-specifies it as "Minimal expected signal." These issues should be resolved before submission.

---

## Methodology

**Research question and pre-registration.** The confirmatory hypothesis (H1: β < 0, FDR p < 0.05) remains unambiguous and the pre-registration in RESEARCH_PLAN.md is genuine. P1 is confirmed (β = −0.021, FDR p = 6.4×10⁻⁸).

**New analyses (Q1–Q4).** All four manuscript-response analyses are exploratory (correctly labelled) and methodologically sound:
- *Q1 null category PGLS*: clean standalone confirmation that the five non-metal categories from NB18 are genuinely near-zero — results match NB18 exactly, providing independent reproducibility of a key specificity control.
- *Q2 cofactor overlap audit*: thorough; the 83/382 overlap with the metal gene list is expected by KEGG design and the quantitative impact check (β for 382-KO set = β for 370-KO reduced set = −0.029) is appropriate.
- *Q3 carbohydrate metabolism reconciliation*: the geometric explanation (per-Mb density vs. GapMind pathway completeness) is correct and clearly stated. Appropriately labelled exploratory.
- *Q4 latitude mechanism*: nine PGLS models (A–I) plus per-metal decomposition (J–M) and redox proxy controls (N series) are well-structured. VIF diagnostics (all < 2) confirm the per-metal models are not collinear. The Cr and Co bedrock findings — robust across pH control and soil moisture — are novel and represent the strongest environmental-mechanism result in the project. The SOM negative-predictor finding (β = −0.016, p = 6.8×10⁻⁵) is a genuine incidental result that deserves mention in the Limitations section (see Suggestion 7).

**INTERPRETATION_TABLE vs RESEARCH_PLAN contradiction (unresolved from REVIEW_1).** `RESEARCH_PLAN.md` section 5.2 explicitly pre-specifies the functional category expectations as: resistance = "Strongest expected driver" and cofactor = "Minimal expected signal." The `INTERPRETATION_TABLE.md` Section 3 instead describes cofactor biosynthesis as "Expected strongest negative signal" and marks the observed result "✓ As predicted (strongest effect)." This is not "as predicted" by the pre-registered plan; the actual result reverses the pre-specified expectation. The INTERPRETATION_TABLE expectation column appears to have been updated post-hoc to match the findings. The project's narrative in REPORT.md and REVIEW_1.md both correctly describe this as a reversal and a methodological discovery — but the INTERPRETATION_TABLE table row itself still contains the post-hoc expectation. This undermines the interpretive record for the most scientifically interesting finding in the project.

---

## Reproducibility

**What was resolved since REVIEW_1:**
- `16_clade_stratified_pgls.ipynb` now exists and is fully executed (5/5 code cells with outputs). This was the most critical gap.
- `15_ausmicrobiome_density_replication.ipynb` is now fully executed (5/5 outputs).
- `requirements.txt` is present.
- README now contains a `## Reproduction` table covering Spark vs local execution.
- NB26 description in REPORT updated to correctly name the file and describe both its analyses (interaction test and cofactor jackknife).
- Stale "(figure pending)" annotations removed for `internal_structure_forest.png` and `aus_composition_comparison.png`.
- REPORT typo ("execution.]") appears fixed.
- NB24 stale "pending" language replaced with actual results.
- P3/P4 naming is clarified in the README.

**What remains unresolved:**

*NB03, NB04, NB17 still essentially unexecuted (critical — same as REVIEW_1 Suggestion 2).* Notebook output counts:
- `03_tier_and_category_analysis.ipynb`: 6 code cells, **1 with output** (likely the import/setup cell)
- `04_confounder_checks.ipynb`: 5 code cells, **1 with output**
- `17_negative_controls.ipynb`: 6 code cells, **2 with outputs**

These are confirmatory notebooks (P1–P3 tier comparisons, confounder checks, named negative controls). The corresponding data files exist on disk (`data/03_category_pgls_results.csv`, `data/04_confounder_results.csv`, etc.), confirming the analyses ran — but not from these notebooks. This is the pitfall documented in `docs/pitfalls.md` ("Commit Notebooks Alongside Their Artifacts, Not Just the TSVs"). For pre-registered confirmatory analyses, the executed notebook is the reproducibility record.

*Findings 12–17 and Q1–Q4 are backed by standalone scripts, not notebooks (new issue since REVIEW_1).* The results for six of the seventeen REPORT findings come from scripts in the `scripts/` directory:
- Finding 12 (phylo-D): `scripts/fritz_purvis_d_analysis.py`
- Finding 13 (env niche breadth): `scripts/env_niche_breadth_analysis.py`
- Finding 14 (per-KO drivers): `scripts/per_ko_driver_analysis.py`
- Findings 15–16 (co-occurrence): `scripts/run_cooccurrence_analysis.py`, `scripts/partner_characterisation.py`
- Finding 17 (HGT evidence): `scripts/hgt_direct_evidence.py`
- Q1–Q4 responses: `scripts/null_category_pgls.py`, `scripts/cofactor_overlap_audit.py`, `scripts/latitude_mechanism_tests.py`, `scripts/per_metal_bedrock_models.py`, `scripts/redox_metal_models.py`

Scripts produce no output record in the repository unless explicitly run. A reviewer cannot verify the numbers in Findings 12–17 without re-executing these scripts with Spark access. Converting key analysis scripts to executed notebooks, or committing script stdout as `.log` files, would close this gap.

*`aus_density_overlap_scatter.png` still "(figure pending)" (unresolved from REVIEW_1 Suggestion 5).* The REPORT figures list still marks this figure as "(figure pending)" even though NB21 is now executed.

*NB06 still essentially empty.* `06_confounder_discovery.ipynb` has 1 output across 16 code cells. This is exploratory (lower impact), but the notebook is effectively a shell.

---

## Code Quality

**Statistical methods.** The PGLS implementation remains consistent throughout. New analyses follow the same pattern: ML-estimated Pagel's λ, BH-FDR correction, effect sizes with SE and 95% CI. The Q4 per-metal analysis correctly applies BH-FDR across 6 metals and the VIF diagnostics (all < 2) are a welcome addition. The redox proxy controls (N series) correctly test whether the Cr bedrock signal is attenuated by soil moisture — the answer is no (β unchanged to three decimal places), which rules out a specific mechanistic pathway and strengthens the Cr interpretation.

**Co-occurrence network saturation (Findings 15–16).** The REPORT acknowledges that 38–42% of genus pairs show significant positive co-occurrence, making clustering and betweenness metrics degenerate. This is correctly handled. However, the near-saturated network also means the PGLS of positive partner count on KO density (β = 138–210, p < 10⁻²¹) is measuring enrichment within a context where the majority of pairs already co-occur. The caveat that niche breadth correlates with partner count (Spearman ρ = 0.33–0.37) is noted, and partial analysis controlling for B_std is listed as Future Direction 9. This confound should be stated more prominently as a limitation in Findings 15–16 themselves, not only in the methodological note.

**FDR value discrepancy (unresolved from REVIEW_1 Suggestion 3).** INTERPRETATION_TABLE Section 1 table row correctly shows p(FDR) = 6.42e-08, matching REPORT Finding 1. However, the "Observed outcome" narrative paragraph in Section 1 and the Final claim classification block still state "FDR p = 4.3e-08." The ground truth is `data/02_joint_fdr.csv`. This internal inconsistency has not been corrected since REVIEW_1.

**pH niche β units (unresolved from REVIEW_1 Suggestion 8).** Finding 13 reports β = −0.760 for soil pH niche width against z-scored KO density but does not define how pH niche width is computed or what units it is in. Without the response scale, the coefficient cannot be contextualised against the primary β = −0.021 or checked for plausibility.

---

## Findings Assessment

**Findings 1–11.** The assessment from REVIEW_1 stands. Primary finding (P1 β = −0.021, FDR p = 6.4×10⁻⁸) is well-supported. Functional landscape (Finding 3) and internal split (Finding 4) remain the most important contributions. Coreness permutation (emp_p = 0.298) is reported transparently.

**Finding 12 (two-scale phylo-D framework).** The Fritz & Purvis D × Pagel's λ dual framework is well-conceived. The near-orthogonality of D and λ (Spearman ρ = −0.041, p = 0.49) correctly validates that the two metrics capture independent signals. The 13 double-signal KOs are all resistance/transport/sensing genes; no cofactor KO appears — internally consistent with Findings 4 and 17. The figure path `figures/png/fig08_phylo_D_lambda.pdf` (a PDF in a `png/` subdirectory) is cosmetically inconsistent with the rest of the figures directory.

**Finding 13 (pH niche β = −0.760).** The pH-specificity result is mechanistically well-motivated. The null temperature result provides meaningful contrast. Correctly labelled exploratory. Still needs response-variable units (see Suggestion 5).

**Findings 14–16 (per-KO drivers, co-occurrence).** emrB as broadest multi-metal associator is plausible (RND/MFS broad substrate range). The metal-match Mann-Whitney result (p = 0.035) provides modest specificity evidence. Findings 15–16 are quantitatively impressive but are entangled with the niche-breadth signal; the partial PGLS controlling for B_std should be prioritised before any publication of co-occurrence claims.

**Finding 17 (HGT direct evidence).** MWU comparison of Fritz & Purvis D between double-signal and control KOs (p = 1.81×10⁻⁴) is the strongest evidence line. The NCBI GenBank plasmid/mobile-element fractions are weaker (marginal p; publication-bias limitations correctly noted). The finding converges with Finding 4 at gene-level resolution.

**Q4 Cr/Co bedrock finding.** The Cr bedrock association (BH p = 6.7×10⁻⁹, unattenuated by pH and soil moisture) is the most robust environmental-mechanism result in the project. The mechanistic interpretation — serpentine/ultramafic soil evolutionary filtering rather than acute Cr(VI) toxicity — is supported by the negative redox proxy controls and is well-reasoned. Mafic score (ecotapestry, Model H) independently corroborates GeoROC Cr. This finding would merit a pre-registered follow-up.

**Limitations section.** Well-maintained. The SOM incidental finding (β = −0.016, negative predictor of niche breadth in Q4 redox models; SOM absorbs the pH association) should be added as a limitation: if SOM mediates part of the pH association, the pH niche signal (Finding 13) may be partially confounded by SOM availability rather than reflecting direct metal-speciation pH effects.

**Discoveries section.** Ten entries, all quantitatively grounded with specific numbers and notebook/script references. The genome-streamlining pervasiveness claim is a strong candidate for cross-project surfacing; the scope annotation (genus-level per-Mb KO density vs MicrobeAtlas B_std) is present and appropriate.

---

## Suggestions

1. **[Critical] Execute NB03, NB04, and NB17, or commit executed scripts alongside the notebook stubs.** These confirmatory notebooks have 1–2 outputs each (effectively empty beyond the import cell) despite corresponding data files existing on disk. Run each notebook end-to-end, or commit the generating scripts with execution logs and document the discrepancy in RESEARCH_PLAN.md's revision history, as recommended by `docs/pitfalls.md`.

2. **[Critical] Correct the cofactor pre-specification in INTERPRETATION_TABLE.** Section 3 expectation column should reflect what RESEARCH_PLAN.md §5.2 actually states: cofactor = "Minimal expected signal." Update the "Consistent?" column to "✗ Reversed — cofactor strongest, resistance null (methodological discovery)." The reversal is scientifically important and already well-described in the REPORT narrative — the INTERPRETATION_TABLE should match that honest characterisation rather than appearing to have predicted the result.

3. **[Moderate] Commit output records for script-based findings (12–17, Q1–Q4).** Convert key analysis scripts to executed notebooks, or commit `.log` files showing script stdout alongside each script. At minimum, commit a `scripts/EXECUTION_LOG.md` with run date, environment, and key numerical outputs (β, p, n) per script — providing the minimum traceability for independent verification.

4. **[Moderate] Fix FDR value in INTERPRETATION_TABLE narrative.** Both the "Observed outcome" paragraph in Section 1 and the Final claim classification block state "FDR p = 4.3e-08." The correct value (BH over 3 tests at rank 1) is 6.42e-08, consistent with the table row and REPORT. Update both narrative occurrences.

5. **[Moderate] Add response-variable units for pH niche β = −0.760.** Add a one-sentence definition at the start of Finding 13 specifying how pH niche width is computed and in what units — e.g., "pH niche width = max(pH) − min(pH) across 16S sampling sites for each genus (units: pH units)" — so the coefficient can be contextualised.

6. **[Moderate] Generate `aus_density_overlap_scatter.png` or remove its entry.** NB21 is executed; this figure should be producible. Either generate it and remove the "(figure pending)" annotation, or remove the figure entry from the REPORT figures list.

7. **[Minor] Add SOM incidental finding to Limitations.** The Q4 redox proxy analysis found that soil organic matter independently predicts narrower niches (β = −0.016, p = 6.8×10⁻⁵) and absorbs the pH association in K models. A one-sentence note in the Limitations section would flag that the pH niche signal (Finding 13) may be partially mediated by SOM rather than direct metal-speciation pH dependence.

8. **[Minor] Add co-occurrence confound to Findings 15–16 text.** The network-saturation and B_std correlation caveats are currently in a "methodological note" paragraph. Move the "Partial analyses controlling for B_std are needed" sentence into the main findings statement of Finding 15 so reviewers see it immediately, not only in the method discussion.

9. **[Minor] Execute or clear NB06.** `06_confounder_discovery.ipynb` has 1 output across 16 code cells. If the confounder discovery analysis is fully captured in `data/06_candidate_coverage.csv`, document this in a header cell noting that outputs are cached and the notebook has not been re-executed.

10. **[Minor] Fix figure path for Finding 12.** `figures/png/fig08_phylo_D_lambda.pdf` is the only figure in a `png/` subdirectory and the only PDF in the figures list. Move to `figures/fig08_phylo_D_lambda.png` (or equivalent) for consistency.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-07-15
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md (1,270 lines), INTERPRETATION_TABLE.md, 30 notebooks (cell-output audit), 70+ figures (existence check), 50+ data/results files (listed in REPORT), docs/pitfalls.md; assessed against REVIEW_1.md (2026-07-14)
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:84c91f0b01565ac20721d7a933e59543d16529f31ccbbcf1068243156e51bd48 -->
