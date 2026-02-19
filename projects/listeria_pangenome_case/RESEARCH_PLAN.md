# Research Plan: L. monocytogenes Amino Acid Biosynthesis and Carbon Source Utilization

## Research Question

*Listeria monocytogenes* is a facultative intracellular pathogen found in food, clinical, and environmental settings. Using GapMind pathway predictions from the BERDL pangenome database, we ask:

1. **Amino acid biosynthesis**: Which amino acid pathways are complete, incomplete, or absent across *L. monocytogenes* genomes? Do predictions match known auxotrophies?
2. **Carbon source utilization**: Which carbon sources does the pangenome predict *L. monocytogenes* can use?
3. **Clade variation**: Do the three GTDB clades (corresponding to classical lineages) differ in metabolic pathway completeness?
4. **Environment variation**: Do pathway completeness profiles differ across food, clinical, and environmental isolates?

## Hypothesis

- **H1 (Known auxotrophies confirmed)**: GapMind will predict incomplete biosynthesis for branched-chain amino acids (isoleucine, leucine, valine), cysteine, and methionine -- matching experimentally validated *L. monocytogenes* growth requirements.
- **H2 (Clade-specific metabolism)**: The three GTDB clades may show different pathway completeness profiles, reflecting known lineage-specific adaptations (lineage I = clinical, lineage II = environmental/food, lineage III = animal-associated).
- **H3 (Environment-associated pathway variation)**: Food and environmental isolates may show broader carbon source utilization than clinical isolates, reflecting metabolic adaptation to nutrient-diverse environments.

## Approach

### 1. Species Identification
- Query `gtdb_species_clade` and `pangenome` for *L. monocytogenes* clades
- Identify genome counts and pangenome statistics per clade

### 2. GapMind Pathway Completeness
- Query `gapmind_pathways` for all *L. monocytogenes* genomes
- Handle multiple rows per genome-pathway pair (take MAX score per pair)
- Score categories: complete > likely_complete > steps_missing_low > steps_missing_medium > not_present
- Separate amino acid biosynthesis (18 pathways) from carbon source utilization (62 pathways)

### 3. Cross-Clade Comparison
- Compare pathway completeness distributions across the 3 GTDB clades
- Identify pathways with clade-specific variation

### 4. Environment Cross-Reference
- Join with `genome_env_metadata.csv` (from `gene_environment_association` project) for environment categories
- Compare pathway profiles across food, clinical, and environmental isolates

### 5. Validation
- Compare amino acid pathway predictions against published *L. monocytogenes* minimal medium formulations
- Cross-reference with known metabolic capabilities from literature

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `gtdb_species_clade` - Species taxonomy and clade IDs
  - `pangenome` - Pangenome statistics (genome count, core/accessory/singleton counts)
  - `gapmind_pathways` - GapMind pathway predictions (305M rows total; ~80 pathways per genome)
  - `genome` - Genome metadata
- **External data**: `genome_env_metadata.csv` from `gene_environment_association` project

## Expected Outputs

### Figures
- Amino acid pathway completeness heatmap across clades
- Carbon source utilization profile
- Pathway completeness by environment category

### Notebooks
- `01_listeria_pathway_case.ipynb` - GapMind pathway analysis, cross-clade comparison, environment cross-reference (~5-10 min runtime)

## Related Projects

- **gene_environment_association** - Provides environment metadata and gene-environment association framework; L. monocytogenes is one of 212 qualifying species
- **pangenome_pathway_geography** - Used same GapMind query patterns at broader scale
- **essential_metabolome** - Similar GapMind pathway analysis for 7 other organisms

## Revision History
- **v1** (2026-02): Initial plan
