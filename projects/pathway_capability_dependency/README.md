# Metabolic Capability vs Dependency

## Research Question

When a bacterium's genome encodes a complete biosynthetic or catabolic pathway, does the organism actually depend on it? Can we use fitness data to distinguish **active dependencies** from **latent capabilities** — and predict which pathways are candidates for evolutionary gene loss?

## Status

Complete — all 5 notebooks executed (2026-02-19). Key findings: 35.4% of classified pathways are Active Dependencies, variable pathways correlate with pangenome openness (rho=0.530 controlled), and condition-type analysis reveals all "Latent Capabilities" become important under stress/limitation.

## Overview

GapMind predicts metabolic pathway completeness for 293K bacterial genomes across 80 pathways (amino acid biosynthesis + carbon source utilization). But "complete" doesn't mean "needed." Using RB-TnSeq fitness data from the Fitness Browser (~34 organisms with pangenome links), we classify pathways into four categories: **Active Dependencies** (complete + fitness-important), **Latent Capabilities** (complete + fitness-neutral), **Incomplete but Important** (partial + fitness-important), and **Missing** (incomplete + unneeded). We then extend to all 27K pangenome species using gene conservation as a proxy for dependency, and define **metabolic ecotypes** from within-species pathway variation.

## Related Projects

This project builds on an extensive upstream analytical pipeline:

| Project | Relationship |
|---------|-------------|
| `metal_fitness_atlas` | **Primary methodological template** — same framework (fitness × conservation × BQH) applied to metal tolerance. Found 87.4% of metal-fitness genes are core (OR=2.08). |
| `essential_metabolome` | **Pilot study** — GapMind + essential genes for 7 FB organisms. Identified GapMind coverage gaps. |
| `conservation_vs_fitness` | **Infrastructure** — FB-pangenome link table (177K links), essential gene classification |
| `fitness_effects_conservation` | **Methodology** — fitness breadth predicts conservation better than magnitude |
| `core_gene_tradeoffs` | **Confounders** — lab fitness ≠ natural selection (28K costly-but-conserved genes) |
| `ecotype_analysis` | **Controls** — phylogeny dominates gene content (60.5% of species) |

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy, related projects
- [Report](REPORT.md) — findings, interpretation, supporting evidence (pending)

## Data Sources

- `kbase_ke_pangenome.gapmind_pathways` — 305M rows, 80 pathways, 293K genomes
- `kescience_fitnessbrowser.genefitness` — 27M fitness measurements, 48 organisms
- `kescience_fitnessbrowser.experiment` — 7.5K experiments with condition metadata (expGroup, condition_1)
- `kescience_fitnessbrowser.besthitkegg` + `keggmember` — KEGG KO annotations for FB genes
- `kescience_fitnessbrowser.seedannotation` — SEED subsystem annotations for FB genes

## Project Structure

```
pathway_capability_dependency/
  README.md
  RESEARCH_PLAN.md
  REPORT.md
  notebooks/
    01_data_extraction.ipynb        # Spark: extract GapMind, fitness, annotations
    02_tier1_pathway_classification.ipynb  # Classify pathways using fitness
    03_tier2_pathway_conservation.ipynb    # Pan-bacterial pathway conservation
    04_metabolic_ecotypes.ipynb     # Within-species pathway clustering
    05_synthesis.ipynb              # Summary figures and statistics
    run_nb01.py, run_nb01_remaining.py, run_nb01_final.py  # NB01 execution scripts
    run_nb02.py                     # NB02 execution (FB-native KEGG approach)
    run_nb03.py                     # NB03 execution
    run_nb04.py                     # NB04 execution
    run_nb05.py                     # NB05 synthesis execution
  data/                            # 19 CSV files (~3.9 GB total)
  figures/                         # 20 figures + summary statistics
```

## Reproduction

### Prerequisites
- Python 3.10+ with `.venv-berdl` environment (see `scripts/bootstrap_client.sh`)
- BERDL proxy chain for NB01 (SSH tunnels + pproxy; see `.claude/skills/berdl-query/references/proxy-setup.md`)
- NB02-NB05 run locally on pre-extracted CSV data

### Steps
1. **NB01** (requires BERDL): Extract data from Spark. Run the sequence:
   ```bash
   python notebooks/run_nb01.py           # Steps 1-7
   python notebooks/run_nb01_remaining.py  # Steps 8-10
   python notebooks/run_nb01_final.py      # Steps 9-10 (retry KEGG/essential genes)
   ```
2. **NB02** (local): `python notebooks/run_nb02.py`
3. **NB03** (local): `python notebooks/run_nb03.py`
4. **NB04** (local): `python notebooks/run_nb04.py`
5. **NB05** (local): `python notebooks/run_nb05.py`

NB02-NB05 depend only on NB01 CSV outputs; NB03 and NB04 are independent of NB02.

## Authors

- Dileep Kishore
- Paramvir Dehal
