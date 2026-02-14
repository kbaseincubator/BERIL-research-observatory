# The Pan-Bacterial Essential Genome

## Research Question

Which essential genes are conserved across bacteria, which are context-dependent, and can we predict function for uncharacterized essential genes using module context from non-essential orthologs?

## Motivation

The `conservation_vs_fitness` project identified 27,693 putative essential genes across 33 bacteria and showed they are modestly enriched in core pangenome clusters (OR=1.56). The `fitness_modules` project built 1,116 ICA fitness modules across 32 organisms and aligned them into 156 cross-organism families. But no one has asked: **when an essential gene in organism A has an ortholog in organism B, is that ortholog also essential?**

This project clusters essential genes into cross-organism ortholog families and classifies them along a spectrum:

- **Universally essential** — essential in every organism where the family has members. These are the most fundamental bacterial functions.
- **Variably essential** — essential in some organisms, non-essential in others. Essentiality depends on genomic context, metabolic wiring, or strain background.
- **Never essential** — ortholog family has no essential members in any organism.

For uncharacterized essential genes (~44% hypothetical), we predict function by finding non-essential orthologs in other organisms that participate in ICA fitness modules, transferring the module's functional context.

## Approach

1. **Extract data** — Essential gene status + BBH ortholog pairs for all 48 FB organisms via Spark
2. **Build ortholog groups** — Connected components of BBH graph (networkx)
3. **Classify families** — Universal vs variable vs never essential
4. **Predict function** — Module-based function transfer for hypothetical essentials
5. **Conservation architecture** — Connect essential families to pangenome core/accessory status

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `organism` | All 48 organisms |
| `kescience_fitnessbrowser` | `gene` | Gene metadata, type=1 for CDS |
| `kescience_fitnessbrowser` | `genefitness` | Absence = putative essential |
| `kescience_fitnessbrowser` | `ortholog` | BBH pairs across organisms |
| `kescience_fitnessbrowser` | `seedannotation` | SEED functional annotations |
| Shared | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Conservation status |
| Shared | `fitness_modules/data/modules/*` | ICA module membership + annotations |
| Shared | `fitness_modules/data/module_families/*` | Cross-organism module families |

## Project Structure

```
projects/essential_genome/
├── README.md
├── src/
│   └── extract_data.py               # Spark: extract essentials + orthologs
├── notebooks/
│   ├── 02_essential_families.ipynb    # Build and classify essential gene families
│   ├── 03_function_prediction.ipynb   # Predict function for hypothetical essentials
│   └── 04_conservation_architecture.ipynb  # Connect to pangenome conservation
├── data/
│   ├── all_essential_genes.tsv        # Essential status for all 48 organisms
│   ├── all_bbh_pairs.csv             # BBH pairs for all 48 organisms
│   └── all_ortholog_groups.csv       # OG assignments for all 48 organisms
└── figures/
```

## Key Definitions

- **Essential gene**: Protein-coding gene (type=1 in FB gene table) with zero entries in `genefitness` — no viable transposon mutants were recovered during RB-TnSeq library construction. This is an upper bound on true essentiality; some genes may lack insertions due to being short or in regions with poor transposon coverage.
- **Ortholog group (OG)**: Connected component in the BBH (bidirectional best BLAST hit) graph across organisms. Each OG represents a family of orthologous genes.
- **Universally essential family**: OG where every member gene is essential in its respective organism.
- **Variably essential family**: OG with at least one essential and one non-essential member.

## Key Findings

### Essential Gene Landscape (NB01)
- **221,005 genes** across 48 organisms, **41,059 essential** (18.6%)
- Essentiality rate ranges from 12.2% (*Pedo557*) to 29.7% (*Magneto*)
- **2,838,750 BBH pairs** yield **17,222 ortholog groups** spanning all 48 organisms

### Essential Gene Families (NB02)
- **859 universally essential families** (5.0%) — essential in every organism where they have members. Dominated by ribosomal proteins, tRNA synthetases, cell wall biosynthesis, and DNA replication.
- **15 families essential in ALL 48 organisms** — the absolute core of bacterial life (rpsC, rplW, groEL, pyrG, fusA, rplK, valS, rplB, rplA, rpsJ, rplF, rpsI, rpsM, rps11, SelGGPS)
- **4,799 variably essential families** (27.9%) — essential in some organisms, non-essential in others. Median essentiality penetrance is 33%.
- **7,084 orphan essential genes** with no orthologs — 58.7% hypothetical, the highest-priority targets for functional discovery
- Universally essential genes are only 8.2% hypothetical vs 58.7% for orphan essentials

### Function Prediction for Hypothetical Essentials (NB03)
- **8,297 hypothetical essential genes** across 48 organisms (20.2% of all essentials)
- **1,382 function predictions** for hypothetical essentials via ortholog-module transfer (35.3% of predictable targets)
- All 1,382 predictions are family-backed (supported by cross-organism module conservation)
- Top predicted functions: TIGR00254 (signal transduction), PF00460 (flagellar basal body rod), PF00356 (lactoylglutathione lyase)

### Conservation Architecture (NB04)
- Universally essential genes are **91.7% core** vs 80.7% for non-essential genes — the strongest conservation enrichment
- **71% of universally essential families are 100% core**; 82% are ≥90% core
- Variably essential families are 88.9% core — between universal and never-essential
- Orphan essentials (no orthologs) are only **49.5% core** — they are strain-specific essential functions
- There is a significant negative correlation between essentiality penetrance and core fraction (rho=-0.123, p=1.6e-17) among variably essential families: families essential in more organisms tend to be core, but the relationship is weak
- Clade size does NOT predict essentiality rate (rho=-0.13, p=0.36)

## Reproduction

**Prerequisites**: Python 3.10+, pandas, numpy, matplotlib, scipy, networkx, scikit-learn. BERDL Spark Connect for data extraction.

1. **Extract data** (Spark): `python3 src/extract_data.py`
2. **Run NB02** (local): `jupyter nbconvert --execute notebooks/02_essential_families.ipynb`
3. **Run NB03** (local): `jupyter nbconvert --execute notebooks/03_function_prediction.ipynb`
4. **Run NB04** (local): `jupyter nbconvert --execute notebooks/04_conservation_architecture.ipynb`

Requires data from `conservation_vs_fitness` (link table) and `fitness_modules` (module membership, annotations, families).

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
