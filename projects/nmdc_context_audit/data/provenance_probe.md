# NMDC Provenance Probe


## `nmdc.metadata`

- (DESCRIBE DATABASE failed: KeyError: 0)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| biosample_set | 16,640 | 2026-05-20 01:15:48.857000 |
| study_set | 84 | 2026-05-20 01:17:08.258000 |
| data_generation_set | 12,026 | 2026-05-20 01:16:18.759000 |
| workflow_execution_set | 30,882 | 2026-05-20 01:17:19.909000 |
| functional_annotation_agg | 54,348,408 | 2026-05-20 01:16:50.909000 |

## `nmdc.ncbi_biosamples`

- (DESCRIBE DATABASE failed: KeyError: 0)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| biosamples_flattened | 51,711,888 | 2026-03-09 03:58:35.218000 |
| biosamples_attributes | 756,112,544 | 2026-03-09 03:56:05.861000 |
| bioprojects_flattened | 1,034,221 | 2026-03-09 03:53:21.263000 |
| sra_biosamples_bioprojects | 33,738,101 | 2026-03-09 04:00:23.761000 |

## `nmdc.ref_data`

- (DESCRIBE DATABASE failed: KeyError: 0)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| pfam_terms | 27,481 | 2026-05-20 01:17:47.112000 |

## `nmdc.results`

- (DESCRIBE DATABASE failed: KeyError: 0)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| annotation_statistics | 4,815 | 2026-05-20 01:31:48.258000 |
| gtdbtk_bacterial_summary | 18,410 | 2026-05-20 01:17:55.295000 |
| checkm_statistics | 69,723 | 2026-05-20 01:17:49.161000 |
| annotation_kegg_orthology | 1,831,998,811 | 2026-05-20 01:31:46.032000 |

## `kbase.nmdc_arkin`

- (DESCRIBE DATABASE failed: UnknownException: (org.apache.iceberg.exceptions.ForbiddenException) Forbidden: Principal 'mamillerpa' with activated PrincipalRoles '[kesciencero_member, microbialdisc)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| study_table | 48 | 2026-05-27 04:10:31.296000 |
| taxonomy_dim | 2,594,787 | 2026-05-27 04:10:34.181000 |
| embeddings_v1 | 5,316 | 2026-05-27 04:08:18.439000 |
| sample_file_lookup | 6,700 | 2026-05-27 04:10:24.977000 |
| metabolomics_gold | 3,129,061 | 2026-05-27 04:08:59.978000 |
| omics_files_table | 385,562 | 2026-05-27 04:10:16.778000 |

## `kbase.nmdc_mags`

- (DESCRIBE DATABASE failed: UnknownException: (org.apache.iceberg.exceptions.ForbiddenException) Forbidden: Principal 'mamillerpa' with activated PrincipalRoles '[kesciencero_member, microbialdisc)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| mag_catalog | 62,346 | 2026-07-02 16:09:49.338000 |
| bin_catalog | 17,218 | 2026-07-02 16:12:24.853000 |
| biosample_metadata | 1,349 | 2026-07-01 17:59:52.754000 |
| study_sample | 1,405 | 2026-07-01 17:59:57.038000 |

## `kbase.nmdc_neon`

- (DESCRIBE DATABASE failed: UnknownException: (org.apache.iceberg.exceptions.ForbiddenException) Forbidden: Principal 'mamillerpa' with activated PrincipalRoles '[kesciencero_member, microbialdisc)

| table | rows | last_commit (Iceberg) |
|---|---:|---|
| neon_mag_catalog | 16,093 | 2026-07-02 16:06:07.593000 |
| sample_data | 340,871 | 2026-06-24 20:38:10.605000 |
| study_sample | 5,917 | 2026-07-02 16:38:18.866000 |