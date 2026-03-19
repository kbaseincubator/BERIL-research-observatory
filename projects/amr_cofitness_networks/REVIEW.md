---
reviewer: BERIL Automated Review
date: 2026-03-19
project: amr_cofitness_networks
---

# Review: AMR Co-Fitness Support Networks

## Summary

This is a scientifically rigorous and well-executed follow-up to `amr_fitness_cost`, mapping the co-fitness neighborhoods of 801 AMR genes across 28 bacteria using full pairwise Pearson correlations from cached fitness matrices and ICA fitness modules. The project stands out for its scientific honesty: the REPORT provides an unusually thorough self-critique, identifying the "shared dispensability" confound as a plausible alternative explanation for the central finding (flagellar/biosynthetic enrichment) and proposing the exact experiment needed to resolve it. The four pre-specified hypotheses (H1–H4) are tested systematically, and negative results (H2 partially unsupported, H3 not supported) are presented alongside positive ones. The annotation quality comparison — where InterProScan GO transforms a null result (0/280 significant with old SEED) into a significant one (35/3,193 significant) — is a concrete methodological contribution. All 6 notebooks are executed with saved outputs, 9 figures cover every analysis stage, and 18 data files are present and internally consistent. The main gaps are (1) the InterProScan annotation extraction code exists only as commented-out Spark SQL in NB03b Cell 2, not as an executable cell; (2) the operon exclusion heuristic uses matrix index position rather than actual genomic coordinates; and (3) the permutation test matches on conservation class but not mean fitness level — a limitation the authors themselves identify as "the single most important follow-up analysis."

## Methodology

**Research question and hypotheses**: The RESEARCH_PLAN pre-specifies four hypotheses (H1–H4) with explicit statistical tests (Fisher's exact with BH-FDR, Mann-Whitney U, Spearman correlation, permutation test), effect directions, expected outcomes, and seven named confounders. This level of pre-registration is well above average for exploratory bioinformatics projects and makes the analysis much easier to evaluate.

**Literature context**: The RESEARCH_PLAN cites 7 relevant papers with PMIDs, grounding the analysis in established cofitness validation (Sagawa et al. 2017), compensatory evolution theory (Eckartt et al. 2024, Patel & Matange 2021), and the intrinsic resistome concept (Cox & Wright 2013). The gap statement — that no study has systematically mapped AMR co-fitness neighborhoods pan-bacterially — is well-defined and appropriately scoped.

**Approach**: The decision to compute full pairwise cofitness from cached fitness matrices rather than using the FB `cofit` table (which stores only top ~96 partners) is correctly motivated and necessary for threshold-based network definition. The 28-organism intersection is verified with explicit locusId overlap checks showing 100% match in NB01 Cell 3. The three-threshold sensitivity analysis (|r| > 0.3, 0.4, 0.5) is good experimental design.

**Data provenance**: Six upstream tables and three prior projects are clearly identified. The cross-project dependency chain (`amr_fitness_cost` → `fitness_modules` → `conservation_vs_fitness`) is documented in the README with specific file paths.

**Reproducibility**: The README includes a clear 6-step reproduction guide with estimated runtimes per notebook, prerequisites, and a note about which notebook requires Spark. The `requirements.txt` file is present with version lower bounds. However, the InterProScan annotation files (`fb_interproscan_go.csv`, `fb_interproscan_pfam.csv`, `fb_bakta_kegg.csv`) are loaded by NB03b and NB04b but produced by Spark queries that appear only as commented-out code in NB03b Cell 2. While the comments do contain the full SQL queries, they are not executable as-is — a new user would need to uncomment and adapt them manually.

## Code Quality

**Notebook organization**: All six notebooks follow a consistent structure: markdown header → imports/paths → data loading → computation → visualization → summary/save. Markdown section headers break each notebook into logical stages. The code is clean, uses descriptive variable names, and includes inline print statements that document intermediate results.

**Pitfall awareness** (checked against `docs/pitfalls.md`):
- **locusId type mismatch**: Handled with `.astype(str)` throughout — NB01 Cell 3 converts both sides before overlap checks, NB01 Cell 8 does the same for matrix indices. This is the single most commonly documented pitfall and it is handled correctly everywhere.
- **FB numeric string columns**: `pd.to_numeric(errors='coerce')` applied to fitness matrices in NB01 Cell 8.
- **`cofit` table limitation**: Correctly identified in both RESEARCH_PLAN and NB01 markdown. The full pairwise computation is the right approach.
- **Row-wise apply performance**: NB03b Cell 4 uses `.apply(lambda r: ..., axis=1)` on 179K rows to map `(orgId, partner_locusId)` tuples to `gene_cluster_id`. Per `docs/pitfalls.md`, this is orders of magnitude slower than a merge-based approach. Not a correctness issue, but affects runtime.

**Cofitness computation (NB01 Cell 8)**: The numpy-vectorized approach is efficient and correct in structure: center each gene's profile, normalize, dot-product. The `np.nan_to_num(..., 0)` step replaces missing experiment values with zero in z-score space before computing correlations. This approximates but does not equal pairwise-complete Pearson correlation — missing data contributes zero to the numerator while the denominator reflects the full experiment count. The REPORT Limitations section (item 2) acknowledges this approximation and notes it is unlikely to affect conclusions for the relatively dense FB matrices.

**Operon exclusion (NB01 Cell 8)**: The 5-ORF exclusion uses `abs(locus_to_idx[partner] - locus_to_idx[amr_locus]) <= 5` — matrix index position as a proxy for genomic proximity. This is approximate: the matrix row order reflects how genes were loaded from the fitness matrix CSV, which is not guaranteed to match chromosomal gene order. Only 995/180,370 pairs (0.6%) are excluded, which is suspiciously low for 28 genomes and could indicate the heuristic is not reliably identifying proximal genes. The genomic coordinates (`begin`, `end`, `scaffoldId`, `strand`) are already loaded in NB01 Cell 12 but are not used. Both the RESEARCH_PLAN and REPORT acknowledge this approximation.

**Module coverage label (NB01 Cell 3)**: The `pct_in_module_file` column and the final print statement ("In module file index: 801/801") check whether AMR locusIds appear in the module membership file index (which contains ALL genes, not just those assigned to modules). The variable is correctly labeled `pct_in_module_file` with a clarifying comment, but the final print line says "Module coverage: 100.0%" which could mislead. The correct 24% figure is computed independently in NB01 Cell 5 and NB02.

**Permutation test (NB03 Cell 8)**: Runs 200 permutations instead of the planned 1,000. A code comment explains the reduction. For the main conclusion (no significant SEED enrichment), this is adequate. The null result at 200 draws would remain null at 1,000.

**Sensitivity analysis at |r| > 0.4 (NB03b Cell 10)**: This is a strength. The notebook runs the full GO enrichment at the stricter |r| > 0.4 threshold and finds the signal is actually *stronger*: flagellum assembly significant in 8 organisms (vs 5 at |r| > 0.3), flagellum-dependent motility in 7 organisms (vs 5), tryptophan biosynthesis in 6 organisms (vs 3). This confirms the enrichment is not driven by a tail of weak correlations and significantly strengthens the main finding.

**Statistical methods**: Fisher's exact test with BH-FDR correction is appropriate for the enrichment analyses. The FDR scope (within each organism for NB03/NB03b, within each mechanism-organism pair for mechanism-specific tests) is correctly applied and matches the RESEARCH_PLAN specification. Mann-Whitney U for module size comparisons and Spearman for the network-size-vs-cost correlation are both appropriate non-parametric choices.

## Findings Assessment

**H1 (AMR support networks enriched for specific functions)**: Supported with InterProScan GO. Six GO terms significant in ≥3 organisms (FDR < 0.05): four flagellar terms (motility, assembly, swarming, bacterial-type flagellum; 4–5 organisms, mean OR 4.7–5.3) and two amino acid biosynthesis terms (histidine, tryptophan; 3 organisms, OR 5.3). The comparison with old SEED annotations (0/280 significant) is properly retained as a baseline. The sensitivity check at |r| > 0.4 confirms and strengthens these results. Crucially, the REPORT provides an intellectually honest discussion of the shared dispensability confound: flagella are useless in shaken liquid culture, biosynthesis is redundant in supplemented media, and AMR genes are dispensable without antibiotics — all three gene classes are metabolic burdens under FB experimental conditions. The proposed follow-up (fitness-matched permutation) is exactly the right test.

**H2 (Efflux in stress modules, enzymatic in isolated modules)**: Partially tested. AMR-containing modules are larger than non-AMR modules (median 46 vs 27, p = 1.7×10⁻⁸) and 99% are in cross-organism conserved families. But efflux vs enzymatic module sizes are indistinguishable (both median 48, MWU p = 0.91). H2 as formulated is not supported. The REPORT correctly frames this as a partial result.

**H3 (Network size predicts fitness cost)**: Not supported (Spearman rho = −0.006, p = 0.87, N = 769). Holds within each mechanism. Properly contextualized as possibly reflecting narrow cost variance (std = 0.15) rather than absence of a real relationship.

**H4 (Support networks conserved across organisms)**: The organism-specificity finding is the project's most robust result. Cross-mechanism Jaccard (same organism) = 0.375 vs within-mechanism Jaccard (different organisms) = 0.207, MWU p = 4.3×10⁻¹³. As the REPORT notes, this finding is robust to the dispensability confound because it is a structural observation about genome co-regulation architecture. The finding also connects back to `amr_fitness_cost`: mechanism predicts conservation but not cost, and now we see that the cost context is organism-determined.

**Annotation quality lesson**: The SEED → InterProScan comparison (0/280 vs 35/3,193 significant enrichments; Jaccard 0.069 vs 0.207 for cross-organism conservation) is a genuine methodological contribution. The 68% GO coverage vs variable SEED coverage explains why prior analyses may have missed functional signals in cofitness data.

**Limitations**: Seven specific limitations are documented in the REPORT, prioritized appropriately. The shared dispensability discussion is genuinely insightful and has implications beyond AMR — it identifies a general caveat for all cofitness-based functional inference using lab-grown organisms.

**Completeness**: No incomplete analyses or placeholder text. All 18 data files listed in REPORT.md are present in `data/`. All 9 figures referenced in the REPORT are present in `figures/`. The three-document structure (README → RESEARCH_PLAN → REPORT) is well-organized and internally consistent.

## Suggestions

1. **[Critical — Reproducibility]** Make the InterProScan data extraction executable. NB03b Cell 2 contains the Spark SQL queries as comments but they cannot be run as-is. Convert to an executable cell guarded by `if not os.path.exists(os.path.join(DATA, 'fb_interproscan_go.csv')):` so the notebook either regenerates annotations from Spark (on JupyterHub) or loads cached files (locally). This is the single most important reproducibility gap — without it, a new user cannot reproduce NB03b or NB04b from scratch.

2. **[Moderate — Methodology]** Replace the index-position operon exclusion with a coordinate-based one. The `begin`, `end`, `scaffoldId`, and `strand` columns are already loaded in NB01 Cell 12 — build a per-organism lookup of `{locusId: (scaffoldId, begin, end, strand)}` and exclude partners within a defined chromosomal distance (e.g., 10 kb on the same scaffold and strand). The current heuristic excludes only 0.6% of pairs, which may reflect that index order does not match chromosomal order. A proper coordinate-based exclusion would give more confidence that the support networks are not confounded by polar effects.

3. **[Moderate — Methodology]** Run the fitness-matched permutation test identified as "the single most important follow-up" in the REPORT. Drawing random non-AMR genes matched on mean fitness level (−0.05 to +0.05) and comparing their cofitness neighborhoods' GO enrichment to AMR genes would directly resolve the shared-dispensability question. This could be added as a cell in NB03b without a new notebook.

4. **[Minor — Code]** Fix the misleading "Module coverage: 100.0%" print statement in NB01 Cell 3. The variable is already named `pct_in_module_file` with a clarifying comment, but the final print line still says "Module coverage." Change to: `print(f'In module file index: {org_stats_df["amr_in_modules"].sum()}/{org_stats_df["amr_in_matrix"].sum()} (note: file index coverage, not module assignment)')`.

5. **[Minor — Performance]** Replace `.apply(lambda r: ..., axis=1)` in NB03b Cell 4 with a merge-based lookup per `docs/pitfalls.md`. Create a DataFrame from the `locus_to_cluster` dict and merge on `['orgId', 'partner_locusId']` — this would be orders of magnitude faster on 179K rows.

6. **[Minor — Methods precision]** Add a brief note in the REPORT Methods or a code comment in NB01 Cell 8 explicitly stating that missing experiment values are replaced with zero in z-score space (`np.nan_to_num`) and that this approximates pairwise-complete Pearson correlation. The current Limitations item 2 mentions this but it could be more prominent.

7. **[Nice-to-have — Analysis]** Leverage the already-loaded Pfam annotations (`fb_interproscan_pfam.csv`, 88% coverage, 229K rows) for domain-level enrichment analysis. Pfam's higher coverage and more specific domain-level vocabulary could reveal support network functions masked by broad GO terms like "membrane" and "transmembrane transport." The REPORT Future Directions item 4 identifies this as a next step, and the data is already in hand.

8. **[Nice-to-have — Verification]** Directly check whether flagellar gene knockouts show positive mean fitness across FB experiments, as proposed in REPORT Future Directions item 3. This would take ~10 lines of code in NB03b: load all gene fitness values, filter to genes annotated with GO:0071973 (flagellar motility), and plot their mean fitness distribution. If the distribution overlaps with AMR gene fitness, the shared-dispensability interpretation is strengthened.

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 6 notebooks (all with saved outputs), 18 data files (81 MB total), 9 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
