# Parquet staging CLI

`scripts/ingest_dataset.py` provides a non-interactive path for staging a
directory containing one Parquet file per table. It reuses the same upload,
ingest, progress, and source-grounded verification functions as the maintained
ingest notebooks. It does not promote, drop, or replace a canonical namespace.

The command is off-cluster: run it from a BERIL checkout whose `.venv-berdl`
environment, tunnels, proxy, and object-store configuration pass the existing
remote-ingest preconditions. The in-cluster workflow still uses the maintained
notebook because its Spark and object-store clients require the JupyterHub
bypass described by the `berdl-ingest` skill.

## Plan without mutation

Choose a unique staging dataset, bronze prefix, progress key, and configuration
key. The progress and configuration objects must be children of the bronze
prefix. Running without `--execute-staging` validates the identifiers and source
directory, prints every table and destination, and performs no network or
storage operation:

```bash
source .venv-berdl/bin/activate
python scripts/ingest_dataset.py \
  --data-dir /absolute/path/to/parquet-snapshot \
  --tenant nmdc \
  --dataset nmdc_metadata_staging_20260819 \
  --staging-namespace nmdc.nmdc_metadata_staging_20260819 \
  --mode overwrite \
  --bronze-prefix tenant-general-warehouse/nmdc/staging/20260819 \
  --progress-key tenant-general-warehouse/nmdc/staging/20260819/progress.jsonl \
  --config-key tenant-general-warehouse/nmdc/staging/20260819/config.json
```

The directory may contain non-tabular snapshot metadata alongside the Parquet
files. It must not contain CSV, TSV, SQLite, symlinked Parquet, unsafe table
names, or two Parquet files with the same stem. Parquet planning reports bytes,
not binary newline counts; exact source rows are counted from uploaded Parquet
during verification.

## Execute staging and verify

Review the plan first. Add both the explicit execution flag and a new outcome
path to run the same plan:

```bash
python scripts/ingest_dataset.py \
  --data-dir /absolute/path/to/parquet-snapshot \
  --tenant nmdc \
  --dataset nmdc_metadata_staging_20260819 \
  --staging-namespace nmdc.nmdc_metadata_staging_20260819 \
  --mode overwrite \
  --bronze-prefix tenant-general-warehouse/nmdc/staging/20260819 \
  --progress-key tenant-general-warehouse/nmdc/staging/20260819/progress.jsonl \
  --config-key tenant-general-warehouse/nmdc/staging/20260819/config.json \
  --outcome /absolute/path/to/staging-outcome.json \
  --execute-staging
```

Execution proceeds through four declared phases:

1. initialize the existing remote Spark and object-store clients;
2. replace every selected bronze Parquet object and stream-hash its stored bytes;
3. ingest into the explicit staging namespace; and
4. compare every catalog table count with Spark's count of its uploaded source
   Parquet object.

The outcome file is created atomically and is never replaced. It records the
destination and the object-storage-verified source SHA-256 for every table, so
downstream automation can bind catalog verification to exact reviewed bytes.
The command exits
nonzero for an incomplete progress record, unreadable source, count mismatch,
upload or ingest failure, or an existing outcome path. Provider exceptions are
reduced to their type in the outcome so credentials and records cannot be
copied into an automation artifact.

A verified outcome authorizes no promotion. Review it with the dataset-specific
disposition and metadata plans before using a separately approved canonical
promotion and recovery procedure.
