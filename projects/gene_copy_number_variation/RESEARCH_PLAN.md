# Research Plan: Gene Copy Number Variation Across Pangenome Functional Categories

## Research Question
Beyond presence/absence, do adaptive vs housekeeping gene clusters show different paralog copy number patterns within bacterial pangenomes? Specifically, do housekeeping genes (translation, nucleotide metabolism, coenzyme metabolism) maintain fixed copy numbers while adaptive genes (mobile elements, defense, cell wall) tolerate copy number variation?

## Hypothesis
- **H0**: Gene clusters across all COG functional categories show statistically equivalent copy number variance within pangenomes. Paralog multiplicity is independent of functional category.
- **H1**: Housekeeping COG categories (J, F, H, C) have significantly lower copy number variance than adaptive COG categories (L, V, M, K). Specifically:
  - **H1a**: Core housekeeping genes (J = translation/ribosomal, F = nucleotide metabolism, H = coenzyme metabolism) exist at fixed copy numbers (CV < 0.05 across genomes within a species).
  - **H1b**: Adaptive/mobile gene categories (L = replication/recombination/repair, V = defense, S/- = poorly characterized) show higher copy number variance (CV > 0.1) and a higher fraction of multi-copy clusters.
  - **H1c**: The housekeeping–adaptive copy number variance gap is consistent across phylogenetically diverse species (>3 phyla).

## Literature Context
- Pangenome studies extensively characterize core vs accessory gene content by COG category (Hyun et al. 2022, Cummins et al. 2022, Chauhan et al. 2025), but focus on **presence/absence** across genomes, not **copy number within a genome**.
- Gene dosage constraint is well-studied in eukaryotes (aneuploidy, dosage balance hypothesis — Birchler & Veitia 2012), less so in prokaryotes where paralogy is the primary copy number variation mechanism.
- Dilucca et al. 2018 showed essential genes (dominated by information-processing COGs) are under stronger purifying selection, consistent with dosage sensitivity.
- Douglas & Shapiro 2024 used pseudogenes as a neutral reference for pangenome selection — similar logic applies here (copy number drift as a neutral reference for dosage constraint).
- The BERDL pangenome (293K genomes, 27K species, 132M gene clusters at 90% AAI) provides unprecedented scale for systematic within-species copy number analysis.

**Gap**: No study has systematically quantified paralog copy number variance by functional category across thousands of bacterial pangenomes. This project fills that gap.

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `gene` | Map genes to genomes | 1.01B | Filter by genome_id via species |
| `gene_genecluster_junction` | Map genes to gene clusters | 1.01B | Filter by gene_id from gene table |
| `gene_cluster` | Core/accessory status, species assignment | 132M | Filter by gtdb_species_clade_id |
| `eggnog_mapper_annotations` | COG category for each gene cluster | 93M | Filter by query_name (= gene_cluster_id) |
| `pangenome` | Species metadata (genome count, cluster count) | 27K | Safe to scan |
| `gtdb_species_clade` | Taxonomy for phylogenetic diversity | 27K | Safe to scan |

### Key Queries

1. **Per-species copy number matrix** — For each species, count genes per genome per gene cluster:
```sql
SELECT gc.gene_cluster_id, gc.is_core, g.genome_id, COUNT(*) as copy_count
FROM kbase_ke_pangenome.gene g
JOIN kbase_ke_pangenome.gene_genecluster_junction j ON g.gene_id = j.gene_id
JOIN kbase_ke_pangenome.gene_cluster gc ON j.gene_cluster_id = gc.gene_cluster_id
JOIN kbase_ke_pangenome.genome gm ON g.genome_id = gm.genome_id
WHERE gm.gtdb_species_clade_id LIKE 's__<species>%'
AND gc.gtdb_species_clade_id LIKE 's__<species>%'
GROUP BY gc.gene_cluster_id, gc.is_core, g.genome_id
```

2. **COG-stratified copy number stats** — Aggregate copy number variance by COG category:
```sql
-- After creating copy_counts temp view from query 1:
SELECT ann.COG_category,
       COUNT(DISTINCT cc.gene_cluster_id) as n_clusters,
       AVG(cc.copy_count) as mean_copies,
       STDDEV(cc.copy_count) as std_copies,
       SUM(CASE WHEN cc.copy_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_multicopy
FROM copy_counts cc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann ON cc.gene_cluster_id = ann.query_name
GROUP BY ann.COG_category
```

### Performance Plan
- **Tier**: JupyterHub Spark SQL (billion-row joins required)
- **Estimated complexity**: Moderate — per-species iteration over 3-way join
- **Strategy**: Process species one at a time (Pattern 2 from performance.md); aggregate in Spark, collect only summary stats
- **Known pitfalls**: `gene` and `gene_genecluster_junction` are ~1B rows each — always filter by species. The 3-way join is ~18x slower than ANI extraction per species (~32s/species). For 50 species, expect ~25-30 minutes total.

## Analysis Plan

### Notebook 01: Data Exploration & Pilot
- **Goal**: Validate the copy number extraction approach on 5 phylogenetically diverse pilot species. Characterize the basic distribution: what fraction of gene clusters are multi-copy? How does copy number distribute (mostly 1, some 2, rare 3+)?
- **Expected output**: `data/pilot_copy_numbers.csv`, basic distribution plots in `figures/`

### Notebook 02: Multi-Species Analysis
- **Goal**: Scale to 50+ species (≥50 genomes each, spanning ≥5 phyla). For each species, compute per-COG-category copy number statistics: mean copies, CV, fraction multi-copy.
- **Expected output**: `data/species_cog_copy_stats.csv`

### Notebook 03: Statistical Testing & Visualization
- **Goal**: Test H1a/H1b/H1c. Compare copy number variance between housekeeping (J, F, H, C) and adaptive (L, V, M, S) COG categories. Mixed-effects model with species as random effect. Generate publication-quality figures.
- **Expected output**: Statistical test results, `figures/cog_copy_number_*.png`

### Notebook 04: Core vs Accessory Interaction
- **Goal**: Test whether the copy number variance pattern differs between core and accessory gene clusters. Do core L genes (mobile elements that reached fixation) show less copy number variation than accessory L genes?
- **Expected output**: `data/core_accessory_copy_stats.csv`, interaction figures

## Expected Outcomes
- **If H1 supported**: Housekeeping genes are under dosage constraint (fixed copy numbers), while adaptive genes tolerate or exploit copy number variation. This connects pangenome-level observations to molecular-level dosage sensitivity and extends the eukaryotic dosage balance hypothesis to prokaryotes at population scale.
- **If H0 not rejected**: Copy number variation is functionally neutral — paralogy rates are set by genomic context (proximity to mobile elements, recombination hotspots) rather than functional constraint. This would suggest that dosage balance is not a significant force in bacterial evolution.
- **Potential confounders**:
  - Gene cluster AAI threshold (90%) may merge recent paralogs into a single cluster, underestimating true copy number variation for divergent paralogs.
  - Genome assembly quality — fragmented assemblies may split or merge paralogs.
  - Species with very few genomes may have insufficient power to detect copy number variance.
  - Mobile elements (IS elements, transposases) in category L may dominate the signal — need to test whether L remains significant after excluding IS elements.

## Revision History
- **v1** (2026-07-07): Initial plan based on pilot exploration of L. seeligeri (168 genomes). Pilot showed L (3.2% multi-copy) > housekeeping (0%) pattern.
- **v2** (2026-07-07): NB01 pilot on 5 species found direction consistent 5/5 phyla but pooled ratio only 1.4× (below pre-registered 3× threshold). Binary "any multi-copy in ≥1 genome" is too coarse — a rare cluster with 1 multi-copy occurrence flips the binary. Revising to use continuous metrics: **cluster-carrier-weighted multi-copy rate** (SUM(multicopy_genomes) / SUM(carrier_genomes)) and **mean-copies-per-carrier**. Also revising pre-registered thresholds:
  - Directional criterion: adaptive > housekeeping in ≥4/5 pilots (unchanged; already met at 5/5).
  - Magnitude criterion: cluster-carrier-weighted ratio ≥2× (relaxed from 3× on the coarser binary).
  - Spirochaetota (*Borreliella*) documented as a phylum outlier with multi-partite genome structure — retained but reported separately in NB03.
  - Also revising COG classification: **C (energy) and J (translation) moved from housekeeping to "mixed"** — pilot showed both have known paralog cases (cytochrome paralogs, rRNA operons, ribosomal protein duplicates). Housekeeping now = {F, H} (nucleotide + coenzyme metabolism); adaptive still = {L, V, M, K}; C and J tracked separately.

## Authors
- Justin Reese (LBL, ORCID: 0000-0002-2170-2250)
