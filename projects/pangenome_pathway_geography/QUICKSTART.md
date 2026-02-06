# Quick Start Guide

## Project Overview

This project analyzes the relationships between:
1. **Pangenome openness** (core vs. accessory genes)
2. **Metabolic pathway diversity** (gapmind predictions)
3. **Biogeographic distribution** (AlphaEarth embeddings)

## Running the Analysis

### Step 1: Upload Notebooks to BERDL JupyterHub

1. Navigate to [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us)
2. Authenticate with your KBase credentials
3. Create a project directory:
   ```bash
   mkdir -p ~/workspace/pangenome_pathway_geography
   ```
4. Upload the notebooks from `notebooks/` directory:
   - `01_data_extraction.ipynb`
   - `02_comparative_analysis.ipynb`

### Step 2: Run Data Extraction (on JupyterHub)

**Estimated runtime**: 10-20 minutes

1. Open `01_data_extraction.ipynb`
2. Run all cells: Kernel → Restart & Run All
3. This will:
   - Extract pangenome statistics for 27,690 species
   - Aggregate gapmind pathway data to species level (305M rows)
   - Calculate biogeographic metrics from AlphaEarth embeddings (83K genomes)
   - Save datasets to `../data/` directory

**Expected outputs**:
- `data/pangenome_metrics.csv` (~27K species)
- `data/pathway_diversity.csv` (~27K species)
- `data/biogeography_metrics.csv` (~2-3K species with ≥5 genomes)
- `data/integrated_dataset.csv` (merged dataset)
- `data/alphaearth_genome_embeddings.csv` (~83K genomes)

### Step 3: Download Data Files

After notebook execution completes:

1. In JupyterHub file browser, navigate to `pangenome_pathway_geography/data/`
2. Select all CSV files
3. Download using the Download button
4. Place downloaded files in your local `projects/pangenome_pathway_geography/data/` directory

**Git note**: Large CSV files are gitignored. Small summary files (<10MB) can be committed.

### Step 4: Run Analysis Notebook (on JupyterHub or locally)

**Estimated runtime**: 5-10 minutes

1. Open `02_comparative_analysis.ipynb`
2. Run all cells: Kernel → Restart & Run All
3. This will:
   - Load integrated dataset
   - Test correlations between pangenome, pathways, and geography
   - Generate visualizations
   - Perform stratified analysis by phylum

**Expected outputs**:
- `figures/pangenome_vs_pathways.png`
- `figures/geography_vs_pathways.png`
- `figures/pangenome_vs_geography.png`
- `figures/phylum_stratified_analysis.png`

### Step 5: Interpret Results

Review the correlation analyses to test the three hypotheses:

1. **H1: Pangenome Openness → Pathway Diversity**
   - Look for positive correlation between accessory/core ratio and pathway count
   - Control for genome count

2. **H2: Geographic Range → Pathway Diversity**
   - Look for positive correlation between geodesic distance and pathway count
   - Check if AlphaEarth distances match geodesic patterns

3. **H3: Pangenome Openness → Geographic Range**
   - Look for positive correlation between accessory/core ratio and geographic distance
   - Test if open pangenomes are more dispersed

## Data Availability

| Dataset | Records | Coverage | Notes |
|---------|---------|----------|-------|
| Pangenome | 27,690 species | 100% | Complete for all species |
| Pathways | ~27K species | ~100% | Gapmind predictions available |
| AlphaEarth | 83,287 genomes | 28% | Filtered to species with ≥5 genomes |
| **Integrated** | ~2-3K species | ~10% | All three data types |

## Key Challenges

### 1. AlphaEarth Coverage
- Only 28% of genomes have embeddings
- **Solution**: Focus on species with ≥5 genomes with embeddings
- **Impact**: Reduces dataset to ~2-3K species

### 2. Pathway Data Volume
- 305M rows in `gapmind_pathways` table
- **Solution**: Aggregate to species level using Spark SQL
- **Runtime**: 5-10 minutes on JupyterHub

### 3. Confounding Variables
- Genome count varies widely across species
- **Solution**: Include as covariate in analyses
- **Approach**: Calculate normalized metrics (e.g., pathways per genome)

## Next Steps

After running the initial analysis:

1. **Refine species selection**
   - Identify species with high-quality data across all three dimensions
   - Consider minimum thresholds (e.g., ≥10 genomes, ≥5 with embeddings)

2. **Deep dive on outliers**
   - Species with open pangenomes but few pathways
   - Species with narrow geography but high pathway diversity
   - Investigate biological explanations

3. **Stratified analyses**
   - By phylum (Proteobacteria, Firmicutes, Actinobacteriota)
   - By environment (marine, terrestrial, host-associated)
   - By lifestyle (free-living vs pathogen)

4. **Manuscript preparation**
   - Document significant correlations
   - Generate publication-quality figures
   - Write methods and results sections

## Questions or Issues?

- Check `README.md` for detailed project description
- Review BERDL skill documentation: `.claude/skills/berdl/SKILL.md`
- Consult `docs/pitfalls.md` for common SQL gotchas
- Update `docs/discoveries.md` with any interesting findings

## Citation

This analysis uses data from:
- **GTDB r214**: Pangenome classifications
- **GapMind**: Metabolic pathway predictions
- **AlphaEarth**: Geospatial embeddings for microbial genomes
