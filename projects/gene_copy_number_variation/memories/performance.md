# Performance Notes — gene_copy_number_variation

<!-- [gene_copy_number_variation] 2026-07-08T10:27:42Z  approved-report extraction (REVIEW: REVIEW_2.md) -->

- **Per-species iteration on the 3-way join** (`gene × gene_genecluster_junction × gene_cluster`, ~1B rows each) took **140–290 s per species** on 50–250-genome species (median ~200 s). For a 24-species pilot this is ~80 min total; scaling to 100+ species should use CTS batch processing rather than a JupyterHub notebook loop.
- **`jupyter nbconvert --execute` is fragile for long-running Spark jobs.** A background nbconvert of the extraction loop died silently after ~1.5 hr with the notebook file unchanged and only the intermediate CSV written. Standalone `src/extract_multi_species.py` with per-species CSV output was resumable, streamed progress via `print(flush=True)`, and completed under the same wall-clock budget. Detailed pitfall memo in `memories/pitfalls.md`.
