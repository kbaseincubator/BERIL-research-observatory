# kg-microbe, METPO, and OBI: Assessment Questions

## Context

Mark's longer-term vision is **OBI + METPO** as complementary ontology layers:
- **OBI** → study designs, assays, instruments, data transformations (the "how")
- **METPO** → microbial traits and phenotypes (the "what organisms can do")
- **CHEBI, GO, EC, etc.** → specificity (already used in kg-microbe and NMDC annotations)

The design principle for kg-microbe and METPO: **general-purpose assay and result classes
that offload specificity onto CHEBI, GO, EC, etc.** For example:
- "metabolite utilization assay" (OBI-level) + "lactose" (CHEBI) + "positive" (PATO)
- Not a single monolithic term for "lactose utilization positive"

## What BERDL Has (from Spark queries 2026-04-03)

### Ontology Store
| Ontology | In Store? | Terms |
|---|---|---|
| OBI | Yes | 4,422 |
| PATO | Yes | 2,869 |
| OMP (Ontology of Microbial Phenotypes) | Yes | 2,059 |
| CHEBI | Yes | 223,078 |
| GO | Yes | 51,811 |
| METPO | **No** | 0 |
| EDAM | **No** | 0 |
| SWO | **No** | 0 |

### Phenotype/Trait Data in BERDL

**BacDive** (`kescience_bacdive`):
- `metabolite_utilization`: 988K tests — `compound_name` (free text), `chebi_id` (sparse), `utilization` (+/-)
- `physiology`: gram stain, cell shape, motility, oxygen tolerance — all free text
- `enzyme`: 643K records
- No ontology IDs for assay types, result types, or phenotype classes

**NMDC trait tables** (`nmdc_arkin`):
- 4 trait sources: metaTraits, FAPROTAX, BactoTraits, IJSEM PhenoDB
- `trait_features`: 90+ functional group columns as booleans (fermentation, nitrogen_fixation, etc.)
- `trait_unified`: harmonized traits
- No OBI or METPO IDs anywhere

## Questions for Agents with Web Access

### About kg-microbe
1. Does kg-microbe currently use OBI for any assay/investigation modeling?
2. What ontologies does kg-microbe use for representing phenotype assertions? (METPO? OMP? Custom?)
3. How does kg-microbe model the relationship between a trait assertion, the assay that produced it, and the organism?
4. Check `CultureBotAI/KG-Microbe-search` for OBI imports or references

### About METPO
1. What OBI terms does METPO import or reference?
2. Does METPO define its own assay classes, or does it delegate to OBI?
3. How does METPO handle the pattern: "organism X was tested by assay Y and showed phenotype Z"?
4. Check `turbomam/microbial-traits-and-phenotypes-ontology` for OBI dependencies

### Architecture Questions
1. If kg-microbe wants to say "BacDive reports that strain X utilizes lactose", what's the ideal OBI + METPO + CHEBI representation?
2. Should METPO import OBI's assay hierarchy, or maintain a lightweight parallel set of assay classes?
3. Would loading METPO into `kbase_ontology_source` be useful? (Currently not there)
4. Would loading EDAM into `kbase_ontology_source` fill the computational workflow gap that OBI can't?

## Relevant BERDL Tables for Testing

If we want to test OBI + METPO annotation on real data:
- `kescience_bacdive.metabolite_utilization` — 988K tests, already has CHEBI links (sparse)
- `kescience_bacdive.physiology` — gram stain, cell shape, etc.
- `kescience_bacdive.enzyme` — 643K enzyme activity records
- `nmdc_arkin.trait_features` — 90+ boolean traits per sample
- `kescience_fitnessbrowser` — 27M fitness scores (quantitative phenotypes)
