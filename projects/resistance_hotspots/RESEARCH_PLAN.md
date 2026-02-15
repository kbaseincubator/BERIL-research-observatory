# Research Plan: Antibiotic Resistance Hotspots in Microbial Pangenomes

## Research Question

Which microbial species and ecological environments show the highest concentration of antibiotic resistance genes (ARGs)? Can we predict which environmental conditions and phylogenetic lineages are most prone to accumulating resistance mechanisms?

## Scientific Motivation

Antibiotic resistance is a critical global health threat. Understanding the distribution, prevalence, and evolutionary dynamics of antibiotic resistance genes across diverse microbial taxa could:

- Guide surveillance efforts toward high-risk species and environments
- Identify organisms with exceptional resistance gene diversity
- Reveal phylogenetic and ecological patterns in resistance evolution
- Predict which organisms are at highest risk for future resistance emergence
- Inform intervention strategies targeting resistance hotspots

## Project Goals

1. **Identify ARG Distribution**: Map antibiotic resistance genes across the 293,059 genomes in the pangenome collection
2. **Discover Hotspots**: Identify species, genera, and environmental niches with exceptionally high ARG prevalence
3. **Analyze Pangenome Patterns**: Compare "open" vs. "closed" pangenomes in relation to resistance gene diversity
4. **Understand Fitness Trade-offs**: Use fitness browser data to evaluate the cost of carrying resistance genes
5. **Build Predictive Models**: Develop models to predict ARG accumulation based on phylogenetic and ecological features

## Approach

### Phase 1: Data Exploration
- Explore BERDL pangenome database structure and tables
- Understand relationships between genomes, genes, orthogroups, and taxonomy
- Document schemas, row counts, and available metadata
- Identify functional annotation sources (eggNOG, KEGG, COG, PFAM)

### Phase 2: ARG Identification
- Query gene annotations from `eggnog_mapper_annotations` table
- Identify ARGs using known resistance databases (CARD, ResFinder) via keyword matching
- Cross-reference with COG and KEGG functional categories
- Build ARG annotation dataset linking genes to resistance mechanisms and drug classes
- Save curated ARG dataset for downstream analysis

### Phase 3: Distribution Analysis
- Calculate ARG prevalence metrics by:
  - Species (% genomes with ARGs, mean ARGs per genome)
  - Drug class distribution
  - Phylogenetic clade patterns
- Identify statistical outliers (hotspot species)
- Analyze patterns by environment (if metadata available)

### Phase 4: Pangenome Characterization
- Classify genes as core, accessory, or unique for each species
- Compute pangenome openness metrics
- Analyze correlation between pangenome openness and ARG diversity
- Test whether ARGs are preferentially core or accessory

### Phase 5: Fitness Analysis
- Cross-reference ARG genes with `kescience_fitnessbrowser` fitness data
- Extract fitness effects across experimental conditions
- Analyze trade-offs between resistance carriage and fitness costs
- Identify essential vs. non-essential ARGs

### Phase 6: Integration & Visualization
- Create publication-quality figures showing:
  - Top hotspot species by ARG prevalence and diversity
  - Phylogenetic distribution patterns
  - Fitness trade-off landscapes
- Build interactive dashboards for exploration
- Generate summary statistics and reports

## Data Sources

### Primary Collections
- **Pangenome** (`kbase_ke_pangenome`): 293,059 genomes across 27,690 microbial species from GTDB r214
  - Tables: `pangenome`, `gene`, `orthogroup`, `gtdb_species_clade`, and others
- **Fitness Browser** (`kescience_fitnessbrowser`): Gene fitness data from transposon mutants
  - Tables: `fitness`, `fitness_experiments`, and related tables
- **KBase Genomes** (`kbase_genomes`): Structural genomics data for detailed annotation

### External Reference Data
- CARD (Comprehensive Antibiotic Resistance Database)
- ResFinder database
- PATRIC resistance gene annotations
- GTDB taxonomy for phylogenetic context

## Project Structure

```
resistance_hotspots/
├── README.md
├── notebooks/
│   ├── 01_explore_data.ipynb
│   ├── 02_identify_args.ipynb
│   ├── 03_distribution_analysis.ipynb
│   ├── 04_pangenome_analysis.ipynb
│   ├── 05_fitness_analysis.ipynb
│   └── 06_visualization_dashboards.ipynb
├── data/
│   ├── arg_annotations.csv
│   ├── hotspot_species.csv
│   ├── fitness_results.csv
│   └── raw/
├── figures/
│   ├── arg_prevalence.png
│   ├── phylogenetic_distribution.png
│   ├── fitness_tradeoffs.png
│   └── interactive_dashboards/
└── results/
    ├── summary_statistics.txt
    └── publication_figures/
```

## Key Metrics

- **ARG Prevalence**: Percentage of genomes in a species/genus carrying specific ARGs
- **ARG Diversity**: Total number of unique ARGs per species
- **Hotspot Score**: Combined metric ranking species by ARG concentration and diversity
- **Pangenome Openness**: Measure of accessory genome size relative to core
- **Fitness Cost**: Transposon mutant fitness effect for ARG-containing genes

## Dependencies

- Python 3.11+
- PySpark for BERDL queries
- Pandas, NumPy for data analysis
- Matplotlib, Plotly for visualization
- Scikit-learn for statistical modeling
- Biopython for sequence analysis (if needed)

## References

- CARD Database: https://card.mcmaster.ca/
- ResFinder: https://www.ncbi.nlm.nih.gov/pubmed/22782694
- GTDB: https://gtdb.ecogenomic.org/
- PATRIC: https://www.patricbrc.org/

## Revision History
- **v1** (2026-02): Migrated from README.md
