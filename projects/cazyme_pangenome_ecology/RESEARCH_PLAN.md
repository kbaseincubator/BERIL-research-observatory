# Research Plan: CAZyme Pangenome Ecology — Carbohydrate Metabolism Distribution Across Bacterial Biomes

## Research Question
At the scale of the MGnify Genomes catalog (49K genomes, 57K species, 18 biomes), do carbohydrate-active enzyme (CAZyme) profiles differ systematically across environments, and are CAZyme genes preferentially located in the accessory pangenome?

## Hypothesis
- **H0**: CAZyme class composition and density are uniform across biomes after controlling for phylogeny and genome size.
- **H1**: CAZyme class composition differs significantly by biome — specifically, GH (glycoside hydrolases) enriched in fiber-rich environments (rumen, soil) vs marine; GT (glycosyl transferases) enriched in soil (EPS/biofilm biosynthesis).
- **H2**: CAZyme gene density is positively correlated with pangenome openness (cloud gene fraction), consistent with CAZymes being frequently acquired via HGT for niche-specific carbohydrate exploitation.

## Literature Context
- Pudlo et al. 2022 (mSystems) showed CAZyme diversity drives within-species phenotypic diversification in gut Bacteroidales — single-clade, not pan-bacterial.
- Sun et al. 2023 (Front Microbiol) showed polymeric carbohydrate utilization separates marine microbiome niches — single environment.
- Andrade et al. 2017 (Genet Mol Biol) compared freshwater and soil CAZyme metagenomes — community-level, not genome-resolved.
- No published study has compared genome-resolved CAZyme profiles across 18 biomes at 49K-genome scale.

## Query Strategy

### Tables Required
| Database.Table | Purpose | Rows | Filter Strategy |
|---|---|---|---|
| `kescience_mgnify.genome_cazy` | Per-genome CAZy class gene counts | 345K | No filter needed (small table) |
| `kescience_mgnify.genome` | GTDB taxonomy, biome, genome quality, genome_type | 518K | Filter to genomes with CAZy data |
| `kescience_mgnify.species` | Species-level representative metadata | 57K | Join on species_id |
| `kescience_mgnify.pangenome_stats` | Core/shell/cloud gene counts per species | 16K | Join on species_id |
| `arkinlab_dbcan.fam_substrate_mapping` | CAZy family-to-substrate reference | 1K | Reference table |

### Key Queries
1. **Genome-level CAZy profiles**:
```sql
SELECT g.genome_id, g.biome_id, g.lineage, g.length, g.completeness,
       g.genome_type, g.species_id, c.cazy_family, c.gene_count
FROM kescience_mgnify.genome g
JOIN kescience_mgnify.genome_cazy c ON g.genome_id = c.genome_id
WHERE g.completeness >= 50
```

2. **Species-level CAZy + pangenome openness**:
```sql
SELECT s.species_id, s.biome_id, s.gtdb_phylum, s.genome_count,
       p.total_genes, p.core_genes, p.cloud_genes,
       (p.cloud_genes / p.total_genes) as cloud_fraction
FROM kescience_mgnify.species s
JOIN kescience_mgnify.pangenome_stats p ON s.species_id = p.species_id
WHERE s.genome_count >= 3
```

### Performance Plan
- **Tier**: Local bounded Spark SQL
- **Estimated complexity**: Simple (all tables <500K rows)
- **Known pitfalls**: None documented for kescience_mgnify (first use)

## Analysis Plan

### Notebook 01: Data Extraction and QC
- **Goal**: Extract genome-level CAZy profiles with metadata. Quality-filter genomes (completeness >= 50%). Characterize biome × phylum × genome_type distribution.
- **Expected output**: `data/genome_cazy_profiles.tsv`, `data/sample_summary.tsv`

### Notebook 02: CAZy Class Composition by Biome
- **Goal**: Test H1. Compare CAZy class distributions across biomes. Kruskal-Wallis + post-hoc Dunn's test for each class. PERMANOVA on multivariate CAZy profiles. Control for genome size and phylogeny (phylum as covariate). Visualize with heatmap and boxplots.
- **Expected output**: `figures/cazy_biome_heatmap.png`, `data/biome_tests.tsv`

### Notebook 03: CAZy Density and Pangenome Openness
- **Goal**: Test H2. Join species-level CAZy means with pangenome_stats. Correlate GH/GT/total CAZy density with cloud_fraction. Control for genome_count (sampling effort) and phylum. Partial correlation and linear regression.
- **Expected output**: `figures/cazy_vs_openness.png`, `data/openness_correlation.tsv`

### Notebook 04: Phylogenetic Distribution and Biome Specialists
- **Goal**: Map CAZy profiles onto GTDB taxonomy. Identify phyla with unusual CAZy compositions. Find biome-specialist species (high CAZy in one biome, low in others). Compare Isolate vs MAG CAZy profiles as bias control.
- **Expected output**: `figures/cazy_phylum_tree.png`, `data/biome_specialists.tsv`

### Notebook 05: Synthesis
- **Goal**: Integrate findings across H1 and H2. Draft key figures for REPORT.md. Summarize ecological rules.
- **Expected output**: Summary figures, statistical tables

## Expected Outcomes
- **If H1 supported**: CAZy composition reflects substrate availability in each environment (fiber in rumen/soil → GH enrichment; EPS/biofilm in soil → GT enrichment). Provides genome-resolved confirmation of metagenome-level patterns (Andrade 2017, Sun 2023).
- **If H0 not rejected**: CAZy class composition is phylogenetically constrained and biome-invariant — environment selects species, not enzyme repertoire. Would strengthen the phylogeny-drives-everything narrative from ecotype_env_reanalysis.
- **If H2 supported**: CAZymes are part of the mobilome — frequently gained/lost for niche exploration. Links to the HGT signature (L enrichment) found in cog_analysis and the prophage-AMR co-mobilization findings.
- **Potential confounders**: Genome completeness (MAGs missing CAZy genes), genome size (larger genomes have more of everything), biome sampling bias (56% human-gut/mouse-gut), phylogenetic autocorrelation.

## Revision History
- **v1** (2026-05-21): Initial plan

## Authors
- Justin Reese, Lawrence Berkeley National Laboratory (ORCID: 0000-0002-2170-2250)
