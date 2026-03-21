---
reviewer: BERIL Automated Review
date: 2026-03-21
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is a remarkably thorough and well-structured project that integrates six distinct data modalities — planktonic inhibition assays, carbon source utilization, growth kinetics, patient metagenomics, pairwise interaction data, and pangenome analysis — to rationally design commensal formulations for competitive exclusion of *P. aeruginosa* in CF airways. The 12-notebook pipeline produces 35 figures and 21 data files, culminating in a concrete, actionable output: a ranked set of FDA-safe formulations with quantified confidence intervals and pangenome-validated robustness. The REPORT.md is written at a high standard, with a clear narrative arc from problem statement through mechanistic analysis to translational recommendations. The project's greatest strengths are (1) the honest, quantitative treatment of what metabolic competition can and cannot explain (R² = 0.274 training, 0.145 CV), (2) the staged safety filtering that transparently shows the cost of clinical viability, (3) the pangenome robustness analysis demonstrating that formulation targets are invariant across 1,796 lung PA genomes, and (4) the mature discussion of the *M. luteus* engraftment tension with a concrete k=2 vs k=3 recommendation. The main areas for improvement are minor text errors in the REPORT, a row-count discrepancy in one data file, and a stale reference in the data dictionary. This is a strong project that reads as a near-complete translational blueprint for experimental follow-up.

## Methodology

**Research question and hypotheses**: The central question is clearly stated, testable, and decomposed into six well-motivated sub-hypotheses (H0–H6) that build on each other logically. The progression from "does metabolic overlap predict inhibition?" (H1) through "do combinations outperform singles?" (H2) to "are these results robust across the species pangenome?" (H5) creates a natural escalation of confidence. The null hypothesis (H0: inhibition is driven by direct antagonism alone) is properly framed and partially rejected with quantitative support.

**Approach soundness**: The multi-objective optimization framework is well-conceived. The five scoring criteria (niche coverage, complementarity, inhibition, engraftability, safety) capture the key dimensions of a translatable formulation. The dual-pass safety filtering (permissive NB05 vs strict NB05b) is a particularly smart design choice — it shows the reader exactly which organisms are lost and what inhibition ceiling is sacrificed when applying clinically realistic constraints. The exhaustive enumeration of all 147,440 k=3 triples confirming the greedy optimum, and the bootstrap confidence intervals showing k=2–5 are statistically indistinguishable, are strong additions that move the analysis from "plausible" to "rigorous."

**Data sources**: Clearly documented in README.md, RESEARCH_PLAN.md (§Data Sources), and REPORT.md (§5). The 23-table PROTECT Gold dataset is thoroughly characterized with row counts and roles. BERDL databases are used appropriately for validation and extension (pangenome conservation, environmental metadata, GapMind predictions) rather than as primary evidence. The bridge between experimental isolates and pangenome genomes via reference genome accessions is carefully managed, including prefix-stripping (RS_/GB_) as documented in docs/pitfalls.md.

**Reproducibility**:
- **Notebook outputs**: All 12 notebooks have been executed with saved outputs — text, tables, and figures are preserved in every code cell. This fully meets the hard requirement for committed outputs and means the project is reviewable without re-running any code.
- **Figures**: 35 figures in `figures/` cover every analysis stage: EDA (10 figures from NB01), growth kinetics (4 from NB02), inhibition modeling (4 from NB03), patient ecology (1 from NB04), formulation optimization (3 from NB05/05b), prebiotic analysis (1 from NB06), pangenome conservation (2 from NB07), interaction modeling (2 from NB08), genomic extension (1 from NB09), PA adaptation (6 from NB10), and growth rate prediction (1 from NB12). Coverage is excellent.
- **Dependencies**: `requirements.txt` lists 10 packages with minimum versions. PySpark and `berdl_notebook_utils` are noted as BERDL JupyterHub prerequisites in the README.
- **Reproduction guide**: The README includes a Reproduction section with prerequisites, a notebook dependency DAG showing parallel branches, clear identification of which notebooks require Spark (NB07, NB09, NB10), and estimated runtimes (< 2 min local, 5–10 min Spark).
- **Spark/local separation**: Clean. Nine notebooks run locally from cached parquet files and upstream TSV outputs. Three notebooks (NB07, NB09, NB10) require BERDL Spark access for pangenome queries. This is well-documented.
- **Data dictionary**: `data/DATA_DICTIONARY.md` provides per-file documentation with source notebook, row counts, and column-level metadata. This is a significant aid to reproducibility.

## Code Quality

**Notebook organization**: All 12 notebooks follow a consistent pattern: imports and setup → data loading → analysis → visualization → output saving → summary. Markdown cells provide section headers, goal statements, and inline interpretation. Each notebook header identifies inputs and outputs. The code is clean, uses descriptive variable names, and applies pandas/scipy/sklearn idiomatically.

**Statistical methods**: Appropriate and carefully applied throughout:
- NB03: OLS regression with proper 5-fold cross-validation, honest reporting of the train-CV gap (0.274 vs 0.145). Kruskal-Wallis for genus effects is appropriate for non-normal distributions.
- NB05b: Bootstrap CIs (1,000 resamples) on composite scores and exhaustive combinatorial enumeration.
- NB10: Mann-Whitney U tests with FDR correction (Benjamini-Hochberg) for pathway differential analysis, PCA with KMeans clustering (k=2, silhouette=0.95) for PA subpopulation identification.
- Effect sizes are reported alongside p-values throughout — a commendable practice.

**SQL queries**: NB07, NB09, and NB10 use Spark SQL for pangenome queries. Queries are well-structured with proper `GROUP BY`, appropriate `CAST(... AS DOUBLE)` for Spark DECIMAL columns (per docs/pitfalls.md), and `WHERE` filtering by `gtdb_species_clade_id` rather than LIKE patterns. The GapMind `clade_name` format pitfall is handled correctly.

**Pitfall awareness**: The project addresses multiple documented pitfalls: GapMind genome ID prefix stripping (NB07), Spark DECIMAL column casting (NB09, NB10), `ncbi_env` EAV format pivot (NB07, NB10). The discovery that `fact_pairwise_interaction` is identical to `fact_carbon_utilization` (correlation = 1.0, NB08) is properly documented and reported as a limitation rather than silently worked around.

**Notable code quality decisions**:
- NB05b's exhaustive k=3 enumeration with a species-uniqueness constraint is well-implemented.
- NB07's clade sensitivity check for *N. mucosa* (comparing 15-genome vs 8-genome clades) adds important validation directly in the notebook.
- NB10's consolidation of the former NB10+NB11 into a single coherent notebook with 7 sections is well-organized.

**Minor issues identified**:
- NB03 cell-18: The permissive safety filter includes `Pseudomonas` but not `Pseudomonas_E`, allowing *P. juntendi* into the top candidates list. This is by design (the strict filter catches it in NB05b), but a brief comment in the code noting this is intentional would prevent reader confusion.

## Findings Assessment

**Conclusions well-supported by data**:
- The metabolic overlap–inhibition correlation (r = 0.384, p = 2.3×10⁻⁶) is statistically robust, and the conservative CV R² (0.145) prevents overclaiming. The identification of "dual-mechanism" species that combine metabolic competition with direct antagonism (§2.3) is a valuable insight grounded in the residual analysis.
- The five-species formulation achieving 100% PA niche coverage at k=3 is directly verifiable from carbon utilization data.
- PA amino acid pathway conservation (97.4% across 1,796 lung genomes, §2.13) is a strong result. The finding that CF vs non-CF lung PA show zero amino acid pathway differences is compelling for translational generalizability.
- The sugar alcohol prebiotic discovery (§2.11) — six pathways complete in commensals and absent in PA — is well-supported by both GapMind predictions and patient metatranscriptomics.
- The *M. luteus* engraftment discussion (§3.2) honestly confronts the fundamental design tension and arrives at a concrete, well-reasoned recommendation (k=2 as primary candidate).

**REPORT narrative quality**: The REPORT reads well for a scientific audience unfamiliar with the project. The Introduction establishes the CF clinical problem, the competitive exclusion design theory, and the multi-stage study design within three pages. Each Results subsection opens with a "Rationale" that explains *why* the analysis was done (not just what was done), making the logical flow easy to follow. The Discussion synthesizes the findings into a multi-mechanism model (§3.1), confronts the M. luteus engraftment question directly (§3.2), and places results in literature context (§3.5) with relevant citations. The Proposed Experiments (§4) are ordered by priority and include clear rationale and expected outcomes — this section reads as a genuine experimental roadmap, not an afterthought.

**Limitations honestly acknowledged**: Section 3.7 is thorough, covering planktonic assay limitations, the 22-substrate constraint, sparse pairwise data, inferred engraftability, the `fact_pairwise_interaction` data quality issue, and the *N. mucosa* clade selection. The CUB/GC confound (NB12) is presented as a negative result rather than hidden.

**Internal consistency issues**:
- REPORT §3.1 contains two duplicated phrases: "additional an additional 9%" (line 331) and "The remaining the remaining 64%" (line 335). These appear to be editing artifacts.
- The `formulations_strict_safety.tsv` file contains 146,379 data rows, but the DATA_DICTIONARY reports 22,515 rows and the REPORT §5 table reports 25,731. This discrepancy likely reflects the exhaustive k=3 enumeration added in the review response — the file grew substantially but the documentation was not fully updated. This should be reconciled.
- The DATA_DICTIONARY lists `pa_target_robustness.tsv` as sourced from "NB11 — `11_pa_within_lung_diversity.ipynb`", but NB11 was consolidated into NB10 during the review response. The source notebook reference should be updated.
- The REPORT §5 table lists `pa_target_robustness.tsv` with 24 rows, but `wc -l` shows 23 (22 data rows + header). A minor off-by-one.

**Visualization quality**: The 35 figures are well-labeled with descriptive titles, axis labels, and legend entries. The numbered prefix system (01_, 02_, ...) makes figures easy to trace to their source notebooks. Key figures are embedded inline throughout the REPORT with contextual captions.

## Suggestions

### Critical (factual/consistency errors)

1. **Fix duplicated phrases in REPORT §3.1**: Line 331 reads "additional an additional 9%" — should be "an additional 9%". Line 335 reads "The remaining the remaining 64%" — should be "The remaining 64%". These are copy-editing errors that undermine an otherwise polished narrative.

2. **Reconcile `formulations_strict_safety.tsv` row count**: The file contains 146,379 data rows (reflecting both greedy-search and exhaustive k=3 enumeration results), but the DATA_DICTIONARY reports 22,515 and the REPORT §5 table reports 25,731. Update both documents to reflect the actual file contents, and consider adding a note explaining the two result sets within the file (e.g., a `method` column distinguishing greedy vs exhaustive results, or separate files).

3. **Update DATA_DICTIONARY `pa_target_robustness.tsv` source**: Currently references "NB11 — `11_pa_within_lung_diversity.ipynb`" which was deleted and consolidated into NB10 (`10_pa_lung_adaptation.ipynb`).

### Important (strengthening the analysis)

4. **Clarify the k=2 → k=3 niche coverage jump in the REPORT**: The formulation table (§2.6) shows coverage jumping from 18% at k=2 to 100% at k=3. This is a dramatic transition that deserves a sentence explaining which specific substrates *M. luteus* covers that *N. mucosa* and *R. dentocariosa*/*S. salivarius* do not. This would help the reader understand why *M. luteus*'s broad metabolic profile is so critical.

5. **Add a brief note on GTDB taxonomy conventions**: The project uses GTDB taxonomy throughout (e.g., *Pseudomonas_E*, *Serratia_J*, *Bacillus_A*). A one-sentence note in the REPORT Introduction or Methods explaining that species names follow GTDB conventions (which differ from NCBI taxonomy) would help readers unfamiliar with the naming system. This is especially relevant for the clinical audience who may not recognize *Pseudomonas_E juntendi* as a non-aeruginosa Pseudomonas.

6. **Consider noting selection bias in the 142-isolate cohort**: The core analysis cohort (142 isolates with both inhibition and carbon utilization data) is a subset of 4,949 total isolates. While this is acknowledged implicitly, a brief note in §3.7 Limitations about whether this subset is taxonomically representative of the full collection would strengthen the methodology. NB01's data overlap figure addresses this visually but a quantitative statement would help.

### Nice-to-Have

7. **Add a comment in NB03 about the permissive safety filter design**: The top-20 candidate list (cell 18) includes *Pseudomonas_E juntendi* and *Leclercia adecarboxylata* because the permissive filter excludes `Pseudomonas` but not `Pseudomonas_E`. A brief code comment noting this is intentional (the strict filter in NB05b catches these) would prevent reader confusion.

8. **Reconcile `pa_target_robustness.tsv` row count**: The REPORT says 24 rows, but the actual file has 22 data rows. Minor but worth fixing for consistency.

9. **Consider a summary figure**: A single "graphical abstract" figure showing the pipeline from data integration through formulation design to pangenome validation — possibly as the first figure in the REPORT — would help readers quickly grasp the project's scope and logic before diving into details.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-21
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, DATA_DICTIONARY.md, 12 notebooks, 21 data files, 35 figures, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
