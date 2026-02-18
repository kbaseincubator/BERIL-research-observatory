# Lakehouse Transfer Report

**Generated**: 2026-02-18T03:04:51
**Target database**: `microbialdiscoveryforge_observatory`
**Total projects**: 22

## Summary

| Metric | Value |
|--------|-------|
| Projects with data | 15 |
| Projects without data | 7 |
| Delta tables to create | 630 |
| Total files to upload | 1225 |
| Total data size (tabular) | 7663.8 MB |
| Total size (all files) | 8712.9 MB (8.5 GB) |

## Per-Project Breakdown

| Project | Data? | Tables | Files | Data MB | Total MB | Issues |
|---------|-------|--------|-------|---------|----------|--------|
| cofitness_coinheritance | Yes | 56 | 75 | 6277.5 | 6280.4 | Large file (>500 MB): data/Smeli_phi_results.tsv (554 MB); Large file (>500 MB): data/all_phi_results.tsv (3058 MB) |
| cog_analysis | Yes | 0 | 17 | 0.0 | 6.4 | - |
| conservation_fitness_synthesis | No | 0 | 9 | 0.0 | 0.6 | No data/ directory exists |
| conservation_vs_fitness | Yes | 53 | 287 | 248.8 | 1047.1 | - |
| core_gene_tradeoffs | No | 0 | 12 | 0.0 | 1.0 | No data/ directory exists |
| costly_dispensable_genes | Yes | 1 | 16 | 20.4 | 21.6 | - |
| ecotype_analysis | Yes | 4 | 14 | 0.9 | 2.1 | - |
| ecotype_env_reanalysis | Yes | 2 | 17 | 0.1 | 19.1 | - |
| enigma_contamination_functional_potential | Yes | 14 | 27 | 4.9 | 5.3 | - |
| env_embedding_explorer | Yes | 5 | 41 | 89.5 | 282.9 | - |
| essential_genome | Yes | 7 | 22 | 184.9 | 186.1 | - |
| field_vs_lab_fitness | Yes | 3 | 19 | 1.0 | 2.3 | - |
| fitness_effects_conservation | Yes | 3 | 20 | 86.1 | 87.8 | - |
| fitness_modules | Yes | 460 | 522 | 683.7 | 686.1 | - |
| lab_field_ecology | Yes | 7 | 20 | 19.4 | 20.3 | - |
| metal_fitness_atlas | Yes | 13 | 36 | 46.6 | 48.5 | - |
| module_conservation | Yes | 2 | 11 | 0.1 | 0.4 | - |
| pangenome_openness | No | 0 | 5 | 0.0 | 0.2 | No data/ directory exists |
| pangenome_pathway_ecology | No | 0 | 10 | 0.0 | 0.1 | No data/ directory exists |
| pangenome_pathway_geography | No | 0 | 19 | 0.0 | 14.3 | data/ directory contains only .gitkeep (no data files) |
| resistance_hotspots | No | 0 | 19 | 0.0 | 0.1 | data/ directory contains only .gitkeep (no data files) |
| temporal_core_dynamics | No | 0 | 7 | 0.0 | 0.1 | No data/ directory exists |

## Issues

- **cofitness_coinheritance**: Large file (>500 MB): data/Smeli_phi_results.tsv (554 MB)
- **cofitness_coinheritance**: Large file (>500 MB): data/all_phi_results.tsv (3058 MB)
- **conservation_fitness_synthesis**: No data/ directory exists
- **core_gene_tradeoffs**: No data/ directory exists
- **pangenome_openness**: No data/ directory exists
- **pangenome_pathway_ecology**: No data/ directory exists
- **pangenome_pathway_geography**: data/ directory contains only .gitkeep (no data files)
- **resistance_hotspots**: data/ directory contains only .gitkeep (no data files)
- **temporal_core_dynamics**: No data/ directory exists

## Projects Without Data

These projects have no data files to upload as Delta tables. They will still have
their non-data files (notebooks, figures, markdown) uploaded to the  table.

- **conservation_fitness_synthesis**: 9 files (docs/notebooks/figures only)
- **core_gene_tradeoffs**: 12 files (docs/notebooks/figures only)
- **pangenome_openness**: 5 files (docs/notebooks/figures only)
- **pangenome_pathway_ecology**: 10 files (docs/notebooks/figures only)
- **pangenome_pathway_geography**: 19 files (docs/notebooks/figures only)
- **resistance_hotspots**: 19 files (docs/notebooks/figures only)
- **temporal_core_dynamics**: 7 files (docs/notebooks/figures only)

## Large File Warnings

These files exceed 500 MB and may require extra Spark memory or chunked upload:

- **cofitness_coinheritance**: Large file (>500 MB): data/Smeli_phi_results.tsv (554 MB)
- **cofitness_coinheritance**: Large file (>500 MB): data/all_phi_results.tsv (3058 MB)

## Table Inventory (Top 5 Projects by Size)

### cofitness_coinheritance (6277.5 MB)

| Table | Source | Size |
|-------|--------|------|
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__all_phi_results` | data/all_phi_results.tsv | 3058.0 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__smeli_phi_results` | data/Smeli_phi_results.tsv | 553.6 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__btheta_phi_results` | data/Btheta_phi_results.tsv | 445.5 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__koxy_phi_results` | data/Koxy_phi_results.tsv | 392.7 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__putida_phi_results` | data/Putida_phi_results.tsv | 386.0 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__syringaeb728a_phi_results` | data/SyringaeB728a_phi_results.tsv | 380.9 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__pseudo3_n2e3_phi_results` | data/pseudo3_N2E3_phi_results.tsv | 372.1 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__ddia6719_phi_results` | data/Ddia6719_phi_results.tsv | 195.7 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__korea_phi_results` | data/Korea_phi_results.tsv | 179.8 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__phaeo_phi_results` | data/Phaeo_phi_results.tsv | 151.7 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__cofit_pseudo3_n2e3_cofit` | data/cofit/pseudo3_N2E3_cofit.tsv | 24.5 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__cofit_smeli_cofit` | data/cofit/Smeli_cofit.tsv | 19.0 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__cofit_koxy_cofit` | data/cofit/Koxy_cofit.tsv | 18.9 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__cofit_syringaeb728a_cofit` | data/cofit/SyringaeB728a_cofit.tsv | 16.8 MB |
| `microbialdiscoveryforge_observatory.cofitness_coinheritance__cofit_putida_cofit` | data/cofit/Putida_cofit.tsv | 16.0 MB |
| ... | +41 more tables | |

### fitness_modules (683.7 MB)

| Table | Source | Size |
|-------|--------|------|
| `microbialdiscoveryforge_observatory.fitness_modules__orthologs_pilot_bbh_pairs` | data/orthologs/pilot_bbh_pairs.csv | 53.4 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_btheta_fitness_matrix` | data/matrices/Btheta_fitness_matrix.csv | 23.1 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_dvh_fitness_matrix` | data/matrices/DvH_fitness_matrix.csv | 23.0 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_btheta_t_matrix` | data/matrices/Btheta_t_matrix.csv | 21.9 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_dvh_t_matrix` | data/matrices/DvH_t_matrix.csv | 21.7 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_putida_fitness_matrix` | data/matrices/Putida_fitness_matrix.csv | 16.0 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_putida_t_matrix` | data/matrices/Putida_t_matrix.csv | 15.0 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_psrch2_fitness_matrix` | data/matrices/psRCH2_fitness_matrix.csv | 12.9 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_psrch2_t_matrix` | data/matrices/psRCH2_t_matrix.csv | 12.2 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_pseudo3_n2e3_fitness_matrix` | data/matrices/pseudo3_N2E3_fitness_matrix.csv | 11.8 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_pseudo3_n2e3_t_matrix` | data/matrices/pseudo3_N2E3_t_matrix.csv | 11.1 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_pseudo6_n2e2_fitness_matrix` | data/matrices/pseudo6_N2E2_fitness_matrix.csv | 10.7 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_pseudo5_n2c3_1_fitness_matrix` | data/matrices/pseudo5_N2C3_1_fitness_matrix.csv | 10.7 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_koxy_fitness_matrix` | data/matrices/Koxy_fitness_matrix.csv | 10.6 MB |
| `microbialdiscoveryforge_observatory.fitness_modules__matrices_marino_fitness_matrix` | data/matrices/Marino_fitness_matrix.csv | 10.3 MB |
| ... | +445 more tables | |

### conservation_vs_fitness (248.8 MB)

| Table | Source | Size |
|-------|--------|------|
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__cluster_metadata` | data/cluster_metadata.tsv | 186.9 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__fb_pangenome_link` | data/fb_pangenome_link.tsv | 21.8 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__essential_genes` | data/essential_genes.tsv | 14.0 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__seed_annotations` | data/seed_annotations.tsv | 7.8 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__kegg_annotations` | data/kegg_annotations.tsv | 4.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__seed_hierarchy` | data/seed_hierarchy.tsv | 0.7 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_cup4g11` | data/diamond_hits/Cup4G11.tsv | 0.5 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_bfirm` | data/diamond_hits/BFirm.tsv | 0.5 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_pseudo5_n2c3_1` | data/diamond_hits/pseudo5_N2C3_1.tsv | 0.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_pseudo6_n2e2` | data/diamond_hits/pseudo6_N2E2.tsv | 0.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_pseudo1_n1b4` | data/diamond_hits/pseudo1_N1B4.tsv | 0.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_pseudo13_gw456_l13` | data/diamond_hits/pseudo13_GW456_L13.tsv | 0.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_pseudo3_n2e3` | data/diamond_hits/pseudo3_N2E3.tsv | 0.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_syringaeb728a_mexbdelta` | data/diamond_hits/SyringaeB728a_mexBdelta.tsv | 0.4 MB |
| `microbialdiscoveryforge_observatory.conservation_vs_fitness__diamond_hits_smeli` | data/diamond_hits/Smeli.tsv | 0.4 MB |
| ... | +38 more tables | |

### essential_genome (184.9 MB)

| Table | Source | Size |
|-------|--------|------|
| `microbialdiscoveryforge_observatory.essential_genome__all_bbh_pairs` | data/all_bbh_pairs.csv | 143.2 MB |
| `microbialdiscoveryforge_observatory.essential_genome__all_essential_genes` | data/all_essential_genes.tsv | 21.2 MB |
| `microbialdiscoveryforge_observatory.essential_genome__all_seed_annotations` | data/all_seed_annotations.tsv | 11.3 MB |
| `microbialdiscoveryforge_observatory.essential_genome__all_ortholog_groups` | data/all_ortholog_groups.csv | 5.0 MB |
| `microbialdiscoveryforge_observatory.essential_genome__essential_families` | data/essential_families.tsv | 2.7 MB |
| `microbialdiscoveryforge_observatory.essential_genome__family_conservation` | data/family_conservation.tsv | 1.3 MB |
| `microbialdiscoveryforge_observatory.essential_genome__essential_predictions` | data/essential_predictions.tsv | 0.2 MB |

### env_embedding_explorer (89.5 MB)

| Table | Source | Size |
|-------|--------|------|
| `microbialdiscoveryforge_observatory.env_embedding_explorer__alphaearth_with_env` | data/alphaearth_with_env.csv | 86.4 MB |
| `microbialdiscoveryforge_observatory.env_embedding_explorer__umap_coords` | data/umap_coords.csv | 3.0 MB |
| `microbialdiscoveryforge_observatory.env_embedding_explorer__isolation_source_raw_counts` | data/isolation_source_raw_counts.csv | 0.2 MB |
| `microbialdiscoveryforge_observatory.env_embedding_explorer__ncbi_env_attribute_counts` | data/ncbi_env_attribute_counts.csv | 0.0 MB |
| `microbialdiscoveryforge_observatory.env_embedding_explorer__coverage_stats` | data/coverage_stats.csv | 0.0 MB |
