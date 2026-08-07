"""Standalone eggnog KO-count pipeline — parse-on-the-fly variant.

Downloads eggnog per sample, counts KOs per MAG immediately, writes a tiny
per-sample parquet to data/ko_counts/. Raw gzip is never saved to disk.
Resumable: skips samples whose parquet already exists.

Disk usage: ~few KB per sample (vs ~36 MB/sample for raw gzip).

Usage:
    python scripts/process_eggnog_standalone.py
    python scripts/process_eggnog_standalone.py --max-samples 5   # test run
"""

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parents[1] / 'scripts'))

DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = DATA_DIR / 'spire_cache'
KO_COUNTS_DIR = DATA_DIR / 'ko_counts'
KO_COUNTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_WORKERS = 20
_STANDARD = re.compile(r'^(SAMN|SAMEA|SRS|ERS|DRS)\d+$')


def get_mag_metadata():
    """Query Spark for soil MAG metadata."""
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
            gm.genus,
            gm.completeness,
            gm.contamination
        FROM refdata.spire.mag_coordinates mc
        JOIN refdata.spire.genome_metadata gm ON mc.mag_id = gm.genome_id
        WHERE mc.latitude IS NOT NULL
          AND mc.longitude IS NOT NULL
          AND gm.domain = 'Bacteria'
          AND EXISTS (
            SELECT 1 FROM refdata.spire.sample_microntology sm
            WHERE sm.sample_id = mc.sample_id
              AND (sm.environment_term LIKE '%soil%'
                OR sm.environment_term LIKE '%rhizosphere%')
          )
          AND NOT EXISTS (
            SELECT 1 FROM refdata.spire.sample_microntology sm
            WHERE sm.sample_id = mc.sample_id
              AND (sm.environment_term LIKE '%host%'
                OR sm.environment_term LIKE '%gut%'
                OR sm.environment_term LIKE '%clinical%')
          )
    """).toPandas()

    print(f"Soil bacterial MAGs: {len(df):,}  Samples: {df['sample_id'].nunique():,}")
    return df


def process_sample(sample_id, mag_ids, client, primary_kos, subcat_kos,
                   parse_eggnog, normalise_ko_ids):
    """Download eggnog for one sample, count KOs per MAG, save parquet.

    Returns (n_mags_written, status_str).
    """
    out_path = KO_COUNTS_DIR / f"{sample_id}.parquet"
    if out_path.exists():
        return (0, "cached")

    data = client.fetch_eggnog_bytes(sample_id)
    if data is None:
        return (0, "failed")

    try:
        eggnog_df = parse_eggnog(data)
    except Exception as exc:
        return (0, f"parse_error:{exc}")

    if eggnog_df.empty or "query" not in eggnog_df.columns:
        return (0, "empty")

    eggnog_df = eggnog_df.copy()
    eggnog_df["contig"] = eggnog_df["query"].str.rsplit("_", n=1).str[0]

    records = []
    for mag_id in mag_ids:
        contigs = client.get_mag_contig_set(mag_id)
        if contigs is None:
            continue
        mask = eggnog_df["contig"].isin(contigs)
        ko_series = (eggnog_df.loc[mask, "KEGG_ko"] if mask.any()
                     else pd.Series(dtype=str))
        ko_set: set = set()
        for raw in ko_series.dropna():
            ko_set.update(normalise_ko_ids(str(raw)))
        row: dict = {"sample_id": sample_id, "mag_id": mag_id,
                     "n_ko_primary": len(ko_set & primary_kos)}
        for cat, cat_kos in subcat_kos.items():
            col = "n_ko_" + cat.lower().replace(" ", "_").replace("/", "_")
            row[col] = len(ko_set & cat_kos)
        records.append(row)

    if records:
        pd.DataFrame(records).to_parquet(out_path, index=False)
    return (len(records), "ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Process at most N samples (for testing)")
    args = parser.parse_args()

    from spire_api import SPIREClient, _parse_eggnog_gzip
    from mag_utils import get_primary_ko_set, get_subcategory_ko_sets, normalise_ko_ids

    mag_meta_df = get_mag_metadata()

    # Filter to standard sample IDs (non-standard stall the eggnog endpoint)
    standard_mask = mag_meta_df['sample_id'].str.match(_STANDARD)
    n_dropped = (~standard_mask).sum()
    if n_dropped:
        print(f"Dropping {n_dropped:,} MAGs with non-standard sample IDs")
    mag_meta_df = mag_meta_df[standard_mask].copy()

    sample_groups = mag_meta_df.groupby('sample_id')['mag_id'].apply(list).to_dict()

    # Resume: skip samples already processed
    done_ids = {p.stem for p in KO_COUNTS_DIR.glob('*.parquet')}
    to_process = {sid: mids for sid, mids in sample_groups.items()
                  if sid not in done_ids}

    print(f"Total samples:     {len(sample_groups):,}")
    print(f"Already processed: {len(done_ids):,}")
    print(f"To process:        {len(to_process):,}")

    if not to_process:
        print("All samples processed. Merge parquets with NB01 CACHED_ONLY mode.")
        return

    if args.max_samples:
        to_process = dict(list(to_process.items())[:args.max_samples])
        print(f"Capped to {args.max_samples} samples (test mode)")

    primary_kos = get_primary_ko_set()
    subcat_kos = get_subcategory_ko_sets()
    client = SPIREClient(cache_dir=CACHE_DIR)

    total = len(to_process)
    done_count = [0]
    failed_count = [0]
    start = time.time()

    def _process(sid_mids):
        sid, mids = sid_mids
        _, status = process_sample(sid, mids, client, primary_kos, subcat_kos,
                                   _parse_eggnog_gzip, normalise_ko_ids)
        if status == "failed" or status.startswith("parse_error"):
            failed_count[0] += 1
        done_count[0] += 1
        n = done_count[0]
        if n % 10 == 0 or n == total:
            elapsed = time.time() - start
            rate = n / elapsed * 60 if elapsed > 0 else 0
            n_parquets = len(list(KO_COUNTS_DIR.glob('*.parquet')))
            print(f"  {n:,}/{total:,} done  ({failed_count[0]} failed)  "
                  f"{rate:.1f}/min  parquets={n_parquets:,}", flush=True)

    print(f"\nStarting with {MAX_WORKERS} workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_process, item) for item in to_process.items()]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    elapsed = time.time() - start
    n_parquets = len(list(KO_COUNTS_DIR.glob('*.parquet')))
    print(f"\nDone. {done_count[0]}/{total} attempted, {failed_count[0]} failed, "
          f"{elapsed/60:.1f} min elapsed.")
    print(f"Parquet count: {n_parquets:,}")


if __name__ == '__main__':
    main()
