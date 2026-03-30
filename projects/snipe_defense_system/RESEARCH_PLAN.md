# Research Plan: SNIPE Defense System in the BERDL Pangenome

## Research Question

How prevalent are SNIPE homologues across the 293K-genome BERDL pangenome, and does their taxonomic distribution, environmental context, or pangenome status reveal ecological patterns of phage defense?

## Hypothesis

- **H0**: SNIPE domain genes (DUF4041 + GIY-YIG) are rare or absent in the BERDL pangenome and show no taxonomic or environmental enrichment — i.e., their distribution is random with respect to phylum, habitat, and pangenome status.
- **H1**: SNIPE homologues are detectable across multiple bacterial phyla in BERDL, are predominantly accessory (not core) genes within species pangenomes (consistent with defense island mobility), and are enriched in environmental/non-clinical isolates where phage pressure is high.

## Literature Context

SNIPE (Surface-associated Nuclease Inhibiting Phage Entry) was characterized by Saxton et al. (2026) in *Nature* as a membrane-bound nuclease that cleaves phage DNA during genome injection in *E. coli*. Key findings:

- SNIPE localizes to the inner membrane via N-terminal transmembrane domains
- It associates with the ManYZ complex (mannose PTS — the receptor phage lambda uses for DNA entry)
- The DUF4041 domain binds phage tape measure proteins and incoming DNA
- The GIY-YIG nuclease domain cleaves the phage genome
- Self/non-self discrimination is spatial, not sequence-based
- >500 homologues identified across diverse phyla
- ~34% of homologues use alternative membrane-anchoring (DivIVA-like, T3SS ATPase-like)
- Mutations E223K and W257R enhance TMP binding, suggesting ongoing evolutionary refinement

SNIPE joins Zorya and Kiwa as membrane-localized systems that exploit phage genome injection as a vulnerability. The paper identifies DUF4041 and GIY-YIG as the signature domains. **Note**: The paper cites PF13291 for DUF4041, but the correct Pfam accession is **PF13250** (IPR025280). The SNIPE nuclease is **PF13455** (Mug113, GIY-YIG clan CL0418), not PF01541 (canonical GIY-YIG). See REPORT.md § "Corrected Pfam Domain Assignments" for details.

## Query Strategy

### Tables Required

| Table | Database | Purpose | Estimated Rows | Filter Strategy |
|-------|----------|---------|---------------|-----------------|
| `eggnog_mapper_annotations` | `kbase_ke_pangenome` | Find gene clusters with DUF4041/GIY-YIG Pfam domains | 93M | `PFAMs LIKE '%DUF4041%'` (by name, not accession) |
| `gene_cluster` | `kbase_ke_pangenome` | Core/accessory/singleton status for SNIPE clusters | 132M | Join on `gene_cluster_id` |
| `genome` | `kbase_ke_pangenome` | Map clusters to genomes via species clade | 293K | Join on `gtdb_species_clade_id` |
| `gtdb_taxonomy_r214v1` | `kbase_ke_pangenome` | Phylum-level taxonomy for each genome | 293K | Join on `genome_id` |
| `gene_genecluster_junction` | `kbase_ke_pangenome` | Count genes per cluster (copy number) | 1B | Join on `gene_cluster_id` |
| `alphaearth_embeddings_all_years` | `kbase_ke_pangenome` | Environmental embeddings for SNIPE genomes | 83K | Join on species |
| `browser_protein_cog_classes` | `phagefoundry_*` | Defense gene (COG V) counts in phage-target organisms | varies | COG class = 'V' |
| `browser_eggnog_description` | `phagefoundry_*` | Search for nuclease/defense terms | varies | `LIKE '%GIY-YIG%'` etc. |
| `browser_gene` | `phagefoundry_*` | Gene annotations (function text) | varies | Text search |
| NMDC `get_data_objects_by_pfam_domains` | NMDC API | Metagenome samples with DUF4041 | 5,456 samples | PF13250 |
| NMDC `fetch_and_filter_gff_by_pfam_domains` | NMDC API | GFF genomic context for SNIPE genes | per sample | PF13250 + PF13455 |

### Key Queries

1. **Find DUF4041-containing gene clusters**:
```sql
SELECT e.query_name AS gene_cluster_id,
       e.PFAMs,
       e.Description,
       e.Preferred_name,
       e.COG_category,
       gc.gtdb_species_clade_id,
       gc.is_core,
       gc.is_auxiliary,
       gc.is_singleton
FROM kbase_ke_pangenome.eggnog_mapper_annotations e
JOIN kbase_ke_pangenome.gene_cluster gc
  ON e.query_name = gc.gene_cluster_id
WHERE e.PFAMs LIKE '%DUF4041%'  -- Note: PFAMs stores domain names, not accessions
```

2. **Find GIY-YIG nuclease clusters**:
```sql
SELECT e.query_name AS gene_cluster_id,
       e.PFAMs,
       e.Description,
       e.Preferred_name,
       gc.gtdb_species_clade_id,
       gc.is_core,
       gc.is_auxiliary,
       gc.is_singleton
FROM kbase_ke_pangenome.eggnog_mapper_annotations e
JOIN kbase_ke_pangenome.gene_cluster gc
  ON e.query_name = gc.gene_cluster_id
WHERE e.PFAMs LIKE '%GIY-YIG%'  -- Note: SNIPE nuclease is actually PF13455/Mug113, not PF01541
```

3. **Identify putative SNIPE genes (both domains co-occurring)**:
```sql
-- Gene clusters with BOTH DUF4041 and GIY-YIG
SELECT e.query_name AS gene_cluster_id,
       e.PFAMs,
       e.Description,
       gc.gtdb_species_clade_id,
       gc.is_core,
       gc.is_auxiliary,
       gc.is_singleton
FROM kbase_ke_pangenome.eggnog_mapper_annotations e
JOIN kbase_ke_pangenome.gene_cluster gc
  ON e.query_name = gc.gene_cluster_id
WHERE e.PFAMs LIKE '%DUF4041%'  -- Note: PFAMs stores domain names, not accessions
  AND e.PFAMs LIKE '%PF01541%'
```

4. **Taxonomic distribution**:
```sql
SELECT t.phylum, t.class, t.order, t.family,
       COUNT(DISTINCT g.genome_id) AS genome_count,
       COUNT(DISTINCT gc.gtdb_species_clade_id) AS species_count
FROM kbase_ke_pangenome.eggnog_mapper_annotations e
JOIN kbase_ke_pangenome.gene_cluster gc
  ON e.query_name = gc.gene_cluster_id
JOIN kbase_ke_pangenome.genome g
  ON g.gtdb_species_clade_id = gc.gtdb_species_clade_id
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t
  ON g.gtdb_taxonomy_id = t.gtdb_taxonomy_id
WHERE e.PFAMs LIKE '%DUF4041%'  -- Note: PFAMs stores domain names, not accessions
GROUP BY t.phylum, t.class, t.order, t.family
ORDER BY species_count DESC
```

5. **AlphaEarth environmental comparison**:
```sql
-- Mean embeddings for SNIPE-bearing vs non-SNIPE species
-- (aggregate at species level, then compare)
```

### Performance Plan

- **Tier**: REST API for initial counts; Spark Connect for full extraction if row counts are manageable
- **Known pitfalls**:
  - `PFAMs` column may contain comma-separated lists — use `LIKE` not exact match
  - `eggnog_mapper_annotations` has 93M rows — `LIKE` with leading `%` won't use indexes; expect full scan
  - AlphaEarth only covers 28.4% of genomes; environmental analysis is biased toward environmental isolates
  - Gene clusters are species-specific; one "SNIPE gene" may appear as separate clusters in each species

## Analysis Plan

### Notebook 1: Extract SNIPE Domains (`01_extract_snipe_domains.ipynb`)
- **Goal**: Query BERDL for all gene clusters containing DUF4041 (PF13250) and/or GIY-YIG (PF13455/Mug113). Identify the subset containing both domains (putative SNIPE). Retrieve pangenome status and taxonomy. **Note**: The eggNOG PFAMs column stores domain *names* (e.g., "DUF4041"), not accessions (e.g., "PF13250").
- **Expected output**: `snipe_clusters.csv` (all hits), `snipe_both_domains.csv` (DUF4041 + GIY-YIG co-occurrence), `snipe_taxonomy.csv`

### Notebook 2: Taxonomic Distribution (`02_taxonomic_distribution.ipynb`)
- **Goal**: Visualize SNIPE distribution across phyla. Compare to overall BERDL genome distribution to identify enriched/depleted lineages. Analyze core vs. accessory status across species.
- **Expected output**: `snipe_phylum_counts.csv`, phylum distribution figure, core/accessory pie chart

### Notebook 3: Environmental Analysis (`03_environmental_analysis.ipynb`)
- **Goal**: Compare AlphaEarth embeddings for SNIPE-bearing vs. non-SNIPE species. Test whether SNIPE genomes occupy distinct environmental niches. Dimensionality reduction (PCA/UMAP) visualization.
- **Expected output**: `snipe_environmental.csv`, embedding comparison figure, statistical test results

### Notebook 4: Phage Databases (`04_phage_databases.ipynb`)
- **Goal**: Three-part analysis using phage-host and metagenome data:
  - **Part A — PhageFoundry**: Search 4 species-specific genome browsers (*Acinetobacter*, *Klebsiella*, *P. aeruginosa*, *P. viridiflava*) for SNIPE-related genes via COG class V (defense), eggNOG descriptions, and gene annotations. These are key phage therapy targets — SNIPE presence would affect phage susceptibility.
  - **Part B — NMDC metagenomes**: Survey the 5,456 metagenome samples with DUF4041 (PF13250) annotations. Characterize ecosystem distribution (soil, aquatic, host-associated). Fetch GFF files to examine genomic context of SNIPE genes in metagenome assemblies.
  - **Part C — Defense enrichment**: Test whether SNIPE-bearing species in the pangenome have higher overall COG V (defense) gene density than non-SNIPE species — i.e., do SNIPE genes reside in defense islands?
- **Expected output**: `phagefoundry_defense_hits.csv`, `nmdc_duf4041_ecosystems.csv`, `species_defense_enrichment.csv`, defense enrichment figure

## Expected Outcomes

- **If H1 supported**: SNIPE homologues will be detected in hundreds of species, predominantly as accessory genes. Taxonomic distribution will be patchy (consistent with HGT of defense islands). Environmental embeddings may show SNIPE enrichment in soil/aquatic environments with high phage pressure.
- **If H0 not rejected**: SNIPE domains may be too rare or the Pfam annotations too coarse to detect meaningful patterns. DUF4041 and GIY-YIG may occur independently far more often than together, suggesting the SNIPE architecture is restricted to a narrow clade.
- **Potential confounders**:
  - eggNOG Pfam annotations may not capture all SNIPE homologues (sensitivity depends on annotation pipeline)
  - GIY-YIG is a widespread nuclease superfamily — many hits will be non-SNIPE (restriction enzymes, DNA repair)
  - Co-occurrence of both domains in the same gene cluster ≠ same protein (need single-protein domain architecture)
  - AlphaEarth coverage bias (28.4%) limits environmental analysis

## Revision History

- **v1** (2026-03-01): Initial plan — survey SNIPE domains in BERDL pangenome using Pfam annotations.
- **v2** (2026-03-01): Added PhageFoundry genome browser queries, NMDC metagenome analysis (5,456 samples), and defense enrichment analysis (notebook 04).
