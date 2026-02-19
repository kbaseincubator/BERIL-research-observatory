# Research Plan: Metabolic Capability vs Metabolic Dependency

## Research Question

Just because a bacterium's genome encodes a complete amino acid biosynthesis or carbon utilization pathway, does the organism actually depend on it? Can we distinguish metabolic *capability* (genome predicts pathway present) from metabolic *dependency* (fitness data shows pathway genes matter)?

## Hypotheses

### H1: Capability ≠ Dependency
Not all genomically complete pathways are functionally important. A substantial fraction of "complete" pathways will show neutral fitness effects, indicating latent capabilities rather than active dependencies.

### H2: Black Queen Hypothesis
Amino acid biosynthesis pathways that are "latent capabilities" (complete but fitness-neutral) are candidates for future gene loss via the Black Queen Hypothesis. Species with more latent capabilities will have:
- More open pangenomes (ongoing streamlining)
- Higher gene turnover in pathway-related clusters
- Evidence of cross-feeding dependencies in their native environments

### H3: Metabolic Ecotypes
Within-species pathway heterogeneity defines metabolic ecotypes. Genomes from the same species but different environments will show different profiles of active dependencies vs latent capabilities, correlating with:
- Environmental metadata (isolation source, geographic location)
- AlphaEarth embeddings (niche breadth)
- Gene content clusters (already identified in ecotype_analysis)

## Approach

### Phase 1: Data Integration (NB01-02)

**NB01: Extract GapMind Pathway Data** (JupyterHub + Spark)
- Query `kbase_ke_pangenome.gapmind_pathways` (305M rows)
- For each genome-pathway pair, take the BEST score across pathway steps:
  - `complete` (5 pts), `likely_complete` (4), `steps_missing_low` (3), `steps_missing_medium` (2), `not_present` (1)
- Aggregate to genome level: count complete pathways (score ≥ 5) per genome
- Output: `data/gapmind_genome_pathways.csv` (genome_id, pathway, best_score, is_complete)

**NB02: Map Pathways to Fitness Genes** (local)
- Load FB-pangenome link table: `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv`
- Join GapMind genes with link table to get FB `(orgId, locusId)` pairs
- For each organism with pathway + fitness data:
  - Extract gene-level fitness scores from `genefitness` table
  - Compute pathway-level fitness metrics: mean |t-score|, max |t-score|, % essential genes
  - Infer essentiality: genes in `gene` table (type='1') but NOT in `genefitness`
- Output: `data/pathway_fitness_mappings.csv` (orgId, pathway, n_genes, n_essential, mean_abs_t)

### Phase 2: Pathway Classification (NB03)

**NB03: Classify Active Dependencies vs Latent Capabilities**
For each organism-pathway pair with complete prediction:
- **Active Dependency**: mean |t| > 2.0 OR >20% essential genes
- **Latent Capability**: mean |t| < 1.0 AND <5% essential genes
- **Intermediate**: Between thresholds

Statistical tests:
- Compare % active vs latent across pathway categories:
  - Amino acid biosynthesis (15 pathways)
  - Carbon source utilization (20 pathways)
  - Cofactor biosynthesis (10 pathways)
  - Others
- Chi-square test: pathway category × dependency class

Output:
- `data/pathway_classification.csv` (orgId, pathway, class, mean_abs_t, pct_essential)
- Figure: Stacked bar chart of pathway classes by category
- Figure: Scatter plot (mean |t| vs % essential) with decision boundaries

### Phase 3: Black Queen Hypothesis Test (NB04)

**NB04: Latent Capabilities Predict Gene Loss**

Approach:
- For organisms with pangenome links (n=22), map pathway genes to gene clusters
- Compute pathway conservation metrics:
  - % core genes in pathway
  - Mean conservation across pathway genes
  - Singleton gene count (putative recent losses)
- Test association: latent capabilities have LOWER conservation than active dependencies

Statistical model:
```
conservation ~ dependency_class + pathway_category + log(n_genes) + (1|organism)
```

Expected result: Active dependencies → high conservation; Latent capabilities → low conservation

Output:
- `data/pathway_conservation.csv` (orgId, pathway, class, pct_core, mean_conservation)
- Figure: Box plot of % core by dependency class
- Figure: Survival curve (conservation CDF) by dependency class

### Phase 4: Metabolic Ecotypes (NB05)

**NB05: Within-Species Pathway Heterogeneity**

For species with ≥50 genomes and ≥30 complete pathways:
1. Build genome × pathway binary matrix (complete=1, incomplete=0)
2. Cluster genomes by pathway profiles (hierarchical clustering, Jaccard distance)
3. Test association with environmental metadata:
   - Isolation source (harmonized categories from `ncbi_env`)
   - Geographic location (AlphaEarth embeddings if available)
   - Gene content clusters (from `ecotype_analysis` if species overlap)

Statistical test:
- Mantel test: pathway distance vs environment distance
- Permutation test: within-cluster environment homogeneity vs random

Output:
- `data/metabolic_ecotypes.csv` (species, genome_id, cluster_id, environment)
- Figure: Heatmap (genomes × pathways) with cluster dendrogram
- Figure: PCA of pathway profiles colored by environment

## Query Strategy

### Key BERDL Queries

**GapMind Pathways (NB01)** — Direct Spark, ~5 min runtime
```sql
WITH pathway_scores AS (
    SELECT
        genome_id,
        clade_name AS species,
        pathway,
        CASE score_category
            WHEN 'complete' THEN 5
            WHEN 'likely_complete' THEN 4
            WHEN 'steps_missing_low' THEN 3
            WHEN 'steps_missing_medium' THEN 2
            WHEN 'not_present' THEN 1
            ELSE 0
        END as score_value
    FROM kbase_ke_pangenome.gapmind_pathways
)
SELECT
    genome_id,
    species,
    pathway,
    MAX(score_value) as best_score,
    CASE WHEN MAX(score_value) >= 5 THEN 1 ELSE 0 END as is_complete
FROM pathway_scores
GROUP BY genome_id, species, pathway
```

**Fitness Data** — Use existing cached matrices from `fitness_modules/data/matrices/`
- Already extracted for 32 organisms
- Contains gene-level t-scores across all conditions
- No need to re-query Fitness Browser

**Essentiality Inference** — Query `kescience_fitnessbrowser.gene` vs `genefitness`
- Genes in `gene` (type='1') but absent from `genefitness` = putatively essential
- Already computed in `conservation_vs_fitness` project

## Expected Challenges

### Challenge 1: Sparse Fitness Coverage
Only ~30 of 48 FB organisms have pangenome links. For pathway-level analysis, we need both pathway predictions AND fitness data AND pangenome mappings. Expected final organism count: 20-25.

**Mitigation**: Focus on high-quality organisms with >1000 fitness experiments and >100 genomes in pangenome.

### Challenge 2: Pathway Granularity
GapMind pathways vary in size (3-20 genes). Small pathways may have noisy fitness aggregates. Large pathways may mix essential and dispensable steps.

**Mitigation**:
- Require ≥5 genes per pathway for classification
- Report results stratified by pathway size
- Compute both mean and max fitness metrics

### Challenge 3: Essentiality Inference is Noisy
Absence from `genefitness` doesn't guarantee essentiality (could be poor library coverage, low expression, etc.). This inflates false positives for "active dependencies."

**Mitigation**:
- Use multiple metrics (|t-score| + essentiality + condition breadth)
- Validate against literature-curated essential genes if available
- Report classification confidence scores

### Challenge 4: Within-Species Pathway Variation
Most species have <50 genomes with pathway predictions, limiting power for ecotype detection.

**Mitigation**:
- Focus on well-sampled species (E. coli, K. pneumoniae, P. aeruginosa, etc.)
- Pool related species if needed (same genus)
- Use permutation tests for significance (doesn't require large n)

## Success Criteria

**Minimum Viable Analysis:**
1. Pathway classification for ≥15 organisms
2. Demonstrate that latent capabilities exist (≥10% of complete pathways show neutral fitness)
3. Show that active dependencies are more conserved than latent capabilities (p < 0.05)

**Stretch Goals:**
1. Identify metabolic ecotypes in ≥5 species
2. Validate against environmental metadata or literature
3. Predict pathway loss events using longitudinal/comparative data

## Dependencies

### Data Files from Prior Projects
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv`
- `projects/conservation_vs_fitness/data/organism_mapping.tsv`
- `projects/fitness_modules/data/matrices/*.tsv` (fitness matrices)
- `projects/fitness_modules/data/annotations/experiment_metadata.tsv`
- `projects/ecotype_analysis/data/ecotypes_expanded/` (if species overlap)

### BERDL Access
- JupyterHub with Spark (for NB01 pathway extraction only)
- Subsequent notebooks run locally on cached data

## Timeline

- **Week 1**: NB01-02 (data extraction and integration) — 2-3 days compute time
- **Week 2**: NB03 (pathway classification and visualization) — 2-3 days analysis
- **Week 3**: NB04-05 (Black Queen test and ecotype analysis) — 3-4 days
- **Week 4**: Synthesis, figures, and writeup

Total estimated effort: 3-4 weeks

## Revision History

- **v1** (2026-02-17): Initial research plan
