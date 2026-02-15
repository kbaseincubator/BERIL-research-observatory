# Research Plan: Temporal Core Genome Dynamics

## Research Question

How does core genome composition change over sampling time? Do genes "come and go" from core status, explaining why heavily-sampled species show smaller cores?

## Hypothesis

The core genome is not static - genes transition in and out of core status over ecological/evolutionary time. Species sampled over longer time periods (decades of microbial collection) show smaller cores because:

1. **Environmental/niche shifts**: The species' lifestyle has genuinely changed over time
2. **Sampling bias evolution**: Earlier decades sampled different environments than recent ones
3. **Geographic expansion**: As sequencing became cheaper, we sampled more diverse locations
4. **True population dynamics**: Some genes really do cycle in/out of universality

## Species

| Species | Total Genomes | With Collection Dates | Coverage |
|---------|--------------|----------------------|----------|
| Pseudomonas aeruginosa | 6,760 | ~4,960 | 73.4% |
| Acinetobacter baumannii | 6,647 | ~5,021 | 75.5% |

Both species are semi-environmental (found in soil, water, biofilms) with clinical crossover, making them ideal models for temporal dynamics.

## Approach

### 1. Data Extraction
- Query BERDL for genomes with valid collection dates (1999-2021+)
- Extract gene cluster memberships for each genome
- Parse variable date formats (YYYY, YYYY-MM, YYYY-MM-DD)

### 2. Sliding Window Analysis

**Cumulative Expansion**: Sort genomes chronologically, progressively add genomes and track core erosion.

**Fixed Time Windows**: Group genomes into 2-year periods, calculate core within each window (minimum 30 genomes per window).

### 3. Core Thresholds

Compare multiple definitions to test robustness:
- 90% presence (relaxed)
- 95% presence (standard)
- 99% presence (strict)

### 4. Key Metrics
- Core size per window
- Core composition (which gene clusters are core)
- Jaccard similarity between adjacent windows
- Core turnover rate (genes entering vs leaving)
- Stable core (genes core across all windows)

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `genome` - Genome metadata
  - `ncbi_env` - Collection date metadata (attribute_name = 'collection_date')
  - `gene_cluster` - Gene family classifications
  - `gene_genecluster_junction` - Gene-to-cluster memberships
  - `gene` - Individual gene records
  - `eggnog_mapper_annotations` - Functional annotations for enrichment analysis

## Key Questions

1. **How fast does the core shrink?** - Quantify decay rate per additional genome
2. **Is shrinkage linear or asymptotic?** - Fit decay models to identify pattern
3. **Which genes leave first?** - Functional characterization of early leavers
4. **Are some genes "permanently core"?** - Identify the irreducible stable core
5. **Do both species show similar patterns?** - Compare decay rates and gene categories

## Expected Outputs

### Figures
- `core_decay_curve.png` - Core size vs cumulative genomes by collection date
- `turnover_heatmap.png` - Which genes leave core at what point
- `species_comparison.png` - P. aeruginosa vs A. baumannii decay rates
- `functional_enrichment.png` - COG categories of early-leaving genes

### Data
- `p_aeruginosa_genomes.parquet` - Genomes with parsed dates
- `a_baumannii_genomes.parquet` - Genomes with parsed dates
- `window_results.parquet` - Core sizes and compositions per window
- `core_turnover.csv` - Genes entering/leaving core over time

### Notebooks
- `01_data_extraction.ipynb` - Extract genomes with dates, gene cluster memberships
- `02_sliding_window.ipynb` - Calculate core across time windows
- `03_analysis.ipynb` - Decay curves, turnover analysis, species comparison
- `04_functional.ipynb` - COG enrichment of early-leaving vs stable core genes

## Revision History
- **v1** (2026-02): Migrated from README.md
