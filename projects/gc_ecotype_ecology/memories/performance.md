# Performance Notes — gc_ecotype_ecology

<!-- [gc_ecotype_ecology] 2026-05-27T17:23:33Z  approved-report extraction (REVIEW: REVIEW_2.md) -->

- `genome_ani` IN-clause queries scale to ~5,000 genomes per species without trouble on the JupyterHub Spark Connect kernel. Per-species ANI pull ran in seconds for typical species (50–500 genomes), seconds-to-a-minute for the largest (Staph aureus subsample at 5,000 genomes).
- Pulling all of `alphaearth_embeddings_all_years` into pandas (83K genomes × 65 columns) finished in under a minute.
- `df.to_parquet` on a Spark-Connect-derived pandas DataFrame fails with `TypeError: Object of type PlanMetrics is not JSON serializable`. Workaround: rebuild the frame as `pd.DataFrame({c: df[c].to_numpy() for c in df.columns})` to strip the Spark-side metadata before pyarrow serialization.
