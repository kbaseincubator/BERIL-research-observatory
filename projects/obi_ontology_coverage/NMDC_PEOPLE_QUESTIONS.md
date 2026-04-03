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

### Known People

| Person | Role | Relevance |
|---|---|---|
| Adam Arkin | UC Berkeley / LBNL, PI | BERDL NMDC tenant is named `nmdc_arkin` — likely the tenant owner |
| Paramvir Dehal | LBNL, data architect | Built the BERDL lakehouse, loaded the data, maintains infrastructure |
| Christopher Neely | LBNL | Author of nmdc_community_metabolic_ecology project in this repo |
| Justin Reese | LBNL / BBOP | Developer of OpenScientist; BBOP connection to OBO Foundry ontology community |

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
