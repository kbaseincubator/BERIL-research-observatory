---
reviewer: BERIL Automated Review
date: 2026-02-22
project: ecotype_species_screening
---

# Review: Ecotype Species Screening

## Summary

This is an exemplary upstream screening project that fills a genuine gap in prior BERIL ecotype work. Rather than selecting species by AlphaEarth coverage, it systematically ranks all 338 species with phylogenetic tree data across three independent, biologically motivated dimensions — phylogenetic substructure (CV of branch distances), environmental diversity (Shannon entropy of ENVO-harmonized env_broad_scale), and pangenome openness (singleton fraction). The documentation is excellent: the three-file README/RESEARCH_PLAN/REPORT structure is complete and coherent, hypotheses are stated with explicit null and alternative forms, and the Limitations and Future Directions sections are candid and specific. Spark best practices are followed throughout — aggregations are pushed to the cluster and only small summary frames are collected. The code correctly handles two non-trivial data engineering challenges (EAV-format `env_triads_flattened`, Spark Connect `createDataFrame()` incompatibility), both now documented in `docs/pitfalls.md`. Face validity is strong: *Prochlorococcus* A, the canonical bacterial ecotype example, ranks first. The main concerns are a factual N inconsistency in the REPORT H2 results table (three different values appear for the same comparison across the document), a variable mislabel in one figure caption, a broken cross-reference to a non-existent file, and one key numeric result (rho = −0.37) that appears only in a figure title rather than a printed output.

---

## Methodology

**Research question and hypotheses**: The research question is clearly stated and operationalized. The three-hypothesis structure (H1 screening validity, H2 retrospective validation, H3 coverage gap) is well-designed — each is independently testable and directionally stated with explicit null alternatives. The composite score design (equal-weight sum of z-scores) is transparent and reproducible; equal weighting is reasonable given the stated goal of capturing two distinct evolutionary paths toward ecotype potential and is supported by the finding that the three dimensions are weakly correlated (all pairwise |rho| < 0.2).

**H1 direction handling**: The RESEARCH_PLAN predicted a positive correlation between phylogenetic substructure and environmental diversity. The observed r = −0.171 (p = 0.003) is significant but negative. The REPORT correctly handles this: "H0 is rejected, but the observed direction contradicts H1." The ecological interpretation that follows (specialist/generalist dichotomy) is biologically coherent and well-supported by the Maistrenko et al. (2020) citation.

**H2 hypothesis vs. implemented test**: The RESEARCH_PLAN specified an AUC-based head-to-head comparison between branch distance CV and ANI variance as competing predictors of significant prior ecotype signal. The implemented test instead uses Spearman correlation without computing ANI variance as a competing predictor or calculating AUC values. The analysis tests whether the new metrics correlate with prior signal, which is informative but a weaker test than what was planned. The REPORT correctly says "H2 partially supported" but does not note that the AUC comparison was not implemented.

**Retrospective validation design**: Linking composite scores to prior `r_partial_emb_jaccard` from `ecotype_analysis` is a strong methodological choice that grounds the screening in an independent empirical benchmark. The 99-species overlap (out of 213 prior species) is explained implicitly — 114 prior species lacked phylogenetic tree data — but this is not made explicit in the REPORT.

**Data sources**: Clearly identified and appropriate. Cross-database joins between `kbase_ke_pangenome` and `nmdc_ncbi_biosamples` are correctly structured. The cross-project dependency on `ecotype_analysis/data/ecotype_correlation_results.csv` is declared and used correctly.

**Reproducibility**: High. All eight data CSVs are committed, enabling NB02 and NB03 to run locally without BERDL access. The README Reproduction section is detailed: it specifies execution order, explains the JupyterHub vs. local split, lists outputs per step, and notes the proxy requirement for NB01 cell outputs. One broken cross-reference: README Step 1b says "see `references/proxy-setup.md`" but no `references/` directory or `proxy-setup.md` file exists in the project.

---

## Code Quality

**NB01 — Data Extraction**: High quality throughout. Cell 4 explicitly checks genome ID format before joining — correctly discovering bare accessions without RS_/GB_ prefix — and Cell 5 verifies cross-table ID alignment for a test species. These are exactly the steps recommended in `docs/pitfalls.md` (`[cofitness_coinheritance] Phylo distance genome IDs lack GTDB prefix`). The `NULLIF(AVG(...), 0)` guard in the CV calculation correctly handles potential divide-by-zero. The SQL subquery pattern (`WHERE ... IN (SELECT gtdb_species_clade_id FROM phylogenetic_tree)`) correctly avoids the `spark.createDataFrame()` Spark Connect incompatibility. The EAV-format handling of `env_triads_flattened` (filtering on `attribute = 'env_broad_scale'`, referencing `label`) precisely matches the corrective pattern documented in `docs/pitfalls.md`. All 14 cells have saved outputs verifying correct execution. Cell 14 performs a final file inventory sanity check confirming all six output files with expected row counts.

**NB02 — Composite Scoring**: Clean and well-organized (load → merge → z-score → test → visualize). The `zscore_robust()` function with ±5 clipping appropriately handles the strongly right-skewed CV distribution driven by the *Prochlorococcus* outlier (CV = 5.84). The H3 Fisher's exact test uses `alternative='less'` correctly to test the directional depletion hypothesis. All statistical results in cells 1–6 and 9 have saved text outputs. Cells 5, 7, and 8 generate figures saved to `figures/` — their notebook outputs contain large base64 image data (noted as too large to display in the reader), but the PNG files are present on disk in the `figures/` directory.

**Minor entropy issue**: The Shannon entropy function uses `np.log2(probs + 1e-12)` to avoid log(0), producing a very slightly negative value (−1.44 × 10⁻¹²) for single-environment species. This is visible in NB02 Cell 2's describe output (`env_broad_entropy min = -1.44e-12`) and propagates into `species_env_stats.csv` and `species_scored.csv`. Technically, entropy should be ≥ 0; the artifact is negligible analytically but could confuse downstream users.

**NB03 — Retrospective Validation**: Well-structured. Cell 1's upfront inspection of prior data (column names, dtypes, null counts) before merging is good defensive practice. Cell 3 explicitly prints both Spearman correlations central to Finding 2 (rho = 0.153 for CV vs r_ani; rho = 0.277 for composite vs r_partial). All cells have saved text outputs.

**Key result missing a print statement**: In NB03 Cell 4, the Spearman rho between composite score and r_ani_jaccard — reported in the REPORT as rho = −0.37, p < 0.001, cited as core evidence in Finding 2 — is computed as variable `r_c` and placed only in a matplotlib figure title (`ax.set_title(f'... rho={r_c:.2f}, p={p_c:.3f}')`). There is no `print()` call for this value. Since figure outputs are base64 images, this result is not text-verifiable from notebook outputs alone.

**`01b_env_extraction_continuation.py`**: The script correctly mirrors NB01 Cells 8–14, and the column renaming (`env_broad_label` → `env_broad_scale`) ensures output compatibility with NB02. The docstring clearly states its purpose, inputs, and usage. As a `.py` script it produces no saved cell outputs, which is an acceptable tradeoff for a fallback path documented as an alternative to NB01. However, `docs/pitfalls.md` specifically flags this pattern (`[env_embedding_explorer]: Notebooks committed without outputs are useless for review`). The README clearly marks 01b as an alternative path rather than a primary notebook, which is important context.

**Pitfall awareness**: Both project-specific pitfalls in `docs/pitfalls.md` are handled correctly in code and acknowledged in NB01's opening cell. The genome ID prefix pitfall is verified empirically in Cells 4–5. No relevant pitfalls from the known list appear to be missed.

---

## Findings Assessment

**Finding 1 (H1)**: The negative correlation between phylo CV and env entropy (r = −0.171, p = 0.003; Spearman rho = −0.202, p < 0.001) is reported correctly and the unexpected direction is interpreted thoughtfully — the specialist/generalist dichotomy is biologically coherent, supported by the Maistrenko et al. citation, and strengthens rather than undermines the composite score rationale.

**Finding 2 (H2) — N inconsistency [factual error]**: There is a factual error in the REPORT: three different sample sizes appear for the single comparison of composite score vs r_partial_emb_jaccard:

| Location in REPORT | Stated N |
|--------------------|----------|
| Finding 2 figure caption (h2_composite_vs_rpartial.png) | **70** |
| Results H2 table, third row | **99** |
| NB03 Cell 4b printed output (`N for composite vs r_partial: 85`) | **85** |

The notebook output is the ground truth: N = 85. Neither N = 70 nor N = 99 is correct for this comparison. The rho = 0.277 and p = 0.010 values are consistent across all locations, so only the N values are wrong.

**Finding 2 — figure caption variable mislabel [factual error]**: The caption for `h2_composite_vs_rpartial.png` in Finding 2 reads: *"Composite score vs **r_ani_jaccard** (environment–gene content partial correlation controlling for phylogeny)…"* The variable name says `r_ani_jaccard` but the description identifies `r_partial_emb_jaccard`. These are distinct metrics: one is the ANI-gene content correlation (a phylogenetic coupling measure), the other is the partial correlation of environment and gene content controlling for phylogeny (the ecotype signal). The figure code (NB03 Cell 4b) and the rho value (0.277) confirm this is `r_partial_emb_jaccard`. The variable name in the caption is wrong.

**Finding 3 (H3)**: Correctly analyzed. OR = 1.45, p = 0.937 for `alternative='less'` is a valid non-rejection of the depletion hypothesis. The interpretation that prior species selection was not systematically biased against high-scorers is accurate and honest.

**Finding 4 (Top 10 table)**: All values cross-check correctly against NB02 Cell 3 printed output — species names, genome counts, CV, entropy, singleton fractions, and composite scores match exactly.

**Composite vs r_ani_jaccard (rho = −0.37)**: This result, central to Finding 2's mechanistic argument, is computed only in NB03 Cell 4 and placed in a figure title with no corresponding `print()`. Its value is stated in the REPORT but cannot be independently verified from notebook text outputs.

**Limitations section**: Strong and specific. The NMDC coverage unevenness (17 species with zero annotations), env_broad_scale coarseness, clinical/host-associated confounders (*S. epidermidis*, *F. tularensis*), and singleton fraction genome-count bias are all correctly identified. The genome-count bias is particularly important — *S. epidermidis* (n = 1,315) and *L. monocytogenes* B (n = 1,923) rank partly due to this artifact — and the rarefaction correction in Future Directions is the right solution.

**References**: Correct and appropriately cited. All literature claims in the Interpretation section are supported by the cited papers, and the specific *Prochlorococcus* ecotype validation (Kettler 2007, Larkin 2016) is accurate.

---

## Suggestions

1. **(Critical) Fix the N discrepancy in REPORT H2**: In the Results → H2 table, change `(N=99)` to `(N=85)` in the third row (composite vs r_partial_emb_jaccard). In the Key Findings → Finding 2 figure caption for `h2_composite_vs_rpartial.png`, change `N=70` to `N=85`.

2. **(Critical) Fix the variable mislabel in the Finding 2 figure caption**: In the `h2_composite_vs_rpartial.png` caption, change `r_ani_jaccard` to `r_partial_emb_jaccard`. The current caption is contradictory (the variable name and the description refer to different metrics).

3. **(Moderate) Add a print statement for the composite vs r_ani_jaccard result**: In NB03 Cell 4, after computing `r_c, p_c = stats.spearmanr(h2_df['composite_score'], h2_df['r_ani_jaccard'])`, add `print(f"Spearman rho (composite vs r_ani_jaccard): {r_c:.3f}, p={p_c:.4f}, N={len(h2_df)}")`. This makes the rho = −0.37 value cited in Finding 2 text-verifiable without decoding the figure.

4. **(Moderate) Fix the broken proxy-setup cross-reference**: README Step 1b says "see `references/proxy-setup.md`" but no such file or directory exists. Either create a brief `docs/proxy-setup.md` pointing to `.claude/skills/berdl-minio/SKILL.md` for proxy chain instructions, or replace the reference with a direct pointer to the correct location.

5. **(Moderate) Note the AUC gap in the REPORT**: RESEARCH_PLAN v1 specified an AUC-based comparison between branch CV and ANI variance as competing predictors. The implemented analysis replaces this with Spearman correlation and does not compute ANI variance as a predictor. A one-sentence note in the H2 results section ("the planned AUC comparison was replaced by Spearman correlation testing; ANI variance was not computed as a competing predictor") would prevent readers from expecting the original analysis.

6. **(Minor) Clip the entropy floor to zero**: In NB01 Cell 12 (and `01b_env_extraction_continuation.py`), apply `.clip(lower=0)` to `entropy_per_species['env_broad_entropy']` after computing it. This prevents the −1.44 × 10⁻¹² floating-point artifact from propagating into output CSVs.

7. **(Minor) Explain the 99/213 overlap gap in REPORT**: The Results section notes "99 species overlapped with the 213-species prior `ecotype_analysis` dataset" but does not explain why 114 prior species are absent. A brief parenthetical (e.g., "those 114 species lacked single-copy core gene trees in `kbase_ke_pangenome`") would help readers interpret the scope of the H2 comparison.

8. **(Minor) Consider adding a printed H2 composite vs r_partial summary to Cell 4b**: Cell 4b already prints `rho=0.277, p=0.0103, N=85`, which is good. Consider also printing a formatted one-line summary matching the format of the other comparisons in Cell 3, to make all H2 statistics consistently text-verifiable in a single place.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-22
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 2 notebooks (01_data_extraction.ipynb, 02_composite_scoring.ipynb, 03_retrospective_validation.ipynb), 1 Python script (01b_env_extraction_continuation.py), 8 data files, 5 figures, docs/pitfalls.md (repository context)
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
