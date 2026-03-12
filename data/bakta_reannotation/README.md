# Bakta Reannotation of Pangenome Cluster Representatives

## Status

**Complete.** All 4 tables ingested into `kbase_ke_pangenome` on 2026-03-12.

### What was done

1. Annotated all **132,538,155** protein cluster representatives (from 27,690 species) using `bakta_proteins` v1.12.0 on NERSC Perlmutter
2. Extracted per-chunk tables (176 chunks) and combined into 4 final TSVs
3. Uploaded TSVs to MinIO user staging area
4. Ingested into Delta Lake via `data_lakehouse_ingest` on JupyterHub

### Delta Lake tables in `kbase_ke_pangenome`

| Table | Rows | Description |
|-------|------|-------------|
| `bakta_annotations` | 132,538,155 | Main annotations: gene, product, EC, GO, COG, KEGG, UniRef, MW, pI |
| `bakta_db_xrefs` | 572,376,477 | Database cross-references (db, accession) |
| `bakta_pfam_domains` | 18,807,208 | Pfam domain hits with scores, e-values, coverage |
| `bakta_amr` | 83,008 | AMR gene annotations from AMRFinderPlus |

### Example queries

```sql
-- Get bakta annotation for a gene cluster
SELECT * FROM kbase_ke_pangenome.bakta_annotations
WHERE gene_cluster_id = 'JABHIP010000076.1_14';

-- Find all AMR genes
SELECT gene_cluster_id, amr_gene, amr_product, identity
FROM kbase_ke_pangenome.bakta_amr
ORDER BY identity DESC;

-- Count Pfam domain assignments
SELECT pfam_id, pfam_name, COUNT(*) as n_clusters
FROM kbase_ke_pangenome.bakta_pfam_domains
GROUP BY pfam_id, pfam_name
ORDER BY n_clusters DESC
LIMIT 20;

-- Cross-reference: find all KEGG links for a cluster
SELECT gene_cluster_id, db, accession
FROM kbase_ke_pangenome.bakta_db_xrefs
WHERE gene_cluster_id = 'JABHIP010000076.1_14'
  AND db = 'KEGG';
```

## Background

The `kbase_ke_pangenome` database has 1B gene cluster representatives but only eggNOG-based functional annotations. This reannotation adds Bakta's broader annotation pipeline:

- **UniProt lookups**: UPS (UniParc), IPS (InterPro), PSC/PSCC (UniRef clusters)
- **Pfam domain annotation**: HMM-based domain hits with coverage metrics
- **AMR detection**: AMRFinderPlus with identity/coverage scores
- **Cross-references**: Links to external databases (SO, UniRef, KEGG, COG, GO, EC, Pfam)
- **Physical properties**: Molecular weight and isoelectric point

### Software versions

- bakta: 1.12.0
- bakta DB: v6.0
- AMRFinderPlus: 4.2.7 (DB: 2026-01-21.1)
- HMMER: 3.4

### Key files on NERSC pscratch (ephemeral — may be purged)

- Chunks: `/pscratch/sd/p/psdehal/bakta_reannotation/chunks_2M/chunk_000.fasta` through `chunk_043.fasta`
- Raw results: `/pscratch/sd/p/psdehal/bakta_reannotation/results_2M/chunk_*/`
- Per-chunk tables: `/pscratch/sd/p/psdehal/bakta_reannotation/tables/chunk_*/`
- Final combined tables: `/pscratch/sd/p/psdehal/bakta_reannotation/tables/final/`

### Scripts

| Script | Purpose |
|--------|---------|
| `extract_bakta_tables.py` | Parse bakta TSV output into normalized tables per chunk |
| `combine_tables.py` | Concatenate per-chunk tables into final combined files |
| `ingest_bakta.py` | Original upload + ingest script (paths point to NERSC) |
| `run_ingest.py` | Final ingest script used for Delta Lake import (reads from MinIO user staging) |
| `bakta_reannotation.json` | Ingestion config with table schemas |

### Ingestion notes

- Tenant is `kbase` (not `kbase_ke`) — see pitfalls doc
- `data_lakehouse_ingest` auto-prepends tenant name to the dataset as a namespace prefix, so `dataset="ke_pangenome"` with `tenant="kbase"` produces `kbase_ke_pangenome`
- Ingestion of all 4 tables took ~20 minutes on JupyterHub Spark
- Staging TSVs on MinIO were deleted after successful ingestion
