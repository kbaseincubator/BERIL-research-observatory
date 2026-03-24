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

### Phase 2: InterProScan on NERSC — COMPLETE

Ran InterProScan 5.77-108.0 on all 132,538,155 cluster rep sequences at NERSC
Perlmutter using the shared queue. All 18 member databases with lookup service
enabled, GO terms, and pathway annotations.

| Metric | Value |
|--------|-------|
| Input sequences | 132,538,155 |
| Result lines | 833,242,989 |
| Result files | 13,254 splits |
| Result size | 2.8 TB (TSV) |
| Analyses | 18 (Pfam, CDD, Gene3D, PANTHER, SUPERFAMILY, etc.) |
| Annotations | GO terms, KEGG, MetaCyc, Reactome pathways |

**Job configuration (determined by benchmarking):**
- 10K sequences per split, 8 CPUs, 24 GB memory, 4-hour limit
- Shared queue (`--qos=shared`) for partial-node allocation
- Lookup service enabled — resolves ~90-95% of sequences in milliseconds
- Node-local `/tmp` (tmpfs) for InterProScan temp files (Lustre causes race conditions)
- `module load python` required (MobiDB needs Python ≥ 3.7, system is 3.6)
- Asterisks stripped from sequences (InterProScan rejects stop codon `*` characters)

**Throughput:** ~2.9 seq/s per job (8 CPUs), ~500 concurrent jobs on shared queue

**Known issues:**
- Sequences >10K aa can cause jobs to run for hours (e.g., 175K aa assembly artifact)
- The `split_fasta.py` script strips asterisks during splitting
- 8 GB memory is insufficient — jobs need 9-16 GB (24 GB provides safe headroom)

### Phase 3: Transform & Ingest into BERDL — COMPLETE

Transformed the raw 15-column InterProScan TSV into 3 normalized tables and
ingested into the existing `kbase_ke_pangenome` database alongside bakta tables.

| Table | Rows | Status |
|-------|------|--------|
| `kbase_ke_pangenome.interproscan_domains` | 833,303,130 | Ingested |
| `kbase_ke_pangenome.interproscan_go` | 266,317,724 | Ingested |
| `kbase_ke_pangenome.interproscan_pathways` | 287,228,475 | Ingested |

**Coverage:** 111M clusters (83.8% of 132.5M) have at least one domain hit.
584M hits have formal IPR accessions; 249M are member-DB-only hits (Pfam, CDD, etc.).

**Note:** Reactome pathways (~12B rows) are excluded — they are eukaryotic
species-specific mappings inherited from InterPro and not relevant for bacterial proteins.
Use `--include-reactome` with `09_transform_results.py` to include them.

**MinIO path:** `s3a://cdm-lake/users-general-warehouse/psdehal/data/interproscan_results/`

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
| `07_nersc_interproscan.sh` | SLURM job array for InterProScan at NERSC | NERSC | Done |
| `split_fasta.py` | Split FASTA into 10K sub-chunks (strips asterisks) | NERSC | Done |
| `run_iprscan_shared.sh` | Production shared-queue InterProScan job | NERSC | Done |
| `08_collect_results.py` | Collect InterProScan TSV results → BERDL ingest | JupyterHub | Done |
| `09_transform_results.py` | Transform 15-col TSV → 3 normalized tables | NERSC | Done |
| `10_ingest_interproscan_results.py` | Upload to MinIO + ingest into BERDL | JupyterHub | Done |

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

### Installation
InterProScan 5.77-108.0 installed at `/pscratch/sd/p/psdehal/interproscan/interproscan-5.77-108.0`
(50 GB, downloaded from EBI FTP). Requires Java 11 (available by default on Perlmutter).

### Workflow (as executed)
```bash
# 1. Download FASTA chunks from MinIO (9 missing + 18 symlinked from bakta)
bash download_missing_chunks.sh

# 2. Split into 10K sub-chunks with asterisk stripping
python split_fasta.py /pscratch/sd/p/psdehal/interproscan/fasta/ \
       /pscratch/sd/p/psdehal/interproscan/splits/ --chunk-size 10000
# → 13,254 split files, 40 GB total

# 3. Submit on shared queue in batches (5,000 job submit limit)
sbatch --account=amsc002 --array=0-4999%500 run_iprscan_shared.sh
sbatch --account=amsc002 --array=5000-8999%500 run_iprscan_shared.sh
sbatch --account=kbase   --array=9000-13253%500 run_iprscan_shared.sh

# 4. Transform results into 3 normalized tables
python scripts/09_transform_results.py

# 5. Upload to MinIO and ingest into BERDL
python scripts/10_ingest_interproscan_results.py
```

### Benchmarking Results

**Chunk size scaling (64 CPUs, lookup enabled):**

| Sequences | Wall time | Seqs/sec | Memory |
|-----------|-----------|----------|--------|
| 100 | 1.7 min | 1.0 | 4.2 GB |
| 500 | 5.2 min | 1.6 | 4.4 GB |
| 2,000 | 15.7 min | 2.1 | 6.1 GB |
| 10,000 | 36.6 min | 4.6 | 16.8 GB |

**CPU scaling (3K sequences, lookup enabled):**

| CPUs | Wall time | Speedup vs 8 | Memory |
|------|-----------|-------------|--------|
| 8 | 21.1 min | 1.0x | 4.8 GB |
| 16 | 19.5 min | 1.08x | 7.6 GB |
| 32 | 17.6 min | 1.20x | 7.9 GB |
| 64 | 18.2 min | 1.16x | 8.0 GB |

**Key finding:** CPU scaling is minimal (8→64 CPUs gives only 1.2x speedup).
The optimal config is 8 CPUs with many concurrent jobs on the shared queue.

**Lookup service impact (100 sequences):**

| Mode | Wall time | Seqs/sec |
|------|-----------|----------|
| With lookup | 104s | 1.0 |
| Without (-dp) | 272s | 0.4 |

Lookup service provides ~2.6x speedup. Perlmutter compute nodes have internet access.

### Output format
InterProScan TSV output (one line per domain hit, 15 columns):
```
protein_id  md5  seq_len  analysis  sig_acc  sig_desc  start  stop  score  status  date  ipr_acc  ipr_desc  go_terms  pathways
```

### Results on pscratch
```
/pscratch/sd/p/psdehal/interproscan/
  interproscan-5.77-108.0/   # InterProScan installation (50 GB)
  fasta/                      # 27 input FASTA chunks (42 GB)
  splits/                     # 13,254 × 10K-sequence splits (40 GB)
  results/                    # 13,254 TSV result files (2.8 TB)
  tables/                     # 3 transformed + compressed tables (27.4 GB)
  benchmark/                  # Benchmark results and summary
  logs/                       # SLURM job logs
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
