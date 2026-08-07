#!/usr/bin/env python3
"""Build a unified MAG -> KO annotation parquet from SPIRE eggnog downloads.
ALL ENVIRONMENTAL (NON-HOST) MAGs VERSION.

Downloads eggnog per sample (streaming, no raw gzip saved to disk), maps each
gene annotation to its MAG via a preloaded contig->MAG dict, then emits per-KO
aggregated rows -- one row per (mag_id, ko_id).

Uses polars for parsing and string operations (vectorized Rust); pandas only
for final parquet write.

Schema mirrors kbase.ke_pangenome eggnog annotations, with per-gene values
aggregated across all genes in the MAG that carry each KO:

    mag_id          str
    sample_id       str
    ko_id           str    e.g. "K00001"
    count           int    copy number
    mean_score      float  mean eggNOG bit score
    min_evalue      float  best e-value
    seed_ortholog   str    first observed
    eggNOG_OGs      str    first observed
    max_annot_lvl   str    first observed
    COG_category    str    first observed
    Description     str    first observed
    Preferred_name  str    first observed
    GOs             str    union (comma-separated)
    EC              str    union
    KEGG_Pathway    str    union
    KEGG_Module     str    union
    KEGG_Reaction   str    union
    KEGG_rclass     str    union
    BRITE           str    first observed
    KEGG_TC         str    union
    CAZy            str    union
    BiGG_Reaction   str    union
    PFAMs           str    union

NOTE: Contig map coverage is 54.3% (80,327 of 147,920 all-env MAGs).
      Rows for MAGs without contig entries will not appear in output.
      Coverage is documented in the final merge log.

Outputs:
  - data/ko_annotations_all/{sample_id}.parquet  -- per-sample intermediates (resumable)
  - data/mag_ko_annotations_all/sample_id={SID}/data.parquet -- Hive-partitioned

Usage:
    python scripts/process_eggnog_all_env.py [--max-samples N]
    python scripts/process_eggnog_all_env.py --merge-only
"""

import argparse
import gc
import gzip
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import pandas as pd
import polars as pl

SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parents[1] / 'scripts'))

DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = DATA_DIR / 'spire_cache'
KO_ANNOT_ALL_DIR = DATA_DIR / 'ko_annotations_all'
KO_ANNOT_ALL_DIR.mkdir(parents=True, exist_ok=True)

MAX_WORKERS = 1
_STANDARD = re.compile(r'^(SAMN|SAMEA|SRS|ERS|DRS)\d+$')

_FIRST_FIELDS = ['seed_ortholog', 'eggNOG_OGs', 'max_annot_lvl', 'COG_category',
                 'Description', 'Preferred_name', 'BRITE']
_UNION_FIELDS = ['GOs', 'EC', 'KEGG_Pathway', 'KEGG_Module', 'KEGG_Reaction',
                 'KEGG_rclass', 'KEGG_TC', 'CAZy', 'BiGG_Reaction', 'PFAMs']

_ALL_ENV_META_CACHE = DATA_DIR / 'all_env_mag_metadata_cache.csv'


def get_all_env_mag_metadata():
    """Return all-env (non-host) MAG metadata. Uses CSV cache to avoid Spark on restarts."""
    if _ALL_ENV_META_CACHE.exists():
        df = pd.read_csv(_ALL_ENV_META_CACHE)
        print(f"Loaded metadata from cache: {len(df):,} MAGs, "
              f"{df['sample_id'].nunique():,} samples")
        return df

    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
    except ImportError:
        from get_spark_session import get_spark_session

    spark = get_spark_session()
    print(f"Spark connected: {spark.version}")

    df = spark.sql("""
        SELECT DISTINCT
            mc.mag_id,
            mc.sample_id,
            gm.genome_size AS genome_size_bp,
            gm.genus
        FROM refdata.spire.mag_coordinates mc
        JOIN refdata.spire.genome_metadata gm ON mc.mag_id = gm.genome_id
        WHERE mc.latitude IS NOT NULL
          AND mc.longitude IS NOT NULL
          AND gm.domain = 'Bacteria'
          AND NOT EXISTS (
            SELECT 1 FROM refdata.spire.sample_microntology sm
            WHERE sm.sample_id = mc.sample_id
              AND (sm.environment_term LIKE '%host%'
                OR sm.environment_term LIKE '%gut%'
                OR sm.environment_term LIKE '%clinical%')
          )
    """).toPandas()

    df.to_csv(_ALL_ENV_META_CACHE, index=False)
    print(f"All-env (non-host) bacterial MAGs: {len(df):,}  Samples: {df['sample_id'].nunique():,}")
    return df


def load_contig_map(all_env_mag_ids: set):
    """Load contig->MAG mapping for all-env MAGs; return (polars DataFrame, frozenset).

    Note: contig map only covers ~54.3% of all-env MAGs (80,327 of 147,920).
    Rows for MAGs without contig entries will simply not appear in output.
    This is acceptable — we process what we can and document coverage.
    """
    parquet_path = DATA_DIR / 'mag_contig_map.parquet'
    print(f"Loading contig->MAG map (filtering to {len(all_env_mag_ids):,} all-env MAGs)...")
    t0 = time.time()
    df = pd.read_parquet(parquet_path, columns=['mag_id', 'contig'])
    df = df[df['mag_id'].isin(all_env_mag_ids)].drop_duplicates(subset='contig').copy()

    n_mags_in_map = df['mag_id'].nunique()
    coverage_pct = 100.0 * n_mags_in_map / len(all_env_mag_ids)

    contig_to_mag_pl = pl.from_pandas(df[['contig', 'mag_id']])
    contig_set = frozenset(df['contig'])

    del df
    gc.collect()
    elapsed = time.time() - t0
    print(f"Loaded {len(contig_to_mag_pl):,} contig->MAG entries "
          f"({n_mags_in_map:,} MAGs, {coverage_pct:.1f}% of all-env) in {elapsed:.1f}s")
    return contig_to_mag_pl, contig_set, n_mags_in_map


ANNOT_ALL_DIR = DATA_DIR / 'mag_ko_annotations_all'

# Canonical schema for the partitioned dataset. count is int64 for compatibility
# with older per-sample parquets written before the polars rewrite (uint32 → int64).
import pyarrow as pa
_ANNOT_SCHEMA = pa.schema([
    ('mag_id',         pa.large_utf8()),
    ('ko_id',          pa.large_utf8()),
    ('count',          pa.int64()),
    ('mean_score',     pa.float64()),
    ('min_evalue',     pa.float64()),
    ('seed_ortholog',  pa.large_utf8()),
    ('eggNOG_OGs',     pa.large_utf8()),
    ('max_annot_lvl',  pa.large_utf8()),
    ('COG_category',   pa.large_utf8()),
    ('Description',    pa.large_utf8()),
    ('Preferred_name', pa.large_utf8()),
    ('BRITE',          pa.large_utf8()),
    ('GOs',            pa.large_utf8()),
    ('EC',             pa.large_utf8()),
    ('KEGG_Pathway',   pa.large_utf8()),
    ('KEGG_Module',    pa.large_utf8()),
    ('KEGG_Reaction',  pa.large_utf8()),
    ('KEGG_rclass',    pa.large_utf8()),
    ('KEGG_TC',        pa.large_utf8()),
    ('CAZy',           pa.large_utf8()),
    ('BiGG_Reaction',  pa.large_utf8()),
    ('PFAMs',          pa.large_utf8()),
    ('sample_id',      pa.large_utf8()),
])


def _normalize_table(table):
    """Cast one per-sample parquet to the canonical schema, filling missing columns."""
    cols = {}
    for field in _ANNOT_SCHEMA:
        if field.name in table.schema.names:
            col = table.column(field.name)
            cols[field.name] = col.cast(field.type) if col.type != field.type else col
        else:
            cols[field.name] = pa.nulls(len(table), type=field.type)
    return pa.table(cols, schema=_ANNOT_SCHEMA)


def merge_parquets():
    """Write per-sample parquets to a Hive-partitioned directory.

    Layout: data/mag_ko_annotations_all/sample_id={SID}/data.parquet
    Each file is one sample — reads are partition-prunable and appends
    are trivial (drop in a new sample_id= subdirectory).
    """
    import pyarrow.parquet as pqlib

    files = sorted(KO_ANNOT_ALL_DIR.glob('*.parquet'))
    if not files:
        print("No per-sample parquets to merge.")
        return

    ANNOT_ALL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing {len(files):,} per-sample parquets to {ANNOT_ALL_DIR}/")

    rows_total = 0
    t0 = time.time()
    for i, f in enumerate(files):
        table = _normalize_table(pqlib.read_table(f))
        sid = table.column('sample_id')[0].as_py()
        part_dir = ANNOT_ALL_DIR / f'sample_id={sid}'
        part_dir.mkdir(exist_ok=True)
        pqlib.write_table(table, str(part_dir / 'data.parquet'), compression='snappy')
        rows_total += len(table)
        del table
        if (i + 1) % 200 == 0 or (i + 1) == len(files):
            elapsed = time.time() - t0
            print(f"  {i+1}/{len(files)}  {rows_total:,} rows  {elapsed:.0f}s", flush=True)

    total_size_gb = sum(
        p.stat().st_size for p in ANNOT_ALL_DIR.rglob('*.parquet')
    ) / 1e9
    elapsed = time.time() - t0
    print(f"Done: {rows_total:,} rows across {len(files):,} partitions  "
          f"{total_size_gb:.1f} GB  {elapsed:.0f}s")


def _process_sample(sid, fetch_fn, contig_to_mag_pl: pl.DataFrame,
                    contig_set: frozenset, all_env_mag_ids: set):
    """Download + parse one sample's eggnog; aggregate per (mag_id, ko_id); save parquet.

    Memory strategy: decompress line-by-line and keep only all-env-MAG rows before
    passing to polars. Large SAMEA samples can be 476 MB gzip = 4 GB decompressed
    with millions of rows from non-env MAGs. By filtering during decompression,
    polars only receives rows belonging to all-env MAGs, keeping per-worker peak reasonable.

    Memory per worker: 36 MB (gzip) + filtered buf + 200 MB (polars) = ~640 MB
    """
    out_path = KO_ANNOT_ALL_DIR / f"{sid}.parquet"
    if out_path.exists():
        return "cached"

    data = fetch_fn(sid)
    if data is None:
        return "failed"

    # Decompress line-by-line; filter to all-env-MAG rows using precomputed frozenset
    col_names = None
    filtered_lines = []
    try:
        with gzip.open(BytesIO(data), 'rt', encoding='ascii', errors='replace') as fh:
            for line in fh:
                if line.startswith('#query'):
                    col_names = line.lstrip('#').strip().split('\t')
                    continue
                if line.startswith('#') or not line.strip():
                    continue
                # Extract contig: strip last '_N' gene-index suffix from query field
                tab = line.index('\t')
                query = line[:tab]
                underscore = query.rfind('_')
                if underscore > 0:
                    contig = query[:underscore]
                    if contig in contig_set:
                        filtered_lines.append(line)
    except Exception as e:
        print(f"  Decompress error {sid}: {e}", flush=True)
        return "parse_error"
    finally:
        del data  # free gzip bytes
    gc.collect()

    if col_names is None:
        return "empty"
    if not filtered_lines:
        return "no_match"

    # Parse only the all-env-MAG rows with polars (fast Rust CSV parser)
    raw_tsv = ''.join(filtered_lines).encode('ascii', errors='replace')
    del filtered_lines
    try:
        df = pl.read_csv(
            raw_tsv,
            separator='\t',
            has_header=False,
            new_columns=col_names,
            infer_schema_length=0,
            ignore_errors=True,
        )
    except Exception as e:
        print(f"  CSV parse error {sid}: {e}", flush=True)
        return "parse_error"
    del raw_tsv
    gc.collect()

    if 'query' not in df.columns:
        return "empty"

    # Strip last '_N' gene index from query to get contig name (vectorized Rust regex)
    df = df.with_columns([
        pl.col('query').str.extract(r'^(.*?)_\d+$', group_index=1).alias('contig')
    ])

    # Inner join = filter to all-env MAGs + lookup mag_id in one vectorized pass
    df = df.join(contig_to_mag_pl, on='contig', how='inner')

    if df.is_empty():
        return "no_match"

    if 'KEGG_ko' not in df.columns:
        return "no_kos"

    # Cast numeric columns (still String from infer_schema_length=0)
    cast_exprs = []
    for col in ('score', 'evalue'):
        if col in df.columns:
            cast_exprs.append(pl.col(col).cast(pl.Float64, strict=False))
    if cast_exprs:
        df = df.with_columns(cast_exprs)

    # Explode KEGG_ko: "ko:K00001,ko:K00002" -> one row per raw token
    df = df.with_columns([
        pl.col('KEGG_ko').fill_null('').str.split(',').alias('_ko_tokens')
    ])
    df = df.explode('_ko_tokens')

    # Extract K##### identifiers (handles "ko:K00001" and "K00001" formats)
    df = df.with_columns([
        pl.col('_ko_tokens').str.extract(r'(K\d{5})').alias('ko_id')
    ])
    df = df.filter(pl.col('ko_id').is_not_null())

    if df.is_empty():
        return "no_kos"

    # Build aggregation expressions
    agg_exprs = [pl.len().alias('count')]

    if 'score' in df.columns:
        agg_exprs.append(pl.col('score').mean().alias('mean_score'))
    if 'evalue' in df.columns:
        agg_exprs.append(pl.col('evalue').min().alias('min_evalue'))

    # First-non-empty value for annotation fields
    for field in _FIRST_FIELDS:
        if field in df.columns:
            agg_exprs.append(
                pl.col(field)
                .filter(
                    pl.col(field).is_not_null() &
                    (pl.col(field).str.strip_chars() != '') &
                    (pl.col(field).str.strip_chars() != '-')
                )
                .first()
                .alias(field)
            )

    result = df.group_by(['mag_id', 'ko_id']).agg(agg_exprs)

    # Union fields: split comma-separated values, deduplicate, rejoin
    for field in _UNION_FIELDS:
        if field in df.columns:
            union_df = (
                df.select(['mag_id', 'ko_id', field])
                .with_columns([pl.col(field).fill_null('').str.split(',').alias('_toks')])
                .explode('_toks')
                .with_columns([pl.col('_toks').str.strip_chars()])
                .filter(
                    (pl.col('_toks') != '') & (pl.col('_toks') != '-')
                )
                .group_by(['mag_id', 'ko_id'])
                .agg(pl.col('_toks').unique().sort().str.join(',').alias(field))
            )
            result = result.join(union_df, on=['mag_id', 'ko_id'], how='left')

    result = result.with_columns([pl.lit(sid).alias('sample_id')])
    result.write_parquet(str(out_path))
    return "ok"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-samples', type=int, default=None)
    parser.add_argument('--merge-only', action='store_true')
    args = parser.parse_args()

    if args.merge_only:
        merge_parquets()
        return

    from spire_api import SPIREClient

    mag_meta_df = get_all_env_mag_metadata()

    standard_mask = mag_meta_df['sample_id'].str.match(_STANDARD)
    n_dropped = (~standard_mask).sum()
    if n_dropped:
        print(f"Dropping {n_dropped:,} MAGs with non-standard sample IDs")
    mag_meta_df = mag_meta_df[standard_mask].copy()

    all_env_mag_ids = set(mag_meta_df['mag_id'])
    contig_to_mag_pl, contig_set, n_mags_in_map = load_contig_map(all_env_mag_ids)

    sample_groups = mag_meta_df.groupby('sample_id')['mag_id'].apply(list).to_dict()

    # Skip samples already written to the partitioned output directory
    done_ids = {p.parent.name.split('=')[1]
                for p in ANNOT_ALL_DIR.glob('sample_id=*/data.parquet')
                if p.parent.name.startswith('sample_id=')}
    to_process = {sid: mids for sid, mids in sample_groups.items()
                  if sid not in done_ids}

    print(f"Total samples:     {len(sample_groups):,}")
    print(f"Already processed: {len(done_ids):,}")
    print(f"To process:        {len(to_process):,}")
    print(f"Contig map covers: {n_mags_in_map:,}/{len(all_env_mag_ids):,} MAGs ({100*n_mags_in_map/len(all_env_mag_ids):.1f}%)")

    if not to_process:
        print("All samples already processed -- merging.")
        merge_parquets()
        return

    if args.max_samples:
        to_process = dict(list(to_process.items())[:args.max_samples])
        print(f"Test mode: capped to {args.max_samples} samples")

    client = SPIREClient(cache_dir=CACHE_DIR)

    done_count = [0]
    failed_count = [0]
    result_counts = {}
    _lock = threading.Lock()
    start = time.time()
    total = len(to_process)

    def _worker(sid_mids):
        sid, _ = sid_mids
        t0 = time.time()
        outcome = _process_sample(sid, client.fetch_eggnog_bytes,
                                  contig_to_mag_pl, contig_set, all_env_mag_ids)
        elapsed = time.time() - t0
        with _lock:
            if outcome not in ("ok", "cached"):
                failed_count[0] += 1
            result_counts[outcome] = result_counts.get(outcome, 0) + 1
            done_count[0] += 1
            n = done_count[0]
        if n <= 5 or n % 10 == 0 or n == total:
            overall_rate = n / (time.time() - start) * 60
            print(f"  [{outcome}] {sid}  {elapsed:.0f}s  "
                  f"| {n}/{total}  {overall_rate:.1f}/min", flush=True)

    print(f"\nStarting with {MAX_WORKERS} workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_worker, item) for item in to_process.items()]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    elapsed = time.time() - start
    print(f"\nDone: {done_count[0]}/{total}  {failed_count[0]} failed  "
          f"{elapsed/60:.1f} min  outcomes={result_counts}")

    merge_parquets()


if __name__ == '__main__':
    main()
