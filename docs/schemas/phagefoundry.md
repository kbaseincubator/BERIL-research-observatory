# PhageFoundry Genome Browser Databases Schema Documentation

**Databases**:
- `phagefoundry_acinetobacter_genome_browser`
- `phagefoundry_klebsiella_genome_browser_genomedepot`
- `phagefoundry_paeruginosa_genome_browser`
- `phagefoundry_pviridiflava_genome_browser`
- `phagefoundry_strain_modelling`

**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: PhageFoundry
**Last Updated**: 2026-02-11

---

## Overview

Species-specific genome browser databases for the PhageFoundry project, supporting phage-host interaction research. Each genome browser database shares the same schema (GenomeDepot format) with 37 tables covering genomes, genes, proteins, functional annotations, operons, regulons, and strain metadata.

Confirmed species:
- *Acinetobacter* (~891 strains, 112K contigs)
- *Klebsiella* (GenomeDepot format)
- *Pseudomonas aeruginosa*
- *Pseudomonas viridiflava*

An additional `phagefoundry_strain_modelling` database exists but timed out during introspection.

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

---

## Pitfalls

- Schema introspection timed out for most tables in these databases.
- All four genome browsers share the same table structure but contain different species data.
- `phagefoundry_strain_modelling` is a separate database with unknown schema.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.
