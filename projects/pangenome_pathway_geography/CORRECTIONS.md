# Analysis Corrections Summary

## Problems Identified

### 1. Pathway Data Misinterpretation

**Original Problem:**
- The initial analysis counted all 80 GapMind pathways for every species
- Looked for `score_category = 'present'` which doesn't exist in the data
- Result: Every species showed 80 pathways with 0% present

**Root Cause:**
- GapMind has **exactly 80 pathways** total (amino acids, cofactors, etc.)
- Each genome-pathway pair has **MULTIPLE rows** (one per step/component)
- Score categories are: `complete`, `likely_complete`, `steps_missing_low`, `steps_missing_medium`, `not_present`

**Correct Approach:**
```sql
-- Take BEST score for each genome-pathway pair
WITH pathway_scores AS (
    SELECT
        genome_id, pathway,
        MAX(score_value) as best_score  -- Multiple rows → best score
    FROM gapmind_pathways
    GROUP BY genome_id, pathway
)
-- Then aggregate to species level
SELECT
    species,
    AVG(complete_pathways) as mean_complete,
    STDDEV(complete_pathways) as std_complete
FROM genome_pathway_stats
GROUP BY species
```

### 2. AlphaEarth Analysis Focus

**Original Problem:**
- Focused primarily on geographic distance (latitude/longitude)
- Treated AlphaEarth embeddings as secondary to geography

**Issue:**
- AlphaEarth embeddings capture **ECOLOGICAL** context, not just geography
- Geographic distance doesn't necessarily correlate with ecological difference
- Embedding distance is the primary measure of niche breadth

**Correct Approach:**
- Use **embedding distance** as the main niche breadth metric
- Calculate **embedding variance** across genomes within species
- Combine distance + variance into a **niche breadth score**
- Geographic distance is supplementary, not primary

## Key Metrics (Revised)

### Pangenome Openness
- **Accessory/Core Ratio**: `no_aux_genome / no_core`
- **Core Fraction**: `no_core / no_gene_clusters`
- **Singleton Ratio**: `no_singleton_gene_clusters / no_gene_clusters`

### Pathway Completeness (CORRECTED)
- **Mean Complete Pathways**: Average number of complete pathways per genome (out of 80 total)
- **Pathway Variability (Std Dev)**: Intra-species variation in pathway completeness
- **Likely Complete**: Pathways with `complete` OR `likely_complete` status

### Niche Breadth (REVISED)
- **Mean Embedding Distance**: Pairwise Euclidean distance between 64D AlphaEarth vectors
- **Embedding Variance**: Variance across embedding dimensions (ecological diversity)
- **Niche Breadth Score**: `mean_distance × (1 + variance)` - combines both aspects
- Geographic distance: Secondary metric for context

## Data Availability

| Metric | Species Count | Coverage |
|--------|--------------|----------|
| Pangenome stats | 27,690 | 100% |
| Pathway completeness | 27,690 | 100% |
| AlphaEarth embeddings (≥5 genomes) | ~2,159 | 7.8% |
| **Complete dataset** | **~2,159** | **7.8%** |

## Revised Hypotheses

### H1: Pangenome → Pathway Completeness
**Original**: Open pangenomes have more pathways
**Revised**: Open pangenomes have MORE VARIABLE pathway completeness (higher std dev)

**Rationale**: Accessory genes enable niche-specific metabolic capabilities, leading to intra-species heterogeneity.

### H2: Niche Breadth → Pathway Completeness
**Original**: Geographic range correlates with pathway count
**Revised**: Broader ecological niches (high embedding diversity) correlate with higher mean pathway completeness

**Rationale**: Diverse ecological contexts require more complete metabolic toolkits.

### H3: Pangenome → Niche Breadth
**Original**: Open pangenomes correlate with geographic range
**Revised**: Open pangenomes correlate with ecological niche breadth (embedding diversity)

**Rationale**: Pangenome flexibility enables adaptation to diverse ecological niches.

## Expected Results

Based on the corrected analysis, we expect:

1. **Pathway completeness range**: 0-80 pathways (not uniform 80 for all species)
2. **Mean completeness**: Likely 20-60 pathways complete (varies by lifestyle)
3. **Strong signals**:
   - Niche breadth → pathway completeness (positive)
   - Pangenome openness → pathway variability (positive)
4. **Weaker signals**:
   - Pangenome openness → mean pathway completeness (unclear direction)
   - Geographic distance vs embedding distance (may diverge)

## Files Updated

### Created
- `notebooks/01_data_extraction_REVISED.ipynb` - Corrected pathway aggregation
- `notebooks/02_comparative_analysis_REVISED.ipynb` - Corrected hypotheses and metrics
- `CORRECTIONS.md` - This document

### Deprecated
- `notebooks/01_data_extraction.ipynb` - ❌ Incorrect pathway counting
- `notebooks/02_comparative_analysis.ipynb` - ❌ Wrong assumptions

## Next Steps

1. **Run revised notebooks** on BERDL JupyterHub
2. **Verify pathway metrics** look reasonable (mean < 80, variation exists)
3. **Analyze correlations** with corrected data
4. **Interpret results** in biological context

## Key Learnings

1. **Always inspect raw data** before aggregating
2. **Understand score categories** in annotated databases
3. **Multiple rows per entity** is common in relational data (need GROUP BY)
4. **Embedding distances** capture more than geography alone
5. **Variance/std dev** can be as important as mean values
