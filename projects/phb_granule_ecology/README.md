# Polyhydroxybutyrate Granule Formation Pathways: Distribution Across Clades and Environmental Selection

## Research Question

How are polyhydroxybutyrate (PHB) granule-forming pathways distributed across bacterial clades and environments, and does this distribution support the hypothesis that carbon storage granules are most beneficial in temporally variable feast/famine environments?

## Status

Complete — see [Report](REPORT.md) for findings. H1a (environmental enrichment) and H1b (niche breadth) supported; H1c (NMDC cross-validation) supported; H1d (subclade selection) partially supported.

## Overview

PHB is one of the most widely distributed carbon storage strategies in bacteria, yet systematic pan-bacterial surveys of its distribution across both phylogeny and environment are lacking. We use the BERDL pangenome (293K genomes, 27K species) to map PHB pathway completeness across the bacterial tree using eggNOG annotations (KEGG KOs, PFam domains), then correlate with environmental metadata (NCBI isolation source, AlphaEarth embeddings) and NMDC metagenomic data (abiotic features, taxonomic profiles). We test the classical feast/famine hypothesis: that PHB pathways are enriched in clades and environments with temporally variable carbon availability.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Data Sources

- `kbase_ke_pangenome` — 293K genomes, 27K species pangenomes with eggNOG functional annotations
- `kbase_ke_pangenome.alphaearth_embeddings_all_years` — 83K genomes with environmental embeddings
- `kbase_ke_pangenome.ncbi_env` — NCBI environment metadata
- `nmdc_arkin` — NMDC multi-omics with abiotic features, taxonomy profiles, and metabolomics

## Reproduction

**Prerequisites**: BERDL JupyterHub access with valid `KBASE_AUTH_TOKEN`.

```bash
# Install dependencies
pip install -r requirements.txt

# Run notebooks in order (requires Spark session on JupyterHub)
cd projects/phb_granule_ecology/notebooks
papermill 01_phb_gene_discovery.ipynb 01_phb_gene_discovery.ipynb -k python3
papermill 02_phylogenetic_mapping.ipynb 02_phylogenetic_mapping.ipynb -k python3
papermill 03_environmental_correlation.ipynb 03_environmental_correlation.ipynb -k python3
papermill 04_nmdc_metagenomic_analysis.ipynb 04_nmdc_metagenomic_analysis.ipynb -k python3
papermill 05_subclade_enrichment.ipynb 05_subclade_enrichment.ipynb -k python3
```

NB01b (`01b_fix_remaining_cells.ipynb`) is a patch notebook that completes cells from NB01 that errored on first run; it does not need to be re-run if NB01 completes successfully.

## Authors

- Adam Arkin (ORCID: 0000-0002-4999-2931), UC Berkeley / Lawrence Berkeley National Laboratory
