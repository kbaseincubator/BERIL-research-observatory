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

1. **Explore & select** — Surveyed all 48 organisms; selected 32 with ≥100 experiments
2. **Extract matrices** — Built gene × experiment fitness matrices from Spark (2,531-6,384 genes × 104-757 experiments)
3. **Robust ICA** — 30-50× FastICA runs → DBSCAN clustering → stable modules (5-50 genes each)
4. **Annotate modules** — KEGG, SEED, TIGRFam enrichment (Fisher exact + BH FDR); map to conditions
5. **Cross-organism alignment** — 1.15M BBH pairs → 13,402 ortholog groups → module family fingerprints → 156 families
6. **Predict function** — Module + family context → 878 function predictions for hypothetical proteins
7. **Validate** — Within-module cofitness (93.2% enriched) and gene correlation (17-138× above random)

## Key Methods

- **Robust ICA**: FastICA with 30-50 random restarts, 32-80 components (capped at 40% of experiments); components clustered by |cosine similarity| (DBSCAN eps=0.15) to identify stable modules
- **Module membership**: Absolute weight threshold (|Pearson r| ≥ 0.3 with module profile, max 50 genes per module)
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
| `ortholog` | BBH pairs for cross-organism alignment (1.15M for 32 organisms) |
| `cofit` | Cofitness validation baseline |
| `besthitkegg` → `keggmember` → `kgroupdesc` | KEGG functional annotations |
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

## Status & Next Steps

**Completed**:
1. Stable fitness modules (5-50 genes each) for 32 organisms with biological labels
2. 156 cross-organism module families (28 spanning 5+ organisms, 7 spanning 10+)
3. 878 function predictions for hypothetical proteins (493 family-backed, 385 module-only)

**Remaining**:
4. Formal benchmarking: precision/recall comparison of module-based vs cofitness/ortholog/domain baselines (NB07 has validation metrics but not the full held-out benchmark)
5. Resolve TIGRFam IDs to human-readable function descriptions in predictions

## Results

### ICA Decomposition (32 organisms)
- **1,077 stable modules** across 32 organisms (all with ≥100 experiments)
- Module sizes: median 7-50 genes per module (biologically correct range)
- **93.2%** of modules show elevated within-module cofitness vs genome-wide background
- Within-module gene correlation: 17-138x above random pairs

### Cross-Organism Alignment
- **1.15M BBH pairs** across 32 organisms → **13,402 ortholog groups**
- **156 module families** spanning 2+ organisms (28 spanning 5+, 7 spanning 10+, 1 spanning 21)
- 32 annotated families with consensus functional labels
- Largest family spans 21 organisms — a pan-bacterial fitness module

### Function Prediction
- **878 function predictions** for hypothetical proteins across 29 organisms
- **493 family-backed** (56%) — supported by cross-organism conservation
- 385 module-only predictions
- Predictions backed by module enrichment (KEGG, SEED, TIGRFam)

### Key Finding
The strict membership threshold (|weight| ≥ 0.3, max 50 genes) was critical. The initial D'Agostino K² approach gave 100-280 genes per module with weak cofitness signal (59% enriched, 1-17x correlation). After switching to absolute weight thresholds, modules became biologically coherent (93% enriched, 17-138x correlation).

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

## References

- Borchert AJ et al. (2019). "Proteome and transcriptome analysis of *Pseudomonas putida* KT2440 using independent component analysis." *mBio*.
- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature*.
- Hyvärinen A & Oja E (2000). "Independent component analysis: algorithms and applications." *Neural Networks*.
