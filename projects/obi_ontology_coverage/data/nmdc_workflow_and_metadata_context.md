# NMDC Workflow Types and Metadata Context for OBI Assessment

## About NMDC

The National Microbiome Data Collaborative (NMDC) standardizes and integrates environmental microbiome data from DOE user facilities (JGI, EMSL, ESS-DIVE). It captures study-level metadata, biosample metadata (using MIxS/ENVO), and downstream bioinformatics workflow outputs.

## NMDC Workflow Types (from nmdc-schema)

These are the computational workflow types that NMDC tracks. Each produces typed outputs with provenance metadata. The question is: which of these have OBI terms, and which lack representation?

| Workflow Type | Description | Typical Tools | OBI Coverage? |
|---|---|---|---|
| ReadQcAnalysis | Quality filtering of raw sequencing reads | fastp, bbtools | Unknown |
| ReadBasedTaxonomyAnalysis | Taxonomic classification from reads | Kraken2, Centrifuge | Unknown |
| MetagenomeAssembly | Assembly of metagenomic reads into contigs | MEGAHIT, metaSPAdes | Unknown |
| MetagenomeAnnotation | Gene finding and functional annotation | Prodigal, KEGG, COG, Pfam | Unknown |
| MetatranscriptomeAssembly | Assembly of metatranscriptomic reads | rnaSPAdes | Unknown |
| MetatranscriptomeAnnotation | Annotation of metatranscriptome assemblies | Same as metagenome | Unknown |
| MagsAnalysis | Metagenome-assembled genome binning + QC | MetaBAT2, CheckM | Unknown |
| NomAnalysis | Natural organic matter characterization | EMSL NOM tools | Unknown |
| MetabolomicsAnalysis | Metabolite identification and quantification | EMSL metabolomics pipeline | Unknown |
| MetaproteomicsAnalysis | Protein identification from metaproteomics | EMSL metaproteomics pipeline | Unknown |

## NMDC Biosample Metadata Fields Relevant to OBI

These fields describe how samples were collected and processed. MIxS recommends OBI terms for several of them, but adoption is inconsistent.

| Field | MIxS Name | OBI Recommended? | Typical Values |
|---|---|---|---|
| samp_collect_device | Sample collection device | Yes | Grab sampler, corer, filter |
| seq_meth | Sequencing method | Yes (OBI:0002003 etc.) | Illumina, Nanopore, PacBio |
| nucl_acid_ext | Nucleic acid extraction | Yes | PowerSoil kit, phenol-chloroform |
| lib_const_meth | Library construction method | Partial | Nextera, TruSeq |
| samp_mat_type | Sample material type | Partial | soil, sediment, water |
| investigation_type | Investigation type | No (uses MI terms) | metagenome, amplicon |

## Ontologies Currently Used by NMDC

| Ontology | Used For | Adoption Level |
|---|---|---|
| ENVO | Environmental context (biome, feature, material) | High — required by MIxS env_broad_scale/env_local_scale/env_medium |
| UBERON | Anatomical context for host-associated samples | Moderate |
| NCBITaxon | Taxonomic identification | High |
| CHEBI | Chemical entities in metabolomics | Moderate |
| GO | Gene Ontology for functional annotation | High (in annotation outputs) |
| OBI | Investigations, assays, instruments | Low — loaded in ontology store but underused in metadata |
| NMDC Schema | Workflow provenance, data objects, studies | High (internal) |

## Key Questions for OBI Assessment

1. Which NMDC workflow types map to existing OBI `assay` or `data transformation` terms?
2. Where does OBI stop — e.g., does OBI model "metagenome assembly" as a process, or only wet-lab assays?
3. What other ontologies model computational bioinformatics workflows (EDAM, SWO, OBI planned terms)?
4. How do other large-scale microbiome projects (EBI Metagenomics, Earth Microbiome Project, Human Microbiome Project) use OBI?
5. What would NMDC gain from systematic OBI adoption — interoperability with whom?
