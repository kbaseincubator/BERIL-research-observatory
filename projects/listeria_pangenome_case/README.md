# L. monocytogenes Pangenome Case Study: Amino Acid Biosynthesis and Carbon Source Utilization

## Research Question

*Listeria monocytogenes* is a facultative intracellular pathogen isolated from food, clinical, and environmental settings. Using GapMind pathway predictions from the BERDL pangenome database, we ask:

1. **Amino acid biosynthesis**: Which pathways are complete vs incomplete? Do predictions match known auxotrophies?
2. **Carbon source utilization**: Which carbon sources does the pangenome predict *L. monocytogenes* can use?
3. **Clade variation**: Do the three GTDB clades differ in metabolic pathway completeness?
4. **Environment variation**: Do pathway completeness profiles differ across food, clinical, and environmental isolates?

## Approach

1. **Species identification** (notebook 01): Query BERDL for *L. monocytogenes* clades and pangenome statistics
2. **GapMind pathway completeness** (notebook 01): Query pre-computed GapMind predictions for amino acid biosynthesis (18 pathways) and carbon source utilization (62 pathways). Handle multi-row step data by taking MAX score per genome-pathway pair.
3. **Cross-clade comparison** (notebook 01): Compare pathway completeness distributions across GTDB clades
4. **Environment cross-reference** (notebook 01): Join with environment metadata from `gene_environment_association` project
5. **Validation** (notebook 01): Compare GapMind predictions against published *L. monocytogenes* minimal medium formulations

## Key Methodological Feature

All pathway definitions come from **GapMind** (pre-computed in the BERDL lakehouse), not from manually curated gene lists. This ensures:
- Traceable pathway definitions (GapMind HMM profiles)
- Reproducible scoring (no hardcoded gene lists)
- Coverage of 80 pathways (18 amino acid + 62 carbon source) per genome

## Data Sources

| Source | Database | Table(s) |
|--------|----------|----------|
| Species | `kbase_ke_pangenome` | `gtdb_species_clade`, `pangenome` |
| Pathway predictions | `kbase_ke_pangenome` | `gapmind_pathways` |
| Genomes | `kbase_ke_pangenome` | `genome` |
| Environment metadata | `gene_environment_association` project | `data/genome_env_metadata.csv` |

## Notebooks

| Notebook | Purpose | Runtime |
|----------|---------|---------|
| `01_listeria_pathway_case.ipynb` | GapMind pathway analysis, cross-clade comparison, environment cross-reference, validation | ~5-10 min |

## Reproduction

1. Upload notebook to BERDL JupyterHub
2. Ensure `gene_environment_association/data/genome_env_metadata.csv` exists (run notebook 02 from that project first)
3. Run all cells (requires Spark Connect to `kbase_ke_pangenome`)

## Related Projects

- `gene_environment_association/` -- Provides environment metadata; *L. monocytogenes* is one of 212 species qualifying for gene-environment association testing
- `pangenome_pathway_geography/` -- Used same GapMind query patterns at broader scale (all species)
- `essential_metabolome/` -- Similar GapMind pathway analysis for 7 other organisms

## Known Issues

- **GapMind multi-row pitfall**: Each genome-pathway pair has multiple rows (one per step). Must take MAX score per pair before aggregating. See `docs/pitfalls.md` [pangenome_pathway_geography].
- **GapMind coverage**: Limited to amino acid biosynthesis and carbon source utilization (80 pathways total). Does not cover virulence factors, stress tolerance, or other pathways.

## Authors

- **Mark A. Miller** (Lawrence Berkeley National Lab)
