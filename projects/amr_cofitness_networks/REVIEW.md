---
reviewer: BERIL Automated Review
date: 2026-03-19
project: amr_cofitness_networks
---

# Review: AMR Co-Fitness Support Networks

## Summary

This is a thorough and scientifically mature follow-up to `amr_fitness_cost`, mapping co-fitness support networks of 801 AMR genes across 28 bacteria using pairwise Pearson correlations from cached fitness matrices and ICA fitness modules. The project excels in three areas: (1) all 6 notebooks are fully executed with saved outputs, 9 figures cover every analysis stage, and a clear reproduction guide is provided; (2) the RESEARCH_PLAN pre-specifies four hypotheses with explicit statistical tests, null models, and power concerns, far above average for an exploratory project; and (3) the REPORT contains an unusually honest self-critique of the main finding — the flagellar motility/amino acid biosynthesis enrichment could reflect shared dispensability under lab conditions rather than genuine co-regulation, and the authors identify the exact follow-up experiment needed to distinguish these interpretations. The annotation quality comparison (SEED null result vs InterProScan significant result) is a concrete, reproducible methodological lesson. The main gaps are a missing Spark extraction notebook for the InterProScan annotation files, an approximate operon exclusion heuristic that does not use genomic coordinates, and a permutation test that matches on conservation class but not mean fitness level — a gap the authors themselves flag as the most important limitation.

## Methodology

**Research question and hypotheses**: Clearly stated and operationally testable. Four numbered hypotheses (H1-H4) each specify the statistical test, FDR scope, and expected effect direction. The RESEARCH_PLAN documents null models (conservation-matched random genes for H1, random KO overlap for H4), confounders (operon proximity, module size bias, annotation coverage), and power concerns (H3 cost variance). This level of pre-specification is well above average.

**Approach**: The decision to compute full pairwise cofitness from cached fitness matrices rather than using the `cofit` table (which stores only top ~96 partners per gene) is correctly motivated and documented in both the RESEARCH_PLAN and NB01 markdown. The 28-organism intersection is verified with explicit locusId overlap checks, and all 28 organisms show 100% locusId match between AMR genes and fitness matrices.

**Data sources**: Clearly identified across six upstream tables and three prior projects. The cross-project dependency chain (`amr_fitness_cost` + `fitness_modules` + `conservation_vs_fitness`) is documented in the README with specific file paths.

**Key reproducibility gap — missing Spark extraction code**: The files `fb_interproscan_go.csv` (18 MB, 438K rows), `fb_interproscan_pfam.csv` (24 MB, 229K rows), and `fb_bakta_kegg.csv` (1.6 MB, 42K rows) are present in `data/` and loaded by NB03b and NB04b, but no notebook contains the Spark queries that extracted these from `kbase_ke_pangenome.interproscan_go`, `kbase_ke_pangenome.interproscan_domains`, or `kbase_ke_pangenome.bakta_annotations`. The README mentions NB03b "requires Spark for data extraction step" but does not specify what queries to run. A reproducer would be unable to generate these files from scratch. This is the single most significant reproducibility gap.

## Code Quality

**Overall structure**: Each notebook follows a consistent setup -> load -> compute -> visualize -> save pattern with markdown section headers. The code is clean, well-commented, and logically organized.

**Pitfall awareness** (checked against `docs/pitfalls.md`):
- locusId type mismatch: Handled with `.astype(str)` on both sides in NB01 Cell 3 and Cell 8
- FB numeric string columns: `pd.to_numeric(errors='coerce')` applied to fitness matrices in NB01 Cell 8
- `cofit` table limitation: Correctly identified and worked around by computing full pairwise correlations
- Unnecessary `.toPandas()`: Not applicable — all Spark work is pre-extracted; analysis is local pandas throughout

**Cofitness computation (NB01 Cell 8)**: The numpy-vectorized correlation replaces NaN with zero via `np.nan_to_num(..., 0)` after centering and normalizing. This is a common approximation but is not equivalent to pairwise-complete Pearson correlation: experiments where one gene has missing data contribute zero to the numerator but are excluded from the denominator normalization, biasing those correlations toward zero. For the Fitness Browser matrices (which are relatively dense), this is unlikely to change conclusions materially, but the REPORT describes these as "Pearson correlations" without noting this approximation.

**Operon exclusion (NB01 Cell 8)**: The 5-ORF exclusion uses fitness matrix row index position (`abs(locus_to_idx[partner] - locus_to_idx[amr_locus]) <= 5`) as a proxy for genomic proximity. However, the fitness matrix index order is not guaranteed to reflect chromosomal gene order — it depends on how genes were loaded from the FB gene table. As a result, this exclusion may not reliably identify truly proximal genes. Only 0.6% of pairs (995/180,370) are excluded, which could indicate either that few proximal gene pairs show strong cofitness, or that the heuristic is not identifying truly proximal genes. Notably, the `begin`, `end`, and `strand` columns are already loaded in NB01 Cell 12 (the annotations DataFrame) but are not used for the exclusion. The RESEARCH_PLAN flags this as approximate and the REPORT limitations section acknowledges it.

**Module coverage label (NB01 Cell 3)**: The `pct_in_modules` column checks whether AMR locusIds appear in the module membership *file* index (which contains ALL genes as rows, not just those assigned to modules), so it reports 100% by construction. The output says "Module coverage: 100.0% of AMR genes with fitness data," which contradicts the correct 24% figure computed in NB01 Cell 5 and NB02. The downstream analysis (NB02) independently computes the correct 24% figure, so this does not affect results, but it is misleading in the intermediate output.

**NB02 Cell 8 text output**: The summary line reads "AMR modules are LARGER non-AMR modules" — missing the word "than" in the f-string comparison template.

**Permutation test (NB03 Cell 8)**: Runs 200 permutations instead of the 1,000 specified in the RESEARCH_PLAN. The code notes this was "reduced from 1000 for speed; sufficient for a first pass." For the main conclusion (0 significant enrichments with SEED annotations), 200 permutations are adequate — but reporting this deviation from the plan is good practice, and it is noted in the code comment.

**NB03b Cell 3 performance**: Uses `.apply(lambda r: ..., axis=1)` on 179K rows to map `(orgId, partner_locusId)` tuples to `gene_cluster_id` via a dictionary. This row-wise apply is slow (see `docs/pitfalls.md` on row-wise apply). A vectorized approach using `pd.merge` or creating a multi-index lookup would be faster. Not a correctness issue, but affects runtime.

**GO enrichment figure (NB03b Cell 8)**: The bar chart y-axis shows raw GO IDs (e.g., GO:0071973) rather than human-readable descriptions. The `GO_DESCRIPTIONS` dict exists in NB04b but is not imported into NB03b, so the figure is not self-explanatory without consulting the REPORT table.

**Fisher enrichment design (NB03b Cell 5)**: The background set for each organism uses all genes in the FB-pangenome link (`all_locus_clusters[org]`), while the foreground is all extra-operon partner gene clusters. At |r| > 0.3, the mean partner set has 233 genes — a large foreground that gives high power to detect even small frequency differences. The key flagellar motility terms show mean odds ratios of 4.7-5.3, which are genuine enrichments regardless of power. However, confirming these hold at |r| > 0.4 (mean 110 genes) would add confidence that the signal is not driven by a tail of weak correlations.

**requirements.txt**: Lists 6 packages without version pins. Adding version constraints would improve long-term reproducibility.

## Findings Assessment

**H1 (AMR genes enriched for specific functional categories)**: Supported with InterProScan GO annotations. Six GO terms are significant in >=3 organisms (FDR < 0.05): flagellar motility (5 orgs, mean OR ~5), flagellum assembly (5 orgs), bacterial-type flagellum (4 orgs), flagellum-dependent swarming (4 orgs), histidine biosynthesis (3 orgs, OR 5.3), and tryptophan biosynthesis (3 orgs, OR 5.3). The comparison with old SEED annotations (0/280 significant) is retained as a baseline, which is excellent scientific practice. Critically, the REPORT's Interpretation section provides an unusually thorough self-critique: the enrichment may reflect shared dispensability under lab conditions (flagella useless in shaken culture, biosynthesis redundant in supplemented media) rather than genuine co-regulation. This is one of the strongest aspects of the project — the authors correctly identify the key unresolved test (fitness-matched permutation) and explain exactly why it matters.

**H2 (Efflux in stress modules vs enzymatic in isolated modules)**: Partially addressed. AMR-containing modules are significantly larger than non-AMR modules (median 46 vs 27, p = 1.7x10^-8), and 99% are in cross-organism conserved families. But the mechanism-level comparison (efflux vs enzymatic module size) shows no difference (MWU p = 0.91), so H2 is not supported as originally formulated. The REPORT accurately presents this as a partial result.

**H3 (Network size predicts fitness cost)**: Correctly reported as not supported (Spearman rho = -0.006, p = 0.87, N = 769). Properly contextualized as possibly reflecting narrow cost variance rather than absence of relationship.

**H4 (Support networks conserved across organisms)**: The finding that networks are organism-specific (cross-mechanism J = 0.375) rather than mechanism-specific (within-mechanism J = 0.207, p = 4.3x10^-13) is nuanced, interesting, and robustly supported by the data. The REPORT correctly notes this finding is robust to the dispensability confound because it is a structural observation about how organisms organize gene co-regulation, regardless of why genes correlate.

**Limitations**: Seven specific limitations are documented, including the most important ones (shared dispensability confound, cofitness != co-regulation, GO term granularity, large network sizes, H3 power, FB organism bias, operon heuristic). The shared-dispensability discussion is genuinely insightful and adds value beyond the specific AMR question — it identifies a general caveat for all cofitness-based functional genomics.

**Completeness**: No "to be filled" sections or incomplete analyses. All 12 generated data files listed in REPORT.md are present in `data/` with sizes consistent with reported row counts. All 9 figures referenced in REPORT.md are present in `figures/`.

## Suggestions

1. **[Critical - Reproducibility]** Add a data extraction cell or standalone notebook documenting the Spark queries used to produce `fb_interproscan_go.csv`, `fb_interproscan_pfam.csv`, and `fb_bakta_kegg.csv`. A cell guarded by `if not os.path.exists(...)` at the top of NB03b would allow the notebook to either regenerate annotations from Spark or load cached files. Without this, a new user cannot reproduce the core InterProScan analysis from scratch.

2. **[Moderate - Methodology]** Replace the index-position-based operon exclusion with a coordinate-based one. The `begin`, `end`, `scaffoldId`, and `strand` columns are already loaded in NB01 Cell 12. Build a per-organism lookup of `{locusId: (scaffoldId, begin, end, strand)}` and exclude partners within a defined distance (e.g., 10 kb) on the same scaffold and strand. This would make the exclusion meaningful.

3. **[Moderate - Findings]** Confirm the flagellar motility and amino acid biosynthesis enrichments hold at |r| > 0.4 (mean network size ~110 genes). A few additional lines in NB03b Cell 5 running the same Fisher tests on the `|r| > 0.4` subset would strengthen the main conclusion by showing it is not driven by weak correlations.

4. **[Moderate - Code Correctness]** Fix the misleading "Module coverage: 100.0%" label in NB01 Cell 3. The variable checks whether AMR locusIds appear in the module *file* (which contains all genes), not whether they are assigned to a module. Rename to `pct_in_module_file` and update the print statement, or add a clarifying comment that this measures file coverage, not module assignment.

5. **[Minor - Figure Quality]** Update the NB03b enrichment figure (Cell 8) to show human-readable GO descriptions instead of raw GO IDs on the y-axis. The `GO_DESCRIPTIONS` dict in NB04b contains all relevant terms — copy it into NB03b or extract to a shared utility.

6. **[Minor - Methods Precision]** Add a sentence in the REPORT (or a code comment in NB01 Cell 8) noting that missing experiment values in the fitness matrix are replaced with zero in z-score space before computing correlations, and that this approximates but does not equal pairwise-complete Pearson correlation.

7. **[Minor - Reproducibility]** Pin version ranges in `requirements.txt` (e.g., `pandas>=2.0,<3`, `scipy>=1.10`, `statsmodels>=0.14`).

8. **[Minor - Code]** Fix the NB02 Cell 8 f-string: `"AMR modules are {"LARGER" if ... else "similar size to"}"` is missing "than" after "LARGER" — should read "LARGER than".

9. **[Nice-to-have - Analysis]** The REPORT's Future Directions item 4 notes Pfam has 88% coverage. Since `fb_interproscan_pfam.csv` (24 MB) is already in `data/` and loaded in NB03b, a Pfam domain-level enrichment analysis would be straightforward and could reveal more specific functional signals than broad GO terms.

10. **[Nice-to-have - Performance]** Replace the `.apply(lambda r: ..., axis=1)` in NB03b Cell 3 with a merge-based lookup. The current row-wise apply on 179K rows is slow; a `pd.merge` on `['orgId', 'partner_locusId']` would be orders of magnitude faster (see `docs/pitfalls.md`).

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 6 notebooks (51 code cells — all with outputs), 18 data files, 9 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
