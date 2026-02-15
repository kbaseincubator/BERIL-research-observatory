# Research Plan: Ecotype Correlation Analysis

## Research Question

What drives gene content similarity between bacterial genomes: **environmental similarity** or **phylogenetic relatedness**? When genomes from similar environments share similar gene content, is it because they adapted to the same niche, or because they inherited genes from a common ancestor?

## Hypothesis

Environmental similarity should predict gene content similarity even after controlling for phylogenetic distance. If bacteria adapt their gene repertoires to their ecological niches, genomes from similar environments should share more genes than expected from their evolutionary relationships alone.

## Approach

1. **Select target species**: Identify species with sufficient genome count (50-500) and environmental embedding coverage from AlphaEarth
2. **Extract distance matrices** for each species:
   - **Environment distance**: Cosine distance between AlphaEarth 64-dimensional embeddings
   - **Phylogenetic distance**: 100 - ANI (Average Nucleotide Identity)
   - **Gene content distance**: Jaccard distance between gene cluster presence/absence profiles
3. **Compute correlations**:
   - Raw correlation: environment vs gene content
   - Partial correlation: environment vs gene content, controlling for phylogeny
   - Partial correlation: phylogeny vs gene content, controlling for environment
4. **Compare across ecological categories**: Stratify by pathogen/commensal/environmental lifestyle

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `alphaearth_embeddings_all_years` - Environmental embeddings (64-dim vectors)
  - `genome_ani` - Pairwise ANI between genomes
  - `gene_genecluster_junction` - Gene-to-cluster memberships
  - `gtdb_species_clade` - Species taxonomy

## Revision History
- **v1** (2026-02): Migrated from README.md
