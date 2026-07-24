# DOE/LBL Datasets in BERDL: OBI Relevance Assessment

## Goal

Beyond NMDC, what other DOE/LBL-generated data in the lakehouse could interact with
or benefit from OBI? Focused on primary experimental data, not third-party reference databases.

## Fitness Browser (`kescience_fitnessbrowser`)

**Source**: Arkin lab (LBNL), DOE ENIGMA SFA and related projects  
**Scale**: 48 organisms, 7,552 experiments, 27M fitness scores  
**OBI relevance**: **HIGH**

Every experiment is an RB-TnSeq fitness assay — a specific `planned process` with:
- An organism (mutant library)
- A growth condition (media + chemical stressor/carbon source)
- An instrument (microplate reader, Tecan Infinite F200)
- A protocol (grow, extract barcodes, sequence, compute fitness)

The `experiment` table has rich metadata, all free text:

| Field | Example values | OBI could model? |
|---|---|---|
| `media` | LB, MOPS glucose, defined | Yes — `growth medium` |
| `vessel` | 48 well microplate; Tecan Infinite F200 | Yes — `instrument` |
| `temperature` | 25, 30, 37 | Yes — `temperature setting datum` |
| `aerobic` | Aerobic, Anaerobic | Yes — `oxygen availability specification` |
| `condition_1` | Nickel (II) chloride hexahydrate | Yes — CHEBI compound + OBI `material component` |
| `concentration_1` | 0.6 | Yes — `concentration measurement datum` |
| `units_1` | mM | Yes — `unit` |
| `expGroup` | stress, carbon source, nitrogen source | Yes — `study design` |

**The assay type itself** (RB-TnSeq / random barcode transposon sequencing) is not in OBI.
This is a DOE-developed high-throughput fitness assay used across ~100 papers. It would be
a natural term request:

- Parent: `OBI:0000070` (assay)
- Definition: "An assay that measures the fitness effect of disrupting each gene in a genome
  by growing a pool of randomly barcoded transposon mutants under a specific condition and
  quantifying barcode abundance changes via sequencing"

## KBase Phenotype (`kbase_phenotype`)

**Source**: KBase platform  
**Scale**: 4 experiments, 182K conditions, 28K measurements, 3 protocols  
**OBI relevance**: **MODERATE**

Small dataset but it has a `protocol` table (3 entries) and structured experimental design
(`experimental_variable`, `experimental_context`, `condition_set`). This is exactly the kind
of data OBI was designed to describe — experimental protocols with conditions and measurements.

Worth checking: do the 3 protocols reference OBI terms, or are they free text?

## PlanetMicrobe (`planetmicrobe_planetmicrobe`)

**Source**: iMicrobe / CyVerse, marine microbiology  
**Scale**: 2K samples, 6K experiments, 30 tables  
**OBI relevance**: **MODERATE**

Marine microbial ecology with campaign/sample/experiment structure. Likely has
instrument and method metadata for oceanographic sampling (CTD casts, Niskin bottles,
flow cytometry). These are standard OBI concepts.

## ENIGMA CORAL (`enigma_coral`)

**Source**: ENIGMA SFA (Arkin lab), DOE  
**Scale**: 3K taxa, 7K genomes, 45 tables  
**OBI relevance**: **HIGH** (but access denied from this session)

ENIGMA has process tables linking genomes → annotations → assemblies → reads → sequencing → strains
with full provenance (per NUC session notes). This is exactly the pattern where OBI terms
would add value. The NUC agent noted this is the model NMDC should follow.

## Pangenome (`kbase_ke_pangenome`)

**Source**: Paramvir Dehal (LBNL), built from GTDB r214  
**OBI relevance**: **LOW for OBI, HIGH for understanding DOE data**

The pangenome is a derived dataset (computational), not experimental. However:
- `pangenome_build_protocol` has protocol documentation — could reference OBI process terms
- The functional annotations (eggNOG, GapMind) are computational pipelines that could map
  to OBI data transformation terms

## Summary: OBI Opportunities in DOE Data

| Dataset | Experiments | Assay Type | OBI Status |
|---|---|---|---|
| Fitness Browser | 7,552 | RB-TnSeq fitness assay | No OBI term exists for RB-TnSeq |
| NMDC workflows | 385K files | 11 workflow types | Partial (assembly, annotation exist; binning, QC don't) |
| KBase Phenotype | 4 | Growth phenotyping | Unknown |
| ENIGMA CORAL | Unknown | Environmental microbiology | Unknown (no access) |
| PlanetMicrobe | 6K | Marine sampling + sequencing | Unknown |

**Key message for OBI meeting**: It's not just NMDC. The Fitness Browser alone has 7,552
experiments with no OBI type for the assay. DOE's experimental microbiology community is
generating massive structured experimental data that OBI could describe but currently doesn't.
