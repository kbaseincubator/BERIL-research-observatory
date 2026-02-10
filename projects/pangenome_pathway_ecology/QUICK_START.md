# Quick Start Guide: Pangenome Openness, Pathways & Distances

## Project Overview

Analyze how open vs. closed pangenomes correlate with metabolic pathway completeness and phylogenetic/structural distances.

**Database**: `kbase_ke_pangenome` on BERDL
**Key Tables**:
- `pangenome` - Species-level pangenome stats (27,690 species)
- `gapmind_pathways` - Metabolic pathway predictions for genomes
- `alphaearth_embeddings_all_years` - Structural embeddings (~28% of genomes)
- `phylogenetic_tree_distance_pairs` - Phylogenetic distances

## How to Run Analysis

### Local Setup
```bash
cd projects/pangenome_pathway_ecology
```

### On BERDL JupyterHub

1. **Upload notebooks**:
   - Go to https://hub.berdl.kbase.us
   - Upload `notebooks/` folder to your workspace
   - Place in: `~/workspace/projects/pangenome_pathway_ecology/`

2. **Run exploration**:
   - Open `notebooks/01_data_exploration.ipynb`
   - Kernel → Restart & Run All
   - Download outputs from `data/` and `figures/` folders

3. **Follow-on analysis**:
   - `02_pangenome_openness.ipynb` - Metrics and distributions
   - `03_pathway_analysis.ipynb` - Correlation with GapMind
   - `04_structural_distances.ipynb` - AlphaEarth embeddings
   - `05_phylogenetic_analysis.ipynb` - Phylogenetic context

## Key Metrics

### Pangenome Openness Score
```
openness = (auxiliary_genes + singleton_genes) / total_genes
```
- **0** = Completely closed (all genes core)
- **1** = Completely open (no core genes)
- Typical range: 0.2 - 0.8

### Data Availability
- **Pangenome stats**: All 27,690 species ✓
- **GapMind pathways**: Most genomes ✓
- **AlphaEarth embeddings**: ~28% of genomes (82K/293K)
- **Phylogenetic distances**: Available for species pairs ✓

## Common BERDL Queries

### Get species openness
```sql
SELECT
  s.GTDB_species,
  p.no_genomes,
  (p.no_aux_genome + p.no_singleton_gene_clusters) / p.no_gene_clusters AS openness
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
WHERE p.no_genomes >= 10
ORDER BY openness DESC
```

### Get pathway scores for a species
```sql
SELECT
  g.genome_id,
  gp.pathway,
  gp.score,
  gp.score_simplified
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gapmind_pathways gp
  ON g.genome_id = gp.genome_id
WHERE g.gtdb_species_clade_id = 's__Species_name--RS_GCF_123'
```

## Data Outputs

Generated files in `data/`:
- `species_pangenome_openness.csv` - All species openness scores
- `target_species_for_analysis.csv` - Selected species with good coverage
- `species_pathway_profiles.csv` - Pathway completion by species (later)
- `pathway_openness_correlations.csv` - Correlation results (later)

## Important Notes

1. **Species IDs**: Use exact equality with backticks: `` WHERE id = 's__Species--RS_GCF_123' ``
2. **Large tables**: Always filter `genome` (293K rows) before use
3. **AlphaEarth coverage**: Only ~28% of genomes - plan for missing data
4. **Slow queries**: AlphaEarth embeddings table is large - use with filters
5. **Gene clusters**: Species-specific - cannot compare across species

## Documentation References

- See `../../docs/schema.md` for full table schemas
- See `../../docs/pitfalls.md` for SQL gotchas
- See `../../PROJECT.md` for workflow instructions

## Contact & Attribution

Tag discoveries with: `[pangenome_pathway_ecology]`
Update central docs in `../../docs/` when learning something shareable!
