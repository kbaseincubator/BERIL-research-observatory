# Isolate Schema to NMDC-Schema Mapping and Conceptual Discrimination Analysis

Date: 2026-04-03
Source schema: `/home/mark/Downloads/entities-for-isolates.yaml` (from Alicia's 2026-04-01 whiteboard)
Target schema: `microbiomedata/nmdc-schema` (local: `~/gitrepos/nmdc-schema/`)
Context: OBI April 6 call prep, isolate modeling work (nmdc-schema#2803, #2884, #2885, #2892, #2898)

---

## Class-to-Class Mapping: Isolate Schema vs NMDC-Schema

| Isolate Schema Class | NMDC-Schema Class | Mapping Type | Notes |
|---|---|---|---|
| **Organism** | **OrganismSample** (partial) | broad | NMDC conflates organism identity with the sample. OrganismSample is "a material sample in which all cells share the same genome" -- it's a **sample**, not an organism. OBI:0100026 (organism) has no direct NMDC class equivalent. |
| **Strain** | slots on OrganismSample: `isolate_name`, `organism_genus`, `organism_species`, `subspecf_gen_lin`, `culture_type`, `type_strain` | decomposed | NMDC has no Strain class. Strain identity is scattered across 6+ slots on OrganismSample. |
| **Taxon** | `samp_taxon_id` slot (TextValue with CURIE) | slot | No Taxon class in NMDC. Taxonomy is a string-valued slot. |
| **Cell** | (no equivalent) | gap | NMDC does not model individual cells as entities. |
| **Community** | **Biosample** (partial) | broad | Environmental Biosamples implicitly represent communities. No explicit Community class. |
| **Colony** | `single_colony_isolation` slot (YesNoEnum) | slot | Colony is a boolean property on OrganismSample, not an entity. |
| **Population** | (no equivalent) | gap | NMDC has no population concept. |
| **Tissue** | (no equivalent; host-associated Biosample) | implicit | Plant/animal tissue would be a host-associated Biosample. |
| **Plasmid** | `extrachrom_elements` slot (integer count) | slot | Plasmid is a count, not an entity. |
| **Genotype** | slots: `genetic_mod`, `encoded_traits`, `gc_content`, `ploidy`, `reference_genome` | decomposed | No Genotype class. Genotypic info scattered across slots. |
| **Phenotype** | slots: `gram_stain`, `cell_shape`, `motility`, `sporulation`, `temperature_range`, `organism_color`, `carbon_source` | decomposed | No Phenotype class. Phenotypic info is GOLD-derived slots. |
| **Sample** | **Sample** (abstract) / **Biosample** | exact / close | NMDC `Sample` is abstract parent; `Biosample` is the environmental concrete class. |
| **TreatedSample** | **ProcessedSample** | close | ProcessedSample is_a Sample; carries `biomaterial_purity`, `dna_concentration`. |
| **Analyte** | slots on OrganismSample: `analyte_volume`, `sample_format`, `dnase_treated`, `dna_concentration` | decomposed | No Analyte class. Analyte properties live on OrganismSample (issue #2892 questions this). |
| **InstrumentPrepProcessing** | **PlannedProcess** subtypes: `LibraryPreparation`, `Extraction`, `NucleotideSequencing` | close | NMDC has rich process hierarchy under PlannedProcess (class_uri: OBI:0000011). |
| **ExperimentalTreatment** | (no equivalent) | gap | NMDC has no treatment/perturbation class. |
| **Site** | **FieldResearchSite** | close | NMDC uses `collected_from` linking Biosample/OrganismSample to FieldResearchSite. |
| **Command** | **Protocol** / `protocol_link` slot | close | NMDC has Protocol class with url/name/type. |

---

## The Core Conceptual Discrimination: How NMDC Colleagues Think Differently

### The fundamental tension

Alicia's whiteboard diagram separates **what the organism IS** (Organism, Strain, Taxon, Genotype, Phenotype, Plasmid) from **what was collected** (Sample, TreatedSample, Analyte) from **what was done to it** (InstrumentPrepProcessing, ExperimentalTreatment). These are three distinct entity types.

**NMDC-schema collapses the first two into one class: OrganismSample.**

OrganismSample is simultaneously:
- An organism identity (genus, species, strain, taxon)
- A biological characterization (gram stain, motility, cell shape)
- A physical sample (volume, container, format)
- A genome characterization (GC content, ploidy, reference genome)
- An environmental context (geo_loc_name, env_broad_scale)

This is the GOLD model transplanted into LinkML. GOLD's `organism_v2` table has 153 columns in one flat structure.

### Who thinks what

| Person | Conceptual Model | Evidence |
|---|---|---|
| **Alicia Clum** (JGI) | Organism-centric. Organisms have properties; samples are physical things you send to JGI. The whiteboard diagram (2026-04-01) cleanly separates organisms from samples. But JGI's *submission form* (v19) conflates them. | Whiteboard diagram, meeting notes (isolate-culture-meeting-notes-2026-04-01.md), nested `organism_metadata` in her YAML example |
| **Chris Mungall** (BBOP) | Ontologically rigorous. Wants clean separation of concerns. Raised the scope question (2026-03-23): "What portions of reality do we want to model?" Comfortable with class hierarchies. | isolate-modeling-open-questions-2026-03-23.md, nmdc-schema#2803 |
| **Montana Smith** | Pragmatic data modeler. Works with what JGI/GOLD provide. Present at 2026-04-01 meeting. | Meeting attendance |
| **Patrick Kalita** | Schema implementer. Built PR #2884 (OrganismSample). Took the pragmatic path: one class that captures everything JGI needs. | PR #2884, organism_sample.yaml |
| **Mark Miller** | Sees the OBI/BFO separation of concerns as correct but recognizes the pragmatic cost. Created flat alternative YAML to compare approaches. Has TURBO background (deep OBI). | obi-april-6-nmdc-perspective-2026-03-30.md, isolate-modeling-brief-2026-03-14.md |

### The three competing models

**Model A: "Everything is a Sample" (current NMDC)**
```
Sample (abstract)
  Biosample (environmental, multi-organism)
  OrganismSample (single-genome, conflated organism+sample)
  ProcessedSample (DNA extract, library)
```

**Model B: "Separate Organism from Sample" (Alicia's whiteboard / this schema)**
```
Organism → has_taxon → Taxon
Organism → has_genotype → Genotype
Organism → has_phenotype → Phenotype
Sample → derived_from → Organism
Sample → collected_from → Site
TreatedSample → result_of → ExperimentalTreatment
Analyte → extracted_from → Sample
```

**Model C: "OBI process graph" (TURBO-style, what OBI was designed for)**
```
material_sampling_process → has_specified_input → environmental_sample
material_sampling_process → has_specified_output → specimen
isolation_process → has_specified_input → specimen
isolation_process → has_specified_output → pure_culture
nucleic_acid_extraction → has_specified_input → pure_culture
nucleic_acid_extraction → has_specified_output → DNA_extract
```

### Where the models agree and disagree

| Question | Model A (NMDC) | Model B (Whiteboard) | Model C (OBI) |
|---|---|---|---|
| Is an organism the same as its sample? | Yes (OrganismSample) | No (separate classes) | No (organism is input to process) |
| Where does taxonomy live? | Slot on sample | Property of Organism | Property of organism, but organism participates in process |
| Where does phenotype live? | Slots on sample | Separate Phenotype class | Quality inhering in organism |
| Is a colony an entity? | No (boolean slot) | Yes (Colony class) | Yes (would be a population or material entity) |
| Is a community an entity? | No (implicit in Biosample) | Yes (Community class) | Yes (collection of organisms) |
| Is an analyte an entity? | No (slots on OrganismSample) | Yes (Analyte class) | Yes (material entity with analyte role) |

---

## OBI Bridge Opportunities

From `obi-april-6-nmdc-perspective-2026-03-30.md`, this isolate schema exercise directly serves the OBI call agenda:

### 1. The isolate schema makes explicit what NMDC leaves implicit

Every class in the isolate schema has OBI/OBO mappings. This demonstrates what *would* change if NMDC used OBI as a modeling framework (Model C) rather than just a vocabulary:

| Isolate Schema Class | OBI Mapping | Currently Used in NMDC? |
|---|---|---|
| Organism | OBI:0100026 (via COB:0000022) | Only as class_uri, not instantiated |
| InstrumentPrepProcessing | OBI:0000094 (material processing) | PlannedProcess uses OBI:0000011 |
| Sample | OBI:0100051 (specimen) | Yes, but as string mapping only |
| Analyte | OBI:0000275 (analyte role) | Not used |
| ExperimentalTreatment | Not in OBI (EFO:0000727) | Not used |
| Site | BFO:0000029 (site) | FieldResearchSite exists but no BFO mapping |

### 2. The IEDB comparison

The isolate schema is small enough to be a **proof-of-concept** for OBI-style modeling in NMDC. If NMDC adopted Model B or C for isolates:
- Tree-based UI filtering (like IEDB's Assay Finder) could navigate organism taxonomy
- Subsumption queries could find "all gram-negative isolates from soil" without string matching
- QC reasoning could catch classification errors (like IEDB's 20,000 corrections)

### 3. Concrete nmdc-schema issues this connects to

| Issue | How This Schema Relates |
|---|---|
| [nmdc-schema#2803](https://github.com/microbiomedata/nmdc-schema/issues/2803) | The parent issue for isolate modeling. This schema is an alternative Model B proposal. |
| [nmdc-schema#2884](https://github.com/microbiomedata/nmdc-schema/pull/2884) | PR that created OrganismSample (Model A). This schema shows what Model B would look like. |
| [nmdc-schema#2885](https://github.com/microbiomedata/nmdc-schema/issues/2885) | Subclasses of OrganismSample. This schema's Community/Colony/Population are candidates. |
| [nmdc-schema#2892](https://github.com/microbiomedata/nmdc-schema/issues/2892) | Analyte/container slot triage. This schema separates Analyte as its own class, resolving the question. |
| [nmdc-schema#2898](https://github.com/microbiomedata/nmdc-schema/issues/2898) | nmdc-schema vs submission-schema. This schema is schema-agnostic -- could inform either. |
| [nmdc-schema#2906](https://github.com/microbiomedata/nmdc-schema/issues/2906) | OBI audit. This schema's OBI mappings could seed the audit. |
| [nmdc-schema#2907](https://github.com/microbiomedata/nmdc-schema/issues/2907) | OLS4 embeddings for nmdc-schema. Already done for this schema -- method transferable. |

---

## Recommendation

Use this isolate schema as a **discussion artifact** for the next isolate modeling meeting. It makes the implicit disagreements explicit:

1. **Alicia's whiteboard already shows Model B.** She thinks in terms of organisms, not samples-that-are-organisms. The JGI form conflates them only because forms are flat.

2. **Patrick's OrganismSample (PR #2884) implements Model A.** It works, but it inherits the GOLD flat-table pattern that makes it hard to reason about what's an organism property vs a sample property.

3. **This schema bridges to OBI (Model C)** via the mappings already added. It shows what a principled separation of concerns looks like without requiring full OBI ABox reasoning.

The pragmatic path forward is probably:
- Keep OrganismSample as the NMDC implementation (Model A) for near-term JGI submission support
- Use this schema's class/slot separation to inform which OrganismSample slots should eventually migrate to proper classes (Analyte, Phenotype, etc.) as NMDC matures
- Use the OBI mappings to ground the April 6 discussion about what "using OBI" could mean in practice

---

## Additional Findings from Full-Source Research

### GitHub Issues (beyond the ones already cited)

- [nmdc-schema#2925](https://github.com/microbiomedata/nmdc-schema/issues/2925) -- bacteria isolated from soil example (open, 2026-03-31)
- [nmdc-schema#2926](https://github.com/microbiomedata/nmdc-schema/issues/2926) -- isolate modeling: syncom example (open, 2026-03-31)
- [nmdc-schema#2927](https://github.com/microbiomedata/nmdc-schema/pull/2927) -- Isolate from culture example PR (open, reviewed by Chris Mungall)
- [nmdc-schema#2928](https://github.com/microbiomedata/nmdc-schema/pull/2928) -- Update genbank identifier modeling (Alicia, April 2)
- [microbiomedata/issues#1573](https://github.com/microbiomedata/issues/issues/1573) -- "1.3 Modeling of microbial isolates" (2026 Milestone)
- [nmdc-schema#2912](https://github.com/microbiomedata/nmdc-schema/issues/2912) -- Ground mass spec/chromatography enums in OBI
- [nmdc-schema#2913](https://github.com/microbiomedata/nmdc-schema/issues/2913) -- Use OWL axiom decomposition to refine embeddings matches
- [nmdc-schema#2921](https://github.com/microbiomedata/nmdc-schema/issues/2921) -- Document ontology governance policy
- [nmdc-schema#535](https://github.com/microbiomedata/nmdc-schema/pull/535) -- biosample relations, OBI perspective (MERGED, historical)

### Slack Naming Debate (NMDC workspace DMs, 2026-03-17)

- **Mark**: "Is MicrobialIsolate acceptable to you as the name for the class?"
- **Alicia**: "MicrobialIsolate could be a subclass but would have many overlapping slots"
- **Alicia**: "fwiw GOLD models this as Organisms"
- **Mark**: "So Organism?" / "Or would the things we're representing always fit CulturedOrganism"
- This debate directly connects to this schema: this schema chose **Organism** + **Strain** as separate classes, with **Colony** and **Community** as siblings -- none of which exist in nmdc-schema.

### Key Google Docs

| Doc | Modified | Link |
|---|---|---|
| OrganismSample -- Briefing for Q3 Planning | 2026-04-01 | https://docs.google.com/document/d/11AYoy3ojN10Ct9qxL98oVCWc1GEOwKxVGicXdwwtX-A/edit |
| 20260401 isolate modeling hackathon | 2026-04-01 | https://docs.google.com/document/d/1PYNy6iRzsDZdvA_whfwbWz00T5kOeC05x_kBUhiI41E/edit |
| CMM isolate analysis pt 1 | 2026-02-20 | https://docs.google.com/document/d/18ViTbMFgDV5O51u5rmFANPKIvE0i4WQH9cj_rB_sPCI/edit |
| OBI Development Call Agenda 2026 | 2026-03-30 | https://docs.google.com/document/d/1eEutJAG56gncTsWf2sAqHa4a9pQAuCbhsg_kmbF78tw/edit |
| 2023-10-23 Mark consults with OBI on NMDC | 2024-09-26 | https://docs.google.com/document/d/19kd61sOEBvMzWfF95DeGaN1sCYir5wsmFrJPuGZzTvM/edit |
| OBI-COB Rollout | 2025-11-14 | https://docs.google.com/document/d/13U5rkEapyK0QcKzidWF47hPnqAMjslERmTk7sVyEGxo/edit |

### OBI Presentation (April 7)

`~/Desktop/markdown/obi-meeting-story-2026-04-07.md` documents 48 OBI references in nmdc-schema, identifies 5 computational gaps (read QC, genome binning, taxonomic classification, expression quantification, RB-TnSeq), and requests 5 new OBI terms. This isolate schema exercise directly feeds that presentation by demonstrating what OBI-grounded modeling looks like for isolate workflows.

### JGI Pupo Excel Data

`~/Downloads/JGI isolate metadata_Pupo.xlsx` contains 1,000 rows of real isolate submission data (fungus-growing ant isolates, Amycolatopsis sp.) across 55 JGI v19 columns. This is the empirical test data for validating whether the isolate schema's classes and slots can capture real-world submissions.

---

## Sources

- `~/Downloads/entities-for-isolates.yaml` -- this schema
- `~/gitrepos/nmdc-schema/src/schema/core.yaml` -- Biosample, OrganismSample, ProcessedSample, Sample definitions
- `~/gitrepos/nmdc-schema/src/schema/organism_sample.yaml` -- 90+ organism-specific slots
- `~/gitrepos/nmdc-schema/src/schema/basic_classes.yaml` -- PlannedProcess (OBI:0000011), Instrument (OBI:0000968)
- `~/Desktop/markdown/obi-april-6-nmdc-perspective-2026-03-30.md` -- OBI call research
- `~/Desktop/markdown/isolate-modeling-open-questions-2026-03-23.md` -- Chris 1:1 design questions
- `~/Desktop/markdown/isolate-modeling-brief-2026-03-14.md` -- Isolate modeling condensed brief
- `~/Desktop/markdown/isolate-culture-meeting-notes-2026-04-01.md` -- Alicia's meeting notes
- OLS4 LLM embeddings search results (120 mappings across 18 classes)
- nmdc-schema issues: #2803, #2884, #2885, #2892, #2898, #2906, #2907
