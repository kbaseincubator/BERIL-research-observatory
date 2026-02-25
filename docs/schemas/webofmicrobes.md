# Web of Microbes Module

## Overview
Web of Microbes (WoM) is a curated microbial exometabolomics database that records which metabolites microorganisms produce or amplify when grown in defined environments. It links organisms to their extracellular metabolic activities through mass spectrometry-based measurements.

**Database**: `kescience_webofmicrobes`
**Generated**: 2026-02-23
**Source**: [Web of Microbes](https://webofmicrobes.org/) (Kosina et al., BMC Microbiology 2018)
**Snapshot**: 2018 archived version (from Wayback Machine)

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `compound` | 589 | Metabolite identities with formula, mass, and chemical identifiers |
| `environment` | 10 | Growth media and conditions (R2A, BG11 variants, A+ minimal, ZMMG) |
| `organism` | 37 | Organisms including ENIGMA groundwater isolates, biocrust isolates, E. coli, Synechococcus |
| `project` | 5 | Published ENIGMA studies with DOIs |
| `observation` | 10,744 | Metabolite action assertions (Increased, Emerged, No change, Detected) |

## Key Table Schemas

### observation
Core data table linking organisms, metabolites, and environments with measured actions.
| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Observation ID |
| `organism_id` | int | FK to organism table |
| `compound_id` | int | FK to compound table |
| `environment_id` | int | FK to environment table |
| `action` | string | Metabolite action: I=Increased, E=Emerged (de novo), N=No change, D=Detected (control only) |
| `confidence` | int | Confidence score (1-5) |
| `project_id` | int | FK to project table |
| `entered_by` | string | Curator username |
| `doi` | string | Associated publication DOI |

### compound
Metabolite identities.
| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Compound ID |
| `compound_name` | string | Metabolite name (e.g., "glutamine", "Adenine", "Unk_331.2834p_...") |
| `formula` | string | Molecular formula |
| `neutralmass` | double | Neutral mass |
| `pubchem_id` | int | PubChem compound ID |
| `inchi_key` | string | InChI key |
| `smiles_string` | string | SMILES structural notation |

### organism
Microbial strains and controls.
| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Organism ID (1 = "The Environment" control) |
| `common_name` | string | Organism name (e.g., "Pseudomonas sp. (FW300-N2E3)") |
| `NCBI_taxid` | int | NCBI taxonomy ID |

## Action Encoding

WoM uses different action semantics for controls vs organisms:

| Actor | Action | Meaning |
|-------|--------|---------|
| Control ("The Environment") | D | Detected in starting medium |
| Control ("The Environment") | N | Not detected in starting medium |
| Organisms | I | Increased — metabolite was in medium, level went up |
| Organisms | E | Emerged — metabolite was NOT in medium, now detected (de novo production) |
| Organisms | N | No significant change vs control |

**E and I are mutually exclusive** — zero overlap across all observations. There is no "Decreased" (consumption) action for any organism in this 2018 snapshot.

## Cross-Collection Links

| Target Collection | Join Key | Notes |
|-------------------|----------|-------|
| `kescience_fitnessbrowser` | Organism name → FB strain (2 direct: FW300-N2E3, GW456-L13; 1 same-strain: BW25113/Keio) | ENIGMA isolate overlap |
| `kbase_msd_biochemistry` | Compound name/formula → molecule name/formula | 69 exact name + 107 formula matches |
| `kbase_ke_pangenome` | Organism genus → pangenome species clade | All WoM genera represented |

## Known Limitations
- 2018 frozen snapshot — newer data may exist on GNPS2 (wom-chat.gnps2.org)
- No consumption (decrease) data for any organism
- 56% of metabolites are unidentified (Unk_* prefix)
- E. coli BW25113 has only 12 observations (sulfur metabolism focus)
