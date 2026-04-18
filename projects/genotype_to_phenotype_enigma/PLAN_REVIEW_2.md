# BERIL Research Plan Review
## Project: genotype_to_phenotype_enigma

**Overall**: This is an ambitious and well-structured research plan with strong theoretical foundations, but several critical feasibility and performance issues need to be addressed before execution.

**Critical** (likely to cause failures or wasted effort):

1. **Spark session setup mismatch**: The plan states execution on BERDL JupyterHub but doesn't specify the correct import pattern. Use `spark = get_spark_session()` (no import needed - injected into kernel) for notebooks, or `from berdl_notebook_utils.setup_spark_session import get_spark_session` for CLI scripts on JupyterHub.

2. **Performance-critical queries lack optimization strategy**: NB05-NB07 plan to query billion-row tables (`gene`, `gene_genecluster_junction`, `genome_ani`) for 123 strains without specifying chunking or filtering strategies. This will likely timeout or exceed memory limits. Apply patterns from `docs/performance.md`: filter by `genome_id` for `gene` queries, use species-level iteration for ANI, and avoid `.toPandas()` on intermediate results.

3. **Table reference verification needed**: Several table names in the Data Sources section need verification against actual BERDL schemas. For example, the plan references `enigma_coral.ddt_brick0000928` through `ddt_brick0001230` but these specific brick numbers should be confirmed via `enigma_coral.ddt_ndarray` metadata.

4. **Condition alignment strategy is over-optimistic**: Plans A-D fallback strategy assumes ChEBI coverage will be comprehensive, but ENIGMA conditions may use non-standard compound names. Plan C (fuzzy string matching) and Plan D (condition-class pooling) should be tested early as they're more likely to be needed than Plan B (ChEBI ID match).

**Recommended** (would improve the plan):

1. **Add specific performance constraints**: Specify memory and timeout limits for large queries. For example, cap ANI queries at species with <500 genomes, use `LIMIT` for exploration queries, and implement checkpointing in compute-intensive notebooks.

2. **Strengthen biological meaningfulness validation**: FB concordance is innovative but relies on only 7 anchor strains. Consider adding validation via cross-species transfer (use phylogenetically blocked CV results to validate that FB-concordant features transfer better than FB-discordant features).

3. **Clarify feature engineering scope**: NB05 plans 4 levels of features but doesn't specify dimensionality constraints. With ~2,000 KOs × 123 strains, feature selection will be critical. Specify selection criteria (stability selection, elastic net) and target feature counts per level.

**Optional** (nice-to-have):

1. **Add runtime estimates**: Based on `docs/performance.md` examples, billion-row joins take 3-5 minutes per species. With 123 strains, matrix extraction could take hours - document expected runtimes.

2. **Consider pilot validation**: Run the variance partitioning framework (NB06) on a subset of well-characterized conditions before full deployment to validate the approach.

**Relevant pitfalls from docs/pitfalls.md**:

- **String-typed numeric columns**: Fitness Browser columns require `CAST(fit AS FLOAT)` before comparisons (affects NB08 FB concordance validation)
- **`gene_genecluster_junction` performance**: Billion-row table joins require BROADCAST hints and long timeouts (affects NB05 feature extraction)
- **REST API vs Direct Spark**: Use direct Spark SQL for complex queries and billion-row operations (affects NB02-NB05)
- **Spark DECIMAL columns**: Results from `AVG()` aggregates return `decimal.Decimal` objects - use `CAST AS DOUBLE` in queries (affects NB06 variance partitioning)
- **Phylogenetic ID format mismatch**: GTDB genome IDs use `RS_/GB_` prefixes while some annotation tables don't - strip prefixes before joins (affects NB05 feature engineering)
- **AlphaEarth coverage limitation**: Only 28.4% genome coverage - plan mentions this but should emphasize impact on environmental context analysis in NB04

---

Plan reviewed by Claude (claude-sonnet-4-20250514).
