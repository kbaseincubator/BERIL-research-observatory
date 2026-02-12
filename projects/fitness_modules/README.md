# Pan-bacterial Fitness Modules via Independent Component Analysis

## Research Question

Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?

## Motivation

The Fitness Browser (fit.genomics.lbl.gov) provides fitness scores for ~228K genes across ~7,500 experiments in 48 bacteria. Current analysis relies on **edge-based** approaches (cofitness between gene pairs). This project upgrades to **module-based** analysis:

- **Modules** = groups of genes that respond coherently across conditions (independent components)
- **Cross-organism alignment** = modules from different organisms matched via ortholog fingerprints
- **Function prediction** = unannotated genes inherit function from their module's enrichment

This approach follows Borchert et al. (2019) who applied ICA to *P. putida* fitness data, but extends it to a pan-bacterial framework.

## Approach

### Phase 1: Pilot (5 data-rich organisms)

1. **Explore & select** — Survey all 48 organisms; pick ~5 by data richness (experiment count, gene count, ortholog connectivity)
2. **Extract matrices** — Build gene × experiment fitness matrices from Spark
3. **Robust ICA** — 100× FastICA runs → DBSCAN clustering → stable modules
4. **Annotate modules** — KEGG, SEED, domain enrichment; map to conditions
5. **Cross-organism alignment** — BBH ortholog groups → module family fingerprints
6. **Predict function** — Module + family context → function for hypothetical proteins
7. **Benchmark** — Compare to cofitness voting, ortholog transfer, domain-only baselines

### Phase 2: Scale to all 48 organisms

Extend pipeline after validating on pilot set.

## Key Methods

- **Robust ICA**: FastICA with 100 random restarts; components clustered by cosine similarity (DBSCAN eps~0.15) to identify stable modules
- **Module membership**: D'Agostino K² normality test on gene-weight distribution; outlier genes = members
- **Cross-organism matching**: Convert modules to ortholog-group fingerprints; cosine similarity → hierarchical clustering into families
- **Function prediction**: Module enrichment label × |gene weight| × cross-organism consistency

## Data Sources

All from `kescience_fitnessbrowser` on BERDL:

| Table | Use |
|-------|-----|
| `organism` | Organism metadata, pilot selection |
| `gene` | Gene coordinates, descriptions |
| `experiment` | Condition metadata, QC metrics |
| `genefitness` | Fitness scores (27M rows) |
| `fitbyexp_*` | Pre-pivoted fitness matrices |
| `ortholog` | BBH pairs for cross-organism alignment |
| `cofit` | Baseline comparison |
| `keggmember`, `seedannotation`, `genedomain` | Functional annotations for enrichment |
| `specificphenotype` | Condition-gene associations |

## Project Structure

```
projects/fitness_modules/
├── README.md
├── notebooks/
│   ├── 01_explore_and_select.ipynb     # Data landscape, pick pilot organisms
│   ├── 02_extract_matrices.ipynb       # Gene-fitness matrices from Spark
│   ├── 03_ica_modules.ipynb            # Robust ICA → modules
│   ├── 04_module_annotation.ipynb      # Functional enrichment of modules
│   ├── 05_cross_organism_alignment.ipynb # Module families via ortholog fingerprints
│   ├── 06_function_prediction.ipynb    # Predict function for unannotated genes
│   └── 07_benchmarking.ipynb           # Evaluate vs baselines
├── src/
│   └── ica_pipeline.py                 # Reusable FastICA + DBSCAN stability code
├── data/
│   ├── matrices/       # Per-organism fitness matrices
│   ├── modules/        # ICA module definitions + weights
│   ├── annotations/    # Gene/experiment metadata + functional annotations
│   ├── orthologs/      # BBH pairs + ortholog groups
│   ├── module_families/ # Cross-organism aligned families
│   └── predictions/    # Function predictions + benchmarks
└── figures/
```

## Expected Outcomes

1. **Stable fitness modules** (5-50 genes each) for pilot organisms with biological labels
2. **Conserved module families** shared across 3+ organisms — the pan-bacterial fitness regulon catalog
3. **Function predictions** for hypothetical proteins with confidence scores
4. **Benchmark showing** module-based predictions outperform cofitness voting alone

## References

- Borchert AJ et al. (2019). "Proteome and transcriptome analysis of *Pseudomonas putida* KT2440 using independent component analysis." *mBio*.
- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature*.
- Hyvärinen A & Oja E (2000). "Independent component analysis: algorithms and applications." *Neural Networks*.
