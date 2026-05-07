# What Metabolic Functions Does the Cultured Collection Miss at Oak Ridge?

## Research Question

At the ENIGMA Oak Ridge Field Research Center, what metabolic functions does BERDL's cultured-isolate genome collection (3,110 genomes) systematically under-represent compared to 623 metagenome-assembled genomes recovered from the same site?

## Status

In Progress — research plan created, awaiting analysis.

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
| ENIGMA CORAL MAGs (`enigma_coral.sdt_bin`) | 623 MAGs | Contigs only — annotated via bakta in NB02 |
| BERDL Pangenome (147 linked) | 147 ENIGMA isolates | eggNOG, GapMind, bakta (cross-validation) |

## Reproduction

### Prerequisites
- Python 3.10+
- BERDL Spark access (JupyterHub for NB01, NB03)
- CTS access (NB02 MAG annotation)
- Packages: see `requirements.txt`

### Steps
1. Run `NB01` on JupyterHub — extracts per-bin FASTAs from metagenome assemblies, runs CheckM2
2. Run `NB02` via CTS — bakta annotation of QC-filtered MAGs
3. Run `NB03` on JupyterHub — extracts cultured genome KO profiles from genome depot
4. Run `NB04-NB08` locally — statistical comparison, taxonomic analysis, validation, synthesis

### Runtime
- NB01: ~2-4 hours (FASTA extraction + CheckM2)
- NB02: ~6-12 hours (bakta on ~400-500 MAGs via CTS)
- NB03: ~15-30 min
- NB04-08: ~1 hour total

## Related Projects

- [`clay_confined_subsurface`](../clay_confined_subsurface/) — porewater-bias framework and SR/IR marker dictionary
- [`lab_field_ecology`](../lab_field_ecology/) — Fitness Browser genera detected at Oak Ridge (14/26)
- [`bacillota_b_subsurface_accessory`](../bacillota_b_subsurface_accessory/) — Bacillota_B subsurface gene content + clay H3 IR correction
- [`metal_fitness_atlas`](../metal_fitness_atlas/) — pan-bacterial metal tolerance genomics

## Authors

Justin Reese (ORCID: [0000-0002-2170-2250](https://orcid.org/0000-0002-2170-2250)) — Lawrence Berkeley National Laboratory
