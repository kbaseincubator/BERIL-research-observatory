# PhageFoundry Genome Browser Databases Schema Documentation

**Databases**:
- `phagefoundry_acinetobacter_genome_browser`
- `phagefoundry_ecoliphagesgenomedepot`
- `phagefoundry_klebsiella_genome_browser_genomedepot`
- `phagefoundry_paeruginosa_genome_browser`
- `phagefoundry_pviridiflava_genome_browser`
- `phagefoundry_strain_modelling`

**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: PhageFoundry
**Last Updated**: 2026-05-05

---

## Overview

Species-specific genome browser databases for the PhageFoundry project, supporting phage-host interaction research. Each genome browser database shares the same schema (GenomeDepot format) with 37 tables covering genomes, genes, proteins, functional annotations, operons, regulons, and strain metadata. The companion `phagefoundry_strain_modelling` database (different schema) holds strain-modelling experiment results — see the dedicated section below.

Confirmed species:
- *Acinetobacter* (~891 strains, 112K contigs) — `phagefoundry_acinetobacter_genome_browser`
- *E. coli* phages — `phagefoundry_ecoliphagesgenomedepot` (38 tables; the only browser DB with `browser_config`)
- *Klebsiella* — `phagefoundry_klebsiella_genome_browser_genomedepot`
- *Pseudomonas aeruginosa* — `phagefoundry_paeruginosa_genome_browser`
- *Pseudomonas viridiflava* — `phagefoundry_pviridiflava_genome_browser`

---

## Common Table Schema (all genome browsers)

All four genome browser databases share identical table structure:

### Entity Tables

| Table | Description |
|-------|-------------|
| `browser_genome` | Genome records |
| `browser_gene` | Gene records |
| `browser_protein` | Protein sequences |
| `browser_contig` | Contigs/scaffolds |
| `browser_strain` | Strain information |
| `browser_sample` | Sample metadata |
| `browser_taxon` | Taxonomic information |
| `browser_annotation` | Gene annotations |
| `browser_operon` | Operon definitions |
| `browser_regulon` | Regulon definitions |
| `browser_regulon_regulators` | Regulon regulator genes |
| `browser_ortholog_group` | Ortholog groups |
| `browser_site` | Regulatory sites |
| `browser_tag` | Genome tags/labels |

### Functional Annotation Tables

| Table | Description |
|-------|-------------|
| `browser_cazy_family` | CAZy family definitions |
| `browser_cog_class` | COG class definitions |
| `browser_ec_number` | EC number definitions |
| `browser_eggnog_description` | eggNOG descriptions |
| `browser_go_term` | GO term definitions |
| `browser_kegg_ortholog` | KEGG ortholog definitions |
| `browser_kegg_pathway` | KEGG pathway definitions |
| `browser_kegg_reaction` | KEGG reaction definitions |
| `browser_tc_family` | Transporter classification families |

### Protein Annotation Junction Tables

| Table | Description |
|-------|-------------|
| `browser_protein_cazy_families` | Protein-CAZy associations |
| `browser_protein_cog_classes` | Protein-COG associations |
| `browser_protein_ec_numbers` | Protein-EC associations |
| `browser_protein_go_terms` | Protein-GO associations |
| `browser_protein_kegg_orthologs` | Protein-KEGG ortholog associations |
| `browser_protein_kegg_pathways` | Protein-KEGG pathway associations |
| `browser_protein_kegg_reactions` | Protein-KEGG reaction associations |
| `browser_protein_ortholog_groups` | Protein-ortholog group associations |
| `browser_protein_tc_families` | Protein-transporter associations |

### Other Tables

| Table | Description |
|-------|-------------|
| `browser_genome_tags` | Genome-tag associations |
| `browser_sample_metadata` | Sample key-value metadata |
| `browser_strain_metadata` | Strain key-value metadata |
| `browser_site_genes` | Regulatory site-gene associations |
| `browser_site_operons` | Regulatory site-operon associations |
| `browser_config` | Browser-instance configuration as `(id, param, value)` rows. Present only on `phagefoundry_ecoliphagesgenomedepot`. |

---

## phagefoundry_strain_modelling

Companion database holding strain-modelling experiment results (genome-set comparisons, protein families, feature-level metrics). 18 tables, schema unrelated to the genome-browser tables above. All `id` columns are surrogate primary keys; foreign keys use `bigint`.

### Genome and organism tables

| Table | Columns | Notes |
|-------|---------|-------|
| `strainmodelling_organism` | `id` (int), `name` (string), `full_name` (string), `domain` (string), `description` (string) | Source organisms |
| `strainmodelling_organism_metadata` | `id` (int), `param` (string), `value` (string), `organism_id` (bigint), `description` (string) | Key-value metadata for organisms |
| `strainmodelling_genome` | `id` (int), `ref` (string), `organism_id` (bigint), `description` (string), `genome_file` (string), `name` (string) | Genome assemblies |
| `strainmodelling_genome_set` | `id` (int), `description` (string), `name` (string) | Named genome groupings used in experiments |
| `strainmodelling_genome_set_genomes` | `id` (int), `genome_set_id` (bigint), `genome_id` (bigint) | Genome-set membership |

### Sequence and feature tables

| Table | Columns | Notes |
|-------|---------|-------|
| `strainmodelling_sequence` | `id` (int), `name` (string), `accession` (string), `genome_id` (bigint), `sequence` (string) | Contig/scaffold sequences |
| `strainmodelling_gene` | `id` (int), `name` (string), `locus_tag` (string), `start` (int), `end` (int), `strand` (int), `protein_seq` (string), `seq_src_id` (bigint), `genome_id` (bigint), `product` (string) | Gene records with protein sequence |
| `strainmodelling_interval` | `id` (int), `start` (int), `end` (int), `strand` (int), `contig_id` (bigint) | Genomic intervals |
| `strainmodelling_feature` | `id` (int), `feature_type` (string), `experiment_id` (bigint), `genome_id` (bigint) | Computed features per experiment |
| `strainmodelling_feature_intervals` | `id` (int), `feature_id` (bigint), `interval_id` (bigint) | Feature ↔ interval junction |
| `strainmodelling_feature_metric` | `id` (int), `param` (string), `value` (string), `feature_id` (bigint), `description` (string) | Per-feature metrics |

### Experiment tables

| Table | Columns | Notes |
|-------|---------|-------|
| `strainmodelling_experiment` | `id` (int), `name` (string), `timestamp` (string), `genomeset1_id` (bigint), `genomeset2_id` (bigint), `description` (string) | Strain-comparison experiments |
| `strainmodelling_experiment_metadata` | `id` (int), `param` (string), `value` (string), `experiment_id` (bigint) | Experiment-level key-value metadata |
| `strainmodelling_experiment_metric` | `id` (int), `param` (string), `value` (string), `experiment_id` (bigint), `description` (string) | Experiment-level metrics |
| `strainmodelling_interaction` | `id` (int), `organism1_id` (bigint), `organism2_id` (bigint), `description` (string), `value` (int), `experiment_id` (bigint) | Pairwise organism interactions per experiment |

### Protein family tables

| Table | Columns | Notes |
|-------|---------|-------|
| `strainmodelling_protein_family` | `id` (int), `name` (string), `genomeset_id` (bigint) | Protein families derived per genome-set |
| `strainmodelling_protein_family_features` | `id` (int), `protein_family_id` (bigint), `feature_id` (bigint) | Family ↔ feature junction |
| `strainmodelling_protein_family_genes` | `id` (int), `protein_family_id` (bigint), `gene_id` (bigint) | Family ↔ gene junction |

---

## Pitfalls

- Schema introspection of the genome-browser tables timed out in 2026-02 ingestion logs; column-level types for `browser_*` tables are not in this doc and should be fetched on demand via `DESCRIBE TABLE`.
- All five genome browsers share the same `browser_*` core schema. `phagefoundry_ecoliphagesgenomedepot` has one extra table (`browser_config`) not present on the others.
- `phagefoundry_strain_modelling` uses a different schema family (`strainmodelling_*`) and should not be joined to the genome-browser tables; it tracks experiment results, not browseable annotations.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.
- **2026-05-05**: Document `phagefoundry_strain_modelling` (18 tables) and `phagefoundry_ecoliphagesgenomedepot`-only `browser_config`. Add `phagefoundry_ecoliphagesgenomedepot` to the database list (was missing).
