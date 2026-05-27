# Pitfalls hit during gc_ecotype_ecology

## kbase_ke_pangenome.ncbi_env: value column is `content`, not `attribute_value` (2026-05-27)

`DESCRIBE kbase_ke_pangenome.ncbi_env` shows columns:
`accession, attribute_name, content, display_name, harmonized_name, id, package_content`.

The actual attribute value is in `content`. Naive guesses like `attribute_value` or `value` will fail with an unresolved-attribute error that surfaces as a long Spark stack trace with no obvious hint at the top. When pivoting `ncbi_env`, use:

```sql
SELECT accession, harmonized_name, content
FROM kbase_ke_pangenome.ncbi_env
WHERE harmonized_name IN ('isolation_source', 'host', ...)
  AND content IS NOT NULL AND content != ''
```

`docs/pitfalls.md` notes ncbi_env is EAV and to filter by `harmonized_name`, but does not name the value column — adding here for future projects.

## kbase_ke_pangenome.genome_ani: no species clade column; ANI is uppercase (2026-05-27)

`DESCRIBE` shows columns: `genome1_id, genome2_id, protocol_id, ANI, AF, AFMapped, AFTotal`. There is no `gtdb_species_clade_id` column. Documented as "within-species comparisons only" — so filtering by both `genome1_id IN (...)` and `genome2_id IN (...)` against a species-specific genome list is sufficient.

The ANI column is uppercase `ANI`, not `ani`. Spark Connect's case sensitivity sometimes accepts lowercase silently, sometimes not — always use `ANI`.

## CAST is needed for many "numeric" columns (2026-05-27)

`gtdb_metadata.gc_percentage`, `genome_size`, `checkm_completeness`, `checkm_contamination` are all `string`-typed. Always `CAST(... AS DOUBLE)` / `CAST(... AS BIGINT)` before numeric operations or comparisons.
