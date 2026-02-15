# Conservation vs Fitness -- Linking FB Genes to Pangenome Clusters

## Research Question

Are essential genes preferentially conserved in the core genome, and what functional categories distinguish essential-core from essential-auxiliary genes?

## Status

Completed -- 177,863 gene-to-cluster links built; essential genes 86% core (OR=1.56) across 33 organisms.

## Overview

This project builds the bridge between the Fitness Browser (~221K genes, 48 bacteria) and the KBase pangenome (132.5M gene clusters). It maps FB genes to pangenome clusters via DIAMOND blastp, identifies putative essential genes (no viable transposon mutants), and tests whether essential genes are enriched in core clusters. It also profiles essential genes by conservation category, revealing that essential-core genes are enzyme-rich and well-annotated while essential-auxiliary genes are poorly characterized.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) -- Findings, interpretation, supporting evidence

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, matplotlib, scipy
- DIAMOND (v2.0+) for protein similarity search
- BERDL JupyterHub access (for data extraction scripts)

**Running the pipeline:**

1. **Data extraction** (Spark Connect): `python3 src/run_pipeline.py` (NB01+NB02 data)
2. **DIAMOND search** (local): `src/run_diamond.sh data/organism_mapping.tsv data/fb_fastas data/species_fastas data/diamond_hits`
3. **Link table + QC** (local): Execute `notebooks/03_build_link_table.ipynb`
4. **Essential gene extraction** (Spark Connect): `python3 src/extract_essential_genes.py` -- also generates `seed_hierarchy.tsv`
5. **Conservation analysis** (local): Execute `notebooks/04_essential_conservation.ipynb`

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
