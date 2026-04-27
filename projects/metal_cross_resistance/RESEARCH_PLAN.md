# Research Plan: Gene-Resolution Metal Cross-Resistance Across Diverse Bacteria

## Research Question
Is the genetic architecture of metal cross-resistance conserved across phylogenetically diverse bacteria, or is it rewired species by species? Can gene-level fitness data decompose metal tolerance into shared and specific components, and does the shared component predict multi-metal co-tolerance at pangenome scale?

## Hypothesis
- **H0**: Metal cross-resistance patterns are organism-specific — different species use different genes for the same metal pair, and cross-resistance matrices are uncorrelated across organisms.
- **H1**: Metal-metal fitness correlations are conserved across organisms (same metal pairs cluster in >70% of species). Cross-resistance reflects metal chemistry, not organism-specific wiring.
- **H2**: Cross-resistance (shared) genes are more core in the pangenome than metal-specific genes, extending the 87.4% core enrichment finding (Metal Fitness Atlas) with a finer gradient: general stress > metal-shared > metal-specific.
- **H3**: Predicted multi-metal tolerance (from conserved cross-resistance gene signatures) correlates with polymetallic isolation environments in BacDive, extending the single-metal validation (Cohen's d=+1.0) to multi-metal predictions.

## Literature Context

### What's known
- Classic metal cross-resistance is well-established for chemically similar divalent cations: Co-Ni-Zn share efflux systems (CzcCBA, RcnA; Nies 1999, 2003); Cu-Ag share P-type ATPases (CopA; Rensing & Grass 2003).
- MIC-based studies document cross-resistance at the organism level — a strain resistant to Co tends to be resistant to Ni — but these are binary measurements on a handful of model organisms.
- Recent genome-wide association approaches (Whelan et al. 2020; Pal et al. 2015) link resistance genes to metals using presence/absence, but don't capture the *magnitude* of gene-level fitness effects.

### What's new here
- **Gene-resolution fitness data** from RB-TnSeq across 30 organisms and up to 13 metals — unprecedented scale for cross-resistance analysis.
- **Quantitative fitness effects** (not binary presence/absence) allow us to detect partial cross-resistance and asymmetry.
- **Multi-phylum coverage** (Proteobacteria, Bacteroidetes, Firmicutes, Archaea) tests whether cross-resistance is universal or lineage-specific.
- The Metal Fitness Atlas (our prior work) established that metal genes are 87.4% core — the cross-resistance analysis asks whether the *shared* genes driving cross-resistance are even more core (ancestral defense) while *specific* genes are more accessory (recently acquired).

### Key references
- Nies DK (1999) Microbial heavy-metal resistance. *Appl Microbiol Biotechnol* 51:730-750
- Pal C et al. (2015) Co-occurrence of resistance genes to antibiotics, biocides and metals. *BMC Genomics* 16:964
- Price MN et al. (2018) Mutant phenotypes for thousands of bacterial genes. *Nature* 557:503-509
- Chandrangsu P et al. (2017) Metal homeostasis and resistance in bacteria. *Nat Rev Microbiol* 15:338-350
- Metal Fitness Atlas (this observatory) — 559 experiments, 31 organisms, 14 metals
- Metal Specificity (this observatory) — 55% of metal-important genes are genuinely metal-specific
- Counter Ion Effects (this observatory) — DvH metal-NaCl correlation hierarchy validates toxicity mechanism grouping

## Data Sources

### Primary: Fitness Browser metal experiments
- **422 metal experiments** across **37 organisms** and **13 metals** (Al, Cd, Co, Cr, Cu, Fe, Hg, Mn, Mo, Ni, Se, U, W, Zn)
- **30 organisms with ≥3 metals** — sufficient for cross-resistance matrices
- **12 organisms with ≥5 metals** — ideal for full cross-resistance network analysis
- Best coverage: DvH (13 metals, 112 experiments), psRCH2 (6 metals), 10 organisms with 5 metals each

### Secondary: Existing observatory data products
- Fitness matrices from `fitness_modules` project (32 organisms, genes × experiments)
- Metal-important gene lists from `metal_fitness_atlas` (12,838 records)
- Metal-specificity classification from `metal_specificity` (55% metal-specific)
- Ortholog groups from `essential_genome` (17,222 families, 48 organisms)
- Pangenome gene cluster conservation (132M clusters, 27K species)
- BacDive isolation environments (97K strains, 6,426 matched species)

### Tertiary: Pangenome functional annotations
- eggNOG COG/KEGG/PFAM from `kbase_ke_pangenome.eggnog_mapper_annotations`
- GapMind pathway predictions from `kbase_ke_pangenome.gapmind_pathways`

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_fitnessbrowser.experiment` | Classify metal experiments | ~20K | Filter by condition keywords |
| `kescience_fitnessbrowser.genefitness` | Gene-level fitness per experiment | 27M | Filter by orgId |
| `kescience_fitnessbrowser.ortholog` | Cross-organism gene families | ~1.15M | Filter by orgId pair |
| `kbase_ke_pangenome.gene_cluster` | Core/accessory classification | 132M | Filter by species |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | Functional annotations (COG, PFAM) | 93M | Filter by gene_cluster_id |
| `kescience_bacdive.isolation_environment` | Isolation site metadata | ~97K | Full scan (small) |

### Key Queries

1. **Metal experiment classification** — Classify all FB experiments by metal type:
```sql
SELECT orgId, expName, condition_1, expGroup
FROM kescience_fitnessbrowser.experiment
WHERE [metal keyword filters]
```

2. **Per-organism gene × metal fitness matrix** — For each organism, pivot fitness by metal:
```sql
SELECT gf.locusId, e.metal_type, AVG(CAST(gf.fit AS FLOAT)) as mean_fit
FROM kescience_fitnessbrowser.genefitness gf
JOIN metal_experiments e ON gf.expName = e.expName
WHERE gf.orgId = '{orgId}'
GROUP BY gf.locusId, e.metal_type
```

3. **Core/accessory status via ortholog groups** — Link FB genes to pangenome conservation:
```sql
-- Reuse essential_genome ortholog groups + family_conservation data
```

### Performance Plan
- **Tier**: Direct Spark SQL on JupyterHub
- **Estimated complexity**: Moderate — per-organism queries are fast; cross-organism aggregation is the bottleneck
- **Known pitfalls**:
  - All FB columns are strings — CAST to FLOAT for fitness values
  - Metal experiment naming is inconsistent (see NB01 for classification logic)
  - DvH locusId type mismatch with fitness matrices (always convert to str)
  - Fitness matrices from fitness_modules use integer-typed locusId indices

## Analysis Plan

### Notebook 1: Metal Experiment Inventory & Fitness Extraction (`01_metal_experiment_inventory.ipynb`)
- **Goal**: Classify all FB experiments by metal type; build organism × metal coverage matrix; extract per-organism gene × metal fitness matrices
- **Expected output**: `data/metal_experiments.csv`, `data/organism_metal_coverage.csv`, `data/gene_metal_fitness/{orgId}_metal_fitness.csv`
- **Environment**: BERDL JupyterHub (Spark required for genefitness extraction)

### Notebook 2: Per-Organism Cross-Resistance Matrices (`02_cross_resistance_matrices.ipynb`)
- **Goal**: For each organism with ≥3 metals, correlate gene fitness profiles between all metal pairs. Produce a metal × metal Pearson correlation matrix per organism.
- **Key analysis**:
  - For each organism, build a gene × metal matrix (mean fitness across replicates per metal)
  - Compute pairwise Pearson correlation between all metal columns
  - Test significance via permutation (shuffle gene labels, recompute correlation, 1000 permutations)
  - Identify asymmetry: is corr(Co→Ni) = corr(Ni→Co)? (Yes for Pearson, but contribution magnitudes differ)
- **Expected output**: `data/cross_resistance_matrices/{orgId}_metal_corr.csv`, `figures/cross_resistance_heatmaps.png`
- **Environment**: Local (from cached fitness data)

### Notebook 3: Conservation of Cross-Resistance Patterns (H1) (`03_cross_resistance_conservation.ipynb`)
- **Goal**: Compare cross-resistance matrices across organisms. Test whether metal pairs that are correlated in one organism are correlated in others.
- **Key analysis**:
  - Extract the common metal pairs tested in ≥5 organisms (Co-Ni, Co-Cu, Co-Zn, Co-Al, Cu-Ni, Ni-Zn, Al-Co, etc.)
  - For each metal pair, collect the Pearson r values across all organisms that tested both metals
  - Test H1: sign consistency (>70% of organisms show same-sign correlation for each metal pair)
  - Hierarchical clustering of the consensus cross-resistance matrix
  - Compare to known chemical groupings (divalent cation displacement vs pathway-specific)
  - Mantel test: does chemical similarity (ionic radius, charge, electronegativity) predict fitness correlation?
- **Expected output**: `data/consensus_cross_resistance.csv`, `figures/cross_resistance_conservation.png`, `figures/metal_clustering_dendrogram.png`
- **Environment**: Local

### Notebook 4: Shared vs Specific Gene Architecture (H2) (`04_shared_vs_specific_genes.ipynb`)
- **Goal**: For each gene, classify as general-stress / metal-shared / metal-specific based on fitness profiles. Test whether shared genes are more core than specific genes.
- **Key analysis**:
  - Three-tier classification per gene:
    - **General stress**: Important (fit < -1) in ≥1 metal AND sick rate ≥ 50% across non-metal experiments (pleiotropic)
    - **Metal-shared**: Important in ≥2 metals, sick rate < 50% in non-metal experiments
    - **Metal-specific**: Important in exactly 1 metal, sick rate < 50% in non-metal experiments
  - Map genes to pangenome core/accessory via ortholog groups (from essential_genome)
  - Test H2: core enrichment gradient — general > metal-shared > metal-specific
  - Identify the genes driving cross-resistance (metal-shared) — functional enrichment via COG/KEGG
  - Compare metal-shared genes across organisms: are the same gene families shared in different organisms?
- **Expected output**: `data/gene_tier_classification.csv`, `data/tier_conservation.csv`, `figures/core_enrichment_gradient.png`
- **Environment**: Local + Spark for pangenome lookups

### Notebook 5: Pangenome Prediction & BacDive Validation (H3) (`05_pangenome_prediction.ipynb`)
- **Goal**: Use conserved cross-resistance gene signatures to predict multi-metal tolerance across 27K species. Validate against BacDive isolation environments.
- **Key analysis**:
  - Define a "multi-metal score" per species: count of conserved cross-resistance gene families present
  - Predict which species should tolerate multiple metals simultaneously
  - Validate against BacDive: do species from polymetallic environments (mine tailings, contaminated sediments, acid mine drainage) have higher multi-metal scores?
  - Compare to single-metal predictions from Metal Fitness Atlas (are multi-metal predictions more informative?)
  - Identify "surprise" species: high multi-metal score but not from known contaminated environments (bioprospecting candidates)
- **Expected output**: `data/species_multimetal_scores.csv`, `figures/bacdive_multimetal_validation.png`
- **Environment**: BERDL JupyterHub (Spark for pangenome-scale annotation lookup)

### Notebook 6: Summary Figures (`06_summary_figures.ipynb`)
- **Goal**: Publication-quality figures summarizing key findings
- **Expected output**: `figures/fig1_cross_resistance_network.png`, `figures/fig2_conservation_across_organisms.png`, `figures/fig3_core_enrichment_tiers.png`, `figures/fig4_pangenome_prediction.png`
- **Environment**: Local

## Expected Outcomes
- **If H1 supported** (conserved cross-resistance): Metal cross-resistance is a universal property of metal chemistry, not organism-specific wiring. The consensus cross-resistance network becomes a predictive tool — knowing a species tolerates Co lets you predict its Ni tolerance. Practical implications for bioremediation site assessment.
- **If H1 rejected** (rewired cross-resistance): Each organism has independently evolved its cross-resistance architecture. This means organism-specific fitness data is required for accurate multi-metal predictions — no shortcuts from model organisms. Equally interesting as it shows convergent evolution of different solutions to the same chemical challenge.
- **If H2 supported** (core enrichment gradient): The evolutionary story is: ancestral general stress defense (deepest core) → shared metal defense (core) → specialized metal-specific resistance (more accessory). This adds a temporal dimension to the Metal Fitness Atlas findings.
- **If H0 not rejected**: Metal fitness effects are too noisy or organism-specific for cross-resistance patterns to emerge. This would suggest that MIC-based cross-resistance studies are measuring a different phenomenon than gene-level fitness effects.
- **Potential confounders**:
  - Metal concentration differences across experiments (dose-response effects)
  - Counter ion effects (addressed by counter_ion_effects project — not the primary confound)
  - Unequal experiment counts per metal per organism
  - Phylogenetic non-independence (organisms share evolutionary history)

## Revision History
- **v1** (2026-04-27): Initial plan

## Authors
- Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
