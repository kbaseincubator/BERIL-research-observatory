# Performance Notes — metal_defense_vs_metabolism_classification

<!-- [metal_defense_vs_metabolism_classification] 2026-06-29T01:10:49Z  approved-report extraction (REVIEW: REVIEW_4.md) -->

- `spark.read.parquet(local_path)` fails when the local path is on the JupyterHub filesystem — remote Spark executors cannot access it. Fix: collect Spark results to pandas with `.toPandas()` then write with `pandas.to_parquet()`, and reload via `pd.read_parquet()` on subsequent cells. Cache-check pattern (`is_valid_parquet()`) before re-running expensive Spark queries is recommended for all notebooks in this collection.
- Joining `kbase.ke_pangenome.gene_cluster` to `gtdb_taxonomy_r214v1` requires bridging through `kbase.ke_pangenome.genome` — direct join on `species` vs `gtdb_species_clade_id` fails due to format mismatch (long format `s__Genus_species--RS_GCF_xxx` in gene_cluster vs short format `s__Genus_species` in taxonomy).