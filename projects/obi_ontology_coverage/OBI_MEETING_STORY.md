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

## Mark's OBI History (for credibility framing)

You're not an outsider asking for things. You're the 8th ranked contributor:
- 27 commits, 13 merged PRs, 20 authored issues
- Built clinical assay terms (PennTURBO era), Illumina sequencer series classes (2024)
- Alicia Clum asked you to add NovaSeq X and sequencer groupings -- you delivered via PRs #1826, #1828
- Regular OBI call participant since at least 2023
- Built assay terms using ChatGPT 5 (referenced in #1910 comment)
- Chris Mungall filed #1693 about environmental replicates and told the OBI team "Mark may be able to make a call and present on what we are doing in NMDC"

## Key Open Issues to Reference

### obi-ontology/obi#1693 -- Environmental metagenome replicates (THE critical issue)
https://github.com/obi-ontology/obi/issues/1693

Filed by Chris Mungall (2023-05-04). OBI's replicate role hierarchy was written for human
subjects and explicitly excludes environmental samples -- even though the
`participant under investigation role` definition mentions a lake example. Chris proposed
broadening labels/definitions. Bjoern Peters agreed ("we should change subject/participant
to material"). You attended an OBI call about it (2023-09-25). **Discussion stalled in
Nov 2023 with no resolution and no PR.** This is directly blocking NMDC from properly
describing biological and technical replicates for environmental samples.

### obi-ontology/obi#990 -- Microbiome sequencing design (open 7+ years)
https://github.com/obi-ontology/obi/issues/990

Requested 2018-12-04. Extensive discussion involving James Overton, Chris Mungall,
Ramona Walls, Pier Luigi Buttigieg about where microbiome/microbiota terms belong
(PCO? ENVO? OHMI?). Chris warned about "patching together hierarchies from multiple
different ontologies." Still open.

### obi-ontology/obi#1910 -- Bodily fluid cell count assay
https://github.com/obi-ontology/obi/issues/1910

The pattern example: someone wants cell counts not restricted to bodily fluid. James
tagged you. You responded noting you built these classes with ChatGPT 5. Bjoern proposed
a general `cell counting assay` parent. James is drafting a PR (discussed 2026-03-16).
Same tension as DOE workflows that aren't "biomedical."

### obi-ontology/obi#671 -- Sequence assembly (open since 2013!)
https://github.com/obi-ontology/obi/issues/671

About representing sequence assembly as data vs. data transformation. 13 years unresolved.

### obi-ontology/obi#950 -- Transcriptome assembly
https://github.com/obi-ontology/obi/issues/950

### obi-ontology/obi#1869 -- Data transformation template migration
https://github.com/obi-ontology/obi/issues/1869

Only 5 of ~200 data transformation terms are in the template. This is the infrastructure
gap that makes adding computational workflow terms harder.

### obi-ontology/obi#1056 -- Whole metagenome sequencing assay (SUCCESS)
https://github.com/obi-ontology/obi/issues/1056

Requested 2019, added 2021. **Proof that this process works** -- if we request
metagenomics workflow terms, they can get added.

## Other Context from Slack

### Katherine Heal found OBI's plan_specification relevant
(NMDC Slack, 2024-04-24): Katherine found `IAO:0000591` (software_method) as a sibling
of `OBI:0000272` (protocol) under `IAO:0000104` (plan_specification). She thought this
was close to what NMDC needed for Configuration modeling. You invited her to an OBI call.

### Chris on term selection philosophy
(NMDC Slack, 2024-01-17): "Its better to avoid pick-n-mix, its also better to prioritize
OBO ontologies" -- endorsing OBI over non-OBO alternatives like BAO.

### BioPortal OBO/OBI confusion
(BBOP Slack, 2026-03-12): Sierra Moxon found "OBO" appearing as a separate ontology
alongside OBI on BioPortal (from BERVO mapping work). Chris said "no need to get OBI
folks any more riled up." You noted you could raise it at the OBI call you're chairing.

### James Overton's IEDB tour
(BBOP DM, 2026-03-30): You told Chris that James gave you a tour of the IEDB website's
assay class browser, similar to NMDC's environmental triad browsers. James seemed
interested in chromatography and mass spec interfaces on the Data Portal.

## Room Dynamics — Know Your Audience

### Chris Mungall's Modeling Philosophy (7 relevant blog posts)

Read the full posts at https://douroucouli.wordpress.com/. Key positions:

**"Shadow Concepts Considered Harmful" (2022-08-10):** Uses OBI's `measurement datum`
classes as a prime negative example. "Axillary temperature measurement datum" is a shadow
of "temperature." Don't propose new terms as shadow variants (datum, specification, output).
Propose core concepts.

**"Don't Over-Specify OWL Definitions" (2019-07-29):** If the reasoner can infer it, don't
assert it. OBI assays are often over-axiomatized. Your ask for "lightweight" computational
workflow terms aligns with this.

**"Rococo OWL" / Design Pattern Alignment (2020-11-02):** His term for excessive axiom
complexity. DOSDPs (Dead Simple OWL Design Patterns) are the remedy. OBI #1869 notes only
5 of ~200 data transformation terms are in templates. Suggesting DOSDP-based terms would
resonate.

**Pick-and-Mix Antipattern (2021-07-03):** Don't grab assay terms from OBI, workflow terms
from EDAM, and tool terms from SWO. Draw from one place. This supports expanding OBI
rather than patching from multiple ontologies.

**Using Ontologies Within Data Models (2022-07-15):** Proposes LinkML dynamic enums (value
sets defined as ontology graph queries) rather than hardcoded lists. Relevant to how OBI
terms get consumed by nmdc-schema.

**KG Modeling Design Patterns (2019-03-14):** Contrasts KG modeling (simple edges readable
as sentences) with OWL modeling (formal, reasoner-driven). Notes "lack of ontological
commitment makes agreement on standards easier." Frames the question: should OBI invest in
richer axioms or simplify toward KG-consumable patterns?

**Rector Normalization (2019-06-29):** Decompose into simple primitives, reconstruct via
reasoning. Assay ontologies are ideal candidates because they're compositional
(method + target + instrument).

### Other Key People

**James Overton** (lead OBI maintainer, 1003 commits): Methodical, infrastructure-focused.
Created 48 NIEHS DTT assays in one batch using templates. Will evaluate: does this follow
OBI patterns? Is the axiomatization tractable? Is the build pipeline clean?

**Bjoern Peters** (LJI, IEDB): Immunology-database pragmatist. In #1693, immediately
proposed changing "subject/participant" to "material" -- a generalizing move. Proposed
dual-release process (#1837) for OBI modernization. Sympathetic to expanding scope if it
simplifies rather than complicates.

**Chris Stoeckert** (UPenn, OBI co-creator, Mark's former boss): Governance- and
quality-oriented. Requires ORCIDs for term editors (#1605), added OBO Dashboard badges
(#1551). Will say yes to well-defined, properly attributed terms. Protective of OBI's
established design patterns.

**Damion Dooley** (SFU, Public Health Bioinformatics, GenEpiO): Very relevant -- he filed
#1232 "Does OBI want the following sequence assembly datums?" (2020), directly asking about
sequence assembly terms. Also filed #1194 (specimen collection device NTRs from MIxS),
#1175 (names of sequencing software), and actively participated in #1693 (environmental
replicates) by drafting revised definitions for "reference subject role." He comes from a
genomic epidemiology perspective and bridges public health and environmental use cases.
A natural ally for broadening OBI scope.

**Sebastian Duesing** (LJI, Peters Lab): 2nd ranked contributor (299 commits). The
operational backbone -- filed #1869 (only 5 of ~200 data transformation terms in templates),
#1857 (COB transition), #1847 (specimen hierarchy cleanup). He's the person who would
actually build the templates for any new terms. Getting his buy-in on the DOSDP/template
approach for computational workflow terms is essential.

**Damien Goutte-Gattat** (German BioImaging, ODK): Infrastructure/build expert, not an
OBI content contributor. Relevant for build pipeline questions but won't have opinions on
term scope.

**jmfostel** (NIEHS): Filed #1910 (cell count assay) and several recent assay/measurement
issues (#1963, #1962, #1960, #1966). Active in adding clinical assay terms. Represents the
"biomedical" side of OBI -- your proposal shows the environmental side deserves equal attention.

### Read on the Room

| Person | Will want | Will push back on |
|---|---|---|
| Chris Mungall | Core concepts, simple axioms, no shadows, DOSDP templates | Over-axiomatization, shadow hierarchies |
| James Overton | Template-driven additions, clean builds, proper pattern | Anything that breaks the build or doesn't follow conventions |
| Bjoern Peters | Generalizing existing terms, practical annotation | Unnecessary abstraction layers |
| Chris Stoeckert | Well-documented terms, proper attribution, governance | Scope creep without process |
| Damion Dooley | Broadening scope (already asked about assembly datums) | Overly narrow biomedical framing |
| Sebastian Duesing | Template-driven additions (owns the templates) | Ad-hoc additions that bypass templates |
| jmfostel | Well-defined assays with measurement datums | May feel environmental terms dilute clinical focus |

### Your Sweet Spot

"Lightweight computational workflow terms with just enough structure to classify and
distinguish workflow types" hits all four:
- Simple enough for Chris M (no shadows, no Rococo OWL)
- Template-able for James (DOSDP or assays.tsv pattern)
- Generalizing for Bjoern (broadening OBI beyond clinical)
- Well-defined for Chris S (proper definitions, provenance)

Don't propose 50 new terms. Propose 5-7 core concepts (metagenome assembly, genome binning,
taxonomic classification, gene prediction, functional annotation, read quality assessment,
metatranscriptome assembly) and ask the group how they'd like them axiomatized.

## Agenda Doc

https://docs.google.com/document/d/1eEutJAG56gncTsWf2sAqHa4a9pQAuCbhsg_kmbF78tw/edit
