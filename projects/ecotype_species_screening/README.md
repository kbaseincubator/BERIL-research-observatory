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

*TBD — add after analysis is complete.*

Prerequisites: Python 3.10+, `pip install -r requirements.txt`. NB01 requires BERDL JupyterHub. NB02–NB04 run locally.

## Authors

- **Mikaela Cashman** (Lawrence Berkeley National Laboratory) | ORCID: [0000-0003-0620-7830](https://orcid.org/0000-0003-0620-7830)
