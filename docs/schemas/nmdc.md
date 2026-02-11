# NMDC Databases Schema Documentation

**Databases**: `nmdc_arkin`, `nmdc_ncbi_biosamples`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: NMDC (National Microbiome Data Collaborative)
**Last Updated**: 2026-02-11

---

## Overview

Two databases supporting the National Microbiome Data Collaborative (NMDC):

1. **`nmdc_arkin`**: Multi-omics analysis data including functional annotations, embeddings, metabolomics, proteomics, lipidomics, metatranscriptomics, and microbial trait data. Used for integrated microbiome analysis.

2. **`nmdc_ncbi_biosamples`**: Harmonized NCBI BioSample metadata with standardized attributes, environmental triads, and dimensional statistics.

---

## nmdc_arkin

### Table Summary

#### Annotation & Ontology Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `annotation_terms_unified` | 67,353 | Unified annotation terms (COG, EC, GO, KEGG, MetaCyc) |
| `annotation_crossrefs` | varies | Cross-references between annotation systems |
| `annotation_hierarchies_unified` | varies | Hierarchical annotation relationships |
| `cog_categories` | varies | COG category definitions |
| `cog_hierarchy_flat` | varies | Flattened COG hierarchy |
| `ec_terms` | varies | EC number definitions |
| `ec_hierarchy_flat` | varies | Flattened EC hierarchy |
| `go_terms` | varies | GO term definitions |
| `go_hierarchy_flat` | varies | Flattened GO hierarchy |
| `kegg_ko_terms` | varies | KEGG KO definitions |
| `kegg_ko_module` | varies | KO-to-module mappings |
| `kegg_ko_pathway` | varies | KO-to-pathway mappings |
| `kegg_module_terms` | varies | KEGG module definitions |
| `kegg_pathway_terms` | varies | KEGG pathway definitions |
| `metacyc_pathways` | varies | MetaCyc pathway definitions |
| `metacyc_pathway_reactions` | varies | Pathway-reaction mappings |
| `metacyc_reaction_ec` | varies | Reaction-EC mappings |
| `rhea_reactions` | varies | Rhea reaction definitions |
| `rhea_crossrefs` | varies | Rhea cross-references |

#### Embeddings & ML Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `embeddings_v1` | 5,316 | 256-dimensional sample embeddings |
| `sample_tokens_v1` | varies | Tokenized sample representations |
| `vocab_registry_v1` | varies | Token vocabulary |
| `abiotic_embeddings` | varies | Abiotic factor embeddings |
| `biochemical_embeddings` | varies | Biochemical embeddings |
| `taxonomy_embeddings` | varies | Taxonomy embeddings (all ranks) |
| `trait_embeddings` | varies | Microbial trait embeddings |
| `unified_embeddings` | varies | Combined embeddings |
| `embedding_metadata` | varies | Embedding metadata |

#### Feature Tables (per-sample structured data)

| Table | Row Count | Description |
|-------|-----------|-------------|
| `abiotic_features` | varies | Environmental measurements per sample |
| `biochemical_features` | varies | Biochemical measurements |
| `taxonomy_features` | varies | Taxonomic profiles (6,365 samples) |
| `trait_features` | varies | Microbial trait profiles (90+ traits) |
| `trait_unified` | varies | Unified trait data |

#### Multi-omics Gold Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `metabolomics_gold` | 3,129,061 | Metabolomics measurements |
| `proteomics_gold` | varies | Proteomics measurements |
| `lipidomics_gold` | 1,395,867 | Lipidomics measurements |
| `metatranscriptomics_gold` | varies | Metatranscriptomics data |
| `nom_gold` | varies | Natural organic matter data |

#### Taxonomy & Study Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `study_table` | 48 | Study definitions |
| `taxonomy_dim` | varies | Taxonomy dimensions |
| `taxstring_lookup` | varies | Taxonomy string lookups |
| `centrifuge_gold` | varies | Centrifuge classifications |
| `gottcha_gold` | varies | GOTTCHA classifications |
| `kraken_gold` | varies | Kraken classifications |
| `contig_taxonomy` | varies | Contig-level taxonomy |

---

### Key Table Schemas

#### `annotation_terms_unified`

| Column | Type | Description |
|--------|------|-------------|
| `source` | string | Annotation source (COG, EC, GO, KEGG, MetaCyc) |
| `term_id` | string | Term identifier |
| `name` | string | Term name |
| `description` | string | Term description |
| `namespace` | string | Term namespace |
| `is_obsolete` | string | Whether term is obsolete |

#### `abiotic_features`

| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | string | **Primary Key**. Sample identifier |
| `annotations_ammonium_has_numeric_value` | string | Ammonium concentration |
| `annotations_ph` | string | pH value |
| `annotations_temp_has_numeric_value` | string | Temperature |
| `annotations_diss_oxygen_has_numeric_value` | string | Dissolved oxygen |
| ... | string | (21 environmental measurement columns) |

#### `trait_features`

| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | string | **Primary Key**. Sample identifier |
| `cell_shape` | string | Cell morphology |
| `oxygen_preference` | string | Aerobic/anaerobic preference |
| `gram_stain` | string | Gram stain result |
| `motility` | string | Motility |
| `spore_formation` | string | Spore formation ability |
| `GC_content` | string | GC content |
| `functional_group:*` | string | ~90 functional group columns (e.g., fermentation, nitrogen_fixation) |

---

## nmdc_ncbi_biosamples

### Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `biosamples_flattened` | varies | Flattened biosample records |
| `biosamples_attributes` | varies | Biosample attributes |
| `biosamples_ids` | varies | Biosample identifiers |
| `biosamples_links` | varies | Biosample-related links |
| `bioprojects_flattened` | varies | Flattened bioproject records |
| `env_triads_flattened` | varies | Environmental triads (broad/local/medium) |
| `ncbi_attributes_flattened` | varies | NCBI attribute definitions |
| `ncbi_packages_flattened` | varies | NCBI package definitions |
| `sra_biosamples_bioprojects` | varies | SRA-BioSample-BioProject links |
| `attribute_harmonized_pairings` | varies | Harmonized attribute pairs |
| `content_pairs_aggregated` | varies | Aggregated content pairs |
| `harmonized_name_dimensional_stats` | varies | Harmonized name statistics |
| `harmonized_name_usage_stats` | varies | Usage statistics |
| `measurement_evidence_percentages` | varies | Measurement evidence |
| `measurement_results_skip_filtered` | varies | Filtered measurement results |
| `mixed_content_counts` | varies | Mixed content statistics |
| `unit_assertion_counts` | varies | Unit assertion counts |

---

## Pitfalls

- `nmdc_arkin` has 60+ tables. Many are specialized ML/embedding tables.
- Embedding dimensions vary: `embeddings_v1` has 256 dimensions, other embeddings vary.
- The `trait_features` table has ~90 functional group columns as individual boolean-like columns.
- Many row counts timed out during introspection; actual sizes may be large.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.
