# Research Plan: Prophage Gene Modules and Terminase-Defined Lineages Across Bacterial Phylogeny and Environmental Gradients

## Research Question

How are operationally defined prophage gene modules (packaging, head, tail, lysis, integration, lysogenic regulation, anti-defense) and terminase-defined prophage lineages distributed across bacterial phylogeny and environmental gradients? How much of the variance in prophage module abundance is attributable to host phylogeny versus abiotic environmental parameters, after controlling for genome size and assembly completeness? Which modules and lineages show environmental enrichment exceeding phylogenetic expectation?

## Hypothesis

- **H0**: Prophage module and lineage distributions are explained by host phylogeny alone; environment adds no significant variance after controlling for phylogeny, genome size, and assembly completeness.
- **H1a**: Prophage module prevalence varies across environmental gradients (soil vs marine vs host-associated, etc.) beyond what host phylogeny predicts.
- **H1b**: Specific prophage lineages (TerL-defined clusters) show environment-specific enrichment that exceeds phylogenetic expectation under null models preserving host composition and genome size.
- **H1c**: Genes within operationally defined prophage modules co-occur across genomes significantly more than random gene groupings of equal size, validating the module definitions.
- **H1d**: In NMDC metagenomic samples, taxonomy-inferred prophage burden correlates with abiotic environmental parameters independently of community composition.

## Literature Context

### Prophage Distribution Across Bacterial Genomes

Prophages are among the most abundant genetic elements in bacterial genomes. Touchon et al. (2016, ISME J) found that ~46% of sequenced bacterial genomes harbor at least one prophage, with the number scaling with genome size. Roux et al. (2015, eLife) mined ~12,000 genomes and identified ~12,500 high-confidence viral signals, demonstrating that prophage diversity is largely uncharacterized ("viral dark matter"). Casjens (2003, Mol Microbiol) established that prophage sequences can constitute 10-20% of a bacterial genome. Bobay et al. (2014, PNAS) showed that defective (degraded) prophages are even more common than intact ones, with many domesticated for host functions.

### Modular Theory of Phage Evolution

Hendrix et al. (2000, Trends Microbiol) proposed that phage genomes are mosaics assembled from interchangeable functional modules (head/capsid, tail, DNA replication, lysogeny, lysis). Casjens & Hendrix (2015, Virology) detailed lambda phage's modular organization as the reference paradigm. Mavrich & Hatfull (2017, Nature Microbiol) showed that structural modules (terminase, capsid) are the most conserved across temperate phages, making them suitable for lineage classification, while tail modules evolve rapidly and determine host range (Dion et al. 2020, Nat Rev Microbiol).

### Terminase-Based Phage Classification

TerL is the most reliable single-gene marker for phage lineage definition (Casjens & Gilcrease 2009, Methods Mol Biol). TerL phylogeny is broadly concordant with whole-genome phylogeny (Low et al. 2019, Nature Microbiol) and has enabled discovery of major new phage families including Crassvirales (Yutin et al. 2018, Nature Microbiol). We adopt TerL-based clustering at ~70% AAI as our primary lineage definition.

### Environmental Drivers of Lysogeny

The "Piggyback-the-Winner" (PtW) hypothesis (Knowles et al. 2016, Nature) predicts that temperate (lysogenic) phages are favored at high microbial densities because prophages gain a replication advantage by integrating into fast-growing hosts. Lysogeny prevalence varies systematically across environments: soil environments particularly favor temperate strategies (Williamson et al. 2017, Annu Rev Virol), while marine prophage communities vary with depth and productivity (Coutinho et al. 2017, Nature Comms). This motivates our test of whether prophage module prevalence varies across environments beyond phylogenetic expectation.

### Variance Partitioning Methods

Borcard et al. (1992, Ecology) introduced canonical variance partitioning for separating spatial/environmental effects in ecology. PERMANOVA (Anderson 2001, Austral Ecol) enables multivariate testing of group differences. Phylogenetic logistic regression (Ives & Garland 2010, Syst Biol) handles binary traits (module presence/absence) while accounting for phylogenetic non-independence. Goberna & Verdu (2016, ISME J) showed that phylogenetic signal strength varies substantially across microbial traits — some are strongly conserved while others are labile.

### Key References
- Touchon M et al. (2016) ISME J 10:2744-2754
- Hendrix RW et al. (2000) Trends Microbiol 8:504-508
- Knowles B et al. (2016) Nature 531:466-470
- Casjens SR, Gilcrease EB (2009) Methods Mol Biol 502:91-111
- Yutin N et al. (2018) Nature Microbiol 3:38-46
- Low SJ et al. (2019) Nature Microbiol 4:1306-1315
- Roux S et al. (2015) eLife 4:e08490
- Camargo AP et al. (2023) Nature Biotechnol 42:1303-1312
- Anderson MJ (2001) Austral Ecol 26:32-46
- Ives AR, Garland T (2010) Syst Biol 59:9-26
- Bobay L-M et al. (2014) PNAS 111:12127-12132
- Mavrich TN, Hatfull GF (2017) Nature Microbiol 2:17112
- Dion MB et al. (2020) Nature Rev Microbiol 18:125-138
- Koskella B, Brockhurst MA (2014) FEMS Microbiol Rev 38:916-931

## Prophage Module Definitions

Seven operationally defined modules, each identified by eggNOG annotations (Pfam domains, Description keywords, KEGG KOs):

| Module | Key Markers | Presence Rule | Expected Pfam/Description |
|--------|-------------|---------------|--------------------------|
| **A. Packaging** | TerL, TerS, Portal protein | TerL alone OR Portal + TerS | Terminase_1, Terminase_GpA, Phage_portal |
| **B. Head Morphogenesis** | Major capsid protein (MCP), capsid protease, scaffold | MCP required | HK97, Phage_cap_E, Peptidase_S14 |
| **C. Tail** | Tail tube, tail sheath, tape measure, baseplate | >=1 structural tail protein | Phage_tail_S, Phage_sheath, Phage_fiber |
| **D. Lysis** | Holin, endolysin, spanin | Holin OR endolysin | Phage_holin_1-6, Phage_lysozyme |
| **E. Integration** | Integrase (Tyr or Ser), excisionase | Integrase required | Phage_integrase, Phage_int_SAM_5 |
| **F. Lysogenic Regulation** | CI-like repressor, Cro, antitermination | CI-like repressor | XRE_N, HTH_3, Phage_CI_repr |
| **G. Anti-Defense** | Anti-CRISPR, anti-restriction | Any anti-defense gene | ArdA, Anti_CRISPR |

Classification logic: `src/prophage_utils.py`

## Prophage Lineage Definition

A "prophage lineage" is defined by clustering TerL protein sequences at >=70% amino acid identity using MMseqs2. Each gene cluster containing TerL is assigned to a lineage. If a genome has multiple TerL genes, it receives multiple lineage assignments. Lineage representatives are used for rough phylogenetic placement.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.eggnog_mapper_annotations` | Find prophage gene clusters by PFAMs, Description, KEGG_ko | 93M | Multi-OR keyword filter |
| `kbase_ke_pangenome.gene_cluster` | Map to species, get core/aux/singleton, extract TerL sequences | 132M | Filter by gene_cluster_id from annotations |
| `kbase_ke_pangenome.gene` | Gene-to-genome mapping for co-occurrence | 1B | Per-species batches |
| `kbase_ke_pangenome.gene_genecluster_junction` | Gene-cluster membership for co-occurrence | 1B | Per-species batches |
| `kbase_ke_pangenome.genome` | Genome metadata | 293K | Safe to scan |
| `kbase_ke_pangenome.gtdb_species_clade` | Species taxonomy and ANI stats | 27K | Safe to scan |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | GTDB taxonomy hierarchy | 293K | Safe to scan |
| `kbase_ke_pangenome.gtdb_metadata` | Genome size, CheckM completeness | 293K | Safe to scan |
| `kbase_ke_pangenome.pangenome` | Pangenome stats | 27K | Safe to scan |
| `kbase_ke_pangenome.ncbi_env` | Environment metadata (EAV) | 4.1M | Filter by harmonized_name |
| `kbase_ke_pangenome.alphaearth_embeddings_all_years` | Environmental embeddings | 83K | Safe to scan (28% coverage) |
| `nmdc_arkin.taxonomy_features` | NMDC taxonomic profiles per sample | 6,365 | Safe to scan |
| `nmdc_arkin.taxonomy_dim` | Taxid-to-taxonomy mapping | 2.6M | Safe to scan |
| `nmdc_arkin.abiotic_features` | NMDC environmental measurements | 13,847 | Safe to scan |
| `nmdc_arkin.study_table` | NMDC study metadata | 48 | Safe to scan |

### Key Queries

1. **Identify prophage gene clusters** (NB01):
```sql
SELECT gc.gene_cluster_id, gc.gtdb_species_clade_id, gc.is_core, gc.is_auxiliary,
       gc.is_singleton, gc.faa_sequence, ann.PFAMs, ann.Description, ann.KEGG_ko,
       ann.COG_category
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
    ON gc.gene_cluster_id = ann.query_name
WHERE LOWER(ann.Description) LIKE '%terminase%'
   OR LOWER(ann.Description) LIKE '%capsid%'
   OR LOWER(ann.Description) LIKE '%portal protein%'
   OR LOWER(ann.Description) LIKE '%holin%'
   OR LOWER(ann.Description) LIKE '%endolysin%'
   OR LOWER(ann.Description) LIKE '%integrase%'
   OR LOWER(ann.Description) LIKE '%tail sheath%'
   OR LOWER(ann.Description) LIKE '%tail tube%'
   OR LOWER(ann.Description) LIKE '%tape measure%'
   OR LOWER(ann.Description) LIKE '%baseplate%'
   OR LOWER(ann.PFAMs) LIKE '%Terminase%'
   OR LOWER(ann.PFAMs) LIKE '%Phage_portal%'
   OR LOWER(ann.PFAMs) LIKE '%HK97%'
   OR LOWER(ann.PFAMs) LIKE '%Phage_integrase%'
   OR LOWER(ann.PFAMs) LIKE '%Phage_holin%'
   -- (full list generated by src/prophage_utils.build_spark_where_clause())
```

2. **Genome-level module presence** (NB03, per species):
```sql
SELECT g.genome_id, j.gene_cluster_id
FROM kbase_ke_pangenome.gene g
JOIN kbase_ke_pangenome.gene_genecluster_junction j ON g.gene_id = j.gene_id
WHERE g.genome_id IN ({genome_ids_for_species})
  AND j.gene_cluster_id IN ({prophage_cluster_ids_for_species})
```

3. **Environment metadata** (NB04):
```sql
SELECT g.genome_id, g.gtdb_species_clade_id,
       ne.harmonized_name, ne.content
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.ncbi_env ne ON g.ncbi_biosample_id = ne.accession
WHERE ne.harmonized_name IN ('isolation_source', 'env_broad_scale',
                              'env_local_scale', 'env_medium', 'host')
```

### Performance Plan
- **Tier**: JupyterHub direct Spark (required for 93M annotation join and billion-row co-occurrence)
- **Estimated complexity**: High — NB01 is a large join, NB03 requires per-species billion-row extraction
- **Known pitfalls**:
  - eggNOG annotations join on `query_name` = `gene_cluster_id`
  - Gene clusters are species-specific — use PFAMs/KEGG for cross-species comparison
  - PFAMs column uses textual domain names (not Pfam accession IDs)
  - `genomad_mobile_elements` NOT FOUND — must use annotation-based identification only
  - Billion-row joins in NB03 need BROADCAST hints and per-species batching (~5 min/species)
  - ncbi_env is EAV format — needs pivoting
  - AlphaEarth embeddings only 28% coverage

## Analysis Plan

### Notebook 1: Prophage Gene Discovery (JupyterHub)
- **Goal**: Identify all prophage-associated gene clusters; classify into 7 modules; extract TerL sequences
- **Expected output**: `data/prophage_gene_clusters.tsv`, `data/terL_sequences.fasta`, `data/species_module_summary.tsv`

### Notebook 2: TerL Lineage Clustering (JupyterHub/local)
- **Goal**: Cluster TerL sequences at ~70% AAI; assign lineage IDs; build rough lineage phylogeny
- **Expected output**: `data/terL_lineages.tsv`, `data/lineage_summary.tsv`, `figures/terL_lineage_tree.png`

### Notebook 3: Module Co-occurrence Validation (JupyterHub)
- **Goal**: Test whether module genes co-occur more than random in ~15 representative species (v2: reduced from 50)
- **Design**: 15 species across phyla, max 300 genomes/species (sampled), 200 null permutations, vectorized Jaccard via scipy.pdist
- **Expected output**: `data/module_cooccurrence_stats.tsv`, `data/contig_colocation.tsv`, `figures/module_cooccurrence_heatmap.png`

### Notebook 4: Phylogenetic Distribution & Variance Partitioning (local)
- **Goal**: Map prophage prevalence across GTDB; partition variance (PERMANOVA) into phylogeny vs environment
- **Statistical methods**: PERMANOVA, partial Mantel, phylogenetic logistic regression, genome size stratification
- **Expected output**: `data/variance_partitioning_results.tsv`, `data/species_prophage_environment.tsv`, figures

### Notebook 5: NMDC Environmental Gradient Analysis (JupyterHub + local)
- **Goal**: Taxonomy-based inference of prophage burden per NMDC sample; correlate with abiotic features
- **Expected output**: `data/nmdc_prophage_prevalence.tsv`, `data/nmdc_module_by_environment.tsv`, figures

### Notebook 6: Environment-Enriched Modules & Lineages (local)
- **Goal**: Identify modules/lineages with environment enrichment exceeding phylogenetic expectation
- **Statistical methods**: Null models with constrained permutations (preserve host family, genome size); FDR correction
- **Expected output**: `data/enriched_modules.tsv`, `data/enriched_lineages.tsv`, figures

## Expected Outcomes

- **If H1a supported**: Prophage module prevalence varies by environment beyond phylogenetic prediction. This would extend the Piggyback-the-Winner framework from lytic-lysogenic balance to module-level architecture — specific functional modules (e.g., anti-defense, integration) may be enriched in environments with different host-phage coevolutionary pressures.

- **If H1b supported**: Specific TerL lineages are environment-specialists, enriched in particular habitats beyond what host phylogeny predicts. This would demonstrate that prophage lineage ecology is not simply a mirror of bacterial ecology.

- **If H1c supported**: Operational prophage module definitions are validated by co-occurrence statistics, confirming that these gene groups behave as functional units within bacterial genomes rather than independently assorted annotations.

- **If H1d supported**: NMDC taxonomy-inferred prophage burden correlates with abiotic variables, providing independent validation from metagenomic community data.

- **If H0 not rejected**: Prophage distribution is overwhelmingly phylogenetically determined, suggesting that prophage acquisition/loss dynamics are primarily driven by host lineage rather than environmental selection. This would imply prophages are "passengers" of host diversification rather than active players in environmental adaptation.

- **Potential confounders**:
  - Genome size scales with prophage count (Touchon et al. 2016) — requires explicit control
  - Assembly completeness affects gene detection (MAGs vs complete genomes)
  - eggNOG annotation-based identification has unknown sensitivity/specificity for prophage genes
  - Non-phage homologs (bacterial integrases, bacterial holins) inflate false positive rates
  - AlphaEarth embeddings biased toward clinical/well-sampled lineages (28% coverage)
  - NCBI environment metadata sparse and inconsistently labeled
  - NMDC taxonomy-based inference is indirect

## Revision History
- **v1** (2026-02-20): Initial plan
- **v2** (2026-02-21): NB03 redesign — reduced from 50 to 15 species, capped genomes at 300/species, added BROADCAST hints for both genome and cluster temp views, replaced O(n²) Python Jaccard with scipy.pdist, reduced null permutations from 500 to 200. Original approach was intractable (K. pneumoniae alone stalled the notebook due to 1B×1B row join repeated per species).

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory
