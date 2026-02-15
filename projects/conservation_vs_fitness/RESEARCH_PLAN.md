# Research Plan: Conservation vs Fitness -- Linking FB Genes to Pangenome Clusters

## Research Question

How do gene conservation patterns (core/auxiliary/singleton in pangenome clusters) relate to fitness phenotypes across diverse bacteria? Specifically: are essential genes preferentially conserved in the core genome, and what functional categories distinguish essential-core from essential-auxiliary and strain-specific essential genes?

## Hypothesis

The Fitness Browser provides mutant fitness data for ~221K genes across 48 bacteria, while the KBase pangenome classifies 132.5M gene clusters by conservation level (how many genomes in a species carry a given cluster). By linking these datasets, we can ask: do core genes (present in >=95% of species genomes) show different fitness patterns than auxiliary or singleton genes? We expect essential genes to be enriched in the core genome, and that functional profiles will differ between essential-core and essential-auxiliary genes.

## Approach

1. **Link table** (Phase 1) -- Map FB genes to pangenome clusters via DIAMOND blastp (>=90% identity, best hit per gene), resolving GTDB taxonomic renames via three matching strategies (NCBI taxid, organism name, scaffold accession)
2. **Essential gene identification** (Phase 2) -- Identify putative essential genes as protein-coding genes (type=1) absent from `genefitness` (no viable transposon mutants recovered)
3. **Conservation analysis** -- Compare conservation status (core/auxiliary/singleton) between essential and non-essential genes across 34 organisms
4. **Functional characterization** -- Use FB annotations (SEED, KEGG) to profile essential genes by conservation category

## Key Methods

- **Organism matching**: Three complementary strategies (NCBI taxid, NCBI organism name in gtdb_metadata, scaffold accession prefix) to handle GTDB taxonomic renames
- **DIAMOND blastp**: Same-species protein similarity search at >=90% identity threshold with best-hit-only output
- **Multi-clade resolution**: When GTDB splits an NCBI species into multiple clades, the clade with the most DIAMOND hits is chosen
- **Conservation classification**: Core (>=95% of species genomes), auxiliary (<95%, >1 genome), singleton (1 genome)
- **Essential gene definition**: Protein-coding genes (type=1 in FB gene table) with zero entries in `genefitness`. This is the standard RB-TnSeq definition -- no viable transposon mutants were recovered. This is an upper bound on true essentiality; some genes may lack insertions due to being short or in regions with poor transposon coverage.
- **Statistical testing**: Fisher's exact test per organism (2x2: essential/non-essential x core/non-core), odds ratios, Spearman correlations for pangenome context

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `organism` | FB organism metadata, taxonomy IDs |
| `kescience_fitnessbrowser` | `gene` | Gene coordinates, type (1=CDS), descriptions |
| `kescience_fitnessbrowser` | `genefitness` | Fitness scores -- absence = putative essential |
| `kescience_fitnessbrowser` | `seedannotation` | SEED functional annotations |
| `kescience_fitnessbrowser` | `besthitkegg` + `keggmember` + `kgroupdesc` | KEGG functional annotations |
| `kescience_fitnessbrowser` | `seedannotationtoroles` + `seedroles` | SEED functional hierarchy |
| `kbase_ke_pangenome` | `gtdb_metadata` | NCBI taxid/name for organism matching |
| `kbase_ke_pangenome` | `gene_cluster` | Cluster rep sequences, is_core/is_auxiliary/is_singleton |
| `kbase_ke_pangenome` | `pangenome` | Clade size, core/auxiliary/singleton counts |
| External | `fit.genomics.lbl.gov/cgi_data/aaseqs` | FB protein sequences |

## Project Structure

```
projects/conservation_vs_fitness/
├── README.md
├── notebooks/
│   ├── 01_organism_mapping.ipynb        # Map FB orgs -> pangenome clades (Spark)
│   ├── 02_extract_cluster_reps.ipynb    # Download FB proteins + extract per-species FASTAs (Spark)
│   ├── 03_build_link_table.ipynb        # DIAMOND results -> link table + QC (local)
│   └── 04_essential_conservation.ipynb  # Essential genes vs conservation analysis (local)
├── src/
│   ├── run_pipeline.py                  # NB01+NB02 data extraction via Spark Connect
│   ├── run_diamond.sh                   # DIAMOND search script (local)
│   └── extract_essential_genes.py       # NB04 data extraction via Spark Connect
├── data/
│   ├── organism_mapping.tsv             # FB org -> clade mapping (44 organisms)
│   ├── fb_pangenome_link.tsv            # Final link table (177,863 rows)
│   ├── essential_genes.tsv              # Gene essentiality classification (153,143 genes)
│   ├── cluster_metadata.tsv             # Cluster conservation data (2.2M clusters)
│   ├── seed_annotations.tsv             # SEED annotations (125K)
│   ├── kegg_annotations.tsv             # KEGG annotations (73K)
│   ├── seed_hierarchy.tsv               # SEED functional hierarchy
│   └── pangenome_metadata.tsv           # Clade size and openness metrics
└── figures/
```

## Revision History

- **v1** (2026-02): Migrated from README.md
