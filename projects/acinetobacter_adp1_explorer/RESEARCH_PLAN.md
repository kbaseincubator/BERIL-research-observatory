# Research Plan: Acinetobacter baylyi ADP1 Data Explorer

## Research Question
What is the full scope of a comprehensive ADP1 database, and where does it connect to BERDL collections?

## Hypothesis
This is an exploration project rather than a hypothesis-driven study. The working assumption is that the ADP1 database contains identifiers (reaction IDs, pangenome cluster IDs, UniRef IDs, COG/KEGG annotations) that map directly to BERDL collections, enabling cross-referencing between user-provided experimental data and the broader lakehouse.

## Approach

### Phase 1: Database Inventory
Characterize every table in `berdl_tables.db`:
- Row counts, column types, NULL coverage
- Key identifier formats and value distributions
- Relationships between tables (shared keys)

### Phase 2: BERDL Connection Mapping
For each identifier type found in the ADP1 database, check whether it maps to a BERDL collection:

| ADP1 Identifier | BERDL Collection | Link Strategy |
|-----------------|-----------------|---------------|
| `reaction_id` (rxn00001 format) | `kbase_msd_biochemistry.reaction` | Direct match on reaction ID |
| `pangenome_cluster_id` | `kbase_ke_pangenome.gene_cluster` | Match via species clade + cluster ID |
| `uniref_50/90/100` | `kbase_uniref50/90/100` | Direct match on UniRef ID |
| `cog` | `kbase_ke_pangenome.eggnog_mapper_annotations` | Match via COG_category |
| `ko` | `kbase_ke_pangenome.eggnog_mapper_annotations` | Match via KEGG_ko |
| `genome_id` (GCF/GCA format) | `kbase_ke_pangenome.genome` | Direct match on genome_id |
| Organism name | `kescience_fitnessbrowser.organism` | Taxonomy match |
| Organism name | `phagefoundry_acinetobacter_genome_browser` | Strain match |

### Phase 3: Integration Highlights
For the strongest connection points, pull sample data from both sides and demonstrate the join works.

## Analysis Plan

### Notebook 1: Database Exploration
- **Goal**: Full inventory of the SQLite database — tables, schemas, row counts, sample data, NULL coverage, key distributions
- **Expected output**: Summary tables, relationship diagram

### Notebook 2: BERDL Connection Scan
- **Goal**: For each identifier type, query BERDL to check for matches
- **Expected output**: Connection matrix showing which links work and coverage %

### Notebook 3: Integration Deep-Dives (if warranted)
- **Goal**: For the richest connection points, pull data from both sides and explore
- **Expected output**: Joined datasets, comparison figures

## Revision History
- **v1** (2026-02-18): Initial plan

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
