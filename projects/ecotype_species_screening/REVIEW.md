---
reviewer: BERIL Automated Review
date: 2026-02-22
project: ecotype_species_screening
---

# Review: Ecotype Species Screening

## Summary

This is a well-executed, clearly documented upstream screening project that fills a genuine gap in prior BERIL ecotype work. Rather than selecting species by AlphaEarth coverage, it systematically ranks all 338 species with phylogenetic tree data across three biologically motivated, independently measured dimensions: phylogenetic substructure (CV of pairwise branch distances), environmental diversity (Shannon entropy of ENVO-harmonized env_broad_scale labels), and pangenome openness (singleton gene cluster fraction). The three-file documentation structure is complete and internally consistent; all notebooks have executed outputs; all 5 figures are present; all 8 data CSVs are committed. Pitfall awareness is excellent — both the `env_triads_flattened` EAV format issue and the `spark.createDataFrame()` Spark Connect incompatibility were identified, handled correctly, and documented in `docs/pitfalls.md`. Face validity is strong: *Prochlorococcus* A, the canonical bacterial ecotype example, ranks first. The main correctable issues are: the rho=−0.37 result for composite vs r_ani_jaccard (a key claim in Finding 2) appears only in a figure title rather than printed to notebook text; the RESEARCH_PLAN's planned AUC comparison for H2 was replaced with Spearman correlation without acknowledgment in the REPORT; the README contains a broken file cross-reference to a nonexistent `references/proxy-setup.md`; and a Mann-Whitney test in NB03 Cell 5 checks the wrong directional alternative.

---

## Methodology

**Research question and hypotheses**: Clearly stated and operationalized. The three-hypothesis structure (H1: correlation between phylo substructure and env diversity; H2: branch CV predicts prior ecotype signal; H3: top candidates underrepresented in prior work) is well-designed — each is independently testable with an explicit null and directional alternative.

**Composite score design**: The equal-weight sum of z-scores is transparent and reproducible. Equal weighting is justified by the finding that the three dimensions are weakly correlated (all pairwise |rho| < 0.2, confirmed by the dimension_correlations figure), meaning no dimension dominates. The `zscore_robust()` function clips at ±5, appropriately limiting the undue influence of the *Prochlorococcus* outlier (unclipped z ≈ 11.7).

**H1 direction handling**: The RESEARCH_PLAN predicted a *positive* correlation between phylo substructure and env diversity. The observed r = −0.171 (p = 0.003) is significant but negative. The REPORT correctly states "H0 is rejected, but the observed direction contradicts H1" and provides a biologically coherent interpretation (specialist/generalist dichotomy). This honest handling of the unexpected result strengthens the work.

**H2 — planned AUC comparison not implemented**: The RESEARCH_PLAN specified "AUC of branch distance variance vs ANI variance for predicting significant prior ecotype signal" as the H2 test. The implemented test uses Spearman rank correlation instead; ANI variance is never computed as a competing predictor, and no AUC values are reported. The Spearman correlation is informative, but the more diagnostic head-to-head comparison was not performed. The REPORT says "H2 partially supported" without noting this deviation from the plan. A brief acknowledgment in the Results section would be appropriate.

**Retrospective validation design**: Linking composite scores to prior `r_partial_emb_jaccard` from `ecotype_analysis` is a strong choice — it grounds the screening in an independent empirical benchmark. The 99-species overlap with prior work is adequate for Spearman correlation. The REPORT does not explain why only 99 of the 213 prior species appear in the overlap (the remaining 114 lack phylogenetic tree data in BERDL); a brief note for readers would help.

**Filters from RESEARCH_PLAN not applied**: The plan specified (1) a minimum 20-genome filter and (2) exclusion of species with >90% single-category biosample environments. Neither is applied in NB02. The genome-count filter is inconsequential (only 2 species have <20 genomes per NB01 Cell 14). The single-category filter is largely self-correcting (low-entropy species receive low env z-scores), but the deviation from the stated plan should be documented with a note in NB02.

**Data sources**: All clearly identified in RESEARCH_PLAN and REPORT with table names, database names, and row-count estimates. The cross-project dependency on `ecotype_analysis/data/ecotype_correlation_results.csv` is declared and used correctly.

---

## Reproducibility

**Notebook outputs**: All non-figure cells across NB01, NB02, and NB03 have text/table outputs committed. Figure cells (NB02 Cells 5, 7, 8; NB03 Cells 4, 4b) show "Outputs are too large to include" in the notebook reader — this reflects large base64-encoded PNG data in executed cell outputs, not missing outputs. All five corresponding PNG files are present in `figures/`.

**Data files**: All 8 CSVs are committed. The README correctly states that NB02 and NB03 can be run locally from committed data without BERDL access. This is a good checkpointing pattern.

**Spark/local separation**: Clearly documented. NB01 is labeled for JupyterHub; NB02 and NB03 for local execution. The `01b_env_extraction_continuation.py` script provides a valid alternative path for re-running env extraction locally via Spark Connect, and its docstring clearly states its inputs and usage.

**Broken cross-reference**: README Step 1b says `01b` "requires the local Spark Connect proxy to be running (see `references/proxy-setup.md`)". No `references/` directory exists in the project and no `proxy-setup.md` file exists anywhere in the repository. The correct resource is `.claude/skills/berdl-minio/SKILL.md`, referenced in `docs/pitfalls.md`. This should be corrected to point to the right location.

**Dependencies**: `requirements.txt` covers all packages used in NB02–NB03 (numpy, pandas, scipy, matplotlib). Version ranges (`>=`) are appropriate for this type of analysis. No missing dependencies detected.

---

## Code Quality

**SQL correctness**: SQL in NB01 is correct throughout. Specific strengths:
- Cell 4–5 explicitly verifies genome ID format before any joins, confirming bare accessions in `phylogenetic_tree_distance_pairs` — precisely the check recommended by the `[cofitness_coinheritance]` pitfall entry in `docs/pitfalls.md`.
- Cell 6 uses `NULLIF(AVG(...), 0)` to guard the CV denominator against divide-by-zero.
- Cell 10 uses a SQL subquery (`WHERE gtdb_species_clade_id IN (SELECT ... FROM phylogenetic_tree)`) to avoid the `spark.createDataFrame()` Spark Connect incompatibility — correctly documented in NB01's opening markdown cell and in the RESEARCH_PLAN v2 revision history.
- Cell 11 correctly pivots the EAV format using `COUNT(DISTINCT CASE WHEN t.attribute = 'env_broad_scale' THEN t.label END)` — matching the corrective pattern from the `[ecotype_species_screening]` pitfall entry.

**Pitfall awareness**: Excellent. Both project-generated pitfalls in `docs/pitfalls.md` are handled correctly in code. Cell 14 performs a final file inventory sanity check confirming all six output files with correct row counts before handoff.

**Shannon entropy epsilon bias**: The entropy function in NB01 Cell 12 (and mirrored in `01b`) uses `np.log2(probs + 1e-12)` to avoid log(0). For single-environment species (probability = 1.0), this yields `−1 × log2(1 + ε) ≈ −1.44 × 10⁻¹²` — a slightly negative entropy. NB01 Cell 12 output confirms the minimum is `−1.44e−12`. This is negligible analytically and does not affect rankings, but technically entropy should be ≥ 0. The cleanest fix is to filter zero-probability bins before the log: `probs = probs[probs > 0]`, or to use `scipy.stats.entropy(counts, base=2)`.

**Key statistic not printed to notebook text**: In NB03 Cell 4, `r_c, p_c = stats.spearmanr(h2_df['composite_score'], h2_df['r_ani_jaccard'])` is computed but only placed in a matplotlib `ax.set_title()` string — never printed to stdout. The REPORT cites rho = −0.37 (p < 0.001) as core evidence for Finding 2's mechanistic argument about gene content decoupling from phylogeny. This value cannot be independently verified from notebook text outputs; it requires either running the notebook or reading the figure image.

**Mann-Whitney test direction error in NB03 Cell 5**: Cell 5 uses `alternative='greater'` to test whether high composite scorers have higher r_ani_jaccard than low scorers. The output reveals the opposite: high scorers have a *lower* mean r_ani_jaccard (0.627 vs 0.734), consistent with the negative rho = −0.37. The one-sided test in the wrong direction produces p = 0.9953. This cell is exploratory and its result does not appear in the REPORT, but the direction error should be corrected to avoid misleading a reader who re-runs the analysis.

**`01b_env_extraction_continuation.py`**: Well-structured and correctly mirrors NB01 Cells 8–14. One minor point: the SQL in `01b` Cell 12 aliases the env category column as `env_broad_label`, while NB01 uses `env_broad_scale`. Line 142 renames the column before saving, producing identical CSVs. The rename is correctly handled but the inconsistent SQL alias could confuse someone comparing the two implementations; a comment explaining the rename would help.

**NB02 and NB03**: Clean and well-organized. The H3 Fisher's exact test correctly uses `alternative='less'` to test directional depletion. NB03 Cell 3 cleanly prints both Spearman statistics central to H2 (rho = 0.153 for CV alone; rho = 0.277 for composite vs r_partial). Cell 1's upfront inspection of prior data dtypes and null counts before merging is good defensive practice.

---

## Findings Assessment

**Finding 1 (H1)**: The negative correlation (Pearson r = −0.171, p = 0.003; Spearman rho = −0.202, p < 0.001) is correctly reported and cross-checks against NB02 Cell 5 printed output. The specialist/generalist interpretation is biologically coherent and grounded in Maistrenko et al. (2020). The argument that the negative correlation *strengthens* the case for the composite score (the two dimensions capture orthogonal aspects of ecotype potential) is logically valid.

**Finding 2 (H2)**: The two text-verifiable H2 statistics from NB03 Cell 3 are correctly reported:
- Branch CV vs r_ani_jaccard: rho = 0.153, p = 0.130, N=99 ✓
- Composite vs r_partial_emb_jaccard: rho = 0.277, p = 0.010, N=85 ✓

The third statistic — composite vs r_ani_jaccard (rho = −0.37, p < 0.001, N=99) — is cited in the REPORT's Finding 2 body text and H2 Results table but is not printed to NB03 notebook text (see Code Quality above). The N values in the REPORT are internally consistent: N=99 for r_ani comparisons (no missing values in that column), N=85 for r_partial comparisons (14 species with missing r_partial values, consistent with NB03 Cell 1 output showing 30 NaN entries in r_partial_emb_jaccard).

**Finding 3 (H3)**: Correctly analyzed. Fisher's exact OR = 1.45, p = 0.937 is consistent with NB02 Cell 6 output. The interpretation that prior species selection was not systematically biased against high-scorers is accurate and honestly stated.

**Finding 4 (Top 10 table)**: All values cross-check exactly against NB02 Cell 3 printed output — species names, genome counts, CV, entropy, singleton fractions, and composite scores match.

**Validation by known ecotypes**: Recovery of *Prochlorococcus* A sp000635495 at rank 1 and *S. warneri* at rank 7 (strongest prior partial ecotype signal, r_partial = 0.42) are meaningful positive controls. *Akkermansia* sp004167605 at rank 2 with r_ani_jaccard = 0.82 (highest in the overlap set) further supports face validity.

**Limitations**: The four acknowledged limitations (NMDC coverage unevenness, env_broad_scale coarseness, clinical/host-associated confounders, singleton fraction genome-count bias) are appropriate and honestly stated. The genome-count bias is particularly relevant for S. epidermidis (n=1,315, rank 5) and L. monocytogenes B (n=1,923, rank 8); the rarefaction correction suggested in Future Directions is the right solution.

**References**: Correct and appropriately cited. All specific claims in the Interpretation section are supported by cited papers.

---

## Suggestions

1. **(Moderate) Add a print statement for the composite vs r_ani_jaccard result in NB03 Cell 4.** After `r_c, p_c = stats.spearmanr(h2_df['composite_score'], h2_df['r_ani_jaccard'])`, add `print(f"Spearman rho (composite vs r_ani_jaccard) = {r_c:.3f}, p = {p_c:.4f}, N={len(h2_df)}")`. This makes the rho = −0.37 value cited in Finding 2 text-verifiable from notebook outputs.

2. **(Moderate) Fix the broken proxy-setup cross-reference in README.** The reference to `references/proxy-setup.md` points to a nonexistent file. Replace with a direct pointer to `.claude/skills/berdl-minio/SKILL.md` (the correct resource per `docs/pitfalls.md`), or add a `references/proxy-setup.md` stub that redirects there.

3. **(Moderate) Fix the Mann-Whitney test direction in NB03 Cell 5.** Change `alternative='greater'` to `alternative='less'` (or `'two-sided'`), and add a comment explaining that high composite scores are expected to correlate *negatively* with r_ani_jaccard, consistent with the rho = −0.37 result.

4. **(Moderate) Acknowledge the AUC gap in the REPORT H2 section.** The RESEARCH_PLAN specified an AUC-based head-to-head comparison between branch CV and ANI variance. The implemented analysis uses Spearman correlation and never computes ANI variance as a competing predictor. Add one sentence to Results → H2: e.g., "The planned AUC comparison between branch CV and ANI variance as competing predictors was replaced with Spearman rank correlation; ANI variance was not independently computed."

5. **(Minor) Fix the Shannon entropy floor.** In NB01 Cell 12 and `01b` line 128, update the entropy function to filter zero-probability bins before the log: replace `np.log2(probs + 1e-12)` with `probs = probs[probs > 0]` then `return float(-np.sum(probs * np.log2(probs)))`. Alternatively use `scipy.stats.entropy(counts, base=2)`. As a belt-and-suspenders measure, also apply `.clip(lower=0)` when saving in Cell 13, to prevent the −1.44 × 10⁻¹² artifact from propagating to output CSVs.

6. **(Minor) Document filter deviations from RESEARCH_PLAN in NB02.** Add a brief comment in NB02 Cell 2 noting that (1) the ≥20 genome filter was omitted (2 species affected, negligible impact) and (2) the >90% single-category exclusion was replaced by z-scoring which naturally penalizes low-entropy species.

7. **(Minor) Clarify the 99/213 overlap in the REPORT.** In Results → Species Universe, add a parenthetical explaining why 114 of the 213 prior ecotype_analysis species are absent from the overlap (they lacked single-copy core gene trees in `kbase_ke_pangenome`). This contextualizes the scope of the H2 comparison for readers.

8. **(Nice-to-have) Add a comment explaining the column rename in `01b`.** In `01b_env_extraction_continuation.py` line 142, add a comment explaining that `env_broad_label` is renamed to `env_broad_scale` for output CSV compatibility with the column alias used in NB01.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-22
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 3 notebooks (01_data_extraction.ipynb, 02_composite_scoring.ipynb, 03_retrospective_validation.ipynb), 1 Python script (01b_env_extraction_continuation.py), 8 data files, 5 figures, docs/pitfalls.md (repository context)
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
