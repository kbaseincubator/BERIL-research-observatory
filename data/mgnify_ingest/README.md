# MGnify Database Download & BERDL Ingest

MGnify (EBI Metagenomics) data download for integration as a BERDL collection. Enables cross-referencing with existing pangenome, fitness, and biochemistry data.

## Download Status

| Phase | Description | Status | Size |
|-------|-------------|--------|------|
| 1 | Metadata (18 biomes + protein DB) | **Complete** | 198 MB |
| 2 | Protein cluster data (718M clusters) | **Complete, verified** | 121 GB |
| 3 | Genome catalogue species reps (3 biomes) | **Complete** | 2.9 TB |
| 4 | Sourmash sketch DBs (14 biomes) | **Complete** | 1.4 GB |
| **Total** | | | **~3.0 TB** |

### Phase 3 Detail (Genome Catalogues)

| Biome | Species Reps | Downloaded | Size |
|-------|-------------|------------|------|
| human-gut (v2.0.2) | 4,744 | 4,744 (100%) | 61 GB |
| soil (v1.0) | 19,472 | 19,472 (100%) | 2.0 TB |
| marine (v2.0) | 13,223 | 13,223 (100%) | 843 GB |

Remaining 15 biomes (~19K species) not yet downloaded. Run `download_phase3.sh <biome>` to add more.

## Data Location

All data is on the BERDL JupyterHub at `/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/`. Data is NOT checked into git.

```
data/mgnify_ingest/
├── metadata/                          # Phase 1: 198 MB
│   ├── protein_db/                    # README, md5sum, biome counts
│   └── genome_catalogues/<biome>/     # genomes-all_metadata.tsv per biome
├── protein_db/                        # Phase 2: 121 GB
│   ├── mgy_clusters.fa.gz            # 74 GB - 718M cluster rep sequences
│   ├── mgy_clusters.tsv.gz           # 7.4 GB - cluster stats
│   ├── mgy_cluster_seqs.tsv.gz       # 16 GB - cluster membership
│   ├── mgy_biomes.tsv.gz             # 7.2 GB - protein→biome mapping
│   ├── mgy_counts.tsv.gz             # 6.4 GB - per-protein obs counts
│   ├── mgy_assemblies.tsv.gz         # 11 GB - protein→assembly mapping
│   └── md5sum.txt                     # all checksums verified
├── genome_catalogues/<biome>/         # Phase 3: 2.9 TB
│   └── species_catalogue/<bucket>/<species_id>/
│       ├── genome/                    # .faa .fna .gff eggNOG InterProScan KEGG COG CAZy
│       └── pan-genome/                # core_genes, gene_presence_absence, pan-genome.fna
├── sourmash_dbs/<biome>/              # Phase 4: 1.4 GB
│   └── sourmash_species_representatives_k21.sbt.zip
├── scripts/                           # Download & exploration scripts (in git)
└── logs/                              # Download logs
```

## Key Findings from Metadata Exploration

- **2.46 billion proteins** in the protein database, clustered into **718M clusters** (90% identity)
- **56,766 species representatives** across 18 biomes (19 including marine-eukaryotes beta)
- Taxonomy: **GTDB** — same system as BERDL pangenome, BUT mixed releases:
  - Older catalogues (human-gut, chicken-gut, cow-rumen, etc.): **GTDB r202** (uses Firmicutes/Proteobacteria)
  - Newer catalogues (soil, marine, mouse-gut, etc.): **GTDB r207** (uses Bacillota/Pseudomonadota)
  - BERDL pangenome uses **GTDB r214**
- **Genus-level overlap with BERDL pangenome:** 4,552 genera (42% of MGnify, 54% of BERDL)
- **Species-level overlap:** ~9,593 species (31% of MGnify) after name normalization
- **MGnify-unique genera:** 6,302 — significant new diversity not in BERDL

### Sourmash DB Availability

14 of 18 biomes have downloadable sourmash sketch DBs. The missing 4 (soil, marine_sediment, human-skin, barley-rhizosphere) haven't had the [BioSIFTR pipeline](https://github.com/EBI-Metagenomics/biosiftr) run — they DO support server-side genome search via the MGnify API.

## Scripts

| Script | Purpose |
|--------|---------|
| `download_phase1.sh` | Metadata & small files (minutes) |
| `download_phase2.sh` | Protein cluster data with MD5 verification (hours) |
| `download_phase3.sh` | Genome catalogue species reps via parallel curl (hours-days per biome) |
| `download_phase4.sh` | Sourmash sketch DBs (minutes) |
| `retry_missing.sh` | Retry failed downloads from Phase 3 with `--retry 3` |
| `explore_metadata.py` | Parse metadata, taxonomy analysis, BERDL overlap check |

### Usage

```bash
# Download remaining biomes (run from scripts/ dir)
nohup bash download_phase3.sh mouse-gut cow-rumen chicken-gut > ../logs/phase3_batch2.log 2>&1 &

# Retry any failures
nohup bash retry_missing.sh mouse-gut cow-rumen chicken-gut > ../logs/retry_batch2.log 2>&1 &

# Monitor
tail -f ../logs/phase3_batch2.log
find ../genome_catalogues/<biome>/species_catalogue -name "*.faa" | wc -l
```

### Notes for Continuing Download

- FTP server: `ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/` (no auth required)
- Parallel downloads: 16 connections works but causes ~25% failure rate on first pass; retry script with 8 connections + `--retry 3` recovers all failures
- Species IDs ending in `.1` (versioned genomes, e.g. `MGYG000000761.1`) use the base ID for bucket path but `.1` for directory name — the retry script handles this for human-gut but `download_phase3.sh` does not yet
- Soil genomes are much larger than expected (~130 KB avg per species vs ~15 KB for human-gut), driving the 2.0 TB total
- Newer catalogues (soil, marine) have additional annotations: AMRFinderPlus, antiSMASH, CRISPRCasFinder, defense_finder, GECCO, mobilome, sanntis, dbcan

## Next Steps

1. **Decompress and convert to Delta Lake tables** — needs a drive with 5-10 TB free space (compressed data is 3 TB)
2. **Download remaining biomes** — 15 biomes, ~19K more species reps
3. **Build DIAMOND index** from `mgy_clusters.fa.gz` for protein-level search (MGnify does NOT provide pre-built DIAMOND indexes)
4. **Cross-reference with BERDL pangenome** at protein level via DIAMOND
5. **Back up raw files to MinIO** for persistence across JupyterHub session recycling
