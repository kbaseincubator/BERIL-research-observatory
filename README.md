# BERIL Research Observatory

**BERIL** is an AI integration layer for the **KBase BER Data Lakehouse (BERDL)** that creates resources, skills, and plugins to facilitate agent or co-scientist analysis of BERDL data.

Through the BERIL Research Observatory, users can:

- **Analyze BERDL data** using AI-assisted workflows and documented patterns
- **Analyze their own data** in the context of BERDL reference collections
- **Share discoveries**, lessons learned, pitfalls, and data products
- **Explore multiple collections** across the data lakehouse
- **Contribute** to a growing knowledge base with proper attribution

## What is BERDL?

The **KBase BER Data Lakehouse (BERDL)** is a Delta Lakehouse containing curated scientific datasets for computational biology research. It includes:

- **Pangenome Collection** (`kbase_ke_pangenome`): 293,059 genomes across 27,690 microbial species derived from GTDB r214
- **Fitness Browser** (`kescience_fitnessbrowser`): Gene fitness data from transposon mutant experiments across 40+ bacterial organisms
- **ModelSEED Biochemistry** (`kbase_msd_biochemistry`): Metabolic modeling reference data
- **KBase Genomes** (`kbase_genomes`): Structural genomics data including contigs, features, and proteins
- And more collections covering phenotypes, phage data, and reference databases

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
   KB_AUTH_TOKEN="your-token-here"
   ```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kbase/ke-pangenome-science.git
   cd ke-pangenome-science
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
   # Edit .env with your KB_AUTH_TOKEN
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
ke-pangenome-science/
├── docs/                   # Shared knowledge base
│   ├── overview.md         # Project goals & data workflow
│   ├── schema.md           # Database table schemas
│   ├── pitfalls.md         # SQL gotchas & common errors
│   ├── discoveries.md      # Running log of insights
│   └── research_ideas.md   # Future research directions
│
├── data/                   # Shared data extracts
│   ├── core_ogs_parts/     # Core orthologous groups
│   └── ecotypes/           # Ecotype clustering data
│
├── projects/               # Individual research projects
│   ├── cog_analysis/       # COG functional categories analysis
│   ├── ecotype_analysis/   # Environment vs phylogeny effects
│   └── pangenome_openness/ # Open vs closed pangenome patterns
│
├── exploratory/            # Ad-hoc analysis & prototypes
│
├── ui/                     # BERIL Research Observatory web app
│   ├── app/                # FastAPI application
│   ├── config/             # Collections and configuration
│   └── content/            # Content files (discoveries, pitfalls)
│
└── .claude/                # Claude Code AI integration
    └── skills/
        └── berdl/          # BERDL query skill for AI assistants
```

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `docs/` | Shared knowledge base - document SQL pitfalls, performance strategies, discoveries |
| `data/` | Shared data extracts reusable across projects |
| `projects/` | Complete research projects with notebooks, data, and figures |
| `exploratory/` | Scratch space for ad-hoc analysis and prototypes |
| `ui/` | Web application for browsing collections, projects, and knowledge |

## Using the Data

### Via JupyterHub (Recommended)

Access the BERDL JupyterHub at [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us) for interactive Spark SQL queries:

```python
# In a JupyterHub notebook
df = spark.sql("""
    SELECT s.GTDB_species, p.no_genomes, p.no_core
    FROM kbase_ke_pangenome.pangenome p
    JOIN kbase_ke_pangenome.gtdb_species_clade s
      ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
    ORDER BY p.no_genomes DESC
    LIMIT 10
""")
df.show()
```

### Via REST API

Query BERDL directly using the REST API:

```bash
# Set your auth token
AUTH_TOKEN=$(grep "KB_AUTH_TOKEN" .env | cut -d'"' -f2)

# Execute a query
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
3. Share research ideas in `docs/research_ideas.md`

### Using AI Assistants

This repository includes a BERDL skill for AI assistants (Claude Code, etc.) that enables:

- Schema exploration and query generation
- Understanding of table relationships
- Common query patterns for pangenome analysis

See `.claude/skills/berdl/SKILL.md` for details.

## Key Data Collections

| Collection | Database ID | Scale | Use Cases |
|------------|-------------|-------|-----------|
| Pangenome | `kbase_ke_pangenome` | 293K genomes, 27K species | Comparative genomics, functional analysis |
| Fitness Browser | `kescience_fitnessbrowser` | 40+ organisms | Essential genes, fitness effects |
| Genomes | `kbase_genomes` | 16 tables | Structural genomics |
| Biochemistry | `kbase_msd_biochemistry` | 4 tables | Metabolic modeling |

## Resources

- **BERDL JupyterHub**: [https://hub.berdl.kbase.us](https://hub.berdl.kbase.us)
- **KBase**: [https://www.kbase.us](https://www.kbase.us)
- **Schema Documentation**: See `docs/schema.md`
- **Query Pitfalls**: See `docs/pitfalls.md`

## License

This project is part of KBase (DOE Systems Biology Knowledgebase).
