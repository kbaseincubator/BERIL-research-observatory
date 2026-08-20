#!/usr/bin/env python3
"""
extend_eur_aus_covariates.py

Extends EUR/AUS lm_input CSVs with globally available covariates:
  - SoilGrids: organic_matter (SOC), bulk_density_0cm, sand_0cm, silt_0cm, nitrogen_0cm, cec
  - WorldClim: mat_c, map_mm, temp_seasonality, precip_seasonality, temp_annual_range_c, elevation_m
  - GLiM: lith_class

Outputs:
  lm_input_EUR_v2_*.csv  -- extended EUR inputs for each metal
  lm_input_AUS_v2_*.csv  -- extended AUS inputs
  lm_out_EUR_v2_*.csv    -- R model results with shared covariate formula
  lm_out_AUS_v2_*.csv    -- R model results
  replication_summary_v2.csv -- replication check against 75 USA V3 hits
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
import subprocess, os

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO    = Path('/home/hmacgregor/BERIL-research-observatory')
DATA    = REPO / 'projects/microbeatlas_metal_ecology/data'
OUTDIR  = DATA / 'eur_aus_cwm'
USA_DIR = DATA / 'usa_cwm'
ENV     = Path('/home/hmacgregor/data/envdbs')
RSCRIPT = '/home/hmacgregor/r_env/bin/Rscript'
SCRIPT  = REPO / 'projects/microbeatlas_metal_ecology/scripts/lm_ns_full_model.R'
COV_V2  = USA_DIR / 'covariate_matrix_634_v2.csv'
METALS  = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
MC_CORES = 4

# ── Load reference grids ──────────────────────────────────────────────────────
print("Loading SoilGrids master (0.25°)...")
sg = pd.read_parquet(ENV / 'SoilGrids/soilgrids_master.parquet',
    columns=['lat','lon','soil_organic_carbon_0cm','bulk_density_0cm',
             'sand_0cm','silt_0cm','nitrogen_0cm','cation_exchange_capacity_0cm'])
sg = sg.dropna(subset=['lat','lon'])
sg_tree = cKDTree(sg[['lat','lon']].values)
print(f"  {len(sg):,} grid cells")

print("Loading WorldClim (0.25°)...")
wc = pd.read_parquet(ENV / 'WorldClim/global_worldclim_all.parquet',
    columns=['lat','lon','annual_mean_temp_c','annual_precip_mm',
             'temp_seasonality','precip_seasonality','temp_annual_range_c','elevation_m'])
wc = wc.dropna(subset=['lat','lon'])
wc_tree = cKDTree(wc[['lat','lon']].values)
print(f"  {len(wc):,} grid cells")

print("Loading GLiM lithology (0.25°)...")
gl = pd.read_parquet(ENV / 'GLIM/global_lithology_glim.parquet')
gl = gl.dropna(subset=['lat','lon','lithology_class'])
gl_tree = cKDTree(gl[['lat','lon']].values)
print(f"  {len(gl):,} grid cells with lithology")

def kd_join(coords, ref_df, ref_tree, columns, max_km=40.0):
    """Nearest-neighbor join, null-out if distance > max_km."""
    dists, idxs = ref_tree.query(coords, k=1)
    # Approx deg to km at the equator: 1° ≈ 111 km
    dists_km = dists * 111.0
    result = ref_df.iloc[idxs][columns].reset_index(drop=True)
    result[dists_km > max_km] = np.nan
    return result

def extend_lm_inputs(region):
    """Load existing lm_input CSVs for region, add global covariates, re-save as v2."""
    print(f"\n{'='*60}")
    print(f"Processing {region}")

    # Load any existing lm_input to get sample locations
    sample_f = OUTDIR / f'lm_input_{region}_Pb.csv'
    sample_raw = pd.read_csv(sample_f)
    samples = sample_raw[['sample_id','lat','lon']].drop_duplicates('sample_id').reset_index(drop=True)
    coords = samples[['lat','lon']].values
    n = len(samples)
    print(f"  {n} unique samples in {region}")

    # KD-join to SoilGrids
    sg_joined = kd_join(coords, sg, sg_tree,
        ['soil_organic_carbon_0cm','bulk_density_0cm','sand_0cm','silt_0cm',
         'nitrogen_0cm','cation_exchange_capacity_0cm'])
    sg_joined.columns = ['organic_matter','bulk_density_0cm','sand_0cm','silt_0cm',
                         'nitrogen_0cm','cec']
    sg_joined.insert(0, 'sample_id', samples['sample_id'].values)

    # KD-join to WorldClim
    wc_joined = kd_join(coords, wc, wc_tree,
        ['annual_mean_temp_c','annual_precip_mm','temp_seasonality',
         'precip_seasonality','temp_annual_range_c','elevation_m'])
    wc_joined.columns = ['mat_c','map_mm','temp_seasonality','precip_seasonality',
                         'temp_annual_range_c','elevation_m']
    wc_joined.insert(0, 'sample_id', samples['sample_id'].values)

    # KD-join to GLiM
    gl_joined = kd_join(coords, gl, gl_tree, ['lithology_class'])
    gl_joined.columns = ['lith_class']
    gl_joined.insert(0, 'sample_id', samples['sample_id'].values)

    # Merge all new covariates into a sample-level patch
    patch = samples[['sample_id']].copy()
    patch = patch.merge(sg_joined, on='sample_id', how='left')
    patch = patch.merge(wc_joined, on='sample_id', how='left')
    patch = patch.merge(gl_joined, on='sample_id', how='left')
    print(f"  Patch coverage: organic_matter={patch['organic_matter'].notna().sum()}/{n}, "
          f"mat_c={patch['mat_c'].notna().sum()}/{n}, "
          f"lith_class={patch['lith_class'].notna().sum()}/{n}")

    # For each metal, load existing lm_input, merge patch, save as v2
    v2_files = {}
    for metal in METALS:
        in_f = OUTDIR / f'lm_input_{region}_{metal}.csv'
        if not in_f.exists():
            print(f"  SKIP {metal}: no lm_input file")
            continue
        d = pd.read_csv(in_f)
        # Drop columns that will be replaced or are US-specific
        drop_cols = ['tectonic_boundary_dist', 'usgs_mine_distance', 'epa_tri_releases',
                     'epa_tri_organic_releases']
        d = d.drop(columns=[c for c in drop_cols if c in d.columns], errors='ignore')
        # Merge patch (one row per sample_id, will broadcast to all KO rows)
        d = d.merge(patch, on='sample_id', how='left')
        out_f = OUTDIR / f'lm_input_{region}_v2_{metal}.csv'
        d.to_csv(out_f, index=False)
        v2_files[metal] = out_f
        print(f"  Written {out_f.name}: {len(d):,} rows, {d.shape[1]} cols")

    return v2_files

def run_r(region, metal, in_path, out_path):
    env = os.environ.copy()
    env['MC_CORES'] = str(MC_CORES)
    env['OMP_NUM_THREADS'] = '1'
    log_path = REPO / f'projects/microbeatlas_metal_ecology/logs/lm_v2_{region}_{metal}.log'
    cmd = [RSCRIPT, str(SCRIPT), str(in_path), metal, str(out_path), str(COV_V2)]
    with open(log_path, 'w') as lf:
        r = subprocess.run(cmd, env=env, stdout=lf, stderr=lf, timeout=3600)
    return r.returncode == 0

# ── Main ──────────────────────────────────────────────────────────────────────
for region in ['EUR', 'AUS']:
    v2_files = extend_lm_inputs(region)

    print(f"\nRunning R models for {region} (v2 covariates)...")
    for metal, in_f in v2_files.items():
        out_f = OUTDIR / f'lm_out_{region}_v2_{metal}.csv'
        if out_f.exists():
            print(f"  SKIP {region} {metal} (already done)")
            continue
        print(f"  Running {region} {metal}...", end=' ', flush=True)
        ok = run_r(region, metal, in_f, out_f)
        print("OK" if ok else "ERROR")

print("\nDone. Outputs in:", OUTDIR)
