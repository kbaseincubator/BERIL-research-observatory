---
reviewer: BERIL Automated Review
date: 2026-03-19
project: amr_fitness_cost
---

# Review: Fitness Cost of Antimicrobial Resistance Genes

## Summary

This is a well-designed, largely well-executed project that leverages 27M RB-TnSeq fitness measurements across 25 bacteria to test the cost-of-resistance hypothesis at pan-bacterial scale. The three-file project structure (README, RESEARCH_PLAN, REPORT) is used correctly; the RESEARCH_PLAN demonstrates genuine iterative refinement across three documented revisions including a NB02 checkpoint; statistical methods — DerSimonian-Laird random-effects meta-analysis, Jonckheere-Terpstra ordered-alternative test, pre-registered minimum group sizes — are appropriate and correctly implemented; and the central finding (25/25 organisms show a positive AMR-vs-background fitness shift) is scientifically compelling and well-supported. Known pitfalls (locusId type mismatch, string-typed fitness values, essential gene censoring) are explicitly anticipated and correctly handled. Two issues require correction before this project is cited or built upon: `requirements.txt` is missing `statsmodels`, which is used in three notebooks and will cause an `ImportError` for anyone following the documented reproduction steps; and NB04b's genome-count sensitivity analysis silently fails because it uses linked gene count rather than genome count as a proxy — every species exceeds every threshold, making the three comparisons trivially identical and uninformative.

---

## Methodology

**Research question and hypotheses**: The research question is clearly stated and operationally testable. All four hypotheses (H1–H4) and the null H0 have explicit, measurable predictions. Minimum group sizes are pre-registered (N≥5 for per-organism tests, N≥20 for mechanism tests). The checkpoint design between NB02 and NB03-04 is documented in the RESEARCH_PLAN, and the v3 revision records that the checkpoint was actually evaluated and the plan approved to proceed.

**Unit of analysis**: The per-gene mean fitness approach (averaging across experiments before running per-organism Mann-Whitney tests) avoids inflating the per-organism p-values by the number of experiments. This is methodologically correct and explicitly justified in both the RESEARCH_PLAN and REPORT.

**Two-tier AMR identification**: The Tier 1 (strict `bakta_amr`) / Tier 2 (keyword `bakta_annotations`) strategy is well-reasoned. The NB02 spot-check of 114 unclassified Tier 2 genes confirms they are genuinely AMR-related (fosfomycin resistance proteins, RND efflux MFP subunits, tellurite resistance proteins — no obvious false positives). The Tier 1–only sensitivity analysis (KS D=0.112, p=0.17) supports pooling the tiers.

**Cross-project dependencies**: Three prior project artifacts are consumed (`conservation_vs_fitness/fb_pangenome_link.tsv`, `fitness_modules/matrices/`, `essential_genome/`). These are clearly documented and their paths are resolved robustly. The ~14% background essential rate cited in the REPORT is correctly attributed to a different project (`fitness_effects_conservation`) using a different organism set; the REPORT notes the difference ("different organism set") and interprets the lower AMR essential rate (4.6%) correctly as consistent with AMR genes being more dispensable than average.

**Reproducibility**: The README reproduction section clearly lists execution order, identifies which step requires Spark (only `src/extract_amr_data.py`), and notes that all downstream notebooks can run locally from cached data. This is the correct pattern. However, `requirements.txt` lists only `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn` — it omits `statsmodels`, which is imported as `from statsmodels.stats.multitest import multipletests` in NB02 (cell-13), NB03 (cell-1), and NB04 (cell-5). Anyone following the documented reproduction steps will hit an `ImportError` at the first BH-FDR correction.

---

## Code Quality

**SQL and Spark (`extract_amr_data.py`)**: The batched IN-clause approach for querying 163K cluster IDs in blocks of 5,000 is correct and necessary. The import `from berdl_notebook_utils.setup_spark_session import get_spark_session` matches the JupyterHub CLI pattern documented in pitfalls.md. Keyword terms for Tier 2 extraction are specific enough to avoid metabolic enzymes (efflux pump hits are gated on `rnd`, `multidrug`, `antibiotic`, or `resistance`).

**Known pitfall handling**: Three pitfalls are explicitly anticipated in the RESEARCH_PLAN and correctly handled in the code:
- locusId integer vs. string mismatch: `fit_mat.index = fit_mat.index.astype(str)` and explicit `str(l)` casts throughout NB02–NB04 (NB02 cell-8).
- String-typed fitness values: `fit_mat = fit_mat.apply(pd.to_numeric, errors='coerce')` (NB02 cell-8).
- Essential gene censoring: quantified per organism in NB02 cell-6 (4.6% overall), with direction of bias discussed in the REPORT.

**DerSimonian-Laird implementation (NB02 cell-15)**: Correct. Computes fixed-effects weights, Cochran's Q, τ², random-effects weights, pooled estimate, 95% CI using 1.96×SE, one-sided z-test for effect > 0. Output matches the REPORT (θ=+0.086, CI=[+0.074, +0.098], z=14.3, I²=54.3%).

**Jonckheere-Terpstra implementation (NB04 cell-4)**: Conceptually correct but implemented as a nested double loop over all pairs across all four group combinations. With N=254 (efflux), N=304 (enzymatic inactivation), N=144 (metal), and N=74 (unknown), this iterates over roughly 254×304 + 254×144 + 254×74 + 304×144 + 304×74 + 144×74 ≈ 202K pair comparisons. Likely ran without timeout but the runtime could be several minutes on slow hardware. Consider noting the expected runtime or referencing a faster implementation.

**AMR product classifier — fosfomycin and tellurite gap (NB01 cells 7 and 9)**: The SQL extraction in `extract_amr_data.py` correctly captures "Fosfomycin resistance protein AbaF" (3 genes, confirmed in NB01 cell-3 spot-check) and "Tellurite resistance protein" variants (>15 genes). However, `classify_amr_product()` in NB01 cell-7 has no matching branch for either `fosfomycin` or `tellurite`, so these ~25 genes propagate through all analyses as `amr_class='unclassified', amr_mechanism='unknown'`. They are counted in the `unknown` mechanism group (N=74 in NB04) alongside genuine unknowns. The REPORT's Limitations section acknowledges this gap, but it is fixable with two additional `if` branches.

**NB04b cells 10–12 — genome-count sensitivity analysis (critical logic error)**: The code computes:
```python
genome_counts = fb_link.groupby('gtdb_species_clade_id')['locusId'].count()
```
This counts linked **genes** per species (the `fb_link` table has one row per gene-cluster link). The resulting column `n_genes_linked` ranges from 1,020 to 7,187 — values that represent gene counts, not genome counts. Threshold comparisons (`>=50 genomes`, `>=100 genomes`, `>=200 genomes`) are then applied to this column. Since every species far exceeds even the highest threshold, all three comparisons include the full dataset identically: core N=638, accessory N=163, p=0.6562 at all three levels. The cell-12 output confirms this — mean=4,860, min=1,020. The intended sensitivity analysis (whether the H3 null result holds for well-sampled species with reliable core/accessory labels) was not executed. This is a silent failure — no error is raised, results look plausible, but they are uninformative.

---

## Findings Assessment

**H1 (universal cost of resistance)**: The 25/25 positive per-organism shift and meta-analytic pooled effect (+0.086 [+0.074, +0.098], z=14.3) are compelling. The REPORT correctly interprets this as a relative difference: "AMR gene knockouts are 0.086 fitness units less detrimental than the average gene knockout — i.e., AMR genes are more dispensable than the typical gene" and notes that "absolute AMR knockout fitness averages −0.024 (slightly below the pool mean), so AMR knockouts still grow slower than the pool average." The REPORT also correctly addresses the one-sample test (Wilcoxon p=0.9985 against zero), explaining that the relevant comparison is AMR vs. background knockouts within each organism, not AMR vs. wildtype. Both the effect size interpretation and the one-sample test discussion are accurate and transparent.

**H4 (antibiotic validation)**: The any-antibiotic Wilcoxon (p=0.0001, N=797) provides solid positive-control support. The class-matched Wilcoxon (p=0.14, N=157) is non-significant. The REPORT correctly reports both results in the summary table and acknowledges the class-matched non-significance in the REPORT narrative with a plausible explanation (small N per class, heterogeneous experiments). The efflux vs. enzymatic flip comparison (NB04b cell-4, MWU p=0.007) is a genuinely interesting secondary finding that supports the narrow-spectrum vs. broad-spectrum interpretation.

**H2 (mechanism-dependent costs)**: The null result is clearly reported (KW H=0.65, p=0.89; JT z=0.23, p=0.41) and all pairwise comparisons survive FDR correction at q>0.8. The interpretation — uniform compensatory evolution reaching a "floor" cost — is biologically plausible and supported by the cited literature (Olivares Pacheco et al. 2017; Vogwill & MacLean 2015).

**H3 (accessory > core costs)**: The null result is clearly reported (MWU p=0.33, Cohen's d=0.002). The caveat about imprecise core/accessory labels for species with few genomes (median 9 per FB organism) is appropriately flagged. However, the genome-count sensitivity analysis intended to test this (NB04b cells 10–12) fails silently as described above, so the imprecision concern cannot actually be ruled out from the current analysis.

**Mechanism × conservation interaction (NB04b cell-6)**: The chi-square result (χ²=69.3, p=1.4×10⁻¹³) is correctly computed and the finding — mechanism predicts pangenome location but not fitness cost — is genuinely novel and well-framed.

**Literature comparisons**: The comparison to Melnyk et al. (2015)'s 5–9% absolute fitness cost is honest about the methodological difference ("these are different measurement scales") while noting convergent order-of-magnitude agreement. The literature section is unusually thorough for a BERDL project (8 targeted citations, each linked to a specific finding).

---

## Suggestions

1. **(Critical)** Add `statsmodels` to `requirements.txt`. It is imported in NB02 cell-13, NB03 cell-1, and NB04 cell-5 (`from statsmodels.stats.multitest import multipletests`) and will cause `ImportError` for any user who installs only the listed packages.

2. **(Critical)** Fix or remove the genome-count sensitivity analysis in NB04b cells 10–12. The variable `n_genes_linked` holds gene counts (range 1,020–7,187), not genome counts, so all threshold comparisons are trivially identical. The correct fix is to retrieve actual genome counts from the pangenome `pangenome` table (`no_genomes` column) by joining on `gtdb_species_clade_id` via a Spark query, or to query the `species_genome_counts.csv` file that already exists in the project's `data/` directory (which may contain this information). If a Spark query is not feasible post-hoc, remove the cells and add a note to the REPORT Limitations that the genome-count precision analysis was not completed.

3. **(Moderate)** Add fosfomycin and tellurite handling to `classify_amr_product()` in NB01 cell-7. Two branches would reclassify ~25 currently-unknown genes: `if 'fosfomycin' in product_lower` → `('fosfomycin', 'enzymatic_inactivation')` and `if 'tellurite' in product_lower` → `('tellurite', 'metal_resistance')`. This would reduce the unexplained `unknown` mechanism group from N=74 to approximately N=49 and eliminate the need for the Limitation 7 caveat in the REPORT.

4. **(Minor)** Add a note in NB04b cell-3 clarifying why the "any_abx with class match" flip (mean=−0.006) differs from the class-matched flip (mean=+0.113). The difference arises because the "any_abx" set averages over all antibiotic experiments for each gene, diluting the signal from the single class-matching antibiotic. This is not an error, but the discrepancy is confusing and the MWU comparison (p=0.9772, class-matched flip vs. unmatched flip using any-abx fitness) tests an inconsistent pairing.

5. **(Minor)** Add a runtime comment to the Jonckheere-Terpstra implementation in NB04 cell-4. The O(n₁×n₂) pair-counting over four groups of 74–304 genes involves ~202K comparisons. It likely completed in under a minute, but noting the expected runtime would help future users who might apply it to larger datasets.

6. **(Minor)** Check `data/species_genome_counts.csv` — this file exists in the project `data/` directory (visible in the file listing) but is never loaded or used in any notebook. If it contains per-species genome counts from the pangenome, it could directly fix Suggestion 2 without a Spark query.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks (NB01–NB04b), 1 source script (src/extract_amr_data.py), requirements.txt, 8 data files, 11 figures, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
