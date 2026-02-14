---
reviewer: BERIL Automated Review
date: 2026-02-14
project: conservation_vs_fitness
---

# Review: Conservation vs Fitness — Linking FB Genes to Pangenome Clusters

## Summary

This is an exceptionally well-executed cross-database analysis that bridges Fitness Browser RB-TnSeq essentiality data with KBase pangenome conservation classifications across 33 diverse bacteria. The project asks a clear, testable question — are essential genes preferentially conserved in the core genome? — and answers it with appropriate statistical rigor (Fisher's exact test with BH-FDR correction, median OR=1.56, 18/33 significant). The functional characterization adds genuine biological insight: essential-core genes are enzyme-rich and well-annotated (41.9% enzymes, 13.0% hypothetical), while essential-auxiliary and essential-unmapped genes represent poorly characterized frontiers (38–58% hypothetical). The project excels in pipeline architecture (clean Spark/local separation via `src/` scripts with cached TSV intermediates), documentation (thorough README with quantitative results, literature context, candid limitations, and step-by-step reproduction guide), and pitfall awareness (correctly handles GTDB renames, FB string-typed columns, KEGG join paths, locus tag mismatches). The main areas for improvement are minor: NB01/NB02 lack saved outputs, a few README numbers don't match the NB04 actuals after Dyella79 exclusion, and the SEED hierarchy extraction step is documented but not integrated into the pipeline script.

## Methodology

**Research question**: Clearly stated and testable. The two-phase structure (Phase 1: build the link table; Phase 2: essential genes vs conservation) is well-motivated and logically sequenced. The extension into functional characterization (Sections 6–8 of NB04) goes beyond the original question to provide genuinely useful biological insight.

**Organism matching**: The three-strategy approach (NCBI taxid → NCBI organism name → scaffold accession) is thorough and well-justified given GTDB taxonomic renames. The `src/run_pipeline.py` script properly escapes single quotes in organism names (lines 168–169), demonstrating attention to SQL safety. Multi-clade resolution by DIAMOND hit count is a reasonable heuristic, and the NB03 output confirms it works correctly — for example, Pseudomonas organisms mapped to multiple GTDB sub-clades are resolved to the best-fitting one.

**Essential gene definition**: Well-documented as an upper bound on true essentiality (type=1 CDS absent from `genefitness`). The NB04 header includes a thorough explanation of why this definition is necessary — after checking all 45 tables in `kescience_fitnessbrowser`, there is no explicit essentiality flag. The gene length validation (NB04 Section 1, Mann-Whitney U test) directly addresses the insertion bias concern raised by Goodall et al. (2018), and this caveat is honestly acknowledged in the README Limitations.

**Statistical methods**: Fisher's exact test per organism with Benjamini-Hochberg FDR correction is appropriate for the 2×2 contingency tables (essential/non-essential × core/non-core). Spearman correlations for pangenome context variables (clade size, openness) are suitable for non-normal distributions. The lifestyle stratification (Section 5) provides an additional biological dimension.

**Data sources**: Comprehensively documented in a README table covering 10 database tables plus external protein sequences. The KEGG annotation join path (`besthitkegg → keggmember → kgroupdesc`) correctly follows the pattern documented in `docs/pitfalls.md`, avoiding the known join-key gotcha.

## Code Quality

**SQL queries**: Correct and efficient throughout. Key observations:
- The `extract_essential_genes.py` queries properly use `orgId` filters on the 27M-row `genefitness` table and cast coordinate columns with `CAST(begin AS INT)` / `CAST(end AS INT)`, consistent with the documented pitfall that all FB columns are strings.
- Per-clade FASTA extraction in `run_pipeline.py` uses exact equality on the partitioned `gtdb_species_clade_id` column rather than LIKE patterns — consistent with performance guidance in `docs/pitfalls.md`.
- The KEGG join in `extract_essential_genes.py` (lines 120–128) correctly follows the three-table `besthitkegg → keggmember → kgroupdesc` path.
- The `type = '1'` filter (string comparison) for protein-coding genes is correct given the all-strings schema.

**Pitfalls from `docs/pitfalls.md` addressed**:
- ✅ String-typed numeric columns: Cast before comparison throughout
- ✅ FB gene table has no essentiality flag: Derives essentiality from absence in `genefitness`
- ✅ FB aaseqs locus tag mismatch: Dyella79 explicitly excluded with clear documentation
- ✅ KEGG annotation join path: Uses correct `besthitkegg → keggmember → kgroupdesc` chain
- ✅ Spark LIMIT/OFFSET pagination: Uses per-clade queries instead of pagination
- ✅ Core/auxiliary/singleton mutual exclusivity and subset relationship: Correctly handled
- ✅ Gene clusters are species-specific: Cross-species comparison uses SEED/KEGG annotations, not cluster IDs
- ✅ `seedannotation` used for functional descriptions (not `seedclass`)
- ✅ Large table filters: Always filters by `orgId` when touching `genefitness`

**Notebook organization**: NB03 and NB04 follow a clean, consistent structure: markdown header (purpose, inputs, outputs, requirements) → setup → data loading → analysis → QC → visualization → summary. Section headers with numbered markdown cells make the flow easy to follow. NB04 is the densest (25 cells, 8 sections) but remains well-organized with clear progression from overview → core question → stratification → functional enrichment.

**Shell script**: `run_diamond.sh` is well-written with `set -euo pipefail`, proper argument validation with usage message, a cleanup trap for temp files, progress reporting, and caching (skip organisms with existing output). The DIAMOND parameters (`--id 90 --max-target-seqs 1`) are appropriate for same-species high-identity searches.

**`src/` scripts**: Both `run_pipeline.py` and `extract_essential_genes.py` are well-structured, with proper Spark session management via `berdl_notebook_utils.setup_spark_session`, progress reporting, and caching checks (skip if output file exists). The pipeline design — extract to TSV, then analyze locally — is the correct pattern for BERDL work.

**Minor code issues**:
1. In NB01 (cell `cell-name-match`), the NCBI name matching interpolates `genus` and `species` directly into SQL LIKE patterns without escaping single quotes. The `run_pipeline.py` version correctly handles this with `replace("'", "''")`. The notebook version should do the same for consistency.
2. In NB03, the conservation stacked bar chart (cell `cell-qc-conservation`) plots core + auxiliary + singleton as additive bars. Since singletons are a subset of auxiliary (documented in `docs/pitfalls.md`), the chart visually overstates the total. The text output is correct — only the visualization is affected.
3. The NB03 spot check shows `MR1:SO_0001 → NO MATCH` and `MR1:SO_0002 → NO MATCH` without explanation. Since MR1 has 96.9% coverage overall, these are likely edge cases worth a brief note.

## Findings Assessment

**Core result well-supported**: The finding that essential genes are modestly enriched in core clusters (median OR=1.56, 18/33 organisms significant after BH-FDR) is convincingly demonstrated through the forest plot, per-organism 2×2 tests, and appropriate multiple testing correction. The honest characterization as "modest" enrichment — noting that most genes in well-characterized bacteria are core regardless of essentiality — shows good scientific judgment.

**Functional analysis adds depth**: The four-way breakdown (essential-core / essential-auxiliary / essential-unmapped / nonessential) with enzyme classification and SEED/KEGG category analysis goes well beyond the core question:
- Essential-core genes: 41.9% enzymes, 13.0% hypothetical, enriched in Protein Metabolism (+13.7 pp), Cofactors/Vitamins (+6.2 pp)
- Essential-auxiliary genes: 13.4% enzymes, 38.2% hypothetical, top subsystems include ribosomes, DNA replication, type 4 secretion
- Essential-unmapped genes: 58.1% hypothetical, dominated by divergent ribosomal proteins (L34, L36, S11, S12), transposases, DNA-binding proteins
- The depletion of Carbohydrates (-7.9 pp) and Membrane Transport (-4.0 pp) in essential-core genes — "functions that tend to be conditionally important" — is a biologically satisfying interpretation

**Limitations comprehensively acknowledged**: The README's five-point Limitations section covers essentiality definition bias, small-clade core fraction inflation, E. coli exclusion, single growth condition, and coverage-based organism exclusion. The gene length validation (NB04 Section 1) directly tests the most important potential confound.

**Literature context**: Five relevant references cited with DOIs and PMIDs. The Rosconi et al. (2022) parallel is particularly apt — their universal essential / core strain-specific / accessory essential categories map directly onto essential-core / essential-auxiliary / essential-unmapped. The Hutchison et al. (2016) quantitative comparison (31% unknown function in minimal genome vs 44.7% hypothetical in essential-unmapped) strengthens the findings.

**Stratification analyses**: The Spearman correlations between odds ratio and clade size/openness (NB04 Section 4) and the lifestyle stratification (NB04 Section 5) provide important context, addressing whether the enrichment is an artifact of pangenome structure vs a genuine biological pattern.

**Number inconsistencies between README and NB04**: The README reports some figures that appear to predate the Dyella79 exclusion in NB04:
- README: "34 organisms" → NB04 actual: 33 (after Dyella79 exclusion)
- README: "28,399 putative essential genes" → NB04: 27,693
- README: "153,143 protein-coding genes" → NB04: 148,826
- README: "1,965" essential-unmapped → NB04: 1,259
- README: "18 of 33 organisms" significant → NB04: 18/33 (this one matches)

These are not errors in the analysis — the NB04 code and outputs are internally consistent. The README just needs to be updated to reflect the final 33-organism dataset. The key results (OR=1.56, 18/33 significant, functional breakdown percentages) are correct in both places.

## Suggestions

1. **[Important] Reconcile README numbers with NB04 actuals**: Update the README to consistently use the 33-organism, post-Dyella79 numbers: 148,826 total protein-coding genes, 27,693 essential (18.6%), 1,259 essential-unmapped. The percentages and statistical results in the README already match NB04, so this is primarily a matter of updating the raw counts and the "34 organisms" references.

2. **[Important] Add `seed_hierarchy.tsv` extraction to `extract_essential_genes.py`**: The SQL query for generating `seed_hierarchy.tsv` is documented in a NB04 markdown cell and actually included in `extract_essential_genes.py` (lines 166–179) — however, it has a caching check that skips if the file exists. This is good. But a reader following the reproduction steps from scratch needs to know this file is generated by `extract_essential_genes.py` step 4, not a separate manual step. A note in the README's reproduction section would help.

3. **[Moderate] Save NB01 and NB02 notebook outputs**: These two Spark-dependent notebooks have 0 code cells with saved outputs (vs 15/15 and 18/18 for NB03 and NB04). Since they require BERDL JupyterHub access to re-run, a reader cannot verify organism matching statistics, QC results, or extraction progress without Spark access. Running `jupyter nbconvert --execute` and saving the executed notebooks would preserve this narrative context alongside the cached TSV files.

4. **[Minor] Fix NB03 conservation stacked bar chart**: The bar chart in `cell-qc-conservation` plots core + auxiliary + singleton as additive bars. Since singletons ⊂ auxiliary (per `docs/pitfalls.md`), this overstates the total. Plot as core + (auxiliary − singleton) + singleton, or core + auxiliary with singleton as an overlay/annotation.

5. **[Minor] Explain MR1 spot-check failures in NB03**: `MR1:SO_0001` and `MR1:SO_0002` show "NO MATCH" despite 96.9% overall coverage. A brief note explaining why (e.g., short genes below identity threshold, or non-standard locus tag format for these specific genes) would help readers interpret the QC results.

6. **[Minor] Escape single quotes in NB01 organism name matching**: The notebook version of the NCBI name matching (cell `cell-name-match`) interpolates genus/species directly into SQL without escaping. Apply the same `replace("'", "''")` fix used in `src/run_pipeline.py` for consistency and to guard against species names containing apostrophes.

7. **[Nice-to-have] Add DIAMOND query coverage filter**: `run_diamond.sh` uses `--id 90` but no `--query-cover` flag. The high median identity (100.0%) and coverage (94.2%) suggest current results are clean, but adding `--query-cover 70` would guard against partial-length matches in future runs.

8. **[Nice-to-have] Clean up empty `data/strain_fastas/` directory**: This directory exists (10 bytes, created 2026-02-10) but appears to be from an abandoned approach. Either remove it or add a note explaining its purpose.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-14
- **Scope**: README.md, 4 notebooks, 3 src scripts, 10 data files, 8 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
