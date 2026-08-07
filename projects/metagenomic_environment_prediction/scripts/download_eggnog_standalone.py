"""Standalone eggnog downloader — runs outside Jupyter.

Queries Spark for soil sample IDs, filters to uncached standard IDs,
then downloads eggnog files with progress reporting.

Usage:
    python scripts/download_eggnog_standalone.py
"""

import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add scripts dir to path
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parents[1] / 'scripts'))

DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = DATA_DIR / 'spire_cache'
MAX_WORKERS = 20
_STANDARD = re.compile(r'^(SAMN|SAMEA|SRS|ERS|DRS)\d+$')


def get_soil_sample_ids():
    """Query Spark for soil-filtered sample IDs."""
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
    except ImportError:
        from get_spark_session import get_spark_session

    spark = get_spark_session()
    print("Spark connected:", spark.version)

    df = spark.sql("""
        SELECT DISTINCT mc.sample_id
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

    sample_ids = set(df['sample_id'].tolist())
    print(f"Soil sample IDs from Spark: {len(sample_ids):,}")
    return sample_ids


def main():
    from spire_api import SPIREClient

    # Get soil sample IDs
    soil_ids = get_soil_sample_ids()

    # Filter to standard IDs only
    standard_ids = {s for s in soil_ids if _STANDARD.match(s)}
    print(f"Standard IDs (SAMN/SAMEA/SRS/ERS/DRS): {len(standard_ids):,}")

    # Find uncached
    cached = {p.stem for p in (CACHE_DIR / 'eggnog').glob('*.gz')}
    to_download = sorted(standard_ids - cached)
    print(f"Already cached: {len(cached & standard_ids):,}")
    print(f"To download:    {len(to_download):,}")

    if not to_download:
        print("Nothing to download.")
        return

    client = SPIREClient(cache_dir=CACHE_DIR)

    done = [0]
    failed = [0]
    start = time.time()

    def _download(sample_id):
        result = client.download_eggnog_for_sample(sample_id)
        if result is None:
            failed[0] += 1
        done[0] += 1
        n = done[0]
        if n % 10 == 0 or n == len(to_download):
            elapsed = time.time() - start
            rate = n / elapsed * 60
            print(f"  {n:,}/{len(to_download):,} done  "
                  f"({failed[0]} failed)  "
                  f"{rate:.1f}/min  "
                  f"cache={len(list((CACHE_DIR/'eggnog').glob('*.gz'))):,}",
                  flush=True)

    print(f"\nStarting downloads with {MAX_WORKERS} workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_download, sid) for sid in to_download]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    elapsed = time.time() - start
    print(f"\nDone. {done[0]} attempted, {failed[0]} failed, "
          f"{elapsed/60:.1f} min elapsed.")
    print(f"Cache now: {len(list((CACHE_DIR/'eggnog').glob('*.gz'))):,} files")


if __name__ == '__main__':
    main()
