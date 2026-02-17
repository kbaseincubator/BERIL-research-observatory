# Microbial Discovery Forge

The **Microbial Discovery Forge** is an AI co-scientist and research observatory for BERDL-scale microbial discovery. Built on the **KBase BER Data Lakehouse (BERDL)**, it combines reusable skills, shared memory, and scalable data to accelerate research.

Through the Microbial Discovery Forge, users can:

- **Analyze BERDL data** using AI-assisted workflows and documented patterns
- **Analyze their own data** in the context of BERDL reference collections
- **Share discoveries**, lessons learned, pitfalls, and data products
- **Explore multiple collections** across the data lakehouse
- **Contribute** to a growing knowledge base with proper attribution

## What is BERDL?

The **KBase BER Data Lakehouse (BERDL)** is a Delta Lakehouse containing curated scientific datasets for computational biology research. It hosts **35 databases across 9 tenants**:

| Tenant | Databases | Highlights |
|--------|-----------|------------|
| **KBase** | 10 | Pangenome (293K genomes), Genomes (253M proteins), Biochemistry, Phenotype, UniProt/UniRef |
| **KE Science** | 1 | Fitness Browser (48 organisms, 27M fitness measurements) |
| **ENIGMA** | 1 | Environmental microbiology (7K genomes, communities, strains) |
| **NMDC** | 2 | Multi-omics analysis, harmonized BioSamples |
| **PhageFoundry** | 5 | Species-specific genome browsers for phage research |
| **PlanetMicrobe** | 2 | Marine microbial ecology |
| **PROTECT** | 1 | Pathogen genome browser |

See [docs/collections.md](docs/collections.md) for the full inventory with schema links.

Access is available via Spark SQL, REST API, or JupyterHub.

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- A KBase account with BERDL access

### Getting BERDL Access

1. **Request access** to BERDL through your KBase organization or by contacting the KBase team
2. **Get your auth token** from the BERDL JupyterHub:
   - Go to [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us)
   - Log in with your KBase credentials
   - Access the token from the JupyterHub environment or request one from your administrator. For example, you can get the token from a Jupyter notebook like this:
     ```python
     import os
     print(os.environ.get('KBASE_AUTH_TOKEN'))
     ```
3. **Create your `.env` file** in the project root:
   ```bash
   KBASE_AUTH_TOKEN="your-token-here"
   ```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kbaseincubator/BERIL-research-observatory.git
   cd BERIL-research-observatory
   ```

2. **Set up the UI application** (optional, for browsing the observatory):
   ```bash
   cd ui
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create your environment file**:
   ```bash
   # In the project root
   cp .env.example .env
   # Edit .env with your KBASE_AUTH_TOKEN
   ```

### Running the Observatory UI

```bash
cd ui
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Project Structure

```
BERIL-research-observatory/
├── docs/                       # Shared knowledge base
│   ├── collections.md          # Overview of all BERDL databases & tenants
│   ├── schemas/                # Per-collection schema documentation
│   │   ├── pangenome.md        # kbase_ke_pangenome (293K genomes)
│   │   ├── fitnessbrowser.md   # kescience_fitnessbrowser (48 organisms)
│   │   ├── genomes.md          # kbase_genomes (proteins, features)
│   │   ├── biochemistry.md     # kbase_msd_biochemistry (reactions)
│   │   ├── phenotype.md        # kbase_phenotype
│   │   ├── uniprot.md          # kbase_uniprot
│   │   ├── uniref.md           # kbase_uniref50/90/100
│   │   ├── enigma.md           # enigma_coral
│   │   ├── nmdc.md             # nmdc_arkin, nmdc_ncbi_biosamples
│   │   ├── phagefoundry.md     # phagefoundry_* (4 genome browsers)
│   │   ├── planetmicrobe.md    # planetmicrobe_*
│   │   └── protect.md          # protect_genomedepot
│   ├── overview.md             # Scientific context & data workflow
│   ├── pitfalls.md             # SQL gotchas & common errors
│   ├── performance.md          # Query optimization strategies
│   ├── discoveries.md          # Running log of insights
│   └── research_ideas.md       # Future research directions
│
├── data/                       # Shared data extracts
│
├── projects/                   # Individual research projects
│   ├── cog_analysis/           # COG functional categories analysis
│   ├── ecotype_analysis/       # Environment vs phylogeny effects
│   ├── pangenome_openness/     # Open vs closed pangenome patterns
│   ├── pangenome_pathway_geography/  # Pathways & biogeography
│   ├── pangenome_pathway_ecology/    # Pathway ecology
│   ├── resistance_hotspots/    # Antibiotic resistance analysis
│   └── conservation_vs_fitness/  # Gene conservation vs fitness
│
├── exploratory/                # Ad-hoc analysis & prototypes
│
├── ui/                         # BERIL Research Observatory web app
│   ├── app/                    # FastAPI application
│   ├── config/                 # Collections and configuration
│   └── content/                # Content files (discoveries, pitfalls)
│
└── .claude/                    # Claude Code AI integration
    └── skills/
        ├── berdl/              # BERDL query skill
        ├── berdl-discover/     # Database discovery skill
        └── hypothesis/         # Research hypothesis skill
```

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `docs/` | Shared knowledge base - collection schemas, SQL pitfalls, performance strategies, discoveries |
| `docs/schemas/` | Per-collection schema documentation for all BERDL databases |
| `data/` | Shared data extracts reusable across projects |
| `projects/` | Complete research projects with notebooks, data, and figures |
| `exploratory/` | Scratch space for ad-hoc analysis and prototypes |
| `ui/` | Web application for browsing collections, projects, and knowledge |

## Using the Data

### Via JupyterHub (Recommended)

Access the BERDL JupyterHub at [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us) for interactive Spark SQL queries:

```python
# In a JupyterHub notebook
spark = get_spark_session()

# Query any database — results are Spark DataFrames
df = spark.sql("""
    SELECT s.GTDB_species, p.no_genomes, p.no_core
    FROM kbase_ke_pangenome.pangenome p
    JOIN kbase_ke_pangenome.gtdb_species_clade s
      ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
    ORDER BY p.no_genomes DESC
    LIMIT 10
""")

# Use PySpark operations for filtering, aggregation, joins
# Only convert to pandas for final small results (plotting, export)
df.toPandas()  # Fine here — LIMIT 10

# Query fitness browser data
fitness = spark.sql("""
    SELECT orgId, genus, species, strain
    FROM kescience_fitnessbrowser.organism
""")  # Small table — .toPandas() OK when needed
```

### Via REST API

Query BERDL directly using the REST API:

```bash
# Set your auth token
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)

# List all databases
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"use_hms": true, "filter_by_namespace": true}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/list

# Execute a query against any database
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM kbase_ke_pangenome.pangenome LIMIT 10"}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/query
```

## Contributing

### Starting a New Project

1. Create a new directory under `projects/`:
   ```bash
   mkdir -p projects/my_project/{notebooks,data,figures}
   ```

2. Add a `README.md` with your research question and approach

3. Use the standard structure:
   - `notebooks/` - Jupyter notebooks for analysis
   - `data/` - Project-specific processed data
   - `figures/` - Visualizations and plots

### Documenting Discoveries

When you learn something valuable:

1. Add it to `docs/discoveries.md` with the project tag
2. Document SQL pitfalls in `docs/pitfalls.md`
3. Update schema docs in `docs/schemas/{collection}.md`
4. Share research ideas in `docs/research_ideas.md`

### Adding a New Database

Use the `/berdl-discover` skill to introspect a new database:

1. Run `/berdl-discover` to generate schema documentation
2. Create `docs/schemas/{name}.md` with the generated output
3. Add the database to `docs/collections.md`
4. Optionally create a skill module in `.claude/skills/berdl/modules/{name}.md`

### Using AI Assistants

This repository includes BERDL skills for AI assistants (Claude Code, etc.) that enable:

- Schema exploration and query generation
- Database discovery and documentation
- Research hypothesis generation
- Common query patterns across all collections

See `.claude/skills/berdl/SKILL.md` for details.

## Key Data Collections

For the full inventory of 35 databases, see [docs/collections.md](docs/collections.md).

| Collection | Database ID | Scale | Use Cases |
|------------|-------------|-------|-----------|
| Pangenome | `kbase_ke_pangenome` | 293K genomes, 27K species, 1B genes | Comparative genomics, functional analysis |
| Fitness Browser | `kescience_fitnessbrowser` | 48 organisms, 27M fitness scores | Essential genes, gene function, stress response |
| Genomes | `kbase_genomes` | 293K genomes, 253M proteins | Protein sequences, structural genomics |
| Biochemistry | `kbase_msd_biochemistry` | 56K reactions, 46K molecules | Metabolic modeling, thermodynamics |
| Phenotype | `kbase_phenotype` | 182K conditions | Growth phenotypes |
| ENIGMA | `enigma_coral` | 7K genomes, 596 sites | Environmental microbiology |
| NMDC | `nmdc_arkin` | 48 studies, multi-omics | Microbiome analysis |
| PhageFoundry | `phagefoundry_*` | 4 species | Phage-host interactions |

## Resources

- **BERIL Observatory UI**: [http://beril-observatory.knowledge-engine.development.svc.spin.nersc.org/](http://beril-observatory.knowledge-engine.development.svc.spin.nersc.org/)
- **BERDL JupyterHub**: [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us)
- **KBase**: [https://www.kbase.us](https://www.kbase.us)
- **Collections Overview**: See [docs/collections.md](docs/collections.md)
- **Schema Documentation**: See [docs/schemas/](docs/schemas/)
- **Query Pitfalls**: See [docs/pitfalls.md](docs/pitfalls.md)

## License

This project is part of KBase (DOE Systems Biology Knowledgebase).
