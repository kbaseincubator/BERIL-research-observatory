# Bakta Reannotation of Pangenome Cluster Representatives

## Status

**Phase: MinIO upload complete — ready for Delta Lake ingestion on JupyterHub.**

### What's done

- Annotated all **132,538,155** protein cluster representatives (from 27,690 species) using `bakta_proteins` v1.12.0 on NERSC Perlmutter
- Extracted per-chunk tables (176 chunks) and combined into 4 final TSVs
- Uploaded all files to MinIO at `s3a://cdm-lake/users-general-warehouse/psdehal/data/bakta_reannotation/`

### Final tables

| File | Rows | Size | Description |
|------|------|------|-------------|
| `bakta_annotations.tsv` | 132,538,155 | 18 GB | Main annotations: gene, product, EC, GO, COG, KEGG, UniRef, MW, pI |
| `bakta_db_xrefs.tsv` | 572,376,477 | 22 GB | Database cross-references (db, accession) |
| `bakta_pfam_domains.tsv` | 18,807,208 | 2.1 GB | Pfam domain hits with scores, e-values, coverage |
| `bakta_amr.tsv` | 83,008 | 8 MB | AMR gene annotations from AMRFinderPlus |
| `bakta_reannotation.json` | — | 2 KB | Ingestion config (schema definitions, paths) |

### Next step: Ingest into Delta Lake (on JupyterHub)

1. Open a JupyterHub terminal at `https://hub.berdl.kbase.us`
2. Update `ingest_bakta.py` paths to read from the user area:
   ```python
   FINAL_DIR = None  # not needed — files already on MinIO
   BRONZE_PREFIX = "users-general-warehouse/psdehal/data/bakta_reannotation"
   ```
   Or copy the files from user area to the tenant bronze path first:
   ```python
   # From JupyterHub (has tenant write access):
   from berdl_notebook_utils.minio_governance import get_minio_credentials
   # ... copy from users-general-warehouse to tenant-general-warehouse
   ```
3. Run `data_lakehouse_ingest` with the config JSON to create Delta Lake tables in `kbase_ke_pangenome`
4. Verify tables are queryable:
   ```sql
   SELECT COUNT(*) FROM kbase_ke_pangenome.bakta_annotations;
   -- expect 132,538,155
   ```

### MinIO paths

- **User staging area**: `s3a://cdm-lake/users-general-warehouse/psdehal/data/bakta_reannotation/`
- **Target bronze path**: `s3a://cdm-lake/tenant-general-warehouse/kbase_ke/datasets/pangenome/bakta/`
- **Target database**: `kbase_ke_pangenome`

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

### Key files on NERSC pscratch

- Chunks: `/pscratch/sd/p/psdehal/bakta_reannotation/chunks_2M/chunk_000.fasta` through `chunk_043.fasta`
- Raw results: `/pscratch/sd/p/psdehal/bakta_reannotation/results_2M/chunk_*/`
- Per-chunk tables: `/pscratch/sd/p/psdehal/bakta_reannotation/tables/chunk_*/`
- Final combined tables: `/pscratch/sd/p/psdehal/bakta_reannotation/tables/final/`

### Scripts

| Script | Purpose |
|--------|---------|
| `extract_bakta_tables.py` | Parse bakta TSV output into normalized tables per chunk |
| `combine_tables.py` | Concatenate per-chunk tables into final combined files |
| `ingest_bakta.py` | Upload to MinIO and run Delta Lake ingestion |
| `bakta_reannotation.json` | Ingestion config with table schemas |
