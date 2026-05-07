# Annotation-Gap Discovery via Phenotype-Fitness-Pangenome-Gapfilling Integration

## Research Question

Can we systematically identify and resolve metabolic annotation gaps in bacterial genomes by integrating experimental growth phenotypes, gene fitness data, metabolic model gapfilling, pangenome context, and sequence homology?

## Status

In Progress — research plan created, awaiting analysis.

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

## Data Sources

- **Fitness Browser**: 48 organisms, 27M fitness scores, carbon source experiments
- **BacDive**: 988K metabolite utilization records (+/- growth calls)
- **GapMind**: Pathway completeness predictions for 293K genomes
- **ModelSEED Biochemistry**: 56K reactions, 46K molecules
- **Pangenome**: 293K genomes, 132M gene clusters with protein sequences
- **eggNOG/Bakta**: EC, KEGG, COG, UniRef annotations

## Reproduction

### Prerequisites
- Python 3.10+
- BERDL access with `KBASE_AUTH_TOKEN`
- Packages: `cobra`, `modelseedpy`, `diamond` (bioconda), plus standard scientific Python stack

### Steps
1. Install dependencies: `pip install -r requirements.txt` and `conda install -c bioconda diamond`
2. Run NB01-02 on BERDL JupyterHub (requires Spark)
3. Run NB03-08 locally or on JupyterHub

## Authors

- Janaka N. Edirisinghe (ORCID: [0000-0003-2493-234X](https://orcid.org/0000-0003-2493-234X)), Data Science and Learning Division, Argonne National Laboratory, Lemont, IL, 60439, USA
