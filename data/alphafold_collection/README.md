# AlphaFold Protein Structure Collection for BERDL

## Status

**In progress.** Downloading and preparing AlphaFold metadata for ingestion.

### Goal

Bring AlphaFold protein structure metadata into BERDL as `kescience_alphafold` — a new database under the KE Science tenant. Phase 1 is metadata-only (linkage + quality info). Phase 2 (future) adds targeted structure retrieval for specific research questions.

### Data sources

| File | Source URL | Size | Description |
|------|-----------|------|-------------|
| `accession_ids.csv` | `https://ftp.ebi.ac.uk/pub/databases/alphafold/accession_ids.csv` | 7.9 GB | UniProt accession, residue range, AlphaFold ID, model version |
| `msa_depths.csv` | `https://ftp.ebi.ac.uk/pub/databases/alphafold/latest/msa_depths.csv` | 3.5 GB | MSA depth per entry (prediction quality proxy) |

### Delta Lake tables in `kescience_alphafold`

| Table | Rows (est.) | Description |
|-------|-------------|-------------|
| `alphafold_entries` | ~241M | UniProt accession, first/last residue, AlphaFold DB ID, model version |
| `alphafold_msa_depths` | ~241M | MSA depth per entry — higher depth = more confident prediction |

### Join patterns

AlphaFold is keyed by UniProt accession. Any BERDL collection with UniProt or UniRef references can join directly at query time:

```sql
-- Join bakta annotations to AlphaFold via UniRef100 → UniProt accession
SELECT b.gene_cluster_id, b.product, a.alphafold_id, a.first_residue, a.last_residue
FROM kbase_ke_pangenome.bakta_annotations b
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = REPLACE(b.uniref100, 'UniRef100_', '')
WHERE b.uniref100 IS NOT NULL
LIMIT 10;

-- Check MSA depth (prediction confidence) for linked structures
SELECT a.uniprot_accession, a.alphafold_id, m.msa_depth
FROM kescience_alphafold.alphafold_entries a
JOIN kescience_alphafold.alphafold_msa_depths m
  ON m.uniprot_accession = a.uniprot_accession
WHERE a.uniprot_accession = 'P12345';
```

### Phase 2: Targeted Structure Retrieval (Future)

When specific research questions require actual 3D coordinates:
- Use `alphafold_entries` to identify proteins of interest
- Download structures via AlphaFold API: `https://alphafold.ebi.ac.uk/api/prediction/{uniprot_accession}`
- Store coordinate files (PDB/mmCIF) in MinIO object storage
- Phenix workflows can then consume structures for refinement

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/download_alphafold_data.sh` | Download CSVs from EBI FTP to pscratch |
| `scripts/prepare_alphafold_tables.py` | Parse EBI CSVs into headerized TSVs for ingestion |
| `scripts/alphafold_collection.json` | Ingestion config with table schemas |
| `scripts/ingest_alphafold.py` | Upload TSVs to MinIO + run Delta Lake ingestion |

## Scratch data location

`/pscratch/sd/p/psdehal/alphafold_collection/`
