# Isolate Entities Schema as OBI Bridge

Date: 2026-04-03

## How the Isolate Schema Connects OBI Coverage to Active NMDC Work

The `entities-for-isolates.yaml` schema was derived from Alicia Clum's whiteboard
diagram (2026-04-01 hackathon). It models 18 classes for the isolate workflow. This
document explains how it bridges the OBI coverage assessment to three active workstreams.

## Bridge 1: OBI Process Modeling (the "how")

The schema's process classes map directly to the OBI workflow gap analysis in
`OBI_NMDC_WORKFLOW_MAPPING.md`:

| Schema Class | OBI Mapping | Gap Status |
|---|---|---|
| InstrumentPrepProcessing | OBI:0000094 (material processing) | Covered |
| ExperimentalTreatment | EFO:0000727 (no OBI equivalent) | **Gap** -- OBI lacks experimental treatment as a planned process |
| Command | IAO:0000007 (action specification) | Covered via IAO |

The ExperimentalTreatment gap is notable. OBI models assays (measuring) and material
processing (transforming), but not experimental perturbation (exposing a sample to
conditions to observe response). OGMS:0000090 covers clinical treatment but not
research perturbation. This is a real OBI gap for microbiology -- antibiotic exposure
assays, growth condition experiments, and gene knockout studies all lack a clean OBI
home.

**Potential OBI term request:** "experimental perturbation" as a planned process with
specified input (sample) and specified output (treated sample), distinct from both
assay and material processing.

## Bridge 2: Trait/Phenotype Modeling (the "what")

The schema's biological characterization classes connect to the trait data landscape
documented in `KG_MICROBE_METPO_QUESTIONS.md`:

| Schema Class/Slot | BacDive Equivalent | GOLD Equivalent | OBI/METPO Term? |
|---|---|---|---|
| Phenotype | physiology table (free text) | gram_stain, motility, sporulation | OBI lacks phenotype; PATO has quality |
| Genotype | (none) | genetic_mod, encoded_traits | GENO:0000536 |
| colony_morphology | morphology table | organism_color | No OBI term |
| growth_medium | culture_conditions table | (none) | OBI:0000079 (growth medium) exists |
| optimal_growth_temperature | culture_conditions.temperature | temperature_range enum | No specific OBI term |
| analyte_type | (none) | (implicit in JGI submission) | OBI:0000275 (analyte role) |

The schema makes these trait/phenotype concepts **first-class entities** with typed
slots, rather than free-text fields on a flat record. This is exactly the
"general-purpose class + specificity from CHEBI/GO/PATO" pattern described in
`KG_MICROBE_METPO_QUESTIONS.md`.

For example, the schema's `Phenotype` class with `phenotype_value` and
`measurement_method` slots could represent:
- `{phenotype_description: "lactose utilization", phenotype_value: "positive", measurement_method: "API 20E strip"}`

This decomposes what BacDive stores as a single row in `metabolite_utilization`
into structured components that can be grounded to OBI (assay method), CHEBI
(compound), and PATO (quality).

## Bridge 3: Organism vs Sample Separation (the modeling question)

The OBI coverage work asks: "Is OBI a vocabulary or a modeling framework?"
The isolate schema makes this concrete:

- **Vocabulary path:** NMDC keeps OrganismSample as one flat class, uses OBI CURIEs
  as labels. The schema's OBI mappings (120 entries) feed nmdc-schema#2907.
- **Framework path:** NMDC separates Organism from Sample as distinct entities,
  linked by `derived_from`. Processes connect them via `has_input`/`has_output`.
  This is what OBI was designed for (TURBO did this).

The schema implements the framework path. The mapping analysis
(`isolate-schema-nmdc-mapping-analysis.md`) shows what NMDC would gain and lose
by adopting it.

## What This Means for the OBI April 7 Presentation

The isolate schema provides a **concrete example** for the OBI community:

1. Here is a real DOE/NMDC domain (isolate characterization)
2. Here are 18 entity types that researchers think about (Alicia's whiteboard)
3. Here are 120 OBI/OBO mappings discovered via OLS4 embeddings
4. Here is what the domain looks like when modeled as OBI intended (separate entities, typed relations)
5. Here is what it looks like in practice (NMDC's OrganismSample flat class)
6. The gap between 4 and 5 is the cost of the vocabulary-only path

This is more compelling than abstract arguments about modeling philosophy because
it's grounded in a real whiteboard from a real meeting with real domain experts.

## Connected Issues

- [nmdc-schema#2803](https://github.com/microbiomedata/nmdc-schema/issues/2803) -- Model isolates/organisms
- [nmdc-schema#2906](https://github.com/microbiomedata/nmdc-schema/issues/2906) -- OBI audit
- [nmdc-schema#2907](https://github.com/microbiomedata/nmdc-schema/issues/2907) -- OLS4 embeddings for schema elements
- [BERIL#186](https://github.com/kbaseincubator/BERIL-research-observatory/issues/186) -- OBI coverage project
