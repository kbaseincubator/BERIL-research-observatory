# Research Plan: Ecotype Species Screening

## Research Question

Which bacterial species are the best candidates for ecotype analysis, and can we identify them systematically using phylogenetic branch length structure and environmental diversity from harmonized biosample metadata?

## Hypothesis

- **H0 (Screening validity)**: Phylogenetic substructure (branch distance variance) is uncorrelated with environmental diversity (ENVO category entropy) across the 338 screened species — i.e., there is no joint signal that identifies ecotype candidates.
- **H1 (Screening validity)**: Species with high phylogenetic substructure have higher environmental diversity, meaning eco-geographic diversification and phylogenetic clustering co-occur and jointly predict ecotype potential.

- **H0 (Retrospective validation)**: Branch distance variance is no better than ANI variance at predicting which species showed significant environment–gene content correlations in the prior `ecotype_analysis` project.
- **H1 (Retrospective validation)**: Branch distance variance is a stronger predictor of prior ecotype signal than the ANI-based proxy, validating the use of tree-derived distances for candidate selection.

- **H0 (Coverage gap)**: High-scoring candidate species are proportionally represented in the 213 species analyzed in `ecotype_analysis` — prior work did not systematically miss candidates.
- **H1 (Coverage gap)**: High-scoring candidates are disproportionately absent from prior `ecotype_analysis` species, explaining the weak average signal: prior work lacked AlphaEarth coverage for the most ecotypically diverse species.

## Literature Context

**Ecotype theory**: Cohan (2002, *Annu Rev Microbiol*; 2006, *Phil Trans R Soc B*) defines bacterial ecotypes as ecologically cohesive populations that occupy a distinct niche and are periodically purged by selective sweeps. A productive candidate for ecotype analysis must (1) span multiple ecological niches and (2) show phylogenetic substructure consistent with ecological specialization. Identifying such candidates *a priori* is under-explored.

**Pangenome–environment relationships**: Maistrenko et al. (2020, *ISMEJ*) directly showed that both phylogenetic inertia and habitat preferences shape prokaryotic within-species diversity, with environmental specialists having more constrained pangenomes than generalists. This supports using environmental diversity as a screening criterion. Von Meijenfeldt et al. (2023, *Nat Ecol Evol*) showed generalists have more open pangenomes, linking niche breadth to gene content variation. Dewar et al. (2024, *PNAS*) confirm bacterial lifestyle shapes pangenome structure.

**Prior BERIL work**: Two prior projects tested the ecotype hypothesis across 172–224 species using AlphaEarth environmental embeddings and ANI-based phylogenetic proxies. Both found that phylogeny dominates and environment effects are weak for most species (`ecotype_analysis`; `ecotype_env_reanalysis`). However, neither project performed systematic upstream screening: species were selected for AlphaEarth coverage (28% of genomes, clinically biased) rather than ecotype potential. This project addresses that gap directly.

**Gap**: No prior BERIL analysis has used (1) actual phylogenetic branch lengths from single-copy core gene trees or (2) harmonized ENVO ontology environmental triads from `nmdc_ncbi_biosamples`. Both datasets are now available in BERDL and offer qualitatively better signal for candidate selection than AlphaEarth coverage or ANI variance.

## Approach

Score all 338 species with phylogenetic tree distance data across three independent dimensions, then combine into a composite candidate score.

### Scoring Dimensions

| Dimension | Metric | Source | Rationale |
|-----------|--------|--------|-----------|
| **Phylogenetic substructure** | Coefficient of variation of pairwise branch distances; optionally bimodality coefficient | `phylogenetic_tree_distance_pairs` | High variance → two or more distinct phylogenetic clusters → potential ecotypes |
| **Environmental diversity** | Entropy of `env_broad_scale` ENVO categories per species; count of distinct categories | `nmdc_ncbi_biosamples.env_triads_flattened` joined via `sample.ncbi_biosample_accession_id` | Broad environmental span → ecological diversification is plausible |
| **Pangenome openness** | `no_singleton_gene_clusters / no_gene_clusters` | `kbase_ke_pangenome.pangenome` | Open pangenomes have more gene content variation to study |

### Filters

- Minimum 20 genomes per species
- Exclude species where >90% of biosample environments are from a single category (uninformative for environment analysis)
- Flag (but do not exclude) species already analyzed in `ecotype_analysis` — use for retrospective validation

### Composite Score

```
composite_score = z(phylo_substructure) + z(env_diversity) + z(pangenome_openness)
```

Z-score each dimension, sum, rank descending. Output: top 50 candidates with full scoring breakdown.

### Retrospective Validation

For the 213 species in `ecotype_analysis`, compare:
- Their composite score (new) vs whether they showed significant environment–gene content partial correlation (prior result)
- AUC of branch distance variance vs ANI variance for predicting significant prior ecotype signal

## Data Sources

| Table | Database | Purpose |
|-------|----------|---------|
| `phylogenetic_tree_distance_pairs` | `kbase_ke_pangenome` | Branch length variance per species |
| `phylogenetic_tree` | `kbase_ke_pangenome` | Map tree UUIDs to species clade IDs |
| `pangenome` | `kbase_ke_pangenome` | Openness metrics, genome counts |
| `gtdb_species_clade` | `kbase_ke_pangenome` | Species taxonomy, GTDB names |
| `sample` | `kbase_ke_pangenome` | Map genome IDs to BioSample accessions |
| `env_triads_flattened` | `nmdc_ncbi_biosamples` | ENVO-harmonized environmental categories |
| `biosamples_flattened` | `nmdc_ncbi_biosamples` | isolation_source, geo_loc_name as fallback |
| `genome` | `kbase_ke_pangenome` | Link genomes to species and biosample IDs |

## Query Strategy

### Tables Required

| Table | Estimated Rows | Filter Strategy |
|-------|---------------|-----------------|
| `phylogenetic_tree_distance_pairs` | 22.6M | Filter by `phylogenetic_tree_id` (one tree per species) |
| `phylogenetic_tree` | 330 | Full scan (small) |
| `pangenome` | 27,702 | Full scan (small) |
| `sample` | 293,059 | Full scan or filter by species genome list |
| `env_triads_flattened` | Unknown | Join by BioSample accession |

### Key Queries

**1. Get all 338 tree species with branch distance stats:**
```sql
SELECT
    pt.gtdb_species_clade_id,
    pt.phylogenetic_tree_id,
    COUNT(DISTINCT pd.genome1_id) as n_genomes,
    AVG(pd.branch_distance) as mean_dist,
    STDDEV(pd.branch_distance) as std_dist,
    MAX(pd.branch_distance) as max_dist,
    MIN(pd.branch_distance) as min_dist,
    STDDEV(pd.branch_distance) / AVG(pd.branch_distance) as cv_dist
FROM kbase_ke_pangenome.phylogenetic_tree pt
JOIN kbase_ke_pangenome.phylogenetic_tree_distance_pairs pd
    ON pt.phylogenetic_tree_id = pd.phylogenetic_tree_id
GROUP BY pt.gtdb_species_clade_id, pt.phylogenetic_tree_id
```

**2. Link species genomes to BioSample accessions:**
```sql
SELECT
    g.gtdb_species_clade_id,
    s.ncbi_biosample_accession_id
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.sample s ON g.genome_id = s.genome_id
WHERE g.gtdb_species_clade_id IN (/* tree species list */)
```

**3. Get environmental diversity per species via NMDC BioSamples:**
```sql
SELECT
    accession,
    attribute,
    label,
    id as envo_id
FROM nmdc_ncbi_biosamples.env_triads_flattened
WHERE attribute = 'env_broad_scale'
  AND accession IN (/* biosample accessions for target species */)
```

Note: Genome IDs in `phylogenetic_tree_distance_pairs` are bare accessions without GTDB prefix (e.g., `GCF_000005845.2` not `RS_GCF_000005845.2`). Strip `RS_` or `GB_` prefix when joining.

### Performance Plan

- **Tier**: JupyterHub direct Spark for data extraction (NB01); local for scoring and analysis (NB02–NB04)
- **Key large table**: `phylogenetic_tree_distance_pairs` (22.6M rows) — aggregate per tree_id in Spark before collecting
- **nmdc linkage**: `env_triads_flattened` size unknown; filter to `attribute = 'env_broad_scale'` and join to species BioSample list

## Analysis Plan

### Notebook 1: Data Extraction (JupyterHub)
- **Goal**: Extract branch distance stats, pangenome stats, and BioSample links for all 338 tree species
- **Expected output**: `data/tree_species_phylo_stats.csv`, `data/tree_species_biosample_map.csv`

### Notebook 2: Environmental Diversity Scoring (local)
- **Goal**: Join BioSample accessions to NMDC env_triads, compute ENVO category entropy per species
- **Expected output**: `data/env_diversity_scores.csv`

### Notebook 3: Composite Scoring and Ranking (local)
- **Goal**: Merge all dimensions, z-score, compute composite score, rank candidates
- **Expected output**: `data/candidate_rankings.csv`, figures

### Notebook 4: Retrospective Validation (local)
- **Goal**: For the 213 prior `ecotype_analysis` species, compare composite score vs prior ecotype signal; compute AUC
- **Input**: `projects/ecotype_analysis/data/ecotype_correlation_results.csv`
- **Expected output**: `data/retrospective_validation.csv`, figures

## Expected Outcomes

- **If H1 (screening validity) supported**: Environmental diversity correlates with phylogenetic substructure — the composite score identifies a coherent set of ecotype candidates. Top 50 candidates represent a priority list for future deep-dive ecotype analyses.
- **If H0 not rejected**: Phylogenetic substructure and environmental diversity are orthogonal signals — both are needed independently, and combining them into a composite score is still justified as they measure different dimensions of ecotype potential.
- **If H1 (retrospective) supported**: Branch distance variance predicts prior ecotype signal (AUC > 0.6), validating the new metric for future screening.
- **If H1 (coverage gap) supported**: High-scorers were systematically absent from prior work due to AlphaEarth limitations — identifies specific species worth re-analyzing.
- **Potential confounders**: Clinical/host-associated species may have high phylogenetic substructure but no ecological signal (immune evasion, not ecotype). Flag species with >50% host-associated biosamples.

## Revision History

- **v1** (2026-02-21): Initial plan

## Authors

- **Mikaela Cashman** (Lawrence Berkeley National Laboratory) | ORCID: [0000-0003-0620-7830](https://orcid.org/0000-0003-0620-7830) | Author
