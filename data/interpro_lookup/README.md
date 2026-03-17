# InterPro Ingest for BERDL

Ingest the full InterPro protein annotation database as a permanent BERDL collection:
`kescience_interpro`.

## Status

### Phase 1: Bulk Database Ingest — COMPLETE

The full InterPro v108.0 protein2ipr database has been ingested into BERDL:

| Table | Rows | Status |
|-------|------|--------|
| `kescience_interpro.protein2ipr` | 1,175,529,272 | Ingested |
| `kescience_interpro.entry` | 51,489 | Ingested |
| `kescience_interpro.go_mapping` | 30,200 | Ingested |

**Coverage of pangenome (132.5M gene clusters):**
- 38.5M clusters (29.0%) have InterPro entries via UniRef100/UniRef50 lookup
- Remaining 73.6M clusters need InterProScan annotation

### Phase 2: InterProScan on NERSC — READY TO RUN

Run InterProScan on all 132.5M cluster rep sequences at NERSC Perlmutter.
InterProScan's built-in lookup service will resolve ~54% of sequences from cache
(milliseconds each); only ~46% need full local analysis.

**Input files on MinIO** (ready to use):
```
cts/io/psdehal/bakta_reannotation/fasta_chunks_5M/
  chunk_000.fasta  ...  chunk_026.fasta   (27 files, 42.2 GB total)
  5M sequences per chunk, 132,538,155 total
```

**Job sizing:**
- 27 FASTA chunks × 500 sub-chunks of 10K sequences = ~13,500 jobs
- Each job: ~10K sequences, ~5,400 cache misses, ~1 hour wall time w/ 32 cores
- Total: ~13,500 node-hours on Perlmutter

See `scripts/07_nersc_interproscan.sh` for the SLURM job array script.

## Why

InterPro pre-computes domain/family/site annotations for all ~250M UniProt proteins
using 14 member databases (Pfam, PRINTS, ProSite, SMART, CDD, etc.). Ingesting this
into BERDL enables cross-collection JOINs:

- **Pangenome proteins** → bakta UniRef100/90/50 → InterPro domains, GO terms
- **Fitness Browser genes** → pangenome link → InterPro functional families
- **Any UniProt accession** → full InterPro annotation

## Tables

| Table | Source | Rows | Description |
|-------|--------|------|-------------|
| `protein2ipr` | protein2ipr.dat.gz (16GB) | 1.18B | UniProt acc → InterPro entry with domain boundaries (6 cols: uniprot_acc, ipr_id, ipr_desc, source_acc, start, stop) |
| `entry` | entry.list | 51K | InterPro entry metadata (ID, type, name) |
| `go_mapping` | interpro2go | 30K | InterPro entry → GO term mappings |

## Pipeline

| Script | Description | Runs on | Status |
|--------|-------------|---------|--------|
| `02_download_interpro_bulk.sh` | Download from EBI FTP (16GB, resumable) | Any | Done |
| `03_prepare_for_ingest.sh` | Add headers, parse entry.list + interpro2go to TSV | Any | Done |
| `04_ingest_interpro.py` | Upload to MinIO + run data_lakehouse_ingest | JupyterHub | Done |
| `05_assess_coverage.py` | Coverage report: pangenome × InterPro via Spark | JupyterHub | Done |
| `06_probe_lookup_service.py` | Probe EBI lookup cache to estimate hit rate | JupyterHub | Done (sample) |
| `07_nersc_interproscan.sh` | SLURM job array for InterProScan at NERSC | NERSC | Ready |
| `08_collect_results.py` | Collect InterProScan TSV results → BERDL ingest | JupyterHub | Ready |

## Lookup Service Probe Results

Probed the EBI pre-calculated match lookup service (MD5-based REST API) to estimate
how many sequences have cached InterProScan results vs. needing full analysis:

- **131,500 sequences probed** (sample of 73.6M unmatched)
- **54% cache hits** (71,051) — have pre-calculated results at EBI
- **46% cache misses** (60,449) — need full InterProScan analysis
- **0 errors** — API is reliable

**Key finding**: InterProScan's built-in lookup covers >500M proteins (vs. 166M in
protein2ipr.dat). Many proteins have member database hits (Pfam, CDD, etc.) that
aren't yet integrated into formal InterPro entries.

**Decision**: Run InterProScan directly at NERSC rather than spending 4+ days on
API probing. InterProScan checks the lookup automatically — cache hits resolve in
milliseconds, only true misses incur compute cost.

## NERSC InterProScan Setup

### Prerequisites on NERSC
1. InterProScan 5.77-108.0 (matches our InterPro v108.0 data)
2. InterProScan data directory (~18GB compressed, ~80GB extracted)
3. Access to MinIO for downloading FASTA chunks

### Workflow
```
# 1. Download FASTA chunks from MinIO to $SCRATCH
mc cp --recursive cts/io/psdehal/bakta_reannotation/fasta_chunks_5M/ $SCRATCH/interproscan/fasta/

# 2. Split each 5M chunk into 10K sub-chunks
for chunk in $SCRATCH/interproscan/fasta/chunk_*.fasta; do
  split_fasta.py $chunk $SCRATCH/interproscan/splits/ 10000
done

# 3. Submit job array
sbatch scripts/07_nersc_interproscan.sh

# 4. Collect results and upload to MinIO
python scripts/08_collect_results.py
```

### Output format
InterProScan TSV output (one line per domain hit):
```
protein_id  md5  seq_len  analysis  sig_acc  sig_desc  start  stop  score  status  date  ipr_acc  ipr_desc  go_terms  pathways
```

## BERDL Paths

- **Tenant**: `kescience`
- **Database**: `kescience_interpro`
- **Bronze**: `s3a://cdm-lake/tenant-general-warehouse/kescience/datasets/interpro/`
- **Silver**: `s3a://cdm-lake/tenant-sql-warehouse/kescience/kescience_interpro.db`

## InterPro Data Version

Current release: v108.0 (2026-01-29)
Source: https://ftp.ebi.ac.uk/pub/databases/interpro/current_release/
InterProScan: v5.77-108.0
