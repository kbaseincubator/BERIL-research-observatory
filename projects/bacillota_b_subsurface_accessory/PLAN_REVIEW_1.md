# Research Plan Review: Subsurface Bacillota_B Specialization

**Overall**: This is a well-designed follow-up analysis with clear hypotheses and methodical approach, building appropriately on the `clay_confined_subsurface` project. The plan correctly identifies and addresses a genuine error in the previous project's iron-reduction markers.

## Critical (likely to cause failures or wasted effort)

1. **Cross-species orthology strategy needs clarification**: Line 129 mentions using "eggNOG OG IDs as the orthology surrogate" for cross-species accessory-genome analysis, but the table strategy (lines 90-95) describes per-cluster Fisher tests on `gene_cluster_id`. Gene clusters are species-specific per the schema docs, so comparing clusters across deep-clay vs soil Bacillota_B genomes from different species would be invalid. **Clarify whether NB03 will use `eggnog_mapper_annotations.eggNOG_OGs` as the unit of analysis or restrict to single-species comparisons.**

2. **PFAM domain availability verification required**: The plan correctly flags (line 73) that `bakta_pfam_domains` may silently lack marker PFAMs, specifically mentioning the need to validate PF14537 presence. This should be moved from NB06 to NB01 as a data availability check. **Add a validation step in NB01 to confirm PF14537 exists in `bakta_pfam_domains` before proceeding with Phase 1.**

## Recommended (would improve the plan)

1. **Specify execution environment and Spark session pattern**: The plan doesn't clearly state whether analysis will run on BERDL JupyterHub, local machine, or JupyterHub CLI. This affects the correct `get_spark_session()` import pattern:
   - JupyterHub notebooks: `spark = get_spark_session()` (no import)
   - JupyterHub CLI: `from berdl_notebook_utils.setup_spark_session import get_spark_session`
   - Local machine: `from get_spark_session import get_spark_session`

2. **Add specific filtering strategies for large table joins**: NB02's cluster-presence matrix extraction involves joining billion-row tables (`gene` × `gene_genecluster_junction`). The plan mentions ~10-15 min runtime but should specify the filtering approach. Consider using the BROADCAST hints pattern documented in `docs/pitfalls.md` for target genome/cluster ID temp views.

3. **Clarify cohort size estimates**: The "target n ≈ 15-25" for deep-clay anchor seems low for robust statistics, especially with the noted BacDive linkage constraints (line 130). Consider documenting a minimum viable sample size or fallback strategy if BacDive expansion yields fewer than expected matches.

## Optional (nice-to-have)

1. **Add sensitivity analysis for phylogenetic confounding**: Line 128 notes potential order-level bias in the deep-clay anchor. Consider adding a supplementary per-order stratification to verify that significant clusters aren't driven by taxonomic skew.

2. **Project conventions alignment**: Add a `beril.yaml` manifest and ensure the `notebooks/` directory will use sequential numbering (NB01, NB02, etc.) per PROJECT.md standards.

## Relevant pitfalls from docs/pitfalls.md

- **bakta_pfam_domains query format**: The table may use different PFAM ID formats than expected. Investigate actual values before writing queries (line 1776-1788 in pitfalls.md).
- **Billion-row table joins require BROADCAST hints**: Use temp views with BROADCAST hints for target cluster/genome IDs when building presence matrices (cofitness_coinheritance pitfall).
- **Bacillota_B taxonomy exactness**: Use exact phylum match `phylum = 'p__Bacillota_B'`, not LIKE patterns, since Bacillota_A/B/C are distinct phyla (line 74 correctly notes this).
- **String-typed numeric columns**: Cast before comparisons if any fitness or metadata columns are string-typed: `CAST(col AS DOUBLE)`.
- **SQL `--` in species IDs**: Use single quotes around species IDs; the `--` inside quoted strings is not a problem for direct Spark SQL (lines 473-490 in pitfalls.md).

---

*Plan reviewed by Claude (claude-sonnet-4-20250514)*