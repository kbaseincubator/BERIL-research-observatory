# Research Plan: COG Functional Category Analysis

## Research Question

How do COG (Clusters of Orthologous Groups) functional category distributions differ across core, auxiliary, and novel genes in bacterial pangenomes?

## Hypothesis

Novel genes may have different functional profiles compared to core genes:
- **Core genes**: Expected to be enriched in essential functions (translation, metabolism, cell processes)
- **Auxiliary genes**: Expected to show intermediate patterns
- **Novel genes**: May be enriched in mobile elements, defense mechanisms, or poorly characterized functions

## Approach

1. Query the `kbase_ke_pangenome` database for gene cluster information
2. Extract COG functional category annotations from `eggnog_mapper_annotations` table
3. Classify genes based on their gene_cluster attributes:
   - **Core**: `is_core = 1` (present in most/all genomes)
   - **Auxiliary**: `is_auxiliary = 1` AND `is_singleton = 0` (present in some genomes)
   - **Singleton/Novel**: `is_singleton = 1` (present in only one genome)
4. Compare COG category distributions across these three classes
5. Calculate enrichment/depletion of each COG category in novel vs core genes
6. Visualize results with heatmaps and bar plots

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `gene_cluster` - Gene family classifications (core/auxiliary/singleton)
  - `gene_genecluster_junction` - Links genes to their clusters
  - `eggnog_mapper_annotations` - Functional annotations including COG categories
  - `pangenome` - Per-species pangenome statistics
  - `gtdb_species_clade` - Species taxonomy

## Implementation Notes

### SQL Notes
- **Species IDs**: Species IDs contain `--` (e.g., `s__Escherichia_coli--RS_GCF_000005845.2`), but this is NOT a problem when using exact equality in WHERE clauses since the `--` is inside the quoted string
- **Performance**: Use exact equality (`WHERE id = 'value'`) rather than `LIKE 'pattern%'` for best performance
- **Large Species**: Species with >1000 genomes may have slower queries. Species with 100-500 genomes provide good balance of statistics and performance

### Analysis Workflow

The analysis is implemented in `notebooks/cog_analysis.ipynb`:

1. **Species Selection**: Query for well-represented species (100-500 genomes)
2. **Cluster Statistics**: Count gene clusters by class for the selected species
3. **COG Queries**: Run separate queries for each gene class to get COG distributions
4. **Data Integration**: Combine results and calculate proportions within each class
5. **Visualization**:
   - Heatmap showing COG proportions across gene classes
   - Bar plots showing top enriched/depleted categories in novel genes
6. **Statistical Summary**: Report total genes analyzed and key enrichments

### Running the Analysis

**Prerequisites**: Run notebooks on the BERDL JupyterHub where Spark is available.

```bash
cd projects/cog_analysis/notebooks
jupyter notebook cog_analysis.ipynb
```

**Important**: All notebooks require Spark session initialization. Add this at the top of each notebook:
```python
from get_spark_session import get_spark_session
spark = get_spark_session()
```

Execute all cells. The notebook will:
- Query BERDL database directly using Spark SQL
- Save results to `../data/cog_distributions.csv`
- Generate visualizations in `../data/`

## Revision History
- **v1** (2026-02): Migrated from README.md
