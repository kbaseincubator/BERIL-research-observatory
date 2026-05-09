# Query Patterns & Safety Rules

Reference module for constructing safe, performant BERDL queries. **Read this before writing any SQL.**

## Mandatory Validation Checklist

Before executing any query, verify ALL items:

- [ ] **Partitioned column filter**: Does the query filter on a partitioned/indexed column (e.g., `gtdb_species_clade_id`, `genome_id`, `orgId`)?
- [ ] **Large table guard**: Are very-large tables filtered before joining? Check `docs/pitfalls.md` per-database section for the current list of tables that must always be filtered (commonly `gene`, `gene_genecluster_junction`, `genome_ani`, `genefitness`, `reaction_similarity`).
- [ ] **Bounded results**: Is the result set bounded by LIMIT, aggregation, or a narrow WHERE clause?
- [ ] **Type safety**: Are string-typed numeric columns CAST before comparison? (Affects: fitnessbrowser, genomes, some metadata)
- [ ] **Species ID quoting**: Are species IDs with `--` inside single-quoted strings (not raw SQL)?
- [ ] **Annotation NULL filter**: Are `-` and NULL filtered for annotation columns (`EC`, `KEGG_ko`, `COG_category`)?
- [ ] **ORDER BY present**: Is ORDER BY included for paginated queries?
- [ ] **Correct JOIN keys**: `eggnog_mapper_annotations.query_name` → `gene_cluster.gene_cluster_id` (NOT `gene.gene_id`)

## Performance Tiers

| Expected Result Size | Strategy | `.toPandas()` OK? |
|---|---|---|
| Small (fits comfortably in memory) | Bounded Spark SQL through `spark.sql(query)` or local `scripts/run_sql.py` | Yes |
| Medium (filter/aggregate first) | Filter first, aggregate in SQL, then retrieve | Only for final aggregated result |
| Large (won't fit in driver memory) | PySpark only on JupyterHub, no `.toPandas()`, use `.write.parquet()` | No — use PySpark DataFrame ops |

See `docs/pitfalls.md` for current per-table size guidance.

**Rule**: Estimate result size BEFORE querying. Check row counts with bounded Spark SQL first if uncertain.

## Query Templates

> **Examples below use specific database/table names** (e.g. `kbase_ke_pangenome.genome`) for clarity. Run `get_databases(return_json=False)` to verify the database is accessible to you before adapting any example.

### Pattern: Safe Species Lookup

**Use when**: Querying any table by species name.

```sql
-- Step 1: Find the exact species clade ID
SELECT gtdb_species_clade_id, GTDB_species
FROM kbase_ke_pangenome.gtdb_species_clade
WHERE GTDB_species LIKE '%Escherichia_coli%'
LIMIT 5

-- Step 2: Use exact ID for subsequent queries
SELECT *
FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
LIMIT 100
```

**Safety rules**:
- Always resolve species name → exact `gtdb_species_clade_id` first
- Use exact equality (`=`) not LIKE for the actual data query
- Species IDs contain `--` which is safe inside single-quoted strings

### Pattern: Annotation Query (Filtering NULLs)

**Use when**: Querying functional annotations from `eggnog_mapper_annotations`.

```sql
SELECT gc.gene_cluster_id, gc.is_core, ann.COG_category, ann.EC, ann.Description
FROM kbase_ke_pangenome.gene_cluster gc
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND ann.COG_category != '-'
  AND ann.COG_category IS NOT NULL
ORDER BY gc.is_core DESC, ann.COG_category
```

**Safety rules**:
- JOIN key is `gene_cluster_id` → `query_name` (NOT `gene_id`)
- Always filter by `gtdb_species_clade_id` first (table is huge)
- Filter annotation NULLs: many genes have `-` or NULL for EC, KEGG_ko, COG_category
- ~40% of genes lack functional annotation — account for this in analysis

### Pattern: Batched IN-Clause

**Use when**: Querying 10–100 items by ID.

```sql
SELECT genome_id, gtdb_species_clade_id
FROM kbase_ke_pangenome.genome
WHERE genome_id IN (
  'RS_GCF_000005845.2',
  'RS_GCF_000008865.2',
  'RS_GCF_000009045.1'
)
```

**Safety rules**:
- Up to ~100 items is fine in an IN clause through Spark SQL
- For >100 items, use chunked queries (batch into groups of 50-100) or use temp views on JupyterHub
- For very large lists, switch to JupyterHub with Spark DataFrames

### Pattern: Cross-Table Join (Small → Large)

**Use when**: Joining metadata tables to large gene/annotation tables.

```sql
-- CORRECT: Filter the large table first, then join
SELECT gc.gene_cluster_id, gc.is_core, ann.KEGG_Pathway
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND ann.KEGG_Pathway != '-'

-- WRONG: Unfiltered join on very-large tables (see docs/pitfalls.md)
SELECT gc.gene_cluster_id, ann.KEGG_Pathway
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
-- Missing WHERE clause = full table scan!
```

**Safety rules**:
- Always filter the largest table by a partition key BEFORE joining
- For pangenome: filter by `gtdb_species_clade_id`
- For fitnessbrowser: filter by `orgId`
- For genomes: filter by genome or feature ID
- Multi-table joins across large species should use JupyterHub Spark

### Pattern: Aggregation Before Transfer

**Use when**: Summarizing data that's too large to transfer whole.

```sql
-- CORRECT: Aggregate in SQL, transfer summary
SELECT
  gc.is_core,
  ann.COG_category,
  COUNT(*) as gene_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
GROUP BY gc.is_core, ann.COG_category
ORDER BY gene_count DESC

-- WRONG: Transfer all rows then aggregate locally
-- (This pulls potentially millions of rows)
```

**Safety rules**:
- Do GROUP BY, COUNT, AVG, SUM in SQL — not in pandas
- Only call `.toPandas()` on aggregated results
- For distribution analysis, use SQL percentiles: `PERCENTILE_APPROX(col, 0.5)`

### Pattern: Safe Numeric Comparison (String-Typed Columns)

**Use when**: Querying fitnessbrowser or any database with string-typed numeric columns.

```sql
-- CORRECT: CAST before comparison
SELECT locusId, sysName, gene_name, CAST(fit AS FLOAT) as fitness
FROM kescience_fitnessbrowser.genefitness
WHERE orgId = 'Keio'
  AND CAST(fit AS FLOAT) < -2
ORDER BY CAST(fit AS FLOAT) ASC
LIMIT 20

-- WRONG: String comparison gives wrong order
WHERE fit < '-2'  -- Compares lexicographically!
```

**Safety rules**:
- All fitnessbrowser columns are strings — always CAST
- `orgId` is case-sensitive: use exact case
- genomes database also has string-typed numeric columns
- After `.toPandas()`, explicitly convert with `pd.to_numeric(col, errors='coerce')`

### Pattern: Paginated Retrieval

**Use when**: Retrieving more rows than a single API call allows.

```sql
-- Page 1
SELECT genome_id, gtdb_species_clade_id
FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id = '{species_id}'
ORDER BY genome_id
LIMIT 1000 OFFSET 0

-- Page 2
SELECT genome_id, gtdb_species_clade_id
FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id = '{species_id}'
ORDER BY genome_id
LIMIT 1000 OFFSET 1000
```

**Safety rules**:
- Always include ORDER BY for deterministic pagination
- Keep local result pages bounded with explicit LIMIT values
- For very large result sets that won't fit in driver memory, use JupyterHub Spark or export results

### Pattern: Existence Check Before Analysis

**Use when**: Verifying data coverage before running complex queries.

```sql
-- Check how many genomes have environmental data
SELECT
  COUNT(*) as total_genomes,
  SUM(CASE WHEN has_sample = true THEN 1 ELSE 0 END) as with_sample,
  SUM(CASE WHEN has_sample = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_coverage
FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id = '{species_id}'

-- Check annotation coverage for a species
SELECT
  COUNT(*) as total_clusters,
  SUM(CASE WHEN ann.query_name IS NOT NULL THEN 1 ELSE 0 END) as annotated,
  SUM(CASE WHEN ann.COG_category != '-' AND ann.COG_category IS NOT NULL THEN 1 ELSE 0 END) as has_cog
FROM kbase_ke_pangenome.gene_cluster gc
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
```

**Safety rules**:
- AlphaEarth embeddings: partial coverage — see `docs/pitfalls.md` for current numbers
- Functional annotations: ~40% of genes lack annotation
- NCBI environment metadata: EAV format, sparse coverage
- Geographic coordinates: often NULL or malformed
- Always check coverage BEFORE building an analysis around sparse data

## Local vs JupyterHub Decision Guide

| Scenario | Use local bounded Spark SQL | Use JupyterHub Spark |
|---|---|---|
| Quick schema check | Use helper discovery | — |
| Single-species query (small result) | Yes | — |
| Multi-species aggregation | — | Yes |
| Joining across large tables | — | Yes |
| Very-large tables (see `docs/pitfalls.md`) | — | Yes |
| Iterative analysis with intermediate results | — | Yes |
| One-off count or sample | Yes | — |

Use the environment detected by `scripts/detect_berdl_environment.py`: on-cluster
sessions should run `spark.sql(query)` directly, while off-cluster sessions can
use `scripts/run_sql.py --berdl-proxy` after the proxy chain is ready.

## Common ID Formats

| ID Type | Format | Example |
|---|---|---|
| `genome_id` | `RS_GCF_XXXXXXXXX.X` or `GB_GCA_XXXXXXXXX.X` | `RS_GCF_000005845.2` |
| `gtdb_species_clade_id` | `s__Genus_species--{representative_genome}` | `s__Escherichia_coli--RS_GCF_000005845.2` |
| `gene_cluster_id` | `{contig}_{number}` | `NZ_CP095497.1_1766` |
| ModelSEED reaction | `seed.reaction:rxnNNNNN` | `seed.reaction:rxn00001` |
| ModelSEED compound | `seed.compound:cpdNNNNN` | `seed.compound:cpd00001` |
| Fitness `orgId` | Case-sensitive string | `Keio` |
