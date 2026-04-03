# OBI Meeting — April 7, 2026: DOE Environmental Microbiology Use Case

Mark is chairing. This is the story to tell.

## The Story in 3 Minutes

We ran a data-driven assessment of OBI coverage for NMDC (National Microbiome Data Collaborative)
and related DOE environmental microbiology projects. Here's what we found.

### Where OBI works well for us

NMDC schema references OBI in 48 places across these classes/slots:

- **Instruments**: Illumina sequencing platforms (MiSeq, HiSeq, NovaSeq), PacBio, Nanopore — well covered
- **Wet-lab processes**: `CollectingBiosamplesFromSite`, `Extraction`, `LibraryPreparation`, `Pooling`, `StorageProcess`, `MaterialProcessing` — all mapped to OBI
- **Sequencing methods**: `seq_meth` enum has ~20 OBI-coded instrument types
- **Roles**: `OBI:0000103` (principal investigator role)

OBI's formal axiomatization gives us things MIxS checklists and LinkML enums can't:
classification by subsumption, input/output constraints, and protocol validation.

### Where OBI stops — the computational gap

NMDC has 10 bioinformatics workflow types. OBI covers the wet-lab side but has
**zero terms for computational workflows**:

| NMDC Workflow | OBI Coverage |
|---|---|
| Nucleic acid extraction | OBI:0666667 |
| Library preparation | OBI has terms |
| Sequencing | OBI:0000626 (DNA), OBI:0001177 (RNA), OBI:0002623 (WMS) |
| Read QC / quality filtering | Nothing |
| Metagenome assembly | Nothing |
| Metagenome annotation / gene finding | Nothing |
| Read-based taxonomy (Kraken2, Centrifuge) | Nothing |
| MAG binning + CheckM QC | Nothing |
| Metabolomics analysis | Likely covered (mass spec assays) |
| Metaproteomics analysis | Likely covered (proteomics assays) |

`OBI:0200000` (data transformation) exists as a generic parent with ~22 subtypes
(normalization, clustering, differential expression analysis) but nothing specific
to metagenomics/environmental genomics pipelines.

EDAM and SWO might fill this gap but neither is loaded in our ontology store and
neither has OBI's level of axiomatization.

### The adoption gap — even where OBI has terms

We queried the BERDL data lakehouse (which hosts NMDC data for 48 studies, 14,938 biosamples).
Method/instrument fields that OBI was designed for are **100% free text**:

| Field | Top values (all free text) | OBI term exists? |
|---|---|---|
| `samp_collec_device` | auger, brownie cutter, corer | Yes: OBI:0002814 |
| `dna_isolate_meth` | Qiagen DNeasy PowerSoil, PowerBiofilm | Yes: OBI:0666667 |
| `samp_collec_method` | Seawater, Kit 1, Kit 5 | Yes |
| `seq_meth` | (better — some OBI IDs, but inconsistent format) | Yes |

MIxS *recommends* OBI for these fields but doesn't *require* it (unlike ENVO for env_broad_scale).
Result: submitters write free text, and there's no validation step that maps to OBI.

### What we'd like from OBI

1. **Computational workflow terms**: Even lightweight classes for metagenome assembly,
   genome binning, taxonomic classification, gene prediction, functional annotation.
   These don't need the full axiom depth of wet-lab assays — just enough to classify
   and distinguish workflow types.

2. **Guidance on "OBI for DOE"**: The ontology is called "Biomedical Investigations" but
   DOE environmental genomics uses it heavily. Is there appetite for a broader scope, or
   should DOE extensions live elsewhere?

3. **Value set support**: Chris Mungall's position is that production systems need static
   value sets (OBI terms snapshotted as LinkML enums), not live ontology queries. How does
   OBI see itself fitting into LinkML-based schemas?

### The METPO connection

METPO (Microbial Traits and Phenotypes Ontology) is the phenotype side of this:
- OBI = how the investigation was done (assays, instruments, protocols)
- METPO = what organisms can do (traits, phenotypes)
- Together they could provide a complete ontological layer for environmental microbiology

METPO currently imports only `OBI:0100026` (organism) — minimal integration. A tighter
connection where METPO references OBI assay classes for "how was this phenotype measured"
would strengthen both ontologies.

BacDive (988K metabolite utilization tests in our lakehouse) is a concrete test case:
strain X was tested by assay Y (OBI) and showed phenotype Z (METPO) for compound W (CHEBI).

### What we're doing about it

- Running the OBI census in our data lakehouse (4,422 OBI terms loaded, cross-referenced against actual usage)
- OpenScientist (AI co-scientist) investigation submitted on OBI coverage for environmental microbiology
- Identified a small complete NMDC study (29 biosamples, all workflow types) as a test case for better OBI annotation
- This BERIL research observatory project: https://github.com/turbomam/BERIL-research-observatory/tree/projects/obi_ontology_coverage

## Issue to Reference

obi-ontology/obi#1910 — "bodily fluid cell count assay" request that highlights the
non-biomedical use case tension. Someone wants cell counts that aren't from bodily fluids.
Same pattern as our DOE workflows that aren't "biomedical."

## Agenda Doc

https://docs.google.com/document/d/1eEutJAG56gncTsWf2sAqHa4a9pQAuCbhsg_kmbF78tw/edit
