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
4. **Annotate modules** — KEGG, SEED, TIGRFam, PFam enrichment (Fisher exact + BH FDR); map to conditions
5. **Cross-organism alignment** — 1.15M BBH pairs → 13,402 ortholog groups → module family fingerprints → 156 families
6. **Predict function** — Module + family context → 6,691 function predictions for hypothetical proteins
7. **Validate** — Within-module cofitness (94.2% enriched) and genomic adjacency (22.7× enrichment)

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

## Status & Next Steps

**Completed**:
1. Stable fitness modules (5-50 genes each) for 32 organisms with biological labels
2. 156 cross-organism module families (28 spanning 5+ organisms, 7 spanning 10+)
3. 6,691 function predictions for hypothetical proteins (2,455 family-backed, 4,236 module-only)
4. Formal benchmarking against cofitness/ortholog/domain baselines (NB07, `src/run_benchmark.py`)

**Remaining**:
5. Resolve TIGRFam/PFam domain IDs to human-readable function descriptions in predictions

## Results

### ICA Decomposition (32 organisms)
- **1,116 stable modules** across 32 organisms (all with ≥100 experiments)
- Module sizes: median 7-50 genes per module (biologically correct range)
- **94.2%** of modules show significantly elevated within-module cofitness (Mann-Whitney U, p < 0.05)
- Within-module mean |r| = 0.34 vs background |r| = 0.12 (2.8× enrichment)
- **22.7× genomic adjacency enrichment** — module genes are co-located in operons

### Benchmarking (NB07)

Held-out evaluation: 20% of KEGG-annotated genes withheld, 4 methods predict KO groups.

| Method | Precision (strict) | Coverage | F1 |
|--------|-------------------|----------|-----|
| **Ortholog transfer** | 95.8% | 91.2% | 0.934 |
| Domain-based | 29.1% | 66.6% | 0.401 |
| Module-ICA | <1% | 23.3% | — |
| Cofitness voting | <1% | 73.0% | — |

Module-ICA and cofitness show near-zero strict KO precision because KEGG KO groups are gene-level assignments (~1.2 genes per unique KO). A module with 20 annotated members typically has 20 different KOs. Modules capture **process-level co-regulation** (validated by 94.2% cofitness enrichment and 22.7× adjacency enrichment), not specific molecular function. Function predictions should be interpreted as biological process context, not exact KO assignments.

### Cross-Organism Alignment
- **1.15M BBH pairs** across 32 organisms → **13,402 ortholog groups**
- **156 module families** spanning 2+ organisms (28 spanning 5+, 7 spanning 10+, 1 spanning 21)
- **145 annotated families** with consensus functional labels (93%)
- Largest family spans 21 organisms — a pan-bacterial fitness module

### Function Prediction
- **6,691 function predictions** for hypothetical proteins across all 32 organisms
- **2,455 family-backed** (37%) — supported by cross-organism conservation
- 4,236 module-only predictions
- Predictions backed by module enrichment (KEGG, SEED, TIGRFam, PFam)

### Key Findings
1. The strict membership threshold (|weight| ≥ 0.3, max 50 genes) was critical. The initial D'Agostino K² approach gave 100-280 genes per module with weak cofitness signal (59% enriched, 1-17x correlation). After switching to absolute weight thresholds, modules became biologically coherent (94% enriched, 2.8× correlation enrichment).
2. Adding PFam domains and lowering the enrichment overlap threshold from 3 to 2 increased module annotation rate from 8% to 80% (92 → 890 modules), unlocking 7.6× more function predictions. PFam provides the broadest annotation coverage; KEGG KOs are too gene-specific for module-level enrichment.
3. Module-ICA is **complementary** to sequence-based methods: it excels at identifying co-regulated gene groups (biological process modules) but should not be used for predicting specific molecular functions, where ortholog transfer is far superior.

## Reproduction

**Prerequisites:**
- Python 3.10+
- `pip install -r requirements.txt`
- BERDL JupyterHub access (for NB01-02 only)

**Running the pipeline:**

1. **NB01-02** (JupyterHub): Extract data from Spark into `data/`. These notebooks require `get_spark_session()` which is only available on the BERDL JupyterHub. They produce cached CSV files in `data/matrices/`, `data/annotations/`, and `data/orthologs/`.

2. **NB03-07** (local): Run locally using cached data files. All notebooks check for existing output files and skip recomputation. To re-run from scratch, delete the cached files in `data/modules/`, `data/module_families/`, and `data/predictions/`.

```bash
cd projects/fitness_modules
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/03_ica_modules.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_module_annotation.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/05_cross_organism_alignment.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/06_function_prediction.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/07_benchmarking.ipynb
```

The benchmark can also be run standalone: `python src/run_benchmark.py`

**Note**: NB03 ICA computation takes 30-80 min per organism (30-50 FastICA runs each). With all 32 organisms cached, NB03 runs in ~1 min (PCA + summary only). NB05 ortholog fingerprinting takes ~1 min.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

## References

- Borchert AJ et al. (2019). "Proteome and transcriptome analysis of *Pseudomonas putida* KT2440 using independent component analysis." *mBio*.
- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature*.
- Hyvärinen A & Oja E (2000). "Independent component analysis: algorithms and applications." *Neural Networks*.
