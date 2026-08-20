---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-07-14
project: comprehensive_metal_ecology
---

# Review: Metal-Gene Density Predicts Ecological Niche Breadth in Prokaryotes

## Summary

This is a methodologically ambitious and intellectually honest project. The pre-registration via `RESEARCH_PLAN.md` and `INTERPRETATION_TABLE.md` is genuine (locked before execution), the confirmatory/exploratory labelling is consistent throughout, and the coreness-matched permutation result (NB20; emp_p = 0.298) — which shows the overall metal-gene β is not unusual among conserved gene sets — is reported and discussed rather than buried. The functional landscape analysis (Finding 3) is a genuine contribution: establishing the genome-streamlining baseline as the correct null context rather than zero is exactly the kind of calibrated interpretation that strengthens a finding. The split-magnitude permutation (NB25) and cofactor jackknife (NB26) are well-designed validation steps. The main weaknesses are reproducibility gaps: the `16_clade_stratified_pgls` notebook (backing Finding 8) does not exist on disk, and three confirmatory notebooks (NB03, NB04, NB17) are unexecuted shells with no cell outputs despite the analysis data files existing — indicating these confirmatory analyses were run via scripts or REPL rather than through the committed notebooks. Several REPORT sections also contain stale "pending" language for analyses that have since been completed. These gaps should be addressed before submission.

---

## Methodology

**Research question and hypothesis.** The research question is precisely stated and the confirmatory hypothesis (H1: β < 0) is directional with pre-specified decision rules and a pre-specified 50% attenuation threshold for confounders. FDR correction is applied jointly across P1/P2/P3 as pre-registered.

**Approach.** The PGLS framework with ML-estimated Pagel's λ is appropriate for cross-genus phylogenetically controlled analysis. Levins' standardised B_std from MicrobeAtlas is a reasonable niche-breadth proxy, and its independence from the metal-concentration axes (both from different data sources) is correctly noted.

**Data sources.** Primary data sources (MGnify MAGs, GTDB phylogeny, MicrobeAtlas OTU survey) are clearly identified and linked to specific BERDL tables. The REPORT data section lists every generated file with row counts, which is excellent for traceability.

**Pre-registration integrity.** The RESEARCH_PLAN.md section 5.2 pre-specifies that cofactor biosynthesis has "minimal expected signal" while resistance/detox should be the "strongest expected driver" — the actual result reverses this expectation. The project correctly flags this reversal as a methodological discovery rather than inflating the cofactor result as confirmatory. This is the right approach and shows genuine scientific integrity.

**P3 null result.** The NGSA Australia-only replication (β = −0.002, p = 0.755) is unexplained. The REPORT offers three candidate explanations but these remain unresolved. The AusMicrobiome genomic predictor (P5) recovers the signal using the same genus panel, implicating the soil-concentration predictor. However, since P3 was pre-registered as a confirmatory test and is effectively null, this is a genuine replication gap for the soil-concentration form of the hypothesis.

**Reproducibility.** There is no `requirements.txt` or equivalent, and no `## Reproduction` section in README.md explaining which notebooks require a Spark session, which run locally from cached data, or what the expected runtimes are. A new analyst could not reproduce the pipeline without this information.

---

## Code Quality

**Known pitfalls.** The pitfalls in `docs/pitfalls.md` most relevant to this project include: (1) `gtdb_taxonomy_id` join returning zero rows — correctly avoided (the project joins on `genome_id`); (2) Spark DECIMAL columns returned as `decimal.Decimal` — relevant to any `.toPandas()` calls on MAG/abundance tables; (3) the `ncbi_env` EAV format. No evidence of pitfall (1) in the reviewed code. Pitfalls (2) and (3) cannot be verified in NB03/NB04 because those notebooks are unexecuted.

**Statistical methods.** PGLS is correctly implemented with ML-estimated λ, BH-FDR correction, and effect sizes (β, SE, 95% CI) reported throughout. The coreness-matched permutation test design (NB20) is sound. The split-magnitude permutation (NB25) correctly matches group sizes to the observed resistance/cofactor split. The cofactor jackknife (NB26) properly removes one KO at a time; the 4-KO scope (of 7 original, 3 absent from pangenome) is honestly caveated.

**Unexecuted confirmatory notebooks.** `03_tier_and_category_analysis.ipynb` and `04_confounder_checks.ipynb` are both marked "**Status:** PENDING EXECUTION" in their header cells and have zero code-cell outputs. Yet the corresponding data files (`data/03_category_pgls_results.csv`, `data/03_tier_pgls_results.csv`, `data/04_confounder_results.csv`) exist on disk, meaning the analyses were run via scripts or a REPL rather than through the committed notebooks. This is precisely the pitfall documented in `docs/pitfalls.md` ([genotype_to_phenotype_enigma] "Commit Notebooks Alongside Their Artifacts, Not Just the TSVs"). For confirmatory analyses with pre-registered hypotheses, the executed notebook is the reproducibility record. `17_negative_controls.ipynb` is in the same state (0 outputs) and is heavily cited in Findings 3 and 5.

**NB26 naming inconsistency.** The notebook file is `26_interaction_test_jackknife.ipynb`. The README and REPORT refer to this notebook only as the "cofactor jackknife" and list it as `26_cofactor_jackknife.ipynb` in the Notebooks section. The notebook's own header correctly states "NB26 — Interaction Test and Cofactor Jackknife," indicating it contains both analyses. The mismatch between filename and REPORT description creates confusion about notebook content.

**FDR value discrepancy.** The REPORT (Finding 1) states FDR joint p = 6.4×10⁻⁸ for P1. The INTERPRETATION_TABLE shows p(FDR) = 4.28e-08 for the same test. For BH correction over 3 tests at rank 1: p_adj = 2.14×10⁻⁸ × 3/1 = 6.42×10⁻⁸, which matches the REPORT. The value 4.28×10⁻⁸ ≈ 2.14×10⁻⁸ × 2 corresponds to BH over 2 tests — the INTERPRETATION_TABLE appears to have been computed before P3 was added to the joint correction and not subsequently updated. The ground truth is `data/02_joint_fdr.csv`.

**Minor typo.** REPORT section "MAG quality sensitivity" contains a stray `"execution.]"` bracket preceding the data citation at the end of the block.

---

## Findings Assessment

**Finding 1 (primary β = −0.021, FDR p = 6.4×10⁻⁸).** Well-supported. Six of seven sensitivity analyses are consistent (S7 Australia is near-zero), and the signal survives all pre-specified confounder tests. The genome-size attenuation (46.7%, just below the pre-registered 50% threshold) is correctly noted as partial rather than total confounding.

**Finding 3 (functional landscape / genome-streamlining baseline).** The most important interpretive contribution of the project. Establishing that 14/19 KEGG categories show significantly negative associations with niche breadth — and that the metal-gene signal sits 30–60% below the housekeeping baseline — places the primary finding in its proper context. The coreness permutation (emp_p = 0.298) is reported honestly and its implications clearly worked through. This is a model of calibrated interpretation.

**Finding 4 (internal split: resistance null vs cofactor strong).** The permutation validation (Δβ = 0.035259, 0/1000 null partitions exceeded; NB25) and jackknife stability (NB26) are well-designed. The reversal of the pre-specified expectation (resistance was expected strongest, cofactor was expected minimal) is surfaced as the novel finding rather than hidden.

**Finding 8 (clade-stratified PGLS).** This finding is backed by `data/clade_stratified_pgls_results.csv` and `figures/clade_stratified_forest_plot.png`, but **the notebook `16_clade_stratified_pgls.ipynb` does not exist in the notebooks directory.** The Cochran's Q heterogeneity test (Q = 3.60, df = 3, p = 0.309) and all per-phylum β estimates in this finding are unreachable by any committed notebook. This is the most significant reproducibility gap in the project.

**NB24 sample-depth sensitivity — stale "pending" language.** The REPORT explicitly states "pending JupyterHub execution — Spark required for per-genus sample counts." However, `24_niche_breadth_sensitivity.ipynb` has 10 of 11 code cells with output, and `data/niche_breadth_sensitivity.csv` exists on disk. The analysis appears to have been completed; the REPORT text was not updated to include the actual results.

**Figures marked pending that now exist.** The REPORT's figures list notes `internal_structure_forest.png` and `aus_composition_comparison.png` as "(figure pending)" but both files exist on disk. These annotations should be removed.

**Finding 13 (pH niche β = −0.760).** The pH niche width β of −0.760 is two orders of magnitude larger than any other β reported in the project. The REPORT does not specify the units of the pH niche width response variable or how it was computed relative to the z-scored KO density predictor. Without this information, the coefficient cannot be compared across analyses or checked for scaling artefacts.

**Discoveries section.** All 10 entries are clearly scoped with specific quantitative support from named notebooks. The CWM-from-environment XGBoost entry (poor spatial block CV RMSE, SHAP metal dominance) is honestly framed. The co-occurrence entries note the network saturation caveat appropriately. One cross-project note: the genome-streamlining pervasiveness claim is a strong candidate for surfacing to other BERDL projects, but it should be annotated with its specific scope (genus-level per-Mb KO density against MicrobeAtlas B_std) so downstream projects don't over-generalise it to other analysis levels.

**Limitations.** The limitations section is thorough and appropriately self-critical. The P3 null, cofactor category sample size (n=7 KOs, 4 detectable), r²=0.046, 46.7% genome-size attenuation, and BacDive NB09 incompleteness are all disclosed. The coreness permutation result (emp_p = 0.298) is prominently discussed rather than minimised. This is good scientific practice.

---

## Suggestions

1. **[Critical] Reconstruct and commit `16_clade_stratified_pgls.ipynb`.** Finding 8 has no committed notebook. `data/clade_stratified_pgls_results.csv` and `figures/clade_stratified_forest_plot.png` are committed, but the analysis is not reproducible from any notebook. Reconstruct from the committed data and note the reconstruction in RESEARCH_PLAN.md per the `docs/pitfalls.md` guidance ("Commit Notebooks Alongside Their Artifacts, Not Just the TSVs").

2. **[Critical] Execute NB03, NB04, and NB17, or replace with committed scripts.** These confirmatory notebooks are unexecuted shells ("PENDING EXECUTION") despite their corresponding data files existing. Run each end-to-end to produce matching outputs, or replace the shell notebooks with the actual scripts that generated the data and document this in RESEARCH_PLAN.md revision history. For confirmatory analyses, the executed notebook is the reproducibility record.

3. **[Moderate] Fix FDR value in INTERPRETATION_TABLE.** P1 p(FDR) = 4.28e-08 in the INTERPRETATION_TABLE conflicts with 6.4×10⁻⁸ in the REPORT. Verify against `data/02_joint_fdr.csv` and update the INTERPRETATION_TABLE to the correct value (BH for 3 tests at rank 1 = 6.4×10⁻⁸).

4. **[Moderate] Remove stale "pending" language from REPORT.** Update the NB24 sample-depth sensitivity paragraph to report the actual results from the now-executed notebook. Remove "(figure pending)" from `internal_structure_forest.png` and `aus_composition_comparison.png` in the figures list.

5. **[Moderate] Execute or clear NB06 and NB15.** `06_confounder_discovery.ipynb` (15 code cells, 0 outputs) and `15_ausmicrobiome_density_replication.ipynb` (5 code cells, 0 outputs) are unexecuted shells. If P5 was produced by a script rather than NB15, document this clearly and either run NB15 or remove it from the notebook table in the REPORT.

6. **[Moderate] Add `requirements.txt` and a `## Reproduction` section to README.md.** List at minimum: `pandas`, `numpy`, `scipy`, `statsmodels`, `dendropy` (or equivalent PGLS library), `matplotlib`, `scikit-learn` (for NB29), `berdl_notebook_utils`. The Reproduction section should specify which notebooks require a Spark session versus which can run locally from the cached CSVs in `data/`.

7. **[Minor] Resolve NB26 filename vs REPORT description mismatch.** Update the REPORT Notebooks section to use the correct filename (`26_interaction_test_jackknife.ipynb`) and expand the description to reflect that the notebook contains both the interaction test and the cofactor jackknife.

8. **[Minor] Add units and scale note for pH niche β = −0.760 (Finding 13).** Clarify how the pH niche width response variable is scaled relative to the z-scored KO density predictor, so readers can contextualise this β against the primary β = −0.021.

9. **[Minor] Clarify P3 vs P4 naming in README.** The RESEARCH_PLAN pre-registers the NGSA test as P3; the README lists NB12 as "P4 proper NGSA replication." A one-sentence note explaining that P4 is the expanded version of the pre-registered P3 (AusMicrobiome genus panel + NGSA soil chemistry) would prevent confusion.

10. **[Minor] Fix REPORT typo.** Remove the stray `"execution.]"` bracket in the MAG quality sensitivity data citation (~line 698 of REPORT.md).

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-07-14
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md (1,263 lines), INTERPRETATION_TABLE.md, 29 notebooks (cell-output audit), 63+ figures (existence check), 35+ data files (listed in REPORT), docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:f1100bc26cc40dc906c59dafac648439c37cd2026eb7a514143590f31365bf43 -->
