# Research Plan: Pan-bacterial Fitness Modules via Independent Component Analysis

## Research Question

Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?

## Motivation

The Fitness Browser (fit.genomics.lbl.gov) provides fitness scores for ~228K genes across ~7,500 experiments in 48 bacteria. Current analysis relies on **edge-based** approaches (cofitness between gene pairs). This project upgrades to **module-based** analysis:

- **Modules** = groups of genes that respond coherently across conditions (independent components)
- **Cross-organism alignment** = modules from different organisms matched via ortholog fingerprints
- **Function prediction** = unannotated genes inherit function from their module's enrichment

This approach follows Borchert et al. (2019) who applied ICA to *P. putida* fitness data, but extends it to a pan-bacterial framework.

## Hypothesis

Robust ICA applied to gene-fitness matrices will identify stable, biologically coherent modules of co-regulated genes. These modules can be aligned across organisms using ortholog fingerprints to reveal conserved fitness regulons, and module membership can be used to predict function for unannotated genes.

## Approach

1. **Explore & select** -- Surveyed all 48 organisms; selected 32 with >=100 experiments
2. **Extract matrices** -- Built gene x experiment fitness matrices from Spark (2,531-6,384 genes x 104-757 experiments)
3. **Robust ICA** -- 30-50x FastICA runs -> DBSCAN clustering -> stable modules (5-50 genes each)
4. **Annotate modules** -- KEGG, SEED, TIGRFam, PFam enrichment (Fisher exact + BH FDR); map to conditions
5. **Cross-organism alignment** -- 1.15M BBH pairs -> 13,402 ortholog groups -> module family fingerprints -> 156 families
6. **Predict function** -- Module + family context -> 6,691 function predictions for hypothetical proteins
7. **Validate** -- Within-module cofitness (94.2% enriched) and genomic adjacency (22.7x enrichment)

## Key Methods

- **Robust ICA**: FastICA with 30-50 random restarts, 32-80 components (capped at 40% of experiments); components clustered by |cosine similarity| (DBSCAN eps=0.15) to identify stable modules
- **Module membership**: Absolute weight threshold (|Pearson r| >= 0.3 with module profile, max 50 genes per module)
- **Cross-organism matching**: Convert modules to ortholog-group fingerprints; cosine similarity -> hierarchical clustering into families
- **Function prediction**: Module enrichment label x |gene weight| x cross-organism consistency

## Data Sources

All from `kescience_fitnessbrowser` on BERDL:

| Table | Use |
|-------|-----|
| `organism` | Organism metadata, pilot selection |
| `gene` | Gene coordinates, descriptions |
| `experiment` | Condition metadata, QC metrics |
| `genefitness` | Fitness scores (27M rows) |
| `ortholog` | BBH pairs for cross-organism alignment (1.15M for 32 organisms) |
| `cofit` | Cofitness validation baseline |
| `besthitkegg` -> `keggmember` -> `kgroupdesc` | KEGG functional annotations |
| `seedannotation` | SEED functional descriptions |
| `genedomain` | TIGRFam/PFam domain annotations |
| `specificphenotype` | Condition-gene associations |

## Project Structure

```
projects/fitness_modules/
├── README.md
├── notebooks/
│   ├── 01_explore_and_select.ipynb     # Data landscape, pick pilot organisms
│   ├── 02_extract_matrices.ipynb       # Gene-fitness matrices from Spark
│   ├── 03_ica_modules.ipynb            # Robust ICA -> modules
│   ├── 04_module_annotation.ipynb      # Functional enrichment of modules
│   ├── 05_cross_organism_alignment.ipynb # Module families via ortholog fingerprints
│   ├── 06_function_prediction.ipynb    # Predict function for unannotated genes
│   └── 07_benchmarking.ipynb           # Evaluate vs baselines
├── src/
│   ├── ica_pipeline.py                 # Reusable FastICA + DBSCAN stability code
│   └── run_benchmark.py                # NB07 benchmark (4 methods, cofitness/adjacency validation)
├── data/
│   ├── matrices/       # Per-organism fitness matrices
│   ├── modules/        # ICA module definitions + weights
│   ├── annotations/    # Gene/experiment metadata + functional annotations
│   ├── orthologs/      # BBH pairs + ortholog groups
│   ├── module_families/ # Cross-organism aligned families
│   └── predictions/    # Function predictions + benchmarks
└── figures/
```

## References

- Borchert AJ et al. (2019). "Proteome and transcriptome analysis of *Pseudomonas putida* KT2440 using independent component analysis." *mBio*.
- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature*.
- Hyvarinen A & Oja E (2000). "Independent component analysis: algorithms and applications." *Neural Networks*.

## Revision History
- **v1** (2026-02): Migrated from README.md
