# BERDL Database: Performance & Scale Guide

**Purpose**: Strategies for efficiently querying BERDL databases, especially billion-row tables.

The guidance below is primarily based on experience with `kbase_ke_pangenome` but applies to any large BERDL database. See [collections.md](collections.md) for the full database inventory.

---

## PySpark-First Development

**Avoid calling `.toPandas()` on intermediate or large results.** It pulls all data from the Spark cluster to the driver node, which is slow and can cause out-of-memory errors.

Instead, keep data as Spark DataFrames and use PySpark operations for filtering, joins, and aggregations. Only convert to pandas for final small results (plotting, CSV export, etc.).

```python
# BAD: Pull everything to driver, then filter in pandas
df = spark.sql("SELECT * FROM kbase_ke_pangenome.gene_cluster").toPandas()
core = df[df['is_core'] == 1]

# GOOD: Filter in Spark, only collect the small result
core = spark.sql("""
    SELECT * FROM kbase_ke_pangenome.gene_cluster
    WHERE is_core = 1
    AND gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
""")
# Work with the Spark DataFrame...
summary = core.groupBy("gtdb_species_clade_id").count()
# Only convert to pandas at the end for plotting
summary.toPandas().plot(kind='bar')
```

**When `.toPandas()` is appropriate:**
- Final aggregated results (hundreds/thousands of rows)
- Data needed for matplotlib/seaborn plotting
- Small lookup tables (e.g., `pangenome` at 27K rows)
- Exporting to CSV

**When to stay in Spark:**
- Filtering, joining, or aggregating large tables
- Any intermediate step in a multi-step pipeline
- Data that will be written back to parquet

---

## Pangenome Table Size Reference

| Table | Rows | Size Category | Default Query Strategy |
|-------|------|---------------|----------------------|
| `gene` | 1,011,650,903 | **HUGE** | Filter by `genome_id` |
| `gene_genecluster_junction` | 1,011,650,762 | **HUGE** | Filter by `gene_id` or `gene_cluster_id` |
| `genome_ani` | 421,218,641 | **HUGE** | Query one species at a time |
| `gapmind_pathways` | 305,471,280 | **LARGE** | Filter by `genome_id` or `pathway` |
| `gene_cluster` | 132,531,501 | **LARGE** | Filter by `gtdb_species_clade_id` |
| `eggnog_mapper_annotations` | 93,558,330 | **LARGE** | Filter by `query_name` (gene_cluster_id) |
| `ncbi_env` | 4,124,801 | Medium | Filter by `accession` |
| `genome` | 293,059 | Small | Safe to scan |
| `gtdb_metadata` | 293,059 | Small | Safe to scan |
| `gtdb_taxonomy_r214v1` | 293,059 | Small | Safe to scan |
| `sample` | 293,059 | Small | Safe to scan |
| `alphaearth_embeddings_all_years` | 83,287 | Small | Safe to scan |
| `gtdb_species_clade` | 27,690 | Small | Safe to scan |
| `pangenome` | 27,702 | Small | Safe to scan |

---

## Query Patterns

### Pattern 1: Single Query with IN Clause for Moderate Species Lists

**[cog_analysis]** For 10-100 species, a single query with IN clause outperforms sequential queries:

```python
# Get target species
species_list = ['s__Species1--RS_GCF_123', 's__Species2--RS_GCF_456', ...]  # 32 species

# Create IN clause
species_in_clause = "', '".join(species_list)

# Single query for all species
query = f"""
SELECT
    gc.gtdb_species_clade_id,
    gc.is_core,
    ann.COG_category,
    COUNT(*) as gene_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.gene_genecluster_junction j
    ON gc.gene_cluster_id = j.gene_cluster_id
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
    ON j.gene_id = ann.query_name
WHERE gc.gtdb_species_clade_id IN ('{species_in_clause}')
    AND ann.COG_category IS NOT NULL
GROUP BY gc.gtdb_species_clade_id, gc.is_core, ann.COG_category
"""

result_df = spark.sql(query)  # Keep as Spark DataFrame; call .toPandas() only for final plotting
```

**Performance**: For 32 species analyzing COG distributions:
- Sequential queries (96 queries × 3 gene classes): ~30 minutes
- Single IN clause query: ~6 minutes (5x speedup)

**Key insight**: Let Spark handle parallelization internally rather than doing sequential queries. The overhead of 96 separate query round-trips dominates execution time, not the data transfer.

**When to use**:
- 10-100 species in your analysis
- Each species has moderate data volume (<1M rows per species)
- Query involves JOINs or aggregations

**When NOT to use**:
- >100 species (IN clause becomes unwieldy)
- Species with >10K genomes each (use per-species iteration instead)

### Pattern 2: Per-Species Iteration (For Large Species or Many Species)

For very large species or >100 species total, iterate:

```python
# Get target species list
target_species = [row.gtdb_species_clade_id for row in spark.sql("""
    SELECT gtdb_species_clade_id
    FROM kbase_ke_pangenome.pangenome
    WHERE no_genomes >= 50
""").collect()]

# Process one species at a time
results = []
for species_id in target_species:
    # Use LIKE to avoid -- comment issue
    species_prefix = species_id.split('--')[0]

    df = spark.sql(f"""
        SELECT genome_id, COUNT(*) as n_genes
        FROM kbase_ke_pangenome.gene g
        JOIN kbase_ke_pangenome.genome gm ON g.genome_id = gm.genome_id
        WHERE gm.gtdb_species_clade_id LIKE '{species_prefix}%'
        GROUP BY genome_id
    """)

    # .toPandas() is fine here since we already aggregated to a small result per species
    pdf = df.toPandas()
    pdf['species'] = species_id
    results.append(pdf)

final = pd.concat(results)
```

### Pattern 2: Chunked Genome Queries

When you have a list of genome IDs, process in chunks:

```python
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

genome_ids = [...]  # Your list of genome IDs
CHUNK_SIZE = 500

all_results = []
for chunk in chunk_list(genome_ids, CHUNK_SIZE):
    genome_list = ','.join([f"'{g}'" for g in chunk])

    result = spark.sql(f"""
        SELECT * FROM kbase_ke_pangenome.gene
        WHERE genome_id IN ({genome_list})
    """)

    all_results.append(result)

# Union Spark DataFrames instead of concatenating pandas frames
from functools import reduce
final = reduce(lambda a, b: a.union(b), all_results)
# Only convert to pandas if you need local processing
# final_pd = final.toPandas()
```

### Pattern 3: Pagination for Large Results

```sql
-- First page
SELECT * FROM kbase_ke_pangenome.gene_cluster
WHERE gtdb_species_clade_id LIKE 's__Escherichia_coli%'
ORDER BY gene_cluster_id
LIMIT 10000 OFFSET 0

-- Second page
SELECT * FROM kbase_ke_pangenome.gene_cluster
WHERE gtdb_species_clade_id LIKE 's__Escherichia_coli%'
ORDER BY gene_cluster_id
LIMIT 10000 OFFSET 10000
```

**Important**: Always include `ORDER BY` for consistent pagination.

### Pattern 4: Aggregation Before Collection

Do all filtering, joins, and aggregations in Spark. Only call `.toPandas()` on the final, small result:

```python
# GOOD: Aggregate in Spark, collect small summary
summary = spark.sql("""
    SELECT
        gtdb_species_clade_id,
        COUNT(*) as n_clusters,
        SUM(CASE WHEN is_core = 1 THEN 1 ELSE 0 END) as n_core
    FROM kbase_ke_pangenome.gene_cluster
    GROUP BY gtdb_species_clade_id
""")

# Convert to pandas only for plotting or export (27K rows — fine)
summary_pd = summary.toPandas()

# BAD: Collect all 132M rows then aggregate in pandas
# all_clusters = spark.sql("SELECT * FROM gene_cluster").toPandas()  # DON'T DO THIS
```

---

## Recommended Batch Sizes

| Operation | Batch Size | Rationale |
|-----------|------------|-----------|
| ANI queries | 1 species | Species can have 10K+ genomes = 100M+ pairs |
| Gene queries | 100-500 genomes | ~3K genes/genome = 300K-1.5M rows |
| Gene cluster queries | 1 species | 5K-500K clusters per species |
| Annotation lookups | 10K cluster IDs | JOIN is fast with index |
| Pathway queries | 1K genomes | ~1K pathways/genome |

---

## Table-Specific Strategies

### `genome_ani` (421M rows)

ANI is stored as directional pairs within species. Always filter by species:

```python
# Get genomes for target species first
genomes = [row.genome_id for row in spark.sql("""
    SELECT genome_id FROM kbase_ke_pangenome.genome
    WHERE gtdb_species_clade_id LIKE 's__Klebsiella_pneumoniae%'
""").collect()]

genome_list = ','.join([f"'{g}'" for g in genomes])

# Query ANI only for those genomes — keep as Spark DataFrame
ani = spark.sql(f"""
    SELECT genome1_id, genome2_id, ANI, AF
    FROM kbase_ke_pangenome.genome_ani
    WHERE genome1_id IN ({genome_list})
      AND genome2_id IN ({genome_list})
""")
# .toPandas() only if species is small enough for local analysis
```

### `gene` and `gene_genecluster_junction` (1B+ rows)

Never query without a filter:

```python
# GOOD: Filter by genome
genes = spark.sql("""
    SELECT gene_id, genome_id
    FROM kbase_ke_pangenome.gene
    WHERE genome_id = 'RS_GCF_000005845.2'
""")

# GOOD: Filter by cluster
junction = spark.sql("""
    SELECT gene_id, gene_cluster_id
    FROM kbase_ke_pangenome.gene_genecluster_junction
    WHERE gene_cluster_id IN ('cluster1', 'cluster2', 'cluster3')
""")

# BAD: Full scan
# all_genes = spark.sql("SELECT * FROM kbase_ke_pangenome.gene")  # 1 BILLION ROWS!
```

### `gapmind_pathways` (305M rows)

Filter by genome or pathway:

```python
# Get pathways for specific genomes
pathways = spark.sql("""
    SELECT genome_id, pathway, score_category, score_simplified
    FROM kbase_ke_pangenome.gapmind_pathways
    WHERE genome_id IN ('GCF_000005845.2', 'GCF_000006765.1')
""")

# Get all genomes with a specific pathway
arginine = spark.sql("""
    SELECT genome_id, score, score_category
    FROM kbase_ke_pangenome.gapmind_pathways
    WHERE pathway = 'arginine'
      AND metabolic_category = 'amino_acid'
      AND score_simplified = 1
""")
```

---

## REST API vs Direct Spark

### REST API (`https://hub.berdl.kbase.us/apis/mcp/`)

**Good for:**
- Simple queries returning <1M rows
- Schema exploration (`/tables/list`, `/tables/schema`)
- Row counts (`/tables/count`)
- Quick samples (`/tables/sample`)

**Limitations:**
- 504 timeout on queries taking >60s
- No streaming for large results
- Transient 503 errors during cluster restarts

### Direct Spark SQL (JupyterHub)

**Required for:**
- JOINs across large tables
- Aggregations on billions of rows
- Results >1M rows
- Complex window functions
- Iterative analysis

```python
# On BERDL JupyterHub
from pyspark.sql import SparkSession
spark = get_spark_session()  # Cluster provides this

# Full Spark SQL capabilities
result = spark.sql("""
    SELECT
        g.gtdb_species_clade_id,
        AVG(m.checkm_completeness) as avg_completeness,
        COUNT(*) as n_genomes
    FROM kbase_ke_pangenome.genome g
    JOIN kbase_ke_pangenome.gtdb_metadata m ON g.genome_id = m.accession
    GROUP BY g.gtdb_species_clade_id
    HAVING COUNT(*) >= 10
""")

# Write to parquet for later use
result.write.parquet('/path/to/output/species_quality.parquet')
```

---

## Anti-Patterns to Avoid

### 1. Large IN Clauses

```python
# BAD: 10,000+ values in IN clause
genome_list = ','.join([f"'{g}'" for g in all_genomes])  # 10K+ items
query = f"SELECT * FROM gene WHERE genome_id IN ({genome_list})"

# GOOD: Use temporary table or iterate
spark.createDataFrame([(g,) for g in all_genomes], ['genome_id']).createOrReplaceTempView('target_genomes')
query = """
    SELECT g.* FROM kbase_ke_pangenome.gene g
    JOIN target_genomes t ON g.genome_id = t.genome_id
"""
```

### 2. Cross-Species Gene JOINs

```python
# BAD: JOIN across all species (billions of rows)
query = """
    SELECT * FROM kbase_ke_pangenome.gene g1
    JOIN kbase_ke_pangenome.gene g2 ON g1.gene_id = g2.gene_id
"""

# GOOD: Filter to specific species first
query = """
    SELECT * FROM kbase_ke_pangenome.gene g
    JOIN kbase_ke_pangenome.genome gm ON g.genome_id = gm.genome_id
    WHERE gm.gtdb_species_clade_id LIKE 's__Escherichia_coli%'
"""
```

### 3. Collecting Before Filtering

```python
# BAD: Collect all 132M rows, filter in pandas
df = spark.sql("SELECT * FROM kbase_ke_pangenome.gene_cluster").toPandas()
core_only = df[df['is_core'] == 1]

# GOOD: Filter in Spark, keep as Spark DataFrame
core_only = spark.sql("""
    SELECT * FROM kbase_ke_pangenome.gene_cluster
    WHERE is_core = 1
    AND gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
""")
# Only .toPandas() if the result is small enough for local processing
```

---

## Other Large Databases

### Fitness Browser (`kescience_fitnessbrowser`)

| Table | Rows | Strategy |
|-------|------|----------|
| `genefitness` | 27,410,721 | Filter by `orgId` |
| `cofit` | 13,656,145 | Filter by `orgId` and `locusId` |
| `ortholog` | ~1.15M (32 orgs) | Filter by `orgId1` and/or `orgId2` via IN clause |
| `genedomain` | millions | Filter by `orgId` |

### ICA Pipeline Performance (`fitness_modules`)

**[fitness_modules]** Robust ICA runtime scales with genes × experiments × components × runs:

| Organism | Genes | Experiments | Components | Runs | Time |
|----------|-------|-------------|------------|------|------|
| DvH | 2,741 | 757 | 80 | 50 | 82 min |
| Putida | 4,778 | 300 | 80 | 30 | 78 min |
| Methanococcus_S2 | 1,244 | 371 | 80 | 50 | 13 min |
| SynE | 1,899 | 129 | 41 | 30 | 3 min |
| Kang | 2,003 | 108 | 40 | 30 | 5 min |

**Key performance factors:**
- **Component/experiment ratio**: Keep ≤ 40%. Higher ratios cause FastICA convergence failures, and each failed run hits `max_iter` (very slow). SB2B (68 comp / 190 exps = 36%) took 25 min; dropping to 40% cap would have been fine.
- **Pairwise cosine matrix**: Size = (n_runs × n_components)². At 50 runs × 80 components = 4000 vectors → 16M entries, manageable. At 100 runs × 100 components = 10,000 vectors → 100M entries, very slow.
- **Practical limit**: Cap at 80 components, 30-50 runs. Total time for 32 organisms: ~4-5 hours.
- **Ortholog extraction**: 1.15M BBH pairs for 32 organisms takes ~2 minutes via Spark. The graph construction (networkx connected components) takes ~30 seconds.

### Genomes (`kbase_genomes`)

| Table | Rows | Strategy |
|-------|------|----------|
| `feature` | 1,011,650,903 | Filter by genome via junction tables |
| `encoded_feature` | 1,011,650,903 | Filter by genome via junction tables |
| `name` | 1,046,526,298 | Filter by `name` or `entity_id` |
| `protein` | 253,173,194 | Filter by `protein_id` |
| All junction tables | ~1B each | Always filter by one entity |

### Biochemistry (`kbase_msd_biochemistry`)

| Table | Rows | Strategy |
|-------|------|----------|
| `reaction_similarity` | 671M+ | Always filter by `reaction_id` |
| Other tables | <100K | Safe to scan |

---

## Performance Checklist

Before running a query:

- [ ] Is the target table >10M rows? If yes, add filters
- [ ] Am I using `LIMIT` for exploration queries?
- [ ] Am I keeping data as Spark DataFrames until the final step?
- [ ] Am I only calling `.toPandas()` on small, aggregated results?
- [ ] Am I aggregating in Spark before collecting?
- [ ] Am I iterating per-species/per-organism for cross-entity analysis?
- [ ] Am I using pagination for large result sets?
- [ ] For REST API: Is expected result <1M rows?
- [ ] For REST API: Is query simple (no complex JOINs)?
- [ ] Am I casting string columns to numeric types where needed?
