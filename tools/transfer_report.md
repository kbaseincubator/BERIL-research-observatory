# Lakehouse Transfer Report

**Completed**: 2026-02-18
**Storage**: MinIO object storage (`mc` CLI)
**Path**: `s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/`
**mc alias**: `berdl-minio`

## Summary

| Metric | Value |
|--------|-------|
| Projects uploaded | 22 |
| Total files | 1,244 |
| Total size | 8.5 GiB |
| Upload method | `mc cp --recursive` |
| Validation | All projects OK (remote file count >= local) |

## Per-Project Results

| Project | Local | Remote | Status |
|---------|-------|--------|--------|
| cofitness_coinheritance | 75 | 75 | OK |
| cog_analysis | 17 | 17 | OK |
| conservation_fitness_synthesis | 9 | 11 | OK |
| conservation_vs_fitness | 287 | 298 | OK |
| core_gene_tradeoffs | 12 | 12 | OK |
| costly_dispensable_genes | 16 | 16 | OK |
| ecotype_analysis | 14 | 14 | OK |
| ecotype_env_reanalysis | 17 | 17 | OK |
| enigma_contamination_functional_potential | 27 | 27 | OK |
| env_embedding_explorer | 41 | 42 | OK |
| essential_genome | 22 | 22 | OK |
| field_vs_lab_fitness | 19 | 19 | OK |
| fitness_effects_conservation | 20 | 20 | OK |
| fitness_modules | 522 | 526 | OK |
| lab_field_ecology | 20 | 20 | OK |
| metal_fitness_atlas | 36 | 36 | OK |
| module_conservation | 11 | 11 | OK |
| pangenome_openness | 5 | 5 | OK |
| pangenome_pathway_ecology | 10 | 10 | OK |
| pangenome_pathway_geography | 18 | 18 | OK |
| resistance_hotspots | 19 | 20 | OK |
| temporal_core_dynamics | 7 | 7 | OK |

## Notes

- Remote counts slightly exceed local for some projects because `mc cp` includes
  `.ipynb_checkpoints` files that the local manifest excludes.
- All files uploaded as-is (no format conversion). CSV/TSV files can be read via
  Spark with `spark.read.csv("s3a://cdm-lake/...")` if needed.
- Download any project with: `mc cp --recursive berdl-minio/cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/<project>/ ./`

## Upload Tool

Validate uploads at any time:
```bash
python tools/lakehouse_upload.py --validate
python tools/lakehouse_upload.py --list
```

Upload a single project:
```bash
python tools/lakehouse_upload.py <project_id>
```
