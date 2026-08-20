#!/usr/bin/env python3
"""
eur_aus_latlon_model.py

Adds sp_lat / sp_lon to EUR and AUS v2 lm_input CSVs and reruns the R model.
The R script includes any column starting with 'sp_' in the linear predictor set,
so renaming lat/lon to sp_lat/sp_lon is sufficient to add spatial control.

Outputs: data/eur_aus_cwm/latlon_model/
  lm_input_{EUR,AUS}_v3_{metal}.csv
  lm_out_{EUR,AUS}_v3_{metal}.csv
  gam_results_eur_aus_v3.csv  (pooled BH-FDR across 12 region×metal)
"""
import os, subprocess, time
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.stats.multitest import multipletests

REPO    = Path('/home/hmacgregor/BERIL-research-observatory')
DATA    = REPO / 'projects/microbeatlas_metal_ecology/data'
EUR_AUS = DATA / 'eur_aus_cwm'
OUTDIR  = EUR_AUS / 'latlon_model'
RSCRIPT = '/home/hmacgregor/r_env/bin/Rscript'
SCRIPT  = REPO / 'projects/microbeatlas_metal_ecology/scripts/lm_ns_full_model.R'
MC_CORES = 4
METALS  = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']

OUTDIR.mkdir(exist_ok=True)

env = os.environ.copy()
env['OMP_NUM_THREADS'] = '1'
env['MC_CORES'] = str(MC_CORES)

results = []

for region in ['EUR', 'AUS']:
    for metal in METALS:
        src   = EUR_AUS / f'lm_input_{region}_v2_{metal}.csv'
        dst   = OUTDIR  / f'lm_input_{region}_v3_{metal}.csv'
        out   = OUTDIR  / f'lm_out_{region}_v3_{metal}.csv'

        if out.exists():
            print(f'[{region} {metal}] loading cached results')
            df = pd.read_csv(out)
            df['region'] = region
            df['metal']  = metal
            results.append(df)
            continue

        if not dst.exists():
            print(f'[{region} {metal}] writing v3 lm_input with sp_lat/sp_lon ...')
            df_in = pd.read_csv(src)
            # Add spatial columns — R script picks up sp_* automatically
            df_in['sp_lat'] = df_in['lat']
            df_in['sp_lon'] = df_in['lon']
            df_in.to_csv(dst, index=False)
            n_samples = df_in['sample_id'].nunique()
            n_kos     = df_in['ko_id'].nunique()
            print(f'  n_samples={n_samples}, n_KOs={n_kos}, rows={len(df_in):,}')
        else:
            print(f'[{region} {metal}] v3 lm_input already exists — running R ...')

        cmd = [RSCRIPT, str(SCRIPT), str(dst), metal, str(out)]
        t0 = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        elapsed = time.time() - t0
        if proc.returncode != 0:
            print(f'  R FAILED ({elapsed:.0f}s):\n{proc.stderr[-800:]}')
            continue
        print(f'  Done in {elapsed:.0f}s.')
        if not out.exists():
            print(f'  WARNING: output CSV not found after R run')
            continue

        df = pd.read_csv(out)
        df['region'] = region
        df['metal']  = metal
        results.append(df)
        print(f'  {len(df)} KOs; {df["p_metal_full"].notna().sum()} valid')

# Pool BH-FDR across all 12 region×metal combinations
print('\nPooling BH-FDR across 12 region×metal ...')
all_res = pd.concat(results, ignore_index=True)
mask = all_res['p_metal_full'].notna()
qs   = np.full(len(all_res), np.nan)
_, q, _, _ = multipletests(all_res.loc[mask, 'p_metal_full'], method='fdr_bh')
qs[mask] = q
all_res['q_BH_pooled'] = qs

out_all = OUTDIR / 'gam_results_eur_aus_v3.csv'
all_res.to_csv(out_all, index=False)

sig = all_res[all_res['q_BH_pooled'] < 0.05]
print(f'\nTotal tests: {mask.sum():,}')
print(f'FDR<0.05: {len(sig)}')
print(sig.sort_values(['region','metal','q_BH_pooled'])
      [['region','ko_id','metal','q_BH_pooled','delta_r2_full','beta_sign','n']]
      .round(4)
      .to_string(index=False))

# Compare with v2 hits
print('\n=== v2 vs v3 hit comparison ===')
v2_hits = {('AUS','K25985','As'), ('AUS','K27191','Cr'), ('AUS','K15896','Cr'), ('AUS','K27191','Cu'),
           ('EUR','K00621','As'), ('EUR','K24694','Cd'), ('EUR','K15896','Cr'), ('EUR','K18355','Cr')}
v3_hits = set(zip(sig['region'], sig['ko_id'], sig['metal']))
survived = v2_hits & v3_hits
new_hits = v3_hits - v2_hits
dropped  = v2_hits - v3_hits
print(f'v2 hits that SURVIVE lat/lon control ({len(survived)}/8): {sorted(survived)}')
print(f'v2 hits DROPPED ({len(dropped)}/8): {sorted(dropped)}')
print(f'NEW hits in v3 ({len(new_hits)}): {sorted(new_hits)}')
