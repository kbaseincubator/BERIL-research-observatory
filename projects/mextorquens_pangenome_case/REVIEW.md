---
reviewer: BERIL Automated Review
date: 2026-02-19
project: mextorquens_pangenome_case
---

# Review: M. extorquens Pangenome Case Study — B Vitamin Auxotrophy and Lanthanide-Dependent MDH

## Summary

This is a well-executed single-notebook project that asks two clear, complementary questions about *Methylobacterium extorquens*: (1) which B vitamin biosynthesis pathways are incomplete, and (2) does eggNOG misannotate the lanthanide-dependent methanol dehydrogenase xoxF as mxaF? The analysis delivers a striking finding — EC/KEGG-based reclassification completely inverts the MDH profile across 49 species — and actionable auxotrophy predictions for riboflavin and thiamine. The notebook has saved outputs, the pathway classifier was carefully audited to remove contamination from related pathways, and the README/REPORT documentation is thorough with proper literature context and limitations. The main areas for improvement are: no cached data files are saved (preventing local reproduction), no RESEARCH_PLAN.md exists, and the project would benefit from additional figures for the MDH reclassification and B12 core/accessory variability findings.

## Methodology

**Research questions** are clearly stated and testable. The README poses three specific questions (B vitamin auxotrophy, xoxF/mxaF classification reliability, cross-species MDH profiles), and each is addressed in dedicated notebook sections.

**Approach is sound.** The B vitamin pathway completeness assessment uses a curated gene list with KEGG KO cross-referencing, and the project documents an important methodological refinement: removing KEGG pathway number matching (which pulled in bacteriochlorophyll, molybdopterin, and other contaminants) in favor of gene-name + KEGG-KO-only matching. This audit is well-documented in cell `b5` and the REPORT.

**MDH classification logic is rigorous.** The priority system (EC/KEGG over Preferred_name, with explicit ambiguity tracking) is clearly implemented in cell `b8a`, and the zero-ambiguous-cluster result is reported transparently.

**Data sources are clearly identified** in the README's Data Sources table (3 tables from `kbase_ke_pangenome`). The SQL queries use the correct join pattern (`eggnog_mapper_annotations.query_name` → `gene_cluster.gene_cluster_id`), consistent with `docs/pitfalls.md` guidance.

**Reproducibility gaps:**
- No RESEARCH_PLAN.md exists. While the README serves as a reasonable substitute, the three-file structure (README / RESEARCH_PLAN / REPORT) documented in `docs/pitfalls.md` is the observatory standard.
- The `data/` directory is empty (only `.gitkeep`). No intermediate CSV/TSV files are saved, so reproducing downstream analysis requires re-running the full Spark notebook on JupyterHub. Saving `bvit_pd`, `mdh_all_pd`, `mdh_species_pd`, and `bvit_pivot` as CSV files would enable local analysis and figure regeneration without Spark access.
- The Reproduction section in the README is minimal ("Upload notebook to BERDL JupyterHub; Run all cells"). It does not mention expected runtime for specific cells, Spark session requirements, or how to verify successful completion.

## Code Quality

**SQL queries are correct and follow best practices.** The queries use proper join keys (`e.query_name = gc.gene_cluster_id`), join through `gtdb_species_clade` for taxonomy filtering, and use `LIKE '%extorquens%'` appropriately for species discovery (though exact equality would be faster per pitfalls.md, the LIKE pattern is justified here for initial exploration across two subspecies clades).

**Spark import pattern** (`from berdl_notebook_utils import get_spark_session`) matches the documented JupyterHub import pattern from `docs/pitfalls.md`, though the canonical form documented there is `from berdl_notebook_utils.setup_spark_session import get_spark_session`. Both likely work but should be verified.

**B vitamin classifier (cell `b5`)** is well-designed. The `classify_bvit_pathway` function matches by gene name and KEGG KO only, with a clear docstring explaining why KEGG pathway number matching was removed. The audit trail from the original 78% B12 completeness (with bch* contamination) to the corrected 83% is well-documented.

**Minor code concerns:**
1. Cell `b4` still uses `KEGG_Pathway LIKE '%00860%'` etc. in the initial SQL query, even though cell `b5`'s Python classifier ignores pathway-number matches. This means the SQL query pulls in extra rows (e.g., bch*, bfr) that are then filtered out in Python. The query could be tightened to match only by gene name and KEGG KO, but the current approach is functionally correct — it's just slightly over-fetching.
2. The `classify_bvit_pathway` function uses `row.get()` which suggests it expects a dict, but it receives a pandas Series row from `.apply()`. This works because pandas Series supports `.get()`, but it's an unusual pattern.
3. Cell `b10` output shows some unexpected gene names in the core lists (e.g., `'-'`, `'amiD'`, `'MA20_09775'`, `'nirA'`). These appear to be genes that matched via KEGG KO rather than gene name, which is correct behavior but could confuse readers. A note explaining these non-canonical gene names would help.

**Pitfall awareness:**
- ✅ Correct annotation join key (`query_name` → `gene_cluster_id`)
- ✅ Filtering in Spark before `.toPandas()` (cell `b4` does the heavy join/filter in SQL)
- ✅ Both *Methylobacterium* and *Methylorubrum* taxonomy included
- ✅ No cross-species gene cluster comparison (correctly uses functional annotations for cross-species MDH)
- ⚠️ No explicit numeric type casting, though boolean columns (`is_core`, `is_auxiliary`, `is_singleton`) come through as Python booleans in the output, so this appears to work correctly here

## Findings Assessment

**Conclusions are well-supported by the data shown.** The key findings are:
1. **eggNOG misannotation**: 4 of 5 "mxaF" clusters in *M. extorquens* carry xoxF markers (EC 1.1.2.8 / K00114) — directly visible in cell `b7` output. The cross-species reclassification (44/5/0 → 0/39/10) is computed transparently in cell `b8a`.
2. **Riboflavin auxotrophy** (67%, missing ribA/ribC) and **thiamine auxotrophy** (75%, missing thiM/thiO) — supported by cell `b5` output. The observation that all found riboflavin genes are core strengthens the auxotrophy prediction.
3. **B12 core/accessory variability** — clearly shown in cell `b10` output, where 15 cob genes appear simultaneously in core, auxiliary, and singleton categories.
4. **MDH profile does not predict B vitamin capacity** — the near-identical means (54.5 vs 54.3) with overlapping standard deviations support this null finding.

**Limitations are clearly acknowledged** in both README and REPORT: annotation sensitivity gaps, heuristic 80% threshold, non-exhaustive gene lists, and dependence on EC/KEGG quality.

**Testable predictions are specific and actionable**, connecting pangenome findings to wet-lab experiments.

**Literature context is strong.** The README cites 11 references spanning lanthanide biology (Pol 2014, Keltjens 2014, Masuda 2016), annotation quality (Schnoes 2009), B vitamin auxotrophy (Ryback 2022, Morris 2012), and Methylobacterium taxonomy (Green & Ardley 2018, Hesse 2022). The separate `references.md` file provides annotated citations with relevance notes.

**Incomplete or missing elements:**
- No figure for the MDH reclassification result (the gene-name-based vs EC/KEGG-based comparison). This is arguably the most striking finding and deserves its own visualization (e.g., a grouped bar chart or alluvial diagram showing the inversion).
- No figure for the B12 core/accessory variability. A heatmap of cob gene × status (core/auxiliary/singleton) would make this finding more accessible.
- The right panel of `bvitamin_completeness.png` (MDH profile vs B vitamin genes) shows a null result — useful to include but could be more informative with individual species data points overlaid on the bars.

## Suggestions

1. **[High] Save intermediate data files.** Export `bvit_pd`, `mdh_species_pd`, and `bvit_pivot` as CSV/TSV to `data/`. This enables local reproduction of figures and downstream analysis without Spark access. Add a cell that checks for cached files and loads them if present, skipping Spark queries.

2. **[High] Add a RESEARCH_PLAN.md.** Even retroactively, documenting the hypothesis, approach, and expected outputs in a separate plan file aligns with the observatory's three-file structure and helps future readers understand the project's evolution.

3. **[Medium] Add a figure for the MDH reclassification.** A side-by-side or stacked bar chart showing the gene-name-based (44/5/0) vs EC/KEGG-based (0/39/10) profiles would make the key finding immediately visual. This is the most novel result and currently exists only as text output.

4. **[Medium] Add a figure for B12 core/accessory variability.** A heatmap or dot plot showing each cob gene's status across strains (core in X strains, auxiliary in Y, singleton in Z) would strengthen the strain-specific B12 requirements claim.

5. **[Medium] Tighten the initial SQL query in cell `b4`.** Remove the `KEGG_Pathway LIKE` clauses that are overridden by the Python classifier anyway. This would eliminate the 360→(fewer) row reduction step and make the query intent match the classifier logic.

6. **[Low] Expand the Reproduction section.** Add: (a) expected total runtime (~15 min as noted in the notebook table), (b) which Spark session name is used ("MextorquensBvitamin"), (c) how to verify success (check for the figure file and expected row counts), (d) note that no local-only reproduction path exists without Spark.

7. **[Low] Add a `requirements.txt` note about Spark.** The current file comments out `pyspark>=3.4.0` as "pre-installed on BERDL JupyterHub" — consider adding a note that `berdl_notebook_utils` is also required and only available on JupyterHub.

8. **[Low] Annotate non-canonical gene names in cell `b10` output.** Genes like `'-'`, `'amiD'`, `'MA20_09775'`, and `'nirA'` appearing in B vitamin pathway results are likely KO-matched rather than name-matched. A brief markdown cell explaining this would prevent reader confusion.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, REPORT.md, references.md, requirements.txt, 1 notebook (01_mextorquens_bvitamin_case.ipynb with 22 cells), 0 data files, 1 figure
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
