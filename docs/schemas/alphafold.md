# AlphaFold Collection Schema (`kescience_alphafold`)

**Source**: [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/) (EBI)
**Ingestion date**: TBD
**Scale**: ~241M predicted protein structures

---

## Tables

### `alphafold_entries`

Main table mapping UniProt accessions to AlphaFold predicted structure identifiers.

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_accession` | STRING | UniProt accession (e.g., `A8H2R3`) — primary key |
| `first_residue` | INT | First residue index (UniProt numbering) |
| `last_residue` | INT | Last residue index (UniProt numbering) |
| `alphafold_id` | STRING | AlphaFold DB identifier (e.g., `AF-A8H2R3-F1`) |
| `model_version` | INT | Model version number |

**Source**: `accession_ids.csv` from EBI FTP (7.9 GB, ~241M rows)

### `alphafold_msa_depths`

Multiple Sequence Alignment depth per entry — a proxy for prediction confidence. Higher MSA depth generally correlates with more reliable structure predictions.

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_accession` | STRING | UniProt accession — joins to `alphafold_entries` |
| `msa_depth` | INT | Number of sequences in the MSA used for prediction |

**Source**: `msa_depths.csv` from EBI FTP (3.5 GB, ~241M rows)

---

## Cross-Collection Linkage

AlphaFold is keyed by UniProt accession. No dedicated bridge tables are needed — any BERDL collection with UniProt or UniRef references can join directly.

### Join via Bakta UniRef100 annotations

```sql
-- Link pangenome clusters to AlphaFold structures
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

### Join via Bakta db_xrefs

```sql
-- Link via database cross-references
SELECT
    x.gene_cluster_id,
    a.alphafold_id,
    a.model_version
FROM kbase_ke_pangenome.bakta_db_xrefs x
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = REPLACE(x.accession, 'UniRef100_', '')
WHERE x.db LIKE 'UniRef%';
```

### Join via UniRef100 clusters

```sql
-- UniRef100 cluster IDs are UniProt accessions
SELECT
    u.cluster_id,
    a.alphafold_id,
    m.msa_depth
FROM kbase_uniref100.cluster u
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = u.cluster_id
LEFT JOIN kescience_alphafold.alphafold_msa_depths m
  ON m.uniprot_accession = a.uniprot_accession;
```

---

## Coverage Notes

- AlphaFold DB covers ~241M UniProt entries (as of v6)
- Coverage is best for well-studied organisms (human, model organisms)
- MSA depth varies widely: low-depth entries may have less reliable predictions
- The `model_version` field tracks which AlphaFold model was used (v1-v4)

## API Access (Phase 2)

Individual structures can be retrieved via the AlphaFold API:
```
https://alphafold.ebi.ac.uk/api/prediction/{uniprot_accession}
```

This returns JSON with download URLs for PDB, mmCIF, and PAE files.
