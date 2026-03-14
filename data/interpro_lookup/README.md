# InterPro Ingest for BERDL

Ingest the full InterPro protein annotation database as a permanent BERDL collection:
`kescience_interpro`.

## Why

InterPro pre-computes domain/family/site annotations for all ~250M UniProt proteins
using 14 member databases (Pfam, PRINTS, ProSite, SMART, CDD, etc.). Ingesting this
into BERDL enables cross-collection JOINs:

- **Pangenome proteins** → bakta UniRef100/90/50 → InterPro domains, GO terms
- **Fitness Browser genes** → pangenome link → InterPro functional families
- **Any UniProt accession** → full InterPro annotation

## Tables

| Table | Source | Rows (est.) | Description |
|-------|--------|-------------|-------------|
| `protein2ipr` | protein2ipr.dat.gz (16GB) | ~1.5B | UniProt acc → InterPro entry with domain boundaries (6 cols: uniprot_acc, ipr_id, ipr_desc, source_acc, start, stop) |
| `entry` | entry.list | ~50K | InterPro entry metadata (ID, type, name) |
| `go_mapping` | interpro2go | ~30K | InterPro entry → GO term mappings |

## Pipeline

| Script | Description | Runs on | Network? |
|--------|-------------|---------|----------|
| `02_download_interpro_bulk.sh` | Download from EBI FTP (16GB, resumable) | Any | Yes |
| `03_prepare_for_ingest.sh` | Add headers, parse entry.list + interpro2go to TSV | Any | No |
| `04_ingest_interpro.py` | Upload to MinIO + run data_lakehouse_ingest | JupyterHub | Yes (MinIO) |
| `05_assess_coverage.py` | Coverage report: pangenome × InterPro via Spark | JupyterHub | No |

## BERDL Paths

- **Tenant**: `kescience`
- **Database**: `kescience_interpro`
- **Bronze**: `s3a://cdm-lake/tenant-general-warehouse/kescience/datasets/interpro/`
- **Silver**: `s3a://cdm-lake/tenant-sql-warehouse/kescience/kescience_interpro.db`

## Checkpointing

- `02_download`: Uses `wget -c` for resumable downloads
- `04_ingest`: data_lakehouse_ingest handles Delta writes atomically

## Pangenome Coverage Estimate

From bakta_annotations (132.5M gene clusters):
- 46.4% have UniRef100 accessions (exact match, 56.9M unique accessions)
- 79.2% have UniRef50 accessions (≥50% identity, 17.6M unique accessions)
- 20.7% have no accession — would need full InterProScan

After ingest, coverage is assessed via:
```sql
SELECT COUNT(DISTINCT ba.gene_cluster_id)
FROM kbase_ke_pangenome.bakta_annotations ba
JOIN kescience_interpro.protein2ipr ip
  ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip.uniprot_acc
```

## InterPro Data Version

Current release: v108.0 (2026-01-29)
Source: https://ftp.ebi.ac.uk/pub/databases/interpro/current_release/
