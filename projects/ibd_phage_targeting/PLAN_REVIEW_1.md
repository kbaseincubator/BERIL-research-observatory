# Research Plan Review: IBD Phage Targeting

**Overall**: This is an ambitious, well-structured plan with a clear five-pillar framework and systematic four-tier criteria rubric, but it has several critical dependencies on undocumented local data and missing import patterns that could cause execution failures.

**Critical** (likely to cause failures or wasted effort):

1. **Missing fact_* table schemas**: The plan heavily relies on `fact_taxon_abundance`, `fact_pathway_abundance`, `fact_metabolomics`, `fact_strain_frequency_wide`, etc. from the local CrohnsPhage data mart, but there are no schema docs in `docs/schemas/` for these tables. Notebook failures are likely without column names, data types, and filter options.

2. **Spark session import pattern not specified**: NB07 and NB12 use "JupyterHub (Spark)" but don't specify the correct import. On BERDL JupyterHub, use `spark = get_spark_session()` (no import — injected into kernel). Missing this will cause import errors.

3. **Large table scan risk**: Queries against `kescience_fitnessbrowser.genefitness` (27M rows) and `kbase_ke_pangenome.gene_cluster` (132M rows) without species-level filtering could timeout. The plan doesn't specify filter strategies for BERDL queries.

**Recommended** (would improve the plan):

1. **Add data audit for local tables**: NB00 should verify the CrohnsPhage data mart schema against what's documented, especially for the 33 tables in schema v2.4. Many fact tables are referenced but never described.

2. **Performance strategy for ANI queries**: The plan mentions `genome_ani` (421M rows) but doesn't address the O(n²) problem flagged in pitfalls.md. For large species like *K. pneumoniae* (14,240 genomes), cap at ≤500 genomes or use subsampling.

3. **Compositional DA validation**: The *C. scindens* paradox is a good validation check, but consider adding other known protective species (*F. prausnitzii*, *A. muciniphila*) to the validation set to ensure the stratification approach is working.

**Optional** (nice-to-have):

1. **Cross-project data reuse**: The CF formulation design project uses similar pathogen-targeting approaches and PhageFoundry data. Consider referencing their phage coverage matrix patterns rather than rebuilding from scratch.

2. **Runtime estimates**: The plan sketches 17 notebooks but doesn't estimate runtimes. NB07/NB12 involving BERDL Spark queries could be lengthy; providing estimates would help with session planning.

**Relevant pitfalls from docs/pitfalls.md**:

- **String-typed numeric columns**: `kescience_fitnessbrowser.genefitness.fit` and `.t` are stored as strings; must `CAST(t AS DOUBLE)` before comparisons (affects Tier-C C3 fitness cost inference).
- **Fitness Browser KO mapping**: Requires two-hop join through `besthitkegg` and `keggmember` tables — no direct `(orgId, locusId) → KO` table (affects phage resistance gene pathway analysis).
- **Pangenome taxonomy joins**: Use `genome_id` for joining `genome` and `gtdb_taxonomy_r214v1` tables, NOT `gtdb_taxonomy_id` (different taxonomy depth levels).
- **Reserved SQL keywords**: `gtdb_taxonomy_r214v1.order` must be backtick-quoted as `\`order\`` in Spark SQL (affects taxonomic analysis).

---

Plan reviewed by Claude (claude-sonnet-4-20250514).
