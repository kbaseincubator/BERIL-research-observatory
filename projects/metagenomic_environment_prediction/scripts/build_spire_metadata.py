"""Fetch SPIRE API metadata not available in Spark and write reference parquets.

Produces two files scoped to the soil-filtered sample set:

  data/spire_sample_metadata.parquet
      sample_id    str   biosample accession
      study_id     str   SPIRE study identifier
      microntology str   pipe-separated ENVO/ontology terms
                         (richer than refdata.spire.sample_microntology)

  data/spire_mag_qc.parquet
      mag_id        str    SPIRE MAG identifier
      sample_id     str
      n50           int    assembly N50 in bp
      num_contigs   int    number of contigs
      gene_count    int    predicted gene count
      gunc_css      float  GUNC CSS contamination score
      gunc_rrs      float  GUNC RRS contamination score
      spire_cluster str    SPIRE taxonomic cluster (nullable)

Usage:
    python scripts/build_spire_metadata.py [--max-samples N]
"""

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parents[1] / 'scripts'))

DATA_DIR = PROJECT_DIR / 'data'

BASE = "https://spire.embl.de/spire/api"
ENVIRONMENT_URL = BASE + "/environment"
STUDY_URL       = BASE + "/study/{study_id}"
SAMPLE_URL      = BASE + "/sample/{sample_id}"

MAX_WORKERS = 20
TIMEOUT = (10, 30)
_STANDARD = re.compile(r'^(SAMN|SAMEA|SRS|ERS|DRS)\d+$')


def get_soil_sample_ids():
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
    except ImportError:
        from get_spark_session import get_spark_session

    spark = get_spark_session()
    print(f"Spark connected: {spark.version}")

    df = spark.sql("""
        SELECT DISTINCT mc.sample_id, mc.mag_id
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

    standard = df[df['sample_id'].str.match(_STANDARD)]
    print(f"Soil samples: {standard['sample_id'].nunique():,}  "
          f"MAGs: {len(standard):,}")
    return standard


def fetch_environment_map(soil_sample_ids: set) -> dict:
    """Fetch /environment to map sample_id → study_id for our soil samples."""
    print("Fetching /environment map...")
    try:
        resp = requests.get(ENVIRONMENT_URL, timeout=(10, 60))
        resp.raise_for_status()
        env_map = resp.json()
    except Exception as e:
        print(f"  ERROR fetching /environment: {e}")
        return {}

    # env_map keys are "STUDY_SAMPLEID" or just sample IDs — filter to ours
    result = {}
    for key, val in env_map.items():
        sid = key.split('-', 1)[-1] if '-' in key else key
        if sid in soil_sample_ids:
            result[sid] = val.get('study_id', '')
    print(f"  Matched {len(result):,} of {len(soil_sample_ids):,} soil samples to studies")
    return result


def fetch_study_microntology(study_ids: set) -> dict:
    """Fetch /study/{study_id} for each unique study; return sample→microntology map."""
    print(f"Fetching microntology for {len(study_ids):,} studies...")
    sample_to_micro = {}

    def _fetch_study(study_id):
        try:
            resp = requests.get(STUDY_URL.format(study_id=study_id), timeout=TIMEOUT)
            if resp.status_code == 200:
                return study_id, resp.json()
        except Exception:
            pass
        return study_id, {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_fetch_study, sid): sid for sid in study_ids}
        for i, f in enumerate(as_completed(futures), 1):
            study_id, data = f.result()
            for sample_key, sample_data in data.items():
                micro = sample_data.get('microntology', [])
                sid = sample_key.split('-', 1)[-1] if '-' in sample_key else sample_key
                sample_to_micro[sid] = '|'.join(sorted(micro)) if micro else ''
            if i % 10 == 0 or i == len(study_ids):
                print(f"  {i}/{len(study_ids)} studies done", flush=True)

    return sample_to_micro


def fetch_mag_qc(sample_groups: dict) -> list:
    """Fetch /sample/{sample_id} for each sample; collect per-MAG QC metrics."""
    total = len(sample_groups)
    print(f"Fetching per-MAG QC for {total:,} samples...")

    records = []
    done = [0]

    def _fetch_sample(sid):
        try:
            resp = requests.get(SAMPLE_URL.format(sample_id=sid), timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    def _worker(sid_mids):
        sid, mag_ids = sid_mids
        mag_id_set = set(mag_ids)
        data = _fetch_sample(sid)
        rows = []
        # Response is a dict keyed by mag_id → {n50, gunc_css, ...}
        mag_data = data if isinstance(data, dict) else {}
        for mag_id, entry in mag_data.items():
            if mag_id not in mag_id_set:
                continue
            rows.append({
                'mag_id':        mag_id,
                'sample_id':     sid,
                'n50':           entry.get('n50'),
                'num_contigs':   entry.get('num_contigs'),
                'gene_count':    entry.get('gene_count'),
                'gunc_css':      entry.get('gunc_css'),
                'gunc_rrs':      entry.get('gunc_rrs'),
                'spire_cluster': entry.get('spire_cluster'),
            })
        done[0] += 1
        if done[0] % 50 == 0 or done[0] == total:
            print(f"  {done[0]:,}/{total:,} samples done", flush=True)
        return rows

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_worker, item) for item in sample_groups.items()]
        for f in as_completed(futures):
            try:
                rows = f.result()
                if rows:
                    records.extend(rows)
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-samples', type=int, default=None)
    args = parser.parse_args()

    mag_df = get_soil_sample_ids()

    if args.max_samples:
        sample_ids = list(mag_df['sample_id'].unique())[:args.max_samples]
        mag_df = mag_df[mag_df['sample_id'].isin(sample_ids)]
        print(f"Test mode: {len(sample_ids)} samples")

    soil_sample_ids = set(mag_df['sample_id'].unique())
    sample_groups = mag_df.groupby('sample_id')['mag_id'].apply(list).to_dict()

    # ------------------------------------------------------------------ #
    # 1. sample metadata: study_id + microntology
    # ------------------------------------------------------------------ #
    study_map = fetch_environment_map(soil_sample_ids)

    unique_studies = set(study_map.values()) - {''}
    micro_map = fetch_study_microntology(unique_studies) if unique_studies else {}

    sample_records = []
    for sid in soil_sample_ids:
        sample_records.append({
            'sample_id':   sid,
            'study_id':    study_map.get(sid, ''),
            'microntology': micro_map.get(sid, ''),
        })

    sample_df = pd.DataFrame(sample_records)
    sample_out = DATA_DIR / 'spire_sample_metadata.parquet'
    sample_df.to_parquet(sample_out, index=False)
    print(f"\nSaved: {sample_out}  ({len(sample_df):,} samples)")
    print(f"  study_id non-empty:    {(sample_df['study_id'] != '').sum():,}")
    print(f"  microntology non-empty: {(sample_df['microntology'] != '').sum():,}")

    # ------------------------------------------------------------------ #
    # 2. per-MAG QC: GUNC scores, n50, num_contigs, gene_count, cluster
    # ------------------------------------------------------------------ #
    qc_records = fetch_mag_qc(sample_groups)
    qc_df = pd.DataFrame(qc_records) if qc_records else pd.DataFrame()

    qc_out = DATA_DIR / 'spire_mag_qc.parquet'
    qc_df.to_parquet(qc_out, index=False)
    print(f"\nSaved: {qc_out}  ({len(qc_df):,} MAG rows)")
    if not qc_df.empty:
        for col in ['n50', 'num_contigs', 'gene_count', 'gunc_css', 'gunc_rrs']:
            if col in qc_df.columns:
                nn = qc_df[col].notna().sum()
                print(f"  {col}: {nn:,} non-null")


if __name__ == '__main__':
    main()
