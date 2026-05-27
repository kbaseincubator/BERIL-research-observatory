# GC Content as an Ecological Signal Across Bacterial Ecotypes

## Research Question
Does within-species GC content vary systematically with environmental niche after controlling for phylogenetic distance?

## Status
Reviewed — REVIEW_2.md drafted; awaiting /submit.

## Headline Result
40 of 108 well-sampled bacterial species (37%) show within-species GC content variation significantly associated with isolation source after ANI-cluster phylogenetic control (FDR<0.05). 39/40 (98%) survive label-permutation null; 59% of jointly-testable species are independently confirmed by an AlphaEarth continuous environmental embeddings test. Effect sizes small (0.1–0.9% GC shifts) but reproducible across two orthogonal definitions of environment.

## Overview
This project tests whether bacterial genomes from distinct environmental niches show systematic GC content shifts within species, using pangenome-scale data across hundreds of species in BERDL. Prior work (ecotype_analysis) showed phylogeny dominates gene content similarity — this project asks the complementary question about nucleotide composition.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — TBD
- [Report](REPORT.md) — TBD

## Reproduction

Prerequisites:
- On the BERDL JupyterHub kernel (or `.venv-berdl` off-cluster with proxy chain up).
- `KBASE_AUTH_TOKEN` set in environment / `.env`.
- Python deps: `pyspark`, `berdl_notebook_utils`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `pyarrow`.

Run order:

```bash
python notebooks/01_master_table.py          # builds genome_gc_env.parquet (293K x 18)
python notebooks/02_across_species_gc.py     # cross-species sanity check
python notebooks/03_within_species_gc.py     # within-species categorical test
python notebooks/04_robustness_alphaearth.py # part A: permutation null
python notebooks/04b_alphaearth_only.py      # part B: AlphaEarth-PC test
python notebooks/05_final_figures.py         # final figures + summary table
```

Total runtime ≈ 30 min on BERDL JupyterHub. Outputs land in `data/` and `figures/`.

## Authors
- Justin Reese (https://orcid.org/0000-0002-2170-2250), LBL
