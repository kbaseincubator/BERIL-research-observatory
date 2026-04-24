# Plant Microbiome Ecotypes

Compartment-specific functional guilds and their genetic architecture in plant-associated microbiomes.

## Research Question

What is the genomic basis for plant-microbe associations across different plant compartments (rhizosphere, root, phyllosphere, endophyte)? Can we classify plant-associated microbial genera into beneficial, neutral, pathogenic, and dual-nature cohorts with mechanistic hypotheses, and identify which plant-interaction functions are associated with horizontal gene transfer vs. stable vertical inheritance?

## Overview

This project classifies 293K bacterial/archaeal genomes across 27.7K species by plant compartment association (rhizosphere, root, phyllosphere, endophyte) and characterizes the genomic basis of plant-microbe interactions. Species are classified into beneficial (PGP), pathogenic, dual-nature, and neutral cohorts based on marker gene profiles, with analysis of genomic architecture (core vs. accessory), metabolic complementarity, and horizontal gene transfer signatures.

## Hypotheses

| ID | Hypothesis | Notebook |
|----|-----------|----------|
| H0 | Phylogenetic null — functional differences explained by phylogeny alone | All (genus-level fixed effects) |
| H1 | Compartment specificity — distinct functional profiles per plant compartment | NB04 |
| H2 | Beneficial genes are core, pathogenic genes are accessory | NB05 |
| H3 | Co-occurring genera show metabolic complementarity | NB06 |
| H4 | Compartment-adaptation genes show HGT signatures | NB05 |
| H5 | Novel gene families distinguish plant-associated species | NB03 |

## Notebooks

| Notebook | Title | Compute | Description |
|----------|-------|---------|-------------|
| NB01 | Genome Census | Spark | Classify genomes by plant compartment; go/no-go checkpoint |
| NB02 | Marker Gene Survey | Spark | Search for PGP, pathogenicity, and colonization markers; classify species into cohorts |
| NB03 | Enrichment Analysis | Spark + local | Genome-wide eggNOG OG enrichment; volcano plot; phylogenetic control |
| NB04 | Compartment Profiling | Spark + local | Per-compartment functional signatures; GapMind pathways; PERMANOVA |
| NB05 | Genomic Architecture | Spark + local | Core/accessory distribution (H2); mobility proxies (H4) |
| NB06 | Complementarity | Spark + local | NMDC co-occurrence; GapMind gap-filling; PGP-pathogen interactions |
| NB07 | Cohort Synthesis | Local | Composite scoring; genus dossiers; hypothesis summary |
| NB08 | Adversarial Revisions | Spark + local | Sensitivity analyses, negative controls, HGT deep dive, predictive classifiers |

## Key Outputs

| File | Description |
|------|-------------|
| `data/species_compartment.csv` | Species-level plant compartment assignments |
| `data/species_marker_matrix.csv` | Species × marker function presence/absence |
| `data/species_cohort_markers.csv` | PGP/pathogen/dual-nature/neutral cohort assignments |
| `data/enrichment_results.csv` | OG-level enrichment in plant-associated species |
| `data/novel_plant_markers.csv` | Novel gene families enriched in plant species |
| `data/compartment_profiles.csv` | Per-compartment marker enrichment results |
| `data/genomic_architecture.csv` | Core/accessory/singleton statistics by marker type |
| `data/complementarity_network.csv` | Genus-pair metabolic complementarity scores |
| `data/cohort_assignments.csv` | Final composite cohort assignments |
| `data/genus_dossiers.csv` | Detailed profiles for top 20-30 genera |

## Status

Complete — see [Report](REPORT.md) for findings.

## Data Collections

This project uses data from the following BERDL collections:
- `kbase_ke_pangenome` — 293K genomes, pangenome gene clusters, bakta/eggNOG/GapMind annotations
- `kescience_bacdive` — BacDive strain isolation sources and metabolic phenotypes
- `nmdc_arkin` — NMDC community ecology taxonomy features

## Running

Notebooks require the BERDL JupyterHub environment with Spark access. Run in order (NB01-NB07); each notebook caches intermediate results to CSV so individual notebooks can be re-run independently after first execution.

## Prior Work Reused

- `pgp_pangenome_ecology`: Environment classification regex, PGP gene queries
- `nmdc_community_metabolic_ecology`: NMDC taxonomy bridge, GapMind community aggregation
- `phb_granule_ecology`: Environment harmonization patterns
- `prophage_ecology`: eggNOG-based mobile element proxy methodology

## Reproduction

1. Ensure access to the BERDL JupyterHub environment with Spark
2. Install dependencies: `pip install -r requirements.txt`
3. Run notebooks in order: NB01 through NB08
4. Each notebook caches intermediate results to `data/`; re-running individual notebooks after first execution is safe
5. NB08 (adversarial revisions) is optional but recommended for reproducing sensitivity analyses

## Authors

- Adam P. Arkin (ORCID: 0000-0002-4999-2931) — U.C. Berkeley / Lawrence Berkeley National Laboratory
