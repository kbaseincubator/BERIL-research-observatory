# Project pitfalls: gene_copy_number_variation

## jupyter nbconvert --execute is fragile for long-running Spark work

**Problem**: `jupyter nbconvert --execute NB.ipynb` runs the notebook, but stdout is buffered until the entire run finishes — you cannot see progress. If the process is killed mid-run (OOM, Spark contention, background task timeout), the notebook file is not updated and any DataFrames materialized in memory are lost. The visible artifact of a mid-run failure is: notebook mtime unchanged, output CSVs partially written or absent, task output file empty.

**Observed**: NB02 (52-species extraction, ~2-4 min/species) was launched via `jupyter nbconvert --execute` in background. Task exited with code 0 after ~1.5 hr, but no artifacts appeared — the notebook file was never rewritten because the process was likely killed by Spark cluster contention when a second job started. Only the intermediate `species_manifest.csv` (written by cell 3 before the extraction loop began) survived.

**Fix**: For per-species iteration over billion-row joins, write a standalone Python script (`src/extract_*.py`) that:
1. Saves each species result to its own CSV immediately after computation
2. Skips species whose output file already exists (resumable)
3. Uses `print(..., flush=True)` for streaming progress
4. Is invoked directly with `python script.py args` in background — progress flows to the task output file line by line

The notebook then just concatenates the per-species files and does analysis.

**Applies to**: Any BERIL project doing per-species iteration with large joins (`gene`, `gene_genecluster_junction`, `gapmind_pathways`). The moment a single species takes >2 min, prefer script-based extraction over `nbconvert --execute`.
