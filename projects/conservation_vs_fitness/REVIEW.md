---
reviewer: BERIL Automated Review
date: 2026-02-14
project: conservation_vs_fitness
---

# Review: Conservation vs Fitness — Linking FB Genes to Pangenome Clusters

## Summary

This is a well-executed cross-database analysis that bridges the Fitness Browser (RB-TnSeq essentiality data for 48 bacteria) with the KBase pangenome (gene cluster conservation across species). The project successfully maps 44 of 48 FB organisms to pangenome clades, builds a 177,863-row gene-to-cluster link table at high identity (100% median), and demonstrates that essential genes are modestly but significantly enriched in core genome clusters (median OR=1.56, 19/33 organisms significant). The functional analysis revealing that essential-core genes are enzyme-rich (41.9%) while essential-auxiliary genes are poorly characterized (38.2% hypothetical) adds biological depth. The README is thorough with excellent documentation of methods, limitations, and literature context. Key areas for improvement include a missing `requirements.txt`, a data anomaly with Dyella79, and the conservation breakdown percentages in the README summing to more than 100%.

## Methodology

**Research question**: Clearly stated and testable — whether essential genes are preferentially conserved in core pangenome clusters. The two-phase approach (link table construction, then conservation analysis) is logical and well-motivated.

**Organism matching**: The three-strategy approach (NCBI taxid, organism name, scaffold accession) is thorough and handles the GTDB taxonomic renaming problem well. Multi-clade resolution by DIAMOND hit count is a reasonable heuristic. The `src/run_pipeline.py` script properly escapes single quotes in organism names (line 168-169), showing attention to SQL injection-like issues.

**Essential gene definition**: The definition (type=1 CDS absent from `genefitness`) is clearly documented as an upper bound on true essentiality. The gene length validation (NB04 Section 1) appropriately addresses the concern that short genes may lack transposon insertions. The Mann-Whitney U test confirms essential genes are slightly shorter on average, and this caveat is honestly acknowledged in the Limitations section.

**Statistical testing**: Fisher's exact test per organism with odds ratios is appropriate for the 2×2 contingency tables. However, no multiple testing correction (e.g., Bonferroni or FDR) is applied across the 33 organisms, though with 19/33 significant at p<0.05 and many having very small p-values (e.g., 2e-18), this would likely not change the conclusions materially.

**Data sources**: Clearly identified in a table in the README. The `extract_essential_genes.py` script correctly uses the documented KEGG join path (`besthitkegg` → `keggmember` → `kgroupdesc`), consistent with the pitfalls documented in `docs/pitfalls.md`.

## Code Quality

**SQL queries**: Queries are well-constructed. The Fitness Browser queries correctly use `type = '1'` (string comparison, consistent with the pitfall that all FB columns are strings). The `CAST` operations on taxid columns in NB01 are appropriate. The KEGG join path in `extract_essential_genes.py` (lines 120-128) correctly follows the documented pattern from `docs/pitfalls.md`.

**Notebook organization**: All four notebooks follow a clear structure (setup → data loading → analysis → QC → summary). Each notebook begins with a markdown header explaining purpose, inputs, outputs, and whether Spark is required. The separation of Spark-dependent steps (NB01, NB02, `src/run_pipeline.py`, `src/extract_essential_genes.py`) from local analysis (NB03, NB04) is well-designed.

**Notebook outputs**: NB03 and NB04 have saved outputs (text tables, figures), making them reviewable without re-execution. NB01 and NB02 do not have saved outputs, which is acceptable since they require Spark Connect and their results are cached as TSV files. The key analytical notebooks (NB03, NB04) are the ones that matter most for reproducibility of results, and they deliver.

**Shell script**: `run_diamond.sh` is well-written with `set -euo pipefail`, proper argument validation, temp directory cleanup via `trap`, and caching of completed searches. DIAMOND parameters (90% identity, best hit only) are appropriate for same-species protein searches.

**Pitfall awareness**: The project correctly handles several documented pitfalls:
- Uses `type = '1'` (string) for FB gene filtering
- Uses the correct KEGG join path through `besthitkegg`
- Uses `seedannotation` (not `seedclass`) for functional descriptions
- Filters by `orgId` when querying the 27M-row `genefitness` table
- Uses exact equality for `gtdb_species_clade_id` rather than LIKE patterns

**Data anomaly — Dyella79**: In the NB04 per-organism category breakdown, Dyella79 shows 0 essential_mapped and 706 essential_unmapped genes, with 0 nonessential_mapped as well. This means that despite Dyella79 having 4,281 DIAMOND hits in NB03 (97.9% coverage), none of these links are joining to the essential gene data in NB04. This appears to be a join key mismatch — likely Dyella79 was included in the NB03 link table but its locusId format differs between the FB gene table and the link table, or it was excluded from the `extract_essential_genes.py` high-coverage threshold and then re-included with a different set. The organism does appear in the NB04 output (34 organisms), so the data was extracted, but the merge with the link table produced zero matches. This is a silent data quality issue that inflates the essential_unmapped count and should be investigated.

**README conservation percentages**: The README states "145,821 core (82.0%), 32,042 auxiliary (18.0%), 7,574 singleton (4.3%)" — these sum to 104.3%, because singletons are a subset of auxiliary (as documented in `docs/pitfalls.md`). The NB03 summary correctly reports "145,821 core, 32,042 auxiliary, 7,574 singleton" without claiming independence. The README should clarify that singletons are a subset of auxiliary, or report auxiliary-non-singleton and singleton separately.

## Findings Assessment

**Core result**: The finding that essential genes are enriched in core clusters (OR=1.56) is well-supported by the per-organism Fisher's exact tests. The forest plot and the detailed per-organism table make the result transparent. The honest acknowledgment that the enrichment is "modest" and that "most genes in well-characterized bacteria are core regardless of essentiality" shows scientific maturity.

**Functional analysis**: The four-way breakdown (essential-core, essential-auxiliary, essential-unmapped, nonessential) with enzyme classification and SEED category analysis is thorough. The finding that essential-core genes are 41.9% enzymes while essential-auxiliary genes are only 13.4% enzymes is striking and well-presented.

**Limitations**: Comprehensively acknowledged — the essential gene definition as upper bound, pangenome coverage variation with small clades, E. coli exclusion, single growth condition, and organism exclusions. The gene length validation directly addresses one of the most important potential confounds.

**Literature context**: Five relevant references are cited, and the connections to Rosconi et al. (2022) and Hutchison et al. (2016) are particularly apt. The parallel between their categories and the project's conservation categories is well-drawn.

**Stratification analyses**: The pangenome context analysis (clade size, openness) and lifestyle stratification add nuance. The Spearman correlation between clade size and odds ratio is a good way to check whether the result is driven by pangenome structure rather than biology.

**Incomplete elements**: The `Dino` organism shows OR=NaN in the results (100% core for both essential and non-essential), and `Ponti` shows OR=inf (100% core for essential, 99.7% for non-essential). These edge cases are included in the median OR calculation — the NaN for Dino would be excluded from the median, but the inf for Ponti should be handled more carefully if used in any aggregation.

## Suggestions

1. **[Critical] Investigate the Dyella79 join failure**: In NB04, Dyella79 has 706 essential genes but 0 map to pangenome clusters, despite having 97.9% DIAMOND coverage in NB03. This suggests a data pipeline issue between the link table and essential gene extraction. Verify that locusId formats match between `essential_genes.tsv` and `fb_pangenome_link.tsv` for this organism. If Dyella79 data is unreliable, consider excluding it from the 34-organism analysis or documenting the issue.

2. **[Important] Add `requirements.txt`**: No dependency file exists. The project uses pandas, numpy, matplotlib, scipy, and (for Spark steps) pyspark. Adding a `requirements.txt` would improve reproducibility. DIAMOND is an external tool dependency that should also be noted with version requirements.

3. **[Important] Clarify conservation percentages in README**: The Results section reports core (82.0%), auxiliary (18.0%), and singleton (4.3%) which sum to >100%. Per `docs/pitfalls.md`, singletons are a subset of auxiliary. Reword to: "145,821 core (82.0%), 24,468 auxiliary-non-singleton (13.8%), 7,574 singleton (4.3%)" or add a note that singletons ⊂ auxiliary.

4. **[Minor] Handle OR edge cases**: Ponti (OR=inf) and Dino (OR=NaN) in the Fisher's exact test results. Consider adding a note or filtering these from aggregate statistics. The median OR of 1.56 across 33 organisms may be affected by the inf value depending on the pandas median implementation.

5. **[Minor] Add multiple testing correction**: While 19/33 organisms are significant at p<0.05 and many have very small p-values, applying Benjamini-Hochberg FDR correction would strengthen the statistical rigor and is standard practice when testing across multiple organisms.

6. **[Minor] `seed_hierarchy.tsv` provenance**: The SEED hierarchy file is used in NB04 Section 8 but its extraction is not shown in `extract_essential_genes.py` or any notebook. Document how this file was generated (likely from `seedannotationtoroles` + `seedroles` tables) for full reproducibility.

7. **[Nice-to-have] Consider DIAMOND query coverage filter**: The DIAMOND search uses `--id 90` but no explicit query coverage filter (`--query-cover`). The README mentions "94.2% median gene coverage" suggesting coverage is generally high, but adding `--query-cover 70` to `run_diamond.sh` would guard against partial matches inflating the link count.

8. **[Nice-to-have] Add NB01/NB02 notebook outputs**: While these notebooks require Spark and their outputs are cached as TSV files, saving the notebook outputs (via `jupyter nbconvert --execute`) would let reviewers see the exact matching statistics, warnings, and QC results without re-running on the cluster.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-14
- **Scope**: README.md, 4 notebooks, 3 src scripts, 10 data files, 8 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
