# BERDL Database: Common Pitfalls & Gotchas

**Purpose**: Quick reference for avoiding common issues when querying BERDL databases.

See [collections.md](collections.md) for the full database inventory and [schemas/](schemas/) for per-collection documentation.

---

## General BERDL Pitfalls

### REST API Reliability

The REST API at `https://hub.berdl.kbase.us/apis/mcp/` can experience issues:

| Error | Meaning | Solution |
|-------|---------|----------|
| 504 Gateway Timeout | Query took too long | Simplify query, add filters, use direct Spark |
| 524 Origin Timeout | Server didn't respond | Retry after a few seconds |
| 503 "cannot schedule new futures after shutdown" | Spark executor restarting | Wait 30s, retry |
| Empty response | Query failed silently | Check query syntax |

**Rule of thumb**: Use the REST API for simple queries (<1M rows). Use direct Spark SQL on JupyterHub for anything complex.

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

### String-Typed Numeric Columns

Many databases store numeric values as strings. Always cast before comparisons:
```sql
-- WRONG: String comparison
WHERE fit < -2

-- CORRECT: Cast to numeric
WHERE CAST(fit AS FLOAT) < -2
```

This affects: `kescience_fitnessbrowser` (all columns), `kbase_genomes` (coordinates, lengths), and others.

---

## Pangenome (`kbase_ke_pangenome`) Pitfalls

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

### Using `get_spark_session()` on BERDL JupyterHub

`get_spark_session()` is a **built-in function** injected into the JupyterHub notebook kernel. No import is needed:

```python
# CORRECT: Call directly, no import
spark = get_spark_session()
df = spark.sql("SELECT * FROM kbase_ke_pangenome.pangenome LIMIT 10").toPandas()

# WRONG: Don't try to import it — the module doesn't exist as a file
from get_spark_session import get_spark_session  # ImportError!
```

**Note**: This function is only available inside JupyterHub notebook kernels. It does NOT work from the command line (`python3 -c "..."`) or from `jupyter nbconvert --execute`. For CLI execution, notebooks must be run via `jupyter nbconvert` which spawns a kernel that has `get_spark_session()` available.

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

The `fitbyexp_*` tables have non-standard schemas (experiment names as columns). Use for single-organism lookups only.

---

## Genomes (`kbase_genomes`) Pitfalls

### UUID-Based Identifiers

All primary keys are CDM UUIDs. Use the `name` table to map between external gene IDs and CDM UUIDs.

### Billion-Row Junction Tables

Most junction tables have ~1 billion rows. Never query without filters.

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
