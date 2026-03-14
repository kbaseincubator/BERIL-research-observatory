# PDB Collection for BERDL

Status: **Complete.** Both tables ingested into `kescience_pdb` on 2026-03-14.

## What This Is

Protein Data Bank (PDB) experimental structure metadata for BERDL. Provides resolution, R-factors, experimental method, organism, and PDB→UniProt mapping for all ~250K deposited structures. Complements AlphaFold (predicted structures) with experimental data.

## Database

**Database**: `kescience_pdb`

| Table | Rows (est.) | Description |
|-------|-------------|-------------|
| `pdb_entries` | 250,741 | One row per PDB entry (method, resolution, R-factors, organism) |
| `pdb_uniprot_mapping` | 966,977 | PDB chain → UniProt accession mapping (from SIFTS) |

Schema documentation: [docs/schemas/pdb.md](../../docs/schemas/pdb.md)

## Data Sources

| Source | URL | Description |
|--------|-----|-------------|
| RCSB Holdings API | `data.rcsb.org/rest/v1/holdings/current/entry_ids` | All current PDB IDs |
| RCSB GraphQL API | `data.rcsb.org/graphql` | Batch metadata queries (1000 IDs/request) |
| SIFTS | `ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/tsv/pdb_chain_uniprot.tsv.gz` | PDB→UniProt mapping |

## Cross-Collection Links

- **AlphaFold**: `kescience_alphafold.alphafold_entries` — join on `uniprot_accession`
- **Pangenome**: `kbase_ke_pangenome.bakta_annotations` — join via `REPLACE(uniref100, 'UniRef100_', '')` → `uniprot_accession`
- **Structural biology projects**: `kescience_structural_biology.structure_projects` — join on `pdb_id` or `uniprot_accession`

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/download_pdb_data.py` | Fetch metadata from RCSB GraphQL API + SIFTS (~3 min) |
| `scripts/pdb_collection.json` | BERDL ingestion config for 2 Delta Lake tables |
| `scripts/ingest_pdb.py` | Upload TSVs to MinIO + run Delta Lake ingestion |

## Usage

```bash
module load python

# Download (~3 min for 250K entries)
python3 scripts/download_pdb_data.py --output-dir /pscratch/sd/p/psdehal/pdb_collection/

# Test with small sample first
python3 scripts/download_pdb_data.py --output-dir /tmp/pdb_test/ --sample 100

# Ingest into BERDL (requires active Spark session)
python3 scripts/ingest_pdb.py
```

## Scratch Data Location

`/pscratch/sd/p/psdehal/pdb_collection/`
