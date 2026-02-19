---
reviewer: BERIL Automated Review
date: 2026-02-19
project: metabolic_capability_dependency
---

# Review: Metabolic Capability vs Metabolic Dependency

## Summary

This is a well-executed project integrating GapMind pathway predictions with Fitness Browser fitness data to distinguish genomic capability from functional dependency. The three-file documentation structure (README / RESEARCH_PLAN / REPORT) is correctly followed, all five notebooks have saved outputs, and figures cover all major analysis stages. The central finding — that 15.8% of complete pathways are functionally neutral "latent capabilities," with carbon-source pathways 3.5× more likely to be latent than amino acid biosynthesis — is a specific and meaningful result grounded in appropriate statistical tests. The main areas for improvement are: (1) RESEARCH_PLAN.md was never updated to reflect the actual NB02 approach after a pivot from gene-link tables to SEED keyword matching; (2) a meaningful partial-support finding for H2 (pangenome openness vs. latent rate, ρ=0.57) is effectively buried under a "Not Supported" headline; and (3) a few methodological details — the NB02 organism-matching failure, four pathways with no SEED coverage, and a missing row count for one data file — are undocumented in the report.

## Methodology

**Research question and hypotheses** are sharply stated and testable. The three-hypothesis structure (H1: capability ≠ dependency; H2: Black Queen conservation prediction; H3: metabolic ecotypes) maps cleanly onto four analysis notebooks, and explicit success criteria in RESEARCH_PLAN.md make it possible to evaluate whether the analysis reached its goals. H1 exceeds its minimum threshold (15.8% latent > 10% target; χ²=144.1, p=3.7×10⁻³⁰); H3 is met for all 10 target species.

**Approach soundness**: The core analytical idea — using SEED subsystem keywords as a proxy to map GapMind pathway members to Fitness Browser genes — is pragmatic and generally reasonable for amino acid biosynthesis pathways where SEED roles are well-named. It is weaker for carbon-source pathways and cofactor biosynthesis where SEED role names are more heterogeneous. The REPORT.md Limitations section identifies this honestly.

**Pivot in NB02 not reflected in RESEARCH_PLAN.md**: The Research Plan (§Phase 1, NB02) describes loading `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` and performing a direct gene-to-fitness join. The actual implementation abandoned this in favor of SEED keyword matching, and the README.md notes the change with a one-paragraph explanation. However, RESEARCH_PLAN.md itself was never updated. A reader consulting RESEARCH_PLAN.md for context will encounter an approach that was not executed. The plan should be updated to describe the actual NB02 method.

**Data sources** are clearly identified and the provenance of each output file is traceable to a specific notebook. The `gapmind_pathways` query correctly applies the known pitfall fix (MAX score per genome-pathway pair, with numeric scoring of `complete`=5 through `not_present`=1).

## Code Quality

**SQL correctness**: The NB01 GapMind extraction query correctly handles the documented multi-row-per-genome-pathway structure by grouping on `(genome_id, species, pathway)` and taking `MAX(score_value)`. This is the most consequential SQL correctness issue in the project and it is handled properly. The NB02 Fitness Browser aggregate query (`AVG(ABS(t))`, `MAX(ABS(t))`, `percentile_approx`) is syntactically correct, and all numeric comparisons are applied to pre-aggregated float values so no explicit CAST is required in practice.

**Essential gene handling**: NB02 correctly infers putative essential genes as protein-coding genes (type='1') absent from `genefitness`, directly addressing the documented pitfall that genefitness-only analyses miss ~14% of genes. These are included in pathway-level fitness metrics via a separate `n_essential` / `pct_essential` column. This is a notable strength.

**`src/pathway_utils.py`**: The module is well-documented with NumPy-style docstrings, has reasonable type annotations, and is used consistently by NB02, NB03, and NB05. The `classify_pathway_dependency()` function handles NaN gracefully. One subtlety: when `mean_abs_t` is NaN but `pct_essential` is defined (or vice versa), the function assigns `latent_capability` if the non-NaN metric is below its threshold — which could misclassify pathways that are "latent" only because fitness data is absent (no transposon coverage), not because genes are truly neutral.

**Four pathways have no SEED matches**: `phenylalanine`, `tyrosine`, `deoxyribonate`, and `myoinositol` had zero matching SEED roles in NB02 and are therefore absent from all downstream dependency classification. Phenylalanine and tyrosine are named amino acids, and their exclusion from the amino acid biosynthesis category breakdown is not documented in the report. The RESEARCH_PLAN listed 15 amino acid pathways; the final breakdown table covers fewer without explanation.

**Threshold sensitivity analysis**: The active/latent classification thresholds (mean |t| > 2.0 for active, < 1.0 for latent; pct_essential > 20% / < 5%) are applied uniformly across all organisms without sensitivity analysis. The intermediate zone (32.3% of records) is large enough that moderate threshold changes could materially shift the latent and active fractions. No justification for the specific numeric cutoffs is provided in the notebook or report.

**NB02 organism mapping**: An attempt to match Fitness Browser organisms to GapMind clades via NCBI taxonomy IDs from `kbase_ke_pangenome.gtdb_metadata` returned 0 of 48 matches, because the relevant column returned `"t"`/`"f"` boolean strings rather than numeric taxids. The notebook correctly detected the failure and pivoted to a simpler `orgId`-based approach for the fitness aggregation step. However, the mapping failure and its implications are not mentioned in the REPORT.md Limitations section, leaving readers without context for why organism-to-clade links are absent from the classification data.

**Notebook organization**: All notebooks follow a consistent `Setup → Query/Load → Process → Visualize → Save` structure. NB01–NB02 are the Spark-requiring notebooks; NB03–NB05 are local. This separation is documented in README.md and respected in the implementations.

**Pitfalls compliance summary**:
| Pitfall | Status |
|---|---|
| GapMind multi-row-per-pair (take MAX score) | ✓ Correctly handled in NB01 |
| Essential genes invisible in genefitness-only analyses | ✓ Explicitly handled in NB02 |
| String-typed numeric columns in fitness browser | ✓ Not an issue (aggregation in SQL; Python comparisons on floats) |
| Spark vs local import patterns | ✓ Correctly documented and separated |
| `toPandas()` on large tables | ✓ Avoided; aggregations done in Spark before collection |

## Findings Assessment

**H1 (latent capabilities exist)**: Well supported. The χ² result (p=3.7×10⁻³⁰) is convincing, the pathway-category breakdown table is internally consistent (totals check out), and the visualizations (stacked bar, scatter with decision boundaries) are appropriate. The headline finding — carbon-source pathways 3.5× more likely to be latent than amino acid biosynthesis — is a specific, testable, and novel claim.

**H2 (Black Queen conservation)**: The REPORT.md Key Findings heading reads "H2 Not Supported," but the section reports two distinct sub-tests:
1. Conservation rate by dependency class: Not supported (Mann-Whitney p=0.94; medians identical at 100%)
2. Latent capability rate vs. pangenome openness: Supported (Spearman ρ=0.57, p=0.0005, n=33 species)

The second result is meaningful and consistent with the Black Queen Hypothesis at a different level of analysis (species-level genomic dynamics rather than pathway-level conservation), but it is buried in the Interpretation section and does not appear in the Key Findings table. The headline should reflect partial support, e.g., "H2 Mixed: Pathway-Level Conservation Not Differentiated; Pangenome Openness Positively Correlated with Latent Rate."

**H3 (metabolic ecotypes)**: Supported in all 10 target species (silhouette > 0.2). The Salmonella result (silhouette=0.89, χ²=1570, p≈0) is particularly striking. The honest acknowledgment that marine oligotrophs do not show significant environment-cluster associations — with plausible explanations offered — reflects good scientific judgment.

**Limitations**: The limitations section is substantive and accurate. The SEED-proxy noise, lab-condition bias, and coarse conservation measurement are all correctly identified. One additional limitation that should be noted: the organism-to-clade taxonomy matching failure in NB02, which means that while pathway fitness metrics were computed for all 48 FB organisms, the explicit species-level link between fitness-tested organisms and pangenome clades is absent, potentially limiting the strength of H2a.

**`pathway_cluster_signatures.csv`** is listed in the REPORT.md data table with "—" for row count. This appears to indicate the file was generated but the row count was not filled in, or the file may be incomplete. This should be resolved.

## Suggestions

1. **Update RESEARCH_PLAN.md to describe the actual NB02 implementation.** Replace the fb_pangenome_link.tsv approach with the SEED keyword matching approach currently documented in the README. A reader consulting the plan should see what was actually done, not the abandoned approach.

2. **Revise the H2 Key Findings header to reflect partial support.** The pangenome openness correlation (ρ=0.57, p=0.0005) is a substantive positive result that supports the Black Queen framework at the species level. Elevating this from the Interpretation section to the Key Findings heading (e.g., "H2 Mixed: Conservation Undifferentiated; Pangenome Openness Correlated with Latent Rate") would give it the visibility it merits.

3. **Document the four missing SEED-pathway matches in the report.** Phenylalanine and tyrosine are named amino acid pathways that should appear in the amino acid biosynthesis category. Their absence due to no SEED keyword hits reduces the stated pathway count in that category. Add a sentence in the Methods/Results section: "Four pathways (phenylalanine, tyrosine, deoxyribonate, myoinositol) had no SEED role matches and were excluded from dependency classification."

4. **Add a note about the NB02 taxonomy matching failure to the Limitations section.** A single sentence suffices: "An attempt to match FB organisms to GapMind species clades via NCBI taxonomy IDs returned zero matches due to an unexpected column format in `gtdb_metadata`; downstream analyses use organism-level fitness aggregates without explicit clade-level linkage."

5. **Fill in the row count for `pathway_cluster_signatures.csv`** in the REPORT.md data table, or remove the row if the file is empty/not used.

6. **Add a brief threshold sensitivity analysis in NB03.** Even a 2×2 table showing how the latent fraction changes with ±25% variation in the |t|-score thresholds (e.g., 1.5 vs. 2.0 vs. 2.5 for active) would substantially strengthen the classification robustness. Given the large intermediate zone (32.3%), readers will reasonably wonder how sensitive the headline 15.8% latent fraction is to threshold choice.

7. **Consider splitting H2 into two sub-hypotheses in the report.** H2a (pathway-level conservation) and H2b (pangenome openness) test different aspects of the Black Queen Hypothesis at different analytical levels. Presenting them as separate sub-hypotheses with separate conclusions would clarify the mixed result and make the positive openness finding easier for readers to locate.

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, src/pathway_utils.py, 5 notebooks, 17 data files, 12 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
