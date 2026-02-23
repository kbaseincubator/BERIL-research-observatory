---
reviewer: BERIL Automated Review
date: 2026-02-22
project: ecotype_species_screening
---

# Review: Ecotype Species Screening

## Summary

This is a well-designed upstream screening project that fills a genuine gap in prior BERIL ecotype work: rather than selecting species by AlphaEarth coverage, it systematically ranks all 338 species with phylogenetic tree data across three independent, biologically motivated dimensions. The research question is clear, the hypotheses are testable, the scoring logic is sound, and the findings are grounded in real statistical tests with honest limitations acknowledged. The use of two new BERDL data elements (`phylogenetic_tree_distance_pairs` and `nmdc_ncbi_biosamples.env_triads_flattened`) is well-executed, and the project correctly identifies and avoids two known pitfalls — the EAV format of `env_triads_flattened` and the `spark.createDataFrame()` version mismatch — both of which are now documented in `docs/pitfalls.md`. The main weaknesses are: (1) the Reproduction section of README.md was never filled in despite the analysis being complete; (2) NB01 and NB03 have no saved cell outputs, making it impossible to verify data extraction or retrospective validation statistics without re-running; and (3) a unit labeling error in REPORT.md (entropy values reported as "nats" but computed in bits). These are concrete, fixable gaps rather than fundamental methodological problems.

---

## Methodology

**Research question**: Clearly stated and operationally defined. The three scoring dimensions (phylogenetic substructure, environmental diversity, pangenome openness) are individually justified by literature (Maistrenko 2020, Von Meijenfeldt 2023, Cohan 2002) and mutually independent (all pairwise |rho| < 0.2 confirmed in NB02 Cell 8). The retrospective validation design — comparing composite score against prior ecotype signal from `ecotype_analysis` — is a strong methodological choice that grounds the screening in an independent empirical benchmark.

**H1 direction**: The research plan (RESEARCH_PLAN.md, Hypothesis section) states H1 as: *"Species with high phylogenetic substructure have higher environmental diversity."* This predicts a **positive** correlation. The observed Pearson r = −0.171 (p = 0.003) is **negative** — the opposite direction. The REPORT's Finding 1 states "H1 is supported," which is technically misleading: H0 (no correlation) is rejected, but the stated H1 direction is not observed. The report's interpretation of two complementary candidate profiles is ecologically coherent and valuable, but the claim of H1 support should be qualified as "H0 rejected; observed direction opposite to H1." This does not affect the composite scoring value — the negative correlation actually *strengthens* the case for combining both dimensions — but the framing needs correction.

**Data sources**: All tables and their join strategies are clearly documented in RESEARCH_PLAN.md. The cross-project dependency on `ecotype_analysis/data/ecotype_correlation_results.csv` is explicitly declared.

**Reproducibility**: Partially addressed. Minimum genome threshold (≥20) is stated in the plan but the actual analysis includes all 338 species without filtering — the minimum filter is apparently not applied in NB02. This discrepancy should be noted or the plan updated.

---

## Code Quality

**NB01 (`01_data_extraction.ipynb`)**: Well-structured. The entropy calculation (NB01, Cell 12) uses `np.log2`, which produces values in **bits**. However, REPORT.md (Results → Scoring Dimensions table) labels the unit as **"nats"** and states "env_broad_scale entropy (nats)." Nats require `np.log` (natural log). The computed values in NB02 Cell 2 (`mean = 1.447`, `max = 3.62`) are consistent with log2-based bits, not nats — nats would produce smaller values for the same distributions. The REPORT's unit label is incorrect. This affects the reported range "0 – 3.62" and the mean "1.447 ± 0.952" but not the relative rankings, since z-scoring removes absolute scale. The unit error should be corrected in the report (either change the label to "bits" or change `np.log2` to `np.log` in NB01 Cell 12).

**NB01 Cell 12** also contains a minor floating-point artifact: the entropy function uses `np.log2(probs + 1e-12)` to avoid `log(0)`, which can produce a very slightly negative entropy for near-zero probability inputs. This is visible in NB02 Cell 2's describe output: `env_broad_entropy min = -1.44e-12`. The artifact is numerically inconsequential but could confuse downstream users.

**NB02 (`02_composite_scoring.ipynb`)**: Clean and logically organized (load → merge → score → test → visualize). The z-scoring with outlier clipping (`clip=5`) appropriately handles the strongly right-skewed CV distribution driven by *Prochlorococcus* (CV = 5.84). The Fisher's exact test in Cell 6 is correctly specified as one-sided (`alternative='less'`). Statistical tests report both Pearson and Spearman correlations with p-values.

**NB03 (`03_retrospective_validation.ipynb`)**: The merge logic for joining prior results (Cell 2) uses `errors='ignore'` in `drop(columns=...)`, which silently handles potential column name conflicts — acceptable here but worth noting. The figure (Cell 4) plots `cv_branch_dist` vs `r_ani_jaccard` in Panel A, but Panel B switches to `composite_score` vs `r_ani_jaccard` rather than the more relevant `r_partial_emb_jaccard` — the REPORT correctly describes Panel B as showing the partial correlation metric, but the figure code (Cell 4) uses `r_ani_jaccard` for both panels. This inconsistency between the figure code and the REPORT description should be verified.

**Pitfall awareness**: Two pitfalls from `docs/pitfalls.md` that directly apply to this project are properly handled:
- `[ecotype_species_screening] env_triads_flattened is EAV format` — correctly uses `WHERE t.attribute = 'env_broad_scale'` and references `t.label` (NB01 Cells 11–12).
- `[ecotype_species_screening] spark.createDataFrame() fails via Spark Connect` — correctly replaced with SQL subqueries using `WHERE ... IN (SELECT ... FROM phylogenetic_tree)` (NB01 Cell 10).

The ID prefix pitfall (`[cofitness_coinheritance] Phylo distance genome IDs lack GTDB prefix`) is acknowledged in NB01 Cells 4–5 with explicit verification logic, which is the correct approach.

**`01b_env_extraction_continuation.py`**: This script is listed in README.md and REPORT.md as part of the pipeline but has no accompanying explanation of when or why it is needed, what inputs it requires, what outputs it produces, or how its outputs relate to those from NB01. Without this context it is unverifiable. The README lists it as "Env diversity continuation script (local Spark)" but provides no further detail.

---

## Findings Assessment

**Supported conclusions**: The top-10 candidate table is internally consistent with the scoring methodology, and the face-validity check (ranks #1 *Prochlorococcus*, which is the canonical bacterial ecotype exemplar) is a strong positive signal. The claim that composite score predicts prior partial-correlation ecotype signal (rho = 0.277, p = 0.010, N = 99) is supported by the NB02 output. The H3 Fisher's test result (OR = 1.45, p = 0.937) is correctly interpreted: prior species selection was not systematically biased against high-scorers.

**H2 interpretation nuance**: The REPORT states "H2 is partially supported" and correctly notes branch CV alone does not reach significance (rho = 0.153, p = 0.130). The composite score predicts `r_partial_emb_jaccard` (the ecotype signal metric), which does support multi-dimensional screening. However, the original H2 hypothesis ("branch distance variance is a **stronger predictor** than ANI variance") is not directly tested — there is no AUC or head-to-head comparison between branch CV and ANI-based proxy. The retrospective validation as implemented is weaker than what the research plan described.

**Clinical/host confounders**: The report correctly flags that *Staphylococcus epidermidis* (rank 5, 1,315 genomes) and *Francisella tularensis* (rank 6, 852 genomes) may reflect immune-evasion diversification rather than ecotype formation, but no host-association filter was applied. Separately, the singleton fraction metric is acknowledged to be biased by genome count (more genomes → more singletons), and both *S. epidermidis* and *Listeria monocytogenes* B (rank 8, 1,923 genomes) are among the largest species in the dataset. The magnitude of this bias on composite rankings is not assessed and could be substantial.

**N=99 overlap**: Only 99 of 213 prior `ecotype_analysis` species (46%) appear in the 338-species tree universe. The reason for this gap is never explained. Understanding whether the 114 absent species simply lack phylogenetic tree data (the most likely explanation) or were excluded for other reasons would help interpret the retroactive validation scope.

**References**: One reference DOI is incorrect. In `references.md`, the Kettler et al. (2007) *PLoS Genet* paper has `DOI: 10.1128/AEM.02545-17` — this is an Applied and Environmental Microbiology format DOI from 2017, not a PLoS Genetics DOI from 2007. The correct DOI is `10.1371/journal.pgen.0030231`. Additionally, Dewar et al. (2024, *PNAS*) is cited in RESEARCH_PLAN.md but does not appear in `references.md` or the REPORT.md References section.

---

## Suggestions

1. **[Critical] Fill in the Reproduction section of README.md.** The analysis is complete and dated 2026-02-22, but `## Reproduction` still reads "TBD — add after analysis is complete." At minimum, document: which notebooks require BERDL JupyterHub, which run locally, what the expected execution order is (NB01 → 01b → NB02 → NB03), and what outputs each step produces. Clarify the role of `01b_env_extraction_continuation.py` — what triggered it, what it reads and writes, and how its output integrates with NB01's output.

2. **[Critical] Execute NB01 and NB03 and save outputs before final archival.** NB01 (data extraction) has no cell outputs at all — a reader cannot verify the Spark queries ran or see any of the intermediate data previews. NB03 (retrospective validation) similarly has no outputs, meaning the H2 statistics in the REPORT cannot be confirmed from the notebook alone. Per the documented pitfall `[env_embedding_explorer]`, notebooks without outputs are not useful for review. Use `jupyter nbconvert --to notebook --execute --inplace` or re-run Kernel → Restart & Run All, then commit with outputs. Note: NB01 requires JupyterHub; NB03 is local and can be run immediately.

3. **[High] Correct the entropy unit in REPORT.md.** The scoring dimensions table reports "nats" but NB01 Cell 12 computes entropy using `np.log2`, which produces **bits**. Either update the REPORT to say "bits" (easier) or change `np.log2` to `np.log` in NB01 Cell 12 (changes absolute values, not rankings). Be consistent in all references to entropy values.

4. **[High] Clarify H1 framing.** RESEARCH_PLAN.md defines H1 as predicting a *positive* correlation between phylogenetic substructure and environmental diversity. The observed r = −0.171 is significant but *negative*. The REPORT's Finding 1 should state: "H0 (no correlation) rejected; however, the observed direction is negative, contrary to the positive direction stated in H1." The ecological interpretation that follows is sound and should be preserved, but the initial "H1 is supported" claim is technically inaccurate.

5. **[Moderate] Verify Panel B of the H2 figure.** In NB03 Cell 4, Panel B plots `composite_score` vs `r_ani_jaccard`, but the REPORT describes Panel B as showing composite score vs `r_ani_jaccard` (which is consistent) yet the figure caption says "Right: Composite score vs r_ani_jaccard (rho=-0.37, p<0.001). High composite score species have gene content less coupled to ANI phylogeny." — this is internally consistent. However, the REPORT also reports a *separate* positive correlation between composite score and `r_partial_emb_jaccard` (rho = 0.277, p = 0.010) that does not appear to be visualized. Consider adding a third panel or a supplementary figure showing composite vs `r_partial_emb_jaccard`, since this is the key metric validating the screening approach.

6. **[Moderate] Quantify the singleton fraction genome-count bias.** The report flags this limitation but does not assess its magnitude. A brief sensitivity check — recomputing composite scores after regressing out `log(no_genomes)` from `singleton_fraction` — would clarify whether high-genome-count species (*S. epidermidis*, *L. monocytogenes* B, *E. hormaechei* A) owe their rankings primarily to biological signal or sequencing depth artifact. This analysis is straightforward locally with the existing `species_scored.csv`.

7. **[Moderate] Fix the Kettler 2007 DOI and add the Dewar 2024 reference.** In `references.md`: (a) correct `DOI: 10.1128/AEM.02545-17` to `DOI: 10.1371/journal.pgen.0030231` for Kettler et al. 2007; (b) add the full citation for Dewar et al. (2024) *PNAS* which is cited in RESEARCH_PLAN.md but missing from both `references.md` and the REPORT References section.

8. **[Minor] Explain the N=99/213 overlap gap.** Briefly note in the Limitations section of REPORT.md why only 99 of the 213 prior `ecotype_analysis` species appear in the 338-species tree universe — most likely that the remaining 114 species lack phylogenetic tree data in `kbase_ke_pangenome` (i.e., they were in the prior analysis for AlphaEarth coverage reasons but have no single-copy core gene tree). This context helps readers interpret the scope of the H2 retrospective comparison.

9. **[Minor] Address the minimum genome filter discrepancy.** RESEARCH_PLAN.md specifies "Minimum 20 genomes per species" as a filter, but NB02 includes all 338 species without applying this filter. Either apply the filter (which may remove a small number of species) or update the plan to document why the filter was omitted. The current data (`species_pangenome_stats.csv`) contains genome counts, so filtering is straightforward if desired.

10. **[Minor] Add `seaborn` or `statsmodels` to `requirements.txt` if needed by 01b.** The current `requirements.txt` covers NB02 and NB03 dependencies (`numpy`, `pandas`, `scipy`, `matplotlib`). If `01b_env_extraction_continuation.py` uses additional libraries, they should be listed. More broadly, `pyspark` is implicitly required for NB01 but is not in `requirements.txt` (since it is provided by the JupyterHub environment — this is acceptable but worth noting in the Reproduction section).

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-22
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 3 notebooks (01_data_extraction.ipynb, 02_composite_scoring.ipynb, 03_retrospective_validation.ipynb), 1 Python script (01b_env_extraction_continuation.py), 8 data files, 4 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
