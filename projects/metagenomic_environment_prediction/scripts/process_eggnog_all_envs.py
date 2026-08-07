"""Expand SPIRE eggnog KO annotations to all environments (not just soil/rhizosphere).

Identical logic to process_eggnog_to_parquet.py but with no environment filter in
the metadata query. Uses the same mag_contig_map.parquet (covers 80,327 MAGs).
MAGs not present in the contig map are silently dropped (no contig→MAG match).

Outputs:
  - data/all_env_ko_annotations_work/{sample_id}.parquet  -- per-sample intermediates
  - data/all_env_mag_ko_annotations/sample_id={SID}/data.parquet  -- final Hive-partitioned

Usage:
    python scripts/process_eggnog_all_envs.py [--max-samples N]
    python scripts/process_eggnog_all_envs.py --merge-only
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
import pyarrow as pa

SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parents[1] / 'scripts'))

DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = DATA_DIR / 'spire_cache'
WORK_DIR = DATA_DIR / 'all_env_ko_annotations_work'
ANNOT_DIR = DATA_DIR / 'all_env_mag_ko_annotations'
WORK_DIR.mkdir(parents=True, exist_ok=True)

MAX_WORKERS = 5
_STANDARD = re.compile(r'^(SAMN|SAMEA|SRS|ERS|DRS)\d+$')

_FIRST_FIELDS = ['seed_ortholog', 'eggNOG_OGs', 'max_annot_lvl', 'COG_category',
                 'Description', 'Preferred_name', 'BRITE']
_UNION_FIELDS = ['GOs', 'EC', 'KEGG_Pathway', 'KEGG_Module', 'KEGG_Reaction',
                 'KEGG_rclass', 'KEGG_TC', 'CAZy', 'BiGG_Reaction', 'PFAMs']

_META_CACHE = DATA_DIR / 'all_mag_metadata_cache.csv'

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


def get_all_mag_metadata(contig_map_mag_ids: set):
    """Return metadata for all SPIRE bacterial MAGs present in the contig map.

    Uses a CSV cache to avoid Spark on restarts. Queries without environment
    filter; intersects with contig_map_mag_ids so we only fetch samples where
    we can actually do contig→MAG mapping.
    """
    if _META_CACHE.exists():
        df = pd.read_csv(_META_CACHE)
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
    """).toPandas()

    # Only keep MAGs where we have contig→MAG mapping
    before = len(df)
    df = df[df['mag_id'].isin(contig_map_mag_ids)].copy()
    print(f"All bacterial MAGs with coordinates: {before:,}  "
          f"In contig map: {len(df):,}  Samples: {df['sample_id'].nunique():,}")

    df.to_csv(_META_CACHE, index=False)
    return df


def load_contig_map(target_mag_ids: set):
    """Load contig->MAG mapping filtered to target MAG IDs."""
    parquet_path = DATA_DIR / 'mag_contig_map.parquet'
    print(f"Loading contig->MAG map (filtering to {len(target_mag_ids):,} MAGs)...")
    t0 = time.time()
    df = pd.read_parquet(parquet_path, columns=['mag_id', 'contig'])
    df = df[df['mag_id'].isin(target_mag_ids)].drop_duplicates(subset='contig').copy()

    contig_to_mag_pl = pl.from_pandas(df[['contig', 'mag_id']])
    contig_set = frozenset(df['contig'])

    del df
    gc.collect()
    elapsed = time.time() - t0
    print(f"Loaded {len(contig_to_mag_pl):,} contig->MAG entries in {elapsed:.1f}s")
    return contig_to_mag_pl, contig_set


def _normalize_table(table):
    cols = {}
    for field in _ANNOT_SCHEMA:
        if field.name in table.schema.names:
            col = table.column(field.name)
            cols[field.name] = col.cast(field.type) if col.type != field.type else col
        else:
            cols[field.name] = pa.nulls(len(table), type=field.type)
    return pa.table(cols, schema=_ANNOT_SCHEMA)


def merge_parquets():
    """Write per-sample work parquets to a Hive-partitioned output directory."""
    import pyarrow.parquet as pqlib

    files = sorted(WORK_DIR.glob('*.parquet'))
    if not files:
        print("No per-sample parquets to merge.")
        return

    ANNOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing {len(files):,} per-sample parquets to {ANNOT_DIR}/")

    rows_total = 0
    t0 = time.time()
    for i, f in enumerate(files):
        table = _normalize_table(pqlib.read_table(f))
        sid = table.column('sample_id')[0].as_py()
        part_dir = ANNOT_DIR / f'sample_id={sid}'
        # Skip if already merged
        if (part_dir / 'data.parquet').exists():
            rows_total += len(table)
            del table
            continue
        part_dir.mkdir(exist_ok=True)
        pqlib.write_table(table, str(part_dir / 'data.parquet'), compression='snappy')
        rows_total += len(table)
        del table
        if (i + 1) % 200 == 0 or (i + 1) == len(files):
            elapsed = time.time() - t0
            print(f"  {i+1}/{len(files)}  {rows_total:,} rows  {elapsed:.0f}s", flush=True)

    total_size_gb = sum(
        p.stat().st_size for p in ANNOT_DIR.rglob('*.parquet')
    ) / 1e9
    elapsed = time.time() - t0
    print(f"Done: {rows_total:,} rows across {len(files):,} partitions  "
          f"{total_size_gb:.1f} GB  {elapsed:.0f}s")


def _process_sample(sid, fetch_fn, contig_to_mag_pl, contig_set, all_mag_ids):
    out_path = WORK_DIR / f"{sid}.parquet"
    if out_path.exists():
        return "cached"

    data = fetch_fn(sid)
    if data is None:
        return "failed"

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
        del data
    gc.collect()

    if col_names is None:
        return "empty"
    if not filtered_lines:
        return "no_match"

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

    df = df.with_columns([
        pl.col('query').str.extract(r'^(.*?)_\d+$', group_index=1).alias('contig')
    ])
    df = df.join(contig_to_mag_pl, on='contig', how='inner')

    if df.is_empty():
        return "no_match"
    if 'KEGG_ko' not in df.columns:
        return "no_kos"

    cast_exprs = []
    for col in ('score', 'evalue'):
        if col in df.columns:
            cast_exprs.append(pl.col(col).cast(pl.Float64, strict=False))
    if cast_exprs:
        df = df.with_columns(cast_exprs)

    df = df.with_columns([
        pl.col('KEGG_ko').fill_null('').str.split(',').alias('_ko_tokens')
    ])
    df = df.explode('_ko_tokens')
    df = df.with_columns([
        pl.col('_ko_tokens').str.extract(r'(K\d{5})').alias('ko_id')
    ])
    df = df.filter(pl.col('ko_id').is_not_null())

    if df.is_empty():
        return "no_kos"

    agg_exprs = [pl.len().alias('count')]
    if 'score' in df.columns:
        agg_exprs.append(pl.col('score').mean().alias('mean_score'))
    if 'evalue' in df.columns:
        agg_exprs.append(pl.col('evalue').min().alias('min_evalue'))
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

    # Load contig map first (so we can filter metadata to mappable MAGs)
    print("Loading contig map to determine MAG coverage...")
    contig_map_raw = pd.read_parquet(DATA_DIR / 'mag_contig_map.parquet', columns=['mag_id'])
    contig_map_mag_ids = set(contig_map_raw['mag_id'])
    print(f"Contig map covers {len(contig_map_mag_ids):,} unique MAGs")
    del contig_map_raw

    if args.merge_only:
        merge_parquets()
        return

    from spire_api import SPIREClient

    mag_meta_df = get_all_mag_metadata(contig_map_mag_ids)

    standard_mask = mag_meta_df['sample_id'].str.match(_STANDARD)
    n_dropped = (~standard_mask).sum()
    if n_dropped:
        print(f"Dropping {n_dropped:,} MAGs with non-standard sample IDs")
    mag_meta_df = mag_meta_df[standard_mask].copy()

    all_mag_ids = set(mag_meta_df['mag_id'])
    contig_to_mag_pl, contig_set = load_contig_map(all_mag_ids)

    sample_groups = mag_meta_df.groupby('sample_id')['mag_id'].apply(list).to_dict()
    # Skip soil samples already processed by process_eggnog_to_parquet.py
    soil_done = {p.stem for p in (DATA_DIR / 'ko_annotations').glob('*.parquet')}
    done_ids = {p.stem for p in WORK_DIR.glob('*.parquet')} | soil_done
    to_process = {sid: mids for sid, mids in sample_groups.items()
                  if sid not in done_ids}

    print(f"Total samples in scope:   {len(sample_groups):,}")
    print(f"Already processed (soil): {len(soil_done):,}")
    print(f"Already processed (here): {len({p.stem for p in WORK_DIR.glob('*.parquet')}):,}")
    print(f"To process:               {len(to_process):,}")

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
                                  contig_to_mag_pl, contig_set, all_mag_ids)
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
