# ModelSEED Biochemistry Database Schema Documentation

**Database**: `kbase_msd_biochemistry`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: KBase
**Last Updated**: 2026-02-11

---

## Overview

ModelSEED biochemistry reference data for **metabolic modeling**. Contains curated biochemical reactions, compounds (molecules), stoichiometry, molecular structures, and pairwise reaction similarity scores.

Key data:
- 56,012 biochemical reactions with thermodynamic data
- 45,708 chemical compounds/metabolites
- 262,517 reagent (stoichiometry) records
- 97,490 molecular structures (SMILES, InChIKey)
- 671M+ pairwise reaction similarity scores

---

## Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `reaction` | 56,012 | Biochemical reactions with thermodynamic data |
| `molecule` | 45,708 | Chemical compounds and metabolites |
| `reagent` | 262,517 | Reaction-molecule relationships (stoichiometry) |
| `structure` | 97,490 | Molecular structures (SMILES, InChIKey) |
| `reaction_similarity` | 671M+ | Pairwise reaction similarity scores |

---

## Table Schemas

### `reaction`

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | **Primary Key**. ModelSEED reaction ID (e.g., `seed.reaction:rxn00001`) |
| `name` | string | Full reaction name |
| `abbreviation` | string | Short name or EC-based abbreviation |
| `deltag` | float | Gibbs free energy change (kJ/mol) |
| `deltagerr` | float | Uncertainty in deltaG |
| `is_transport` | boolean | Whether reaction is a transport reaction |
| `reversibility` | string | `>` (forward), `<` (reverse), `=` (reversible), `?` (unknown) |
| `source` | string | Data source (Primary Database, Secondary Database) |
| `status` | string | Validation status (OK, CPDFORMERROR, etc.) |

### `molecule`

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | **Primary Key**. ModelSEED compound ID (e.g., `seed.compound:cpd00001`) |
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

### `reagent`

| Column | Type | Description |
|--------|------|-------------|
| `reaction_id` | string | FK -> `reaction.id` |
| `molecule_id` | string | FK -> `molecule.id` |
| `compartment_index` | int | Cellular compartment (0=cytoplasm) |
| `stoichiometry` | float | Coefficient (negative=reactant, positive=product) |

### `structure`

| Column | Type | Description |
|--------|------|-------------|
| `molecule_id` | string | FK -> `molecule.id` |
| `type` | string | Structure type (SMILES, InChIKey) |
| `value` | string | Structure string |

### `reaction_similarity`

| Column | Type | Description |
|--------|------|-------------|
| (columns not fully verified) | | Pairwise reaction similarity scores |

---

## Key Relationships

```
reaction (56K)
    │
    └── 1:N → reagent (262K) → N:1 molecule (46K)
                                       │
                                       └── 1:N → structure (97K)
```

---

## Linking to Pangenome Data

The pangenome `eggnog_mapper_annotations` table contains functional annotations that can link genes to biochemistry:

| Pangenome Column | Potential Biochemistry Link |
|------------------|----------------------------|
| `EC` | Match reaction abbreviations |
| `KEGG_ko` | KEGG ortholog IDs |
| `KEGG_Reaction` | KEGG reaction IDs |
| `BiGG_Reaction` | BiGG reaction IDs |

**Note**: Direct linking requires external mapping tables. ModelSEED uses its own ID system (`seed.reaction:*`, `seed.compound:*`).

---

## Pitfalls

- **reaction_similarity is huge**: 671M+ rows. Always filter by reaction_id.
- **ID format**: ModelSEED IDs use prefix format: `seed.reaction:rxn00001`, `seed.compound:cpd00001`
- **deltag outliers**: Some reactions have extreme deltaG values. Filter with `deltag > -10000000`.
- **NULL structures**: Not all molecules have SMILES or InChIKey. Use LEFT JOIN when querying structures.

---

## Changelog

- **2026-02-11**: Migrated from docs/schema.md (biochemistry section) and skill module.
