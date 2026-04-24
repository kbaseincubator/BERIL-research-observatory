# BERDL Ingest Handoff: NMDC Workflow Collections

**Date:** 2026-04-03
**Source:** NUC (`mark@nuc`), repo `~/gitrepos/external-metadata-awareness/`
**Target namespace:** `nmdc_flattened_biosamples` (existing)
**For:** OBI ontology coverage meeting, Monday 2026-04-07

## What's being ingested

Four new parquet files extending the existing `nmdc_flattened_biosamples` namespace with the NMDC provenance chain:

| File | Rows | Size | Description |
|------|------|------|-------------|
| `flattened_data_generation.parquet` | 10,423 | 363K | Sequencing events (NucleotideSequencing, MassSpectrometry) |
| `flattened_workflow_execution.parquet` | 24,698 | 5.5M | Computational pipelines (MagsAnalysis, MetagenomeAnnotation, etc.) |
| `flattened_workflow_execution_mags.parquet` | 40,580 | 49M | Extracted MAG bins with completeness, contamination, GTDB taxonomy |
| `flattened_data_object.parquet` | 226,864 | 7.6M | Output files (FASTA, GFF, stats, raw data) |

All files use embedded Parquet schemas -- no `.sql` schema file needed.

## Key field: `nmdc_type`

The `nmdc_type` column in `flattened_workflow_execution` is the primary field for the OBI meeting. It contains NMDC's internal type system:

```
4220  nmdc:MetagenomeAnnotation
4026  nmdc:ReadQcAnalysis
3933  nmdc:MetagenomeAssembly
3647  nmdc:ReadBasedTaxonomyAnalysis
3258  nmdc:MagsAnalysis
2658  nmdc:MetabolomicsAnalysis
2583  nmdc:NomAnalysis
 166  nmdc:MetaproteomicsAnalysis
  69  nmdc:MetatranscriptomeAssembly
  69  nmdc:MetatranscriptomeExpressionAnalysis
  69  nmdc:MetatranscriptomeAnnotation
```

The OBI story: these 11 types have no OBI equivalents. OBI has `OBI:0200000` (data transformation) but no subtypes for metagenome assembly, genome binning, or taxonomic classification.

## Provenance chain

```
data_generation (sequencing)
  --> workflow_execution (pipelines, via was_informed_by)
    --> data_object (output files, via was_generated_by)
```

`flattened_workflow_execution_mags` is a child table of `flattened_workflow_execution` -- linked by `workflow_execution_id`.

## Ingest instructions

Use `/berdl-ingest` skill. Point it at this directory:

```
/home/mamillerpa/BERIL-research-observatory/data/nmdc_flattened_biosamples/
```

- **Tenant:** use existing tenant for `nmdc_flattened_biosamples`
- **Dataset:** `nmdc_flattened_biosamples` (same namespace -- these are additional tables)
- **Write mode:** The 4 new tables don't conflict with existing tables (flattened_biosample, flattened_study, etc.). Use overwrite for the new tables only.
- **Parquet format:** schema auto-detected, no chunking needed (largest file is 49M)

## Verification query after ingest

```sql
SELECT nmdc_type, COUNT(*) as cnt
FROM nmdc_flattened_biosamples.flattened_workflow_execution
GROUP BY nmdc_type
ORDER BY cnt DESC
```

Should return 11 rows totaling 24,698.

## How these were produced

`flatten_nmdc_collections.py` in `external-metadata-awareness` was extended to process three additional MongoDB collections (`data_generation_set`, `workflow_execution_set`, `data_object_set`). The `type` field -- normally skipped during flattening -- is preserved as `nmdc_type` because it carries semantic meaning (the workflow type). `mags_list` arrays were extracted into a separate child table following the existing `extract_associated_dois` pattern.

Pipeline: MongoDB --> flatten_nmdc_collections.py --> DuckDB --> Parquet (ZSTD compression).

## Also in this namespace (already loaded)

- `flattened_biosample` (14,938 rows)
- `flattened_biosample_chem_administration` (90 rows)
- `flattened_biosample_field_counts` (281 rows)
- `flattened_study` (48 rows)
- `flattened_study_associated_dois` (71 rows)
- `flattened_study_has_credit_associations` (470 rows)
