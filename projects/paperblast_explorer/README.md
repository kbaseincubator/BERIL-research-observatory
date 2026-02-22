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
- [Notebooks](notebooks/) — exploratory analysis

## Reproduction
```bash
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_paperblast_overview.ipynb
```
Requires BERDL Spark access (JupyterHub or proxy).

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy
- Aindrila Mukhopadhyay (https://orcid.org/0000-0002-6513-7425), Lawrence Berkeley National Laboratory, US Department of Energy
