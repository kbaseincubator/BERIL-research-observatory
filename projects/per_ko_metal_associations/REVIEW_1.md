---
reviewer: BERIL Automated Review (Claude, claude-opus-4-8)
date: 2026-07-10
project: per_ko_metal_associations
---

# Review: per_ko_metal_associations

## Summary
This is a strong, unusually rigorous exploratory project. It runs a genome-wide (all-KO, not curated-list) association screen of KEGG orthologs against bioavailable metal concentrations across ~8,585 MGnify MAGs, with SPIRE as a replication cohort, and then subjects the 219 FDR-significant hits to a genuinely impressive battery of robustness controls: latitude adjustment, multi-metal covariates, class-level and phylo-PC taxonomic control, MAG-quality covariates, and restricted-quality sensitivity subsets. The project's greatest strength is its intellectual honesty — ten hypotheses are pre-registered in the RESEARCH_PLAN and reported at face value (three NOT SUPPORTED), the "all analyses are exploratory" framing is maintained throughout, and NB06 explicitly refutes a "strategic cross-paper paragraph" the authors had hoped to write. Notebooks carry saved outputs, twelve figures span every analysis stage, and the association engine is well-engineered (checkpoint/resume, fork-based multiprocessing, separation-avoiding group filtering). The main weaknesses are documentation drift (a badly stale README), a few unexplained plan→report discrepancies (PF1_Zn silently dropped; a confusing cross-dataset sample-size claim), and headline reliance on near-complete-separation odds ratios that the Limitations section itself warns against. None of these undermine the core conclusions; they are polish and transparency issues.

## Methodology
The research question is clearly stated, testable, and well-motivated as the logical successor to two prior null/weak projects (P1 comprehensive_metal_ecology, P4 metagenomic_environment_prediction). Pre-specification is exemplary: prevalence filters, the exact logistic model, FDR scheme, and per-hypothesis thresholds are all fixed in RESEARCH_PLAN.md before results. Data sources are clearly identified and the spatial join (nearest CSU grid cell ≤ 50 km, haversine BallTree) is consistent with sibling projects.

Two methodological transparency gaps deserve attention:

1. **PF1_Zn was planned but is absent from all results.** RESEARCH_PLAN.md and README.md both specify seven metals "all seven" including PF1_Zn, but the results contain only six (As, Cd, Cr, Cu, Hg, Pb). The code in NB01 defines all seven and filters to those present in the joined data, so Zn was evidently dropped because the CSU join produced no PF1_Zn column — but no sentence in REPORT.md states this. A reader comparing the plan to the report is left to infer it.

2. **The cross-dataset comparison (H2) rests on a small convergent subset that the text obscures.** REPORT.md §H2 says "26,850 KO-metal pairs with betas from both datasets; Spearman ρ = 0.059 ... n = 324." Those numbers are inconsistent on their face: `cross_dataset_comparison.csv` has 26,850 rows, but `compute_beta_correlation` drops pairs with a null beta in either dataset, leaving only 324 (~1.2%) with a finite beta in both. So H2 is computed on the ~1% of shared pairs where both unadjusted logistic models converged to a finite estimate — a convergence-based selection that could bias ρ. This is compounded by H6, where the *adjusted* comparison reports n = 26,749. The ~80× jump in usable pairs between unadjusted and adjusted models is itself a substantive and under-explained observation (it implies the unadjusted models failed to produce a finite beta for the vast majority of shared pairs). The phrasing "26,850 KO-metal pairs with betas from both datasets" should be corrected to reflect that most of those betas are null.

Reproducibility is partly served — notebooks have outputs and intermediate CSVs are committed — but there is **no `requirements.txt`** and **no `## Reproduction` section** in the README explaining execution order, Spark-vs-local separation, or expected runtimes. NB00 needs Spark; the downstream notebooks read cached parquet/CSV and can run locally, which is worth stating explicitly.

## Code Quality
The core statistical engine (`association_utils.py`) is clean and defensible. Numeric-string casting is handled, the per-KO group filter that removes taxa lacking both present and absent members is a sound guard against perfect separation, checkpoint/resume is robust, and FDR is correctly applied per metal over the full KO set (not just survivors). The multiprocessing uses `fork` + copy-on-write appropriately for this 128-CPU host.

Points worth raising:

- **Near-complete separation in headline results.** Many top hits carry OR of 10⁴–10⁹ (e.g., kdpA OR = 7.2×10⁵, Pb hits OR 10⁵–10⁹). `_logistic_one_ko` suppresses convergence warnings and still returns the beta, and `converged` can read True even under quasi-separation. The Limitations section correctly says "interpret direction, not magnitude," yet the top-hit tables and the functional-interpretation narrative still headline these unstable ORs. Consider adding an explicit separation/quasi-separation flag column, and spot-checking a few top hits with Firth penalized logistic regression to confirm the direction is stable.

- **The 219 → 6,432 expansion under latitude adjustment (H4) is asserted, not demonstrated.** Adding one continuous covariate to a model that already contains C(phylum) should not, on its own, 30× the significant count; the "increased statistical power" explanation is plausible but unverified. Since `figures/pvalue_histograms.png` exists, the adjusted model's p-value calibration / inflation should be shown and referenced explicitly to rule out miscalibration.

- **The per-KO taxonomic group filter changes the effective sample per KO** (n_total varies), which is a reasonable separation guard but is not documented in REPORT.md and slightly complicates cross-KO comparison of estimates.

**Pitfall awareness** is good. String-typed numeric columns are cast, and the perfect-separation family of issues (docs/pitfalls.md themes around logistic instability) is actively managed. I did not find any of the specific documented BERDL pitfalls (taxonomy join keys, EAV `ncbi_env`, DECIMAL→Decimal, reserved-word columns) mishandled in the code paths I inspected.

## Findings Assessment
Conclusions are well supported by the artifacts shown, and the Limitations section is thorough and self-critical (separation instability, low cross-dataset ρ, latitude as an imperfect geographic proxy, 16.2% phylo-tree coverage justifying the PGLS skip, threshold-dependent quality sensitivity). The negative results (H2, H3, H6) are reported without spin, and NB06's refutation of the hoped-for functional-split replication is a model of honest reporting — it lays out three non-distinguishable explanations for the null and declines to over-claim at n = 8.

Smaller items:
- **Minor factual inconsistency:** REPORT.md line 204 calls K16080 "identity uncertain in eggnog annotations," while INTERPRETATION_TABLE.md line 126 confidently labels it "kdpF / Kdp K⁺-ATPase subunit F." Reconcile these.
- **No `## Discoveries` / `## Performance Notes` sections, and no `memories/` directory.** This is the one case where absence is worth flagging: the project produced at least two genuinely cross-project-relevant results — (a) the curated 730-KO metal list is *not* enriched among genome-wide metal-associated KOs (a direct, load-bearing caveat for P1/P4 and any future curated-list study), and (b) the As signal is largely phylum-level (collapses under class control) whereas Pb/Cd/Cr survive finer taxonomic control. A short `## Discoveries` section capturing (a) especially would be worth surfacing to sibling projects. Scope each carefully as MGnify-specific given the failed replication.
- Housekeeping: `.ipynb_checkpoints/`, `__pycache__/`, and `ckpt_*.csv` are committed; these are noise and could be gitignored.

## Suggestions
1. **(High) Rewrite the README.** It is badly stale: Status still reads "all notebooks pending — data not yet loaded"; it lists only NB00–03 when seven notebooks (00–06) exist and are complete; and its directory-structure block references files that do not exist (`significant_ko_enrichment.csv`, `volcano_plot.png`, `cross_dataset_scatter.png`, `top_ko_heatmap.png`) instead of the real artifact names. REPORT.md line 18 also cites `00_build_ko_matrices.ipynb` (the file is `00_build_ko_matrix.ipynb`).
2. **(High) Fix the H2 sample-size description.** State plainly that ρ = 0.059 is computed over the 324 shared pairs with a finite beta in *both* unadjusted models (not 26,850), note the convergence-based selection, and explain the n = 324 vs n = 26,749 gap between the unadjusted and adjusted comparisons.
3. **(Medium) Explain the PF1_Zn drop.** Add one sentence to REPORT.md documenting that Zn was pre-specified but excluded because the CSU join yielded no Zn column, so results cover six metals.
4. **(Medium) Add a separation flag and a Firth spot-check.** Flag quasi-separated fits in the association CSVs and confirm the top-OR directions with penalized logistic regression on a handful of headline KOs.
5. **(Medium) Demonstrate the H4 power claim.** Show the adjusted-model p-value histogram / genomic-inflation summary to justify the 219 → 6,432 expansion rather than asserting "increased power."
6. **(Medium) Add reproducibility scaffolding.** Ship a `requirements.txt` and a README `## Reproduction` section (execution order NB00→NB06, which steps need Spark vs run locally from cached data, and approximate runtimes — the plan already notes NB01 is the compute-intensive step).
7. **(Low) Add a `## Discoveries` section** capturing the curated-list null-enrichment result and the As-is-phylum-level result, scoped as exploratory/MGnify-specific.
8. **(Low) Reconcile the K16080 annotation** between REPORT.md and INTERPRETATION_TABLE.md.
9. **(Low) Gitignore** `.ipynb_checkpoints/`, `__pycache__/`, and the `ckpt_*.csv` working files.

## Review Metadata
- **Reviewer**: BERIL Automated Review (Claude, claude-opus-4-8)
- **Date**: 2026-07-10
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, INTERPRETATION_TABLE.md, 7 notebooks, ~28 data files, 12 figures, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:66763752a450840a4e80f24d0ddb1be4f14d33d0567038406c8e1cb9bb5702f9 -->
