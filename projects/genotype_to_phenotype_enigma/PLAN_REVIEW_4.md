# Research Plan Review: Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

**Overall**: Comprehensive, well-structured plan with clear hypotheses, appropriate data sources, and sound methodology. Minor data source verification and a few methodological clarifications needed.

## Critical (likely to cause failures or wasted effort):

1. **Verify ENIGMA Genome Depot access and table names**: The plan references `enigma_genome_depot_enigma.browser_*` tables extensively (browser_genome, browser_protein, browser_protein_kegg_orthologs, etc.). However, this database is not listed in `docs/collections.md` and has no schema documentation. Confirm the database exists in BERDL and table names match before proceeding with Act II. If this is a newly added database, update the collections documentation.

2. **Validate Carbon Source Phenotype database access**: The plan relies heavily on `globalusers_carbon_source_phenotypes` for pretraining (795 genomes), but this database isn't documented in collections.md. Verify access and confirm it's not a development/staging database that might be unstable.

3. **Test condition alignment strategy early (NB02)**: The plan acknowledges condition alignment as "the gating factor for the project" with a 4-level fallback strategy (Plans A-D). Given that cross-dataset alignment is essential for H2-H6, execute NB02 early and validate alignment coverage before investing heavily in modeling notebooks.

## Recommended (would improve the plan):

1. **Clarify FB concordance validation sample size**: The plan states 7 FB anchor strains but acknowledges "Small n for per-strain leave-one-out." Consider how to interpret FB concordance results with this constraint, and whether the CSP pretraining adequately addresses the power limitation.

2. **Document Spark session pattern consistency**: The plan mentions execution environments but should explicitly state the correct `get_spark_session()` import pattern. Based on the memory context (on-cluster JupyterHub), this should be `spark = get_spark_session()` with no import for notebooks, but `from berdl_notebook_utils.setup_spark_session import get_spark_session` for CLI scripts.

3. **Add data extraction checkpoint verification**: With 303 brick tables to read (NB01), include row count validation and QC checks to catch incomplete extractions early. The plan mentions 27,632 total curves - verify this count matches expectations.

4. **Specify model hyperparameter rationale**: The plan provides specific LightGBM hyperparameters but should briefly justify the choices (e.g., why `num_leaves=31, min_data_in_leaf=10` for a 486-pair dataset) or reference validation that informed these settings.

## Optional (nice-to-have):

1. **Consider computational resource estimates**: Act II involves nested GBDT with 4,305 features on 486 samples with 7-fold CV. Estimate runtime and memory requirements to avoid hitting JupyterHub limits.

2. **Plan for model interpretation limitations**: The plan emphasizes interpretability via SHAP on KO features, but with 4,305 KOs, interpretation may still be challenging. Consider strategies for summarizing SHAP results at pathway/module level.

3. **Document active learning validation approach**: NB11 proposes ranking experiments by model disagreement × novelty × FB concordance. Specify the retrospective validation approach to avoid circular reasoning (e.g., holding out recent experiments vs. subsampling existing data).

## Relevant pitfalls from docs/pitfalls.md:

- **Short Strain Names Collide Across Databases**: When linking ENIGMA strains to pangenome via strain names, always cross-check genus consistency between `enigma_genome_depot_enigma.browser_taxon` and GTDB taxonomy. Reject linkages where genera disagree to avoid spurious matches.
- **String-Typed Numeric Columns**: All Fitness Browser columns (fit, t) are stored as strings. Always `CAST(fit AS FLOAT)` before numeric comparisons in FB queries.
- **PySpark Cannot Infer numpy str_ Types**: When using `np.random.choice()` for sampling, cast results to native Python strings before creating Spark DataFrames: `[str(g) for g in sampled_genomes]`.
- **Spark DECIMAL Columns Return decimal.Decimal in Pandas**: Use `CAST(AVG(...) AS DOUBLE)` for aggregated columns to avoid type errors when converting to pandas.

## Duplication check:

- **fw300_metabolic_consistency**: Directly related - analyzed FW300-N2E3 (one of your 7 anchor strains) for consistency across WoM, FB, BacDive, and GapMind. Your project should reference and build on this work rather than repeating the FW300-N2E3 analysis.
- **conservation_vs_fitness**: Provides the FB ↔ pangenome linking infrastructure (`fb_pangenome_link.tsv`) that your FB concordance validation requires. Leverage this existing work.
- **fitness_modules**: Demonstrates fitness-based functional module discovery using ICA across 32 organisms. Consider how your GBDT SHAP features relate to their ICA modules for validation.
- **enigma_contamination_functional_potential**: Uses ENIGMA CORAL taxonomy data and pangenome linkages. May provide useful taxonomy bridging tables and ENIGMA data extraction patterns.

---

Plan reviewed by Claude (claude-sonnet-4-20250514).
