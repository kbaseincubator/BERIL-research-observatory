---
reviewer: BERIL Automated Review
date: 2026-03-19
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an exceptionally ambitious and well-executed project that integrates experimental inhibition assays, carbon utilization profiling, growth kinetics, patient metagenomics, pairwise interaction data, and pangenome analysis to rationally design commensal formulations for competitive exclusion of *P. aeruginosa* in CF airways. The pipeline is comprehensive — 13 notebooks, 35 figures, 21 data files, and a thorough 524-line REPORT.md — and the core finding (a five-organism FDA-safe formulation achieving 100% PA14 niche coverage) is well-supported by multi-layered evidence. The project's greatest strengths are its honest treatment of negative results (no amino acid prebiotics work, CUB is GC-confounded, pairwise interaction data is limited), its staged safety filtering approach, and the pangenome robustness analysis that validates formulation design across hundreds of genomes. The main areas for improvement are the sparse pairwise interaction data (8 comparisons for a 5-species formulation), the *M. luteus* engraftment gap (zero lung genomes, zero patient prevalence), and a few reproducibility gaps around Spark-dependent notebooks.

## Methodology

**Research question**: Clearly stated and testable — the multi-criterion framework for formulation design is well-motivated by the competitive exclusion hypothesis and decomposed into six testable sub-hypotheses (H0–H6). The staged hypothesis structure (metabolic competition → complementary coverage → engraftability → prebiotic boost → pangenome conservation → lung adaptation) creates a logical narrative arc.

**Approach soundness**: The multi-objective optimization framework integrating niche coverage, complementarity, inhibition, engraftability, and safety is well-conceived. The decision to run permissive and strict FDA safety filters in parallel (NB05 vs NB05b) is a smart design choice that transparently shows the cost of clinical viability. The sensitivity analysis across 5 weight schemes converging to the same core formulation strengthens confidence in the result.

**Data sources**: Clearly identified in both README.md and RESEARCH_PLAN.md. The 23-table PROTECT Gold dataset is thoroughly characterized in NB01, with row counts, schema descriptions, and overlap analysis. BERDL databases (pangenome, GapMind, NCBI environment metadata) are used appropriately for validation and extension rather than primary analysis.

**Reproducibility**: The README includes a clear Reproduction section with prerequisites, step-by-step instructions, and Spark/local separation (NB07 and NB09 require BERDL Spark; all others run locally). A `requirements.txt` is provided with versioned dependencies. However, the reproduction guide lists only 10 notebooks (NB01–NB09) while the project contains 13 (NB10–NB12 are omitted). The README Status line says "Eight notebooks executed" but 13 exist with outputs — the README is stale. All 13 notebooks have saved outputs with text, tables, and figures, which is excellent for reviewability.

## Code Quality

**Notebook organization**: All notebooks follow a consistent setup → load → analysis → visualization → save pattern. Markdown cells provide section headers, goal statements, and interpretive commentary. Each notebook clearly identifies its inputs (upstream data files or Spark queries) and outputs (TSV files and figures).

**Statistical methods**: Appropriate and carefully applied. NB03 uses OLS regression with proper cross-validation (5-fold CV R² = 0.145 vs training R² = 0.274), honestly reporting the overfitting gap. Multiple comparison corrections (FDR-BH) are used in NB10–NB11 for pathway differential analysis. Effect sizes are reported alongside p-values throughout. The Kruskal-Wallis test for genus effects (NB03) is appropriate for non-normal inhibition distributions.

**SQL queries**: NB07, NB09, NB10, NB11, and NB12 use Spark SQL for pangenome queries. Queries are well-structured with proper WHERE/GROUP BY clauses. The known pitfall about GapMind `clade_name` matching `gtdb_species_clade_id` format (documented in docs/pitfalls.md) appears to be handled correctly — species are matched using full clade IDs rather than short species names. The `CAST(... AS DOUBLE)` pitfall for Spark DECIMAL columns is addressed where applicable.

**Pitfall awareness**: The RESEARCH_PLAN.md explicitly notes known pitfalls (GapMind genome ID prefix stripping, BacDive metabolite utilization value encoding, protect_genomedepot timeout). The `fact_pairwise_interaction` = `fact_carbon_utilization` identity is discovered and documented in NB08 rather than silently ignored — this is commendable scientific practice.

**Potential issues**:
- The greedy set cover approach for k=4–5 formulations (NB05) may miss globally optimal combinations. For k=3 with 97 candidates (strict safety), exhaustive enumeration of all ~150K triples is feasible and would strengthen the claim that the identified formulation is optimal. The notebook acknowledges this limitation.
- NB12's codon usage bias analysis ultimately finds CUB confounded by GC content (31–73% range across species) and concludes it cannot predict cross-species growth rate differences. This is a correct interpretation, but the notebook could have been omitted or shortened — it contributes a negative result that is already implied by the direct growth data in NB02.
- The *N. mucosa* clade selection issue (noted in REPORT §3.7) — NB07 analyzes `s__Neisseria_mucosa_A` (15 genomes) while the PROTECT isolate maps to `s__Neisseria_mucosa` (8 genomes) — is documented but not resolved in the notebook itself. The sensitivity check showing stronger conservation in the 8-genome clade is reassuring but is presented only in the REPORT, not in the notebook.

## Findings Assessment

**Conclusions supported by data**: The core findings are well-supported:
- Metabolic overlap predicting inhibition (r = 0.384, p = 2.3×10⁻⁶) is statistically robust, and the honest reporting of the CV R² (0.145) alongside training R² (0.274) prevents overclaiming.
- The five-species formulation achieving 100% PA niche coverage at k=3 is directly demonstrable from the carbon utilization data.
- Pangenome conservation (>95% for 4/5 species) across 499 genomes provides genuine translational confidence.
- PA amino acid pathway invariance (97.4% conservation across 1,796 lung genomes) is a strong result supporting formulation robustness.

**Limitations acknowledged**: The REPORT §3.7 provides a thorough limitations section covering planktonic-only assays, limited substrate panel, sparse pairwise data, inferred engraftability, and the `fact_pairwise_interaction` data quality issue. Two additional limitations deserve mention:
- The formulation composite score weights (coverage 30%, complementarity 15%, inhibition 35%, engraftability 20%) are chosen without empirical calibration — the sensitivity analysis shows robustness to weight variation, but the absolute score values are not directly interpretable.
- The 142-isolate core cohort is a subset of 4,949 total isolates — selection bias toward isolates with multiple assay types could affect the generality of the metabolic overlap–inhibition relationship.

**Incomplete analysis**: NB10 and NB11 have substantial overlap in their PA lung adaptation analysis (both perform PCA on lung PA GapMind pathways, both compare CF vs non-CF). Some consolidation would improve clarity. The REPORT mentions "PA strain variation interpretation (accessory genome affects virulence not amino acid growth rate)" in the revision history but this claim, while reasonable, is not directly tested — it is inferred from pathway conservation plus genome size variation.

**Visualizations**: 35 figures are well-labeled with descriptive titles and are referenced inline throughout the REPORT. The progression from EDA (NB01) through mechanistic analysis (NB02–04) to design (NB05–06) to validation (NB07–12) is visually coherent.

## Suggestions

### Critical

1. **Update README.md** to reflect all 13 notebooks, not just the original 8–10. The Status line says "Eight notebooks executed" but 13 exist with outputs. The Reproduction Steps list only NB01–NB09, omitting NB10–NB12. This creates confusion about the project's actual scope.

2. **Address the *M. luteus* engraftment gap more concretely**. This species is the keystone for 100% niche coverage (its addition at k=3 is what closes the substrate gap), yet it has zero patient prevalence and zero lung genomes. The Discussion (§3.2) identifies three paths forward but does not recommend one. Consider either (a) presenting the k=2 formulation (*R. dentocariosa* + *N. mucosa*) as the primary recommendation with k=3 as aspirational, or (b) explicitly recommending a search for a lung-adapted broad-spectrum metabolizer to replace *M. luteus*.

3. **Expand pairwise interaction testing coverage in proposed experiments**. Only 8 pairwise comparisons across 5 unique pairs exist (NB08), while the 5-species formulation has 10 possible pairs. The REPORT correctly flags this as a "critical gap" (§2.10), but Proposed Experiment 4.2 should be elevated to the highest priority — above even sugar alcohol prebiotic validation (4.1) — since antagonistic interactions could invalidate the entire formulation design.

### Important

4. **Consolidate NB10 and NB11**. Both notebooks analyze PA lung adaptation via GapMind pathway PCA, CF vs non-CF comparisons, and metabolic clustering. The overlap is substantial. Merging them into a single "PA Lung Adaptation & Formulation Robustness" notebook would reduce redundancy and strengthen the narrative flow.

5. **Add a data dictionary file**. While individual notebooks document their output columns, a standalone `data/DATA_DICTIONARY.md` mapping each TSV file to its columns, units, and provenance notebook would improve reusability. For example, `formulations_ranked.tsv` has 22,389 rows with composite scores — the column definitions and weight parameterization should be documented outside the notebook.

6. **Document the *N. mucosa* clade resolution in the notebook**. The sensitivity check comparing `s__Neisseria_mucosa_A` (15 genomes) vs `s__Neisseria_mucosa` (8 genomes) is mentioned only in REPORT §3.7 Limitations. Adding this as a cell in NB07 would make the analysis self-contained and reproducible.

### Nice-to-Have

7. **Consider exhaustive enumeration for k=3 strict-safety formulations**. With 97 candidates, C(97,3) ≈ 147,000 — computationally trivial. This would confirm the greedy solution is globally optimal and strengthen the formulation recommendation.

8. **Add a notebook dependency diagram** to the README showing the DAG of data flow (NB01 → NB02/NB03/NB04 → NB05 → NB05b, NB01 → NB07 → NB09, etc.). This would help reproducers understand which notebooks can run in parallel.

9. **Shorten or appendicize NB12** (codon usage bias). The notebook's main conclusion — that CUB is GC-confounded and cannot predict cross-species growth rates — is a negative result already implicit from NB02's direct growth data. It could be reduced to a supplementary analysis or merged into the PA analysis notebooks.

10. **Add confidence intervals to the formulation composite scores**. The current scoring produces point estimates. Bootstrap resampling over the inhibition measurements (which have biological replicates) would provide uncertainty bands that help distinguish genuinely different formulations from scoring noise.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, 13 notebooks, 21 data files, 35 figures, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
