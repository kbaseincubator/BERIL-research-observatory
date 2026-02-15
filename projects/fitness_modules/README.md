# Pan-bacterial Fitness Modules via Independent Component Analysis

## Research Question

Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?

## Status

Completed — 1,116 stable modules across 32 organisms, 156 cross-organism families, 6,691 function predictions for hypothetical proteins.

## Overview

This project applies robust Independent Component Analysis (ICA) to gene-fitness matrices from the Fitness Browser, decomposing them into latent functional modules of co-regulated genes. Modules are aligned across 32 bacterial organisms using ortholog fingerprints to reveal conserved fitness regulons, and module membership is used to predict biological process context for unannotated genes. The approach complements sequence-based methods by capturing process-level co-regulation rather than specific molecular function.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) — Findings, interpretation, supporting evidence
- [Review](REVIEW.md) — Automated review (if submitted)

## Reproduction

**Prerequisites:**
- Python 3.10+
- `pip install -r requirements.txt`
- BERDL JupyterHub access (for NB01-02 only)

**Running the pipeline:**

1. **NB01-02** (JupyterHub): Extract data from Spark into `data/`. These notebooks require `get_spark_session()` which is only available on the BERDL JupyterHub. They produce cached CSV files in `data/matrices/`, `data/annotations/`, and `data/orthologs/`.

2. **NB03-07** (local): Run locally using cached data files. All notebooks check for existing output files and skip recomputation. To re-run from scratch, delete the cached files in `data/modules/`, `data/module_families/`, and `data/predictions/`.

```bash
cd projects/fitness_modules
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/03_ica_modules.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_module_annotation.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/05_cross_organism_alignment.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/06_function_prediction.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/07_benchmarking.ipynb
```

The benchmark can also be run standalone: `python src/run_benchmark.py`

**Note**: NB03 ICA computation takes 30-80 min per organism (30-50 FastICA runs each). With all 32 organisms cached, NB03 runs in ~1 min (PCA + summary only). NB05 ortholog fingerprinting takes ~1 min.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
