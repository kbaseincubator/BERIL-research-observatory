# Metabolic Capability vs Dependency

## Research Question

Can we distinguish metabolic *capability* (genome predicts a complete pathway) from metabolic *dependency* (fitness data shows the pathway genes actually matter)? Do "latent capabilities" — pathways that are genomically present but experimentally dispensable — predict pangenome openness and evolutionary gene loss?

## Status
In Progress — research plan created, awaiting analysis.

## Overview

This project bridges two major BERDL resources: **GapMind pathway predictions** (80 amino acid and carbon source pathways across 293K genomes) and **Fitness Browser RB-TnSeq data** (27M fitness scores across 48 organisms). Using the FB-pangenome link table from `conservation_vs_fitness`, we classify each organism-pathway pair as an **active dependency** (complete + fitness-important), a **latent capability** (complete + fitness-neutral), or **absent**. We then test whether latent capabilities correlate with pangenome openness (Black Queen Hypothesis) and whether within-species pathway variation defines metabolic ecotypes.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Data Sources
- `kbase_ke_pangenome.gapmind_pathways` — 305M rows, 80 pathways
- `kescience_fitnessbrowser.genefitness` — 27M fitness scores, 48 organisms
- Existing: `conservation_vs_fitness/data/fb_pangenome_link.tsv` (177,863 gene-cluster links)
- Existing: `conservation_vs_fitness/data/organism_mapping.tsv` (44 FB → GTDB mappings)

## Structure
notebooks/          — Analysis notebooks (01-05)
data/               — Extracted and processed data
figures/            — Key visualizations
=======
# Metabolic Capability vs Metabolic Dependency

## Research Question

Just because a bacterium's genome encodes a complete metabolic pathway (metabolic *capability*), does the organism actually depend on it? Can we distinguish genomic capability from functional dependency using experimental fitness data?

## Status

Complete — see [Report](REPORT.md) for findings

## Overview

Metabolic pathway prediction from genomes assumes that pathway completeness implies biological relevance. However, many "complete" pathways may be latent capabilities — present but unexpressed, or expressed but functionally redundant with alternative pathways. This project integrates genome-scale metabolic predictions (GapMind pathways) with genome-wide fitness profiling (RB-TnSeq from Fitness Browser) to classify pathways as **active dependencies** (complete + fitness-important), **latent capabilities** (complete + fitness-neutral), or **missing** (incomplete).

For ~30 organisms with both fitness data and pangenome links, we:
1. Map GapMind pathway predictions to fitness-tested genes
2. Classify each predicted-complete pathway by aggregated fitness importance
3. Test if "latent capabilities" predict future gene loss (Black Queen Hypothesis)
4. Identify metabolic ecotypes within species based on pathway heterogeneity

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) — Findings and interpretation (generated after analysis)
- [Review](REVIEW.md) — Automated review (generated after submission)

## Data Sources

- **`kbase_ke_pangenome.gapmind_pathways`** — Pathway completeness predictions (305M rows, 80 pathways, 293K genomes)
- **`kescience_fitnessbrowser.genefitness`** — Gene fitness scores across conditions (27M rows, 48 organisms)
- **`kescience_fitnessbrowser.gene`** — Gene annotations and essentiality inference
- **`kescience_fitnessbrowser.seedannotation`** — SEED subsystem annotations (proxy for pathway membership)
- **`kbase_ke_pangenome.gtdb_metadata`** — NCBI taxonomy for organism matching
- **`kbase_ke_pangenome.pangenome`** — Clade-level core/auxiliary/singleton counts (NB04)

## Project Structure

```
notebooks/          — Analysis pipeline (01-05)
data/               — Extracted and processed data
figures/            — Key visualizations
src/                — Reusable analysis functions
requirements.txt    — Python dependencies
```

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- **Christopher Neely** | ORCID: 0000-0002-2620-8948 | Author
- Sierra Moxon (ORCID: 0000-0002-8719-7760), Lawrence Berkeley National Laboratory / KBase
=======

**Prerequisites:**
- Python 3.11+
- Access to BERDL JupyterHub (for NB01 data extraction)
- Prior project cached data (see Data Sources above)

**Pipeline:**

1. **NB01** (JupyterHub + Spark): Extract GapMind pathway data and aggregate to genome level → `data/gapmind_genome_pathways.csv` ✓ *complete*
2. **NB02** (JupyterHub + Spark): Query FB organism metadata, SEED annotations, fitness aggregates, and essential genes; compute per-pathway fitness metrics using SEED subsystem proxy
3. **NB03** (local): Classify pathways as active dependency / latent capability / intermediate
4. **NB04** (JupyterHub + Spark for pangenome query, then local): Test Black Queen Hypothesis
5. **NB05** (local, Spark optional for env metadata): Identify metabolic ecotypes within species

**Note on NB02 approach**: This project does not depend on `conservation_vs_fitness/data/fb_pangenome_link.tsv`.
Instead, NB02 maps GapMind pathways to Fitness Browser genes via SEED subsystem annotations,
and matches FB organisms to GapMind species clades using NCBI taxonomy IDs from `kbase_ke_pangenome.gtdb_metadata`.

```bash
cd projects/metabolic_capability_dependency
pip install -r requirements.txt

# All notebooks run on BERDL JupyterHub (NB01, NB02, NB04 use Spark; NB03, NB05 run locally)
# NB05 can run independently of NB02-04 (uses only NB01 data)


