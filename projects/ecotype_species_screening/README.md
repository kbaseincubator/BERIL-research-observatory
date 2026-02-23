# Ecotype Species Screening

## Research Question

Which bacterial species are the best candidates for ecotype analysis? Can we identify them systematically using phylogenetic branch length substructure (from single-copy core gene trees) and environmental diversity (from ENVO-harmonized NCBI BioSample metadata)?

## Status

Complete — see [Report](REPORT.md) for findings. Analysis produced top 50 ecotype candidate species scored across phylogenetic substructure, environmental diversity, and pangenome openness using `kbase_ke_pangenome` and `nmdc_ncbi_biosamples`.

## Overview

Prior ecotype analyses in this observatory (`ecotype_analysis`, `ecotype_env_reanalysis`) tested 172–224 species but selected them based on AlphaEarth embedding coverage rather than ecotype potential. This project takes a different approach: systematic *upstream screening* of all 338 species with phylogenetic tree data, scored across three independent dimensions — phylogenetic substructure (branch distance variance), environmental diversity (ENVO category entropy from `nmdc_ncbi_biosamples`), and pangenome openness. The output is a ranked candidate list that prioritizes species most likely to yield meaningful ecotype signal in future analyses.

Two new BERDL data elements not used in prior ecotype work:
1. `phylogenetic_tree_distance_pairs` — actual branch lengths from single-copy core gene trees (22.6M pairs across 338 species)
2. `nmdc_ncbi_biosamples.env_triads_flattened` — ENVO ontology-harmonized environmental categories per genome's BioSample

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, scoring dimensions, query strategy
- [Report](REPORT.md) — findings (after analysis)

## Data Sources

- `kbase_ke_pangenome`: `phylogenetic_tree_distance_pairs`, `phylogenetic_tree`, `pangenome`, `genome`, `sample`
- `nmdc_ncbi_biosamples`: `env_triads_flattened`, `biosamples_flattened`
- Cross-project: `projects/ecotype_analysis/data/ecotype_correlation_results.csv` (retrospective validation)

## Structure

```
notebooks/
  01_data_extraction.ipynb           — Extract phylo stats + biosample map (JupyterHub)
  01b_env_extraction_continuation.py — Env diversity continuation script (local Spark)
  02_composite_scoring.ipynb         — Merge, z-score, rank candidates; H1 + H3 (local)
  03_retrospective_validation.ipynb  — Validate vs prior ecotype_analysis results; H2 (local)
data/                                — Generated CSVs (8 files, 94K+ rows)
figures/                             — Candidate ranking plots, score distributions (4 figures)
```

## Reproduction

Prerequisites: Python 3.10+, BERDL access for NB01.

```bash
pip install -r requirements.txt
```

### Execution order

**Step 1 — Data extraction (requires BERDL JupyterHub):**
Upload `notebooks/01_data_extraction.ipynb` to your JupyterHub session at `https://hub.berdl.kbase.us`. Run all cells. Cells 1–9 extract phylogenetic stats, pangenome stats, and the genome→BioSample map. Cell 10 joins genomes to biosample accessions. Cells 11–12 query `nmdc_ncbi_biosamples.env_triads_flattened` to compute per-species ENVO category diversity.

**Step 1b — Env extraction continuation (local Spark Connect):**
If JupyterHub is not available or cells 10–12 need to be re-run locally, use `notebooks/01b_env_extraction_continuation.py`. This script requires the local Spark Connect proxy to be running (see `references/proxy-setup.md`). It reads `data/genome_biosample_map.csv` (produced by NB01 Cell 10) and writes `data/species_env_stats.csv` and `data/species_env_category_counts.csv`.

**Step 2 — Composite scoring (local):**
Run `notebooks/02_composite_scoring.ipynb` locally. Reads the four CSVs from Step 1 (`species_phylo_stats.csv`, `species_pangenome_stats.csv`, `species_env_stats.csv`) and the prior ecotype_analysis results. Produces `data/species_scored.csv` and three figures.

**Step 3 — Retrospective validation (local):**
Run `notebooks/03_retrospective_validation.ipynb` locally. Reads `data/species_scored.csv` and `../../ecotype_analysis/data/ecotype_correlation_results.csv`. Produces `data/top50_candidates_annotated.csv` and two figures.

### Output files

| Step | Outputs |
|------|---------|
| NB01 / 01b | `species_tree_list.csv`, `species_phylo_stats.csv`, `species_pangenome_stats.csv`, `genome_biosample_map.csv`, `species_env_stats.csv`, `species_env_category_counts.csv` |
| NB02 | `species_scored.csv`, `figures/h1_phylo_vs_env_scatter.png`, `figures/scoring_overview.png`, `figures/dimension_correlations.png` |
| NB03 | `top50_candidates_annotated.csv`, `figures/h2_retrospective_validation.png`, `figures/h2_composite_vs_rpartial.png` |

### Note on NB01 cell outputs
NB01 was executed remotely on BERDL JupyterHub via the Spark Connect interface. To reproduce cell outputs locally, the Spark Connect proxy must be active. The data outputs (`data/*.csv`) are committed to the repository and can be used directly to re-run NB02 and NB03 without re-running NB01.

## Authors

- **Mikaela Cashman** (Lawrence Berkeley National Laboratory) | ORCID: [0000-0003-0620-7830](https://orcid.org/0000-0003-0620-7830)
