"""Genome-wide association runs for NB05: taxonomic and phylogenetic control.

Two models for MGnify (both with latitude covariate):
  Model A  — class-level fixed effects:   C(class) + latitude
  Model B  — continuous phylo-PC proxy:   phylo_pc1..20 + latitude  (no discrete taxonomy)

SPIRE: class taxonomy not available (phylum=None across all MAGs); run with genus
  control + latitude (same as NB04 but with latitude).  Output: spire_adj_ko_associations.csv
  already exists so SPIRE is skipped here unless that file is absent.

Runtime estimate (12 workers, 128-CPU machine):
  Model A: ~45 min  (class dummies ≈ C(phylum) cost × 2.5 due to more groups)
  Model B: ~40 min  (20 continuous covariates, no dummy expansion)

Usage:
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \\
      python scripts/run_nb05_associations.py >> /tmp/nb05_script.log 2>&1 &
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# BLAS thread safety on 128-CPU machine
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
GEO_PATH = (
    PROJECT_DIR.parent / 'microbeatlas_metal_ecology' / 'data'
    / 'final_mags_geospatial_traits.csv'
)

sys.path.insert(0, str(SCRIPT_DIR))
from association_utils import run_all_ko_associations

METAL_COLS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']
N_WORKERS = 12
MAX_RETRIES = 20
CHECKPOINT_INTERVAL = 20


def build_augmented_matrix(
    parquet_path: Path,
    geo_path: Path,
    phylo_pc_path: Path | None = None,
    extra_tax_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Load KO matrix and join extra taxonomy columns + phylo-PCs."""
    print('Loading KO matrix...', flush=True)
    ko = pd.read_parquet(parquet_path)
    print(f'  {ko["genome_id"].nunique():,} MAGs, {ko["ko_id"].nunique():,} KOs', flush=True)

    if extra_tax_cols:
        print(f'Joining taxonomy columns {extra_tax_cols} from geospatial traits...', flush=True)
        geo = pd.read_csv(geo_path, usecols=['genome_id'] + extra_tax_cols)
        before = ko['genome_id'].nunique()
        ko = ko.merge(geo, on='genome_id', how='left')
        after = ko['genome_id'].nunique()
        assert before == after, f'MAG count changed on join: {before} → {after}'
        # Rename Python reserved keywords that break patsy formula parsing
        rename = {col: f'tax_{col}' for col in extra_tax_cols if col in ('class', 'lambda', 'for', 'in')}
        if rename:
            ko = ko.rename(columns=rename)
            print(f'  Renamed reserved-keyword columns: {rename}', flush=True)
        for col in extra_tax_cols:
            actual = rename.get(col, col)
            nn = ko.drop_duplicates('genome_id')[actual].notna().sum()
            print(f'  {actual}: {nn:,}/{before:,} non-null', flush=True)

    if phylo_pc_path and phylo_pc_path.exists():
        print(f'Joining phylo-PCs from {phylo_pc_path.name}...', flush=True)
        pcs = pd.read_csv(phylo_pc_path, index_col='genome_id')
        pc_cols = pcs.columns.tolist()
        pcs = pcs.reset_index()
        ko = ko.merge(pcs, on='genome_id', how='left')
        nn = ko.drop_duplicates('genome_id')[pc_cols[0]].notna().sum()
        print(f'  phylo-PCs joined: {nn:,}/{ko["genome_id"].nunique():,} non-null', flush=True)

    return ko


def run_dataset(
    label: str,
    parquet_path: Path,
    out_path: Path,
    ckpt_path: Path,
    covariate_cols: list[str],
    tax_priority: tuple,
    geo_path: Path,
    phylo_pc_path: Path | None,
    extra_tax_cols: list[str] | None,
) -> None:
    if out_path.exists():
        print(f'[{label}] Output already exists, skipping: {out_path}', flush=True)
        return

    print(f'\n{"="*60}', flush=True)
    print(f'[{label}] Starting  {time.strftime("%H:%M:%S")}', flush=True)
    print(f'  tax_priority={tax_priority}', flush=True)
    print(f'  covariate_cols={covariate_cols}', flush=True)

    ko_matrix = build_augmented_matrix(
        parquet_path, geo_path, phylo_pc_path, extra_tax_cols
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f'[{label}] Attempt {attempt}  {time.strftime("%H:%M:%S")}', flush=True)
            results = run_all_ko_associations(
                ko_matrix=ko_matrix,
                metal_cols=METAL_COLS,
                n_workers=N_WORKERS,
                verbose_interval=200,
                checkpoint_path=ckpt_path,
                checkpoint_interval=CHECKPOINT_INTERVAL,
                covariate_cols=covariate_cols,
                tax_priority=tax_priority,
            )
            results.to_csv(out_path, index=False)
            n_sig = (results['q_value'] < 0.05).sum()
            print(
                f'[{label}] Done  {time.strftime("%H:%M:%S")}'
                f'  rows={len(results):,}  sig={n_sig:,}',
                flush=True,
            )
            return
        except Exception as exc:
            print(f'[{label}] ERROR attempt {attempt}: {exc}', flush=True)
            if attempt < MAX_RETRIES:
                print(f'[{label}] Restarting in 2 s...', flush=True)
                time.sleep(2)
            else:
                print(f'[{label}] All {MAX_RETRIES} attempts exhausted. Aborting.', flush=True)
                raise


def main() -> None:
    phylo_pc_path = DATA_DIR / 'mgnify_phylo_pcs.csv'

    if not phylo_pc_path.exists():
        print('Phylo-PC file not found; run compute_phylo_pcs.py first.', flush=True)
        sys.exit(1)

    pcs_df = pd.read_csv(phylo_pc_path, nrows=1)
    pc_cols = [c for c in pcs_df.columns if c.startswith('phylo_pc')]
    print(f'Found {len(pc_cols)} phylo-PC columns: {pc_cols[:3]}...', flush=True)

    mgnify_parquet = DATA_DIR / 'mgnify_all_ko_matrix.parquet'

    # Model A: class-level fixed effects + latitude
    # Note: 'class' is renamed to 'tax_class' by build_augmented_matrix (Python reserved word)
    run_dataset(
        label='MGnify_ClassLevel',
        parquet_path=mgnify_parquet,
        out_path=DATA_DIR / 'mgnify_class_ko_associations.csv',
        ckpt_path=DATA_DIR / 'ckpt_mgnify_class_ko_associations.csv',
        covariate_cols=['latitude'],
        tax_priority=('tax_class', 'phylum', 'genus'),
        geo_path=GEO_PATH,
        phylo_pc_path=None,
        extra_tax_cols=['class'],
    )

    # Model B: continuous phylo-PC proxy + latitude (no discrete taxonomy)
    run_dataset(
        label='MGnify_PhyloPC',
        parquet_path=mgnify_parquet,
        out_path=DATA_DIR / 'mgnify_phylopc_ko_associations.csv',
        ckpt_path=DATA_DIR / 'ckpt_mgnify_phylopc_ko_associations.csv',
        covariate_cols=['latitude'] + pc_cols,
        tax_priority=(),  # no discrete taxonomy; PCs carry the phylogenetic signal
        geo_path=GEO_PATH,
        phylo_pc_path=phylo_pc_path,
        extra_tax_cols=None,
    )

    print('\nAll NB05 runs complete.', flush=True)


if __name__ == '__main__':
    main()
