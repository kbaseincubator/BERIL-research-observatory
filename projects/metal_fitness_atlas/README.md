# Pan-Bacterial Metal Fitness Atlas

## Research Question
Across diverse bacteria subjected to genome-wide fitness profiling under metal stress, what is the genetic architecture of metal tolerance — is it encoded in the core or accessory genome, is it conserved across species, and can fitness-validated metal tolerance genes predict capabilities across the broader pangenome?

## Status
Completed — metal-important genes are 87.4% core (OR=2.08, p=4.3e-162), reversing the expected accessory enrichment. 1,182 conserved metal gene families identified across species, including 149 novel candidates. Pangenome-scale prediction across 27,702 species shows metal genes are broadly distributed, not concentrated in specialists. See [Report](REPORT.md) for full findings.

## Overview
The Fitness Browser contains 559 metal-related experiments across 31 organisms covering 14 metals (cobalt, nickel, copper, zinc, aluminum, iron, tungsten, molybdenum, chromium, uranium, selenium, manganese, mercury, cadmium). No published study has performed a systematic cross-species, genome-wide fitness comparison for metal tolerance. This project builds a "Metal Fitness Atlas" by: (1) extracting all metal-condition fitness data (383,349 gene x metal records), (2) mapping metal-important genes to pangenome conservation (core vs accessory) for 22 organisms with FB-pangenome links, (3) identifying 1,182 conserved metal fitness gene families across species via ortholog groups, and (4) validating a metal tolerance repertoire scoring approach. The project is framed around DOE critical minerals priorities — cobalt, nickel, manganese, chromium, aluminum, and tungsten are on the USGS critical minerals list.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- `kescience_fitnessbrowser` — RB-TnSeq fitness data (48 organisms, 27M fitness scores; 31 with metal experiments, 24 with fitness matrices)
- `kbase_ke_pangenome` — Species-level pangenomes (293K genomes, 132M gene clusters; 22 FB organisms with pangenome links)
- Prior project data: organism mapping, FB-pangenome links, ortholog groups, ICA modules

## Project Structure
```
notebooks/          — Analysis notebooks (01-07)
data/               — Extracted and processed data (11 CSV files)
figures/            — Publication-quality visualizations (9 PNGs)
```

## Reproduction

### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- Access to prior project cached data (see below)

### Prior Project Dependencies
This project reuses cached data from these completed projects (no re-execution needed):
- `projects/fitness_modules/data/matrices/` — fitness matrices for 32 organisms
- `projects/fitness_modules/data/modules/` — ICA module data for 27+ organisms
- `projects/fitness_modules/data/annotations/` — experiment metadata
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` — FB-to-pangenome gene links
- `projects/conservation_vs_fitness/data/organism_mapping.tsv` — organism-to-clade mapping
- `projects/essential_genome/data/all_ortholog_groups.csv` — cross-organism ortholog groups
- `projects/essential_genome/data/family_conservation.tsv` — pangenome conservation per family
- `projects/essential_genome/data/essential_families.tsv` — essentiality classification
- `projects/essential_genome/data/all_seed_annotations.tsv` — SEED functional annotations

### Running the Pipeline
All notebooks run locally (no Spark required):
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_metal_experiment_classification.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_metal_fitness_extraction.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_metal_conservation_analysis.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_cross_species_metal_families.ipynb
jupyter nbconvert --to notebook --execute --inplace 05_metal_responsive_modules.ipynb
jupyter nbconvert --to notebook --execute --inplace 06_pangenome_metal_prediction.ipynb  # REQUIRES BERDL JupyterHub + Spark
jupyter nbconvert --to notebook --execute --inplace 07_summary_figures.ipynb
```

Notebooks must run in order (NB02 depends on NB01, etc.). Full pipeline runs in under 5 minutes on a standard machine.

### Coverage Notes
- 31 of 48 FB organisms have metal experiments (remaining 17 have <100 total experiments and no cached data)
- 22 of 31 metal-tested organisms have FB-pangenome links (conservation analysis in NB03)
- 24 of 31 have fitness matrices (fitness extraction in NB02)
- NB06 (pangenome-scale prediction) requires BERDL JupyterHub with `get_spark_session()` — queries `gene_cluster` (132M rows) joined with `eggnog_mapper_annotations` (93M rows)

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
