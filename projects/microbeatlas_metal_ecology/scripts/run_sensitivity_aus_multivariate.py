#!/usr/bin/env python3
"""
NB30 — Pre-specified multivariate PGLS sensitivity analysis.

Tests whether NGSA metal → niche breadth associations survive joint control for
soil pH, soil organic matter (SOM), mean annual temperature (MAT), mean annual
precipitation (MAP), and elevation (negative control).

Environmental covariates (all genus-level means from genus_gee_climate.csv):
  - OLM pH 0cm H2O          → pH_mean
  - OLM soil organic matter  → SOC_mean
  - ERA5 mean temperature    → MAT_mean  (converted K → °C)
  - TerraClimate precip      → MAP_mean
  - DEM elevation            → elev_mean (negative control)

Datasets:
  1. AusMicrobiome+NGSA (metals from aus_genus_geo_niche.csv)
  2. MicrobeAtlas+NGSA all-biome Australian samples (NB29 cache)
  3. MicrobeAtlas+NGSA soil-only Australian samples (NB29 cache)

Outputs:
  data/sensitivity_aus_multivariate_pgls.csv
  data/sensitivity_mb_all_multivariate_pgls.csv
  data/sensitivity_mb_soil_multivariate_pgls.csv
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neighbors import BallTree
from scipy.stats import false_discovery_control

PROJECT_DIR = Path(__file__).parent.parent
DATA        = PROJECT_DIR / 'data'
SCRIPTS     = PROJECT_DIR / 'scripts'
CACHE_DIR   = DATA / 'nb30_env_cache'
CACHE_DIR.mkdir(exist_ok=True)

MAX_DIST_KM  = 200
AUS_LAT_MIN, AUS_LAT_MAX = -44, -10
AUS_LON_MIN, AUS_LON_MAX = 112, 154
MIN_OTUS     = 3
METALS       = ['Cu_ppm', 'Zn_ppm', 'Pb_ppm', 'Ni_ppm', 'Co_ppm']
METAL_LABELS = {m: m.replace('_ppm', '') for m in METALS}
ENV_PREDS    = ['pH_mean', 'SOC_mean', 'MAT_mean', 'MAP_mean', 'elev_mean']


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — MicrobeAtlas per-sample genus detections (all-biome + soil-only)
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*70)
print('Phase 1: MicrobeAtlas per-sample genus detections')
print('='*70)

def extract_genus_from_tax(tax_str):
    if not isinstance(tax_str, str):
        return None
    parts = [p.strip() for p in tax_str.split(';') if p.strip()]
    if not parts:
        return None
    g = parts[-1]
    return g.lower().strip() if g and not g.lower().startswith('bacteria') else None

print('  Loading nb29 genus detections cache...')
mb_det = pd.read_parquet(DATA / 'nb29_aus_cache' / 'aus_genus_detections.parquet')
mb_det['genus_lower'] = mb_det['Tax'].apply(extract_genus_from_tax)
mb_det = mb_det[mb_det['genus_lower'].notna()].copy()
print(f'  Cached genus detections: {len(mb_det):,} rows')

print('  Loading MicrobeAtlas sample metadata...')
sample_meta = pd.read_csv(DATA / 'sample_latlon_env.csv')
sample_meta = sample_meta[
    sample_meta['LatitudeParsed'].notna() &
    sample_meta['LongitudeParsed'].notna()
].copy()
sample_meta['lat'] = pd.to_numeric(sample_meta['LatitudeParsed'], errors='coerce')
sample_meta['lon'] = pd.to_numeric(sample_meta['LongitudeParsed'], errors='coerce')
sample_meta = sample_meta.dropna(subset=['lat', 'lon'])

aus_meta_mb = sample_meta[
    (sample_meta['lat'] >= AUS_LAT_MIN) & (sample_meta['lat'] <= AUS_LAT_MAX) &
    (sample_meta['lon'] >= AUS_LON_MIN) & (sample_meta['lon'] <= AUS_LON_MAX)
].copy()
print(f'  MicrobeAtlas Australian samples: {len(aus_meta_mb):,}')

ngsa = pd.read_csv(DATA / 'ngsa_geochemistry.csv').dropna(subset=['lat', 'lon'])
metal_cols_ngsa = ['Cu_ppm', 'Zn_ppm', 'Pb_ppm', 'Ni_ppm', 'Co_ppm']
tree_ngsa = BallTree(np.radians(ngsa[['lat', 'lon']].values), metric='haversine')
aus_rad   = np.radians(aus_meta_mb[['lat', 'lon']].values)
dists, idxs = tree_ngsa.query(aus_rad, k=1)
dist_km = dists[:, 0] * 6371
aus_meta_mb = aus_meta_mb.copy()
aus_meta_mb['ngsa_dist_km'] = dist_km
aus_meta_mb['ngsa_idx']     = idxs[:, 0]
matched_mb = aus_meta_mb[aus_meta_mb['ngsa_dist_km'] <= MAX_DIST_KM].copy()
for col in metal_cols_ngsa:
    matched_mb[col] = ngsa.iloc[matched_mb['ngsa_idx'].values][col].values
print(f'  Matched within {MAX_DIST_KM} km: {len(matched_mb):,} samples')

mb_latlon = matched_mb[['sample_id', 'lat', 'lon', 'Env_Level_1']].set_index('sample_id')
mb_det_matched = mb_det[mb_det['sample_id'].isin(set(mb_latlon.index))].copy()
mb_det_matched['Env_Level_1'] = mb_latlon.loc[mb_det_matched['sample_id'], 'Env_Level_1'].values

mb_all  = mb_det_matched.copy()
mb_soil = mb_det_matched[mb_det_matched['Env_Level_1'] == 'soil'].copy()
print(f'  MB all-biome: {mb_all["sample_id"].nunique():,} samples, '
      f'{mb_all["genus_lower"].nunique():,} genera')
print(f'  MB soil-only: {mb_soil["sample_id"].nunique():,} samples, '
      f'{mb_soil["genus_lower"].nunique():,} genera')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Load genus-level environmental covariates from GEE climate data
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*70)
print('Phase 2: Load GEE environmental covariates (genus_gee_climate.csv)')
print('='*70)

gee_raw = pd.read_csv(DATA / 'genus_gee_climate.csv')
gee = gee_raw.rename(columns={
    'mean_olm_soil_ph_0cm_H2O':             'pH_mean',
    'mean_olm_soil_organic_matter_0cm_pct': 'SOC_mean',
    'mean_ERA5_mean_2m_air_temperature_K':  'MAT_mean',
    'mean_terraclimate_precipitation_mm':   'MAP_mean',
    'mean_DEM_elevation_m':                 'elev_mean',
})[['genus_lower', 'pH_mean', 'SOC_mean', 'MAT_mean', 'MAP_mean', 'elev_mean']].copy()

gee['MAT_mean'] = gee['MAT_mean'] - 273.15  # Kelvin → Celsius

n_complete = gee[ENV_PREDS].notna().all(axis=1).sum()
print(f'  GEE covariates: {len(gee):,} genera loaded, {n_complete:,} with all 5 env vars')
print(f'  pH range: {gee["pH_mean"].min():.1f}–{gee["pH_mean"].max():.1f}')
print(f'  MAT range: {gee["MAT_mean"].min():.1f}–{gee["MAT_mean"].max():.1f} °C')
print(f'  MAP range: {gee["MAP_mean"].min():.0f}–{gee["MAP_mean"].max():.0f} mm')
print(f'  Elev range: {gee["elev_mean"].min():.0f}–{gee["elev_mean"].max():.0f} m')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Build per-dataset PGLS inputs
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*70)
print('Phase 3: Build PGLS inputs')
print('='*70)

traits = pd.read_csv(DATA / 'genus_trait_table.csv')
levins = traits[['gtdb_genus_lower', 'mean_levins_B_std', 'n_otus']].rename(
    columns={'gtdb_genus_lower': 'genus_lower'})

# AusMicrobiome: metal means from aus_genus_geo_niche.csv (AusMicrobiome+NGSA spatial join)
am_geo = pd.read_csv(DATA / 'aus_genus_geo_niche.csv')
am_ngsa = am_geo[['genus_lower', 'Cu_mean', 'Zn_mean', 'Pb_mean', 'Ni_mean', 'Co_mean']].rename(
    columns={'Cu_mean': 'Cu_ppm', 'Zn_mean': 'Zn_ppm',
             'Pb_mean': 'Pb_ppm', 'Ni_mean': 'Ni_ppm', 'Co_mean': 'Co_ppm'})

def mb_ngsa_means(mb_df, matched_df):
    """Mean NGSA metal concentration per genus across matched samples."""
    sample_metal = matched_df.set_index('sample_id')[METALS].copy()
    merged = mb_df[['sample_id', 'genus_lower']].merge(
        sample_metal.reset_index(), on='sample_id', how='inner')
    return merged.groupby('genus_lower')[METALS].mean().reset_index()

mb_all_ngsa  = mb_ngsa_means(mb_all,  matched_mb)
mb_soil_ngsa = mb_ngsa_means(mb_soil, matched_mb)

def build_pgls_input(ngsa_df, levins_df, gee_df, label):
    df = ngsa_df.merge(gee_df, on='genus_lower', how='inner')
    df = df.merge(levins_df, on='genus_lower', how='inner')
    df = df[df['n_otus'] >= MIN_OTUS].dropna(subset=['mean_levins_B_std'])
    print(f'  {label}: {len(df):,} genera in merged input')
    return df

am_input   = build_pgls_input(am_ngsa,      levins, gee, 'AusMicrobiome')
mb_all_in  = build_pgls_input(mb_all_ngsa,  levins, gee, 'MB all-biome')
mb_soil_in = build_pgls_input(mb_soil_ngsa, levins, gee, 'MB soil-only')

datasets = [
    ('AusMicrobiome', am_input,   DATA / 'sensitivity_aus_multivariate_pgls.csv'),
    ('MB_all',        mb_all_in,  DATA / 'sensitivity_mb_all_multivariate_pgls.csv'),
    ('MB_soil',       mb_soil_in, DATA / 'sensitivity_mb_soil_multivariate_pgls.csv'),
]


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Multivariate PGLS per dataset × metal
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*70)
print('Phase 4: Multivariate PGLS')
print('='*70)

TREE = DATA / 'gtdb_bac_genus_pruned.tree'

all_results = []
for ds_label, ds_input, ds_output in datasets:
    print(f'\n--- Dataset: {ds_label} (n={len(ds_input)}) ---')
    ds_results = []

    for metal in METALS:
        metal_label = METAL_LABELS[metal]
        need_cols = ['genus_lower', 'mean_levins_B_std', metal] + ENV_PREDS
        sub = ds_input[need_cols].dropna().copy()
        if len(sub) < 50:
            print(f'  {metal_label}: only {len(sub)} genera, skip')
            continue

        metal_mean_col = f'{metal_label}_mean'
        sub = sub.rename(columns={metal: metal_mean_col})
        all_pred_cols = [metal_mean_col] + ENV_PREDS
        pred_str      = ','.join(all_pred_cols)

        inp_csv = CACHE_DIR / f'{ds_label}_{metal_label}_multi_input.csv'
        out_csv = CACHE_DIR / f'{ds_label}_{metal_label}_multi_result.csv'
        sub.to_csv(inp_csv, index=False)

        shell_cmd = (
            f'source /opt/conda/etc/profile.d/conda.sh && conda activate r_env && '
            f'Rscript {SCRIPTS / "pgls_multivariate.R"} '
            f'--input {inp_csv} '
            f'--tree {TREE} '
            f'--response mean_levins_B_std '
            f'--predictors {pred_str} '
            f'--focal {metal_mean_col} '
            f'--output {out_csv} '
            f'--label "{ds_label} {metal_label} multivariate (NB30)"'
        )
        r = subprocess.run(['bash', '-c', shell_cmd],
                           capture_output=True, text=True, cwd=str(PROJECT_DIR))
        if r.returncode != 0:
            print(f'  {metal_label}: R error — {r.stderr[-300:]}')
            continue

        row = pd.read_csv(out_csv)
        row['dataset'] = ds_label
        row['metal']   = metal_label
        row['n_genera_input'] = len(sub)
        ds_results.append(row)
        focal_full = row[(row['model_type'] == 'full_multivariate') &
                         (row['predictor'] == metal_mean_col)]
        if len(focal_full):
            b, p = focal_full['beta'].iloc[0], focal_full['p_value'].iloc[0]
            print(f'  {metal_label} (full model, focal): β={b:+.4f}, p={p:.4g}')

    if not ds_results:
        print(f'  No results for {ds_label}')
        continue

    combined = pd.concat(ds_results, ignore_index=True)
    focal_mask = ((combined['model_type'] == 'full_multivariate') &
                  (combined['predictor'].str.endswith('_mean')) &
                  combined['predictor'].str[:-5].isin(METAL_LABELS.values()))
    combined['q_bh'] = np.nan
    if focal_mask.sum() > 1:
        pvals = combined.loc[focal_mask, 'p_value'].values
        combined.loc[focal_mask, 'q_bh'] = false_discovery_control(pvals, method='bh')
    elif focal_mask.sum() == 1:
        combined.loc[focal_mask, 'q_bh'] = combined.loc[focal_mask, 'p_value'].values

    combined.to_csv(ds_output, index=False)
    print(f'\n  Saved: {ds_output.name}')
    all_results.append(combined)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — Summary
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*70)
print('Phase 5: Summary')
print('='*70)

for ds_label, _, ds_output in datasets:
    if not ds_output.exists():
        continue
    df = pd.read_csv(ds_output)
    focal_full = df[df['model_type'] == 'full_multivariate']
    print(f'\n=== {ds_label} — full multivariate model ===')
    print(focal_full[['metal', 'predictor', 'beta', 'SE', 'p_value', 'q_bh', 'lambda', 'n']]
          .to_string(index=False))

print('\nDone.')
