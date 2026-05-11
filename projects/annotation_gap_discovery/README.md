# Annotation-Gap Discovery via Phenotype-Fitness-Pangenome-Gapfilling Integration

## Research Question

Can we systematically identify and resolve metabolic annotation gaps in bacterial genomes by integrating experimental growth phenotypes, gene fitness data, metabolic model gapfilling, pangenome context, and sequence homology?

## Status

Complete — see [Report](REPORT.md) for findings. H1 supported: 47.8% of gapfilled reactions resolved via evidence triangulation (EC match + Bakta + BLAST homology + fitness + pangenome conservation).

## Overview

Genome-scale metabolic models built from automated annotation pipelines routinely require gapfilling to match observed growth phenotypes. Each gapfilled reaction represents an "annotation gap" — a metabolic function the organism performs but whose responsible gene remains unidentified. This project integrates five independent evidence types to resolve these gaps:

1. **ModelSEED/COBRApy** models identify which reactions are missing (gapfilling)
2. **GapMind** pathway predictions identify missing pathway steps independently
3. **Fitness Browser** RB-TnSeq data reveals which genes matter under each carbon source
4. **Pangenome** gene co-occurrence links candidates to known pathway genes
5. **DIAMOND BLAST** against exemplar sequences confirms sequence homology

By triangulating these evidence types, we assign confidence-scored gene-reaction links to previously orphan gapfilled reactions, improving metabolic model accuracy and reducing annotation debt.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Collections

- `kescience_fitnessbrowser` — 48 organisms, 27M fitness scores, carbon source RB-TnSeq experiments
- `kbase_ke_pangenome` — 293K genomes, 132M gene clusters, Bakta/eggNOG annotations, GapMind pathways
- `kbase_msd_biochemistry` — 56K reactions, 46K molecules (ModelSEED reference biochemistry)

## Reproduction

### Prerequisites
- Python 3.10+ with packages from `requirements.txt`
- BERDL JupyterHub access with `KBASE_AUTH_TOKEN` (for NB01-05)
- DIAMOND (`conda install -c bioconda diamond`) for NB06
- COBRApy + ModelSEEDpy for NB02/NB07

### Execution Order and Runtimes

Notebooks must run sequentially — each reads outputs from prior notebooks.

| Notebook | Requires | Runtime | Description |
|---|---|---|---|
| NB01 | Spark | ~15 min | Genome and carbon source selection |
| NB02 | Spark + ModelSEEDpy | ~2-4 hours | Model building, baseline FBA, gapfilling |
| NB03 | Spark | ~30 min | EC-based gene candidate identification |
| NB04 | Spark | ~20 min | GapMind decomposition, Bakta alternatives |
| NB05 | Spark | ~15 min | Pangenome conservation, fitness profiling |
| NB06 | Local (DIAMOND) | ~45 min | Swiss-Prot BLAST, evidence triangulation |
| NB07 | Local (COBRApy) | ~5 min | Validation, cross-validation, hypothesis test |
| NB08 | Local (matplotlib) | ~2 min | Publication figures and summary tables |

### Steps
1. On BERDL JupyterHub: run NB01 through NB05 in order
2. Download `data/` directory for local execution
3. Install DIAMOND: `conda install -c bioconda diamond`
4. Locally: run NB06 through NB08 in order

All notebooks are committed with saved outputs. Re-running regenerates figures and TSV files in `data/`. Full re-execution requires BERDL Spark access; read-only review is possible from saved outputs.

## Authors

- Janaka N. Edirisinghe (ORCID: [0000-0003-2493-234X](https://orcid.org/0000-0003-2493-234X)), Data Science and Learning Division, Argonne National Laboratory, Lemont, IL, 60439, USA
