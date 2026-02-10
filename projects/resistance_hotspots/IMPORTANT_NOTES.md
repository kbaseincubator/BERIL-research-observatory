# Important Notes Before Running Notebooks

## ⭐ CRITICAL VALIDATION FINDINGS - READ THIS

✅ **Project queries have been TESTED against real BERDL API**
- See `BERDL_VALIDATION_REAL.md` for detailed execution results
- **⚠️ Confidence: 40%** (major issues found)

**CRITICAL FINDINGS**:
- ✅ Core tables exist (genome, pangenome)
- ✅ Can sample small data (LIMIT 5-100)
- ❌ Large table operations TIMEOUT after 55 seconds
- ❌ `eggnog_mapper_annotations` table inaccessible via REST API
- ❌ `orthogroup` table does not exist or times out
- ❌ COUNT(*) queries on billion-row tables DO NOT WORK

**IMPORTANT**:
- **Notebooks MUST run in BERDL JupyterHub Spark SQL environment**
- **NOT suitable for REST API queries from local scripts**
- Notebooks should be uploaded to JupyterHub and run there
- Spark SQL has better optimization for these large tables

---

## Critical Information for Phase Execution

### Data Structure Notes

1. **eggNOG Annotations Table** (For Phase 2: ARG Identification)
   - Location: `kbase_ke_pangenome.eggnog_mapper_annotations`
   - Contains functional annotations with COG, KEGG, GO, EC, and PFAM identifiers
   - Use this to identify potential ARGs via keyword matching on COG descriptions and KEGG pathways
   - The CARD and ResFinder databases should be downloaded externally and mapped via keyword matching

2. **Gene Table Structure** (For Phases 2-5)
   - Primary table: `kbase_ke_pangenome.gene`
   - Use `gene_cluster` table for orthogroup information
   - Join with `eggnog_mapper_annotations` using gene_id to access functional annotations

3. **Genome Relationships**
   - `genome` table is the central hub
   - Links to: `gtdb_species_clade`, `gtdb_taxonomy_r214v1`, `gtdb_metadata`, `ncbi_env`
   - Use `gtdb_species_clade_id` for species-level grouping

### Data Source Challenges

#### Phase 2: ARG Identification
- **Challenge**: BERDL doesn't include pre-computed ARG annotations
- **Solution**: Use keyword matching on:
  - COG functional category descriptions
  - KEGG pathway names and modules
  - Gene product names in `eggnog_mapper_annotations`
- **Limitation**: This will identify candidates, not definitive ARGs
- **Next step**: Consider downloading CARD JSON and doing homology matching if needed

#### Phase 5: Fitness Analysis
- **Challenge**: `kescience_fitnessbrowser` collection structure is not yet documented
- **Solution**: First explore this collection:
  ```sql
  SHOW TABLES IN kescience_fitnessbrowser;
  ```
- **Fallback**: If fitness data doesn't map cleanly to pangenome genes, this phase may be simplified or deferred

### Performance Considerations

1. **Large tables** - Some queries may be slow:
   - `gene` table: 1B+ rows
   - `genome_ani`: 421M rows
   - Use `LIMIT` during development

2. **JOIN operations** - Be mindful of:
   - Not all genes may have eggNOG annotations (~93.5B annotated out of 1B+)
   - Some genomes may lack environmental metadata
   - Use `DISTINCT` carefully (can be expensive on large tables)

3. **Spark optimization tips**:
   - Cache intermediate results: `df.cache()`
   - Use `repartition()` before large JOINs
   - Check execution plans with `.explain()`

### Implementation Notes

#### Recommended Approach for Phase 2 (ARG Identification)

```python
# Option A: Spark SQL approach (recommended for BERDL)
arg_query = """
SELECT DISTINCT
    g.gene_id,
    g.genome_id,
    e.cog_id,
    e.kegg_ko,
    e.kegg_pathways,
    e.product_name
FROM kbase_ke_pangenome.gene g
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations e
    ON g.gene_id = e.gene_id
WHERE LOWER(COALESCE(e.product_name, '')) LIKE '%resistance%'
    OR LOWER(COALESCE(e.product_name, '')) LIKE '%antibiotic%'
    OR LOWER(COALESCE(e.kegg_pathways, '')) LIKE '%resistance%'
"""

# Save to CSV or Parquet for Phase 3
df_args = spark.sql(arg_query)
df_args.write.mode("overwrite").csv("../data/arg_candidates.csv")
```

#### Recommended Approach for Phase 4 (Pangenome Analysis)

To identify core/accessory genes:
```python
# Count genome occurrences per orthogroup
ortho_prevalence = """
SELECT
    og.orthogroup_id,
    COUNT(DISTINCT g.genome_id) as n_genomes_with_gene,
    s.n_genomes_in_species,
    ROUND(100.0 * COUNT(DISTINCT g.genome_id) / s.n_genomes_in_species, 2) as prevalence_percent,
    CASE
        WHEN COUNT(DISTINCT g.genome_id) >= 0.95 * s.n_genomes_in_species THEN 'core'
        WHEN COUNT(DISTINCT g.genome_id) > 0 THEN 'accessory'
        ELSE 'absent'
    END as gene_category
FROM kbase_ke_pangenome.gene g
JOIN kbase_ke_pangenome.gene_cluster gc ON g.gene_id = gc.gene_id
JOIN kbase_ke_pangenome.orthogroup og ON gc.gene_cluster_id = og.gene_cluster_id
JOIN (
    SELECT gtdb_species_clade_id, COUNT(*) as n_genomes_in_species
    FROM kbase_ke_pangenome.genome
    GROUP BY gtdb_species_clade_id
) s ON g.gtdb_species_clade_id = s.gtdb_species_clade_id
GROUP BY og.orthogroup_id, s.n_genomes_in_species
"""
```

### File Organization Tips

1. **Intermediate data**: Save DataFrames as Parquet (more efficient than CSV)
   ```python
   df.write.mode("overwrite").parquet("../data/intermediate/my_data.parquet")
   ```

2. **Checkpointing**: For long queries, checkpoint intermediate results:
   ```python
   df.checkpoint()
   ```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Table not found" | Typo in collection/table name | Run `SHOW TABLES IN kbase_ke_pangenome` to verify |
| Memory errors | Loading entire large table into memory | Use Spark SQL directly, not `.collect()` on large tables |
| Slow JOINs | Missing partition info or unoptimized schema | Check table statistics: `ANALYZE TABLE ... COMPUTE STATISTICS` |
| Gene ID mismatches | Different ID formats across tables | Test joins on small samples first |

### Next Steps Before Running

1. **Verify access** - Run notebook 01 up to the database listing cell
2. **Check available tables** - Confirm all expected tables exist
3. **Test a simple query** - Run a count on `genome` table to verify connectivity
4. **Document findings** - Update this file with actual table structures found

---

## Session Management

- **Spark Session**: In BERDL JupyterHub, the session is pre-initialized. Don't need to create one.
- **DataFrame caching**: Call `.cache()` on intermediate results you'll reuse multiple times
- **Cleanup**: Call `spark.catalog.dropTempView(name)` if creating temporary views

## References

- [BERDL Documentation](https://hub.berdl.kbase.us)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [Schema Documentation](../../docs/schema.md)
