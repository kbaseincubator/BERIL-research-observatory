# Research Plan Review: Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

**Overall**: Ambitious and well-structured plan with solid scientific rationale. A few critical database access issues and several optimization opportunities that would strengthen the execution.

## Critical (likely to cause failures or wasted effort):

1. **Update collections documentation for key databases**: The plan relies heavily on `enigma_genome_depot_enigma` and `globalusers_carbon_source_phenotypes`, but neither database is documented in `docs/collections.md`. While evidence shows these databases exist and are being used successfully (per REPORT.md), the missing documentation creates a barrier for future users and reviews. Add schema documentation to `docs/schemas/` for both databases.

2. **Validate Spark session patterns match execution environment**: The plan states "on-cluster (BERDL JupyterHub)" but should explicitly clarify the correct import pattern for consistency. Based on the environment, notebooks should use `spark = get_spark_session()` with no import (injected into kernel), while CLI scripts need `from berdl_notebook_utils.setup_spark_session import get_spark_session`.

3. **Plan for large table query timeouts**: The plan involves reading 303 brick tables (`ddt_brick0000928`-`ddt_brick0001230`) and joining large annotation tables (16.6M genes, 6.8M proteins, 29.4M ortholog groups). Without proper filtering strategies, these queries may exceed JupyterHub resource limits or timeout. Consider chunking brick reads and always filtering protein annotation tables by `genome_id` lists.

## Recommended (would improve the plan):

1. **Leverage existing FB-pangenome linkage**: The `conservation_vs_fitness` project already built the critical `fb_pangenome_link.tsv` bridge table (177K gene pairs across 30 organisms) needed for your FB concordance validation. Reference and reuse this existing work rather than rebuilding the linkage infrastructure.

2. **Address genus verification for strain linkages**: The pitfall "Short Strain Names Collide Across Databases" is directly relevant when linking ENIGMA strains to pangenome via strain names. Always cross-check genus consistency between `enigma_genome_depot_enigma.browser_taxon` and GTDB taxonomy to avoid spurious matches (e.g., ENIGMA MT20 vs clinical Streptococcus MT20).

3. **Plan for condition alignment validation**: The plan acknowledges condition alignment as "the gating factor" but should validate the ChEBI-based approach early in NB02 before investing in downstream modeling. Given the complexity of mapping 195 ENIGMA molecules → 379 CSP phenotypes → 350 FB conditions, include alignment coverage metrics and fallback strategies in the success criteria.

4. **Consider computational resource requirements**: Act II involves nested GBDT with 4,305 features across 67K training pairs (ENIGMA + CSP) with genus-level blocked holdout. This is computationally intensive. Estimate memory and runtime requirements to ensure JupyterHub can handle the full-scale modeling, particularly for NB07's revised full-corpus approach.

## Optional (nice-to-have):

1. **Build on metabolic consistency insights**: The `fw300_metabolic_consistency` project analyzed FW300-N2E3 (one of your 7 anchor strains) and found tryptophan overflow metabolism as a key biological discordance across WoM/FB/BacDive/GapMind. Reference this finding when interpreting FB concordance results for FW300-N2E3 to avoid rediscovering known biology.

2. **Plan SHAP interpretation at pathway level**: With 4,305 KO features, raw SHAP importance may be difficult to interpret. Consider aggregating SHAP values at KEGG pathway or module level for more actionable biological insights, similar to the pathway-level analysis in `metabolic_capability_dependency`.

3. **Document model hyperparameter selection**: The plan specifies detailed LightGBM hyperparameters (e.g., `num_leaves=31, min_data_in_leaf=10`) but doesn't justify these choices for the 486-pair anchor dataset. Include brief rationale or reference validation that informed these settings.

## Relevant pitfalls from docs/pitfalls.md:

- **String-Typed Numeric Columns**: Fitness Browser stores `fit` and `t` as strings. Always use `CAST(fit AS FLOAT)` before numeric operations to avoid comparison failures.
- **PySpark Cannot Infer numpy str_ Types**: When using `np.random.choice()` for sampling (relevant for strain subsampling in NB06-NB07), cast results to native Python strings before creating DataFrames: `[str(g) for g in sampled_genomes]`.
- **Brick Table Iteration**: Reading 303 brick tables is acceptable via Spark but slow via REST API. Use direct Spark access as planned.
- **DECIMAL Columns in Pandas**: Spark `AVG()` returns decimal types. Use `CAST(AVG(...) AS DOUBLE)` in aggregation queries to avoid pandas type errors when calling `.toPandas()`.

## Duplication check:

- **fw300_metabolic_consistency**: Analyzed one of your anchor strains (FW300-N2E3) across the same databases (WoM, FB, BacDive, GapMind). Build on these findings rather than repeating the analysis.
- **conservation_vs_fitness**: Provides the FB ↔ pangenome gene linkage infrastructure essential for your biological meaningfulness validation.
- **fitness_modules**: Demonstrates fitness-based functional decomposition using ICA across 32 organisms. Consider how GBDT SHAP features relate to their discovered modules.
- **metabolic_capability_dependency**: Uses similar GapMind + FB approach for distinguishing metabolic capability vs dependency. Good reference for pathway-level fitness interpretation.

---

Plan reviewed by Claude (claude-sonnet-4-20250514).
