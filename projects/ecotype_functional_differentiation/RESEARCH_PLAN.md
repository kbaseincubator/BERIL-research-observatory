# Research Plan: Ecotype Functional Differentiation

## Research Question
Do gene-content ecotypes within bacterial species differ in their COG functional profiles — specifically, do they show differentiation in adaptive functions (defense, transport, secondary metabolism) while sharing core metabolic functions?

## Hypothesis
- **H0**: Ecotypes within a species have indistinguishable COG functional profiles — gene content variation is functionally random.
- **H1**: Ecotypes differ in adaptive COG categories (V-Defense, P-Inorganic ion transport, G-Carbohydrate transport, E-Amino acid transport, Q-Secondary metabolites, M-Cell wall, K-Transcription) but NOT in core metabolic categories (J-Translation, F-Nucleotide metabolism, H-Coenzyme metabolism, C-Energy production).

## Literature Context
Within-species ecological differentiation (ecotypes) is well-established in microbiology but the functional architecture of this differentiation at pangenome scale remains underexplored.

**Key findings from prior work:**
- **Maistrenko et al. (2020, ISME J)**: Environmental preferences explain up to 49% of pangenome feature variance across 155 species — habitat drives pangenome structure.
- **Moulana et al. (2020, mSystems)**: COG categories P (inorganic ion transport) and S (unknown function) showed the most variation between *Sulfurovum* ecotypes at hydrothermal vents.
- **Conrad et al. (2022, ISME J)**: Only 3.5% of *Salinibacter* accessory genes are ecologically adaptive, but they encode critical osmoregulation functions.
- **Dewar et al. (2024, PNAS)**: Bacterial lifestyle (free-living vs host-associated) is a major predictor of pangenome structure.
- **Chase et al. (2019, mBio)**: Free-living soil bacteria show population structure delineated by gene flow discontinuities with flexible gene content differences driving local adaptation.
- **Brockhurst et al. (2019, Current Biology)**: Species with larger pangenomes occupy more varied ecological niches; accessory genome shaped by HGT, gene loss, and mobile element conflict.

**From the BERIL observatory:**
- `ecotype_analysis`: Phylogeny dominates gene content similarity (60.5% of 172 species), environment effects weak — but this tested whole-genome correlations, not functional category differences.
- `cog_analysis`: Universal "two-speed genome" — novel genes enriched in L (+10.88%) and V (+2.83%), core genes enriched in J (-4.65%) and F (-2.09%). Tested between-class (core/auxiliary/singleton) but NOT within-species between-ecotype.
- `ecotype_env_reanalysis`: Environmental-only species do NOT show stronger environment-gene content correlations than host-associated species.

**Gap**: No study has systematically tested whether within-species gene-content clusters (ecotypes) differ in specific COG functional categories across hundreds of species. The ecotype_analysis showed that whole-genome gene content correlates weakly with environment — but Moulana et al. suggest the signal may be concentrated in specific functional categories (P, V, M) rather than spread across the whole genome. This project tests that hypothesis at scale.

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `pangenome` | Select species with ≥50 genomes | 27,702 | Safe to scan |
| `gene_cluster` | Gene presence/absence per species, COG-linked via cluster_id | 132M | Filter by `gtdb_species_clade_id` |
| `gene_genecluster_junction` | Map gene clusters → genomes | 1B | Filter by `gene_cluster_id` within species |
| `eggnog_mapper_annotations` | COG categories per gene cluster | 93M | Join on `query_name = gene_cluster_id` |
| `genome` | Genome metadata, taxonomy | 293K | Safe to scan |

### Key Queries

1. **Species selection** (REST API safe):
```sql
SELECT gtdb_species_clade_id, no_genomes, no_gene_clusters,
       no_core_gene_clusters, no_auxiliary_gene_clusters, no_singleton_gene_clusters
FROM kbase_ke_pangenome.pangenome
WHERE no_genomes >= 50
ORDER BY no_genomes DESC
```

2. **Per-species gene cluster presence/absence matrix** (JupyterHub — large):
```sql
SELECT gc.gene_cluster_id, gc.is_core, gc.is_auxiliary, gc.is_singleton,
       j.gene_id, g.genome_id
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.gene_genecluster_junction j
  ON gc.gene_cluster_id = j.gene_cluster_id
JOIN kbase_ke_pangenome.gene g
  ON j.gene_id = g.gene_id
WHERE gc.gtdb_species_clade_id = '{species_id}'
```

3. **Per-species COG profile by gene cluster** (JupyterHub):
```sql
SELECT gc.gene_cluster_id, gc.is_core, gc.is_auxiliary, gc.is_singleton,
       ann.COG_category
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND ann.COG_category IS NOT NULL
  AND ann.COG_category != '-'
```

### Performance Plan
- **Tier**: JupyterHub (Spark) — gene_genecluster_junction is 1B rows
- **Estimated complexity**: Moderate-to-complex — need per-genome gene content matrix for clustering, then COG aggregation per cluster
- **Known pitfalls**:
  - Column is `is_auxiliary` not `is_accessory`
  - `--` in species IDs disallowed by REST API metacharacter filter; use LIKE for REST, exact equality for Spark
  - ~40% of gene clusters lack COG annotation
  - Gene clusters are species-specific — cannot compare cluster IDs across species

## Analysis Plan

### Notebook 1: Species Selection & Data Availability (NB01)
- **Goal**: Select target species, check genome counts and COG annotation coverage
- **Approach**: Query pangenome table for species with ≥50 genomes; for a sample, check COG annotation rates
- **Expected output**: `data/target_species.csv` with species IDs, genome counts, annotation coverage

### Notebook 2: Gene Content Clustering (NB02, Spark)
- **Goal**: For each target species, cluster genomes by accessory gene content to define ecotypes
- **Approach**:
  - For each species, build a genome × gene_cluster binary presence/absence matrix (accessory genes only — core genes are shared by all, singletons are noise)
  - Reduce dimensionality (PCA or UMAP on the binary matrix)
  - Cluster with HDBSCAN (handles variable cluster counts per species)
  - Quality filter: keep species with ≥2 clusters, each cluster ≥10 genomes, silhouette > 0.2
- **Expected output**: `data/ecotype_assignments.csv` with genome_id, species, cluster_id

### Notebook 3: COG Functional Profiles per Ecotype (NB03, Spark)
- **Goal**: For each ecotype cluster, compute COG category frequencies
- **Approach**:
  - For each species with valid ecotype clusters, get all gene clusters and their COG annotations
  - Compute per-ecotype COG proportions: for each ecotype, what fraction of annotated genes falls in each COG category?
  - Focus on auxiliary genes (the differentiating fraction) — core genes are shared
- **Expected output**: `data/ecotype_cog_profiles.csv`

### Notebook 4: Differential Enrichment Analysis (NB04, local)
- **Goal**: Statistical test for COG category differences between ecotypes within each species
- **Approach**:
  - For each species with ≥2 ecotypes: chi-square or Fisher's exact test per COG category
  - Multiple testing correction (BH-FDR across species × COG combinations)
  - Aggregate: which COG categories are MOST FREQUENTLY differentiated across species?
  - Test H1: adaptive categories (V, P, G, E, Q, M, K) differentiated more often than housekeeping (J, F, H, C)
  - Visualize: heatmap of differentiation strength × COG category × species
- **Expected output**: Figures in `figures/`, summary statistics

### Notebook 5: Ecological Interpretation (NB05, local)
- **Goal**: Connect COG differentiation patterns to ecological context
- **Approach**:
  - For species with the strongest ecotype-COG differentiation, characterize the differentiating genes
  - Cross-reference with NCBI environment metadata where available
  - Compare with phylum-level patterns from cog_analysis
- **Expected output**: Narrative synthesis, key examples

## Expected Outcomes
- **If H1 supported**: Ecotypes are functionally specialized — they share core metabolism but differ in niche-adaptive functions. This would mean within-species gene content variation is not random but reflects ecological adaptation at the functional level.
- **If H0 not rejected**: Gene content ecotypes exist but are not functionally coherent — variation is distributed randomly across COG categories. This would suggest ecotypes reflect drift/demography rather than functional specialization.
- **Potential confounders**:
  - Phylogenetic structure within species could drive both gene content clusters and COG profiles without ecological causation
  - COG annotation coverage (~60%) may miss adaptive genes in poorly-characterized functional categories
  - Clustering method sensitivity — different algorithms may identify different ecotypes

## Revision History
- **v1** (2026-04-27): Initial plan

## Authors
- Justin Reese (https://orcid.org/0000-0002-2170-2250), Lawrence Berkeley National Laboratory
