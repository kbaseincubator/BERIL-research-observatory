# Plan Review: Gene Function Ecological Agora

**Overall**: Ambitious but well-structured three-phase atlas with sound methodological design, though several critical performance and data quality issues need addressing before Phase 1 execution.

## Critical (likely to cause failures or wasted effort):

1. **Phase 3 Pfam completeness audit is mandatory, not optional** — per docs/pitfalls.md [bakta_reannotation], 12/22 marker Pfams were silently missing from `bakta_pfam_domains` in a prior project. This audit must run before any Phase 3 analysis, not during. Consider running a spot-check on key architectures (TCS, PSII) during Phase 2 planning to avoid nasty surprises.

2. **Species ID `--` handling needs clarification** — The plan mentions using exact equality or LIKE with prefix for species IDs containing `--`, but doesn't specify which approach each phase will use. Direct Spark SQL handles `--` correctly in quoted strings, but this should be explicit in the query strategy to avoid confusion.

3. **Large table scan protection missing** — Several queries will hit billion-row tables (`gene_genecluster_junction`, `bakta_db_xrefs`). The plan mentions filters but doesn't specify the per-phase filter strategies. Phase 1's "one genome per species" should use IN clauses on representative genome IDs, not species-level scans.

## Recommended (would improve the plan):

1. **Query performance specifics needed** — The plan references docs/performance.md patterns but doesn't commit to which pattern each phase uses. Phase 1 should use Pattern 2 (per-species iteration) given the scale. Phase 2/3 should use Pattern 1 (IN clauses) for moderate KO/architecture subsets.

2. **Spark session environment inconsistency** — The plan states "on-cluster" but shows import pattern for off-cluster (`from berdl_notebook_utils.setup_spark_session import get_spark_session`). On-cluster should use `spark = get_spark_session()` with no import per docs/pitfalls.md.

3. **Phase gate criteria could be more quantitative** — "≥30% of UniRef50s show non-trivial quadrant structure" needs a definition of "non-trivial" (e.g., effect size threshold, confidence interval width). The current gate criteria mix statistical significance with biological interpretation.

## Optional (nice-to-have):

1. **Cross-resolution projection validation** — The Phase 1→2 handoff relies on UniRef50→KO projection concordance ≥75%, but doesn't specify how to handle systematic biases (e.g., if EggNOG systematically under-annotates certain functional classes). A bias audit could strengthen the handoff.

2. **Consider computational cost estimates** — 16 agent-weeks is substantial. Phase 1 alone processes ~133M clusters across 28K species. Runtime estimates for key bottlenecks (null model construction, per-clade scoring) would help resource planning.

3. **Alternative stop-point for methodological failure** — If Phase 2 Alm 2006 back-test fails, the plan halts for "methodological diagnosis." Consider specifying 2-3 most likely failure modes and diagnostic paths to avoid analysis paralysis.

## Relevant pitfalls from docs/pitfalls.md:

- **String-Typed Numeric Columns**: `kescience_fitnessbrowser` fitness scores are strings — any fitness browser integration needs `CAST(fit AS DOUBLE)` before comparisons
- **Large Species Blow Up ANI Queries**: Species with >500 genomes (*K. pneumoniae* ~14K, *S. aureus* ~14K) will timeout on ANI queries. The plan should cap at ≤500 genomes for any within-species analysis
- **Disable autoBroadcast on UniProt joins**: When joining `bakta_db_xrefs` to `kbase_uniprot`, disable autoBroadcast to avoid maxResultSize errors per pitfall documentation

## Project Structure Assessment:

The plan follows expected BERIL conventions well: proper notebook numbering (01-19), phase-gated design with publishable stop-points, clear data handoffs between phases. The three-resolution approach with forced ordering is methodologically sound and addresses the EggNOG annotation density confound elegantly. The weak-prior calibration for pre-registered hypotheses is appropriately conservative.

---

*Plan reviewed by Claude (claude-sonnet-4-20250514)*
