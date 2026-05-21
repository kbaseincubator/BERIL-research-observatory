# Performance Notes — cazyme_pangenome_ecology

<!-- [cazyme_pangenome_ecology] 2026-05-21T23:00:00Z  approved-report extraction (REVIEW: REVIEW_2.md) -->

- `kescience_mgnify.genome_cazy` is a small table (~345K rows) that joins cleanly to `kescience_mgnify.genome` on `genome_id`; no performance issues.
- Pivoting 49K genomes × 7 CAZy classes to wide format completes in seconds with pandas — no Spark needed for the pivot step.
- `kescience_mgnify.pangenome_stats` is pre-computed; no need to aggregate from per-gene tables.
