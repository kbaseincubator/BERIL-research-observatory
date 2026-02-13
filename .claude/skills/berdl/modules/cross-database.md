# Cross-Database Query Patterns

Patterns for joining data across BERDL databases and linking to external resources.

## Database Linking Overview

```
kbase_ke_pangenome          kbase_msd_biochemistry       External (NCBI Entrez)
────────────────────        ──────────────────────       ──────────────────────
eggnog_mapper_annotations   reaction                     NCBI Taxonomy
  .EC ──────────────────────► .abbreviation (pattern)    NCBI Gene
  .KEGG_Reaction ───────────► (via KEGG ID mapping)      NCBI Protein
  .BiGG_Reaction ───────────► (via BiGG ID mapping)      PubMed
  .KEGG_ko                                                UniProt
  .KEGG_Pathway

genome                      molecule
  .genome_id ───────────────► NCBI Assembly accession
  .ncbi_biosample_id ───────► NCBI BioSample

gtdb_species_clade
  .GTDB_species ────────────► NCBI Taxonomy (name lookup)
```

## Pangenome ↔ Biochemistry Joins

### Link Gene Clusters to Reactions via EC Numbers

The most reliable cross-database link. EC numbers in pangenome annotations can be matched to ModelSEED reactions.

```sql
-- Step 1: Get EC numbers for a species' gene clusters
SELECT gc.gene_cluster_id, gc.is_core, ann.EC, ann.Description
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND ann.EC != '-' AND ann.EC IS NOT NULL

-- Step 2: Find matching ModelSEED reactions by EC pattern
-- (EC numbers appear in reaction abbreviations)
SELECT id, name, abbreviation, deltag, reversibility
FROM kbase_msd_biochemistry.reaction
WHERE abbreviation LIKE '%2.7.1.1%'
```

**Limitations**:
- ModelSEED uses its own ID system — no direct foreign key to pangenome
- EC numbers in `reaction.abbreviation` are embedded in strings like `2.7.1.150-RXN.c`
- Use LIKE pattern matching, not exact equality, for EC lookups in biochemistry
- Some gene clusters have multiple EC numbers (comma-separated) — split before matching

### Link Gene Clusters to Reactions via KEGG

```sql
-- Get KEGG reaction IDs from pangenome annotations
SELECT gc.gene_cluster_id, gc.is_core, ann.KEGG_Reaction, ann.KEGG_Pathway
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND ann.KEGG_Reaction != '-' AND ann.KEGG_Reaction IS NOT NULL
```

**Note**: KEGG reaction IDs (e.g., `R00001`) do not directly match ModelSEED IDs (`seed.reaction:rxn00001`). Cross-referencing requires an external mapping (KEGG → ModelSEED), which is not currently available in BERDL. Use EC numbers for the most reliable link.

### Metabolic Pathway Reconstruction for a Species

Combine pangenome annotations with biochemistry to reconstruct metabolic capabilities:

```sql
-- Get all annotated metabolic functions for a species
SELECT
  gc.is_core,
  ann.EC,
  ann.KEGG_Pathway,
  ann.KEGG_ko,
  ann.Description,
  COUNT(*) as cluster_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND (ann.EC != '-' OR ann.KEGG_Pathway != '-')
GROUP BY gc.is_core, ann.EC, ann.KEGG_Pathway, ann.KEGG_ko, ann.Description
ORDER BY gc.is_core DESC, cluster_count DESC
```

Then look up the EC numbers in biochemistry to get thermodynamic data:

```sql
-- For each EC number found, get reaction thermodynamics
SELECT id, name, deltag, deltagerr, reversibility, is_transport
FROM kbase_msd_biochemistry.reaction
WHERE abbreviation LIKE '%{ec_number}%'
  AND deltag > -10000000  -- Filter deltaG outliers
```

### Get Reaction Stoichiometry for Annotated Enzymes

```sql
-- For a specific EC number, get full reaction details
SELECT
  r.id, r.name, r.deltag,
  m.name as compound, m.formula,
  rg.stoichiometry,
  CASE WHEN rg.stoichiometry < 0 THEN 'reactant' ELSE 'product' END as role
FROM kbase_msd_biochemistry.reaction r
JOIN kbase_msd_biochemistry.reagent rg ON r.id = rg.reaction_id
JOIN kbase_msd_biochemistry.molecule m ON rg.molecule_id = m.id
WHERE r.abbreviation LIKE '%{ec_number}%'
ORDER BY r.id, rg.stoichiometry
```

## Pangenome ↔ Fitness Browser Joins

### Link Gene Clusters to Fitness Data

No direct foreign key exists between pangenome and fitness browser. Linking requires:

1. Matching by gene name or locus tag (approximate)
2. Matching by organism — fitness browser covers 48 organisms, most of which overlap with pangenome species

```sql
-- Step 1: Find the fitness browser organism
SELECT DISTINCT orgId, organism
FROM kescience_fitnessbrowser.organism
WHERE organism LIKE '%Escherichia%'

-- Step 2: Get fitness data for specific genes
SELECT locusId, sysName, gene_name, CAST(fit AS FLOAT) as fitness, CAST(t AS FLOAT) as t_score
FROM kescience_fitnessbrowser.genefitness
WHERE orgId = '{orgId}'
  AND CAST(fit AS FLOAT) < -2
ORDER BY CAST(fit AS FLOAT) ASC
LIMIT 50
```

**Limitations**:
- Fitness browser uses locus tags, pangenome uses gene cluster IDs — no direct mapping
- Link by gene name or functional annotation (COG, KEGG) rather than by ID
- All fitness browser columns are strings — always CAST before numeric comparison

## Pangenome ↔ Genomes Database Joins

### Link Pangenome Genomes to Structural Data

The `kbase_genomes` database contains structural genomic data (contigs, features, protein sequences) for the same 293K genomes.

```sql
-- Pangenome genome IDs map to genome accessions
-- e.g., RS_GCF_000005845.2 in pangenome → same accession in genomes

-- Note: kbase_genomes uses CDM UUIDs as primary keys
-- Use the name table to map between external IDs and CDM UUIDs
```

**Limitations**:
- kbase_genomes uses UUID-based identifiers — requires the `name` table for ID mapping
- Junction tables in kbase_genomes have ~1B rows — never query without filters
- This join is complex and should be done on JupyterHub, not via REST API

## NCBI Entrez Integration Patterns

When the NCBI Entrez MCP server is available, use it to enrich BERDL queries:

### Organism Name → GTDB Species ID

```
1. User provides organism name (e.g., "E. coli K-12")
2. NCBI Entrez: Search taxonomy for NCBI Taxonomy ID
3. BERDL: Query gtdb_species_clade WHERE GTDB_species LIKE '%Escherichia_coli%'
4. Match NCBI taxonomy to GTDB species using species name
```

### Gene Name → BERDL Functional Annotations

```
1. User provides gene name (e.g., "dnaA")
2. NCBI Entrez: Look up gene → get EC number, COG, KEGG orthologs
3. BERDL: Query eggnog_mapper_annotations WHERE EC/KEGG_ko matches
4. Find which species have this gene as core vs accessory
```

### PubMed → BERDL Data Connection

```
1. Literature search finds paper about specific organism/pathway
2. Extract organism name, gene names, EC numbers from paper
3. Query BERDL for corresponding pangenome data
4. Verify whether paper's findings are consistent with BERDL data at scale
```

### Protein Accession → BERDL Genome

```
1. PubMed paper references NCBI protein accession
2. NCBI Entrez: Protein accession → genome assembly accession
3. BERDL: Match assembly accession to genome.genome_id
4. Get species context, pangenome statistics, gene cluster membership
```

## Cross-Database Safety Rules

1. **No direct foreign keys across databases** — all cross-database links are approximate (name matching, ID patterns, or external mapping)
2. **Always validate matches** — after linking, verify that the matched records make biological sense
3. **EC numbers are the best bridge** — most reliable link between pangenome annotations and biochemistry
4. **KEGG/BiGG IDs require external mapping** — ModelSEED uses its own ID system
5. **Gene clusters are species-specific** — cannot match cluster IDs across species; use functional annotations (COG, KEGG, EC) for cross-species comparison
6. **Fitness browser has limited species overlap** — only 48 organisms, not all in pangenome
7. **Complex cross-database joins should run on JupyterHub** — REST API will timeout on multi-step queries
