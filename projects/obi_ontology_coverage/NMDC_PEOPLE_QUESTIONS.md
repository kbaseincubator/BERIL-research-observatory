# NMDC People and Decision-Makers: Open Questions for OBI Investigation

## Why This Matters

OBI is fully loaded in the BERDL ontology store (4,422 terms) but barely used in NMDC metadata (<0.2% of method/instrument fields). Understanding *who* makes ontology adoption decisions at NMDC is critical for interpreting whether this is a deliberate choice, a gap in tooling, or simply inertia.

## What We Know

### Data Flow into BERDL

NMDC doesn't generate data — it consolidates and standardizes from DOE user facilities:

| Facility | Contributes | Data in BERDL |
|---|---|---|
| JGI (Joint Genome Institute) | Sequencing, assembly, annotation | Metagenome workflows, MAGs, read QC |
| EMSL (Environmental Molecular Sciences Laboratory) | Metabolomics, proteomics, NOM | metabolomics_gold, proteomics_gold, lipidomics_gold, nom_gold |
| ESS-DIVE | Environmental data archives | Unclear how much flows into BERDL |

### Known People — BERDL/Infrastructure

| Person | Role | Relevance |
|---|---|---|
| Adam Arkin | UC Berkeley / LBNL, PI | BERDL NMDC tenant is named `nmdc_arkin` — likely the tenant owner |
| Paramvir Dehal | LBNL, data architect | Built the BERDL lakehouse, loaded the data, maintains infrastructure |
| Christopher Neely | LBNL | Author of nmdc_community_metabolic_ecology project in this repo |
| Justin Reese | LBNL / BBOP | Developer of OpenScientist; BBOP connection to OBO Foundry ontology community |

### Known People — NMDC Study PIs (from `nmdc_arkin.study_table`)

These are the PIs whose data flows into BERDL. They (or their lab members) are the ones who originally submitted biosample metadata — with or without OBI terms. Nearly all funding is DOE BER.

| PI | ORCID | Institution | Study Topic |
|---|---|---|---|
| Kate Thibault | 0000-0003-3477-6424 | Battelle/NEON | NEON soil, surface water, benthic metagenomes (3 studies) |
| Mitchel J. Doktycz | 0000-0003-4856-8343 | ORNL | Populus root/rhizosphere microbiomes (3 studies) |
| Jillian F. Banfield | 0000-0001-8203-8771 | UC Berkeley | Angelo Reserve meadow soil metagenomes |
| Jennifer Pett-Ridge | 0000-0002-4439-2398 | LLNL | Microbes Persist SFA |
| Trent R. Northen | 0000-0001-8404-3259 | LBNL | EcoFAB 2.0 root microbiome ring trial |
| Eoin L. Brodie | 0000-0002-8453-8435 | LBNL | East River watershed soil microbiomes |
| Henrik Vibe Scheller | 0000-0002-6702-3560 | LBNL | Sorghum microbiome under drought |
| Joel E. Kostka | 0000-0003-3051-1330 | Georgia Tech | Northern peatland warming/drought |
| Jeff Dangl | 0000-0003-3199-8654 | UNC | Arabidopsis/maize/miscanthus rhizosphere |
| Kelly Wrighton | 0000-0003-0434-4217 | Colorado State | Freshwater river microbes worldwide |
| Ashley Shade | 0000-0002-7189-3067 | Michigan State | Perennial crop phyllosphere |
| Katherine McMahon | 0000-0002-7038-026X | UW-Madison | Lake Mendota/Crystal Bog freshwater |
| Emily Graham | 0000-0002-4623-7076 | PNNL | 1000 Soils Research Campaign |
| Esther Singer | 0000-0002-3126-2199 | LBNL | Panicgrass rhizosphere |
| Christopher Schadt | 0000-0001-8759-2448 | ORNL | Peatland carbon cycling |
| Paul J. Hanson | 0000-0001-7293-3561 | ORNL | (peatland-related) |
| Jack A. Gilbert, Janet K. Jansson, Rob Knight | 0000-0002-5487-4315 | Multi-institution | (consortium study) |
| + ~15 more PIs | | | Various soil, freshwater, host-associated studies |

**Key observations:**
- Heavy LBNL/ORNL/PNNL representation (DOE national labs)
- Most studies are soil or freshwater environmental metagenomics
- These are domain scientists, not metadata specialists — they rely on NMDC infrastructure for standardization

### NMDC Workflows Actually in BERDL

From `nmdc_arkin.omics_files_table` (385K files across 16 studies):

| Workflow Type | Files | Studies | OBI Modeled? |
|---|---|---|---|
| MetagenomeAnnotation | 182,060 | 16 | Partially (gene prediction is OBI, but specific tools like Prodigal are not) |
| ReadBasedTaxonomyAnalysis | 63,650 | 16 | Unknown |
| MagsAnalysis | 47,606 | 16 | Unknown |
| MetagenomeAssembly | 41,149 | 16 | Unknown |
| ReadQcAnalysis | 18,951 | 16 | Unknown |
| MetabolomicsAnalysis | 4,823 | 6 | Likely (OBI has mass spec assay terms) |
| NomAnalysis | 2,583 | 8 | Unknown |
| MetaproteomicsAnalysis | 774 | 3 | Likely (OBI has proteomics assay terms) |
| MetatranscriptomeAnnotation | 1,725 | 3 | Same as metagenome |
| MetatranscriptomeAssembly | 345 | 3 | Unknown |

### NMDC Annotation Ontologies (actually used in `nmdc_arkin`)

| Source | Terms | Notes |
|---|---|---|
| GO | 48,196 | Gene Ontology — dominant annotation source |
| EC | 8,813 | Enzyme Commission numbers |
| KEGG KO | 8,104 | KEGG Orthologs |
| MetaCyc | 1,538 | Metabolic pathways |
| KEGG Module | 370 | KEGG modules |
| KEGG Pathway | 306 | KEGG pathways |
| COG | 26 | COG categories (not individual COGs) |

**Note:** OBI does not appear in annotation_terms_unified at all. This is expected — OBI describes *how* data was generated, not *what* was found.

### Known Standards

- **MIxS** (Minimum Information about any Sequence): Recommends OBI for `seq_meth`, `samp_collect_device`, `nucl_acid_ext`
- **NMDC Schema** (nmdc-schema on GitHub): Defines which fields accept which ontologies; maintained by the NMDC team
- **ENVO**: Highly adopted because MIxS *requires* it for env_broad_scale, env_local_scale, env_medium
- **OBI**: *Recommended* but not *required* by MIxS for method fields — hence low adoption

## What We Need to Find Out

### 1. Who maintains the NMDC schema?
The `nmdc-schema` repo on GitHub defines the data model. Who decides which ontology terms are required vs recommended vs free-text for each field? These are the people whose decisions directly control OBI adoption.

### 2. Who curated env_triads_flattened?
This is the most well-structured metadata table in NMDC biosamples — it maps samples to ENVO/UBERON/NCBITaxon terms. Someone built the curation pipeline. They chose not to include OBI. Was that deliberate or just out of scope (env_triads is about environment, not methods)?

### 3. Who are the NMDC metadata curators?
NMDC has people who harmonize biosample metadata from NCBI. They see the raw submissions and decide how to standardize them. They would know whether submitters ever *try* to use OBI and get it wrong, or whether OBI simply never appears in submissions.

### 4. What is the NMDC team's position on OBI?
Possible stances:
- "We'd love to use OBI but submitters don't provide it" (adoption problem)
- "We tried OBI but it doesn't cover our workflow types well" (coverage problem)
- "OBI is on our roadmap but not prioritized" (resource problem)
- "We don't think OBI adds value beyond free text for methods" (value problem)

### 5. What is the relationship between NMDC, OBO Foundry, and BBOP?
Justin Reese (LBNL/BBOP) works on ontology tooling and is connected to OBO Foundry. BBOP (Berkeley Bioinformatics Open-source Projects) develops tools like OAK (Ontology Access Kit) and LinkML. There may already be internal discussions about OBI adoption that we're not seeing from the data alone.

### 6. Who at JGI/EMSL decides what metadata to capture?
The upstream facilities generate the raw metadata. If JGI doesn't ask sequencing users for OBI-coded instrument types, NMDC can't harmonize what was never captured.

## Suggested Next Steps

- Check the `nmdc-schema` GitHub repo for contributors, issues about OBI, and ontology-related discussions
- Check if there's an NMDC metadata working group or ontology committee
- Search for NMDC publications that discuss their metadata standards choices
- Ask Mark's contacts at LBNL (Paramvir, Justin) about the NMDC schema governance

## For Other Agents

If you have web access or literature search capabilities, the following would be valuable:
- GitHub: `microbiomedata/nmdc-schema` — look at issues, PRs, and contributors related to OBI or ontology adoption
- Publications: Search for "NMDC metadata" or "NMDC schema" papers — they typically list the team
- NMDC website: https://microbiomedata.org — team page, governance docs
