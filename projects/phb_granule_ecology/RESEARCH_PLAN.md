# Research Plan: Polyhydroxybutyrate Granule Formation Pathways — Distribution Across Clades and Environmental Selection

## Research Question

How are polyhydroxybutyrate (PHB) granule-forming pathways distributed across bacterial clades and environments, and does this distribution support the hypothesis that carbon storage granules are most beneficial in temporally variable feast/famine environments?

## Hypothesis

- **H0**: PHB pathway distribution across bacterial clades and environments is independent of environmental variability — the pathway is either uniformly distributed or its distribution is explained by phylogeny alone.
- **H1a**: PHB pathway genes (especially phaC, the committed step) are differentially enriched in bacterial clades whose members are found in temporally variable environments (soil, rhizosphere, estuarine) compared to clades in stable environments (open ocean, obligate intracellular).
- **H1b**: Species with complete PHB pathways have broader environmental distributions, as measured by AlphaEarth embedding variance and diversity of isolation source labels.
- **H1c**: In NMDC metagenomic samples, PHB pathway gene prevalence or taxonomic proxies for PHB capability correlate with environmental variability indicators (abiotic parameter variance, dissolved oxygen fluctuation, carbon flux proxies).
- **H1d**: Within clades that carry PHB, subclade-level enrichment patterns correlate with environment type, suggesting ongoing selection rather than ancestral fixation.

## Literature Context

PHB is one of the most widely distributed carbon storage strategies in bacteria, found across Proteobacteria, Firmicutes, Actinobacteria, Cyanobacteria, Bacteroidetes, Planctomycetes, and even halophilic Archaea (Rehm 2003; Kadouri et al. 2005). The canonical pathway involves three core enzymes: phaA (beta-ketothiolase, K00626), phaB (acetoacetyl-CoA reductase, K00023), and phaC (PHA synthase, K03821), plus accessory proteins phaZ (depolymerase), phaP (phasin), and phaR (regulator).

**Key considerations for this study:**

1. **phaC is the committed step**: phaA and phaB participate in general thiolase and short-chain dehydrogenase metabolism beyond PHB synthesis, so phaC (COG3243, PF07167/PF00561) is the most specific marker for PHB capability (Anderson & Dawes 1990).

2. **Four PHA synthase classes** with different phylogenetic distributions: Class I (Cupriavidus, single subunit), Class II (Pseudomonas, mcl-PHA), Class III (Allochromatium, two subunits PhaC+PhaE), Class IV (Bacillus, PhaC+PhaR). These are distinguished by PFam domains and subunit composition (Rehm 2003; Mezzolla et al. 2018).

3. **Extensive HGT of phaC**: Kalia et al. (2007) showed phaC phylogeny is significantly incongruent with 16S rRNA phylogeny, with multiple inter-phylum transfer events. This means phylogenetic distribution cannot be interpreted as purely vertical inheritance.

4. **The feast/famine hypothesis** (Dawes & Senior 1973): PHB is most advantageous under temporal carbon fluctuation — during "feast" periods bacteria polymerize excess carbon, during "famine" they depolymerize for survival. Strong experimental support from competition experiments (Cupriavidus necator), activated sludge enrichment, and rhizosphere dynamics.

5. **Multiple functions beyond carbon storage**: PHB also serves as a stress protectant (oxidative, osmotic, UV, temperature), redox sink (NADH/NAD+ balancing), cryoprotectant, and sporulation substrate (Obruca et al. 2018). The feast/famine hypothesis is dominant but not the sole selective pressure.

6. **Genome streamlining counterexample**: SAR11 (most abundant marine heterotroph) and Prochlorococcus lack pha genes, consistent with selection against PHB in stable oligotrophic pelagic environments (Giovannoni et al. 2005).

### Key References
- Dawes EA, Senior PJ (1973) Adv Microbial Physiol 10:135-266
- Anderson AJ, Dawes EA (1990) Microbiol Rev 54:450-472
- Rehm BHA (2003) Biochem J 376:15-33
- Kadouri D et al. (2005) Crit Rev Microbiol 31:55-67
- Kalia VC et al. (2007) Gene 389:19-26
- Obruca S et al. (2018) Biotechnol Adv 36:856-870
- Mezzolla V et al. (2018) Polymers 10:910
- Jendrossek D, Pfeiffer D (2014) Environ Microbiol 16:2357-2373

## Query Strategy

### PHB Pathway Gene Identification

The committed step for PHB is phaC (PHA synthase). We use a tiered search strategy:

**Tier 1 — High-specificity markers (PHB-specific):**
| Marker | Identifier | Description |
|--------|-----------|-------------|
| phaC | K03821, COG3243 | PHA synthase — the committed step |
| phaP | K14205, PF09361 | Phasin — granule-associated structural protein |
| phaR | K18080, PF05233 | PHB transcriptional regulator |
| phaZ | K05973, PF10503 | PHB depolymerase (intracellular) |

**Tier 2 — Pathway context (shared with general metabolism):**
| Marker | Identifier | Description |
|--------|-----------|-------------|
| phaA | K00626, COG0183 | Beta-ketothiolase (also in fatty acid degradation) |
| phaB | K00023, COG1028 | Acetoacetyl-CoA reductase (SDR family) |
| phaJ | K01715, COG1024 | Enoyl-CoA hydratase (links beta-oxidation to PHA) |

**Classification**: A species has "complete PHB pathway" if it has phaC + at least one of phaA/phaB. Partial = phaC alone or phaA+phaB without phaC.

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.eggnog_mapper_annotations` | Find PHB gene clusters by KEGG_ko, COG, PFAMs | 93M | Filter by KEGG_ko IN list or PFAMs LIKE patterns |
| `kbase_ke_pangenome.gene_cluster` | Map annotations to species, get core/accessory status | 132M | Filter by gene_cluster_id from annotations |
| `kbase_ke_pangenome.gtdb_species_clade` | Species taxonomy and stats | 27K | Safe to scan |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | Full GTDB taxonomy hierarchy | 293K | Safe to scan |
| `kbase_ke_pangenome.genome` | Genome-to-species mapping | 293K | Safe to scan |
| `kbase_ke_pangenome.ncbi_env` | Environment metadata (EAV format) | 4.1M | Filter by harmonized_name |
| `kbase_ke_pangenome.alphaearth_embeddings_all_years` | Environmental embeddings (64-dim) | 83K | Safe to scan (28% coverage) |
| `kbase_ke_pangenome.pangenome` | Pangenome stats (core/aux counts) | 27K | Safe to scan |
| `nmdc_arkin.study_table` | NMDC study definitions | 48 | Safe to scan |
| `nmdc_arkin.abiotic_features` | Environmental measurements per sample | varies | Safe to scan |
| `nmdc_arkin.taxonomy_features` | Taxonomic profiles per sample | 6,365 | Safe to scan |
| `nmdc_arkin.trait_features` | Microbial trait profiles | varies | Check for PHB-related columns |
| `nmdc_arkin.kegg_ko_terms` | KEGG KO definitions | varies | Filter by PHB KOs |

### Key Queries

1. **Identify PHB gene clusters across all species**:
```sql
SELECT gc.gtdb_species_clade_id, gc.gene_cluster_id, gc.is_core, gc.is_auxiliary, gc.is_singleton,
       ann.KEGG_ko, ann.COG_category, ann.EC, ann.PFAMs, ann.Description
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
    ON gc.gene_cluster_id = ann.query_name
WHERE ann.KEGG_ko LIKE '%K03821%'   -- phaC
   OR ann.KEGG_ko LIKE '%K00023%'   -- phaB
   OR ann.KEGG_ko LIKE '%K00626%'   -- phaA
   OR ann.KEGG_ko LIKE '%K05973%'   -- phaZ
   OR ann.KEGG_ko LIKE '%K14205%'   -- phaP
   OR ann.KEGG_ko LIKE '%K18080%'   -- phaR
```

2. **Species-level PHB pathway completeness**:
```sql
-- After extracting per-species PHB gene presence,
-- classify each species as: complete / partial / absent
-- Complete = has phaC + (phaA or phaB)
-- Partial = has phaC alone, or phaA+phaB without phaC
-- Absent = no PHB-specific genes
```

3. **Environmental metadata for PHB+ species**:
```sql
SELECT g.gtdb_species_clade_id, ne.harmonized_name, ne.content, COUNT(*) as n
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.ncbi_env ne ON g.ncbi_biosample_id = ne.accession
WHERE g.gtdb_species_clade_id IN ({phb_positive_species})
  AND ne.harmonized_name IN ('isolation_source', 'env_broad_scale', 'env_local_scale', 'env_medium', 'host', 'geo_loc_name')
GROUP BY g.gtdb_species_clade_id, ne.harmonized_name, ne.content
```

### Performance Plan
- **Tier**: JupyterHub (direct Spark) — required for the 93M-row annotation table join
- **Estimated complexity**: Moderate — single large join for PHB gene discovery, then smaller queries
- **Known pitfalls**:
  - eggNOG annotations join on `query_name` = `gene_cluster_id` (not gene_id)
  - Gene clusters are species-specific — use KEGG/COG/PFam for cross-species comparison
  - KEGG_ko column may contain multiple KOs comma-separated — use LIKE not exact match
  - AlphaEarth embeddings only 28% coverage — check coverage before relying on them
  - NCBI env metadata is EAV format — needs pivoting
  - NMDC abiotic features stored as strings — CAST before numeric comparison
  - phaA (K00626) and phaB (K00023) are pleiotropic — interpret with caution without phaC

## Analysis Plan

### Notebook 1: Data Exploration and PHB Gene Discovery
- **Goal**: Identify all PHB pathway gene clusters in the pangenome; explore NMDC schema for per-sample functional annotations
- **Queries**: Search eggnog_mapper_annotations for PHB KEGG KOs and PFam domains; SHOW TABLES / DESCRIBE for NMDC tables
- **Expected output**: `data/phb_gene_clusters.tsv` (gene_cluster_id, species, KEGG_ko, core/aux/singleton status), NMDC schema notes

### Notebook 2: Pangenome PHB Pathway Mapping
- **Goal**: Classify all 27K species by PHB pathway completeness; map across the GTDB tree
- **Analysis**: Aggregate NB01 results to species level; join with taxonomy; calculate prevalence by phylum/class/order
- **Expected output**: `data/species_phb_status.tsv`, `figures/phb_prevalence_by_phylum.png`, `figures/phb_core_vs_accessory.png`

### Notebook 3: Environmental Correlation
- **Goal**: Test whether PHB+ species are enriched in variable environments
- **Analysis**:
  - Extract ncbi_env metadata for all genomes, classify environments
  - For species with AlphaEarth embeddings: compute embedding variance as environmental breadth proxy
  - Compare PHB+ vs PHB- species on: environment type distribution, embedding variance, geographic spread
  - Statistical tests: chi-squared for environment enrichment, Mann-Whitney for continuous measures
- **Expected output**: `data/species_environment.tsv`, `figures/phb_by_environment.png`, `figures/embedding_variance_phb.png`

### Notebook 4: NMDC Metagenomic Analysis
- **Goal**: Test PHB pathway prevalence across NMDC environments (design depends on NB01 findings)
- **Analysis** (contingent on data availability):
  - If per-sample KO annotations exist: directly count PHB pathway KOs per sample, correlate with abiotic features
  - If not: use taxonomy_features to infer PHB capability from taxonomic composition × pangenome PHB status
  - Correlate PHB signal with abiotic variability (dissolved oxygen, pH, temperature variance across samples within studies)
- **Expected output**: `data/nmdc_phb_prevalence.tsv`, `figures/nmdc_phb_by_environment.png`

### Notebook 5: Subclade Enrichment and Cross-Validation
- **Goal**: Identify subclades with differential PHB enrichment; cross-validate pangenome vs metagenomic patterns
- **Analysis**:
  - Within PHB+ phyla, test for differential enrichment at family/genus level
  - Compare PHA synthase class distribution across environments
  - Cross-validate: do genera enriched for PHB in pangenome data also show enrichment in NMDC metagenomes?
  - Test for HGT signal: do species with discordant PHB status (PHB+ in PHB-poor clades or vice versa) show evidence of HGT?
- **Expected output**: `data/subclade_enrichment.tsv`, `figures/phb_enrichment_heatmap.png`, `figures/pangenome_vs_metagenome.png`

## Expected Outcomes

- **If H1a supported**: PHB pathway prevalence varies significantly by environment type, with enrichment in soil/rhizosphere/estuarine clades and depletion in marine pelagic/intracellular clades. This would provide the first pan-bacterial genomic evidence for the feast/famine hypothesis at the scale of 27K species.

- **If H1b supported**: PHB+ species occupy broader environmental niches (higher AlphaEarth embedding variance), consistent with PHB enabling survival across variable conditions. This would extend the feast/famine hypothesis from temporal to spatial environmental heterogeneity.

- **If H1c supported**: Metagenomic PHB signal correlates with environmental variability proxies in NMDC data, providing independent validation from community-level data.

- **If H0 not rejected**: PHB distribution is explained primarily by phylogeny rather than environment, suggesting the pathway is ancestrally fixed in major clades without ongoing environmental selection. This would challenge the ecological importance of feast/famine dynamics at evolutionary timescales.

- **Potential confounders**:
  - Extensive HGT of phaC complicates phylogenetic interpretation
  - phaA/phaB pleiotropism inflates "partial pathway" counts
  - AlphaEarth embedding coverage bias (28%, skewed toward clinical/human-associated)
  - NCBI environment metadata sparsity and inconsistent labeling
  - PHB has multiple functions beyond carbon storage (stress resistance, redox balance) — feast/famine is not the only possible driver
  - Genome quality variation (MAGs vs complete genomes) may affect gene detection

## Revision History
- **v1** (2026-02-19): Initial plan based on literature review and BERDL schema exploration

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), UC Berkeley / Lawrence Berkeley National Laboratory
