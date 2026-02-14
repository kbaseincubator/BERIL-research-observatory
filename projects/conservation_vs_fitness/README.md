# Conservation vs Fitness — Linking FB Genes to Pangenome Clusters

## Research Question

How do gene conservation patterns (core/auxiliary/singleton in pangenome clusters) relate to fitness phenotypes across diverse bacteria?

## Motivation

The Fitness Browser provides mutant fitness data for ~221K genes across 48 bacteria, while the KBase pangenome classifies 132.5M gene clusters by conservation level (how many genomes in a species carry a given cluster). By linking these datasets, we can ask: do core genes (present in ≥95% of species genomes) show different fitness patterns than auxiliary or singleton genes? This project builds the bridge between the two datasets.

## Approach

**Phase 1 (this project)**: Build a high-quality link table mapping FB genes to pangenome clusters via protein sequence similarity (DIAMOND blastp).

1. **Organism mapping** — Map each FB organism to pangenome species clades using NCBI taxid, NCBI organism name, and scaffold accession matching
2. **Sequence extraction** — Download FB protein sequences from the Fitness Browser website; extract pangenome cluster representative proteins from Spark
3. **DIAMOND search** — Per-organism blastp against mapped species clusters (≥90% identity, best hit)
4. **Link table** — Resolve multi-clade ambiguities, enrich with core/auxiliary/singleton classification

**Phase 2 (future)**: Explore conservation vs fitness patterns across organisms.

## Key Methods

- **Organism matching**: Three complementary strategies (NCBI taxid, NCBI organism name in gtdb_metadata, scaffold accession prefix) to handle GTDB taxonomic renames
- **DIAMOND blastp**: Same-species protein similarity search at ≥90% identity threshold with best-hit-only output
- **Multi-clade resolution**: When GTDB splits an NCBI species into multiple clades, the clade with the most DIAMOND hits is chosen
- **Conservation classification**: Core (≥95% of species genomes), auxiliary (<95%, >1 genome), singleton (1 genome)

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `organism` | FB organism metadata, taxonomy IDs |
| `kescience_fitnessbrowser` | `gene` | Gene coordinates, scaffold IDs |
| `kbase_ke_pangenome` | `gtdb_metadata` | NCBI taxid/name → genome mapping |
| `kbase_ke_pangenome` | `genome` | Genome → species clade mapping |
| `kbase_ke_pangenome` | `gene_cluster` | Cluster rep sequences (`faa_sequence`), conservation |
| `kbase_ke_pangenome` | `gene` | Gene ID prefixes for scaffold matching |
| `kbase_ke_pangenome` | `pangenome` | Expected cluster counts per species |
| External | `fit.genomics.lbl.gov/cgi_data/aaseqs` | FB protein sequences (official translations) |

## Project Structure

```
projects/conservation_vs_fitness/
├── README.md
├── notebooks/
│   ├── 01_organism_mapping.ipynb        # Map FB orgs → pangenome clades (JupyterHub)
│   ├── 02_extract_cluster_reps.ipynb    # Download FB proteins + extract per-species FASTAs (JupyterHub)
│   └── 03_build_link_table.ipynb        # DIAMOND results → link table + QC (local)
├── src/
│   └── run_diamond.sh                   # DIAMOND search script (local)
├── data/
│   ├── organism_mapping.tsv             # FB org → clade mapping
│   ├── fb_aaseqs_all.fasta              # All FB proteins (downloaded)
│   ├── fb_fastas/                       # Per-organism FB protein FASTAs
│   ├── species_fastas/                  # Per-species cluster rep FASTAs
│   ├── diamond_hits/                    # DIAMOND output per organism
│   ├── cluster_metadata.tsv             # Cluster conservation data (from Spark)
│   └── fb_pangenome_link.tsv            # Final link table
└── figures/                             # QC plots
```

## Status & Next Steps

**In progress**: Phase 1 — building the link table.

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, matplotlib
- DIAMOND (v2.0+) for protein similarity search
- BERDL JupyterHub access (for NB01-02 only)

**Running the pipeline:**

1. **NB01** (JupyterHub): Map FB organisms to pangenome clades → `data/organism_mapping.tsv`

2. **NB02** (JupyterHub): Download FB proteins, extract cluster rep FASTAs → `data/fb_fastas/`, `data/species_fastas/`

3. **run_diamond.sh** (local): Run DIAMOND searches
   ```bash
   cd projects/conservation_vs_fitness
   src/run_diamond.sh data/organism_mapping.tsv data/fb_fastas data/species_fastas data/diamond_hits
   ```

4. **NB03** (local): Build link table from DIAMOND results → `data/fb_pangenome_link.tsv`

If the link table passes QC (≥90% coverage, ≥95% median identity), promote to `data/fitnessbrowser_link/fb_pangenome_link.tsv` for cross-project use.

### Known limitations

- **E. coli excluded**: The main `s__Escherichia_coli` clade is absent from the pangenome (too many genomes to process). The FB organism `Keio` (E. coli BW25113) will not map.
- **GTDB taxonomic renames**: Many organisms have different names in GTDB vs NCBI. The three-strategy matching approach handles this, but occasional mismatches are possible.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
