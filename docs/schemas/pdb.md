# PDB Schema (`kescience_pdb`)

Database: `kescience_pdb`
Location: On-prem Delta Lakehouse (BERDL)
Tenant: kescience
Last Updated: 2026-05-05
Verified: Ingested 2026-03-14 (250,741 entries + 966,977 mappings + 5 extended tables)

## Overview

Experimental structure metadata from the Protein Data Bank. Contains ~250K deposited structures with resolution, R-factors, experimental method, organism, and PDB→UniProt chain mapping from SIFTS. Enables cross-collection queries linking pangenome annotations and AlphaFold predictions to experimental structures.

**Database**: `kescience_pdb`
**Source**: RCSB PDB GraphQL API + EBI SIFTS + RCSB CDN sequence clusters
**Scale**: 8 tables, ~12.9M total rows

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `pdb_entries` | 250,741 | One row per PDB entry — core metadata |
| `pdb_uniprot_mapping` | 966,977 | PDB chain → UniProt accession (from SIFTS) |
| `pdb_validation` | 250,741 | wwPDB validation metrics (clashscore, Ramachandran, rotamers) |
| `pdb_taxonomy` | 250,741 | NCBI taxonomy ID and organism per PDB entry |
| `pdb_ligands` | 455,897 | Co-crystallized small molecules (ligand id, name, formula, weight) |
| `pdb_citations` | 296,528 | Primary and secondary citations (PubMed IDs, DOIs, authors) |
| `pdb_pfam` | 990,166 | PDB chain → Pfam domain mapping (from SIFTS) |
| `pdb_sequence_clusters` | 9,532,482 | Pre-computed RCSB sequence clusters at 30/50/70/90/95/100% identity |

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

### pdb_validation

wwPDB validation metrics from RCSB GraphQL API (`pdbx_vrpt_summary_geometry`). One row per PDB entry.

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession — FK to `pdb_entries.pdb_id` |
| `clashscore` | FLOAT | All-atom clashscore |
| `percent_ramachandran_outliers` | FLOAT | % Ramachandran outliers |
| `percent_rotamer_outliers` | FLOAT | % rotamer outliers |
| `angles_rmsz` | FLOAT | RMS Z-score for bond angles |
| `bonds_rmsz` | FLOAT | RMS Z-score for bond lengths |

### pdb_taxonomy

NCBI taxonomy assignment from RCSB GraphQL `rcsb_entity_source_organism`. One row per PDB entry.

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession — FK to `pdb_entries.pdb_id` |
| `taxonomy_id` | INT | NCBI taxonomy ID |
| `organism` | STRING | Source organism scientific name |

### pdb_ligands

Co-crystallized small molecules and ions from RCSB GraphQL `nonpolymer_entities`. One row per (entry, ligand) pair.

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession — FK to `pdb_entries.pdb_id` |
| `ligand_id` | STRING | Three-letter chemical component ID (e.g., "HEM", "ATP") |
| `ligand_name` | STRING | Human-readable name |
| `ligand_type` | STRING | Component type (e.g., "non-polymer") |
| `formula` | STRING | Chemical formula |
| `formula_weight` | FLOAT | Molecular weight in Da |

### pdb_citations

Primary and secondary citations from RCSB GraphQL `citation`. Multiple rows per PDB entry.

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession — FK to `pdb_entries.pdb_id` |
| `citation_id` | STRING | Citation identifier within the entry |
| `is_primary` | STRING | "true" if this is the primary citation |
| `title` | STRING | Paper title |
| `year` | INT | Publication year |
| `journal` | STRING | Journal abbreviation |
| `volume` | STRING | Journal volume |
| `page_first` | STRING | First page |
| `doi` | STRING | DOI |
| `pubmed_id` | INT | PubMed ID |
| `authors` | STRING | Author list (semicolon-separated) |

### pdb_pfam

PDB chain → Pfam domain mapping from SIFTS (`pdb_chain_pfam.tsv.gz`). Multiple rows per (entry, chain).

| Column | Type | Description |
|--------|------|-------------|
| `pdb_id` | STRING | PDB accession — FK to `pdb_entries.pdb_id` |
| `chain_id` | STRING | Chain identifier |
| `uniprot_accession` | STRING | UniProt accession (links to AlphaFold, bakta) |
| `pfam_id` | STRING | Pfam family ID (e.g., "PF00001") |
| `coverage` | FLOAT | Domain coverage fraction |

### pdb_sequence_clusters

RCSB pre-computed sequence clusters at six identity thresholds. One row per (cluster, entity) at each identity level.

| Column | Type | Description |
|--------|------|-------------|
| `cluster_id` | STRING | Cluster identifier |
| `pdb_entity_id` | STRING | PDB entity ID (e.g., "1ABC_1") |
| `identity_level` | INT | Identity threshold: 30, 50, 70, 90, 95, or 100 |

## Cross-Collection Links

| Target Collection | Join Key | Notes |
|-------------------|----------|-------|
| `kescience_alphafold.alphafold_entries` | `pdb_uniprot_mapping.uniprot_accession = alphafold_entries.uniprot_accession` | Link experimental → predicted |
| `kbase_ke_pangenome.bakta_annotations` | `pdb_uniprot_mapping.uniprot_accession = REPLACE(bakta_annotations.uniref100, 'UniRef100_', '')` | Link pangenome → experimental |
| `kbase_ke_pangenome.bakta_annotations` (via Pfam) | `pdb_pfam.uniprot_accession = REPLACE(bakta_annotations.uniref100, 'UniRef100_', '')` | Domain-level link with Pfam ID |
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

### Validation quality by resolution

```sql
SELECT
  CASE
    WHEN pe.resolution < 1.5 THEN '< 1.5 A'
    WHEN pe.resolution < 2.0 THEN '1.5-2.0 A'
    WHEN pe.resolution < 3.0 THEN '2.0-3.0 A'
    WHEN pe.resolution < 4.0 THEN '3.0-4.0 A'
    ELSE '> 4.0 A'
  END AS resolution_bin,
  COUNT(*) AS n_structures,
  ROUND(AVG(pv.clashscore), 2) AS avg_clashscore,
  ROUND(AVG(pv.percent_ramachandran_outliers), 2) AS avg_rama_outliers,
  ROUND(AVG(pv.percent_rotamer_outliers), 2) AS avg_rota_outliers
FROM kescience_pdb.pdb_entries pe
JOIN kescience_pdb.pdb_validation pv ON pv.pdb_id = pe.pdb_id
WHERE pe.method = 'X-ray' AND pe.resolution IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

## Known Limitations

- `pdb_entries` contains one row per entry, not per chain — use `pdb_uniprot_mapping` for chain-level data
- `r_work` and `r_free` are NULL for non-X-ray methods (EM, NMR)
- `resolution` is NULL for NMR structures
- `organism` comes from the first polymer entity — multi-organism complexes show only one
- `pdb_beg`/`pdb_end` in SIFTS mapping can be "None" for unmapped regions
- SIFTS mapping covers SwissProt/TrEMBL UniProt accessions; some PDB chains lack UniProt mapping

## Changelog

- **2026-03-14**: Initial schema design, download, and ingestion. 250,741 PDB entries + 966,977 SIFTS mappings.
- **2026-03-14**: Extended ingestion (commit `7845f8e`): 5 additional tables — `pdb_taxonomy`, `pdb_ligands`, `pdb_citations`, `pdb_pfam`, `pdb_sequence_clusters`. Doc was not updated at the time.
- **2026-05-05**: Document the 5 extended tables ingested 2026-03-14.
