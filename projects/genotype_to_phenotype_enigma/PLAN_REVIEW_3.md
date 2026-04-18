# Research Plan Review: Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

**Overall**: This is a well-structured research plan with clear hypotheses, extensive literature context, and detailed methodology that leverages a unique convergence of five datasets for the same organisms.

## Critical (likely to cause failures or wasted effort):

1. **Verify ENIGMA Genome Depot table existence**: The plan extensively references `enigma_genome_depot_enigma` tables (browser_genome, browser_strain, browser_gene, etc.) but this database is not documented in `docs/schemas/`. You should verify these tables exist and match the described schema before proceeding with NB05 feature engineering.

2. **Check Spark session initialization pattern**: The plan states "on-cluster (BERDL JupyterHub)" execution but shows inconsistent import patterns. For BERDL JupyterHub notebooks, use `spark = get_spark_session()` with no import (injected by kernel). For CLI scripts on-cluster, use `from berdl_notebook_utils.setup_spark_session import get_spark_session`. The plan should clarify which pattern each notebook uses.

## Recommended (would improve the plan):

1. **Cross-reference with existing FW300-N2E3 work**: The `fw300_metabolic_consistency` project has already characterized FW300-N2E3 (one of your 7 anchor strains) across Web of Microbes, Fitness Browser, BacDive, and GapMind. Consider building on their metabolite crosswalk table (`data/metabolite_crosswalk.tsv`) rather than redoing condition alignment from scratch.

2. **Clarify condition alignment status**: The plan states NB02 is complete but then describes it as a major gating factor with fallback Plans A-D. If already complete, skip to the results and validation. If not, prioritize Plan A verification (exact ENIGMA condition ID → FB matching) since this would be gold-standard.

3. **Add specific performance strategies**: For billion-row table joins (gene_genecluster_junction in NB06), consider BROADCAST hints for filter tables and cache intermediate results as noted in `docs/performance.md`. Budget ~5 min per organism for matrix extraction based on `cofitness_coinheritance` experience.

## Optional (nice-to-have):

1. **Consider transfer learning evaluation approach**: For H4 (CSP pretraining), consider phylogenetically-blocked validation as mentioned in Xu et al. 2025 to control for phylogenetic signal when evaluating transfer benefits.

2. **Plan for strain name collision**: For linking ENIGMA strains to pangenome via `gtdb_metadata.ncbi_strain_identifiers`, always verify genus consistency between `enigma_genome_depot_enigma.browser_taxon` and GTDB taxonomy to avoid the strain name collision issue documented in pitfalls.md.

## Relevant pitfalls from docs/pitfalls.md:

- **String-typed numeric columns in Fitness Browser**: All `genefitness` columns are strings. Always `CAST(fit AS FLOAT)` and `CAST(t AS FLOAT)` before numeric operations in NB06 FB concordance calculations.

- **Large table performance considerations**: Tables `gene` (1B rows) and `gene_genecluster_junction` (1B rows) require filters. For NB05 feature engineering, always filter by `genome_id` lists rather than full scans.

- **Short Strain Names Collide Across Databases**: When linking ENIGMA strains to `kbase_ke_pangenome.gtdb_metadata`, verify genus consistency. 12 of 32 previous linkages were incorrect genus matches due to non-unique strain names.

- **Spark DECIMAL columns return decimal.Decimal**: When aggregating with `AVG()` in Spark (e.g., pathway completeness scores), wrap in `CAST(... AS DOUBLE)` to avoid type errors in pandas after `.toPandas()`.

- **ENIGMA Genome Depot Has No Functional Annotations**: The plan assumes `enigma_genome_depot_enigma.browser_protein` has KO annotations but doesn't verify the schema. Check column names before building feature matrices in NB05.

---

Plan reviewed by Claude (claude-sonnet-4-20250514).
