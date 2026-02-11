# BERIL Research Observatory - Directory Structure

```
BERIL-research-observatory/
│
├── PROJECT.md                          # Main project documentation
├── .env                                # Authentication token (KBASE_AUTH_TOKEN)
│
├── docs/                               # Shared knowledge base
│   ├── collections.md                 # Overview of all BERDL databases & tenants
│   ├── schemas/                       # Per-collection schema documentation
│   │   ├── pangenome.md              # kbase_ke_pangenome (293K genomes, 1B genes)
│   │   ├── fitnessbrowser.md         # kescience_fitnessbrowser (48 organisms)
│   │   ├── genomes.md               # kbase_genomes (253M proteins)
│   │   ├── biochemistry.md          # kbase_msd_biochemistry (56K reactions)
│   │   ├── phenotype.md             # kbase_phenotype
│   │   ├── uniprot.md               # kbase_uniprot
│   │   ├── uniref.md                # kbase_uniref50/90/100
│   │   ├── enigma.md                # enigma_coral (ENIGMA SFA)
│   │   ├── nmdc.md                  # nmdc_arkin, nmdc_ncbi_biosamples
│   │   ├── phagefoundry.md          # phagefoundry_* (4 genome browsers)
│   │   ├── planetmicrobe.md         # planetmicrobe_*
│   │   └── protect.md               # protect_genomedepot
│   ├── overview.md                    # Scientific context & data workflow
│   ├── pitfalls.md                    # SQL gotchas & common errors
│   ├── performance.md                 # Query optimization strategies
│   ├── discoveries.md                 # Running log of insights
│   └── research_ideas.md             # Future research directions & project ideas
│
├── data/                               # Shared data across projects
│   ├── pangenome_summary.csv          # Stats for all 27K species
│   ├── core_ogs_parts/                # Core orthologous groups (100 parts)
│   ├── ecotypes/                      # Ecotype clustering data
│   │   ├── alphaearth_embeddings.csv
│   │   ├── genome_clusters_cog/       # COG annotations (20 parts)
│   │   └── within_species_ani/        # ANI matrices (10 parts)
│   └── ecotypes_expanded/             # Extended ecotype analysis
│       ├── target_genomes_expanded.csv
│       ├── embeddings_expanded.csv
│       ├── species_ecological_categories.csv
│       ├── gene_clusters_expanded/    # Gene cluster data (11 parts)
│       └── ani_expanded/              # ANI matrices (2 parts)
│
├── projects/                           # Individual science projects
│   │
│   ├── cog_analysis/                  # COG functional categories analysis
│   │   ├── README.md
│   │   ├── notebooks/
│   │   └── data/
│   │
│   ├── ecotype_analysis/              # Environment vs phylogeny effects
│   │   ├── notebooks/
│   │   ├── figures/
│   │   └── scripts/
│   │
│   ├── pangenome_openness/            # Open vs closed pangenome patterns
│   │   ├── notebooks/
│   │   ├── data/
│   │   └── figures/
│   │
│   ├── pangenome_pathway_geography/   # Pathways & biogeography
│   │   ├── README.md
│   │   └── notebooks/
│   │
│   ├── pangenome_pathway_ecology/     # Pathway ecology
│   │   ├── README.md
│   │   └── notebooks/
│   │
│   ├── resistance_hotspots/           # Antibiotic resistance hotspots
│   │   ├── README.md
│   │   └── notebooks/
│   │
│   └── conservation_vs_fitness/       # Gene conservation vs fitness data
│
├── exploratory/                        # Scratch work & exploratory analysis
│   ├── *.ipynb                        # Ad-hoc analysis notebooks
│   └── data/                          # Exploratory data files
│
├── ui/                                 # BERIL Research Observatory web app
│   ├── app/                           # FastAPI application
│   ├── config/                        # Collections and configuration
│   └── content/                       # Content files (discoveries, pitfalls)
│
└── .claude/                            # Claude Code configuration
    ├── settings.local.json
    └── skills/
        ├── berdl/                     # BERDL query skill
        │   ├── SKILL.md
        │   └── modules/              # Per-collection skill modules
        │       ├── pangenome.md
        │       └── biochemistry.md
        ├── berdl-discover/            # Database discovery skill
        │   └── SKILL.md
        └── hypothesis/               # Research hypothesis skill
            └── SKILL.md
```

## Key Directory Purposes

### Root Level
- **PROJECT.md**: Main documentation explaining project structure and workflows
- **.env**: Authentication token for BERDL database access

### docs/
Shared knowledge base that grows with discoveries:
- **collections.md**: Master index of all 35 BERDL databases across 9 tenants
- **schemas/**: Detailed per-collection schema documentation (table structures, relationships, query patterns)
- Document SQL pitfalls, performance strategies, schema details
- Capture research ideas and future directions as they emerge
- Tag each entry with the project that discovered it (e.g., `[cog_analysis]`)

### data/
Shared extracts reusable across projects:
- Large datasets partitioned into chunks (e.g., `part_000.csv`, `part_001.csv`)
- If another project might need it, put it here
- Include genome metadata, species lists, pangenome stats

### projects/
Each subdirectory is a complete research project with:
- **README.md**: Research question, approach, findings
- **notebooks/**: Jupyter notebooks for analysis
- **data/**: Project-specific processed data
- **figures/**: Visualizations and plots
- Standard structure: docs/, notebooks/, data/, figures/, scripts/

### exploratory/
Scratch space for ad-hoc analysis:
- Experiments that haven't been formalized into projects
- Quick explorations and prototypes
- Gets messy, that's OK!

## Current Projects

| Project | Description |
|---------|-------------|
| **cog_analysis** | COG functional category distributions across core/auxiliary/novel genes |
| **ecotype_analysis** | Environment vs phylogeny effects on gene content |
| **pangenome_openness** | Open vs closed pangenome patterns |
| **pangenome_pathway_geography** | Pangenome openness, metabolic pathways, and biogeography |
| **pangenome_pathway_ecology** | Pathway ecology analysis |
| **resistance_hotspots** | Antibiotic resistance hotspot analysis |
| **conservation_vs_fitness** | Gene conservation vs fitness browser data |

## Database Access

**35 databases** across BERDL Delta Lakehouse (see [docs/collections.md](docs/collections.md))
- Access via Spark SQL on JupyterHub or REST API
- Major collections: pangenome (293K genomes), fitness browser (48 organisms), genomes (253M proteins), biochemistry (56K reactions), and more

## Workflow

1. **Start a new project**: Create `projects/new_project/` with README, notebooks/, data/
2. **Query database**: Use Spark SQL on JupyterHub (see PROJECT.md for examples)
3. **Document learnings**: Update `docs/` when you discover pitfalls or insights
4. **Save shared data**: If data is reusable, put in top-level `data/`
5. **Keep project data local**: Project-specific outputs go in `projects/*/data/`
