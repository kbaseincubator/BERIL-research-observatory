"""Run soil-restricted per-KO associations for MGnify (biome_name == Soil | Rhizosphere).

Filters the 8,585-MAG dataset to 6,615 soil/rhizosphere MAGs using biome_name
from microbeatlas_metal_ecology/data/final_mags_geospatial_traits.csv.
Uses the same logistic model as H1 (no latitude covariate — parallel to H1 unadjusted).
Checkpoint every 20 KOs.

Usage:
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      python scripts/run_soil_restricted_associations.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT   = PROJECT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_DIR / 'scripts'))
from association_utils import run_all_ko_associations

DATA_DIR  = PROJECT_DIR / 'data'
GEO_CSV   = REPO_ROOT / 'projects/microbeatlas_metal_ecology/data/final_mags_geospatial_traits.csv'

METAL_COLS = ['PF1_Cu', 'PF1_Pb', 'PF1_Cr', 'PF1_As', 'PF1_Cd', 'PF1_Hg']
N_WORKERS  = 24
MAX_RETRIES = 20

OUT_PATH  = DATA_DIR / 'mgnify_soil_ko_associations.csv'
CKPT_PATH = DATA_DIR / 'ckpt_mgnify_soil_ko_associations.csv'

if OUT_PATH.exists():
    print(f"Output already exists: {OUT_PATH.name}")
    sys.exit(0)

# --- Load and filter to soil/rhizo MAGs ---
print("Loading biome data ...")
geo = pd.read_csv(GEO_CSV, usecols=['genome_id', 'biome_name'])
soil_ids = set(geo[geo['biome_name'].str.lower().str.contains('soil|rhizo', na=False)]['genome_id'])
print(f"Soil/rhizo MAG IDs: {len(soil_ids)}")

print("Loading MGnify KO matrix ...")
mat = pd.read_parquet(DATA_DIR / 'mgnify_all_ko_matrix.parquet')
n_before = mat['genome_id'].nunique()
mat_soil = mat[mat['genome_id'].isin(soil_ids)].copy()
n_after = mat_soil['genome_id'].nunique()
print(f"MAGs: {n_before} → {n_after} after soil filter")
print(f"KOs retained: {mat_soil['ko_id'].nunique()}")

metals = [m for m in METAL_COLS if m in mat_soil.columns and mat_soil[m].notna().sum() >= 20]
print(f"Metals: {metals}  Workers: {N_WORKERS}")

for attempt in range(1, MAX_RETRIES + 1):
    if attempt > 1:
        print(f"[auto-restart attempt {attempt}/{MAX_RETRIES}]", flush=True)
        time.sleep(2)
    try:
        results = run_all_ko_associations(
            ko_matrix=mat_soil,
            metal_cols=metals,
            n_workers=N_WORKERS,
            verbose_interval=200,
            checkpoint_path=CKPT_PATH,
            checkpoint_interval=20,
        )
        results.to_csv(OUT_PATH, index=False)
        n_sig = (results['q_value'] < 0.05).sum()
        print(f"\nSoil-restricted MGnify complete: {len(results):,} rows, {n_sig} FDR-sig (q<0.05)")
        print(f"Saved: {OUT_PATH}")

        # --- Compute cross-dataset ρ with SPIRE ---
        spire = pd.read_csv(DATA_DIR / 'spire_all_ko_associations.csv')
        merge = (results[results['beta'].notna()][['ko_id','metal','beta']]
                 .rename(columns={'beta':'beta_mg_soil'})
                 .merge(spire[spire['beta'].notna()][['ko_id','metal','beta']]
                        .rename(columns={'beta':'beta_spire'}),
                        on=['ko_id','metal']))
        from scipy.stats import spearmanr
        rho, p_rho = spearmanr(merge['beta_mg_soil'], merge['beta_spire'])
        print(f"\nSoil-restricted cross-dataset ρ: {rho:.4f} (p={p_rho:.4f}, n={len(merge)})")
        print(f"Original ρ (all biomes): 0.059 (p=0.29, n=324)")
        merge.to_csv(DATA_DIR / 'soil_cross_dataset_comparison.csv', index=False)
        print(f"Saved: soil_cross_dataset_comparison.csv ({len(merge)} convergent pairs)")
        break
    except Exception as exc:
        print(f"[Pool crash: {exc}; checkpoint preserved, restarting]", flush=True)
else:
    raise RuntimeError(f"Exceeded {MAX_RETRIES} retries")
