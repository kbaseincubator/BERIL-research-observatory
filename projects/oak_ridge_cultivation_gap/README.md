# What Metabolic Functions Does the Cultured Collection Miss at Oak Ridge?

## Research Question

At the ENIGMA Oak Ridge Field Research Center, what metabolic functions does BERDL's cultured-isolate genome collection (3,110 genomes) systematically under-represent compared to 623 metagenome-assembled genomes recovered from the same site?

## Status

Complete — see [Report](REPORT.md) for findings. Analysis identifies a massive functional asymmetry (78% of KOs significantly biased) driven primarily by Patescibacteria dominance in the MAG cohort. Wood-Ljungdahl carbon fixation is the clearest cultivation gap; aerobic respiration and motility are the strongest enrichment signals.

## Overview

BERDL contains both cultured isolate genomes (ENIGMA Genome Depot, 3,110 genomes with rich KO/COG/Pfam annotations) and metagenome-assembled genomes (623 MAGs from 15 ORFRC wells) from the Oak Ridge subsurface. This project directly compares the functional gene content of these two collections to produce a per-function "cultivation-coverage" table — identifying which metabolic capabilities are well-represented by culture and which require MAG-based analysis.

The approach extends the porewater-bias diagnostic developed in `clay_confined_subsurface` to a contaminated basalt-hosted subsurface system, using a literature-grounded marker dictionary spanning anaerobic respiration, C/N cycling, metal resistance, mobile genetic elements, and CPR/DPANN-signature functions. The comparison framework is packaged as a reusable module for future BERDL projects.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

| Source | Genomes | Annotations |
|---|---|---|
| ENIGMA Genome Depot (`enigma_genome_depot_enigma`) | 3,110 cultured | KO (avg 2,046/genome), COG, Pfam, EC |
| ENIGMA CORAL MAGs (`enigma_coral.sdt_bin`) | 623 MAGs | Contig lists (assembly FASTAs inaccessible) |
| BERDL Pangenome — subsurface MAGs (`kbase_ke_pangenome`) | 2,279 MAGs | bakta KEGG KO annotations via `bakta_db_xrefs` |
| BERDL Pangenome — cross-validation (147 linked) | 147 ENIGMA isolates | eggNOG, GapMind, bakta |

## Reproduction

### Prerequisites
- Python 3.10+
- BERDL Spark access (JupyterHub for NB03)
- Packages: see `requirements.txt`

### Steps
1. Run `NB03` on JupyterHub (Spark) — extracts cultured genome KO profiles from ENIGMA Genome Depot
2. MAG KO profiles are pre-extracted from `kbase_ke_pangenome.bakta_db_xrefs` (cached in `data/mag_ko_profiles.tsv`)
3. Run `NB04-NB08` locally — statistical comparison, taxonomic analysis, cross-validation, synthesis

> **Note**: NB01 (MAG FASTA extraction) and NB02 (CTS bakta annotation) are superseded. The original design targeted CORAL ORFRC MAGs, but assembly FASTAs at `/h/jmc/data/` are not accessible from JupyterHub. The analysis pivoted to 2,279 subsurface MAGs from `kbase_ke_pangenome` with existing bakta KEGG annotations. See RESEARCH_PLAN.md v2 for details.

### Runtime
- NB03: ~15-30 min (Spark)
- NB04-08: ~1 hour total (local)

### Key Output Files
- `data/ko_cultivation_coverage_full.tsv` — per-KO statistical results (10,845 KOs)
- `data/marker_cultivation_coverage.tsv` — marker dictionary hypothesis test results
- `figures/volcano_cultivation_bias.png` — main result visualization
- `figures/synthesis_panel.png` — three-panel summary figure

## Related Projects

- [`clay_confined_subsurface`](../clay_confined_subsurface/) — porewater-bias framework and SR/IR marker dictionary
- [`lab_field_ecology`](../lab_field_ecology/) — Fitness Browser genera detected at Oak Ridge (14/26)
- [`bacillota_b_subsurface_accessory`](../bacillota_b_subsurface_accessory/) — Bacillota_B subsurface gene content + clay H3 IR correction
- [`metal_fitness_atlas`](../metal_fitness_atlas/) — pan-bacterial metal tolerance genomics

## Authors

Justin Reese (ORCID: [0000-0002-2170-2250](https://orcid.org/0000-0002-2170-2250)) — Lawrence Berkeley National Laboratory
