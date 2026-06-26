# AlphaFold MSA Depth as a Lens on the Bacterial Annotation Gap

## Research Question

Does AlphaFold MSA depth predict functional annotation richness in the bacterial pangenome, and is structural novelty (low MSA depth) systematically enriched in accessory and singleton gene families relative to core genes?

## Status

Completed — Core genes show 2.9× higher median MSA depth than accessory genes (Spearman ρ = 0.756 between MSA depth and domain annotation richness); 415,603 "paradox proteins" — universally conserved core clusters with msa_depth < 10 — are 68.9% hypothetical and prioritized for structural characterisation.

**Key results:** Core genes have 2.9× higher median MSA depth than accessory genes (Spearman ρ = 0.756 between MSA depth and domain annotation richness). 415,603 "paradox proteins" — core gene clusters conserved across 14,768 species yet with msa_depth < 10 — are 68.9% hypothetical with near-zero EC/KEGG coverage, making them the highest-priority targets for structural characterisation.

## Overview

AlphaFold assigns each predicted protein structure an MSA depth score — the number of evolutionary homologs used to build the multiple sequence alignment underpinning the prediction. Proteins with low MSA depth are structurally novel: few homologs exist in sequence databases, making them hard to predict and typically poorly annotated.

This project maps MSA depth onto the BERDL pangenome (293K genomes, 27K species, 132M gene clusters) to ask: where does structural novelty live in the core vs. accessory genome? We test whether low-MSA-depth proteins are disproportionately hypothetical, lack domain annotations, and are enriched in the accessory/singleton genome — and identify the exceptional "paradox proteins": core genes that are universally conserved yet structurally uncharacterized.

**Key databases used:**
- `kbase_ke_pangenome` — `gene_cluster`, `bakta_annotations`, `interproscan_domains`
- `kescience_alphafold` — `alphafold_msa_depths`

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, query strategy, analysis plan
- [Report](REPORT.md) — findings and interpretation

## Reproduction

**Prerequisites:** BERDL JupyterHub access (Spark), Python 3.10+, see `requirements.txt`.

Run notebooks in order:
1. `NB01_data_extraction.ipynb` — Spark (JupyterHub required)
2. `NB02_domain_annotation.ipynb` — Spark (JupyterHub required)
3. `NB02b_msa_domain_join.ipynb` — Spark (JupyterHub required)
4. `NB03_statistical_analysis.ipynb` — local Python from cached CSVs in `data/`
5. `NB04_paradox_proteins.ipynb` — local Python from cached CSVs in `data/`
6. `NB04b_paradox_ranking.ipynb` — Spark (JupyterHub required)

Copy `/tmp/gc_msa_agg.csv`, `/tmp/gc_domain_agg.csv`, `/tmp/gc_msa_domain_agg.csv`, `/tmp/gc_h3_spearman.csv`, `/tmp/paradox_summary.csv`, `/tmp/paradox_top1000.csv` to `data/` after Spark runs.

## Authors

- Gazi S. Mahmud | ORCID: 0009-0006-4046-889X | Lawrence Berkeley National Laboratory
