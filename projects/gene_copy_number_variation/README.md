# Gene Copy Number Variation Across Pangenome Functional Categories

## Research Question
Beyond presence/absence, do adaptive vs housekeeping genes show different paralog copy number patterns within bacterial pangenomes?

## Status
Completed — adaptive gene clusters show 8.14× higher copy number variation than housekeeping clusters across 24 bacterial species / 5 phyla (paired Wilcoxon p = 5.96 × 10⁻⁸); effect concentrates in accessory clusters (adaptive-accessory 25× adaptive-core).

## Overview
Existing pangenome studies characterize genes as core vs accessory (present/absent), but ignore **copy number within a genome** — how many paralogs of a gene cluster does each genome carry? This project tests whether housekeeping genes (F = nucleotide metabolism, H = coenzyme metabolism) maintain fixed copy numbers while adaptive genes (L, V, M, K — mobile elements, defense, cell wall, transcription) tolerate variation.

**Result**: across 24 species / 5 phyla drawn from `kbase_ke_pangenome`, adaptive clusters show 8.14× higher species-level weighted multi-copy rate than housekeeping clusters (24/24 species direction-consistent, paired Wilcoxon p = 5.96 × 10⁻⁸). Effect concentrates in accessory clusters: adaptive-accessory (median 1.55%) is 25× adaptive-core (0.06%), while core clusters are near-uniformly single-copy regardless of function. This extends the dosage balance hypothesis to bacteria at pangenome scale and identifies accessory-adaptive clusters as the primary site of copy number variation.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence
- [Review 1](REVIEW_1.md) — first independent AI review (claude-sonnet-4-5); critical issues addressed
- [Review 2](REVIEW_2.md) — post-fix re-review (claude-sonnet-4-5); no critical/important issues remaining

## Data Sources

All data queried from `kbase_ke_pangenome` collection.

## Reproduction

### Prerequisites
- **Environment**: BERDL JupyterHub (in-cluster). Off-cluster runs require the `.venv-berdl` proxy chain (see repo root `scripts/bootstrap_client.sh`).
- **Auth**: `KBASE_AUTH_TOKEN` in `.env` at repo root.
- **Python packages**: `pip install -r requirements.txt` (pandas, numpy, scipy, matplotlib, statsmodels — versions pinned).
- **Compute**: Spark session via `berdl_notebook_utils.setup_spark_session.get_spark_session()`.

### Step-by-step

Total wall-clock ~90 min (dominated by the multi-species extraction).

1. **NB01 — Pilot exploration** (~10 min): `01_pilot_exploration.ipynb`. Extracts per-cluster per-genome copy counts for 5 pilot species. Writes `data/pilot_copy_numbers.csv` and `data/pilot_cog_stats.csv`.
2. **NB01b — Pilot with refined metrics** (~30 s, pandas-only): `01b_pilot_refined_metrics.ipynb`. Re-analyzes NB01 output with cluster-carrier-weighted metrics; runs the pre-registered pass/fail gates that authorized the scale-up. Writes `data/pilot_refined_metrics.csv`.
3. **NB02 — Manifest generation & concatenation** (~1 min for manifest + concat; the ~80-min extraction is externalized to `src/extract_multi_species.py`): `02_multi_species_scale.ipynb`. Cell 1 generates `data/species_manifest.csv` (52 candidates) and `data/species_manifest_25.csv` (24-species reduced manifest). **Between Cell 1 and Cell 2, run the extraction script** (Step 4). Cell 2 verifies `data/per_species/*.csv` are present (assertion). Cell 3 concatenates into `data/multi_species_copy_stats.csv`. The notebook is deliberately a thin manifest+concat wrapper: `jupyter nbconvert --execute` cannot reliably drive an ~80-min Spark loop (see `memories/pitfalls.md`), so the compute lives in a standalone resumable script and the notebook holds the audit trail.
4. **Extraction script** (~80 min, run externally between NB02 cell 1 and cell 2):
   ```bash
   python projects/gene_copy_number_variation/src/extract_multi_species.py \
       projects/gene_copy_number_variation/data/species_manifest_25.csv \
       projects/gene_copy_number_variation/data/per_species/
   ```
   Resumable — re-running skips any species whose CSV already exists.
5. **NB03 — Statistical analysis** (~30 s, pandas-only): `03_statistical_analysis.ipynb`. Reads `multi_species_copy_stats.csv`, runs the paired Wilcoxon primary test and 8 pairwise BH-FDR tests. Writes `data/species_class_rates.csv`, `data/statistical_tests.csv`, `figures/cog_species_rates.png`, `figures/class_vs_phylum.png`.
6. **NB04 — Core vs accessory interaction** (~30 s, pandas-only): `04_core_accessory_interaction.ipynb`. Reads `multi_species_copy_stats.csv`, runs 4 one-sided Wilcoxon tests on the 2×2 (class × core-status) design. Writes `data/core_accessory_stats.csv`, `figures/core_accessory_interaction.png`.

### Notes
- Only NB01 and the extraction script hit the Spark cluster; NB01b, NB02 (post-manifest), NB03, and NB04 are pandas-only and run in seconds.
- `data/per_species/*.csv` files are gitignored (large, regeneratable). They must exist before NB02 cell 2 will pass.
- Namespace: uses `kbase_ke_pangenome` (underscore form), correct for the current Delta-to-Iceberg migration state. Verify with `SHOW TABLES IN kbase_ke_pangenome` if re-running after a migration event.

## Authors
- Justin Reese (LBL, ORCID: 0000-0002-2170-2250)
