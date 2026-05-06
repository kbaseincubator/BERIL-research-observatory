## 📄 Internal Project Data Briefing Memo

**Project:** *Microbial Pangenome & Ecotype Structure*  
**Prepared by:** Paramvir Dehal

---

### 1  Project Overview

Our goal is to probe **ecotype structure within microbial species** by comparing gene-content variation, phylogeny, mobile-element flow, functional capacity, and (where possible) environment metadata. We built species-level pangenomes across the microbial tree and integrated them with harmonized sample information. Genomic signals of recent gene exchange (shared mobile elements, identical sequence tracts in otherwise diverged genomes) will complement sparse environment labels.

We also have functional profiling from **GapMind**, run on all genomes, which provides:  
1. **Per-genome, per-pathway confidence scores** for amino acid biosynthesis and small carbon source utilization pathways.  
2. **Per-step predictions** for each pathway, linked to pangenome gene families.

---

### 2  Data Generation Workflow

| Step                             | Tool / Filter                                                                                                              | Resulting output                                                                              |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Genome selection**             | GTDB r214 → remove single-genome species → drop NCBI-flagged assemblies → collapse ≥99.999 % ANI redundancy                | filtered set of genomes grouped into species-level clades                                     |
| **Within-clade pairwise ANI**    | FastANI                                                                                                                    | per-pair ANI + alignment fraction within each clade                                           |
| **Gene prediction & clustering** | motupan, 90 % AAI                                                                                                          | gene-family clusters per clade                                                                |
| **Functional annotation**        | eggNOG v6 on cluster reps                                                                                                  | one annotation per gene family                                                                |
| **Mobile-element annotation**    | GeNomad                                                                                                                    | gene-level plasmid/virus/prophage/AMR tags                                                    |
| **Pathway profiling**            | GapMind                                                                                                                    | pathway-level confidence scores + per-step mapping to pangenome gene families                 |
| **Phylogenetic trees**           | Single-copy core genes → FastTree                                                                                          | one tree per clade                                                                            |
| **Metadata harvest**             | GTDB & NCBI Biosample                                                                                                      | quality metrics + environment fields                                                          |
| **Storage**                      | On-prem Delta Lakehouse (Spark SQL)                                                                                        | gene-level rows queryable via Spark                                                           |

For current row counts and the live accessible inventory, run `berdl_notebook_utils.get_databases(return_json=False)` and use `SELECT COUNT(*)` or `DESCRIBE EXTENDED` against the relevant tables — the lakehouse is the source of truth.

---

### 3  Data Architecture & Key Tables

| Theme                           | Representative tables (primary keys in **bold**)                                                                                                      | Highlights                                                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Genome & taxonomy**           | `genome`(**genome_id**), `gtdb_taxonomy_r214v1`(**gtdb_taxonomy_id**), `gtdb_species_clade`(**gtdb_species_clade_id**)                                | Links every genome to GTDB taxonomy and clade-level ANI stats (mean/min ANI, circumscription radius, filtered-vs-raw counts).                    |
| **Quality & assembly metadata** | `gtdb_metadata`(**accession**)                                                                                                                        | CheckM completeness/contamination, contig stats, GC%, assembly level, genome size.                                                               |
| **Pairwise metrics**            | `genome_ANI`(**genome1_id**, **genome2_id**), `phylogentic_tree_distance_pairs`(**genome1_id**, **genome2_id**)                                       | Enables joining ANI, alignment fraction (AF) and phylogenetic branch distance for each genome pair.                                              |
| **Pangenome & protocols**       | `pangenome`(**gtdb_species_clade_id**), `pangenome_build_protocol`(**protocol_id**)                                                                   | Stores counts of core/aux/singleton gene clusters and completeness stats; protocol table documents parameter settings for reproducibility.       |
| **Gene families & membership**  | `gene_cluster`(**gene_cluster_id**), `gene_genecluster_junction`(**gene_cluster_id**, **gene_id**), flags `isCore`, `isAccessory`, `isSingleton`     | Rapidly query core vs accessory vs singleton genes per clade.                                                                                    |
| **Annotations**                 | `eggnog_annotation`(**query_name** ← gene_cluster_id)                                                                                                  | COG, GO, KEGG, EC, CAZy, PFAM for cluster representatives (10× compute reduction; consistent within 90 % AAI clusters).                          |
| **Mobile elements**             | `genomad_mobile_elements`(**gene_id**)                                                                                                                 | Plasmid & virus hallmarks, conjugation genes, AMR hits, free-text descriptions.                                                                  |
| **Pathway profiles**            | GapMind pathway results + per-step mapping table                                                                                                      | Pathway-level confidence for amino acid biosynthesis and small carbon source utilization + step-to-gene cluster mapping.                         |
| **Environment metadata**        | `NCBI_env`, `IMG_env`, `sample`                                                                                                                       | Harmonized isolation source, geographic location, ENVO/GOLD ecosystem terms via Biosample IDs.                                                   |
| **Traceability**                | Protocol foreign keys in `pangenome`, `genome_ANI`, `phylogenetic_tree`                                                                               | Every major derivation step is version-tracked.                                                                                                  |

---

### 4  Metagenome-Augmented Pangenomes (Prototype)

1. **Search** public assembled metagenomes with `sourmash branchwater`.
2. **Screen hits**: DIAMOND search of pangenome cluster representatives against metagenome proteomes (within cluster AAI ± margin).
3. **Graph alignment** to species pangenome graphs filters contigs that disrupt gene order.  
   **Precision ≈ 1.0**; sensitivity varies (median ≈ 0.7 when contigs are 2–10 kb). Matched samples carry GOLD / ENVO labels for future expansion.

---

### 5  Known Limitations & Caveats

- **Environment fields are sparsely populated**, especially for environmental (non-host) samples.
- **Core/accessory calls** from motupan do not correct for phylogenetic structure or clade sampling bias.
- **Contig fragmentation** in metagenomes reduces sensitivity for augmentation.
- **Annotation breadth vs depth**:
  - eggNOG provides broad functional categories but limited strain-level nuance.
  - GapMind coverage is limited to its current amino acid and carbon source pathway set.
  - Novel mobile elements may evade GeNomad detection.
- **Occasional GTDB mis-placements**, particularly in uncultivated MAGs.
- Planned recombination metrics (identical ≥100 bp tracts in ~95 % ANI genomes) are not yet implemented.

---

### 6  Data Access

- **Location:** On-prem Delta Lakehouse cluster (Spark 3.x).
- **Interfaces:** Spark SQL, PySpark, or JDBC.
- **Primary schema docs:** `/schemas/pangenome_schema_v2025-05-12.sql` (matches tables above).
- Contact Alcy (or data-engineering slack channel) for credentials, example notebooks, or protocol details.

---

### 7  Next Steps

This briefing intentionally avoids prescribing analyses. Please explore the schema, assess data quality for your questions, and propose directions or collaborations. We welcome feedback on additional harmonization needs, missing metadata, or protocol changes.

---
