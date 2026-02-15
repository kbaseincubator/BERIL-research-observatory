# The Pan-Bacterial Essential Genome

## Research Question

Which essential genes are conserved across bacteria, which are context-dependent, and can we predict function for uncharacterized essential genes using module context from non-essential orthologs?

## Status

Completed — 859 universally essential families identified across 48 organisms, 1,382 function predictions for hypothetical essentials, conservation hierarchy established.

## Overview

This project clusters essential genes (defined by RB-TnSeq: no viable transposon mutants recovered) into cross-organism ortholog families and classifies them as universally essential, variably essential, or never essential. It builds on two upstream projects: `conservation_vs_fitness` (FB-pangenome link table) and `fitness_modules` (ICA modules and cross-organism families). For uncharacterized essential genes (~20% of all essentials are hypothetical), function is predicted by finding non-essential orthologs in other organisms that participate in ICA fitness modules, transferring the module's functional context. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md) for the detailed hypothesis, query strategy, and analysis plan.

Key results: 15 families are essential in all 48 organisms (the irreducible core of bacterial life), variable essentiality is the norm (28% of families), and 7,084 orphan essential genes (58.7% hypothetical) represent the frontier of unknown biology. See [REPORT.md](REPORT.md) for full findings and interpretation.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — Hypothesis, approach, query strategy, analysis plan
- [Report](REPORT.md) — Findings, interpretation, literature context, supporting evidence
- [Review](REVIEW.md) — Automated review
- [References](references.md) — Cited literature

## Key Definitions

- **Essential gene**: Protein-coding gene (type=1 in FB gene table) with zero entries in `genefitness` — no viable transposon mutants recovered. Upper bound on true essentiality.
- **Ortholog group (OG)**: Connected component in the BBH (bidirectional best BLAST hit) graph across organisms.
- **Universally essential family**: OG where every member gene is essential in its respective organism.
- **Variably essential family**: OG with at least one essential and one non-essential member.

## Cross-Project Dependencies

This project requires cached data from two upstream projects:

| File | Source Project | Description |
|------|--------------|-------------|
| `conservation_vs_fitness/data/fb_pangenome_link.tsv` | conservation_vs_fitness | Gene-to-cluster links with conservation status |
| `conservation_vs_fitness/data/organism_mapping.tsv` | conservation_vs_fitness | FB orgId → pangenome species clade mapping |
| `conservation_vs_fitness/data/pangenome_metadata.tsv` | conservation_vs_fitness | Clade size, core counts |
| `conservation_vs_fitness/data/seed_annotations.tsv` | conservation_vs_fitness | SEED functional annotations (34 organisms) |
| `conservation_vs_fitness/data/seed_hierarchy.tsv` | conservation_vs_fitness | SEED functional category hierarchy |
| `fitness_modules/data/modules/*_gene_membership.csv` | fitness_modules | ICA module membership (32 organisms) |
| `fitness_modules/data/modules/*_module_annotations.csv` | fitness_modules | Module functional enrichments |
| `fitness_modules/data/module_families/module_families.csv` | fitness_modules | Module → family mapping |
| `fitness_modules/data/module_families/family_annotations.csv` | fitness_modules | Family consensus annotations |

## Reproduction

**Prerequisites**: Python 3.10+, pandas, numpy, matplotlib, scipy, networkx, scikit-learn. BERDL Spark Connect for data extraction.

```bash
cd projects/essential_genome
pip install -r requirements.txt

# Step 1: Extract data from Spark (requires BERDL access)
python3 src/extract_data.py

# Step 2-4: Run analysis notebooks (local, no Spark needed)
jupyter nbconvert --to notebook --execute --inplace notebooks/02_essential_families.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_function_prediction.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_conservation_architecture.ipynb
```

Requires cached data from upstream projects (see Cross-Project Dependencies above).

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
