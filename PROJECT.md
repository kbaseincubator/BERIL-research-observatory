# BERIL Research Observatory

## Purpose

Use the **BERDL Data Lakehouse** to pursue scientific questions across microbial genomics, ecology, metabolic modeling, and multi-omics analysis, while building shared documentation that accelerates future work.

BERDL hosts **35 databases across 9 tenants** including pangenome data for 293K microbial genomes, mutant fitness data for 48 organisms, ModelSEED biochemistry, multi-omics from NMDC, and more. See [docs/collections.md](docs/collections.md) for the full inventory.

## Dual Goals

1. **Science**: Answer research questions in `projects/` subdirectories
2. **Knowledge**: Capture learnings in `docs/` to reduce re-discovery overhead

## Documentation Workflow

When working on any science project, update `docs/` when you discover:

| Discovery Type | Add To |
|----------------|--------|
| Query pitfall or gotcha | `docs/pitfalls.md` |
| Performance issue or strategy | `docs/performance.md` |
| Data limitation or coverage gap | `docs/pitfalls.md` |
| Useful insight about data structure | `docs/schemas/{collection}.md` |
| Any other learning worth sharing | `docs/discoveries.md` |
| Research idea or future direction | `docs/research_ideas.md` |

**Tag each addition** with the project that uncovered it:
```markdown
### [ecotype_analysis] AlphaEarth coverage is only 28%
Discovered that only 83K/293K genomes have embeddings...
```

## Documentation Files

| File | Purpose |
|------|---------|
| `docs/collections.md` | Overview of all BERDL databases and tenants |
| `docs/schemas/` | Per-collection schema documentation |
| `docs/overview.md` | Project goals, data workflow, scientific context |
| `docs/pitfalls.md` | SQL gotchas, data sparsity, common errors |
| `docs/performance.md` | Query strategies for large tables |
| `docs/discoveries.md` | Running log of insights (low-friction capture) |
| `docs/research_ideas.md` | Future research directions, project ideas |

## Project Structure

Each science project in `projects/` should have:
- `README.md`: Question being addressed, approach, key findings
- `notebooks/`: Analysis notebooks
- `data/`: Extracted/processed data (gitignore large files)

Current projects:
- `projects/ecotype_analysis/` - Environment vs phylogeny effects on gene content
- `projects/pangenome_openness/` - Open vs closed pangenome patterns
- `projects/cog_analysis/` - COG functional category distributions across core/aux/novel genes
- `projects/pangenome_pathway_geography/` - Pangenome openness, metabolic pathways, and biogeography
- `projects/resistance_hotspots/` - Antibiotic resistance hotspot analysis
- `projects/conservation_vs_fitness/` - Gene conservation vs fitness browser data

## Data Organization

| Location | What Goes There | Examples |
|----------|-----------------|----------|
| `data/` | Shared extracts reusable across projects | Pangenome stats for all species, genome metadata, species lists |
| `projects/*/data/` | Project-specific processed data | Distance matrices for specific subsets, analysis outputs |

**Rule of thumb**: If another project might need it, put it in top-level `data/`. If it's clearly for one question, keep it in the project.

## Database Access

- **Databases**: 35 databases across BERDL (see [docs/collections.md](docs/collections.md))
- **Auth**: Token in `.env` file (KBASE_AUTH_TOKEN)
- **API**: `https://hub.berdl.kbase.us/apis/mcp/`
- **Direct Spark**: Use JupyterHub for complex queries

Use `/berdl` skill for BERDL queries. Read `docs/pitfalls.md` before your first query.

### Spark Notebooks

**All analysis notebooks should use direct Spark access** on the BERDL JupyterHub for best performance.

**Required initialization** at the top of every notebook:
```python
from get_spark_session import get_spark_session
spark = get_spark_session()
```

Then query any database with:
```python
df = spark.sql("SELECT ... FROM database_name.table").toPandas()
```

**Benefits vs REST API**:
- No timeouts on complex queries
- Better performance on large joins
- Full Spark SQL functionality
- Can handle species with >500 genomes

### JupyterHub Workflow

**BERDL runs on Kubernetes/Rancher** - compute nodes are ephemeral pods, not persistent VMs. This means:
- No direct SSH to compute nodes
- No remote script execution
- JupyterHub web UI is the designed interface

**Typical workflow:**

1. **Develop locally**
   - Write/edit notebooks on your local machine
   - Test logic with small datasets if possible
   - Commit to git when ready

2. **Upload to JupyterHub**
   - Navigate to: `https://hub.berdl.kbase.us`
   - Authenticate with MFA
   - Upload notebook via Upload button (drag & drop)
   - Place in appropriate directory

3. **Run analysis**
   - Open notebook in JupyterHub
   - Verify Spark session initializes: `spark = get_spark_session()`
   - Kernel -> Restart & Run All (or run cells interactively)
   - Monitor progress (typical runtime: 5-30 minutes for multi-species analyses)

4. **Download results**
   - Select output files in JupyterHub file browser (notebooks, CSVs, PNGs)
   - Right-click -> Download (or use Download button)
   - Place in local `projects/*/data/` directory
   - Commit visualizations and small data files to git

**Current limitations:**
- No programmatic notebook execution (must use web UI)
- No completion notifications (must monitor manually)
- File transfer is manual (acceptable for files <1GB)

## Key Reminders

1. Use exact equality for species IDs (e.g., `WHERE id = 's__Species--RS_GCF_123'`). The `--` inside quotes is fine.
2. Large tables (gene, genome_ani) need filters. Never full-scan.
3. AlphaEarth embeddings only cover 28% of genomes.
4. Gene clusters are species-specific. Can't compare across species.
5. Update docs when you learn something worth sharing!
6. Check [docs/collections.md](docs/collections.md) for the full database inventory.
