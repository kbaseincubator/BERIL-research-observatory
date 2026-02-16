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
df = spark.sql("SELECT * FROM kbase_ke_pangenome.pangenome LIMIT 10")

# WRONG: Don't try to import it — the module doesn't exist as a file
from get_spark_session import get_spark_session  # ImportError!
```

**Note**: The bare `get_spark_session()` (no import) only works inside notebook kernels. However, **[fitness_modules]** discovered that the underlying module IS importable from CLI:

```python
# WORKS from CLI (python3 scripts, not just notebooks)
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
```

This is injected by `/configs/ipython_startup/00-notebookutils.py` in notebooks, but the module itself is a regular Python package. This enables running full Spark analysis pipelines from the command line without `jupyter nbconvert`.

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
