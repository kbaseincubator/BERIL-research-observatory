# Co-fitness Predicts Co-inheritance in Bacterial Pangenomes

## Research Question

Do genes with correlated fitness profiles (co-fit) tend to co-occur in the same genomes across a species' pangenome? Does functional coupling constrain which genes are gained and lost together?

## Status

Completed -- pairwise co-fitness weakly but consistently predicts co-occurrence (delta phi=+0.003, 7/9 organisms positive, p=1.66e-29), with ICA fitness modules showing stronger co-inheritance (delta=+0.053, 49/195 modules significant, accessory modules 73% significant).

## Overview

This project tests whether lab-measured functional coupling (co-fitness from RB-TnSeq) predicts genome-level co-inheritance (co-occurrence in pangenomes) across 11 bacterial species. It builds on `module_conservation` (modules are 86% core) and `fitness_modules` (48 accessory modules exist). Phi coefficients (binary Pearson correlation) measure co-occurrence across genomes, compared against prevalence-matched random pairs. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md) for the detailed hypothesis and analysis plan.

Key results: Pairwise co-fitness weakly but consistently predicts co-occurrence (7/9 organisms positive), though the effect size is small. Multi-gene ICA modules show a substantially stronger co-inheritance signal, especially the 48 accessory modules -- functionally coherent gene groups that travel together through the pangenome (73% significant). See [REPORT.md](REPORT.md) for full findings and interpretation.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Hypothesis, approach, analysis plan
- [Report](REPORT.md) -- Findings, interpretation, literature context, supporting evidence
- [References](references.md) -- Cited literature

## Approach

1. **Genome x gene cluster presence matrices**: For 11 target species, extract which gene clusters are present in which genomes from the KBase pangenome database
2. **Phi coefficient (co-occurrence)**: For each pair of gene clusters, compute phi = Pearson correlation of binary presence/absence vectors across genomes
3. **Co-fitness pairs**: Use top-20 co-fitness partners per gene from Fitness Browser `cofit` table as the test set
4. **Prevalence gradient**: Analyze phi as a continuous function of mean prevalence (not binary core/aux), maximizing statistical power
5. **Controls**: (a) Matched random pairs at same prevalence, (b) Exclude adjacent genes (operon control), (c) Stratify by phylogenetic distance

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kbase_ke_pangenome` | `gene_genecluster_junction`, `gene` | Genome x cluster presence matrices |
| `kescience_fitnessbrowser` | `cofit` | Co-fitness pairs (top-20 per gene) |
| `kescience_fitnessbrowser` | `gene` | Gene coordinates for adjacency control |
| `kbase_ke_pangenome` | `phylogenetic_tree_distance_pairs` | Phylogenetic distances between genomes |
| Shared | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Gene-to-cluster mapping (177K links) |
| Shared | `conservation_vs_fitness/data/organism_mapping.tsv` | Organism-to-species clade mapping |
| Shared | `conservation_vs_fitness/data/seed_annotations.tsv` | SEED functional annotations |
| Shared | `fitness_modules/data/modules/*_gene_membership.csv` | ICA module memberships |
| Shared | `module_conservation/data/module_conservation.tsv` | Module conservation stats |

## Target Organisms

| Organism | Genomes | ANI | Aux% | Aux FB genes | ICA Modules | Cofit data |
|----------|---------|-----|------|-------------|-------------|------------|
| Koxy | 399 | 98.57 | 92.6% | 822 | Yes | Yes |
| Btheta | 287 | 98.44 | 95.1% | 1,632 | Yes | Yes |
| Smeli | 241 | 98.93 | 91.5% | 1,365 | No | Yes |
| RalstoniaUW163 | 141 | 96.27 | 83.3% | 867 | No | **No** |
| Putida | 128 | 97.49 | 90.3% | 1,372 | Yes | Yes |
| SyringaeB728a | 126 | 98.70 | 85.3% | 723 | No | Yes |
| Korea | 72 | 98.13 | 40.3% | 637 | Yes | Yes |
| RalstoniaGMI1000 | 70 | 95.97 | 81.4% | 932 | No | **No** |
| Phaeo | 43 | 97.75 | 68.6% | 508 | Yes | Yes |
| Ddia6719 | 66 | 99.47 | 61.2% | 767 | No | Yes |
| pseudo3_N2E3 | 40 | 99.66 | 47.4% | 140 | Yes | Yes |

## Project Structure

```
projects/cofitness_coinheritance/
├── README.md
├── RESEARCH_PLAN.md
├── REPORT.md
├── references.md
├── notebooks/
│   ├── 01_data_extraction.ipynb        # Spark: genome x cluster matrices, cofit
│   ├── 02_cooccurrence.ipynb           # Local: phi computation + prevalence analysis
│   ├── 03_module_coinheritance.ipynb   # Local: module-level (secondary)
│   └── 04_cross_organism.ipynb         # Local: meta-analysis + figures
├── src/
│   └── extract_data.py                 # Spark Connect extraction script
├── data/
│   ├── genome_cluster_matrices/        # Per-species presence/absence matrices
│   ├── cofit/                          # Per-organism cofit pairs
│   ├── gene_coords/                    # Per-organism gene coordinates
│   ├── phylo_distances/               # Per-species pairwise phylogenetic distances
│   ├── {org}_phi_results.tsv           # Per-organism phi results
│   ├── organism_summary.tsv           # Per-organism effect sizes
│   └── module_coinheritance.tsv       # Module-level co-inheritance
├── figures/
└── requirements.txt
```

## Reproduction

**Step 1** (requires BERDL JupyterHub with Spark):
```bash
cd projects/cofitness_coinheritance
python src/extract_data.py
# or run notebooks/01_data_extraction.ipynb interactively
```

**Step 2** (local):
```bash
jupyter nbconvert --execute notebooks/02_cooccurrence.ipynb
jupyter nbconvert --execute notebooks/03_module_coinheritance.ipynb
jupyter nbconvert --execute notebooks/04_cross_organism.ipynb
```

## Dependencies

Requires data from:
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` and `organism_mapping.tsv`
- `projects/conservation_vs_fitness/data/seed_annotations.tsv`
- `projects/fitness_modules/data/modules/`
- `projects/module_conservation/data/module_conservation.tsv`

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
