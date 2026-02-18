# ModelSEED Biochemistry Module

## Overview
ModelSEED biochemistry database containing reactions, compounds, and stoichiometry for metabolic modeling.

**Database**: `kbase_msd_biochemistry`
**Generated**: 2026-02-17
**Source**: ModelSEED

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `reaction` | 56,012 | Biochemical reactions with thermodynamic data |
| `molecule` | 45,708 | Chemical compounds with structures and properties |
| `reagent` | 262,517 | Stoichiometry linking reactions to molecules |
| `reaction_similarity` | 671M | Similarity scores between reactions |
| `structure` | 97,490 | Molecular structures (SMILES, InChI) |

## Key Table Schemas

### reaction
| Column | Type | Description |
|--------|------|-------------|
| `id` | string | ModelSEED reaction ID (seed.reaction:rxnXXXXX) |
| `name` | string | Enzyme name (systematic nomenclature) |
| `abbreviation` | string | External ID (often KEGG R number) - 80% coverage |
| `source` | string | Data provenance (Primary Database, Secondary Database, etc.) |
| `deltag` | float | Standard Gibbs free energy |
| `deltagerr` | float | Error in deltag |
| `reversibility` | string | Reaction directionality (>, <, =, ?) |
| `is_transport` | boolean | Whether reaction is a transport |
| `status` | string | Quality status (OK, etc.) |

### molecule
| Column | Type | Description |
|--------|------|-------------|
| `id` | string | ModelSEED compound ID (seed.compound:cpdXXXXX) |
| `name` | string | Compound name |
| `abbreviation` | string | Short name |
| `formula` | string | Chemical formula |
| `charge` | int | Net charge |
| `mass` | float | Molecular mass |
| `deltag` | float | Standard formation energy |
| `deltagerr` | float | Error in deltag |
| `inchikey` | string | InChI key for structure |
| `smiles` | string | SMILES notation |
| `pka` | string | Acid dissociation constants |
| `pkb` | string | Base dissociation constants |
| `source` | string | Data provenance |

### reagent
| Column | Type | Description |
|--------|------|-------------|
| `reaction_id` | string | Foreign key to reaction.id |
| `molecule_id` | string | Foreign key to molecule.id |
| `compartment_index` | int | Compartment (0=cytosol, 1=extracellular, etc.) |
| `stoichiometry` | float | Coefficient (negative=substrate, positive=product) |

## Table Relationships

- `reagent.reaction_id` → `reaction.id`
- `reagent.molecule_id` → `molecule.id`
- `structure.molecule_id` → `molecule.id`
- `reaction_similarity.reaction_1/2` → `reaction.id`

## EC Number Mapping

**CRITICAL LIMITATION**: The biochemistry database does **NOT** contain direct EC number → reaction mappings.

**What exists**:
- Reaction names use systematic enzyme nomenclature
- `abbreviation` field contains KEGG reaction IDs (RXNNNN) for 80% of reactions
- KEGG maps reactions to EC numbers externally

**Workarounds**:
1. Use KEGG annotations from eggNOG (KEGG_ko column) instead of EC
2. Focus on pathway-level analysis using GapMind predictions
3. Map essential genes to metabolic pathways rather than individual reactions

## Pitfalls

### 1. No EC Numbers in Database
- Reaction table has no `ec_numbers` column
- Cannot directly map EC numbers from eggNOG to reactions
- Use KEGG IDs (abbreviation field) or external mapping files

### 2. Large reaction_similarity Table
- Size: 671 million rows
- Full scans will timeout - always filter by reaction_1 or reaction_2 first

### 3. KEGG Abbreviations Not Complete
- Only 80.2% of reactions have abbreviations
- 11,108 reactions lack external IDs
