# Research Plan: Pan-Bacterial AMR Gene Landscape

## Research Question

What is the distribution, conservation, phylogenetic structure, functional context, and environmental association of antimicrobial resistance (AMR) genes across 27,000 bacterial species pangenomes — and what does this reveal about the ecology and evolution of resistance?

## Hypotheses

### H1: Conservation
- **H0**: AMR genes show the same core/accessory/singleton distribution as the pangenome average (~47% core, ~53% accessory).
- **H1**: AMR genes are enriched in the accessory genome, reflecting conditional selection dependent on antibiotic exposure.

### H2: Phylogenetic distribution
- **H0**: AMR gene density is evenly distributed across bacterial phyla.
- **H1**: AMR genes are concentrated in specific lineages (e.g., Pseudomonadota, Bacillota) and correlate with pangenome openness.

### H3: Functional context
- **H0**: AMR genes are functionally isolated — no enrichment in co-occurring metabolic or regulatory functions.
- **H1**: AMR clusters are enriched near membrane transport, cell wall biosynthesis, and secondary metabolism genes (defense islands).

### H4: Environmental signal
- **H0**: AMR gene prevalence is independent of isolation environment.
- **H1**: Species from host-associated environments (especially clinical) carry more and different AMR genes than environmental isolates.

### H5: Annotation depth
- **H0**: AMR gene clusters are as well-annotated as the genome average.
- **H1**: A subset of AMR clusters are "AMR-only" — detected by AMRFinderPlus but lacking other functional annotations, representing novel or poorly characterized resistance mechanisms.

### H6: Fitness cost
- **H0**: AMR genes in Fitness Browser organisms have neutral fitness effects.
- **H1**: AMR genes impose measurable fitness costs in standard lab conditions, consistent with their accessory status.

## Literature Context

AMR is typically studied one pathogen at a time (e.g., CARD, NDARO, ResFinder). Pan-bacterial surveys exist (e.g., Crofts et al. 2017 Nat Rev Micro, Larsson & Flach 2022 Nat Rev Micro) but are review-based, not data-driven across thousands of species. The BERDL pangenome collection — with AMRFinderPlus annotations on 132M gene cluster representatives — enables the first truly comprehensive, pangenome-aware AMR landscape analysis.

Key gaps we can address:
- **Conservation**: How often are AMR genes core vs accessory? Prior work focused on individual pathogens.
- **Scale**: No prior study has mapped AMR across 27K species with uniform annotation.
- **Integration**: Combining AMR with pangenome structure, functional annotations, fitness data, and environmental metadata in one analysis.

*Note: Formal literature review will be conducted during analysis and added as a revision.*

## Query Strategy

### Tables Required

| Table | Purpose | Rows | Filter Strategy |
|---|---|---|---|
| `bakta_amr` | AMR annotations on cluster reps | 83K | Safe to full scan |
| `gene_cluster` | Core/aux/singleton flags, species ID | 132M | Filter by gene_cluster_id from bakta_amr |
| `bakta_annotations` | Product, EC, COG, KEGG for AMR clusters | 132M | Filter by gene_cluster_id |
| `bakta_db_xrefs` | Database cross-references | 572M | Filter by gene_cluster_id |
| `bakta_pfam_domains` | Pfam domain hits | 18.8M | Filter by gene_cluster_id |
| `eggnog_mapper_annotations` | COG categories, KEGG, GO | 93M | Filter by query_name (gene_cluster_id) |
| `pangenome` | Species-level pangenome stats | 27K | Safe to full scan |
| `gtdb_species_clade` | Species metadata | 27K | Safe to full scan |
| `gtdb_taxonomy_r214v1` | Full taxonomy | 293K | Safe to full scan |
| `genome` | Genome-species mapping | 293K | Safe to full scan |
| `ncbi_env` | Isolation environment metadata | 4.1M | Filter by accession |
| `alphaearth_embeddings_all_years` | Environmental embeddings | 83K | Safe to full scan |
| `kescience_fitnessbrowser.genefitness` | Fitness effects | 27M | Filter by orgId for matched organisms |

### Key Queries

1. **AMR conservation landscape** — Join bakta_amr to gene_cluster, aggregate by conservation class:
```sql
SELECT
    gc.is_core, gc.is_auxiliary, gc.is_singleton,
    COUNT(*) as n_amr_clusters,
    COUNT(DISTINCT gc.gtdb_species_clade_id) as n_species
FROM kbase_ke_pangenome.bakta_amr amr
JOIN kbase_ke_pangenome.gene_cluster gc
    ON amr.gene_cluster_id = gc.gene_cluster_id
GROUP BY gc.is_core, gc.is_auxiliary, gc.is_singleton
```

2. **AMR by species and phylum** — Join to taxonomy for phylogenetic distribution:
```sql
SELECT
    t.phylum, gc.gtdb_species_clade_id,
    COUNT(*) as n_amr_clusters,
    p.no_gene_clusters as total_clusters
FROM kbase_ke_pangenome.bakta_amr amr
JOIN kbase_ke_pangenome.gene_cluster gc ON amr.gene_cluster_id = gc.gene_cluster_id
JOIN kbase_ke_pangenome.pangenome p ON gc.gtdb_species_clade_id = p.gtdb_species_clade_id
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t ON gc.gtdb_species_clade_id = t.gtdb_species_clade_id
GROUP BY t.phylum, gc.gtdb_species_clade_id, p.no_gene_clusters
```

3. **AMR functional context** — Bakta + eggNOG annotations for AMR clusters:
```sql
SELECT
    amr.amr_gene, amr.amr_product,
    ba.product, ba.cog_category,
    egg.COG_category as eggnog_cog, egg.KEGG_ko
FROM kbase_ke_pangenome.bakta_amr amr
LEFT JOIN kbase_ke_pangenome.bakta_annotations ba ON amr.gene_cluster_id = ba.gene_cluster_id
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations egg ON amr.gene_cluster_id = egg.query_name
```

### Performance Plan
- **Tier**: Local Spark Connect (off-cluster via proxy)
- **Estimated complexity**: Moderate — bakta_amr is small (83K), joins filter naturally
- **Known pitfalls**: Species IDs contain `--` (use exact equality); string-typed numeric columns need CAST; gene clusters are species-specific

## Analysis Plan

### Notebook 01: AMR Data Census
- **Goal**: Characterize the bakta_amr table — gene families, mechanisms, detection methods, identity/coverage distributions
- **Expected output**: Summary stats, mechanism classification, AMR gene family catalog (CSV)

### Notebook 02: Conservation Patterns (Spark)
- **Goal**: Join AMR to gene_cluster; compare core/aux/singleton distribution to pangenome baseline
- **Expected output**: Conservation breakdown CSV, enrichment statistics, species-level AMR counts

### Notebook 03: Phylogenetic Distribution (Spark)
- **Goal**: Map AMR density across taxonomy (phylum → class → order → family → genus)
- **Expected output**: Taxonomic AMR density table, phylogenetic heatmap data

### Notebook 04: Functional Context (Spark)
- **Goal**: Characterize AMR clusters by COG category, KEGG pathway, Pfam domains, Bakta product annotations
- **Expected output**: Functional annotation enrichment, "AMR-only" vs well-annotated clusters

### Notebook 05: Environmental Distribution (Spark)
- **Goal**: Link AMR-carrying species to isolation environments via ncbi_env and AlphaEarth
- **Expected output**: Environment × AMR cross-tabulation, embedding-based analysis

### Notebook 06: Fitness Browser Cross-Reference
- **Goal**: For FB organisms with AMR genes, extract fitness effects; test cost hypothesis
- **Expected output**: Fitness distributions for AMR vs non-AMR genes

### Notebook 07: Synthesis & Visualization
- **Goal**: Integrate all dimensions, generate publication figures, identify key stories
- **Expected output**: Summary figures, integrated data tables

## Expected Outcomes
- **If H1 supported**: AMR genes are accessory → confirms conditional selection model, quantifies the extent across 27K species
- **If H0 not rejected**: AMR genes are as core as anything else → surprising, would suggest AMR is constitutive defense
- **Potential confounders**: Sampling bias toward pathogens in genome databases; AMRFinderPlus sensitivity varies by gene family; singleton clusters may reflect annotation artifacts

## Future Extensions
- NMDC metagenome integration: AMR gene prevalence in environmental communities
- MGnify integration: AMR across global microbiome surveys
- Temporal analysis: AMR gene gain/loss rates using phylogenetic tree distances
- Structural analysis: AMR protein structures via AlphaFold/PDB cross-reference

## Revision History
- **v1** (2026-03-15): Initial plan — broad exploratory analysis across 7 dimensions

## Authors
- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
