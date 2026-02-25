# PaperBLAST Data Explorer

## Research Question
What does the `kescience_paperblast` collection contain, how current is it, and what are its coverage patterns across organisms, domains of life, and functional databases?

## Status
Complete — see [Report](REPORT.md) for findings.

## Overview
PaperBLAST (Price & Arkin, mSystems 2017) links protein sequences to scientific literature via text mining of PubMed Central. This project characterizes the BERDL-hosted copy: scale, taxonomic coverage, temporal currency, cross-database linkages, and limitations.

## Data Sources
- `kescience_paperblast` — all 14 tables (genepaper, gene, snippet, curatedgene, etc.)
- `kescience_fitnessbrowser` — for cross-referencing FB organism coverage (via VIMSS IDs)

## Quick Links
- [Report](REPORT.md) — findings and interpretation
- [Research Plan](RESEARCH_PLAN.md) — analysis plan and context
- [References](references.md) — cited literature
- [Notebooks](notebooks/) — exploratory analysis

## Reproduction

Notebooks must be run on the BERDL JupyterHub (requires `berdl_notebook_utils` for Spark access).

```
NB01 (database overview)
  └─► data/*.csv (organism counts, year distribution, papers per gene)
       └─► NB02 (coverage skew — reads NB01 outputs from data/)
            └─► figures/ (Lorenz curves, top-20 bacteria, etc.)

CTS Job c10c4a0f (MMseqs2 clustering, runs on remote compute)
  └─► data/clusters_{90,50,30}pct.tsv
       └─► NB03 (cluster analysis — reads TSVs locally, Spark for annotations)
            └─► figures/ (cluster size distributions, coverage landscape)
```

```bash
# NB01 and NB02 (require Spark)
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_paperblast_overview.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_coverage_skew.ipynb

# NB03 requires cluster TSVs in data/ — either from a prior CTS run
# or download from MinIO: mc cp berdl-minio/cts/io/psdehal/output/mmseqs_full/ ../data/
jupyter nbconvert --to notebook --execute --inplace 03_sequence_clustering.ipynb
```

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy
