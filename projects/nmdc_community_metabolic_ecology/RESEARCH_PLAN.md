# Research Plan: Community Metabolic Ecology via NMDC × Pangenome Integration

## Research Question

Do the GapMind-predicted pathway completeness profiles of community resident taxa predict or
correlate with observed metabolomics profiles in NMDC environmental samples across diverse
habitat types?

## Hypothesis

- **H0**: Community pathway completeness does not significantly correlate with metabolomics
  profiles after controlling for environment type and study identity.
- **H1**: Communities with higher community-weighted completeness for amino acid biosynthesis
  will show lower detected amino acid concentrations in metabolomics (Black Queen dynamics at
  community scale).
- **H2**: Community metabolic potential (mean GapMind pathway completeness) clusters by
  environment type (soil vs sediment vs marine) more strongly than taxonomic composition alone.

## Literature Context

**What is known:**
- Noecker et al. (2016, *mSystems*) showed that metabolic models integrating microbiome
  taxonomic profiles with genome-scale metabolic reconstructions can predict variation in
  metabolomics profiles in the gut microbiome. Their approach used full genome-scale models
  rather than pathway completeness scores.
- Mallick et al. (2019, *Nature Communications*) demonstrated that metagenomic functional
  profiles predict community metabolomics across multiple body sites (gut, skin, oral), using
  PICRUSt-style inferred metagenomes from 16S amplicon data.
- Danczak et al. (2020, *Nature Communications*) proposed using metacommunity ecology
  frameworks to understand environmental metabolome composition, noting that community assembly
  processes govern which metabolites accumulate or are consumed.
- The "Black Queen Hypothesis" (Morris et al. 2012) predicts that metabolic functions become
  leaky in dense communities, with some taxa losing biosynthetic genes when other community
  members overproduce the metabolite. This predicts a negative correlation between community-
  level biosynthetic completeness and metabolite pool size.

**What is unknown / gap:**
- No study has used GapMind pathway completeness scores — which provide species-level
  predictions across 27,690 pangenome species — to test whether community-weighted metabolic
  potential predicts environmental metabolomics.
- Cross-habitat analysis (soil, sediment, marine, freshwater) at NMDC scale has not been done
  with genome-predicted pathway completeness.
- Whether the Black Queen dynamic is detectable at the scale of diverse environmental
  communities using paired metabolomics + pangenome pathway data is untested.

## Query Strategy

### Tables Required

| Table | Database | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|---|
| `study_table` | `nmdc_arkin` | Study definitions + environment type | 48 | Full scan safe |
| `taxonomy_features` | `nmdc_arkin` | Per-sample taxonomic profiles | 6,365 samples | Full scan safe |
| `kraken_gold` | `nmdc_arkin` | Kraken-based classifications (species level) | Unknown | Filter by sample |
| `centrifuge_gold` | `nmdc_arkin` | Centrifuge classifications | Unknown | Filter by sample |
| `metabolomics_gold` | `nmdc_arkin` | Measured metabolomics per sample | 3,129,061 | Filter by sample + annotated compounds |
| `abiotic_features` | `nmdc_arkin` | Environmental measurements (pH, temp, etc.) | ~6,365 | Full scan safe |
| `metabolomics_gold` columns | `nmdc_arkin` | Metabolite KEGG/ChEBI IDs — verify column names in NB01 (annotation_terms_unified stores gene-annotation terms, NOT compound IDs) | — | Inspect in NB01 |
| `gtdb_species_clade` | `kbase_ke_pangenome` | GTDB taxonomy bridge | 27,690 | Full scan safe |
| `gapmind_pathways` | `kbase_ke_pangenome` | Pathway completeness per genome | 305,471,280 | Filter by pathway + clade |
| `pangenome` | `kbase_ke_pangenome` | Per-species aggregate stats | 27,702 | Full scan safe |

### Key Queries

**1. NMDC sample inventory with study metadata:**
```sql
SELECT s.study_id, s.ecosystem_category, s.ecosystem_type,
       COUNT(DISTINCT tf.sample_id) as n_samples_with_taxa,
       COUNT(DISTINCT mg.sample_id) as n_samples_with_metabolomics
FROM nmdc_arkin.study_table s
LEFT JOIN nmdc_arkin.taxonomy_features tf ON tf.sample_id LIKE CONCAT(s.study_id, '%')
LEFT JOIN nmdc_arkin.metabolomics_gold mg ON mg.sample_id LIKE CONCAT(s.study_id, '%')
GROUP BY s.study_id, s.ecosystem_category, s.ecosystem_type
ORDER BY n_samples_with_taxa DESC
```

**2. Samples with BOTH taxonomic profiles AND metabolomics:**
```sql
SELECT tf.sample_id
FROM nmdc_arkin.taxonomy_features tf
JOIN nmdc_arkin.metabolomics_gold mg ON tf.sample_id = mg.sample_id
GROUP BY tf.sample_id
```

**3. GapMind species-level pathway completeness (two-stage aggregation):**
```sql
WITH best_scores AS (
    SELECT clade_name, genome_id, pathway,
           MAX(CASE score_category
               WHEN 'complete' THEN 5
               WHEN 'likely_complete' THEN 4
               WHEN 'steps_missing_low' THEN 3
               WHEN 'steps_missing_medium' THEN 2
               WHEN 'not_present' THEN 1
               ELSE 0 END) as best_score
    FROM kbase_ke_pangenome.gapmind_pathways
    GROUP BY clade_name, genome_id, pathway
),
genome_pathway_complete AS (
    SELECT clade_name, genome_id,
           SUM(CASE WHEN best_score >= 5 THEN 1 ELSE 0 END) as n_complete,
           SUM(CASE WHEN best_score >= 4 THEN 1 ELSE 0 END) as n_likely_complete,
           COUNT(DISTINCT pathway) as n_total_pathways
    FROM best_scores
    GROUP BY clade_name, genome_id
)
SELECT clade_name,
       AVG(n_complete) as mean_complete_pathways,
       STDDEV(n_complete) as std_complete_pathways,
       AVG(n_likely_complete) as mean_likely_complete_pathways,
       COUNT(DISTINCT genome_id) as n_genomes
FROM genome_pathway_complete
GROUP BY clade_name
```

**4. Per-pathway species-level completeness (for Black Queen test on amino acids):**
```sql
WITH best_scores AS (
    SELECT clade_name, genome_id, pathway, metabolic_category,
           MAX(CASE score_category
               WHEN 'complete' THEN 5
               WHEN 'likely_complete' THEN 4
               WHEN 'steps_missing_low' THEN 3
               WHEN 'steps_missing_medium' THEN 2
               WHEN 'not_present' THEN 1
               ELSE 0 END) as best_score
    FROM kbase_ke_pangenome.gapmind_pathways
    WHERE metabolic_category = 'amino_acid'
    GROUP BY clade_name, genome_id, pathway, metabolic_category
)
SELECT clade_name, pathway, metabolic_category,
       AVG(best_score) as mean_score,
       AVG(CASE WHEN best_score >= 5 THEN 1.0 ELSE 0.0 END) as frac_complete
FROM best_scores
GROUP BY clade_name, pathway, metabolic_category
```

### Performance Plan

- **Tier**: BERDL JupyterHub (Spark SQL required for NB01–NB03; NB04–NB05 can run locally
  from cached data)
- **Estimated complexity**: Moderate
  - NMDC tables: small-medium (safe to full-scan taxonomy/abiotic; filter metabolomics by
    sample)
  - GapMind: 305M rows; use two-stage aggregation pattern from `pangenome_pathway_geography`
    (10–15 min runtime)
- **Known pitfalls**:
  - GapMind has multiple rows per genome-pathway pair — always GROUP BY and MAX score first
    (see `docs/pitfalls.md` [pangenome_pathway_geography] section)
  - NMDC taxonomy resolution: need to inspect `kraken_gold` and `centrifuge_gold` to determine
    if species-level classifications are available; ENIGMA was genus-level only, NMDC may be
    better
  - String-typed numeric columns in NMDC tables — CAST before comparisons
  - `nmdc_arkin` has 60+ tables; many row counts unknown; verify before querying

## Analysis Plan

### Notebook 01: NMDC Schema Exploration and Sample Inventory (`01_nmdc_exploration.ipynb`)
- **Goal**: Characterize NMDC samples with paired taxonomy + metabolomics; understand
  taxonomic classification depth; profile metabolomics annotation rates and compound coverage
- **Requires**: BERDL JupyterHub (Spark)
- **Expected outputs**:
  - `data/nmdc_sample_inventory.csv` — samples with taxonomy + metabolomics, study metadata,
    ecosystem type
  - `data/nmdc_classifier_comparison.csv` — per-classifier summary statistics (3 rows: kraken,
    centrifuge, gottcha); species-rank fraction and file counts per classifier
  - `data/nmdc_metabolomics_coverage.csv` — per-sample compound counts, annotation rates
  - `figures/nmdc_sample_coverage_SUPERSEDED.png` — Venn diagram of sample overlap and ecosystem
    type distribution (generated before `omics_files_table` bridge; shows 0 overlap; superseded
    by `bridge_quality_distribution.png`)
- **Key decisions**: Which taxonomy table (kraken_gold vs centrifuge_gold vs gottcha_gold vs
  taxonomy_features) provides the most species-level resolution? What fraction of metabolomics
  compounds carry KEGG/ChEBI compound IDs in their own columns?
- **Required schema verification steps (first cells of NB01)**:
  1. `DESCRIBE nmdc_arkin.study_table` — confirm `study_id`, `ecosystem_category`,
     `ecosystem_type` columns exist before building dependent queries
  2. `DESCRIBE nmdc_arkin.taxonomy_features` — confirm sample ID format, abundance column
     name, and whether values are relative abundances or raw read counts (normalization step
     needed if raw)
  3. `DESCRIBE nmdc_arkin.metabolomics_gold` — confirm column names for compound IDs
     (KEGG/ChEBI); `annotation_terms_unified` is a gene-annotation table and cannot serve as
     a metabolite compound lookup
  4. Inspect raw `study_id` and `sample_id` values to determine whether sample IDs are
     actually prefixed with study IDs before building LIKE joins in Query 1
  5. Compare species-level classification rates across kraken_gold, centrifuge_gold, and
     gottcha_gold; also check `nmdc_ncbi_biosamples.env_triads_flattened` for structured
     `env_broad_scale / env_local_scale / env_medium` fields as a supplement for ecosystem
     type categorization

### Notebook 02: Taxonomy Bridge — NMDC Taxa to GTDB Species (`02_taxonomy_bridge.ipynb`)
- **Goal**: Map NMDC taxonomic classifications to GTDB species in `gtdb_species_clade`;
  compute bridge quality per sample; identify bridge coverage thresholds
- **Requires**: BERDL JupyterHub (Spark) + cached taxonomy data from NB01
- **Expected outputs**:
  - `data/taxon_bridge.tsv` — NMDC taxon → GTDB species clade mappings with confidence tiers
    (exact, genus-level, family-level)
  - `data/bridge_quality.csv` — per-sample fraction of community abundance mapped to
    pangenome
  - `figures/bridge_quality_distribution.png` — distribution of bridge coverage per sample
- **Methodology**: Follow taxonomy bridge approach from
  `enigma_contamination_functional_potential` (NB02). Map by normalized genus/species name
  matching to `kbase_ke_pangenome.gtdb_species_clade`. Flag samples below 30% coverage.
- **Pitfall**: ENIGMA was genus-only; NMDC Kraken may provide species-level — test both
  depths and report which gives higher coverage.

### Notebook 03: Community Pathway Completeness Matrix (`03_pathway_completeness.ipynb`)
- **Goal**: Compute community-weighted GapMind pathway completeness scores per NMDC sample;
  produce sample × pathway completeness matrix
- **Requires**: BERDL JupyterHub (Spark) + bridge from NB02 + GapMind species data
- **Expected outputs**:
  - `data/species_pathway_completeness.csv` — GapMind completeness per GTDB species per
    pathway (output of species-level aggregation query above; ~27K species × 80 pathways)
  - `data/community_pathway_matrix.csv` — per-sample community-weighted completeness per
    pathway (~N_samples × 80 pathways)
  - `figures/pathway_completeness_heatmap.png` — heatmap of mean completeness by pathway ×
    ecosystem type
- **Methodology**:
  1. Extract species-level pathway completeness from GapMind (use query 3 above)
  2. For each sample, join community taxon abundances with species pathway completeness
  3. Compute community-weighted mean completeness per pathway:
     `completeness_pathway_p_sample_s = Σ(rel_abund_taxon_i × completeness_taxon_i_pathway_p)`

### Notebook 04: Metabolomics Processing (`04_metabolomics_processing.ipynb`)
- **Goal**: Extract and normalize NMDC metabolomics data; map compounds to KEGG pathways
  (especially amino acids); merge with community pathway matrix and abiotic features
- **Requires**: Local (from cached NB01 data) OR Spark if metabolite KEGG mapping requires
  joining back to BERDL
- **Expected outputs**:
  - `data/metabolomics_matrix.csv` — per-sample normalized metabolite abundances for
    annotated compounds
  - `data/amino_acid_metabolites.csv` — subset: amino acid compounds with KEGG IDs
  - `data/analysis_ready_matrix.csv` — merged: community pathway completeness + metabolomics
    + abiotic features, for samples passing bridge coverage threshold
  - `figures/metabolomics_distribution.png` — per-compound abundance distributions by
    ecosystem type
- **Metabolite lookup note**: Compound-to-KEGG mapping must come from `metabolomics_gold`
  own columns (to be verified in NB01). `annotation_terms_unified` in `nmdc_arkin` stores
  COG/EC/GO/KEGG gene-annotation terms, NOT metabolite compound IDs. If metabolomics_gold
  lacks compound annotations, plan B is to filter by compound name matching (amino acid
  names via string search).
- **Abiotic features note**: All columns in `abiotic_features` are string-typed (e.g.,
  `annotations_ph`, `annotations_temp_has_numeric_value`). CAST to FLOAT before any
  numeric comparisons or correlations.

### Notebook 05: Statistical Analysis (`05_statistical_analysis.ipynb`)
- **Goal**: Test H0, H1, H2; report correlations, partial correlations, and environment-type
  clustering
- **Requires**: Local (from analysis_ready_matrix)
- **Expected outputs**:
  - `data/correlation_results.csv` — per-pathway: Spearman ρ between community completeness
    and metabolite abundance, raw p + BH-FDR q
  - `data/partial_correlation_results.csv` — controlled for study ID and ecosystem type
  - `data/black_queen_test.csv` — amino acid pathway completeness vs amino acid metabolomics:
    effect sizes and significance
  - `data/environment_clustering.csv` — cluster membership (community pathway vector) vs
    ecosystem type
  - `figures/correlation_heatmap.png` — completeness vs metabolomics correlation by pathway
  - `figures/black_queen_scatter.png` — scatter: mean AA biosynthesis completeness vs mean
    AA metabolomics per sample
  - `figures/environment_clustering.png` — UMAP/PCA of community pathway profiles colored by
    ecosystem type

## Expected Outcomes

- **If H1 supported (negative correlation for AA biosynthesis)**: Evidence that Black Queen
  dynamics operate at community scale; communities that have invested in complete biosynthetic
  pathways have lower free amino acid pools because they produce and use internally.
- **If H0 not rejected**: Pathway completeness as computed from pangenome predictions does not
  predict observed metabolomics — suggests measurement noise, bridge quality issues, or that
  community-level metabolomics is too coarse to detect biosynthetic signals.
- **If H2 supported (environment type clustering)**: Community metabolic potential is
  organized by habitat, consistent with metabolic niche theory; adds functional context to
  taxonomic biogeography.
- **Potential confounders**: Metabolomics technical variation across NMDC studies; abiotic
  factors (pH, temperature, dissolved oxygen) dominating metabolomics variance; incomplete
  taxonomy bridge (lowering effective sample size); GapMind predictions may not reflect actual
  expression.

## Revision History

- **v1** (2026-02-19): Initial plan — NMDC × Pangenome cross-database integration; community
  metabolic ecology via Black Queen hypothesis test
- **v2** (2026-02-19): NB01 revealed that classifier tables (`centrifuge_gold`, `kraken_gold`,
  `gottcha_gold`) and `metabolomics_gold` use non-overlapping `file_id` namespaces
  (`nmdc:dobj-11-*` vs `nmdc:dobj-12-*`) and share **zero direct overlap by file_id**.
  Pairing requires a `file_id → sample_id` bridge table (to be found in NB02 via full scan
  of `nmdc_arkin`). The NB02 goal was updated to: (1) find this bridge, (2) enumerate
  samples with both omics types, then (3) proceed with GTDB species mapping.
  Centrifuge confirmed as best classifier (61.3% species-rank rows vs 48.9% Kraken,
  44.1% GOTTCHA). Taxon column for centrifuge is `label` (not `name`).

## Authors

- **Christopher Neely** | ORCID: 0000-0002-2620-8948 | Author
