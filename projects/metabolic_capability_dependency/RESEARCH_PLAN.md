# Research Plan: Metabolic Capability vs Dependency

## Research Question

Just because a bacterium's genome encodes a complete biosynthesis or catabolic pathway, does the organism actually depend on it? Can we distinguish metabolic *capability* (genome predicts pathway present) from metabolic *dependency* (fitness data shows pathway genes matter)?

## Hypothesis

- **H0**: GapMind pathway completeness is independent of pathway gene fitness importance — predicted-complete pathways are equally likely to contain fitness-important and fitness-neutral genes.
- **H1**: Predicted-complete pathways partition into two distinct classes:
  - **Active dependencies** — complete pathway + fitness-important genes (disruption causes growth defect)
  - **Latent capabilities** — complete pathway + fitness-neutral genes (pathway is genomically present but experimentally dispensable)

### Secondary Hypotheses

- **H2 (Black Queen)**: Species with more "latent capabilities" have more open pangenomes — ongoing genome streamlining removes dispensable pathways over evolutionary time.
- **H3 (Metabolic ecotypes)**: Within-species variation in pathway completeness defines metabolic ecotypes that correlate with pangenome structure (core vs accessory pathway genes).

## Literature Context

### GapMind Pathway Prediction
GapMind (Price et al., 2020) provides automated annotation of amino acid biosynthesis (18 pathways) and carbon source utilization (62 compounds) for bacterial genomes. It uses experimentally characterized proteins rather than transitive annotations, and scores pathways as complete, likely_complete, steps_missing_low/medium, or not_present. BERDL has GapMind predictions for all 293K genomes across 80 pathways.

### Fitness-Pathway Connection (Direct Precedent)
Price et al. (2018) used RB-TnSeq fitness data to identify novel enzymes filling 9 of 11 gaps in amino acid biosynthesis — directly demonstrating that fitness data can validate and extend genomic pathway predictions. This project scales that approach to all 33 linked FB organisms.

### Black Queen Hypothesis
Morris et al. (2012) proposed that gene loss can be adaptive when community members provide "leaked" metabolic products. Pathways that are genomically present but fitness-neutral (our "latent capabilities") are prime candidates for future Black Queen gene loss.

### Rare Gene Essentiality
Seif et al. (2025) showed that 9.4% of rare metabolic genes in E. coli are essential in at least one host environment, and 41% of strains depend on at least one rare essential metabolic gene. This highlights that essentiality is context-dependent — a gene neutral in lab media may be critical in a host niche.

### Pangenome and Lifestyle
McInerney et al. (2024) demonstrated that bacterial lifestyle shapes pangenome structure. Our work extends this by asking whether lifestyle also determines which pathways are active dependencies vs latent capabilities.

### Key References
1. Price MN et al. (2020). "GapMind: Automated Annotation of Amino Acid Biosynthesis." *mSystems* 5(3). DOI: 10.1128/mSystems.00291-20
2. Price MN et al. (2018). "Filling gaps in bacterial amino acid biosynthesis pathways with high-throughput genetics." *PLOS Genetics* 14(1). DOI: 10.1371/journal.pgen.1007147
3. Morris JJ et al. (2012). "The Black Queen Hypothesis: Evolution of Dependencies through Adaptive Gene Loss." *mBio* 3(2). DOI: 10.1128/mBio.00036-12
4. Seif Y et al. (2025). "Rare metabolic gene essentiality is a determinant of microniche adaptation in E. coli." *PLOS Pathogens*. DOI: 10.1371/journal.ppat.1013775
5. Boon E et al. (2024). "Machine learning analysis of RB-TnSeq fitness data predicts functional gene modules in P. putida." *mSystems*. DOI: 10.1128/msystems.00942-23

## Approach

### Phase 1: Data Integration (Notebooks 01-02)
Link GapMind pathway predictions to Fitness Browser organisms via the existing FB-pangenome bridge.

### Phase 2: Pathway Classification (Notebook 03)
For each organism-pathway pair, classify as: active dependency, latent capability, or absent.

### Phase 3: Cross-Species Patterns (Notebook 04)
Test hypotheses H2 and H3 at the pangenome and species level.

### Phase 4: Visualization & Synthesis (Notebook 05)
Summary figures and statistical validation.

## Data Sources

### Existing Assets (Reusable)
| File | Source Project | Content | Rows |
|------|--------------|---------|------|
| `conservation_vs_fitness/data/fb_pangenome_link.tsv` | conservation_vs_fitness | FB gene → pangenome cluster mapping | 177,863 |
| `conservation_vs_fitness/data/organism_mapping.tsv` | conservation_vs_fitness | FB org → GTDB clade | 44 organisms |
| `conservation_vs_fitness/data/essential_genes.tsv` | conservation_vs_fitness | Gene essentiality classification | 153,143 |
| `fitness_effects_conservation/data/fitness_stats.tsv` | fitness_effects_conservation | Per-gene fitness summary | ~194K |

### New Extractions Required
| Table | Source | Purpose | Estimated Rows | Filter Strategy |
|-------|--------|---------|----------------|-----------------|
| `gapmind_pathways` | `kbase_ke_pangenome` | Pathway predictions for FB-linked genomes | ~30K (33 orgs × ~80 pathways × ~10 genomes) | Filter by genome_id IN (FB-linked genomes) |
| `gapmind_pathways` (all species) | `kbase_ke_pangenome` | Species-level pathway heterogeneity | 305M → 27K species summary | Aggregate via Spark SQL |
| `genefitness` | `kescience_fitnessbrowser` | Per-gene fitness by condition | ~27M → filtered to pathway genes | Filter by orgId + locusId |
| `gene_cluster` + `eggnog_mapper_annotations` | `kbase_ke_pangenome` | EC/KEGG annotations for pathway-gene mapping | Filtered to 33 clades | Filter by gtdb_species_clade_id |

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| `kbase_ke_pangenome.gapmind_pathways` | Pathway predictions per genome | 305M total; ~500K for 33 FB species | Filter by genome_id |
| `kescience_fitnessbrowser.genefitness` | Gene fitness scores | 27M | Filter by orgId |
| `kbase_ke_pangenome.gene_cluster` | Core/accessory status | 132M | Filter by gtdb_species_clade_id |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | EC numbers for pathway-gene linking | 93M | Filter by query_name |
| `kbase_ke_pangenome.pangenome` | Openness metrics | 27K | Full scan OK |

### Key Queries

1. **GapMind pathway scores for FB organisms** (JupyterHub Spark):
```sql
SELECT gp.genome_id, gp.pathway, gp.metabolic_category,
       gp.score_category, gp.score, gp.nHi, gp.nMed, gp.nLo
FROM kbase_ke_pangenome.gapmind_pathways gp
WHERE gp.genome_id IN ({fb_genome_ids})
```

2. **Best pathway score per genome-pathway pair** (aggregation):
```sql
WITH scored AS (
    SELECT genome_id, pathway, metabolic_category,
           CASE score_category
               WHEN 'complete' THEN 5
               WHEN 'likely_complete' THEN 4
               WHEN 'steps_missing_low' THEN 3
               WHEN 'steps_missing_medium' THEN 2
               WHEN 'not_present' THEN 1
               ELSE 0
           END as score_value
    FROM kbase_ke_pangenome.gapmind_pathways
    WHERE genome_id IN ({fb_genome_ids})
)
SELECT genome_id, pathway, metabolic_category,
       MAX(score_value) as best_score
FROM scored
GROUP BY genome_id, pathway, metabolic_category
```

3. **Fitness aggregation for pathway genes** (REST API or Spark):
```sql
SELECT orgId, locusId,
       CAST(fit AS FLOAT) as fit,
       CAST(t AS FLOAT) as t_score
FROM kescience_fitnessbrowser.genefitness
WHERE orgId = '{org_id}'
  AND locusId IN ({pathway_locus_ids})
```

### Performance Plan
- **Tier**: JupyterHub (Spark SQL) for data extraction; local for analysis
- **Estimated complexity**: Moderate — reuses existing link table, new GapMind extraction
- **Known pitfalls**:
  - GapMind has multiple rows per genome-pathway pair (must MAX aggregate)
  - FB fitness values are strings (must CAST to FLOAT)
  - Gene cluster IDs are species-specific (use EC/KEGG for cross-species comparison)
  - Score categories are: complete, likely_complete, steps_missing_low, steps_missing_medium, not_present (NOT a binary 'present' flag)

## Analysis Plan

### Notebook 01: Data Assembly (`01_data_assembly.ipynb`)
- **Goal**: Load existing assets + extract GapMind data for FB-linked organisms
- **Inputs**: `fb_pangenome_link.tsv`, `organism_mapping.tsv`, `essential_genes.tsv`, `fitness_stats.tsv`
- **New extraction**: GapMind pathway scores for genomes in 33 FB-linked species
- **Expected output**: `data/organism_pathway_scores.csv` — per-organism, per-pathway completeness for reference genomes
- **Requires**: BERDL JupyterHub (Spark SQL)

### Notebook 02: Pathway-Gene Linking (`02_pathway_gene_linking.ipynb`)
- **Goal**: Map GapMind pathway steps to FB genes via EC numbers / KEGG orthologs
- **Method**:
  1. Extract EC numbers from `eggnog_mapper_annotations` for FB-linked gene clusters
  2. Map EC numbers to GapMind pathway steps (GapMind annotates which EC fulfills each step)
  3. Link pathway steps → gene clusters → FB genes → fitness scores
- **Expected output**: `data/pathway_gene_fitness.csv` — each row = (organism, pathway, gene, fitness_category, pathway_score)
- **Requires**: BERDL JupyterHub (Spark SQL)

### Notebook 03: Pathway Classification (`03_pathway_classification.ipynb`)
- **Goal**: Classify each organism-pathway as active dependency, latent capability, or absent
- **Method**:
  1. For each organism-pathway: compute pathway completeness score AND aggregate fitness importance of pathway genes
  2. Fitness importance: fraction of pathway genes with |mean fitness| > 1 in any condition
  3. Classification matrix:
     - **Active dependency**: pathway complete/likely_complete AND ≥1 pathway gene is fitness-important
     - **Latent capability**: pathway complete/likely_complete AND no pathway genes are fitness-important
     - **Absent**: pathway not_present or steps_missing
  4. Statistical test: Are active dependencies enriched in amino acid vs carbon source pathways?
- **Expected output**: `data/pathway_classifications.csv`, `figures/pathway_classification_heatmap.png`
- **Runs locally** (no Spark needed)

### Notebook 04: Cross-Species Patterns (`04_cross_species_patterns.ipynb`)
- **Goal**: Test H2 (Black Queen) and H3 (metabolic ecotypes)
- **Method**:
  1. **H2 test**: Correlate fraction of "latent capabilities" per organism with pangenome openness (singleton/total ratio). Spearman correlation + permutation test.
  2. **H3 test**: For species with multiple genomes in pangenome, compute intra-species pathway completeness variance. Correlate with pangenome openness.
  3. **Scaling**: Aggregate GapMind data for all 27K species (reuse pangenome_pathway_geography extraction). Compute pathway heterogeneity = std(complete_pathways) across genomes.
  4. Control for genome count as covariate (species with more genomes may show more variation by sampling alone).
- **Expected output**: `data/cross_species_analysis.csv`, `figures/openness_vs_latent_capabilities.png`, `figures/pathway_heterogeneity_vs_openness.png`
- **Runs locally** (uses pre-extracted data)

### Notebook 05: Summary Visualization (`05_summary_figures.ipynb`)
- **Goal**: Publication-quality figures summarizing key findings
- **Figures**:
  1. Heatmap: organisms × pathways colored by classification (active/latent/absent)
  2. Scatter: pangenome openness vs fraction latent capabilities
  3. Bar chart: amino acid vs carbon pathways — active vs latent proportions
  4. Violin: fitness effect distribution for genes in active vs latent pathways
  5. Species-level: pathway heterogeneity vs openness (27K species)
- **Runs locally**

## Expected Outcomes

- **If H1 supported**: Pathways partition into active dependencies and latent capabilities. Latent capabilities represent genomic "insurance" or evolutionary relics en route to Black Queen loss. This would be the first systematic classification at pangenome scale.
- **If H0 not rejected**: Pathway completeness predicts fitness importance uniformly — GapMind predictions are functionally reliable and pathways aren't "latent." Still valuable as a validation of GapMind at scale.
- **If H2 supported**: Species with more latent capabilities have more open pangenomes, supporting Black Queen dynamics in pangenome evolution.
- **If H3 supported**: Within-species pathway variation defines metabolic ecotypes, connecting metabolic function to pangenome structure.

### Potential Confounders
- **Media-dependent essentiality**: FB fitness measured in specific lab conditions; a "latent" pathway may be essential in a different environment (per Seif et al. 2025)
- **Pathway prediction accuracy**: GapMind false positives (predicted complete but actually broken) or false negatives
- **Gene-pathway mapping gaps**: Not all GapMind steps map cleanly to FB genes via EC numbers
- **Genome count bias**: Species with more genomes may show more pathway variation by sampling alone
- **Phylogenetic non-independence**: Closely related organisms may share pathway profiles non-independently

## Revision History
- **v1** (2026-02-17): Initial plan

## Authors
- Sierra Moxon (ORCID: 0000-0002-8719-7760), Lawrence Berkeley National Laboratory / KBase
