#!/usr/bin/env python3
"""
nb27_inverse_pgls_v2.py
------------------------
Rerun the NB27 inverse PGLS (ko_per_mb_primary ~ niche characteristics)
substituting v2 MicrobeAtlas n_envs_detected for the v1 n_biomes predictor.

Metal-range predictors (Cu_range, Zn_range, Pb_range, Ni_range) are NGSA-Australia-
specific and computed from the AusMicrobiome feature_matrix — they are unchanged by
the global v2 expansion (NGSA is Australia-only regardless of dataset version).

n_biomes_z is the dominant predictor in the v1 inverse PGLS (β=+0.215, p≈0) and is
directly affected by v2: more global samples → genera detected in more environments.

Outputs:
  data/inverse_pgls_results_v2.csv   — full comparison: all v1 predictors + v2 n_envs
  data/nb27_niche_characteristics.csv — per-genus niche characteristics (v1 computed)
"""

import os, sys
import numpy as np
import pandas as pd
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'

PROJECT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
CCP     = Path('/home/hmacgregor/BERIL-research-observatory/projects/community_composition_prediction')
MA      = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology')
DATA    = PROJECT / 'data'
FIGS    = PROJECT / 'figures'
TREE_BAC = str(DATA / 'gtdb_bac_genus_pruned.tree')

sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'scripts'))
from pgls_utils import run_pgls, pgls_results_table

# ── Step 1: Load v1 PGLS input ────────────────────────────────────────────────
print('Step 1: Loading v1 PGLS input (1,574 bacteria) ...')
pgls_input = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
print(f'  n genera: {len(pgls_input)}')

# ── Step 2: Compute v1 niche characteristics from genus_ra × feature_matrix ──
print('\nStep 2: Computing v1 niche characteristics ...')
GENUS_RA_PATH   = CCP / 'data' / 'genus_ra.parquet'
FEAT_MAT_PATH   = CCP / 'data' / 'feature_matrix.parquet'
LATLON_ENV_PATH = DATA / 'sample_latlon_env.csv'

ENV_COLS = ['ph', 'temp_K', 'precip_mm', 'log_Cu_ppm', 'log_Zn_ppm',
            'log_Pb_ppm', 'log_Ni_ppm', 'lat']

fm_full = pd.read_parquet(FEAT_MAT_PATH, columns=ENV_COLS)
print(f'  Feature matrix: {fm_full.shape}')

if LATLON_ENV_PATH.exists():
    latlon_env = pd.read_csv(LATLON_ENV_PATH, usecols=['sample_id', 'Env_Level_1'])
    latlon_env = latlon_env.dropna(subset=['Env_Level_1']).set_index('sample_id')
    fm_biome = fm_full.join(latlon_env['Env_Level_1'], how='left')
    print(f'  Biome coverage: {fm_biome["Env_Level_1"].notna().sum()} / {len(fm_biome)}')
else:
    fm_biome = fm_full.copy()
    fm_biome['Env_Level_1'] = np.nan

pgls_genera_set = set(pgls_input['genus_lower'])
gr_all = pd.read_parquet(GENUS_RA_PATH)
pgls_in_gr = [g for g in pgls_genera_set if g in gr_all.columns]
print(f'  PGLS genera in genus_ra: {len(pgls_in_gr)} / {len(pgls_genera_set)}')

common_idx = gr_all.index.intersection(fm_biome.index)
gr = gr_all.loc[common_idx, pgls_in_gr]
fm_env = fm_biome.loc[common_idx]
del gr_all

DETECT_THRESH = 1e-4
MIN_DETECT    = 10

niche_records = []
for i, genus in enumerate(pgls_in_gr):
    if i % 200 == 0:
        print(f'  {i}/{len(pgls_in_gr)} genera ...')
    ra = gr[genus].values
    present = ra > DETECT_THRESH
    n_det = int(present.sum())
    row = {'genus_lower': genus, 'n_detected': n_det}

    if n_det < MIN_DETECT:
        for col in ENV_COLS:
            row[f'niche_{col}_mean']  = np.nan
            row[f'niche_{col}_sd']    = np.nan
            row[f'niche_{col}_range'] = np.nan
        row['n_biomes'] = np.nan
        niche_records.append(row)
        continue

    for col in ENV_COLS:
        vals = fm_env.loc[present, col].dropna() if col in fm_env.columns else pd.Series(dtype=float)
        if len(vals) >= 5:
            row[f'niche_{col}_mean']  = float(vals.mean())
            row[f'niche_{col}_sd']    = float(vals.std())
            row[f'niche_{col}_range'] = float(vals.max() - vals.min())
        else:
            row[f'niche_{col}_mean']  = np.nan
            row[f'niche_{col}_sd']    = np.nan
            row[f'niche_{col}_range'] = np.nan

    if 'Env_Level_1' in fm_env.columns:
        biomes = fm_env.loc[present, 'Env_Level_1'].dropna().unique()
        row['n_biomes'] = int(len(biomes))
    else:
        row['n_biomes'] = np.nan

    niche_records.append(row)

niche_df = pd.DataFrame(niche_records)
niche_df.to_csv(DATA / 'nb27_niche_characteristics.csv', index=False)
print(f'  Saved nb27_niche_characteristics.csv: {niche_df.shape}')
print(f'  Genera with n_detected >= {MIN_DETECT}: {(niche_df["n_detected"] >= MIN_DETECT).sum()}')

# ── Step 3: Add v2 n_envs_detected (global, 591K env-only samples) ────────────
print('\nStep 3: Loading v2 n_envs_detected ...')
nb_v2 = pd.read_csv(
    MA / 'data' / 'otu_niche_breadth_v2_env_only.csv',
    usecols=['otu_id', 'n_envs_detected', 'genus_v1compat']
)
nb_v2 = nb_v2[nb_v2['genus_v1compat'].notna() & (nb_v2['genus_v1compat'].str.strip() != '')]
nb_v2['genus_lower'] = nb_v2['genus_v1compat'].str.lower().str.strip()

# Aggregate to genus: mean n_envs_detected across OTUs
genus_nenvs_v2 = (nb_v2.groupby('genus_lower')['n_envs_detected']
                        .mean()
                        .reset_index()
                        .rename(columns={'n_envs_detected': 'n_envs_v2'}))
print(f'  Genera with v2 n_envs: {len(genus_nenvs_v2)}')

# ── Step 4: Merge everything ──────────────────────────────────────────────────
print('\nStep 4: Merging PGLS input + v1 niche + v2 n_envs ...')
pgls_df = (pgls_input
           .merge(niche_df, on='genus_lower', how='inner')
           .merge(genus_nenvs_v2, on='genus_lower', how='left'))
print(f'  Merged: {pgls_df.shape}  '
      f'(v2 n_envs non-null: {pgls_df["n_envs_v2"].notna().sum()})')

# Z-score everything
pgls_df['ko_per_mb_z'] = ((pgls_df['ko_per_mb_primary'] - pgls_df['ko_per_mb_primary'].mean())
                          / pgls_df['ko_per_mb_primary'].std())

PREDICTORS = {
    'mean_Cu_z':       'niche_log_Cu_ppm_mean',
    'mean_Zn_z':       'niche_log_Zn_ppm_mean',
    'mean_Pb_z':       'niche_log_Pb_ppm_mean',
    'mean_Ni_z':       'niche_log_Ni_ppm_mean',
    'mean_pH_z':       'niche_ph_mean',
    'sd_pH_z':         'niche_ph_sd',
    'Cu_range_z':      'niche_log_Cu_ppm_range',
    'Zn_range_z':      'niche_log_Zn_ppm_range',
    'temp_range_z':    'niche_temp_K_range',
    'precip_range_z':  'niche_precip_mm_range',
    'mean_lat_z':      'niche_lat_mean',
    'n_biomes_z':      'n_biomes',       # v1: AusMicrobiome 6K samples
    'n_envs_v2_z':     'n_envs_v2',      # v2: global 591K env-only samples
}

for z_col, raw_col in PREDICTORS.items():
    if raw_col in pgls_df.columns:
        vals = pgls_df[raw_col]
        pgls_df[z_col] = (vals - vals.mean()) / vals.std()
    else:
        pgls_df[z_col] = np.nan

print('\nPredictor availability:')
for z in PREDICTORS:
    n = pgls_df[z].notna().sum()
    print(f'  {z:20s}: {n}')

# ── Step 5: Single-predictor PGLS (all predictors incl. n_envs_v2_z) ─────────
print('\nStep 5: Single-predictor PGLS ...')
all_preds = list(PREDICTORS.keys())
single_results = []
for pred in all_preds:
    n_avail = pgls_df[pred].notna().sum()
    if n_avail < 50:
        print(f'  Skipping {pred}: n={n_avail}')
        continue
    try:
        res = run_pgls(
            pgls_df, TREE_BAC,
            response='ko_per_mb_z',
            predictors=[pred],
            taxon_col='genus_lower',
            label=pred,
            min_n=30,
        )
        print(f'  {pred}: β={res["beta"]:+.4f}, p={res["p_value"]:.3e}, n={res["n"]}, λ={res["lambda_est"]:.3f}')
        single_results.append({'model_type': 'single_predictor', **res})
    except Exception as e:
        print(f'  {pred}: FAILED — {e}')

single_df = pd.DataFrame(single_results)

# ── Step 6: Multi-predictor models ───────────────────────────────────────────
print('\nStep 6: Multi-predictor PGLS ...')
BASE_MULTI = ['mean_Cu_z', 'mean_Zn_z', 'mean_pH_z', 'temp_range_z']

multi_rows = []
for label, n_col in [('multi_v1_nbiomes', 'n_biomes_z'), ('multi_v2_nenvs', 'n_envs_v2_z')]:
    preds = [p for p in BASE_MULTI + [n_col] if pgls_df[p].notna().sum() >= 100]
    if len(preds) < 2:
        print(f'  {label}: too few predictors ({preds}), skipping')
        continue
    try:
        res = run_pgls(
            pgls_df, TREE_BAC,
            response='ko_per_mb_z',
            predictors=preds,
            taxon_col='genus_lower',
            label=label,
            min_n=30,
        )
        print(f'\n  {label}: n={res["n"]}, λ={res["lambda_est"]:.3f}, R²={res["r2"]:.4f}')
        for pred in preds:
            b = res['betas'][pred]
            p = res['p_values'][pred]
            print(f'    {pred}: β={b:+.4f}, p={p:.3e}')
        for pred in preds:
            multi_rows.append({
                'model_type': label,
                'label': pred,
                'n': res['n'],
                'lambda_est': res['lambda_est'],
                'beta': res['betas'][pred],
                'SE': res['SEs'][pred],
                'p_value': res['p_values'][pred],
                'r2': res['r2'],
                'delta_aic_vs_null': res.get('delta_aic_vs_null'),
                'converged': res.get('converged'),
            })
    except Exception as e:
        print(f'  {label}: FAILED — {e}')

multi_df = pd.DataFrame(multi_rows)

# ── Step 7: Save results ──────────────────────────────────────────────────────
out = pd.concat([single_df, multi_df], ignore_index=True)
keep_cols = ['model_type', 'label', 'n', 'lambda_est', 'beta', 'SE', 'p_value', 'r2',
             'delta_aic_vs_null', 'converged']
out = out[[c for c in keep_cols if c in out.columns]]
out.to_csv(DATA / 'inverse_pgls_results_v2.csv', index=False)
print(f'\nSaved: data/inverse_pgls_results_v2.csv ({len(out)} rows)')

# ── Step 8: Print comparison ──────────────────────────────────────────────────
print('\n' + '='*70)
print('NB27 INVERSE PGLS: V1 vs V2 n_biomes COMPARISON')
print('='*70)
print('Single-predictor results (sorted by p):')
disp = (single_df[['label', 'n', 'beta', 'p_value', 'lambda_est']]
        .sort_values('p_value')
        .rename(columns={'lambda_est': 'lambda'}))
print(disp.to_string(index=False))

print('\nV1 n_biomes vs V2 n_envs (head-to-head):')
nb = single_df[single_df['label'].isin(['n_biomes_z', 'n_envs_v2_z'])]
print(nb[['label', 'n', 'beta', 'p_value', 'lambda_est']].to_string(index=False))

if len(multi_df):
    print('\nMulti-predictor comparison:')
    print(multi_df[['model_type', 'label', 'beta', 'p_value']].to_string(index=False))

print('\nV1 reference (from REPORT.md):')
print('  n_biomes_z: β=+0.215, p≈0 (dominant predictor)')
print('  temp_range_z: β=+0.161, p=4.9×10⁻¹⁴')
print('  Zn_range_z: β=+0.153, p=4.1×10⁻¹²')
print('  Cu_range_z: β=+0.147, p=1.2×10⁻¹¹')
print()
print('Done.')
