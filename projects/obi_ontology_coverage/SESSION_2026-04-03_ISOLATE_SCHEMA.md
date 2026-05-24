# Session Log: Isolate Entities Schema and OBI Bridge

Date: 2026-04-03
Agent: Claude Opus 4.6 (1M context), NUC session

## What Was Done

1. **Transcribed Alicia Clum's whiteboard photo** (`entities-for-isolates.jpg`) from the 2026-04-01 hackathon into a list of classes and properties
2. **Built a LinkML schema** with 18 classes, 7 enums, 60+ slots, aliases, and descriptions
3. **Ran OLS4 embeddings search** (both lexical and LLM `llama-embed-nemotron-8b_pca512`) for all 18 classes using full descriptions as queries -- produced 120 ontology mappings across OBI, PCO, CL, UBERON, SO, GENO, IAO, BFO, EFO, NCIT, SNOMED, PATO, ENVO, GAZ, CHMO, AGRO, EDAM
4. **Disambiguated confusable class names** (Colony vs Community, Strain vs Organism, Tissue vs Sample, Analyte vs Sample)
5. **Mapped all 18 classes to nmdc-schema** (Biosample, OrganismSample, ProcessedSample, PlannedProcess, FieldResearchSite, Protocol) and documented where NMDC conflates what the schema separates
6. **Full-source research** across GitHub (13 searches), Slack (6 workspaces, 6 search terms), Gmail, Google Drive, desktop markdown, nmdc-schema source code, and memory files
7. **Identified three competing models** for organism/sample representation (flat OrganismSample vs separate entities vs OBI process graph)
8. **Added OBI+CHEBI+PATO phenotype decomposition** to the Phenotype class with PhenotypeCategoryEnum (17 categories from BacDive/GOLD patterns)
9. **Wrote bridge document** connecting isolate schema to OBI coverage findings
10. **Created P. putida KT2440 pTE314 example** from Montana's AMP2/OPAL use case
11. **Researched OPAL and AMP2** DOE BER projects and their relationship to isolate modeling

## Sources Consulted (ranked by usefulness)

### Tier 1: Essential -- drove the design

| Source | What It Provided |
|---|---|
| `~/Downloads/entities-for-isolates.jpg` | Alicia's whiteboard -- the source of truth for class inventory |
| `~/gitrepos/nmdc-schema/src/schema/core.yaml` | Biosample, OrganismSample, ProcessedSample, Sample class definitions. OrganismSample has 143 slot assignments. |
| `~/gitrepos/nmdc-schema/src/schema/organism_sample.yaml` | 90+ JGI/GOLD-specific slots, enums (BiosafetyMaterialCategoryEnum, CultureTypeEnum, etc.), structured_aliases. This is where the rubber meets the road for isolate modeling. |
| `~/Desktop/markdown/isolate-modeling-open-questions-2026-03-23.md` | 7 open design questions from Chris 1:1. The best single document for understanding the design space. |
| `~/Desktop/markdown/obi-april-6-nmdc-perspective-2026-03-30.md` | OBI as vocabulary vs framework. The TURBO contrast. The IEDB gold standard. |
| OLS4 LLM embeddings API (`/api/v2/classes/llm_search`) | 120 ontology mappings. Using full class descriptions as queries produced much better results than names alone. |
| Hackathon draw.io file (Google Drive `13GDwVpciMM3NGEmSeptWocHGGMUjFU08`) | 5 tabs from Bea, Sam, Montana, Sierra, and group consensus. Montana's P. putida KT2440 + pTE314 example. |

### Tier 2: Important context

| Source | What It Provided |
|---|---|
| Hackathon transcript (Google Doc `1PYNy6iRzsDZdvA_whfwbWz00T5kOeC05x_kBUhiI41E`) | 390K chars of discussion. Key: organism vs sample debate, naming (MicrobialIsolate vs Organism vs CulturedOrganism), Montana's Pseudomonas use case, Sierra's 6-starting-point test. |
| `~/Desktop/markdown/isolate-modeling-brief-2026-03-14.md` | Condensed brief reconciling JGI v19, MIxS MIGS-Ba, GOLD organism_v2. |
| `~/Desktop/markdown/isolate-culture-meeting-notes-2026-04-01.md` | Meeting notes: nested vs flat organism_metadata, YAML syntax issues. |
| `~/Desktop/markdown/obi-meeting-story-2026-04-07.md` | OBI presentation: 48 OBI references census, 5 computational gaps, RB-TnSeq gap. |
| `~/gitrepos/nmdc-schema/src/schema/basic_classes.yaml` | PlannedProcess (OBI:0000011), Instrument (OBI:0000968), DataGeneration subtypes. |
| NMDC Slack `#squad-isolates` channel | Alicia's hackathon planning, naming debate DMs with Mark. |
| Slack DMs Mark/Alicia (2026-03-17) | "MicrobialIsolate could be a subclass but would have many overlapping slots" / "fwiw GOLD models this as Organisms" |
| OLS4 lexical search API (`/api/search`) | Complemented embeddings search with exact-match results from specific ontologies. |

### Tier 3: Supporting

| Source | What It Provided |
|---|---|
| `~/Desktop/markdown/organism-sample-precedent-analysis-2026-03-18.md` | Four precedent systems compared. `host_*` semantics flip documented. |
| `~/Desktop/markdown/organism-sample-authority-overlap-2026-03-18.md` | Slot-by-slot authority attribution: MIxS 59, GOLD 94, JGI 26 slots. |
| `KG_MICROBE_METPO_QUESTIONS.md` (this project) | BacDive trait data: 988K metabolite_utilization tests, all free text. OBI+METPO vision. |
| `OBI_NMDC_WORKFLOW_MAPPING.md` (this project) | OBI computational term hierarchy. 5 real gaps identified. |
| `~/Downloads/JGI isolate metadata_Pupo.xlsx` | 1,000 rows of real JGI v19 submission data. Not read in detail but confirms field inventory. |
| Google Doc: OrganismSample Briefing (`11AYoy3ojN10Ct9qxL98oVCWc1GEOwKxVGicXdwwtX-A`) | Mark's design document for Q3 planning. Not read in detail this session. |
| AMP2 Workshop Report (PNNL-38129, July 2025) | AMP2 metadata standards not yet defined. Data Advisory Group forming. |
| nmdc-schema GitHub issues | #2803, #2884, #2885, #2892, #2898, #2906, #2907, #2912, #2913, #2921, #2925, #2926 |

### Sources that were NOT useful

| Source | Why |
|---|---|
| OLS4 embeddings results for "Organism" | Too generic -- returned microbial fuel cell bacteria, vaccine organisms, Drosophila. The class description query was much better. |
| SNOMED results generally | High noise. SNOMED models clinical procedures, not research workflows. Kept a few (Microbiological strain, Organism) but most were irrelevant. |
| Slack BER-CMM workspace | Zero relevant results for "isolate" or "OBI". |
| Gmail "biomaterial" search | One hit from 2021. Not useful. |

## What Further Research Would Help

### Already well-covered (no more research needed)

- OBI mapping landscape for the 18 classes
- nmdc-schema class hierarchy and slot inventory
- Hackathon design decisions and competing models
- OPAL/AMP2 project context

### Would benefit from more work

| Topic | Why | Suggested Approach |
|---|---|---|
| **Validate example YAML against schema** | The P. putida example is hand-written YAML, not validated against the LinkML schema. It uses `class:` keys that aren't standard LinkML instance format. | Convert to proper LinkML instance data and run `linkml-validate`. |
| **Read the hackathon draw.io tabs in detail** | I extracted labels and page names but didn't reconstruct the full graph topology of each diagram. Montana's and Sierra's tabs have specific edge semantics (has_input, has_output, derived_from) that should be compared to the schema's slot definitions. | Export draw.io to PNG/SVG via the Google Drive API, or parse the XML more carefully to extract edge source/target pairs. |
| **Read Mark's OrganismSample Briefing Google Doc** | Only referenced, not read this session. It's the design document for Q3 planning and may contain decisions that supersede the hackathon discussion. | `get_doc_content` on `11AYoy3ojN10Ct9qxL98oVCWc1GEOwKxVGicXdwwtX-A`. |
| **Compare with submission-schema** | The dual-schema question (#2898) requires understanding what submission-schema currently models. Not examined this session. | Read `~/gitrepos/nmdc-submission-schema/` if it exists locally, or `gh` clone. |
| **BacDive phenotype decomposition test** | The new OBI+CHEBI+PATO slots on Phenotype are theoretical. Testing them against real BacDive `metabolite_utilization` rows would validate the pattern. | Query BERDL `kescience_bacdive.metabolite_utilization` and attempt to map 10 rows to Phenotype instances. |
| **METPO alignment** | METPO (Microbial Eco-Trait Phenotype Ontology) is the trait ontology Mark co-maintains. The schema's Phenotype class should map to METPO terms, but METPO is not in OLS4. | Check METPO term inventory locally or via BioPortal. |
| **Alicia's Google Doc** (`1FADBHG8-y56fRDJdR6wz3lXDf1wTuDTAL_p_24GeVV4`) | Shared in #squad-isolates. Not read. May contain additional modeling decisions. | `get_doc_content`. |

## Files Added to Repo This Session

| File | Description |
|---|---|
| `data/entities-for-isolates.jpg` | Alicia's whiteboard photo |
| `data/entities-for-isolates.yaml` | LinkML schema: 18 classes, 8 enums, 70+ slots, 120 OBI/OBO mappings |
| `data/example-pseudomonas-putida-kt2440-pte314.yaml` | P. putida KT2440 + pTE314 AMP2/OPAL example (15 instances) |
| `isolate-schema-nmdc-mapping-analysis.md` | Class-by-class mapping to nmdc-schema, conceptual discrimination analysis |
| `ISOLATE_SCHEMA_OBI_BRIDGE.md` | Bridge document connecting schema to OBI coverage, traits, and modeling question |
| `SESSION_2026-04-03_ISOLATE_SCHEMA.md` | This file |
