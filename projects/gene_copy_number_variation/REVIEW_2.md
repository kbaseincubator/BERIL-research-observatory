---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-5)
date: 2026-07-08
project: gene_copy_number_variation
---

# Review: Gene Copy Number Variation Across Pangenome Functional Categories

## Summary

This project represents exemplary computational biology research at scale. The central finding — that adaptive gene clusters exhibit 8.14× higher copy number variation than housekeeping clusters across 24 bacterial species spanning 5 phyla (p = 5.96×10⁻⁸, 24/24 species direction-consistent) — is statistically robust, biologically interpretable, and novel. The core/accessory interaction analysis reveals that this effect concentrates in accessory clusters (adaptive-accessory 25× adaptive-core), fundamentally reframing the biology from "which genes tolerate paralogy" to "which accessory clusters expand." The methodology is rigorous, the statistical analysis is appropriate with proper multiple-testing correction, and the research plan transparently documents metric refinement based on pilot results. All notebooks contain saved outputs, figures are publication-ready, dependencies are pinned, and the reproduction guide is detailed. The project successfully addresses all gaps identified in REVIEW_1 and is ready for submission.

## Methodology

### Research Question and Hypothesis Testing

The research question addresses a genuine gap in pangenome literature: while presence/absence patterns are well-studied, within-genome paralog copy number by functional category has not been systematically analyzed across bacterial phyla. The hypothesis structure (H0 vs H1a/H1b/H1c) is well-formed with quantitative success criteria that were pre-registered before scale-up.

The operationalization is methodologically sophisticated. After NB01 pilot showed that binary "any multi-copy in ≥1 genome" flags gave only a 1.4× effect (dominated by rare clusters with single occurrences), the team refined to cluster-carrier-weighted multi-copy rate (SUM(multicopy_genomes) / SUM(carrier_genomes)), which gave a 3.3× pilot effect and an 8.1× effect at scale. This weighted metric correctly prioritizes common clusters and is robust to the sparse, rare-event nature of paralog expansion. The plan revision (RESEARCH_PLAN.md v2) transparently documents this change along with the decision to reclassify COG categories J (translation) and C (energy) from "housekeeping" to "mixed" after pilot data revealed known paralog cases (rRNA operons, cytochrome duplications). This kind of data-driven refinement with full documentation is exemplary practice.

The query strategy is appropriate for billion-row tables: per-species iteration over the 3-way `gene × gene_genecluster_junction × gene_cluster` join, filtered on both genome and cluster `gtdb_species_clade_id` to avoid Cartesian explosions, with aggregation in Spark before pandas collection. Species selection (50–249 genomes each, stratified across 5 phyla) balances statistical power with compute feasibility.

### Reproducibility — Fully Addressed

**Notebook outputs**: All four analysis notebooks (NB01, NB01b, NB03, NB04) contain saved outputs showing results, statistical test output, and figure generation. NB02 contains outputs for the manifest generation and concatenation steps; the computationally expensive 24-species extraction was correctly externalized to `src/extract_multi_species.py` as documented in `memories/pitfalls.md`, with the notebook serving as the coordination layer. This is the right architectural choice for long-running Spark jobs.

**Figures**: The `figures/` directory contains 5 PNG files corresponding to all major analysis stages: pilot binary ranking, pilot refined metrics with phylum breakdown, species-level COG distributions, class-by-phylum comparison, and the 2×2 core/accessory interaction. Coverage is complete.

**Dependencies**: `requirements.txt` pins pandas, numpy, scipy, matplotlib, and statsmodels to exact versions. The comment correctly notes that `berdl_notebook_utils` is JupyterHub-provided and references the off-cluster bootstrap script. This is sufficient for reproduction.

**Reproduction guide**: The README's Reproduction section provides step-by-step instructions with estimated runtimes (total ~90 min, dominated by the 80-min extraction script), prerequisites (JupyterHub or off-cluster proxy, auth token, pinned packages, Spark session), and notes on which notebooks need Spark vs run locally (only NB01 and the extraction script hit Spark; NB01b/NB03/NB04 are pandas-only). The script invocation command is explicit with file paths. The note about `data/per_species/*.csv` being gitignored but regeneratable is clear. This is a model reproduction guide.

**Namespace handling**: The project consistently uses `kbase_ke_pangenome` (underscore form) throughout all SQL queries, which is correct for the current Delta-to-Iceberg migration state per `docs/pitfalls.md`. The extraction script includes a sanity check (`SHOW TABLES IN kbase_ke_pangenome`, line 62–71) that would catch a post-migration namespace change. This is good defensive practice.

## Code Quality

### SQL and Statistical Correctness

The SQL queries are correct and efficient. The 3-way join filters on both `genome.gtdb_species_clade_id LIKE '{prefix}%'` and `gene_cluster.gtdb_species_clade_id LIKE '{prefix}%'` (NB01 cell-5, extraction script line 26–27), which is the recommended pattern for billion-row joins. Aggregation happens Spark-side before `.toPandas()` collection. The use of `COUNT(DISTINCT genome_id)` for carrier counts and `SUM(CASE WHEN copy_count > 1 ...)` for multi-copy counts is correct.

Statistical methods are appropriate and well-executed:
- **Paired Wilcoxon signed-rank test** (NB03 cell-6): Correct for testing within-species adaptive > housekeeping with 24 paired observations. One-sided alternative is justified by directional hypothesis.
- **BH-FDR correction** (NB03 cell-10): Applied to 8 pairwise tests (F,H) × (L,V,M,K). All remain significant at adjusted p < 0.01, with smallest p_adj = 4.8×10⁻⁷.
- **Effect size reporting**: Median ratio (8.14×), phylum-stratified ratios (4.0× to 15.4×), and per-COG medians are reported alongside p-values. This is more informative than significance testing alone.
- **Core/accessory interaction** (NB04): The 2×2 design with four one-sided Wilcoxon tests cleanly decomposes the class effect into core vs accessory contributions. All four comparisons are reported with p-values.

No statistical errors detected. The use of nonparametric tests (Wilcoxon) is appropriate given the heavy-tailed distributions visible in the boxplots.

### Pitfall Awareness and Engineering Quality

The project demonstrates excellent pitfall awareness:

**Project-specific pitfall** (`memories/pitfalls.md`): Documents the observed failure mode of `jupyter nbconvert --execute` for long Spark jobs (notebook file not updated after ~1.5hr run, only intermediate CSV survived) and the fix (standalone Python script with per-species incremental output, resumable via skip-if-exists logic, streaming progress via `print(..., flush=True)`). This is a high-quality pitfall capture with actionable fix.

**Weighted metrics for rare events** (REPORT Discoveries section): The finding that weighted rates outperform binary flags for sparse events is correctly generalized to any pangenome analysis where the target is degree rather than presence. This is a transferable methodological insight.

The extraction script (`src/extract_multi_species.py`) is well-engineered:
- Incremental per-species CSV output (resumable)
- Skip-if-exists logic (lines 76–78)
- Namespace sanity check (lines 62–71)
- Clear progress reporting with estimated time remaining (lines 88–90)
- Exception handling per species without killing the entire batch (lines 91–92)

### Notebook Organization

Notebooks are logically organized with clear section headers, markdown cells explaining each step, and incremental artifact saving. The progression (pilot → refined metrics → scale-up → primary tests → interaction analysis) is easy to follow. Code is readable with meaningful variable names (`HOUSEKEEPING`, `ADAPTIVE`, `species_class_core`). The decision to externalize the extraction loop to a script while keeping the notebook as the coordination/documentation layer (NB02) is architecturally sound and well-justified.

## Findings Assessment

### Conclusions Supported by Data

**H1a (housekeeping clusters are copy-number-constrained)**: Species-level median rates are F = 0.062%, H = 0.041%, combined housekeeping = 0.047%. This is 2–3 orders of magnitude below the ~5% rate expected under neutral drift (pseudogene accumulation). The claim that housekeeping clusters are "near-uniformly single-copy" is well-supported. NB03 cell-6 shows 24/24 species have adaptive > housekeeping.

**H1b (adaptive clusters tolerate copy number variation)**: COG L (replication/recombination/repair, includes mobile elements) has median rate 1.12%, which is 24× housekeeping. V, M, K show 0.11–0.12% (2–3× housekeeping). The L-dominance is consistent with L containing transposases and IS elements (cited: Sotiropoulos 2026, Jespersen 2024). All 8 pairwise housekeeping-vs-adaptive tests are significant after BH-FDR correction (smallest p_adj = 4.8×10⁻⁷).

**H1c (pattern holds across phyla)**: 5/5 phyla show adaptive > housekeeping in 100% of their species (4–5 species per phylum). Effect size varies 4-fold (Campylobacterota 4.0×, Pseudomonadota 15.4×), which the authors interpret as reflecting accessory-genome diversity. The phylum-level stratification (NB03 cell-8) is reported as effect size and direction rather than claiming phylum-specific statistical significance, which is appropriate given n=4–5 per phylum.

**H4 (core/accessory interaction)**: Adaptive-accessory (median 1.55%) is 25× adaptive-core (0.06%), while housekeeping-accessory (0.29%) is 10× housekeeping-core (0.03%). Critically, the adaptive-core vs housekeeping-core effect is only 2× (p = 4.9×10⁻⁴), collapsing the 8× species-level main effect. The claim that "the class effect is not primarily about which genes tolerate paralogy at fixation, it is about which clusters get to expand into paralog territory in the first place" (REPORT line 37) is directly supported by NB04's 2×2 breakdown. This is the most important biological insight in the project.

### Limitations Acknowledged

The REPORT's Limitations section (lines 95–101) is thorough:
- 90% AAI clustering ceiling (recent paralogs merged, ancient paralogs split)
- Assembly fragmentation (contig artifacts inflate/deflate counts)
- Species selection bias (oversamples clinical taxa; excludes CPR, Patescibacteria, archaea)
- Coarse functional partition (housekeeping = {F,H} is only ~5% of clusters)
- No direct test for positive selection (observations consistent with purifying selection on housekeeping OR neutral tolerance for adaptive OR mechanistic bias via proximity to mobile elements)

These are legitimate and none are showstoppers. The authors correctly note that distinguishing selection mechanisms requires dN/dS and mobile-element proximity data (Future Direction #1). The only additional limitation worth flagging is that the analysis is restricted to presence-based clusters (genomes either carry or don't carry a cluster) — within-genome heterogeneity (e.g., copy number variation across chromosomes in multi-partite genomes) is not captured. However, this is inherent to the pangenome clustering approach and the authors flag the Spirochaetota outlier (*Borreliella burgdorferi* with multi-partite genome) appropriately.

### Completeness and Visualizations

The analysis is complete. All pre-registered hypotheses (H1a/b/c, H4) are tested. All figures cited in the REPORT exist in `figures/` and are clear, properly labeled, and support the claims:
- `cog_species_rates.png`: Boxplots showing F,H (red) at bottom, L (green) at top
- `class_vs_phylum.png`: Phylum bars with per-species points, showing effect size variation
- `core_accessory_interaction.png`: 2×2 boxplots with p-values, clearly showing the interaction

Color coding is consistent (red = housekeeping, green = adaptive, orange = mixed). No analysis is incomplete or marked "to be filled."

## Discoveries Assessment

The REPORT includes three Discoveries entries (lines 44–48). Each is evaluated as a first-class claim:

**Discovery 1**: "The dosage-constraint × selection story is largely encoded in the core/accessory split, not the COG label."
- **Supported**: NB04 shows adaptive-core (0.06%) is only 2× housekeeping-core (0.03%), while the 8× species-level effect emerges from accessory clusters. Tied to specific results: NB04 cells 2–5, `figures/core_accessory_interaction.png`, `data/core_accessory_stats.csv`.
- **Scope**: "in bacterial pangenomes" — accurate. This is specific to pangenome analyses where core/accessory status is defined.
- **Cross-project value**: High. Any future BERIL project analyzing functional constraint or copy number should stratify by `is_core`.

**Discovery 2**: "Category J (translation) behaves as 'mixed', not housekeeping, at species scale."
- **Supported**: NB01 cell-9 showed J at 2.07% multi-copy (5th of 21 categories), driven by known cases (ribosomal protein paralogs, tRNA/rRNA duplications). Plan revision v2 reclassified J from housekeeping to mixed, which was essential for the housekeeping-vs-adaptive test to be tight.
- **Scope**: "in BERDL pangenome projects using COG functional categories" — accurate and appropriately narrow.
- **Cross-project value**: Moderate. The classic "informational vs operational" divide is an oversimplification; J's behavior is intermediate. This is useful for any project relying on COG-based functional partitions.

**Discovery 3**: "Weighted metrics matter for rare-event enrichment analyses."
- **Supported**: Binary flags gave 1.4× effect (NB01 cell-15); weighted rate gave 3.3× at pilot (NB01b cell-9) and 8.1× at scale (NB03 cell-6). The principle extends beyond copy number to any sparse binary flag.
- **Scope**: "in bacterial pangenome data" — accurate, though the principle is general.
- **Cross-project value**: High. This is a transferable methodological insight applicable to any pangenome analysis with rare events (HGT detection, prophage presence, resistance gene occurrence).

All three discoveries are well-supported, appropriately scoped, and valuable for cross-project surfacing. No overgeneralization detected.

## Performance Notes Assessment

The REPORT includes two Performance Notes (lines 49–52):

**Note 1**: "Per-species iteration on the 3-way join took 140–290s per species."
- **Supported**: NB01 extraction timing and the script output show this range. For 24 species, this is ~80 min total.
- **Actionable**: The recommendation to use CTS batch processing for 100+ species scale-up (Future Direction #3) is appropriate.

**Note 2**: "`jupyter nbconvert --execute` is fragile for long-running Spark jobs."
- **Supported**: Documented failure mode in `memories/pitfalls.md` with fix (standalone script).
- **Actionable**: The pattern (standalone Python script + notebook-as-coordinator) is generalizable.

Both notes are accurate and useful.

## Suggestions

This project is exceptionally strong and ready for submission. The following are minor suggestions for enhancement, not blocking issues:

1. **Future robustness pass** (already noted in Future Directions): Restrict to `checkm_completeness ≥ 95%` and `checkm_contamination ≤ 2%` and re-run NB03 to verify that the L-dominance is not inflated by fragmented assemblies. This would strengthen the claim against the assembly-quality confounder.

2. **IS-element decomposition** (already noted in Future Direction #1): Split COG L into IS-element loci vs true DNA-repair loci. If the effect concentrates in IS elements, the biological story shifts from "adaptive paralogy under dosage balance" to "transposition-mediated CNV." This distinction is important for mechanistic interpretation.

3. **Explicit namespace migration check**: Add a `SHOW TABLES IN kbase.ke_pangenome` attempt at the top of NB01 with a fallback to the underscore form if it fails. This would make the namespace choice self-documenting and future-proof against Iceberg migration.

4. **Spirochaetota multi-partite genome analysis**: *Borreliella* is flagged as an outlier but retained in the analysis. A supplementary analysis excluding Spirochaetota or a brief investigation of whether plasmid-borne clusters drive its elevated housekeeping rate would strengthen the interpretation. (The no-Spiro pooled ratio in NB01b cell-11 already shows robustness, so this is minor.)

5. **Cross-reference with Fitness Browser** (already noted in Future Direction #5): For the ~30 species with FB linkage, test whether paralog-expanded clusters show fitness effects in relevant conditions. This would connect the CNV observation to selection.

None of these block submission. Items 1, 2, and 5 are already flagged in Future Directions. Items 3 and 4 are polish.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-5)
- **Date**: 2026-07-08
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 4 notebooks, 1 extraction script, requirements.txt, 5 figures, 24 per-species data files (verified present), memories/pitfalls.md, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment. This is a re-review following REVIEW_1; all gaps identified in the prior review have been successfully addressed.

<!-- report_hash: sha256:d13f78106dca898b743f95cd91a3768261ab5a3ffaa02907ebf80a0bbbf3d416 -->
