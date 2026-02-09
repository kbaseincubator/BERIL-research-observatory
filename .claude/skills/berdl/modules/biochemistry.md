# Biochemistry Module

## Overview

ModelSEED biochemistry reference data for metabolic modeling.

**Database**: `kbase_msd_biochemistry`

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `reaction` | 56,012 | Biochemical reactions with thermodynamic data |
| `molecule` | 45,708 | Chemical compounds and metabolites |
| `reagent` | 262,517 | Reaction-molecule relationships (stoichiometry) |
| `structure` | 97,490 | Molecular structures (SMILES, InChIKey) |
| `reaction_similarity` | 671M+ | Pairwise reaction similarity scores |

## Key Table Schemas

### reaction
| Column | Type | Description |
|--------|------|-------------|
| `id` | string | ModelSEED reaction ID (e.g., `seed.reaction:rxn00001`) |
| `name` | string | Full reaction name |
| `abbreviation` | string | Short name or EC-based abbreviation |
| `deltag` | float | Gibbs free energy change (kJ/mol) |
| `deltagerr` | float | Uncertainty in deltaG |
| `is_transport` | boolean | Whether reaction is a transport reaction |
| `reversibility` | string | `>` (forward), `<` (reverse), `=` (reversible), `?` (unknown) |
| `source` | string | Data source (Primary Database, Secondary Database) |
| `status` | string | Validation status (OK, CPDFORMERROR, etc.) |

### molecule
| Column | Type | Description |
|--------|------|-------------|
| `id` | string | ModelSEED compound ID (e.g., `seed.compound:cpd00001`) |
| `name` | string | Compound name |
| `abbreviation` | string | Short name |
| `formula` | string | Molecular formula |
| `charge` | int | Net charge |
| `mass` | float | Molecular mass |
| `deltag` | float | Gibbs free energy of formation |
| `deltagerr` | float | Uncertainty in deltaG |
| `smiles` | string | SMILES structure |
| `inchikey` | string | InChIKey identifier |
| `pka` | string | Acid dissociation constants |
| `pkb` | string | Base dissociation constants |
| `source` | string | Data source |

### reagent
| Column | Type | Description |
|--------|------|-------------|
| `reaction_id` | string | FK to reaction.id |
| `molecule_id` | string | FK to molecule.id |
| `compartment_index` | int | Cellular compartment (0=cytoplasm) |
| `stoichiometry` | float | Coefficient (negative=reactant, positive=product) |

### structure
| Column | Type | Description |
|--------|------|-------------|
| `molecule_id` | string | FK to molecule.id |
| `type` | string | Structure type (SMILES, InChIKey) |
| `value` | string | Structure string |

## Table Relationships

```
reagent.reaction_id -> reaction.id
reagent.molecule_id -> molecule.id
structure.molecule_id -> molecule.id
```

## Common Query Patterns

### Get Reactions by Name Pattern
```sql
SELECT id, name, abbreviation, deltag, reversibility
FROM kbase_msd_biochemistry.reaction
WHERE name LIKE '%kinase%'
LIMIT 20
```

### Get Compound Information with Structure
```sql
SELECT m.id, m.name, m.formula, m.mass, m.smiles, s.value as inchikey
FROM kbase_msd_biochemistry.molecule m
LEFT JOIN kbase_msd_biochemistry.structure s
  ON m.id = s.molecule_id AND s.type = 'InChIKey'
WHERE m.name LIKE '%glucose%'
LIMIT 20
```

### Get Reaction Stoichiometry
```sql
SELECT
  r.id as reaction_id,
  r.name as reaction_name,
  m.name as compound,
  rg.stoichiometry,
  CASE WHEN rg.stoichiometry < 0 THEN 'reactant' ELSE 'product' END as role
FROM kbase_msd_biochemistry.reaction r
JOIN kbase_msd_biochemistry.reagent rg ON r.id = rg.reaction_id
JOIN kbase_msd_biochemistry.molecule m ON rg.molecule_id = m.id
WHERE r.id = 'seed.reaction:rxn00001'
ORDER BY rg.stoichiometry
```

### Find Thermodynamically Favorable Reactions
```sql
SELECT id, name, deltag, deltagerr
FROM kbase_msd_biochemistry.reaction
WHERE deltag < -10 AND deltag > -10000000
ORDER BY deltag ASC
LIMIT 20
```

### Find Transport Reactions
```sql
SELECT id, name, reversibility
FROM kbase_msd_biochemistry.reaction
WHERE is_transport = true
LIMIT 20
```

### Find Reactions by EC Number
```sql
SELECT id, name, abbreviation
FROM kbase_msd_biochemistry.reaction
WHERE abbreviation LIKE '%2.7.1.%'
LIMIT 20
```

### Get Compounds by Formula
```sql
SELECT id, name, formula, mass, charge
FROM kbase_msd_biochemistry.molecule
WHERE formula = 'C6H12O6'
```

## Linking to Pangenome Data

The pangenome `eggnog_mapper_annotations` table contains functional annotations that can link genes to biochemistry:

| Pangenome Column | Potential Biochemistry Link |
|------------------|----------------------------|
| `EC` | Match reaction abbreviations |
| `KEGG_ko` | KEGG ortholog IDs |
| `KEGG_Reaction` | KEGG reaction IDs |
| `BiGG_Reaction` | BiGG reaction IDs |
| `KEGG_Pathway` | Pathway identifiers |

**Note**: Direct linking requires external mapping tables. ModelSEED uses its own ID system (`seed.reaction:*`, `seed.compound:*`). Some reaction abbreviations contain EC numbers (e.g., `2.7.1.150-RXN.c`) that can be pattern-matched.

## Pitfalls

- **reaction_similarity is huge**: 671M+ rows. Avoid full table scans. Always filter by reaction_id.
- **ID format**: ModelSEED IDs use prefix format: `seed.reaction:rxn00001`, `seed.compound:cpd00001`
- **deltag outliers**: Some reactions have extreme deltaG values. Filter with `deltag > -10000000` to exclude erroneous data.
- **NULL structures**: Not all molecules have SMILES or InChIKey. Use LEFT JOIN when querying structures.
