# Plan Review: Plant Microbiome Ecotypes Phase 2

**Overall**: Well-structured Phase 2 extension plan with clear methodology, but faces some feasibility constraints and overlaps with completed work in related projects.

## Critical (likely to cause failures or wasted effort):

1. **Phase 1 already substantially complete**: The REPORT.md shows comprehensive Phase 1 results (H1-H5 tested, 8 notebooks complete, 1,136 plant-associated species classified). This appears to be a post-hoc design for Phase 2 rather than a pre-analysis plan review.

2. **MGnify table accessibility unclear**: The plan references `kescience_mgnify` collections (genome_kegg_module, gene_bgc, gene_mobilome) but these are not documented in docs/collections.md or docs/schemas/. Verify these tables exist and are accessible before proceeding.

3. **Large table performance risks**: NB12 plans to process `gene` (1B rows) and `gene_genecluster_junction` (1B rows) per-species. Without proper filtering by genome_id first, this could cause timeouts or memory issues (see docs/performance.md patterns).

## Recommended (would improve the plan):

1. **Spark session pattern not specified**: The plan doesn't specify whether this is on-cluster (JupyterHub) or local execution. Based on the scale, this needs on-cluster access with `spark = get_spark_session()` pattern (no import needed in kernel environment).

2. **Refined marker panel needs validation checkpoint**: NB10 removes "ubiquitous bacterial functions" from markers but should include a sanity check that known PGP organisms (Rhizobium, Pseudomonas) still classify correctly with the refined panel.

3. **Novel OG annotation recovery**: NB09 plans to annotate 50 "novel" OGs but many may have been bypassed due to query format issues. Check if `interproscan_domains` versioned Pfam IDs can recover missed annotations before concluding they're truly novel.

4. **Cross-project data reuse opportunity**: pgp_pangenome_ecology project already extracted PGP gene distributions across environments with very similar marker sets. Consider reusing their data extraction (projects/pgp_pangenome_ecology/data/) rather than re-querying.

## Optional (nice-to-have):

1. **Subclade analysis scope**: NB12 targets 10-15 species with ≥20 genomes but genome_ani table is 421M rows. Consider starting with 3-5 high-priority genera to validate the approach before scaling.

2. **NMDC metabolomics integration**: NB13 mentions metabolomics_gold correlation but this is likely sparse data. Include row count checkpoint before investing analysis time.

## Relevant pitfalls from docs/pitfalls.md:

- **Large table scans**: `gene` and `gene_genecluster_junction` (both 1B+ rows) require genome_id filtering to avoid timeouts. Use Pattern 2 (per-species iteration) from docs/performance.md for NB12.
- **GTDB species ID format**: `gtdb_species_clade_id` includes `--` which can cause SQL comment parsing issues. Use `LIKE 'prefix%'` patterns instead of exact matches in WHERE clauses.
- **ncbi_env EAV structure**: Table stores key-value pairs (attribute_name, content), not flat columns. Use proper EAV queries for host species extraction in NB10.
- **Spark DECIMAL→pandas conversion**: gapmind_pathways and NMDC tables return decimal.Decimal objects that need `.astype(float)` or `CAST(... AS DOUBLE)` in SQL.
- **String-typed numeric columns**: Multiple fitness browser and annotation tables store numeric values as strings requiring CAST operations.

---

Plan reviewed by Claude (claude-sonnet-4-20250514).