---
reviewer: BERIL Automated Review
date: 2026-03-19
project: amr_cofitness_networks
---

# Review: AMR Co-Fitness Support Networks

## Summary

This is a well-executed follow-up to `amr_fitness_cost` that maps the co-fitness support networks of AMR genes across 28 bacteria. The project has excellent reproducibility hygiene — all 6 notebooks are fully executed with 100% output coverage, 9 figures cover every major analysis stage, and the README includes a clear reproduction guide. The three-file structure (README/RESEARCH_PLAN/REPORT) is cleanly maintained. The most scientifically compelling contribution is the annotation quality comparison: showing that legacy SEED/KEGG annotations produce a null result (0/280 significant) while InterProScan GO annotations reveal genuine signal (35/3,193 significant) is a concrete, reproducible methodological lesson. The key biological findings — AMR genes are co-regulated with flagellar motility and amino acid biosynthesis, and support networks are organism-specific rather than mechanism-specific — are supported by the data shown and well-situated in the literature. A few gaps in reproducibility and code correctness warrant attention before the project is cited or extended.

## Methodology

**Research question**: Clearly stated and testable. Four numbered hypotheses (H1–H4) are operationally defined with explicit statistical tests and FDR correction strategies. The RESEARCH_PLAN documents null models, permutation designs, and power concerns — a well-above-average level of prespecification.

**Approach**: The decision to compute full pairwise cofitness from cached fitness matrices (rather than using the `cofit` table, which stores only the top ~96 partners per gene) is correctly motivated and documented. The 28-organism intersection is verified with explicit locusId overlap checks in NB01.

**Data sources**: Clearly identified across six upstream tables and three prior projects. The cross-project dependency chain (`amr_fitness_cost` → `fitness_modules` → `conservation_vs_fitness`) is documented in the README.

**Reproducibility concern — missing extraction code**: `fb_interproscan_go.csv` (18 MB), `fb_interproscan_pfam.csv` (24 MB), and `fb_bakta_kegg.csv` (1.6 MB) are present in `data/` and loaded by NB03b/NB04b, but no notebook contains the Spark queries that extracted these from `kbase_ke_pangenome.interproscan_go`, `kbase_ke_pangenome.interproscan_domains`, or `bakta_annotations`. The README notes NB03b "requires Spark for data extraction step" but a reproducer would not know what queries to run. This is the single most significant reproducibility gap. A short data extraction cell at the top of NB03b (even if guarded by a `if not os.path.exists(...)` check) would close this gap.

## Code Quality

**Overall**: Code is clean, logically organized, and consistently structured. Each notebook follows setup → load → compute → visualize → save, with markdown section headers. Pitfall awareness is good: the known `locusId` integer/string type mismatch (flagged in `docs/pitfalls.md`) is handled with explicit `.astype(str)` on both sides in NB01; FB numeric columns are handled with `pd.to_numeric(errors='coerce')`.

**Cofitness computation (NB01 Cell 9)**: The numpy vectorized correlation uses `np.nanmean` for centering and `np.nansum` for norm computation, then replaces remaining NaN with zero before the dot product (`np.nan_to_num(..., 0)`). This is a common approximation but not equivalent to pairwise-complete Pearson correlation: experiments where one gene has a missing value contribute 0 to the numerator but are excluded from the denominator, creating an asymmetric bias toward zero for pairs with sparse coverage. The REPORT describes these as "Pearson correlations" without qualification. For the Fitness Browser matrices (which are relatively dense), this is unlikely to change conclusions materially, but it should be noted in the Methods section of the REPORT.

**Module coverage label in NB01 (Cell 4)**: The `pct_in_modules` column in `org_stats_df` measures whether AMR gene locusIds appear in the module membership *file* index (a gene × module matrix containing ALL genes), not whether they are assigned to any module. The corresponding print statement outputs "Module coverage: 100.0% of AMR genes with fitness data," which contradicts the correct 24% figure computed in NB02. The variable and print label should read `pct_in_module_file` to avoid confusion. This does not affect any downstream results (NB02 correctly computes the 24% figure independently), but it is misleading in the intermediate output.

**Operon exclusion (NB01 Cell 9)**: The 5-ORF exclusion uses matrix row index position as a proxy for genomic position (`abs(locus_to_idx.get(partner) - locus_to_idx.get(amr_locus)) <= 5`). The fitness matrix index order reflects the order genes appear in the FB gene table, which is not guaranteed to reflect genomic chromosomal order. As a result, this exclusion may be effectively random rather than proximity-based. Only 0.6% of pairs (995/180,370) are excluded, which could indicate either that few proximal gene pairs show strong cofitness, or that the heuristic is not identifying truly proximal genes. The RESEARCH_PLAN correctly flags this as approximate, and the REPORT limitations section acknowledges it. A proper genomic-coordinate-based exclusion using the `begin`/`end` columns available in the gene annotation table (`NB01 Cell 13` loads these) would strengthen this control.

**Fisher enrichment in NB03b (Cell 6)**: The background set for each organism is built from all genes in the FB–pangenome link (`all_locus_clusters[org]`), while the foreground is all extra-operon partner gene clusters. At |r| > 0.3, mean partner set size is 233 genes per AMR gene; the test is asking whether GO terms in this large set are enriched over the genome background. With support sets this large, the test has high power to detect even small frequency differences. The key flagellar motility terms show mean odds ratios of 4.7–5.3, which are genuine enrichments regardless of power. However, confirming the key findings hold at |r| > 0.4 (110 gene mean network) would add confidence that these are not driven by the tail of weak correlations.

**GO enrichment figure (NB03b Cell 9)**: The bar chart shows raw GO IDs (e.g., GO:0071973) rather than human-readable descriptions on the y-axis. The GO_DESCRIPTIONS dict exists in NB04b but is not imported into NB03b. The figure is thus not self-explanatory without consulting the REPORT table. Adding `go_term_labels = [GO_DESCRIPTIONS.get(t, t) for t in top_go.index]` and using those for `ax.set_yticklabels` would make the figure publication-ready.

**requirements.txt**: Lists 6 packages without version pins. Pinning major versions (e.g., `pandas>=2.0,<3`, `statsmodels>=0.14`) would improve long-term reproducibility.

**Known pitfalls addressed**:
- ✅ locusId type mismatch (integer vs string) — handled explicitly
- ✅ FB numeric string columns — `pd.to_numeric(errors='coerce')` applied
- ✅ `cofit` table limitation (top-96 only) — correctly identified and worked around
- ✅ KEGG join path through `besthitkegg` — not needed here (uses cached annotations), no issue
- ✅ Unnecessary `.toPandas()` on large tables — all Spark work is pre-extracted; local analysis uses pandas throughout

## Findings Assessment

**H1 (AMR genes enriched for specific functional categories)**: Supported with InterProScan GO annotations. Flagellar motility (GO:0071973, GO:0044780; 5 organisms, mean OR ≈ 5) and amino acid biosynthesis (GO:0000105, GO:0000162; 3 organisms, mean OR ≈ 5.3) are the key signals. The baseline SEED analysis (0/280 significant) is retained as a comparison, which is good scientific practice. The biological interpretation — PMF competition between efflux pumps, flagella, and aromatic biosynthesis — is coherent and properly cited (Olivares Pacheco et al. 2017).

**H2 (Efflux in stress modules vs enzymatic in isolated modules)**: Not clearly supported or refuted. NB02 finds that AMR-containing modules are larger than non-AMR modules (p = 1.7×10⁻⁸), and 99% are in cross-organism conserved families — but the mechanism-level comparison (efflux vs enzymatic module size) shows no significant difference (MWU p = 0.91). The REPORT accurately characterizes this as partial support.

**H3 (Network size predicts fitness cost)**: Correctly reported as not supported (Spearman rho = −0.006, p = 0.87). This null result is retained and properly interpreted as potentially reflecting narrow cost variance rather than absence of relationship. The 0.086 mean cost with narrow distribution from `amr_fitness_cost` is cited as context.

**H4 (Support networks conserved across organisms for same mechanism)**: Supported with a twist — networks are more organism-specific (cross-mechanism J = 0.375) than mechanism-specific (within-mechanism J = 0.207), with a highly significant difference (p = 4.3×10⁻¹³). This is a nuanced and interesting finding. The comparison between old KEGG (cross < within, p = 1.0) and InterProScan GO (cross > within, p = 4.3×10⁻¹³) effectively demonstrates the annotation quality effect.

**Limitations section**: Honest and specific. Six limitations are listed, including the ones most pertinent to the conclusions (cofitness ≠ co-regulation, broad GO term granularity, large network sizes at |r| > 0.3, FB organism bias, operon exclusion heuristic, H3 power concern). No incomplete or "to be filled" sections were found.

**Data files**: All 12 data files listed in REPORT.md are present in `data/`. File sizes are consistent with reported row counts.

**Figures**: All 9 figures referenced in REPORT.md are present and dated 2026-03-19 (same-day generation). The `support_network_enrichment.png` (null result from old SEED analysis) is an excellent inclusion — showing the failed analysis strengthens the annotation quality argument.

## Suggestions

1. **[Critical — Reproducibility]** Add a data extraction cell or a standalone notebook to document the Spark queries used to produce `fb_interproscan_go.csv`, `fb_interproscan_pfam.csv`, and `fb_bakta_kegg.csv`. A cell guarded by `if not os.path.exists(...)` at the top of NB03b would allow the notebook to either regenerate annotations from Spark or load the cached files. Without this, a new user cannot reproduce the core analysis from scratch.

2. **[Moderate — Code Correctness]** Fix the "Module coverage: 100%" label in NB01. Rename `pct_in_modules` to `pct_in_module_file` and update the print statement accordingly. This prevents misleading readers about the 24% actual module membership rate. Alternatively, add a brief explanatory comment.

3. **[Moderate — Methodology]** Replace the index-position-based operon exclusion with a coordinate-based one. The `begin`, `end`, and `strand` columns are already loaded in NB01 Cell 13 (`annotations` DataFrame). Build a per-organism lookup of `{locusId: (scaffoldId, begin, end, strand)}` and exclude partners within X kb on the same scaffold and strand. This would make the 5-ORF exclusion meaningful.

4. **[Moderate — Findings]** Confirm that the flagellar motility and amino acid biosynthesis enrichments hold at |r| > 0.4 (mean network size ~110 genes). A 2–3 line addition to NB03b Cell 6 running the same Fisher tests on the `|r| > 0.4` subset would strengthen the main conclusion. Report the results as a sensitivity check in the REPORT.

5. **[Minor — Figure Quality]** Update the NB03b enrichment figure to show human-readable GO descriptions on the y-axis instead of raw GO IDs. The `GO_DESCRIPTIONS` dict already exists in NB04b and lists the 15 most relevant terms — copy it into NB03b (or a shared utility) and use it when setting y-tick labels.

6. **[Minor — Reproducibility]** Add version pins to `requirements.txt`. At minimum: `pandas>=2.0`, `numpy>=1.24`, `scipy>=1.10`, `statsmodels>=0.14`, `matplotlib>=3.7`, `seaborn>=0.12`. This prevents silent API changes from breaking the notebooks.

7. **[Minor — Methods clarity]** Add a sentence to the REPORT Methods section (or a comment in NB01 Cell 9) noting that missing experiment values in the fitness matrix are treated as zero in the z-score space when computing correlations, and that this approximates but does not equal pairwise-complete Pearson correlation. This keeps the methods precise without over-inflating the issue.

8. **[Nice-to-have]** The REPORT's Future Directions section item 1 ("Pfam domain-level enrichment") notes that Pfam has 88% coverage. Since `fb_interproscan_pfam.csv` (24 MB) is already in `data/` and loaded in NB03b, a Pfam-level enrichment analysis would be straightforward. This would make NB03b/04b a single complete annotation analysis rather than requiring a new notebook.

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 6 notebooks (63 cells, 51 code cells — all with outputs), 18 data files, 9 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
