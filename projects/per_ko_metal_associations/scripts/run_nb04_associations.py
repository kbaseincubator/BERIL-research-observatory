"""Run latitude-adjusted KO-metal associations for NB04 (both MGnify and SPIRE).

Standalone script; immune to Jupyter kernel crashes. Has auto-restart on Pool
failure — safe to kill and re-run at any time. Checkpoint every 20 KOs.

Usage:
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      python scripts/run_nb04_associations.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / 'scripts'))
from association_utils import run_all_ko_associations

DATA_DIR = PROJECT_DIR / 'data'

METAL_COLS     = ['PF1_Cu', 'PF1_Pb', 'PF1_Cr', 'PF1_As', 'PF1_Cd', 'PF1_Hg']
COVARIATE_COLS = ['latitude']
N_WORKERS      = 12
MAX_RETRIES    = 20


def run_dataset(label: str, parquet_path: Path, out_path: Path, ckpt_path: Path) -> None:
    if out_path.exists():
        print(f"{label}: output already exists ({out_path.name}), skipping.")
        return

    print(f"\n{'='*60}")
    print(f"{label}: loading {parquet_path.name} ...")
    mat = pd.read_parquet(parquet_path)
    print(f"  {mat['genome_id'].nunique():,} MAGs × {mat['ko_id'].nunique():,} KOs")

    metals = [m for m in METAL_COLS if m in mat.columns and mat[m].notna().sum() >= 20]
    print(f"  Metals: {metals}  Covariate: {COVARIATE_COLS}  Workers: {N_WORKERS}")

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            print(f"  [auto-restart attempt {attempt}/{MAX_RETRIES}]", flush=True)
            time.sleep(2)
        try:
            results = run_all_ko_associations(
                ko_matrix=mat,
                metal_cols=metals,
                n_workers=N_WORKERS,
                verbose_interval=200,
                checkpoint_path=ckpt_path,
                checkpoint_interval=20,
                covariate_cols=COVARIATE_COLS,
            )
            results.to_csv(out_path, index=False)
            n_sig = (results['q_value'] < 0.05).sum()
            print(f"\n{label} complete: {len(results):,} rows, {n_sig} FDR-sig (q<0.05)")
            print(f"Saved: {out_path}")
            return
        except Exception as exc:
            print(f"  [Pool crash: {exc}; checkpoint preserved, restarting]", flush=True)

    raise RuntimeError(f"{label}: exceeded {MAX_RETRIES} retries")


if __name__ == '__main__':
    run_dataset(
        label='MGnify',
        parquet_path=DATA_DIR / 'mgnify_all_ko_matrix.parquet',
        out_path=DATA_DIR / 'mgnify_adj_ko_associations.csv',
        ckpt_path=DATA_DIR / 'ckpt_mgnify_adj_ko_associations.csv',
    )
    run_dataset(
        label='SPIRE',
        parquet_path=DATA_DIR / 'spire_all_ko_matrix.parquet',
        out_path=DATA_DIR / 'spire_adj_ko_associations.csv',
        ckpt_path=DATA_DIR / 'ckpt_spire_adj_ko_associations.csv',
    )
    print("\nAll done.")
