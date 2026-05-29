---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-05-02
project: microbeatlas_metal_ecology
---

# Review: Metal Resistance Ecology — Phylogenetic Conservation vs. Environmental Selection

## Summary

This is an unusually thorough and well-executed macro-ecological analysis. The core question — whether metal-resistance functional diversity in the global microbiome reflects phylogenetic constraint or environmental selection — is clearly stated, testable, and genuinely novel at this scale. The analytical pipeline links a 98,919-OTU 16S atlas (464K samples) to pangenome AMR annotations across 6,789 species via GTDB taxonomy, applies Pagel's λ and PGLS with correct phylogenetic control, and then extends into two independent validations (Track A: 1,624 BERDL groundwater samples; Track B: PRJNA1084851, 133 samples processed end-to-end). All six primary notebooks have saved outputs. The REPORT.md is exceptionally detailed — 1,364 lines covering primary results, six robustness analyses (R1–R6), five sensitivity analyses (S1–S5), a full multiple-testing accounting, and explicitly documented limitations. Three known BERDL pitfalls tagged `[microbeatlas_metal_ecology]` in `docs/pitfalls.md` are all addressed: the `ape::corPagel` row-ordering bug is fixed and verified by a unit test, `geiger::fitDiscrete` is replaced with `phytools::phylosig`, and the `kbase_ke_pangenome` JupyterHub-only restriction is correctly flagged in the README and notebook headers. The main areas for improvement are a missing `RESEARCH_PLAN.md` (referenced but absent), R package versions not pinned in a machine-readable file, an interpretation gap in the leave-one-metal-out sensitivity analysis, and moderate root-directory clutter from unlisted intermediate markdown files.

---

## Methodology

**Research question and testability**: Clearly articulated. The primary confirmatory tests (6 simple PGLS models with Bonferroni correction; Pagel's λ for 9 trait × domain combinations) are explicitly separated from exploratory/robustness analyses, which is good statistical hygiene. A pre-registration note in the REPORT under "Study Design and Inferential Framework" appropriately acknowledges the absence of preregistration and recommends it for future work.

**Approach**: Sound and appropriate. PGLS via `nlme::gls + ape::corPagel` with ML estimation of λ is the field standard for this type of macro-ecological comparative analysis. Treating Pagel's λ as a measure of phylogenetic signal and using it both diagnostically (NB04) and embedded within regression (NB05) is correct. The nitrification positive control (λ_bac = 0.939, λ_arc = 1.000) substantially strengthens confidence in the pipeline's ability to recover known signal.

**Data sources**: Clearly identified in both the README and REPORT. The genus-level taxonomy bridge (NB03) covering only 55.6% of OTU genera (12,438 / 22,357) is the most significant structural gap — it is acknowledged in the notebook and report, but no alternative matching strategy (e.g., SILVA–GTDB synonym tables or fuzzy name matching) was attempted. This means 44% of OTUs contribute to niche breadth estimates but not to the PGLS subset, potentially biasing the analytical genera toward well-studied, culturable lineages.

**Reproduction**: Strong. The README includes a well-structured step-by-step reproduction table distinguishing JupyterHub-only steps (NB01, NB02) from locally runnable steps (NB03–NB07), with explicit commands, expected outputs, and runtime notes. However, `RESEARCH_PLAN.md` is linked in the README Quick Links section but does not exist in the project directory — a broken link that affects navigation.

---

## Code Quality

**SQL queries**: Correct and appropriately structured. NB01 uses CTE patterns for multi-step aggregation, correctly joins `bakta_amr` to `gene_cluster` via `gene_cluster_id`, and applies a gene-name priority list before falling back to product-name regex matching. NB02's 260M-row join (`otu_counts_long × sample_metadata`) is an appropriate Spark-side aggregation pushed down before result collection. One potential false-positive risk in NB01: the `RLIKE '(mercury|arsenic|...)'` fallback on `amr_product` could match "metalloproteins" or "metal-binding" domains — the report acknowledges this and notes spot-checking confirms plausible distributions, but a systematic exclusion list (similar to the existing `NOT LIKE '%lactamase%'`) would reduce the risk further.

**Statistical methods**: Appropriate throughout. Levins' B_std is correctly computed as the normalised inverse Simpson index (`(B−1)/(J−1)`). Predictors are z-scored before PGLS for direct β comparability. Bonferroni correction is applied to the 6 confirmatory simple PGLS models, and BH-FDR correction is applied to the full 47-test family (saved to `data/all_tests_fdr.csv`). The PGLS λ discrepancy between standalone Pagel's λ (0.787) and PGLS-estimated λ (0.708) is explained correctly as expected given that the predictor itself carries phylogenetic signal.

**Pitfall compliance**:
- *`ape::corPagel` row-ordering*: **Fixed and tested.** Data is explicitly sorted to `tree$tip.label` order before fitting. `scripts/test_pgls_ordering.py` generates synthetic data with known λ = 0.8 and β = 0.05, scrambles row order, and verifies that sorted PGLS recovers correct estimates while unsorted fails. This is exemplary practice. The pitfall is also called out in the REPORT technical note (NB05).
- *`geiger::fitDiscrete(model='lambda')` in geiger ≥ 2.0*: **Addressed.** `phytools::phylosig(method='lambda', test=TRUE)` is used throughout, including for the binary `is_nitrifier` trait (treated as numeric, consistent with the pitfall fix recommendation).
- *`kbase_ke_pangenome` JupyterHub-only*: **Addressed.** NB01 and NB02 are clearly marked `# REQUIRES JUPYTERHUB` and the README reproduction table explicitly separates JupyterHub steps from local steps, with a note that pre-computed outputs in `data/` allow local re-running from step 3 onward.

**Notebook organisation**: Logical and clean. The six main notebooks follow a clear setup → query → analysis → output pattern. All notebooks have non-empty saved outputs (text tables, printed statistics, and/or figures). The supplementary `clade_specific_sensitivity.ipynb` is noted in the README as a standalone analysis but is not described in the data flow — readers may not know when to run it or what it produces.

**R environment**: `sessionInfo_r.txt` captures the full R environment including package versions (R 4.5.2, ape, phytools). This is good. However, it is not machine-readable for automated environment recreation; a `renv.lock` or equivalent would be more reproducible.

---

## Findings Assessment

**Conclusions supported by data**: Yes. The primary finding (metal type diversity → Levins' B_std, β = +0.021, Bonferroni p = 1.5×10⁻⁴) survives all six robustness analyses and twelve of thirteen leave-one-environment-out sensitivity tests. The REPORT presents results tables with full statistics for every sub-analysis, making the conclusions independently verifiable from the saved CSV files.

**Limitations acknowledged**: Thoroughly. The six limitations sections address: sequencing-effort confounds in niche breadth; underpowered archaeal PGLS (n = 48, power ≈ 11% at α = 0.05); uneven pangenome coverage; genome size; environment category heterogeneity; and the count-predictor Gaussian assumption. The REPORT explicitly notes which limitations are addressed by existing analyses vs. which require new data.

**Incomplete or unresolved analyses**: Three items merit attention:

1. **Sensitivity Analysis S1 (leave-one-metal-out) interpretation**: All seven leave-one-out tests produce non-significant results (p > 0.10), which the REPORT interprets as the effect being "distributed across the metal type diversity spectrum." This interpretation is reasonable but requires a caveat: losing significance after removing one of seven metals could also reflect that the predictor is near the statistical threshold and the compressed variance (max diversity 6 instead of 7) is sufficient to push it below significance. The direction is consistently positive, which supports the distributed interpretation, but the REPORT does not distinguish between "the signal is genuinely distributed" vs. "the signal is marginal and predictor-range-sensitive." Acknowledging this ambiguity would strengthen the S1 section.

2. **ENIGMA Track A effect size**: The Spearman correlation (ρ = +0.112, p = 0.0019) and quartile prevalence comparison (0.62% → 0.81%, Mann-Whitney p = 0.007) confirm the association's direction in groundwater. However, the fold-enrichment metric — arguably more relevant to the environmental selection hypothesis — is non-significant (ρ = +0.042, p = 0.242). The REPORT attributes this to the prevalence advantage being "already embedded in their global distribution," which is plausible but post-hoc. A reader expecting the validation to show that metal-diverse taxa are *specifically* enriched in metal-impacted groundwater (rather than universally more prevalent) will note this as a limitation of Track A that the REPORT does not fully surface.

3. **CWM coverage in Track B**: The community-weighted mean in Track B is computed from only 16.8% of reads (OTUs with genus-level SILVA taxonomy linkable to AMR data). This is mentioned in the pipeline description but not flagged as a limitation in the Track B interpretation section. If the 83% of uncovered reads come from genera with systematically different metal resistance profiles, the CWM could be biased. A brief sensitivity check (e.g., correlating CWM with the per-sample covered-read fraction) would demonstrate robustness.

**Visualisations**: Well-labelled and publication-quality. The five main figures (fig1–fig5) cover all primary result types: λ heatmap, PGLS forest plot, synthesis, metal-type scatter, and robustness summary. ENIGMA validation has two additional figures and the interactive `dashboard.html` adds exploratory value. One minor gap: `niche_breadth_distribution.png` is listed in the REPORT's figures table but not cross-referenced in the narrative — a sentence pointing to it would help.

---

## Suggestions

1. **Create or remove the `RESEARCH_PLAN.md` link** *(Critical — broken link)*. The README Quick Links section references `RESEARCH_PLAN.md` but the file does not exist. Either create a research plan document (even a brief summary of the pre-analysis hypothesis and power considerations) or remove the link. This will confuse any reader or downstream tool that follows it.

2. **Add an `renv.lock` file for R reproducibility** *(High priority)*. `requirements.txt` covers Python only, and `sessionInfo_r.txt` captures R versions as human-readable text but is not machine-executable for environment reconstruction. Running `renv::snapshot()` in the R session would produce a lockfile that `renv::restore()` can use — this is the R equivalent of `pip install -r requirements.txt`.

3. **Clarify the S1 leave-one-metal-out interpretation** *(Medium)*. Add a sentence in the S1 section acknowledging that loss of significance after removing one metal is consistent with *either* a genuinely distributed signal *or* a predictor near the significance threshold with compressed variance. The consistently positive direction across all seven exclusions supports the distributed interpretation, but this nuance should be stated explicitly.

4. **Flag the Track B CWM coverage gap as a formal limitation** *(Medium)*. The Track B results section should note that CWM is computed from only ~17% of sequenced reads and discuss whether the covered fraction is likely to be representative. A plot of CWM vs. covered-read fraction per sample would be a straightforward diagnostic.

5. **Clarify Track A fold-enrichment result** *(Medium)*. The non-significant fold-enrichment result (ρ = +0.042, p = 0.242) is currently embedded mid-paragraph after the significant prevalence results. Elevating it to a distinct row in the Track A results table with an explicit note that the environmental-specificity metric does not reach significance would be more transparent — and would not undermine the overall validation, since the prevalence correlation is still informative.

6. **Clean up the root directory** *(Low priority)*. The project root contains approximately 15 unlisted intermediate Markdown files (`dir1_ph_interaction_summary.md`, `dir2_commodity_summary.md`, `h1_summary.md`, etc.) that are not described in the README or REPORT. Moving these to a `notes/` or `supplementary/` subdirectory, or listing them in the README, would reduce confusion about which files are primary outputs vs. working notes.

7. **Document `clade_specific_sensitivity.ipynb`** *(Low priority)*. This notebook is present in `notebooks/` but is not listed in the README's notebook table, the data flow, or the REPORT's Supporting Evidence section. Add a one-line entry explaining what it produces, when to run it, and what data it depends on.

8. **Complete Zenodo deposit** *(Aspirational)*. The README notes that `data/dir6_georoc_global_pca.csv` (594 MB) and several figures exceed git file size limits and that a Zenodo DOI is "pending." Completing this deposit would make the analysis fully independently reproducible and provide a citable data artifact.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-05-02
- **Scope**: README.md (72 lines), REPORT.md (1,364 lines), 6 primary notebooks (NB01–NB06) + 1 supplementary notebook, 75+ data files, 30+ figures, requirements.txt, sessionInfo_r.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
