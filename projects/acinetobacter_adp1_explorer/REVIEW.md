---
reviewer: BERIL Automated Review
date: 2026-02-18
project: acinetobacter_adp1_explorer
---

# Review: Acinetobacter baylyi ADP1 Data Explorer

## Summary

This is a well-executed exploratory project that systematically characterizes a 136 MB user-provided SQLite database for *Acinetobacter baylyi* ADP1 and validates its integration points with four BERDL collections. The project excels in documentation quality, visual richness (18 figures across 5 notebooks), and methodological transparency — the cluster ID mapping problem (0% direct string match → 100% gene-level bridge) is particularly well handled. The three-file structure (README, RESEARCH_PLAN, REPORT) follows observatory conventions, all notebooks have saved outputs, and the REPORT presents 8 clearly numbered findings with supporting figures. The main areas for improvement are minor: the reproduction instructions cover only one notebook, the PhageFoundry scan cell produced no output, and there are a few opportunities for deeper statistical analysis.

## Methodology

**Research question**: Clearly stated as a two-part exploration: (1) characterize the database, (2) identify BERDL connection points. The framing as an exploration project rather than a hypothesis-driven study is appropriate and honestly acknowledged in the RESEARCH_PLAN.

**Approach**: The phased approach (inventory → connection scan → integration deep-dives) is logical and well-matched to the question. The research plan's connection mapping table (RESEARCH_PLAN.md lines 20-29) lays out 8 identifier types with specific BERDL targets and link strategies, providing a clear checklist.

**Data sources**: Well documented in both README and REPORT. The README identifies 6 data sources (user-provided + 5 BERDL collections), and the REPORT's Data section includes a table showing which tables were used from each collection and their purpose. The identification of ADP1's absence from the Fitness Browser (NB02 cell 12) is a useful negative result.

**Reproducibility**:
- **Notebook outputs**: Excellent — 58 of 59 code cells across all 5 notebooks have saved outputs. The one exception is cell 15 in NB02 (PhageFoundry ADP1/baylyi search), which produced no output — likely because the search found no matches, but this should be documented with a print statement.
- **Figures**: Outstanding — 18 figures in the `figures/` directory, covering every major analysis stage (database inventory, BERDL connections, cluster mapping, essentiality, fitness, proteomics, metabolic model, gapfilling, growth predictions, annotations, ontology). Each figure is referenced in the REPORT with a description.
- **Dependencies**: `requirements.txt` is present with 3 packages (pandas, matplotlib, seaborn). However, it omits the `berdl_notebook_utils` dependency used in NB02 and NB03 for Spark access.
- **Reproduction guide**: The README has a `## Reproduction` section with prerequisites and a run command, but it only shows how to execute NB01 (`01_database_exploration.ipynb`). The guide should cover all 5 notebooks and note that NB02 and NB03 require Spark access via the BERDL JupyterHub environment.
- **Spark/local separation**: Partially documented. NB02 and NB03 use Spark; NB01, NB04, and NB05 use only SQLite and can run locally. This distinction is not explicitly called out in the README. The cached outputs (`data/cluster_id_mapping.csv`, `data/berdl_connection_summary.csv`) enable downstream work without Spark re-execution.

## Code Quality

**SQL correctness**: SQLite queries throughout NB01 are straightforward and correct. The BERDL Spark queries in NB02 use proper `IN` clause batching (batch_size=100 for reactions, batch_size=200 for cluster junctions), avoiding performance issues with overly large IN lists. The `seed.reaction:` prefix handling for biochemistry lookups (NB02 cell 6) is correct.

**Statistical methods**: Appropriate for an exploratory project. Pearson correlation for cross-strain proteomics and carbon source fitness, cross-tabulation for essentiality concordance, and simple descriptive statistics throughout. The concordance analysis (NB04 cell 5) correctly computes agreement rate. The FBA essentiality definition (`rich_media_class == 'essential'`) is reasonable but could be documented more explicitly — the mapping between FBA flux classes and essentiality is a modeling choice.

**Notebook organization**: Each notebook follows a clean structure: markdown header with goals → imports/setup → numbered analysis sections → summary. NB04 is the most complex (8 sections, 10 code cells) and handles it well with clear section headers.

**Pitfall awareness**:
- The project correctly handles the pangenome cluster ID naming convention difference (a known pitfall pattern from docs/pitfalls.md regarding different ID formats between systems).
- The `gene_genecluster_junction` queries use appropriate batching (pitfall: this is a large table).
- The project does not encounter the `--` in species IDs pitfall because it uses exact equality with proper quoting in NB02 cell 4.
- No issues with string-typed numeric columns (the SQLite database appears to use proper types).

**Minor code issues**:
1. In NB04 cell 5, the FBA concordance defines "essential" as `rich_media_class == 'essential'` but the actual flux class values include `essential_forward` and `essential_reverse` (visible in NB01 cell 19). The concordance calculation may undercount FBA-essential genes if the check doesn't match these class names — worth verifying.
2. In NB04 cell 9, the correlation mask is `np.triu(..., k=1)` (upper triangle), but the `upper = corr.where(~mask).stack()` extracts the lower triangle. This is mathematically correct (lower triangle = upper triangle values by symmetry) but the variable name `upper` is misleading.

## Findings Assessment

**Conclusions supported by data**: All 8 key findings in the REPORT are directly supported by notebook outputs. The connection scan results (100% genome, 91% reaction, 100% compound, 100% cluster mapping) are verifiable in NB02 and NB03. The FBA-TnSeq concordance of 73.8% is computed and shown in NB04. The gapfilling dependency (87%) is computed in NB05.

**Limitations acknowledged**: Yes — the REPORT's Limitations section (lines 139-143) identifies four specific limitations: sparse data overlap, indirect cluster mapping, gapfilling dependence, and single-species scope. These are honest and relevant.

**Incomplete analysis**:
- The PhageFoundry connection (NB02 cells 14-15) was identified but not explored. Cell 14 lists 37 tables and shows 15 table names, but cell 15 (ADP1/baylyi search) produced no output. The REPORT acknowledges this as a future direction.
- The UniRef connections (3,100+ IDs identified in NB01) were not validated against BERDL in NB02, despite being listed as a connection point. This is a gap — the project reports 4 of 5 connection types validated, but UniRef, COG, KEGG KO, EC, and Pfam connections were identified but not tested.
- The `growth_phenotype_summary` table shows all genomes with 0.0 accuracy and zero true/false positives/negatives (NB01 cell 24), which suggests the observed growth data may be missing for most genomes. This is not discussed.

**Visualizations**: Clear and properly labeled throughout. Figures use consistent color palettes (red for essential, green for dispensable, blue for core), include titles, axis labels, and annotations (counts on bars, correlation values). The proteomics scatter plot (NB04 cell 12) and growth correlation heatmap (NB04 cell 9) are particularly effective.

## Suggestions

1. **Expand reproduction instructions** (medium priority): Update the README's Reproduction section to list all 5 notebooks with their execution order, note which require Spark (NB02, NB03) vs local-only (NB01, NB04, NB05), and include expected runtimes. Currently only NB01 is shown.

2. **Add a print statement to the empty PhageFoundry cell** (low priority): NB02 cell 15 produces no output. Add a summary line like `print(f'Searched {len(pf_tables)} tables, found N matches')` so readers can confirm the search completed.

3. **Validate UniRef connections** (medium priority): The project identifies 3,100+ UniRef IDs as connection points (NB01 cell 31) but never tests them against BERDL in NB02. Even a sample check of 100 UniRef50 IDs against `kbase_uniref50` would strengthen the connection inventory.

4. **Investigate the zero-accuracy growth phenotype summary** (medium priority): NB01 cell 24 shows all genomes with 0.0 accuracy and zero confusion matrix values in `growth_phenotype_summary`. This likely means observed growth data was not available for accuracy calculation, but it's worth noting in the REPORT since the growth phenotype analysis in NB05 presents prediction classes without discussing validation.

5. **Clarify FBA essentiality definition** (low priority): In NB04 cell 5, verify that `rich_media_class == 'essential'` is the correct filter — the flux class values shown in NB01 cell 19 are `essential_forward` and `essential_reverse`, not bare `essential`. If the filter is checking for a different column value than what appears in the data, the concordance numbers may need correction.

6. **Add `berdl_notebook_utils` to requirements.txt or note the Spark dependency** (low priority): NB02 and NB03 import from `berdl_notebook_utils.setup_spark_session`, which is only available on the BERDL JupyterHub. The `requirements.txt` should either include this or note that NB02/NB03 require the BERDL environment.

7. **Consider adding a combined data coverage UpSet plot** (nice-to-have): NB04 cell 18 shows that no gene has data across all 6 modalities. An UpSet plot showing the intersection sizes across modalities would more clearly convey the pairwise and higher-order overlaps mentioned in Finding 1.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-18
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks (59 code cells, 58 with outputs), 2 data files, 18 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
