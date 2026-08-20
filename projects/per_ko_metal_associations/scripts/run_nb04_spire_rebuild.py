"""Re-run latitude-adjusted SPIRE associations after matrix rebuild (NB04 follow-on).

Runs two models:
  1. Baseline: KO_present ~ PF1_metal + log_genome_size + latitude + C(phylum/genus)
     → spire_adj_ko_associations.csv   (replaces stale file from 2,905-MAG matrix)
  2. SoilGrids-adjusted: adds sg_pH covariate (WP6 resolution)
     → spire_sg_adj_ko_associations.csv  (sensitivity check)

Usage:
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      python scripts/run_nb04_spire_rebuild.py
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

METAL_COLS = ['PF1_Cu', 'PF1_Pb', 'PF1_Cr', 'PF1_As', 'PF1_Cd', 'PF1_Hg']
N_WORKERS  = 12
MAX_RETRIES = 20


def run_model(label: str, mat: pd.DataFrame, covariate_cols: list,
              out_path: Path, ckpt_path: Path) -> None:
    if out_path.exists():
        print(f"{label}: output already exists ({out_path.name}), skipping.")
        return

    metals = [m for m in METAL_COLS if m in mat.columns and mat[m].notna().sum() >= 20]
    print(f"\n{'='*60}")
    print(f"{label}: {mat['genome_id'].nunique():,} MAGs × {mat['ko_id'].nunique():,} KOs")
    print(f"  Metals: {metals}")
    print(f"  Covariates: {covariate_cols}  Workers: {N_WORKERS}")

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
                covariate_cols=covariate_cols,
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
    print("Loading SPIRE matrix ...")
    mat = pd.read_parquet(DATA_DIR / 'spire_all_ko_matrix.parquet')
    print(f"  {mat['genome_id'].nunique():,} MAGs × {mat['ko_id'].nunique():,} KOs")
    sg_cov = 100 * mat['sg_pH'].notna().sum() / len(mat)
    print(f"  sg_pH non-null: {mat['sg_pH'].notna().sum():,} / {len(mat):,} ({sg_cov:.1f}%)")

    # Model 1: baseline (latitude-only, same as original NB04)
    run_model(
        label='SPIRE-baseline (latitude)',
        mat=mat,
        covariate_cols=['latitude'],
        out_path=DATA_DIR / 'spire_adj_ko_associations.csv',
        ckpt_path=DATA_DIR / 'ckpt_spire_adj_ko_associations.csv',
    )

    # Model 2: SoilGrids-adjusted (WP6 sensitivity check)
    run_model(
        label='SPIRE-SoilGrids (latitude + sg_pH)',
        mat=mat,
        covariate_cols=['latitude', 'sg_pH'],
        out_path=DATA_DIR / 'spire_sg_adj_ko_associations.csv',
        ckpt_path=DATA_DIR / 'ckpt_spire_sg_adj_ko_associations.csv',
    )

    print("\nAll done.")
