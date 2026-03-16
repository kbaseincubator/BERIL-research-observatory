# Pan-Bacterial AMR Gene Landscape

## Research Question

What is the distribution, conservation, phylogenetic structure, functional context, and environmental association of antimicrobial resistance (AMR) genes across 27,000 bacterial species pangenomes?

## Status

Complete — see [Report](REPORT.md) for findings. All 7 notebooks executed with saved outputs.

## Overview

The BERDL pangenome collection contains AMRFinderPlus annotations (via Bakta v1.12.0) for 83,008 gene cluster representatives across 132M total clusters in 27,690 species. This project conducts the first comprehensive, pangenome-aware survey of AMR genes at this scale, examining:

1. **Conservation**: Are AMR genes core, accessory, or singleton? How does this compare to the genome-wide baseline?
2. **Phylogeny**: Which lineages are AMR hotspots? How does AMR density scale with pangenome size and openness?
3. **Mechanisms**: What resistance mechanisms dominate (efflux, target modification, enzymatic inactivation)? Which are universal vs lineage-restricted?
4. **Functional context**: What metabolic functions and COG categories co-occur with AMR genes?
5. **Environment**: Do host-associated and clinical isolates carry different AMR profiles than environmental ones?
6. **Annotation depth**: How many AMR clusters lack other functional annotations ("AMR-only" dark matter)?
7. **Fitness cost**: Do AMR genes impose measurable fitness costs in lab conditions?

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

- `kbase_ke_pangenome.bakta_amr` — 83K AMRFinderPlus hits on gene cluster representatives
- `kbase_ke_pangenome.gene_cluster` — 132M clusters with core/accessory/singleton flags
- `kbase_ke_pangenome.bakta_annotations` — 132M Bakta functional annotations
- `kbase_ke_pangenome.eggnog_mapper_annotations` — 93M eggNOG annotations
- `kbase_ke_pangenome.pangenome` — 27K species pangenome statistics
- `kbase_ke_pangenome.ncbi_env` — 4.1M environment metadata records
- `kescience_fitnessbrowser.genefitness` — 27M fitness scores for 48 organisms

## Reproduction

### Prerequisites
- Python 3.11+ with pandas, numpy, matplotlib, scipy, scikit-learn
- BERDL Spark session (JupyterHub or local proxy) for NB01, NB04, NB05, NB06
- `kbase_ke_pangenome` and `kescience_fitnessbrowser` database access

### Steps
1. Run `01_amr_census.ipynb` (Spark) — generates base data in `data/`
2. Run `02_conservation_patterns.ipynb` (local) — conservation deep-dive
3. Run `03_phylogenetic_distribution.ipynb` (local) — taxonomic analysis
4. Run `04_functional_context.ipynb` (Spark) — COG enrichment
5. Run `05_environmental_distribution.ipynb` (Spark) — environment + AlphaEarth
6. Run `06_fitness_crossref.ipynb` (Spark) — fitness cross-reference
7. Run `07_synthesis.ipynb` (local) — summary figures

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
