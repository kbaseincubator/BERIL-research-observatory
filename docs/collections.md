# BERDL Collections Overview

The **KBase BER Data Lakehouse (BERDL)** hosts 37 databases organized across 9 tenants. This document provides an overview of all collections, organized by tenant, with links to detailed schema documentation.

**Last Updated**: 2026-02-23
**Discovery Method**: REST API introspection (`/delta/databases/list`)

---

## Tenants and Collections

### KBase

Core KBase scientific data collections.

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `kbase_ke_pangenome` | Pangenome | 16 | 293K genomes, 1B genes | [pangenome.md](schemas/pangenome.md) | Species-level pangenomes from GTDB r214 with functional annotations, ANI, pathway predictions, environmental embeddings, cluster representative sequences, and phylogenetic trees |
| `kbase_genomes` | Genomes | 16 | 293K genomes, 253M proteins | [genomes.md](schemas/genomes.md) | Structural genomics data (contigs, features, protein sequences) in CDM format |
| `kbase_msd_biochemistry` | Biochemistry | 5 | 56K reactions, 46K molecules | [biochemistry.md](schemas/biochemistry.md) | ModelSEED biochemical reactions, compounds, and stoichiometry for metabolic modeling |
| `kbase_phenotype` | Phenotype | 7 | 4 experiments, 182K conditions | [phenotype.md](schemas/phenotype.md) | Experimental phenotype data (growth conditions and measurements) |
| `kbase_uniprot` | UniProt | 1 | varies | [uniprot.md](schemas/uniprot.md) | UniProt protein identifier cross-references |
| `kbase_uniref50` | UniRef50 | 4 | 100K clusters | [uniref.md](schemas/uniref.md) | UniRef protein clusters at 50% identity |
| `kbase_uniref90` | UniRef90 | 4 | 100K clusters | [uniref.md](schemas/uniref.md) | UniRef protein clusters at 90% identity |
| `kbase_uniref100` | UniRef100 | 4 | 260K clusters | [uniref.md](schemas/uniref.md) | UniRef protein clusters at 100% identity |
| `kbase_refseq_taxon_api` | RefSeq Taxonomy | 5 | small | - | RefSeq taxonomy and identifier mappings |
| `kbase_ontology_source` | Ontology | unknown | unknown | - | Ontology definitions (timed out during discovery) |

### KE Science

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `kescience_fitnessbrowser` | Fitness Browser | 50+ | 48 organisms, 27M fitness scores | [fitnessbrowser.md](schemas/fitnessbrowser.md) | Genome-wide mutant fitness data from RB-TnSeq experiments across diverse bacteria |
| `kescience_webofmicrobes` | Web of Microbes | 5 | 37 organisms, 589 metabolites, 10K observations | [webofmicrobes.md](schemas/webofmicrobes.md) | Curated microbial exometabolomics: metabolite production/excretion profiles (Kosina et al. 2018) |
| `kescience_bacdive` | BacDive | 8 | 97K strains, 988K metabolite tests, 643K enzyme records | [bacdive.md](schemas/bacdive.md) | Bacterial diversity metadatabase: phenotypes, growth conditions, isolation source, metabolite utilization (DSMZ) |

### ENIGMA

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `enigma_coral` | ENIGMA CORAL | 45 | 3K taxa, 7K genomes | [enigma.md](schemas/enigma.md) | Environmental microbiology data from the ENIGMA SFA (samples, genomes, communities, strains) |

### NMDC (National Microbiome Data Collaborative)

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `nmdc_arkin` | NMDC Multi-omics | 60+ | 48 studies, 3M+ metabolomics records | [nmdc.md](schemas/nmdc.md) | Multi-omics analysis data (annotations, embeddings, metabolomics, proteomics, traits) |
| `nmdc_ncbi_biosamples` | NMDC BioSamples | 17 | varies | [nmdc.md](schemas/nmdc.md) | Harmonized NCBI BioSample metadata |

### PhageFoundry

Species-specific genome browsers for phage-host interaction research. All share the GenomeDepot schema (37 tables each).

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `phagefoundry_acinetobacter_genome_browser` | Acinetobacter | 37 | 891 strains | [phagefoundry.md](schemas/phagefoundry.md) | *Acinetobacter* genome browser |
| `phagefoundry_klebsiella_genome_browser_genomedepot` | Klebsiella | 37 | varies | [phagefoundry.md](schemas/phagefoundry.md) | *Klebsiella* genome browser |
| `phagefoundry_paeruginosa_genome_browser` | P. aeruginosa | 37 | varies | [phagefoundry.md](schemas/phagefoundry.md) | *P. aeruginosa* genome browser |
| `phagefoundry_pviridiflava_genome_browser` | P. viridiflava | 37 | varies | [phagefoundry.md](schemas/phagefoundry.md) | *P. viridiflava* genome browser |
| `phagefoundry_strain_modelling` | Strain Modelling | unknown | unknown | [phagefoundry.md](schemas/phagefoundry.md) | Strain modelling data (timed out during discovery) |

### PlanetMicrobe

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `planetmicrobe_planetmicrobe` | PlanetMicrobe | 30 | 2K samples, 6K experiments | [planetmicrobe.md](schemas/planetmicrobe.md) | Marine microbial ecology (campaigns, samples, metagenomics) |
| `planetmicrobe_planetmicrobe_raw` | PlanetMicrobe Raw | 30 | varies | [planetmicrobe.md](schemas/planetmicrobe.md) | Raw/unprocessed version |

### PROTECT

| Database | Short Name | Tables | Scale | Schema Doc | Description |
|----------|-----------|--------|-------|------------|-------------|
| `protect_genomedepot` | PROTECT | 6 | varies | [protect.md](schemas/protect.md) | Pathogen genome browser (GenomeDepot format) |

### Microbial Discovery Forge

Observatory-generated data products from BERIL research projects, stored on MinIO object storage. Project directories are mirrored as-is (data files, notebooks, figures, markdown).

| Storage | Short Name | Scale | Description |
|---------|-----------|-------|-------------|
| `s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/` | Observatory Data | 22 projects, 8.5 GB, 1,244 files | Research project data products: fitness matrices, ortholog groups, conservation scores, DIAMOND hits, notebooks, figures, and docs. Uploaded via `/submit` workflow. |

**Access**:
```bash
# List projects
mc ls berdl-minio/cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/

# Download a project's data
mc cp --recursive berdl-minio/cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/<project>/data/ ./

# Read from Spark
spark.read.csv("s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/<project>/data/<file>.csv", header=True)
```

**Upload**: `python tools/lakehouse_upload.py <project_id>` — see [tools/lakehouse_upload.py](../tools/lakehouse_upload.py).

### Development/Test Databases

These are demo, test, or staging databases. Not for production use.

| Database | Description |
|----------|-------------|
| `globalusers_demo_shared` | Shared demo data |
| `globalusers_demo_test` | Test database |
| `globalusers_demo_test_1` | Test database |
| `globalusers_demo_test_2` | Test database |
| `globalusers_gapmind_pathways` | GapMind pathways (staging) |
| `globalusers_kepangenome_parquet_1` | Pangenome parquet (staging) |
| `globalusers_nmdc_core_test` | NMDC core test |
| `globalusers_nmdc_core_test2` | NMDC core test |
| `globalusers_nmdc_core_test3` | NMDC core test |
| `globalusers_phenotype_ontology_1` | Phenotype ontology (staging) |
| `globalusers_phenotype_parquet_1` | Phenotype parquet (staging) |

---

## Cross-Collection Relationships

Several databases share data or can be linked:

```
kbase_ke_pangenome ←→ kbase_genomes
    │  Gene IDs map via kbase_genomes.name table
    │  Same 293K genomes, same gene features
    │
    ├→ kbase_msd_biochemistry ←→ kescience_webofmicrobes
    │  EC/KEGG → ModelSEED reactions    compound name/formula matching
    │
    ├→ kescience_fitnessbrowser ←→ kescience_webofmicrobes
    │  FB organisms → pangenome species    2 direct strain matches + Keio
    │  (DIAMOND link table under          19 metabolite-condition overlaps
    │   construction)
    │                    ↕
    │              kescience_bacdive
    │              12 FB organisms match by taxid
    │              27K genome accessions → pangenome
    │              988K metabolite utilization records
    │              63 metabolites shared with WoM
    │
    └→ nmdc_arkin
       Shared annotation ontologies (COG, KEGG, EC, GO)
```

### Key Linking Strategies

1. **Pangenome ↔ Genomes**: The `kbase_genomes.name` table maps CDM UUIDs to the gene IDs used in `kbase_ke_pangenome.gene`. Cluster representative protein and nucleotide sequences are also available directly in `gene_cluster.faa_sequence` / `fna_sequence`.

2. **Pangenome ↔ Biochemistry**: Functional annotations in `eggnog_mapper_annotations` (EC numbers, KEGG IDs) can be matched to `kbase_msd_biochemistry.reaction` entries.

3. **Pangenome ↔ Fitness Browser**: Organisms in the fitness browser can be linked to pangenome species via taxonomy. A protein sequence comparison (DIAMOND) link table is being constructed to enable direct gene-level mapping.

4. **NMDC ↔ Annotation Sources**: The `nmdc_arkin` database includes unified annotation terms from the same ontologies (COG, EC, GO, KEGG, MetaCyc) used in the pangenome functional annotations.

5. **Web of Microbes ↔ Fitness Browser**: 2 direct strain matches (Pseudomonas FW300-N2E3 → `pseudo3_N2E3`, GW456-L13 → `pseudo13_GW456_L13`) plus E. coli BW25113 → `Keio`. 19 metabolites that WoM organisms produce are tested as FB carbon/nitrogen sources.

6. **Web of Microbes ↔ ModelSEED**: 69 WoM metabolites match ModelSEED molecules by exact name (26.8% of identified compounds). 107 additional match by molecular formula.

7. **BacDive ↔ Fitness Browser**: 12 of 48 FB organisms match BacDive strains by NCBI taxonomy ID (637 BacDive strains total). Key matches: Pseudomonas fluorescens (103 strains), Ralstonia solanacearum (32), Cupriavidus basilensis (17).

8. **BacDive ↔ Pangenome**: 27,502 BacDive genome accessions (GCA format) can be matched to pangenome genomes. Requires prefix adjustment (BacDive uses GCA_*, pangenome uses GB_GCA_* or RS_GCF_*).

9. **BacDive ↔ Web of Microbes**: 63 WoM metabolite names match BacDive metabolite utilization compound names. Top overlaps: trehalose (13,838 BacDive strains tested), arginine (13,665), glucose (7,103).

---

## Access

All databases are accessible via:
- **Spark SQL**: Direct queries on BERDL JupyterHub (`get_spark_session()`)
- **REST API**: `https://hub.berdl.kbase.us/apis/mcp/`
- **Auth**: Bearer token (see `.env` file)

For query patterns and performance guidance, see:
- [Performance Guide](performance.md)
- [Common Pitfalls](pitfalls.md)
- Individual schema docs linked above

---

## Adding New Collections

When a new database is added to BERDL:

1. Run `/berdl-discover` to introspect the database
2. Create a schema doc in `docs/schemas/{name}.md`
3. Add the database to this collections overview
4. If applicable, create a skill module in `.claude/skills/berdl/modules/{name}.md`
