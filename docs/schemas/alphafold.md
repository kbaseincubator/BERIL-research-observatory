# AlphaFold Collection Schema (`kescience_alphafold`)

## Overview

AlphaFold predicted protein structure metadata from the EBI AlphaFold Protein Structure Database. Contains UniProt-to-structure mappings and MSA depth (prediction quality proxy) for 241M entries. Metadata only — actual 3D coordinates can be retrieved on demand via the AlphaFold API.

**Database**: `kescience_alphafold`
**Ingestion date**: 2026-03-13
**Source**: [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/) (EBI), v6
**Source files**: `accession_ids.csv` (7.9 GB), `msa_depths.csv` (3.5 GB) from EBI FTP

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `alphafold_entries` | 241,070,489 | UniProt accession → AlphaFold structure ID mapping with residue range |
| `alphafold_msa_depths` | 241,070,489 | MSA depth per entry (prediction quality proxy) |

## Key Table Schemas

### alphafold_entries

Main table mapping UniProt accessions to AlphaFold predicted structure identifiers.

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_accession` | STRING | UniProt accession (e.g., `A8H2R3`) — primary key |
| `first_residue` | INT | First residue index (UniProt numbering) |
| `last_residue` | INT | Last residue index (UniProt numbering) |
| `alphafold_id` | STRING | AlphaFold DB identifier (e.g., `AF-A8H2R3-F1`) |
| `model_version` | INT | Model version number (currently all v6) |

### alphafold_msa_depths

Multiple Sequence Alignment depth per entry. Higher MSA depth generally correlates with more reliable structure predictions, as the model had more evolutionary information to work with.

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_accession` | STRING | UniProt accession — joins to `alphafold_entries` |
| `msa_depth` | INT | Number of sequences in the MSA used for prediction |

## Data Richness Summary

| Dimension | Value |
|-----------|-------|
| Total entries | 241,070,489 |
| Model version | v6 (all entries) |
| Protein length range | 16–2,700 residues |
| Average protein length | 329 residues |
| MSA depth range | 1–19,954 |
| Median MSA depth | 8,888 |
| Mean MSA depth | 9,141 |

### MSA Depth Distribution (Prediction Confidence)

| Confidence Tier | MSA Depth | Entries | % of Total |
|----------------|-----------|---------|------------|
| Low | < 30 | 20,885,937 | 8.7% |
| Medium | 30–299 | 21,606,227 | 9.0% |
| High | >= 300 | 198,578,325 | 82.4% |

82% of AlphaFold entries have high MSA depth (>= 300 sequences), indicating generally reliable predictions. The ~9% with low depth (< 30) should be treated with caution for structure-based analyses.

## Cross-Collection Links

| Target Collection | Join Key | Notes |
|-------------------|----------|-------|
| `kbase_ke_pangenome.bakta_annotations` | `REPLACE(uniref100, 'UniRef100_', '')` → `uniprot_accession` | Link pangenome clusters to AlphaFold structures |
| `kbase_ke_pangenome.bakta_db_xrefs` | `REPLACE(accession, 'UniRef100_', '')` → `uniprot_accession` (where `db LIKE 'UniRef%'`) | Alternative join path via cross-references |
| `kbase_uniref100.cluster` | `cluster_id` → `uniprot_accession` | UniRef100 cluster IDs are UniProt accessions |
| `kbase_uniprot` | Direct accession match | UniProt cross-references |

## Example Queries

### Link pangenome clusters to AlphaFold structures

```sql
SELECT
    b.gene_cluster_id,
    b.product,
    a.alphafold_id,
    a.first_residue,
    a.last_residue,
    m.msa_depth
FROM kbase_ke_pangenome.bakta_annotations b
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = REPLACE(b.uniref100, 'UniRef100_', '')
LEFT JOIN kescience_alphafold.alphafold_msa_depths m
  ON m.uniprot_accession = a.uniprot_accession
WHERE b.uniref100 IS NOT NULL
LIMIT 20;
```

### Find high-confidence structures for a protein product

```sql
SELECT a.uniprot_accession, a.alphafold_id, m.msa_depth,
       (a.last_residue - a.first_residue + 1) AS length
FROM kescience_alphafold.alphafold_entries a
JOIN kescience_alphafold.alphafold_msa_depths m
  ON m.uniprot_accession = a.uniprot_accession
WHERE m.msa_depth >= 1000
ORDER BY m.msa_depth DESC
LIMIT 20;
```

### Join via Bakta db_xrefs

```sql
SELECT
    x.gene_cluster_id,
    a.alphafold_id,
    a.model_version
FROM kbase_ke_pangenome.bakta_db_xrefs x
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = REPLACE(x.accession, 'UniRef100_', '')
WHERE x.db LIKE 'UniRef%'
LIMIT 20;
```

### Join via UniRef100 clusters

```sql
SELECT
    u.cluster_id,
    a.alphafold_id,
    m.msa_depth
FROM kbase_uniref100.cluster u
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = u.cluster_id
LEFT JOIN kescience_alphafold.alphafold_msa_depths m
  ON m.uniprot_accession = a.uniprot_accession
LIMIT 20;
```

## API Access (Phase 2 — Future)

Individual structures can be retrieved via the AlphaFold API:
```
https://alphafold.ebi.ac.uk/api/prediction/{uniprot_accession}
```

This returns JSON with download URLs for PDB, mmCIF, and PAE (Predicted Aligned Error) files. Future integration with Phenix structural biology tools could use this for targeted structure retrieval and refinement workflows.

## Known Limitations

- All entries are currently model version 6; the `model_version` column exists for future version tracking
- MSA depth is a proxy for prediction confidence but not a direct quality metric — pLDDT scores (per-residue confidence) are only available in the actual structure files, not in this metadata
- UniRef100 → UniProt accession join requires stripping the `UniRef100_` prefix, which is a string operation on every row; consider materializing a mapping table if performance is critical for large joins
- AlphaFold entries cover UniProt (primarily UniProtKB), not all protein sequences; proteins absent from UniProt will not have AlphaFold predictions
- Fragment models (where `first_residue > 1`) exist for very long proteins split into multiple predictions
