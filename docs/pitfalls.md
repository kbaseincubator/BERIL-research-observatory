# BERDL Database: Common Pitfalls & Gotchas

**Purpose**: Quick reference for avoiding common issues when querying BERDL databases.

See [collections.md](collections.md) for the full database inventory and [schemas/](schemas/) for per-collection documentation.

---

## General BERDL Pitfalls

### PySpark Cannot Infer numpy `str_` Types

**[prophage_ecology]** `np.random.choice()` on a list of Python strings returns numpy `str_` objects. PySpark's `createDataFrame()` cannot infer schema for `str_`, raising `PySparkTypeError: [CANNOT_INFER_TYPE_FOR_FIELD]`.

**Fix**: Always cast to native Python `str` before creating DataFrames:
```python
# WRONG: numpy str_ types
genome_ids = list(np.random.choice(all_genome_ids, 300, replace=False))
spark.createDataFrame([(g,) for g in genome_ids], ['genome_id'])  # FAILS

# CORRECT: explicit str() cast
genome_ids = [str(g) for g in np.random.choice(all_genome_ids, 300, replace=False)]
spark.createDataFrame([(g,) for g in genome_ids], ['genome_id'])  # OK
```

### REST API Reliability

The REST API at `https://hub.berdl.kbase.us/apis/mcp/` can experience issues:

| Error | Meaning | Solution |
|-------|---------|----------|
| 504 Gateway Timeout | Query took too long | Simplify query, add filters, use direct Spark |
| 524 Origin Timeout | Server didn't respond | Retry after a few seconds |
| 503 "cannot schedule new futures after shutdown" | Spark executor restarting | Wait 30s, retry |
| Empty response | Query failed silently | Check query syntax |

**Rule of thumb**: Prefer direct Spark SQL (`get_spark_session()`) over the REST API whenever possible. The REST API `/count` endpoint is particularly unreliable -- it frequently returns errors or times out for tables that Spark queries handle instantly. The REST API is acceptable for small one-off queries, but looping over many tables (e.g., getting row counts for all sdt_* tables) should use Spark directly.

### Schema Introspection Timeouts

The `/schema` API endpoint frequently times out for large tables. Use `DESCRIBE database.table` via the `/query` endpoint instead for more reliable schema introspection.

### Auth Token Variable Name

The `.env` file uses `KBASE_AUTH_TOKEN` (not `KB_AUTH_TOKEN`):
```bash
# CORRECT
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)

# WRONG (legacy docs may reference this)
AUTH_TOKEN=$(grep "KB_AUTH_TOKEN" .env | cut -d'"' -f2)
```

### MinIO Upload Requires Proxy (Off-Cluster)

**[essential_metabolome]** When uploading projects to the lakehouse via `python tools/lakehouse_upload.py`, the `mc` (MinIO client) commands will timeout if proxy environment variables are not set.

**Symptom**: Upload fails with:
```
Get 'https://minio.berdl.kbase.us/cdm-lake/?location=': dial tcp 140.221.43.167:443: i/o timeout
```

**Root cause**: MinIO server (minio.berdl.kbase.us:443) is only reachable from within the BERDL cluster or through the proxy chain.

**Solution**: Set proxy environment variables before running the upload script:
```bash
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1
python3 tools/lakehouse_upload.py <project_id>
```

**Prerequisites**: SSH tunnels (ports 1337, 1338) and pproxy (port 8123) must be running. See `.claude/skills/berdl-minio/SKILL.md` for setup details.

**Note**: This applies to ALL `mc` commands when off-cluster, not just uploads. The `lakehouse_upload.py` script should be updated to set these variables automatically, but for now they must be set manually.

### String-Typed Numeric Columns

Many databases store numeric values as strings. Always cast before comparisons:
```sql
-- WRONG: String comparison
WHERE fit < -2

-- CORRECT: Cast to numeric
WHERE CAST(fit AS FLOAT) < -2
```

This affects: `kescience_fitnessbrowser` (all columns), `kbase_genomes` (coordinates, lengths), and others.

### [nmdc_community_metabolic_ecology] Spark DECIMAL Columns Return `decimal.Decimal` in Pandas, Not `float`

**Problem**: Spark SQL `DECIMAL` columns (e.g., `abundance` in `nmdc_arkin.centrifuge_gold`) are returned as Python `decimal.Decimal` objects when collected via `.toPandas()`. Arithmetic with `float` values (e.g., from `AVG()` aggregates) raises `TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'`.

**Solution**: `CAST(col AS DOUBLE)` in the SQL query, or `.astype(float)` on the pandas column after collection:

```python
# Option 1: Cast in SQL (preferred — avoids the type in the DataFrame entirely)
spark.sql("SELECT CAST(abundance AS DOUBLE) AS abundance FROM ...")

# Option 2: Cast after .toPandas()
df['abundance'] = df['abundance'].astype(float)
```

**Second manifestation**: `AVG(CASE WHEN condition THEN 1.0 ELSE 0.0 END)` also returns `DECIMAL` because Spark treats the literal `1.0` as `DECIMAL(2,1)`, not `DOUBLE`. Use `CAST(AVG(...) AS DOUBLE)` on aggregated columns too:

```sql
-- WRONG — frac_complete arrives as decimal.Decimal
AVG(CASE WHEN best_score >= 5 THEN 1.0 ELSE 0.0 END) AS frac_complete

-- CORRECT
CAST(AVG(CASE WHEN best_score >= 5 THEN 1.0 ELSE 0.0 END) AS DOUBLE) AS frac_complete
```

**Rule of thumb**: Any `AVG()` over integers or decimal literals in Spark SQL should be wrapped in `CAST(... AS DOUBLE)`. Add `.astype(float)` after `.toPandas()` as a defensive safety net.

Observed in `[nmdc_community_metabolic_ecology]` NB03: `centrifuge_gold.abundance` (cell-15) and `gapmind_pathways` AVG aggregates (cell-11/18).

### `SELECT DISTINCT col, COUNT(*) ...` Without GROUP BY Fails in Spark Strict Mode

Spark Connect's SQL analyzer rejects `SELECT DISTINCT` combined with an aggregate function when no `GROUP BY` is present (`MISSING_GROUP_BY`, SQLSTATE 42803). This is a strict standard-SQL interpretation that differs from some other databases (e.g., DuckDB, SQLite) which accept this syntax.

```sql
-- WRONG — AnalysisException: MISSING_GROUP_BY
SELECT DISTINCT score_category, COUNT(*) as n
FROM kbase_ke_pangenome.gapmind_pathways
LIMIT 20

-- CORRECT — GROUP BY only; DISTINCT is redundant when GROUP BY is present
SELECT score_category, COUNT(*) as n
FROM kbase_ke_pangenome.gapmind_pathways
GROUP BY score_category
ORDER BY n DESC
```

**Rule**: Never combine `DISTINCT` with aggregate functions. Use `GROUP BY` exclusively for grouped aggregations. `SELECT DISTINCT col, COUNT(*)` is always wrong — replace with `GROUP BY col`.

Observed in `[nmdc_community_metabolic_ecology]` NB03 cell-9 when checking `score_category` value distribution in `gapmind_pathways`.

---

## Pangenome (`kbase_ke_pangenome`) Pitfalls

### Taxonomy Join: Use `genome_id`, NOT `gtdb_taxonomy_id`

**[prophage_ecology]** The `genome` and `gtdb_taxonomy_r214v1` tables both have a `gtdb_taxonomy_id` column, but they store **different levels of the taxonomy string**:

- `genome.gtdb_taxonomy_id`: truncated at genus level (e.g., `d__Bacteria;p__Bacillota;...;g__Staphylococcus`)
- `gtdb_taxonomy_r214v1.gtdb_taxonomy_id`: includes species (e.g., `d__Bacteria;p__Bacillota;...;s__Staphylococcus aureus`)

Joining on `gtdb_taxonomy_id` returns **zero rows**. Always join on `genome_id`:

```sql
-- CORRECT: join on genome_id
SELECT g.gtdb_species_clade_id, t.phylum, t.family
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t ON g.genome_id = t.genome_id

-- WRONG: returns 0 rows because taxonomy depth differs
SELECT g.gtdb_species_clade_id, t.phylum, t.family
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t ON g.gtdb_taxonomy_id = t.gtdb_taxonomy_id
```

### SQL Syntax Issues

### The `--` Non-Issue in Species IDs

Species clade IDs contain `--` (e.g., `s__Escherichia_coli--RS_GCF_000005845.2`), but this is **NOT a problem** in SQL when the ID is inside a quoted string literal.

```sql
-- CORRECT: The '--' inside quotes is NOT interpreted as a comment
SELECT * FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'

-- AVOID: LIKE patterns are slower and unnecessary
SELECT * FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id LIKE 's__Escherichia_coli%'
```

**Note**: The `--` would only be a problem if it appeared outside of quotes in the SQL statement itself. When using exact equality with proper quoting, there is no issue and performance is better.

### ID Format Reference

| ID Type | Format | Example |
|---------|--------|---------|
| `genome_id` | `RS_GCF_XXXXXXXXX.X` or `GB_GCA_XXXXXXXXX.X` | `RS_GCF_000005845.2` |
| `gtdb_species_clade_id` | `s__Genus_species--{representative_genome_id}` | `s__Escherichia_coli--RS_GCF_000005845.2` |
| `gene_cluster_id` | `{contig}_{number}` or `{prefix}_mmseqsCluster_{number}` | `NZ_CP095497.1_1766` |

### [metabolic_capability_dependency] `gtdb_metadata` NCBI Taxid Column Returns Boolean Strings, Not Numeric IDs

**Problem**: Attempting to join `kescience_fitnessbrowser.organism` to `kbase_ke_pangenome.gtdb_metadata` via NCBI taxonomy IDs returns zero matches. The `ncbi_taxid` (or equivalent) column in `gtdb_metadata` contains the string values `"t"` / `"f"` (boolean tokens) rather than numeric taxonomy IDs.

**Symptom**: A query like:
```python
gtdb_metadata_spark.filter(col("ncbi_taxid").isin(fb_taxids))
```
returns 0 rows even when the taxids should match, because the stored values are `"t"`/`"f"`, not integers.

**Solution**: Inspect the column values before joining:
```python
spark.sql("SELECT ncbi_taxid, COUNT(*) FROM kbase_ke_pangenome.gtdb_metadata GROUP BY ncbi_taxid LIMIT 10").show()
```
Use an alternative join key (e.g., organism name string matching or `orgId`-based lookup) or look for a different taxonomy column. In `metabolic_capability_dependency`, the fallback was to match organisms directly by `orgId` without a clade-level link.

### [nmdc_community_metabolic_ecology] `gapmind_pathways.clade_name` = `gtdb_species_clade_id` Format, NOT `GTDB_species`

**Problem**: `gapmind_pathways.clade_name` stores the full `gtdb_species_clade_id` including the representative genome accession suffix (e.g., `s__Rhizobium_phaseoli--RS_GCF_001234567.1`). It does **not** store the short `GTDB_species` name (e.g., `s__Rhizobium_phaseoli`).

**Symptom**: Joining `gapmind_pathways` on a temp view populated from `gtdb_species_clade.GTDB_species` returns 0 rows because the two formats don't match.

**Solution**: When filtering `gapmind_pathways` by species, use `gtdb_species_clade_id` values directly. The `taxon_bridge.tsv` produced by NB02 already stores `gtdb_species_clade_id` — use those directly as the clade filter without a round-trip through `gtdb_species_clade.GTDB_species`.

```python
# WRONG — uses GTDB_species format (s__Genus_species) which doesn't match clade_name
gtdb_meta = spark.sql("SELECT GTDB_species FROM kbase_ke_pangenome.gtdb_species_clade").toPandas()
clade_names_df = pd.DataFrame({'clade_name': gtdb_meta['GTDB_species'].tolist()})

# CORRECT — use gtdb_species_clade_id directly (matches clade_name in gapmind_pathways)
clade_names_df = pd.DataFrame({'clade_name': mapped_clade_ids})  # from taxon_bridge
```

### [nmdc_community_metabolic_ecology] `gapmind_pathways.metabolic_category` Values Are `'aa'` and `'carbon'`, Not `'amino_acid'`

**Problem**: Filter code using `metabolic_category == 'amino_acid'` returns 0 rows. The actual stored values are `'aa'` (amino acid pathways) and `'carbon'` (carbon source pathways).

```python
# WRONG
aa_mask = df['metabolic_category'] == 'amino_acid'  # always False

# CORRECT
aa_mask = df['metabolic_category'] == 'aa'
```

### [nmdc_community_metabolic_ecology] Spark Connect Temp Views Lost After Long-Running Cell

**Problem**: A Spark temp view registered in cell N may be silently destroyed if the Spark Connect server reconnects during cell N (e.g., triggered by an expensive 305M-row full-table scan). Subsequent cells that JOIN against the temp view return 0 rows with no error.

**Symptom**: Row count queries like `SELECT COUNT(*) FROM table JOIN temp_view ON ...` return 0 unexpectedly.

**Solution**: Re-register the temp view immediately before any cell that uses it in a JOIN. The Python variable holding the data persists in the kernel even when the Spark server reconnects.

```python
# At the top of any cell that JOINs against a temp view:
spark.createDataFrame(
    pd.DataFrame({'clade_name': mapped_clade_names})
).createOrReplaceTempView('mapped_clade_names_tmp')
```

**Prevention**: Avoid expensive full-table scans in cells between temp view registration and temp view use. Use `LIMIT` or `TABLESAMPLE` for schema verification queries rather than full `GROUP BY` counts on large tables.

---

## Data Sparsity Issues

### AlphaEarth Embeddings (28.4% coverage)

Only 83,227 of 293,059 genomes have environmental embeddings.

```sql
-- Check if a species has embeddings before relying on them
SELECT COUNT(DISTINCT ae.genome_id) as n_with_embeddings,
       COUNT(DISTINCT g.genome_id) as n_total
FROM kbase_ke_pangenome.genome g
LEFT JOIN kbase_ke_pangenome.alphaearth_embeddings_all_years ae
    ON g.genome_id = ae.genome_id
WHERE g.gtdb_species_clade_id LIKE 's__Klebsiella_pneumoniae%'
```

**Why sparse?**: Embeddings require valid lat/lon coordinates, which are often missing in NCBI metadata, especially for clinical isolates.

### NCBI Environment Metadata (EAV format)

The `ncbi_env` table uses Entity-Attribute-Value format - multiple rows per sample.

```sql
-- Get isolation source for a genome
SELECT content
FROM kbase_ke_pangenome.ncbi_env
WHERE accession = 'SAMN12345678'
  AND harmonized_name = 'isolation_source'

-- Pivot to get multiple attributes
SELECT accession,
       MAX(CASE WHEN harmonized_name = 'isolation_source' THEN content END) as isolation_source,
       MAX(CASE WHEN harmonized_name = 'geo_loc_name' THEN content END) as location
FROM kbase_ke_pangenome.ncbi_env
WHERE accession IN ('SAMN12345678', 'SAMN87654321')
GROUP BY accession
```

### Geographic Coordinates

`ncbi_lat_lon` in `gtdb_metadata` is often:
- NULL (most common)
- Malformed strings ("missing", "not collected")
- Low precision ("37.0 N 122.0 W")

---

## Foreign Key Gotchas

### Orphan Pangenomes (12 species)

12 pangenome records reference species clades not in `gtdb_species_clade`:

```
s__Portiera_aleyrodidarum--RS_GCF_000300075.1
s__Profftella_armatura--RS_GCF_000441555.1
s__Nanosynbacter_sp022828325--RS_GCF_022828325.1
... (mostly symbionts and single-genome species)
```

These are valid pangenomes but filtered from species metadata. Handle with LEFT JOIN.

### Annotation Table Join Key

`eggnog_mapper_annotations.query_name` joins to `gene_cluster.gene_cluster_id`, NOT to `gene.gene_id`:

```sql
-- CORRECT: Join on gene_cluster_id
SELECT gc.gene_cluster_id, e.COG_category, e.Description
FROM kbase_ke_pangenome.gene_cluster gc
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations e
    ON gc.gene_cluster_id = e.query_name
WHERE gc.gtdb_species_clade_id LIKE 's__Mycobacterium%'

-- WRONG: gene_id won't match
SELECT * FROM kbase_ke_pangenome.eggnog_mapper_annotations
WHERE query_name = 'some_gene_id'  -- This won't find anything
```

### Gene Clusters are Species-Specific

Gene cluster IDs are only meaningful within a species. You cannot compare cluster IDs across species:

```sql
-- This comparison is MEANINGLESS:
-- Cluster "X_123" in E. coli is unrelated to "X_123" in Salmonella

-- To compare gene content across species, use:
-- 1. COG categories from eggnog_mapper_annotations
-- 2. KEGG orthologs (KEGG_ko column)
-- 3. PFAM domains
```

---

## Data Interpretation Issues

### Core/Auxiliary/Singleton Definitions

In `gene_cluster` table:
- `is_core` = 1: Present in ≥95% of genomes
- `is_auxiliary` = 1: Present in <95% and >1 genome
- `is_singleton` = 1: Present in exactly 1 genome

**These are mutually exclusive** (only one flag is 1 per row).

**Important**: These are stored as integers (0/1), not booleans:
```sql
-- CORRECT
WHERE is_core = 1

-- May fail depending on SQL dialect
WHERE is_core = true
```

### Pangenome Table Count Interpretation

In `pangenome` table:
- `no_core` + `no_aux_genome` = `no_gene_clusters` (total clusters)
- `no_singleton_gene_clusters` ⊂ `no_aux_genome` (singletons are a subset of auxiliary)

```sql
-- Verify: core + aux = total
SELECT
    no_core + no_aux_genome as computed_total,
    no_gene_clusters as reported_total,
    no_singleton_gene_clusters as singletons,
    no_aux_genome as auxiliary
FROM kbase_ke_pangenome.pangenome
LIMIT 5
```

---

## JupyterHub Environment Issues

### `get_spark_session()` — Use the Right Import for Your Environment

There are three environments with different import patterns. Using the wrong one causes `ImportError`:

| Environment | Import | Why |
|---|---|---|
| **BERDL JupyterHub notebooks** | `spark = get_spark_session()` (no import) | Injected by `/configs/ipython_startup/00-notebookutils.py` |
| **BERDL JupyterHub CLI/scripts** | `from berdl_notebook_utils.setup_spark_session import get_spark_session` | Same module, explicit import. **[fitness_modules]** discovered this works from regular Python scripts, not just notebooks. |
| **Local machine** | `from get_spark_session import get_spark_session` | Uses `scripts/get_spark_session.py`, requires `.venv-berdl` + proxy chain |

**Common mistakes**:
- Using `from get_spark_session import get_spark_session` on the BERDL cluster → `ImportError` (that module is `scripts/get_spark_session.py`, only on local machines)
- Using `from berdl_notebook_utils.setup_spark_session import get_spark_session` locally → `ImportError` (that package is only on the BERDL cluster)
- Using the bare `get_spark_session()` (no import) in a CLI script on JupyterHub → `NameError` (auto-import only applies to notebook kernels)

### Don't Kill Java Processes

**[conservation_vs_fitness]** The Spark Connect service runs as a Java process on port 15002. Killing Java processes (e.g., when cleaning up stale notebook processes) will take down Spark Connect, and `get_spark_session()` will fail with `RETRIES_EXCEEDED` / `Connection refused`.

**Recovery**: Log out of JupyterHub and start a new session. Then run `get_spark_session()` from a notebook to restart the Spark Connect daemon. You cannot restart it from the CLI.

### Running Notebooks from CLI

Notebooks can be executed headlessly via `jupyter nbconvert`:

```bash
jupyter nbconvert --to notebook --execute notebook.ipynb \
  --output notebook_executed.ipynb \
  --ExecutePreprocessor.timeout=7200
```

The kernel spawned by nbconvert has `get_spark_session()` available. However, long-running notebooks may time out — set `--ExecutePreprocessor.timeout` appropriately.

**Tip**: For long pipelines, design notebooks with checkpointing (save intermediate files, skip steps that already have output). This allows re-running after interruptions without repeating completed work.

---

## Pandas-Specific Issues

### Unnecessary `.toPandas()` Calls

**`.toPandas()` pulls all data from the Spark cluster to the driver node.** This is slow for large results and can cause out-of-memory errors. Do filtering, joins, and aggregations in Spark first.

```python
# BAD: Pull 132M rows to driver, then filter locally
df = spark.sql("SELECT * FROM kbase_ke_pangenome.gene_cluster").toPandas()
core = df[df['is_core'] == 1]

# GOOD: Keep as Spark DataFrame, filter in Spark
df = spark.sql("""
    SELECT * FROM kbase_ke_pangenome.gene_cluster
    WHERE is_core = 1
    AND gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
""")

# Only convert to pandas for small, final results (plotting, export)
summary = df.groupBy("gtdb_species_clade_id").count().toPandas()
```

**Rule of thumb**: Use PySpark DataFrame operations for all intermediate steps. Only call `.toPandas()` when you need the data locally (matplotlib plots, CSV export, or results that are a few thousand rows).

See [performance.md](performance.md) for detailed PySpark-first patterns.

### NaN Handling When Mapping to Dictionaries

**[cog_analysis]** When mapping COG categories to descriptions using a dictionary, composite categories (e.g., "LV", "EGP") will return NaN if not in the dictionary. String operations on NaN values will fail:

```python
# Dictionary only has single-letter COGs
COG_DESCRIPTIONS = {
    'J': 'Translation, ribosomal structure',
    'L': 'Replication, recombination, repair',
    # ... but no "LV", "EGP", etc.
}

# This will introduce NaN values for composite COGs
df['description'] = df['COG_category'].map(COG_DESCRIPTIONS)

# BAD: This will fail with TypeError on NaN values
labels = [f"{row['COG_category']}: {row['description'][:40]}" for _, row in df.iterrows()]

# GOOD: Check for NaN before string operations
labels = []
for _, row in df.iterrows():
    desc = row['description'][:40] if pd.notna(row['description']) else 'Unknown'
    labels.append(f"{row['COG_category']}: {desc}")
```

**Solution**: Always use `pd.notna()` or `pd.isna()` before string slicing or other operations on potentially-NaN columns.

### Type Conversion from Spark .toPandas()

Numeric columns from Spark can come through as strings when using `.toPandas()`:

```python
df = spark.sql("SELECT no_genomes, no_core FROM pangenome").toPandas()

# BAD: Might fail with type error if columns are strings
filtered = df[df['no_genomes'] <= 500]  # TypeError: '<=' not supported for str

# GOOD: Explicitly convert to numeric
numeric_cols = ['no_genomes', 'no_core', 'no_aux_genome']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')
```

---

## Pangenome: Missing Tables

These tables were previously missing but some have been added:

| Table | Mentioned Purpose | Status (2026-02-11) |
|-------|-------------------|--------|
| `phylogenetic_tree` | Species trees from core genes | **NOW AVAILABLE** |
| `phylogenetic_tree_distance_pairs` | Pairwise phylo distances | **NOW AVAILABLE** |
| `pangenome_build_protocol` | Build parameters | NOT FOUND (but `protocol_id` column exists) |
| `genomad_mobile_elements` | Plasmid/virus annotations | NOT FOUND |
| `IMG_env` | IMG environment metadata | NOT FOUND |

---

## Pangenome: API vs Direct Spark

Use direct `spark.sql()` on the cluster when:
- Query involves >1M rows
- JOINs across large tables
- Aggregations on billion-row tables
- REST API keeps timing out

### [cog_analysis] Multi-table joins can be slow for large species

**Problem**: Joining gene → gene_genecluster_junction → gene_cluster → eggnog_mapper_annotations can be slow for species with >500 genomes.

**Solutions**:
1. **Use direct Spark**: Run on JupyterHub with `spark.sql()` instead of REST API
2. **Separate queries per gene class**: Break into smaller queries
3. **Select smaller species**: Use species with 100-300 genomes for faster queries

**Performance tip**: Always use exact equality (`WHERE id = 'value'`) rather than `LIKE` patterns for best performance.

### [cofitness_coinheritance] Phylo distance genome IDs lack GTDB prefix

**Problem**: The `phylogenetic_tree_distance_pairs` table uses bare NCBI accessions (`GCA_001038305.1`, `GCF_000005845.2`) while all other pangenome tables (`genome`, `gene`, `gene_genecluster_junction`) use GTDB-prefixed IDs (`GB_GCA_001038305.1`, `RS_GCF_000005845.2`). Joining phylo distances with presence matrices produces zero matches because no IDs overlap.

**Solution**: Strip the `GB_` or `RS_` prefix (first 3 characters) from GTDB genome IDs before joining with phylo distance data:
```python
def strip_gtdb_prefix(genome_id):
    if genome_id.startswith(('GB_', 'RS_')):
        return genome_id[3:]
    return genome_id
```

After stripping, overlap is 100% for all tested species (399/399 for Koxy, 287/287 for Btheta, etc.).

---

### [cofitness_coinheritance] Billion-row table joins require BROADCAST hints

**Problem**: Joining `gene_genecluster_junction` (~1B rows) with `gene` (~1B rows) to build genome × cluster presence matrices takes 3-5 minutes per species, even on Spark. Neither table is partitioned by `gene_cluster_id` or `genome_id`, so every query requires a full table scan.

**Profiling results** (Smeli, 241 genomes, 6K target clusters):
- Without BROADCAST: ~300s per organism
- With `/*+ BROADCAST(tc), BROADCAST(tg) */` on filter tables: ~274s (8% improvement)
- Two-stage approach (filter junction first, then lookup genome_ids): ~310s (no improvement)
- `.toPandas()` on 1-2M result rows: <2s (not the bottleneck)

**Solutions**:
1. **Use BROADCAST hints**: Register target cluster IDs and genome IDs as temp views, then use `/*+ BROADCAST(tc), BROADCAST(tg) */` in the query
2. **Cache aggressively**: Once extracted, save matrices as TSV and skip on re-run
3. **Set long timeouts**: `ExecutePreprocessor.timeout=3600` for `nbconvert --execute`
4. **Budget ~5 min per organism**: 11 organisms ≈ 55 min total for matrix extraction

**Root cause**: The `gene` and `gene_genecluster_junction` tables are stored as unpartitioned parquet. Adding partitioning by `genome_id` (for `gene`) or `gene_cluster_id` (for junction) would dramatically reduce scan time, but this requires rebuilding the lakehouse tables.

---

## Fitness Browser (`kescience_fitnessbrowser`) Pitfalls

### All Columns Are Strings

Every column in the fitness browser is stored as a string. Always cast before numeric comparisons:

```sql
-- WRONG
WHERE fit < -2

-- CORRECT
WHERE CAST(fit AS FLOAT) < -2
```

### orgId is Case-Sensitive

Use exact case: `WHERE orgId = 'Keio'` (not `'keio'`).

### genefitness Table is Large (27M rows)

Always filter by `orgId` at minimum.

### Per-Organism Convenience Tables

**[fitness_modules]** The `fitbyexp_*` tables are **long format** (columns: `expName, locusId, fit, t`), NOT pre-pivoted wide tables as the schema docs suggest. They're equivalent to a per-organism slice of `genefitness`. Use `genefitness` directly with an `orgId` filter instead.

### KEGG Annotation Join Path

**[fitness_modules]** `keggmember` does NOT have `orgId` or `locusId` columns. It has `keggOrg, keggId, kgroup`. To link genes to KEGG groups:

```sql
-- CORRECT: Join through besthitkegg
SELECT bk.locusId, km.kgroup, kd.desc
FROM kescience_fitnessbrowser.besthitkegg bk
JOIN kescience_fitnessbrowser.keggmember km
    ON bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId
LEFT JOIN kescience_fitnessbrowser.kgroupdesc kd ON km.kgroup = kd.kgroup
WHERE bk.orgId = 'DvH'

-- WRONG: keggmember has no orgId column
SELECT * FROM kescience_fitnessbrowser.keggmember WHERE orgId = 'DvH'
```

Also: `kgroupec` uses column `ecnum` (not `ec`).

### Experiment Table Is Named `experiment`, Not `exps`

**[pathway_capability_dependency]** The experiments table in `kescience_fitnessbrowser` is called `experiment` (not `exps`). Column names: `expName` (not `name`), `expGroup` (not `Group`), `condition_1` (not `Condition_1`). The `expGroup` column provides clean condition categories ("carbon source", "nitrogen source", "stress", "pH", "temperature", etc.) — use this for condition-type classification instead of pattern matching on `condition_1`.

### seedannotationtoroles Joins on `seed_desc`, Not `orgId`/`locusId`

**[pathway_capability_dependency]** The `seedannotationtoroles` table has columns `seed_desc` and `seedrole` only — no `orgId` or `locusId`. Join chain: `seedannotation` (orgId, locusId, seed_desc) → `seedannotationtoroles` (seed_desc → seedrole) → `seedroles` (seedrole → toplevel, category, subsystem). The `seedroles` table columns are `toplevel`, `category`, `subsystem`, `seedrole` — not `seed_role`, `seed_subsystem`, or `seedroleId`.

### seedclass Has No Subsystem Hierarchy

**[fitness_modules]** `seedclass` has columns `orgId, locusId, type, num` — it stores EC numbers, NOT SEED subsystem categories. Use `seedannotation` (columns: `orgId, locusId, seed_desc`) for functional descriptions.

### ICA Component Ratio Affects Performance

**[fitness_modules]** When running FastICA on fitness matrices, keep `n_components` ≤ 40% of `n_experiments`. Higher ratios cause frequent convergence failures, and each failed run hits `max_iter` (very slow). For an organism with 150 experiments, use at most 60 components.

### Cosine Distance Floating-Point Issue

**[fitness_modules]** When computing pairwise cosine distance (`1 - |cosine_similarity|`) for DBSCAN clustering, tiny negative values can appear due to floating-point precision. DBSCAN with `metric="precomputed"` rejects negative distances. Fix: `np.clip(cos_dist, 0, 1, out=cos_dist)` before clustering.

### Ortholog Scope Must Match Analysis Scope

**[fitness_modules]** When building cross-organism ortholog groups, always extract BBH pairs for ALL organisms in the analysis — not just a pilot subset. Using 5-organism orthologs for a 32-organism analysis produced 6x fewer module families and missed all families spanning 5+ organisms. The ortholog graph gains transitive connections from each new organism, so partial extraction severely underestimates cross-organism conservation.

### D'Agostino K² is Wrong for ICA Membership Thresholding

**[fitness_modules]** ICA weight distributions are intentionally non-Gaussian (heavy-tailed), so the D'Agostino K² normality test always rejects normality, causing it to use a permissive z-threshold (2.5) that lets 100-280 genes into each module. Use absolute weight thresholds instead (|Pearson r| ≥ 0.3 with module profile, max 50 genes). This is the single most impactful parameter in the pipeline.

### Enrichment min_annotated Must Match Annotation Granularity

**[fitness_modules]** Using `min_annotated=3` with KEGG KOs (~1.2 genes per KO) results in only 8% of modules getting any enrichment — almost no KEGG term has 3+ genes in a single 5-50 gene module. Lower to `min_annotated=2` (still valid with FDR correction) and include PFam domains (814 terms with 2+ genes) alongside TIGRFam (88 terms). This increases module annotation from 8% to 80%.

### FB Locus Tag Mismatch Between Gene Table and Aaseqs Download

**[conservation_vs_fitness]** The FB protein sequences at `fit.genomics.lbl.gov/cgi_data/aaseqs` use RefSeq-style locus tags for some organisms (e.g., `ABZR86_RS00005` for Dyella79), while the FB `gene` table uses the original annotation locus tags (`N515DRAFT_0001`). If you build DIAMOND databases from aaseqs and then try to join the hit locusIds back to the gene table, the join will silently produce zero matches. Check locusId overlap between datasets before analysis. Affected: Dyella79 (0% overlap). Other organisms had >94% overlap.

### FB Gene Table Has No Essentiality Flag

**[conservation_vs_fitness]** After checking all 45 tables in `kescience_fitnessbrowser`, there is no explicit essentiality column, insertion count, or "has fitness data" flag. The `gene.type` column encodes feature type (1=CDS, 5=pseudo, 7=rRNA, 2=tRNA), not essentiality. To identify putative essential genes, compare the `gene` table (type='1') against `genefitness` — genes absent from genefitness had no viable transposon mutants. This is an upper bound on true essentiality.

### Spark LIMIT/OFFSET Pagination Is Slow

**[conservation_vs_fitness]** Using `LIMIT N OFFSET M` for pagination in Spark queries causes Spark to re-scan all rows up to the offset on each query. For extracting cluster rep FASTAs across 154 clades, paginated queries (5000 rows per batch) were orders of magnitude slower than single queries per clade. Since `gene_cluster` is partitioned by `gtdb_species_clade_id`, a single `WHERE gtdb_species_clade_id = 'X'` query per clade is fast. Only paginate when the result set would exceed memory.

### % Core Denominator Inconsistency Across Projects

**[conservation_fitness_synthesis]** When computing "% core," the denominator matters: using all genes (including unmapped) gives lower percentages (e.g., essential = 82% core) than using mapped genes only (86% core). Different projects may use different denominators. This caused a critical review issue where figures showed 86%/78% but prose said 82%/66%. Always document which denominator is used, and be consistent within a synthesis or comparison.

### Row-Wise Apply on Large DataFrames Is Orders of Magnitude Slower Than Merge

**[core_gene_tradeoffs]** Filtering a 961K-row DataFrame with `df.apply(lambda r: (r['orgId'], r['locusId']) in some_set, axis=1)` is extremely slow because it iterates row-by-row in Python. Replace with `df.merge(keys_df, on=['orgId','locusId'], how='inner')` for the same result in seconds instead of minutes. This applies whenever you need to filter a large DataFrame to rows matching a set of key pairs.

### Column Name Collisions When Merging Family Annotations

**[module_conservation]** Merging `module_families.csv` with `family_annotations.csv` on `familyId` can create duplicate column names (`n_modules_x`, `n_modules_y`) when both DataFrames have columns with the same name. Use explicit `suffixes=('_obs', '_annot')` in the merge call to avoid ambiguous column names in downstream analysis and saved TSV files.

### Essential Genes Are Invisible in genefitness-Only Analyses

**[fitness_effects_conservation]** If you query only the `genefitness` table for fitness data, you miss ~14.3% of protein-coding genes — the essential genes that have no transposon insertions and therefore no entries in `genefitness`. These are the most functionally important genes (82% core). Any analysis of fitness vs conservation must explicitly include essential genes from the `gene` table (type='1' genes absent from `genefitness`), or acknowledge that the most extreme fitness category is missing.

### Reviewer Subprocess May Write to Nested Path

**[fitness_effects_conservation]** When invoking the `/submit` reviewer subprocess, if the subprocess resolves `projects/{id}/` relative to its own working directory rather than the repo root, the `REVIEW.md` file can end up at `projects/{id}/projects/{id}/REVIEW.md` instead of `projects/{id}/REVIEW.md`. Check the output path after the reviewer completes and move the file if needed.

---

## Genomes (`kbase_genomes`) Pitfalls

### UUID-Based Identifiers

All primary keys are CDM UUIDs. Use the `name` table to map between external gene IDs and CDM UUIDs.

### Billion-Row Junction Tables

Most junction tables have ~1 billion rows. Never query without filters.

---

## Python / Pandas Pitfalls

### [essential_genome] fillna(False) Produces Object Dtype, Breaking Boolean Operations

When using `merge(..., how='left')` to create a boolean flag column, the unmatched rows get `NaN`. Calling `.fillna(False)` converts the column to `object` dtype (mixed `True`/`False`/`NaN` → mixed `True`/`False`), NOT boolean. The `~` (bitwise NOT) operator on an `object` column produces silently wrong results instead of boolean negation.

```python
# BAD: creates object dtype, ~ gives garbage
df = left.merge(right_with_flag, how='left')
df['flag'] = df['flag'].fillna(False)
not_flagged = df[~df['flag']]  # WRONG — may include all rows

# GOOD: cast to bool after fillna
df['flag'] = df['flag'].fillna(False).astype(bool)
not_flagged = df[~df['flag']]  # Correct boolean negation
```

This caused an orphan essential gene count of 41,059 (total essentials) instead of 7,084 (actual orphans) — a silently incorrect result with no error message.

---

## Skill / Workflow Pitfalls

### [cofitness_coinheritance] Don't create data/results/ subdirectory

**Problem**: Computed results (phi coefficients, summary tables) were placed in `data/results/` instead of flat in `data/`. The BERIL pattern (per `PROJECT.md`) stores all data files flat in `data/`, with subdirectories only for extracted data categories (e.g., `data/cofit/`, `data/genome_cluster_matrices/`). A `data/results/` subdirectory is non-standard.

**Correct pattern**: Put computed outputs directly in `data/` alongside extracted data. Examples from other projects: `data/module_conservation.tsv`, `data/fitness_stats.tsv`, `data/essential_families.tsv`.

---

### [cofitness_coinheritance] Synthesize skill writes findings to README instead of REPORT.md

**Problem**: The `/synthesize` skill instructions say to update `README.md` with Key Findings, Interpretation, Literature Context, etc. But the observatory uses a **three-file structure**: README (concise overview with links), RESEARCH_PLAN (hypothesis/approach), REPORT (full findings/interpretation). The `essential_genome` project is the canonical example. Writing detailed findings into the README makes it too long and inconsistent with other projects.

**Correct workflow**:
1. `/synthesize` should produce **`REPORT.md`** with: Key Findings, Results, Interpretation, Literature Context, Limitations, Future Directions, Visualizations, Data Files
2. **`README.md`** should be a concise overview with a Status line, Overview paragraph, Quick Links section (linking to RESEARCH_PLAN, REPORT, references), and project metadata (Data Sources, Structure, Reproduction, Dependencies, Authors)
3. The README should link to REPORT.md: `See [REPORT.md](REPORT.md) for full findings and interpretation.`

**Action**: Update the synthesize skill's Step 7 to target REPORT.md instead of README.md, and add a step to update the README with a Status line and Quick Links.

---

### [submit] Codex CLI reviewer fails in sandbox with network disabled

**Problem**: Running `codex exec` from a restricted sandbox can fail with DNS/connection errors to the Codex backend (for example `chatgpt.com` resolution failures) because network egress is disabled in that environment.

**Solution**: Run the reviewer invocation with network-enabled permissions (outside the restricted sandbox) and confirm quickly with a minimal smoke test first, e.g. `codex exec "Reply with exactly: ok"`. If the smoke test works, rerun the full reviewer command.

---

### [submit] Inlining very large reviewer prompts reduces Codex CLI reliability

**Problem**: Passing a long system prompt inline (for example via large shell substitutions) can make `codex exec` runs unstable or fail intermittently.

**Solution**: Keep the CLI prompt compact and reference the on-disk prompt file in instructions (for example: "Read and follow `.claude/reviewer/SYSTEM_PROMPT.md`"), then write output to `projects/{id}/REVIEW.md`. This has been more reliable in BERIL submit workflows.

---

### [enigma_contamination_functional_potential] Copying strict features into relaxed mode invalidates sensitivity analysis

**Problem**: In NB02, setting `feats_relaxed = feats_strict.copy()` produces numerically identical strict/relaxed downstream outputs. This makes mapping-mode sensitivity conclusions invalid because the two modes are no longer independently constructed.

**Solution**: Compute strict and relaxed features independently. A scalable pattern is to precompute clade-level annotation counts once on the union of clades, then aggregate those counts separately per mode.

---

### [enigma_contamination_functional_potential] Aggregating annotations directly at genus level in both modes can be slow

**Problem**: Running separate heavy Spark joins/aggregations over `eggnog_mapper_annotations` for each mapping mode can stall notebook execution on large tables.

**Solution**: Precompute per-clade annotation totals once (`total_ann`, defense, mobilome, metabolism), then derive strict/relaxed genus-level feature fractions via pandas aggregation on the precomputed clade table. This preserves mode independence while reducing duplicate Spark work.

---

### [enigma_contamination_functional_potential] Species/strain bridge cannot be forced from genus-only ENIGMA taxonomy

**Problem**: ENIGMA taxonomy in `ddt_brick0000454` currently includes `Domain` through `Genus` levels only. Attempting species-level bridge logic directly will either fail or silently reuse genus-level mappings while appearing higher resolution.

**Solution**: Verify available taxonomy levels first. If species/strain labels are absent, either:
- use an explicit species-proxy mode (unique genus->single GTDB clade) and report mapped-coverage loss, or
- switch to data sources that support species/strain resolution (metagenomes, ASV reclassification pipeline).

---

### [enigma_contamination_functional_potential] FDR pass can silently miss p-value columns with non-standard names

**Problem**: If multiple-testing correction only targets columns ending in `_p`, it will miss p-value columns named like `adj_cov_p_contamination` or `adj_frac_p_contamination`.

**Solution**: Detect p-value columns by substring pattern (for example columns containing `_p` and excluding derived q-value columns) or by an explicit p-column allowlist before applying BH-FDR.

---

### [enigma_contamination_functional_potential] Bootstrap CI loops can become the runtime bottleneck in notebook models

**Problem**: Adding bootstrap confidence intervals for multiple outcomes and model families can make NB03 noticeably slower if bootstrap counts are set too high.

**Solution**: Use moderate bootstrap sizes (for example 250-400) with fixed seeds for reproducibility, and restrict CI estimation to key coefficients/endpoints. This keeps runtime practical while still giving uncertainty intervals for interpretation.

---

### [ecotype_env_reanalysis] Large species exceed Spark maxResultSize during gene cluster extraction

**Problem**: Extracting gene-cluster memberships for *K. pneumoniae* (250 genomes × ~5,500 genes per genome) via `gene` JOIN `gene_genecluster_junction` WHERE `genome_id IN (...)` exceeds Spark's `spark.driver.maxResultSize` (1GB default). The query succeeds in Spark but fails when collecting results to the driver node.

**Solution**: For species with >200 genomes, chunk the genome list into batches of 50-100 and concatenate results. Alternatively, increase `spark.driver.maxResultSize` in the Spark session config. The per-species extraction script should catch this error and continue to the next species (which it does via try/except).

### [ecotype_env_reanalysis] Broken symlinks to Mac paths cause silent failures on JupyterHub

**Problem**: The `ecotype_analysis/data` directory was a symlink pointing to `/Users/paramvirdehal/...` (a Mac path from local development). On JupyterHub, this path doesn't exist, so `os.makedirs(path, exist_ok=True)` throws `FileExistsError` (the symlink exists but its target doesn't). This is confusing because `exist_ok=True` is supposed to suppress the error.

**Solution**: Check for broken symlinks before creating directories. If the path exists as a symlink but the target is missing, remove the symlink first: `if os.path.islink(path): os.remove(path)`. Or avoid committing symlinks to git — use relative paths in code and `.gitignore` data directories.

---

### [env_embedding_explorer] Notebooks committed without outputs are useless for review

**Problem**: When analysis is prototyped as Python scripts (for debugging speed or iterative development), the notebooks get committed with empty output cells. This defeats their purpose — notebooks are the primary audit trail and methods documentation. The `/synthesize` skill reads notebook outputs to extract results, the `/submit` reviewer checks outputs to verify claims, and human readers rely on outputs to follow the analysis without re-running it. Empty notebooks fail all three use cases.

**Solution**: Always execute notebooks before committing, even if the analysis was originally run as a script. Use `jupyter nbconvert --to notebook --execute --inplace notebook.ipynb` or run Kernel → Restart & Run All in JupyterHub. If UMAP or other expensive steps were pre-computed, design the notebook to load cached results (check for file existence before recomputing). This way the notebook runs quickly and still captures all outputs.

---

### [env_embedding_explorer] AlphaEarth geographic signal is diluted by human-associated samples

**Problem**: The pooled geographic distance–embedding distance curve shows a 2.0x ratio (near vs far), but this blends two distinct populations. Environmental samples show 3.4x (strong signal) while human-associated samples show only 2.0x (weak signal). Using the pooled curve underestimates the true geographic signal in the embeddings.

**Solution**: Always stratify AlphaEarth analyses by environment category. At minimum, compute results separately for environmental vs human-associated samples. If using embeddings as environment proxies (e.g., ecotype analysis), consider excluding human-associated samples entirely.

### [env_embedding_explorer] AlphaEarth NaN embeddings — filter before analysis

**Problem**: 3,838 of 83,287 genomes (4.6%) have NaN in at least one of the 64 embedding dimensions. UMAP, cosine distance, and other operations will fail or produce NaN results silently.

**Solution**: Filter to `~df[EMB_COLS].isna().any(axis=1)` before any embedding-based computation. This reduces the dataset from 83,287 to 79,449 genomes.

### [env_embedding_explorer] UMAP with cosine metric is extremely slow for >50K points

**Problem**: Running `umap.UMAP(metric='cosine')` on 83K genomes with 64 dimensions took >60 minutes and did not complete on a single-CPU JupyterHub pod. The cosine metric requires pairwise precomputation which is O(n^2).

**Solution**: L2-normalize the embeddings first, then use `metric='euclidean'`. For L2-normalized vectors, Euclidean distance is monotonically related to cosine distance (`||a-b||^2 = 2(1-cos(a,b))`), so the UMAP topology is equivalent. Additionally, fit UMAP on a 20K subsample (`reducer.fit(subsample)`) then transform the full dataset (`reducer.transform(all_data)`) — this reduced runtime from >60 min to ~7 min.

### [env_embedding_explorer] kaleido v1 requires Chrome — use v0.2.1 on headless pods

**Problem**: kaleido 1.x (the plotly static image export library) requires Google Chrome installed, which isn't available on headless JupyterHub pods. `fig.write_image()` fails with `ChromeNotFoundError`.

**Solution**: Install kaleido 0.2.1 instead: `pip install kaleido==0.2.1`. This older version uses its own bundled Chromium and works on headless systems. The deprecation warning can be ignored.

---

### [pangenome_pathway_geography] GapMind pathways have multiple rows per genome-pathway pair

**Problem**: The initial analysis counted exactly 80 pathways for every species with 0% present because it looked for `score_category = 'present'` which doesn't exist. The root cause: GapMind has exactly 80 pathways total, and each genome-pathway pair has MULTIPLE rows (one per step/component in the pathway).

**Correct approach**: Take the BEST score for each genome-pathway pair before aggregating to species level:

```sql
WITH pathway_scores AS (
    SELECT
        clade_name,
        genome_id,
        pathway,
        CASE score_category
            WHEN 'complete' THEN 5
            WHEN 'likely_complete' THEN 4
            WHEN 'steps_missing_low' THEN 3
            WHEN 'steps_missing_medium' THEN 2
            WHEN 'not_present' THEN 1
            ELSE 0
        END as score_value
    FROM kbase_ke_pangenome.gapmind_pathways
),
best_scores AS (
    SELECT
        clade_name,
        genome_id,
        pathway,
        MAX(score_value) as best_score
    FROM pathway_scores
    GROUP BY clade_name, genome_id, pathway
)
-- Then aggregate to species level
SELECT
    clade_name,
    AVG(complete_pathways) as mean_complete_pathways,
    STDDEV(complete_pathways) as std_complete_pathways
FROM (
    SELECT clade_name, genome_id,
           SUM(CASE WHEN best_score >= 5 THEN 1 ELSE 0 END) as complete_pathways
    FROM best_scores
    GROUP BY clade_name, genome_id
)
GROUP BY clade_name
```

**Key insight**: GapMind score categories are: `complete`, `likely_complete`, `steps_missing_low`, `steps_missing_medium`, `not_present` (NOT a simple binary 'present' flag).

---

### [aromatic_catabolism_network] Keyword-based gene categorization is fragile — use co-fitness to validate

**Problem**: Categorizing genes by keyword matching on RAST function descriptions (e.g., `if 'protocatechuate' in func.lower()`) misclassifies enzymes with non-obvious names. ACIAD1710 (4-carboxymuconolactone decarboxylase, EC 4.1.1.44) is a core pca pathway enzyme but was classified as "Other" because the keyword list checked for "muconate" but not "muconolactone."

**Solution**: Use keyword-based categorization as an initial pass, then validate with co-fitness correlations. In this case, co-fitness analysis correctly recovered pcaC (r=0.978 with the Aromatic pathway). When writing keyword classifiers for gene functions, test them against known members of each category and add missing synonyms.

### [aromatic_catabolism_network] NotebookEdit can create invalid cells missing 'outputs' field

**Problem**: Using the `NotebookEdit` tool to replace a code cell's content can produce a cell without the required `outputs` and `execution_count` fields. `jupyter nbconvert --execute` then fails with `NotebookValidationError: 'outputs' is a required property`.

**Solution**: After using `NotebookEdit` on code cells, verify the notebook JSON is valid. Fix missing fields with:
```python
import json
with open('notebook.ipynb') as f:
    nb = json.load(f)
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        cell.setdefault('outputs', [])
        cell.setdefault('execution_count', None)
with open('notebook.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
```

### [aromatic_catabolism_network] Claude Code 2.1.47 Bash tool swallows output when waiting on `claude` subprocess

**Problem**: In Claude Code version 2.1.47, running `claude -p` as a foreground command (or backgrounded with `wait`) in the Bash tool causes ALL output to be suppressed — including `echo` statements that precede the `claude` invocation. The `claude -p` process runs and produces correct output, but the Bash tool discards it. This worked correctly in 2.1.45.

**Workaround**: Launch `claude -p` in the background with file redirection, return immediately, then read the output file in a separate Bash call:
```bash
env -u CLAUDECODE claude -p --no-session-persistence ... > /tmp/output.txt 2>&1 &
echo "PID=$!"
# In a separate Bash call:
cat /tmp/output.txt
```

Do NOT use `wait` on the PID — this triggers the same output suppression.

### [counter_ion_effects] NaCl-importance thresholds are sensitive to experiment count

**Problem**: Using `n_sick >= 1` (at least one NaCl experiment with fit < -1) as an NaCl-importance threshold is biased by the number of NaCl experiments per organism. *Synechococcus elongatus* (SynE) has 12 NaCl dose-response experiments (0.5–250 mM) and flags 32.6% of genes as NaCl-important — 3× higher than the next organism. This inflates cross-condition overlap statistics (SynE shows 88.6% metal–NaCl shared-stress).

**Solution**: When comparing gene-level importance across conditions with unequal experiment counts, either (a) require `n_sick >= 2` or use `mean_fit < threshold` instead of `n_sick >= 1`, or (b) report results with and without outlier organisms as a sensitivity check. Excluding SynE, overall metal–NaCl overlap drops from 39.8% to 36.7% — modest but worth documenting.

### [fw300_metabolic_consistency] BacDive utilization has four values, not two

**Problem**: BacDive `metabolite_utilization.utilization` stores four distinct values: `+` (can utilize), `-` (cannot utilize), `produced` (organism produces it), and `+/-` (variable/ambiguous). Treating this as a binary +/- field inflates counts: for *P. fluorescens*, indole has 60 "produced" entries and only 1 actual utilization test. Computing `pct_positive` from raw +/- counts without excluding `produced` and `+/-` entries gives incorrect species-level utilization rates.

**Solution**: Filter to explicit +/- tests before computing utilization percentages:
```python
n_tested = (utilization == '+').sum() + (utilization == '-').sum()
pct_positive = (utilization == '+').sum() / n_tested  # exclude 'produced' and '+/-'
```
Track all four categories separately (`n_positive`, `n_negative`, `n_produced`, `n_ambiguous`) for full transparency.

### [fw300_metabolic_consistency] GapMind genome IDs lack the RS_/GB_ prefix used in pangenome tables

**Problem**: The `kbase_ke_pangenome.gapmind_pathways` table stores genome IDs without the GTDB `RS_` or `GB_` prefix (e.g., `GCF_001307155.1`), while the pangenome `genome` table uses the prefixed form (`RS_GCF_001307155.1`). A direct equality match between a pangenome genome_id and GapMind genome_id returns zero rows.

**Solution**: Strip the `RS_` or `GB_` prefix before matching, or use a fallback chain:
```python
# Try original ID first, then stripped, then partial match
gapmind_match = df[df['genome_id'] == pangenome_id]
if len(gapmind_match) == 0:
    alt_id = pangenome_id.replace('RS_', '').replace('GB_', '')
    gapmind_match = df[df['genome_id'] == alt_id]
if len(gapmind_match) == 0:
    accession = pangenome_id.split('_', 1)[-1]  # e.g., GCF_001307155.1
    gapmind_match = df[df['genome_id'].str.contains(accession)]
```

---

## NMDC (`nmdc_arkin`) Pitfalls

### [nmdc_community_metabolic_ecology] Classifier and metabolomics tables use `file_id`, not `sample_id`

**Problem**: `nmdc_arkin.metabolomics_gold`, `kraken_gold`, `centrifuge_gold`, and
`gottcha_gold` all use `file_id` and `file_name` as their primary identifier — not
`sample_id`. Queries with `WHERE sample_id = ...` or `COUNT(DISTINCT sample_id)` will throw
`AnalysisException: UNRESOLVED_COLUMN` and stop notebook execution.

**Solution**: Use `file_id` as the join key for all classifier and metabolomics tables.
```sql
-- WRONG
SELECT COUNT(DISTINCT sample_id) FROM nmdc_arkin.metabolomics_gold

-- CORRECT
SELECT COUNT(DISTINCT file_id) FROM nmdc_arkin.metabolomics_gold
```

### [nmdc_community_metabolic_ecology] `taxonomy_features` is a wide-format matrix with numeric column names

**Problem**: `nmdc_arkin.taxonomy_features` does not have a `sample_id` or `file_id` column.
Its columns are numeric NCBI taxon IDs (e.g., `7`, `11`, `33`, `34`, ...). Attempting to
`SELECT sample_id FROM taxonomy_features` fails immediately. The table is a pivoted matrix
where rows are likely samples and columns are taxon abundances.

**Solution**: Do not use `taxonomy_features` for tidy-format joins. Use the classifier tables
(`kraken_gold`, `centrifuge_gold`, `gottcha_gold`) instead — they are tidy format with
`file_id`, `rank`, `name`/`label`, and `abundance` columns. Count rows with
`SELECT COUNT(*) FROM nmdc_arkin.taxonomy_features` to verify the row count matches the
expected number of samples.

### [nmdc_community_metabolic_ecology] Confirmed `metabolomics_gold` compound annotation columns

The `metabolomics_gold` table has: `kegg` (string — KEGG compound ID), `chebi` (double —
ChEBI ID), `name` (string — compound name), `inchi`, `inchikey`, `smiles`. Use backtick
quoting for column names with spaces (e.g., `` `Molecular Formula` ``, `` `Area` ``).
The `annotation_terms_unified` table is a gene-annotation lookup (COG/EC/GO/KEGG terms) and
**cannot** be used as a metabolite compound lookup.

### [nmdc_community_metabolic_ecology] Classifier and metabolomics `file_id` namespaces do not overlap — must bridge through `sample_id`

**Problem**: Joining `nmdc_arkin.centrifuge_gold` (or `kraken_gold`, `gottcha_gold`) directly
to `nmdc_arkin.metabolomics_gold` on `file_id` always returns **zero rows**. The two table
sets use non-overlapping `file_id` prefixes:
- Classifier files: `nmdc:dobj-11-*` (metagenomics workflow outputs)
- Metabolomics files: `nmdc:dobj-12-*` (metabolomics workflow outputs)

They are different workflow output types for the same biosample and are only linkable through
the **biosample `sample_id`** (e.g., `nmdc:bsm-11-*`).

**Solution**: Find a `file_id → sample_id` bridge table in `nmdc_arkin` before attempting
to link classifier and metabolomics data. The `abiotic_features` table uses `sample_id` as
its primary key; scan all tables in `nmdc_arkin` with `SHOW TABLES` + `DESCRIBE` to find
any table that has **both** `file_id` and `sample_id` columns. NB02 of
`nmdc_community_metabolic_ecology` does this scan systematically.

```python
# Scan all nmdc_arkin tables for file_id + sample_id
for tbl in all_tables:
    schema = spark.sql(f'DESCRIBE nmdc_arkin.{tbl}').toPandas()
    cols = set(schema['col_name'])
    if 'file_id' in cols and 'sample_id' in cols:
        print(f'Bridge candidate: {tbl}')
```

The bridge table is `nmdc_arkin.omics_files_table` (385,562 rows, confirmed). It has
`file_id`, `sample_id`, `study_id`, `workflow_type`, and `file_type` columns.

### [nmdc_community_metabolic_ecology] `spark.createDataFrame(pandas_df)` fails with `ChunkedArray` error after `.toPandas()` on Spark Connect

**Problem**: When a pandas DataFrame is produced by calling `.toPandas()` on a Spark Connect
DataFrame, its columns are backed by PyArrow `ChunkedArray` objects. Passing this DataFrame
back to `spark.createDataFrame()` raises:

```
TypeError: Cannot convert pyarrow.lib.ChunkedArray to pyarrow.lib.Array
```

This prevents the common pattern of "pull data to pandas, filter it, register as a Spark temp view."

**Solution**: Avoid the pandas→Spark roundtrip entirely. Instead, keep all filtering and joining
in Spark SQL using subqueries and the original table name. For bridge joins, use the full table
name directly in SQL rather than materializing the bridge to a temp view:

```python
# WRONG — fails with ChunkedArray error
bridge_df = spark.sql("SELECT file_id, sample_id FROM nmdc_arkin.omics_files_table").toPandas()
bridge_spark = spark.createDataFrame(bridge_df)  # TypeError

# CORRECT — join using the table name directly in SQL
clf_samples = spark.sql("""
    SELECT DISTINCT b.sample_id
    FROM (SELECT DISTINCT file_id FROM nmdc_arkin.centrifuge_gold) c
    JOIN nmdc_arkin.omics_files_table b ON c.file_id = b.file_id
""").toPandas()
```

If you must convert pandas back to Spark (small DataFrames only), convert columns to native
Python lists first: `df[col] = df[col].tolist()` for each column before calling
`spark.createDataFrame(df)`.

### [nmdc_community_metabolic_ecology] `abiotic_features` Column Names Use `_has_numeric_value` Suffix; No `water_content` Column

**Problem**: Most numeric columns in `nmdc_arkin.abiotic_features` use a `_has_numeric_value` suffix (e.g., `annotations_tot_org_carb_has_numeric_value`), but two columns do not: `annotations_ph` (no suffix) and depth/temp which do have the suffix. Using the bare name without the suffix raises `UNRESOLVED_COLUMN`.

Additionally, `annotations_water_content` does not exist. Use `annotations_diss_org_carb_has_numeric_value` and `annotations_conduc_has_numeric_value` instead.

**Columns are already `double` type** — no `CAST` needed, but harmless if included.

**All-zero values mean missing**: the table stores `0.0` for unmeasured variables rather than `NULL`. Replace zeros with `NaN` before analysis:
```python
for col in abiotic_num_cols:
    abiotic[col] = abiotic[col].replace(0.0, np.nan)
```

**Correct column reference**:
```sql
-- WRONG
a.annotations_tot_org_carb, a.annotations_tot_nitro_content, a.annotations_water_content

-- CORRECT
a.annotations_tot_org_carb_has_numeric_value,
a.annotations_tot_nitro_content_has_numeric_value,
a.annotations_diss_org_carb_has_numeric_value,   -- dissolved organic carbon proxy
a.annotations_conduc_has_numeric_value            -- conductance (replaces water_content)
```

Full column list: `sample_id`, `annotations_ph`, `annotations_temp_has_numeric_value`, `annotations_depth_has_numeric_value`, `annotations_depth_has_maximum_numeric_value`, `annotations_depth_has_minimum_numeric_value`, `annotations_tot_org_carb_has_numeric_value`, `annotations_tot_nitro_content_has_numeric_value`, `annotations_diss_org_carb_has_numeric_value`, `annotations_conduc_has_numeric_value`, `annotations_diss_oxygen_has_numeric_value`, `annotations_ammonium_has_numeric_value`, `annotations_tot_phosp_has_numeric_value`, `annotations_soluble_react_phosp_has_numeric_value`, `annotations_carb_nitro_ratio_has_numeric_value`, `annotations_chlorophyll_has_numeric_value`, `annotations_calcium_has_numeric_value`, `annotations_magnesium_has_numeric_value`, `annotations_potassium_has_numeric_value`, `annotations_manganese_has_numeric_value`, `annotations_samp_size_has_numeric_value`.

---

## Quick Checklist

Before running a query, verify:

- [ ] Using exact equality instead of LIKE patterns for performance
- [ ] Large tables have appropriate filters (genome_id, species_id, orgId)
- [ ] JOIN keys are correct (gene_cluster_id for pangenome annotations, locusId for fitness)
- [ ] Numeric comparisons use CAST for string-typed databases
- [ ] You're not comparing gene clusters across species (pangenome)
- [ ] Expected tables actually exist (check [schemas/](schemas/))
- [ ] Data coverage is sufficient for your analysis
- [ ] Using REST API only for simple queries; Spark SQL for complex ones
