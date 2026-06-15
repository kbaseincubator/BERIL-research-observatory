# Research Plan Review

**Overall**: Well-structured plan with testable hypotheses grounded in published literature and appropriate BERDL data sources.

## Critical (likely to cause failures or wasted effort):

1. **NB01 SRA re-analysis compute requirements**: Plan delegates SRA SRP136695 to CTS with significant compute (prefetch + fasterq-dump + HISAT2 + edgeR). Verify CTS resource limits and expected runtime before proceeding — this could be a 4-8 hour job that might exceed CTS quotas. Consider whether existing processed data from Leaden 2018 is available elsewhere before re-processing from raw reads.

2. **Spark session import pattern needs specification**: Plan references "JupyterHub with outputs committed" but doesn't specify execution environment for each notebook. NB02+ will use `kescience_fitnessbrowser` requiring Spark — clarify whether execution is on-cluster (use `spark = get_spark_session()` with no import) or local with proxy (requires `from berdl_notebook_utils.setup_spark_session import get_spark_session` for CLI scripts).

## Recommended (would improve the plan):

1. **Verify Caulobacter fitness data scope**: Plan assumes 198 Caulobacter experiments span the relevant conditions (iron limitation, oxidative stress, envelope stress). Recommend NB02 start with `SELECT expGroup, COUNT(*) FROM experiment WHERE orgId='Caulo' GROUP BY expGroup` to confirm condition coverage before building the ranking framework.

2. **CtpA significance threshold**: Phase A shows CtpA +0.58 logFC "borderline" in 4599-vs-4584. Consider pre-registering the significance threshold (FDR<0.05? absolute logFC>0.5?) for H3 before NB04 to avoid post-hoc threshold adjustment.

3. **Cross-species pangenome strategy**: NB06 comparative analysis depends on "BERDL pangenome coverage" for the three non-Caulobacter species but provides no fallback. Recommend confirming `kbase_ke_pangenome.genome` coverage for *N. meningitidis*, *A. baumannii*, *M. catarrhalis* before NB06 or documenting the NCBI fallback approach.

## Optional (nice-to-have):

1. **Stop condition specificity**: Plan triggers revision if "NB02 reveals no Fur-released gene with meaningful fitness phenotype" but doesn't define "meaningful" quantitatively. Consider specifying a threshold (e.g., >10% of Fur genes in top fitness decile) to make the stop condition objective.

## Relevant pitfalls from docs/pitfalls.md:

- **Fitness Browser string columns**: `kescience_fitnessbrowser.genefitness.fit` and `.t` are stored as strings — always `CAST(fit AS DOUBLE)` before numeric operations (affects NB02 fitness ranking)
- **Fitness Browser KO mapping**: Requires two-hop join through `besthitkegg` then `keggmember` — no direct `(orgId, locusId) → KO` table (affects NB02 if KO-level analysis needed)
- **FitnessBrowser experiment.expGroup**: Column is `expGroup` not `Group` (affects NB02 condition classification)
- **PaperBLAST year column**: `kescience_paperblast.year` is string — use `CAST(year AS INT)` for chronological filtering (affects NB03/NB04 literature lookups)

---

Plan reviewed by Claude (claude-sonnet-4-20250514).
