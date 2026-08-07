"""Build mag_contig_map.parquet from cached SPIRE MAG contig files.

Reads all .txt files (contig names) and .stats sidecar files (length, gc)
from data/spire_cache/mag_contigs/ and merges into a single parquet.

Schema:
    mag_id   str    e.g. "spire_mag_01050297"
    contig   str    e.g. "k141_10400"
    length   int    contig length in bp (null if .stats not yet cached)
    gc       float  GC fraction 0–1 (null if .stats not yet cached)

Usage:
    python scripts/build_contig_map.py
"""

import sys
import time
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
CONTIG_DIR = DATA_DIR / 'spire_cache' / 'mag_contigs'


def main():
    txt_files = sorted(CONTIG_DIR.glob('*.txt'))
    print(f"Found {len(txt_files):,} cached MAG contig files")

    start = time.time()
    records = []
    stats_count = 0

    for i, txt_path in enumerate(txt_files):
        mag_id = txt_path.stem
        contigs = [l for l in txt_path.read_text().splitlines() if l]

        stats_path = txt_path.with_suffix('.stats')
        if stats_path.exists():
            try:
                stats_df = pd.read_csv(stats_path, sep='\t', index_col='contig')
                stats_count += 1
                for contig in contigs:
                    row = stats_df.loc[contig] if contig in stats_df.index else None
                    records.append({
                        'mag_id': mag_id,
                        'contig': contig,
                        'length': int(row['length']) if row is not None else None,
                        'gc': float(row['gc']) if row is not None else None,
                    })
            except Exception:
                for contig in contigs:
                    records.append({'mag_id': mag_id, 'contig': contig,
                                    'length': None, 'gc': None})
        else:
            for contig in contigs:
                records.append({'mag_id': mag_id, 'contig': contig,
                                'length': None, 'gc': None})

        if (i + 1) % 5000 == 0 or (i + 1) == len(txt_files):
            elapsed = time.time() - start
            rate = (i + 1) / elapsed * 60
            print(f"  {i+1:,}/{len(txt_files):,} MAGs  "
                  f"{len(records):,} contigs  "
                  f"{rate:.0f} MAGs/min", flush=True)

    print(f"\nBuilding DataFrame from {len(records):,} rows...")
    df = pd.DataFrame(records)

    # Downcast int/float columns to save space
    df['length'] = pd.array(df['length'], dtype=pd.Int32Dtype())
    df['gc'] = pd.to_numeric(df['gc'], errors='coerce').astype('float32')

    out_path = DATA_DIR / 'mag_contig_map.parquet'
    df.to_parquet(out_path, index=False)
    size_mb = out_path.stat().st_size / 1e6

    elapsed = time.time() - start
    print(f"\nSaved: {out_path}")
    print(f"  {len(df):,} rows  |  "
          f"{df['mag_id'].nunique():,} MAGs  |  "
          f"{stats_count:,} MAGs with length/GC stats  |  "
          f"{size_mb:.1f} MB  |  "
          f"{elapsed/60:.1f} min elapsed")


if __name__ == '__main__':
    main()
