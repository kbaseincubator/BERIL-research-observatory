# Lignin Enrichment and Ecological Memory in Microbial Communities

## Research Question
How does sequential enrichment on lignin, with or without labile carbon supplementation, shape bacterial and fungal community composition — and does enrichment history create ecological memory that influences subsequent community assembly?

## Status

Completed — Lignin enrichment drives near-complete bacterial community turnover, and enrichment history (Round 1 carbon source) explains more Round 2 community variance (58.9%) than current growth conditions (32.7%), demonstrating ecological memory in lignin-degrading microbial communities.

## Overview
This project analyzes 16S rRNA (bacteria) and ITS (fungi) amplicon sequencing data from a sequential enrichment experiment. A base microbial community was passaged through two rounds of growth on lignin as the primary carbon source, with or without labile carbon supplementation. The 7-group design (1 base + 2 Round 1 + 4 Round 2) enables testing whether prior carbon exposure history shapes how communities reassemble under new conditions — a test of ecological memory at the community level.

### Experimental Design

```
                        Base Community
                              |
                    ┌─────────┴─────────┐
                    │                   │
              Round 1: Lignin     Round 1: Lignin + Labile C
               (Group 2)              (Group 3)
                    │                   │
              ┌─────┴─────┐      ┌─────┴─────┐
              │           │      │           │
         R2: Lignin  R2: Lig+LC  R2: Lignin  R2: Lig+LC
         (Group 4)  (Group 6)  (Group 5)   (Group 7)
```

| Group | Description | Round 1 | Round 2 | Short label |
|-------|------------|---------|---------|-------------|
| 1 | Base community (unenriched) | — | — | Base |
| 2 | Base → Lignin | Lignin | — | L |
| 3 | Base → Lignin + Labile C | Lignin+LC | — | LC |
| 4 | Lignin → Lignin | Lignin | Lignin | L→L |
| 5 | Lignin+LC → Lignin | Lignin+LC | Lignin | LC→L |
| 6 | Lignin → Lignin + Labile C | Lignin | Lignin+LC | L→LC |
| 7 | Lignin+LC → Lignin + Labile C | Lignin+LC | Lignin+LC | LC→LC |

- 3 biological replicates per group (21 samples total)
- Both 16S and ITS sequenced per sample (42 sequencing libraries)

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, analysis strategy, pre-registered decisions
- [Plan Review](PLAN_REVIEW_1.md) — independent reviewer feedback (v1 → v2 revisions)
- [Report](REPORT.md) — full findings, interpretation, and supporting evidence
- [Review](REVIEW.md) — automated reviewer feedback

## Reproduction

### Prerequisites

- Python 3.10+
- [cutadapt](https://cutadapt.readthedocs.io/) (primer trimming)
- [fastp](https://github.com/OpenGene/fastp) (quality filtering)
- [vsearch](https://github.com/torognes/vsearch) (PE merging, OTU clustering, taxonomy)
- Python packages: see `requirements.txt`

Install bioinformatics tools via conda:
```bash
conda install -c bioconda cutadapt fastp vsearch
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Reference databases

Download and place in `data/ref_dbs/`:
- **SILVA 138.2 NR99** — 16S taxonomy (`silva_138.2_nr99.fasta.gz`, 510,495 sequences)
- **NCBI ITS_RefSeq_Fungi** — ITS taxonomy (19,375 sequences), formatted as a BLAST database

### Steps

1. **NB00_setup_and_qc.ipynb** — Install dependencies, inspect raw reads, run fastp QC, create sample manifest (~10 min)
2. **NB01_read_processing.ipynb** — Primer trimming, quality filtering, PE merging, OTU clustering at 97%, taxonomy assignment (~30 min)
3. **NB02_composition_overview.ipynb** — OTU filtering (prevalence >= 2, abundance >= 10), taxonomy bar plots, rarefaction curves (~5 min)
4. **NB03_alpha_diversity.ipynb** — Alpha diversity metrics and Kruskal-Wallis tests (~2 min)
5. **NB04_beta_diversity.ipynb** — PCoA ordination, 3-tier PERMANOVA, PERMDISP (~5 min)
6. **NB05_differential_abundance.ipynb** — CLR-transformed differential abundance for 5 planned contrasts (~5 min)
7. **NB06_ecological_memory.ipynb** — Between-group distances, convergence tests, OTU retention analysis (~2 min)

Notebooks NB02–NB06 read from processed data in `data/` and can be re-run without the bioinformatics tools (NB00–NB01 only).

## Authors
- Markus de Raad (LBNL) — ORCID: [0000-0001-8263-9198](https://orcid.org/0000-0001-8263-9198)
