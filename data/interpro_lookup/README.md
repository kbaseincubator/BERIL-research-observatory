# InterPro Lookup for Pangenome Proteins

Fetch pre-computed InterProScan results for the 132.5M gene cluster representative
proteins in `kbase_ke_pangenome`.

## Strategy

InterPro pre-computes domain/family annotations for all UniProt proteins (~167M).
Bakta mapped our gene clusters to UniRef100/90/50 representatives, giving us UniProt
accessions we can look up directly.

**Match tiers (best to worst):**
1. **UniRef100** — exact sequence match → InterPro results apply precisely
2. **UniRef90** — ≥90% identity → InterPro family/domain annotations transfer reliably
3. **UniRef50** — ≥50% identity → InterPro family annotations likely conserved

## Pipeline

| Script | Description | Runs on | Network? |
|--------|-------------|---------|----------|
| `01_extract_identifiers.py` | Extract UniRef/UniParc accessions from BERDL | JupyterHub (Spark) | No |
| `02_download_interpro_bulk.sh` | Download protein2ipr.dat.gz from EBI FTP | Any | Yes (16GB) |
| `03_match_bulk.py` | Match our accessions against bulk data | Any (needs ~10GB RAM) | No |
| `04_api_lookup_remaining.py` | API lookup for unmatched accessions | Any | Yes |
| `05_assess_coverage.py` | Coverage report and gap analysis | Any | No |

## Checkpointing

All network-dependent scripts checkpoint progress:
- `02`: Uses `wget -c` for resumable downloads
- `04`: Saves progress every N batches to `checkpoints/api_lookup_checkpoint.json`

## Data Files

Outputs go to `data/interpro_lookup/`:
- `gene_cluster_accessions.tsv` — gene_cluster_id → UniProt accession mappings
- `interpro_matches.tsv` — matched InterPro results from bulk data
- `api_matches.tsv` — matched InterPro results from API lookups
- `unmatched_clusters.tsv` — gene clusters with no InterPro results (need InterProScan)
- `coverage_report.txt` — summary statistics

## InterPro Bulk Data

Downloaded to `data/interpro_lookup/bulk/`:
- `protein2ipr.dat.gz` — 16GB, maps UniProt accessions → InterPro entries
- `entry.list` — InterPro entry descriptions and types
- `interpro2go` — InterPro → GO term mappings
