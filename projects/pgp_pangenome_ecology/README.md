# PGP Gene Distribution Across Environments & Pangenomes

## Research Question

Does environmental selection shape the distribution of plant growth-promoting (PGP) bacterial genes across the BERDL pangenome (293K genomes, 27K species), and are those genes core or accessory within their carrier species?

## Status

Complete — see [Report](REPORT.md) for findings.

## Overview

Plant growth-promoting bacteria (PGPB) carry suites of traits — nitrogen fixation (nifH), ACC deaminase (acdS), pyrroloquinoline quinone synthesis (pqqA-E), IAA biosynthesis (ipdC), and hydrogen cyanide production (hcnA-C) — that enhance plant fitness. Whether these traits co-occur non-randomly, accumulate in soil/rhizosphere niches, and spread by horizontal gene transfer (rather than vertical descent) are open questions at pangenome scale. Using 293K genomes across 27K species, we test four hypotheses: (H1) PGP traits form a non-random "PGP syndrome", (H2) rhizosphere/soil genomes are enriched for PGP genes, (H3) PGP genes are predominantly accessory (HGT-driven), and (H4) tryptophan biosynthesis completeness predicts ipdC presence.

**BERDL collections**: `kbase_ke_pangenome` (bakta_annotations, gene_cluster, pangenome, gtdb_metadata, genome, gtdb_taxonomy_r214v1, gapmind_pathways)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy
- [Report](REPORT.md) — findings, interpretation (populated after analysis)

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, scipy, matplotlib, seaborn, statsmodels, scikit-learn
- BERDL JupyterHub access (for NB01 Spark queries)

**Pipeline:**
1. Execute `notebooks/01_data_extraction.ipynb` — Spark queries for PGP genes, environment, taxonomy, pangenome stats, GapMind (~20 min)
2. Execute `notebooks/02_pgp_cooccurrence.ipynb` — H1: co-occurrence matrix and Fisher's exact tests (~5 min, local)
3. Execute `notebooks/03_environmental_selection.ipynb` — H2: environment enrichment + phylogenetic controls (~10 min, local)
4. Execute `notebooks/04_core_accessory_status.ipynb` — H3: core/accessory fractions + pangenome openness (~5 min, local)
5. Execute `notebooks/05_tryptophan_iaa.ipynb` — H4: trp completeness → ipdC logistic regression (~5 min, local)

## Authors

- **Priya Ranjan** (ORCID: [0000-0002-0357-1939](https://orcid.org/0000-0002-0357-1939)) — Oak Ridge National Laboratory
