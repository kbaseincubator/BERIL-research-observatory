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

### ❌ CRITICAL LIMITATION: No EC → Reaction Mappings

**Discovered 2026-02-17**: The biochemistry database does **NOT** contain EC number → reaction mappings.

- The `reaction` table has NO `ec_numbers` column
- The `abbreviation` field contains KEGG reaction IDs (RXNNNN format) for ~80% of reactions
- KEGG database maps reactions to EC numbers, but that mapping is external to BERDL

### Available Linkages

| Pangenome Column | Biochemistry Link | Coverage | Status |
|------------------|------------------|----------|--------|
| `EC` | **NOT AVAILABLE** | N/A | ❌ No direct mapping in BERDL |
| `KEGG_ko` | Via KEGG (external) | Unknown | ⚠️ Requires external data |
| `KEGG_Reaction` | `reaction.abbreviation` | ~80% | ✅ Available (RXNNNN format) |
| `BiGG_Reaction` | Not present | N/A | ❌ Not in ModelSEED |

### Workarounds for EC-based Analysis

1. **Use KEGG annotations**: eggNOG provides `KEGG_ko` column which can link to `reaction.abbreviation`
2. **Pathway-level analysis**: Use GapMind pathway predictions instead of individual reactions
3. **External mapping**: Download EC→KEGG→ModelSEED mapping from KEGG/BiGG databases

**Note**: Direct linking requires external mapping tables. ModelSEED uses its own ID system (`seed.reaction:*`, `seed.compound:*`).

---

## Pitfalls

- **❌ NO EC MAPPINGS**: Cannot directly link eggNOG EC numbers to reactions. Use KEGG_ko or GapMind pathways instead.
- **reaction_similarity is huge**: 671M+ rows. Always filter by reaction_id.
- **KEGG abbreviations incomplete**: Only 80.2% of reactions have `abbreviation` field populated (44,904/56,012)
- **ID format**: ModelSEED IDs use prefix format: `seed.reaction:rxn00001`, `seed.compound:cpd00001`
- **deltag outliers**: Some reactions have extreme deltaG values. Filter with `deltag > -10000000`.
- **NULL structures**: Not all molecules have SMILES or InChIKey. Use LEFT JOIN when querying structures.

---

## Changelog

- **2026-02-17**: [essential_metabolome] Discovered NO EC→reaction mappings exist. Added CRITICAL LIMITATION section. Verified KEGG abbreviation coverage (80.2%). Documented workarounds for EC-based analysis.
- **2026-02-11**: Migrated from docs/schema.md (biochemistry section) and skill module.
