#!/usr/bin/env python3
"""
usa_shared_covariates_model.py

Runs the USA CWM model using only the globally available covariate subset
matching EUR/AUS v2, enabling direct cross-regional comparison.

Excluded (USA-specific): drainage_class, usgs_mine_distance, epa_tri_releases,
  epa_tri_organic_releases, slope_pct, awc_0_25cm, hydrologic_group, flood_freq,
  hydric_pct, ponding_pct, land_cap_class

Outputs:
  data/usa_cwm/lm_input_USA_shared_{metal}.csv
  data/usa_cwm/lm_out_USA_shared_{metal}.csv
  data/usa_cwm/gam_results_usa_shared.csv  (pooled BH-FDR across 6 metals)
"""
import os, subprocess
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.stats.multitest import multipletests

REPO    = Path('/home/hmacgregor/BERIL-research-observatory')
DATA    = REPO / 'projects/microbeatlas_metal_ecology/data'
USA_DIR = DATA / 'usa_cwm'
RSCRIPT = '/home/hmacgregor/r_env/bin/Rscript'
SCRIPT  = REPO / 'projects/microbeatlas_metal_ecology/scripts/lm_ns_full_model.R'
MC_CORES = 4

METALS = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']

# Use a subdirectory so R doesn't find organic_by_sample.csv (which is in usa_cwm/)
# and accidentally add epa_tri_organic_releases to the covariate set.
SUBDIR = USA_DIR / 'shared_model'
SUBDIR.mkdir(exist_ok=True)

# Shared covariate columns (globally available, matching EUR/AUS v2)
SHARED_COLS = [
    'sample_id', 'lat', 'lon',
    'ph_ssurgo',                           # measured pH (GEMAS/NGSA equivalent)
    'clay_pct', 'organic_matter', 'cec',   # SSURGO / SoilGrids soil
    'bulk_density_0cm', 'sand_0cm', 'silt_0cm', 'nitrogen_0cm',  # SoilGrids
    'mat_c', 'map_mm', 'temp_seasonality', 'precip_seasonality',
    'temp_annual_range_c', 'elevation_m',  # WorldClim
    'lith_class',                          # GLiM (factor)
    'lc_forest_pct', 'lc_cultivated_pct', 'lc_urban_pct', 'lc_barren_pct',  # EarthEnv
    'shannon',
    # phylum columns — detected dynamically
]

print("Loading USA covariate matrix and CWM...")
cov_full = pd.read_csv(USA_DIR / 'covariate_matrix_634_v2.csv')
cwm_all  = pd.read_parquet(USA_DIR / 'cwm_all_ko_thinned_634.parquet')

# Add phylum columns to shared set
phylum_cols = [c for c in cov_full.columns if c.startswith('phylum_')]
shared_plus_phyla = SHARED_COLS + phylum_cols
# Keep only columns that exist in cov_full
shared_keep = [c for c in shared_plus_phyla if c in cov_full.columns]
print(f"  Shared covariates: {len(shared_keep) - 3} (excl. sample_id/lat/lon)")
print(f"  USA v3 total columns: {cov_full.shape[1]}")
print(f"  Excluded: {set(cov_full.columns) - set(shared_keep) - {'As','Cd','Cr','Cu','Hg','Pb'}}")

cov = cov_full[shared_keep + METALS].copy()
print(f"  CWM: {cwm_all.shape[0]:,} rows × {cwm_all['ko_id'].nunique():,} KOs × {cwm_all['sample_id'].nunique()} samples")

env = os.environ.copy()
env['OMP_NUM_THREADS'] = '1'
env['MC_CORES'] = str(MC_CORES)

results = []

for metal in METALS:
    out_csv = SUBDIR / f'lm_out_USA_shared_{metal}.csv'
    if out_csv.exists():
        print(f"\n[{metal}] Loading existing results...")
        df = pd.read_csv(out_csv)
        df['metal'] = metal
        results.append(df)
        continue

    inp_csv = SUBDIR / f'lm_input_USA_shared_{metal}.csv'

    if inp_csv.exists():
        print(f"\n[{metal}] lm_input already exists — skipping CSV write, running R...")
        n_samples = cov[metal].notna().sum()
    else:
        print(f"\n[{metal}] Building lm_input...")
        metal_cov = cov[['sample_id','lat','lon'] + [c for c in shared_keep if c not in ['sample_id','lat','lon']] + [metal]].copy()
        metal_cov = metal_cov.rename(columns={metal: 'metal_raw'})
        metal_cov = metal_cov.dropna(subset=['metal_raw'])
        metal_cov['log10_metal'] = np.log10(metal_cov['metal_raw'].clip(lower=1e-6))
        metal_cov['metal'] = metal
        lm_in = cwm_all.merge(metal_cov.drop(columns=['metal_raw']), on='sample_id', how='inner')
        lm_in.to_csv(inp_csv, index=False)
        n_samples = metal_cov['sample_id'].nunique()
        n_kos     = lm_in['ko_id'].nunique()
        print(f"  n_samples={n_samples}, n_KOs={n_kos}, rows={len(lm_in):,}")

    print(f"  Running R model (MC_CORES={MC_CORES})...")
    # R script expects positional args: <input_csv> <metal> <out_csv>
    # MC_CORES and other settings are read from environment variables
    cmd = [RSCRIPT, str(SCRIPT), str(inp_csv), metal, str(out_csv)]
    t0 = __import__('time').time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed = __import__('time').time() - t0
    if proc.returncode != 0:
        print(f"  R FAILED ({elapsed:.0f}s):\n{proc.stderr[-1000:]}")
        continue
    print(f"  Done in {elapsed:.0f}s.")

    df = pd.read_csv(out_csv)
    df['metal'] = metal
    results.append(df)
    print(f"  {len(df)} KOs; {df['p_metal_full'].notna().sum()} valid")

# Pool BH-FDR across all 6 metals
print("\nPooling BH-FDR across 6 metals...")
all_results = pd.concat(results, ignore_index=True)
mask = all_results['p_metal_full'].notna()
qs = np.full(len(all_results), np.nan)
_, q, _, _ = multipletests(all_results.loc[mask, 'p_metal_full'], method='fdr_bh')
qs[mask] = q
all_results['q_BH_pooled'] = qs

out_all = SUBDIR / 'gam_results_usa_shared.csv'
all_results.to_csv(out_all, index=False)

sig = all_results[all_results['q_BH_pooled'] < 0.05]
print(f"\nTotal rows: {len(all_results):,}")
print(f"Valid tests: {mask.sum():,}")
print(f"FDR<0.05: {len(sig):,}")
print(sig.groupby(['metal','beta_sign'])['ko_id'].count().rename('n_hits'))
print("\nTop 10 hits:")
print(sig.nsmallest(10,'q_BH_pooled')[['ko_id','metal','q_BH_pooled','delta_r2_full','beta_sign','n']].round(4).to_string(index=False))
