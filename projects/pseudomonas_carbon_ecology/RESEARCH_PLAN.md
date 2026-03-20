# Research Plan: Carbon Source Utilization Predicts Ecology and Lifestyle in Pseudomonas

## Research Question
Among free-living *Pseudomonas* clades, does the carbon source utilization profile (as predicted by GapMind) predict the soil ecosystem type from which strains were isolated? And do clades that have transitioned to host-associated lifestyles show predictable losses of specific carbon pathways?

## Hypothesis
- **H0a**: Carbon source utilization profiles do not differ between *Pseudomonas* strains from different soil ecosystem types (agricultural, rhizosphere, forest, aquatic).
- **H1a**: Free-living *Pseudomonas* clades from different soil ecosystems have distinct carbon pathway profiles — e.g., rhizosphere strains retain more sugar and aromatic utilization pathways than aquatic strains.

- **H0b**: Host-associated *Pseudomonas* clades (clinical *P. aeruginosa*) have the same carbon pathway repertoire as free-living clades (*P. fluorescens*, *P. putida* groups).
- **H1b**: Host-associated clades show convergent loss of specific carbon pathways (sugars, plant-derived compounds) while retaining amino acid catabolism, reflecting metabolic specialization to host environments.

## Literature Context

The *Pseudomonas* genus spans an extraordinary ecological range — from versatile soil saprophytes to chronic lung pathogens. Key prior work:

- **Loper et al. (2012)**: Ten *P. fluorescens* group genomes revealed ~54% of the genus pan-genome resides in variable regions encoding diverse carbon utilization and secondary metabolite pathways, tailored to specific ecological niches.
- **La Rosa et al. (2018)**: Longitudinal tracking of *P. aeruginosa* in CF lungs showed convergent metabolic specialization — different lineages independently lost carbon source catabolism while specializing on amino acids.
- **Rossi et al. (2021, Nature Rev Microbiol)**: Comprehensive review documenting that chronic *P. aeruginosa* infection involves loss of metabolic versatility, motility, and environmental sensing.
- **Guo et al. (2026)**: Genus-level pangenome of 15 Pseudomonas species showed hydrocarbon degradation genes concentrated in the accessory genome; *P. putida*/*P. citronellolis* had the largest catabolic repertoires while *P. aeruginosa* showed a narrower metabolic specialization.
- **Okumura et al. (2025)**: Pan-genome analysis of 320 genomes classified Pseudomonas into four major groups with distinct metabolic profiles; *P. aeruginosa* group was more streamlined than plant-associated groups.

**Gap**: No study has systematically quantified carbon pathway profiles across the full breadth of *Pseudomonas* species (433 clades, 12,727 genomes) using standardized pathway prediction (GapMind), or tested whether these profiles are predictive of isolation environment at scale.

## Data Sources

### BERDL Tables
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.pangenome` | Pseudomonas species list, pangenome stats | 433 rows | `WHERE gtdb_species_clade_id LIKE 's__Pseudomonas_%'` |
| `kbase_ke_pangenome.gapmind_pathways` | Carbon pathway predictions per genome | ~10M rows (Pseudomonas subset) | `WHERE clade_name LIKE 's__Pseudomonas_%' AND metabolic_category = 'carbon'` |
| `kbase_ke_pangenome.genome` | Genome-to-species mapping | ~12.7K rows | `WHERE gtdb_species_clade_id LIKE 's__Pseudomonas_%'` |
| `kbase_ke_pangenome.ncbi_env` | Isolation source metadata (EAV format) | ~8.5K genomes with data | Join via `sample.ncbi_biosample_accession_id` |
| `kbase_ke_pangenome.gtdb_metadata` | Assembly quality, ncbi_isolation_source | 12.7K rows | `WHERE accession IN (Pseudomonas genomes)` |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | GTDB subgenus classification | 12.7K rows | Join via `genome.gtdb_taxonomy_id` |

### Key Data Characteristics
- **433 Pseudomonas species clades** across 5 GTDB subgenera:
  - *Pseudomonas* sensu stricto (aeruginosa group): 19 species, 6,905 genomes
  - *Pseudomonas_E* (fluorescens/putida group): 398 species, 5,687 genomes
  - *Pseudomonas_B*, *_F*, *_H*: 16 species, 135 genomes
- **62 GapMind carbon pathways** (sugars, amino acids, organic acids, alcohols, aromatics)
- **Isolation source coverage**: 67% of genomes have ncbi_env isolation_source; needs harmonization into ecological categories

## Query Strategy

### Key Queries

1. **Extract genome-level GapMind carbon pathway profiles**:
```sql
WITH best_scores AS (
    SELECT clade_name, genome_id, pathway,
           MAX(CASE score_category
               WHEN 'complete' THEN 5
               WHEN 'likely_complete' THEN 4
               WHEN 'steps_missing_low' THEN 3
               WHEN 'steps_missing_medium' THEN 2
               WHEN 'not_present' THEN 1
               ELSE 0
           END) as best_score
    FROM kbase_ke_pangenome.gapmind_pathways
    WHERE clade_name LIKE 's__Pseudomonas_%'
      AND metabolic_category = 'carbon'
    GROUP BY clade_name, genome_id, pathway
)
SELECT clade_name, genome_id, pathway, best_score
FROM best_scores
```

2. **Extract and harmonize isolation sources**:
```sql
SELECT g.genome_id, g.gtdb_species_clade_id,
       ne.content as isolation_source,
       m.ncbi_isolation_source as gtdb_isolation_source
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.sample s ON g.genome_id = s.genome_id
LEFT JOIN kbase_ke_pangenome.ncbi_env ne
    ON s.ncbi_biosample_accession_id = ne.accession
    AND ne.harmonized_name = 'isolation_source'
JOIN kbase_ke_pangenome.gtdb_metadata m ON g.genome_id = m.accession
WHERE g.gtdb_species_clade_id LIKE 's__Pseudomonas_%'
```

### Performance Plan
- **Tier**: JupyterHub Spark (gapmind_pathways is 305M rows; Pseudomonas subset ~10M)
- **Estimated complexity**: Moderate — two-stage aggregation on gapmind, then join with metadata
- **Known pitfalls**:
  - GapMind has multiple rows per genome-pathway pair; must take MAX score per pair
  - ncbi_env is EAV format; pivot by harmonized_name
  - String-typed numeric columns; CAST before comparison

## Analysis Plan

### Notebook 1: Data Extraction (`01_data_extraction.ipynb`)
- **Goal**: Extract and cache all Pseudomonas data needed for analysis
- **Steps**:
  1. Extract all 433 Pseudomonas species with pangenome stats
  2. Extract genome-level GapMind carbon pathway best scores (genome x pathway matrix)
  3. Extract isolation source metadata for all Pseudomonas genomes
  4. Extract GTDB taxonomy (subgenus assignments)
- **Expected output**: `data/pseudomonas_species.csv`, `data/carbon_pathway_scores.csv`, `data/isolation_sources.csv`, `data/taxonomy.csv`

### Notebook 2: Environment Harmonization (`02_environment_harmonization.ipynb`)
- **Goal**: Classify genomes into ecological categories from free-text isolation sources
- **Steps**:
  1. Keyword-based classification into categories: soil, rhizosphere, aquatic/freshwater, marine, clinical/human, animal, plant surface, food/dairy, industrial, other
  2. Aggregate to species-level: for each species, determine majority environment and environment diversity
  3. Classify species as "free-living" (soil, water, rhizosphere) vs "host-associated" (clinical, animal) vs "plant-associated" vs "mixed"
  4. Validate classification against known Pseudomonas ecology from literature
- **Expected output**: `data/genome_environment.csv`, `data/species_lifestyle.csv`

### Notebook 3: Carbon Pathway Profiles by Lifestyle (`03_pathway_lifestyle_analysis.ipynb`)
- **Goal**: Test H1b — do host-associated clades lose specific carbon pathways?
- **Steps**:
  1. Compute species-level pathway completeness: fraction of genomes with each pathway complete/likely_complete
  2. Compare pathway profiles between GTDB subgenera (Pseudomonas s.s. vs Pseudomonas_E)
  3. Compare pathway profiles between lifestyle categories (free-living vs host-associated)
  4. Identify specific pathways that are differentially present (Mann-Whitney U, FDR-corrected)
  5. Heatmap of pathway presence across species, ordered by lifestyle
- **Expected output**: `data/species_pathway_profiles.csv`, `figures/pathway_heatmap.png`, `figures/pathway_loss_barplot.png`

### Notebook 4: Predicting Ecology from Carbon Profiles (`04_ecology_prediction.ipynb`)
- **Goal**: Test H1a — can carbon profiles predict environment type among free-living clades?
- **Steps**:
  1. Subset to free-living species with sufficient genome count (>=10 genomes, clear environmental classification)
  2. PCA/UMAP of species-level carbon pathway profiles
  3. Test whether environment categories cluster in pathway space (PERMANOVA)
  4. Random forest classifier: predict environment category from pathway profile
  5. Identify which pathways are most discriminating (feature importance)
- **Expected output**: `data/free_living_prediction.csv`, `figures/pathway_pca_by_environment.png`, `figures/rf_importance.png`

### Notebook 5: Synthesis and Visualization (`05_synthesis.ipynb`)
- **Goal**: Integrate results, produce summary figures
- **Steps**:
  1. Summary figure: Pseudomonas genus tree colored by pathway richness and lifestyle
  2. Pathway gain/loss model: which pathways are "core Pseudomonas" vs "lifestyle-specific"?
  3. Within-species pathway variation: do some species show heterogeneous pathway profiles (metabolic ecotypes)?
  4. Compare findings with literature predictions
- **Expected output**: `figures/summary_figure.png`, `figures/core_vs_variable_pathways.png`

## Expected Outcomes
- **If H1a supported**: Carbon pathway profiles predict soil ecosystem type — rhizosphere specialists retain plant sugar degradation; aquatic strains retain organic acid pathways. This implies metabolic niche partitioning is a major axis of Pseudomonas diversification.
- **If H0a not rejected**: Pathway profiles are phylogenetically structured but not predictive of ecosystem type — phylogeny rather than ecology drives carbon utilization.
- **If H1b supported**: Host-associated clades (especially P. aeruginosa) show loss of plant-derived sugar pathways (arabinose, xylose, cellobiose, rhamnose) while retaining amino acid catabolism. This would quantify the "metabolic specialization" previously described qualitatively.
- **If H0b not rejected**: Pathway presence is uniform across the genus — GapMind may lack resolution to detect lifestyle-associated variation.

## Potential Confounders
- **Sampling bias**: P. aeruginosa is massively overrepresented (6,760/12,727 genomes = 53%) due to clinical importance
- **Isolation source quality**: Free-text, unstandardized; harmonization may introduce classification errors
- **GapMind resolution**: Limited to 62 carbon pathways; may miss genus-specific catabolic capabilities (e.g., aromatic degradation via meta-cleavage)
- **Phylogenetic signal**: Pathway profiles may simply recapitulate taxonomy (subgenus = lifestyle) rather than revealing independent ecological signal

## Revision History
- **v1** (2026-03-20): Initial plan based on data exploration and literature review
  - 433 Pseudomonas species, 62 carbon pathways, 67% environment metadata coverage
  - Confirmed GTDB subgenus structure captures free-living vs host-associated split

## Authors
- Mar Andrew Miller ([ORCID: 0000-0001-9076-6066](https://orcid.org/0000-0001-9076-6066))
