# PDB Schema (`kescience_pdb`)

Database: `kescience_pdb`
Location: On-prem Delta Lakehouse (BERDL)
Tenant: kescience
Last Updated: 2026-03-14
Verified: Schema designed, tables not yet ingested

## Overview

Experimental structure metadata from the Protein Data Bank. Contains ~250K deposited structures with resolution, R-factors, experimental method, organism, and PDB→UniProt chain mapping from SIFTS. Enables cross-collection queries linking pangenome annotations and AlphaFold predictions to experimental structures.

**Database**: `kescience_pdb`
**Source**: RCSB PDB GraphQL API + EBI SIFTS
**Scale**: ~250K entries, ~800K chain mappings

## Tables

| Table | Rows (est.) | Description |
|-------|-------------|-------------|
| `pdb_entries` | ~250K | One row per PDB entry — core metadata |
| `pdb_uniprot_mapping` | ~800K | PDB chain → UniProt accession (from SIFTS) |

## Key Table Schemas

### pdb_entries

One row per PDB entry. Core metadata including experimental method, resolution, R-factors, organism, and dates.

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession (e.g., "4HHB") — primary key |
| `title` | STRING | Structure title |
| `method` | STRING | Short method name (X-ray, EM, NMR, etc.) |
| `method_full` | STRING | Full method name (X-RAY DIFFRACTION, ELECTRON MICROSCOPY, etc.) |
| `resolution` | FLOAT | Resolution in Angstroms; NULL for NMR |
| `r_work` | FLOAT | R-work (X-ray only); NULL for EM/NMR |
| `r_free` | FLOAT | R-free (X-ray only); NULL for EM/NMR |
| `organism` | STRING | Source organism scientific name |
| `deposition_date` | STRING | Date deposited (YYYY-MM-DD) |
| `release_date` | STRING | Date released (YYYY-MM-DD) |
| `citation_doi` | STRING | Primary citation DOI |

### pdb_uniprot_mapping

PDB chain → UniProt accession mapping from SIFTS. This is the critical join table connecting experimental structures to AlphaFold predictions and pangenome annotations.

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession (uppercase) |
| `chain_id` | STRING | Chain identifier |
| `uniprot_accession` | STRING | UniProt accession — joins to AlphaFold, bakta |
| `res_beg` | INT | Residue begin |
| `res_end` | INT | Residue end |
| `pdb_beg` | STRING | PDB residue begin (can be "None") |
| `pdb_end` | STRING | PDB residue end (can be "None") |
| `sp_beg` | INT | UniProt sequence begin |
| `sp_end` | INT | UniProt sequence end |

## Cross-Collection Links

| Target Collection | Join Key | Notes |
|-------------------|----------|-------|
| `kescience_alphafold.alphafold_entries` | `pdb_uniprot_mapping.uniprot_accession = alphafold_entries.uniprot_accession` | Link experimental → predicted |
| `kbase_ke_pangenome.bakta_annotations` | `pdb_uniprot_mapping.uniprot_accession = REPLACE(bakta_annotations.uniref100, 'UniRef100_', '')` | Link pangenome → experimental |
| `kescience_structural_biology.structure_projects` | `pdb_entries.pdb_id = structure_projects.pdb_id` | Link to Phenix projects |

## Example Queries

### Find pangenome proteins with experimental structures

```sql
SELECT b.gene_cluster_id, b.product, b.species_id,
       pm.pdb_id, pe.method, pe.resolution
FROM kbase_ke_pangenome.bakta_annotations b
JOIN kescience_pdb.pdb_uniprot_mapping pm
  ON pm.uniprot_accession = REPLACE(b.uniref100, 'UniRef100_', '')
JOIN kescience_pdb.pdb_entries pe
  ON pe.pdb_id = pm.pdb_id
WHERE b.uniref100 IS NOT NULL
  AND pe.resolution < 3.0
LIMIT 20;
```

### Best search model for molecular replacement

```sql
SELECT pm.pdb_id, pe.resolution, pe.r_free, pe.method
FROM kescience_pdb.pdb_uniprot_mapping pm
JOIN kescience_pdb.pdb_entries pe ON pe.pdb_id = pm.pdb_id
WHERE pm.uniprot_accession = 'P0A6Y8'
  AND pe.method = 'X-ray'
ORDER BY pe.resolution ASC
LIMIT 5;
```

### Resolution distribution by method

```sql
SELECT method,
       COUNT(*) AS n_structures,
       ROUND(AVG(resolution), 2) AS avg_resolution,
       ROUND(MIN(resolution), 2) AS best_resolution
FROM kescience_pdb.pdb_entries
WHERE resolution IS NOT NULL
GROUP BY method
ORDER BY n_structures DESC;
```

### Proteins with both AlphaFold and experimental structures

```sql
SELECT af.uniprot_accession, af.mean_plddt,
       pe.pdb_id, pe.method, pe.resolution
FROM kescience_structural_biology.alphafold_structures af
JOIN kescience_pdb.pdb_uniprot_mapping pm
  ON pm.uniprot_accession = af.uniprot_accession
JOIN kescience_pdb.pdb_entries pe
  ON pe.pdb_id = pm.pdb_id
ORDER BY af.mean_plddt DESC
LIMIT 50;
```

## Known Limitations

- `pdb_entries` contains one row per entry, not per chain — use `pdb_uniprot_mapping` for chain-level data
- `r_work` and `r_free` are NULL for non-X-ray methods (EM, NMR)
- `resolution` is NULL for NMR structures
- `organism` comes from the first polymer entity — multi-organism complexes show only one
- `pdb_beg`/`pdb_end` in SIFTS mapping can be "None" for unmapped regions
- SIFTS mapping covers SwissProt/TrEMBL UniProt accessions; some PDB chains lack UniProt mapping

## Changelog

- **2026-03-14**: Initial schema design (2 tables). Scripts ready, tables not yet ingested.
