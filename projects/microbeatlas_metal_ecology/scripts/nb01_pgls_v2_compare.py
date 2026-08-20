#!/usr/bin/env python3
"""
nb01_pgls_v2_compare.py
------------------------
Rerun the primary Arc 1 PGLS (metal gene density → niche breadth) using
MicrobeAtlas v2 niche breadth values in place of the v1 values.

Uses the cached 01_pgls_input_bacteria.csv (predictor data unchanged) and
replaces mean_levins_B_std with v2 values from genus_trait_table_v2.csv.

Tests all available v2 scenarios from nb02_rerun_v2_sensitivity.py:
  - env_only, env_latlon, host_incl, host_latlon

Outputs:
  01_pgls_v2_compare.csv   — full comparison table (v1 + all v2 scenarios)
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Set up paths
REPO    = Path('/home/hmacgregor/BERIL-research-observatory')
CME     = REPO / 'projects' / 'comprehensive_metal_ecology'
MA      = REPO / 'projects' / 'microbeatlas_metal_ecology'
sys.path.insert(0, str(CME))      # for scripts/pgls_utils
sys.path.insert(0, str(CME / 'scripts'))

from pgls_utils import run_pgls, pgls_results_table

DATA_CME = CME / 'data'
DATA_MA  = MA  / 'data'
TREE_BAC = str(DATA_CME / 'gtdb_bac_genus_pruned.tree')

# ── Load v1 PGLS input (predictor unchanged) ─────────────────────────────────
print('Loading v1 PGLS input (cached predictor) ...')
pgls_v1 = pd.read_csv(DATA_CME / '01_pgls_input_bacteria.csv')
print(f'  n bacteria in v1 PGLS: {len(pgls_v1)}')

# ── v1 result for reference ───────────────────────────────────────────────────
print('\nRunning v1 PGLS (verification) ...')
res_v1 = run_pgls(
    df=pgls_v1,
    tree_path=TREE_BAC,
    response='mean_levins_B_std',
    predictors=['predictor_z'],
    taxon_col='genus_lower',
    label='P1_v1_bacteria',
    min_n=100,
)
print(f"  V1: n={res_v1['n']}, λ={res_v1['lambda_est']:.4f}, "
      f"β={res_v1['beta']:+.4f}, p={res_v1['p_value']:.3e}")

all_results = [{'scenario': 'v1_baseline', **res_v1}]

# ── v2 scenarios ──────────────────────────────────────────────────────────────
# Map scenario → niche breadth column in genus_trait_table_v2.csv
SCENARIOS = [
    ('env_only',    'otu_niche_breadth_v2_env_only.csv'),
    ('env_latlon',  'otu_niche_breadth_v2_env_latlon.csv'),
    ('host_incl',   'otu_niche_breadth_v2_host_incl.csv'),
    ('host_latlon', 'otu_niche_breadth_v2_host_latlon.csv'),
]

for sc_name, nb_file in SCENARIOS:
    nb_path = DATA_MA / nb_file
    if not nb_path.exists():
        print(f'\nSkipping {sc_name}: {nb_file} not found (run nb02_rerun_v2_sensitivity.py first)')
        continue

    print(f'\nScenario: {sc_name} ...')

    # Load per-OTU niche breadth
    nb = pd.read_csv(nb_path, usecols=['otu_id', 'levins_B_std', 'genus_v1compat'])
    nb = nb[nb['genus_v1compat'].notna() & (nb['genus_v1compat'].str.strip() != '')]

    # Aggregate to genus level (same logic as NB04)
    genus_nb = nb.groupby('genus_v1compat')['levins_B_std'].mean().reset_index()
    genus_nb.columns = ['genus_lower_raw', 'mean_levins_B_std_v2']
    genus_nb['genus_lower'] = genus_nb['genus_lower_raw'].str.lower().str.strip()
    genus_nb = genus_nb.drop(columns='genus_lower_raw')

    # Merge with v1 PGLS input
    pgls_v2 = pgls_v1.merge(genus_nb, on='genus_lower', how='inner')
    pgls_v2 = pgls_v2.dropna(subset=['mean_levins_B_std_v2', 'predictor_z'])
    print(f'  Genera matched: {len(pgls_v2)} (v1 had {len(pgls_v1)})')

    if len(pgls_v2) < 100:
        print(f'  Too few genera ({len(pgls_v2)}), skipping')
        continue

    # Run PGLS
    res = run_pgls(
        df=pgls_v2,
        tree_path=TREE_BAC,
        response='mean_levins_B_std_v2',
        predictors=['predictor_z'],
        taxon_col='genus_lower',
        label=f'P1_v2_{sc_name}',
        min_n=100,
    )

    print(f"  V2-{sc_name}: n={res['n']}, λ={res['lambda_est']:.4f}, "
          f"β={res['beta']:+.4f}, p={res['p_value']:.3e}")

    # Additional: v2 mean and correlation with v1
    overlap = pgls_v2.copy()
    from scipy import stats
    r, p_r = stats.pearsonr(overlap['mean_levins_B_std'], overlap['mean_levins_B_std_v2'])
    rho, _ = stats.spearmanr(overlap['mean_levins_B_std'], overlap['mean_levins_B_std_v2'])
    print(f'  Pearson r (v1 vs v2): {r:.4f}   Spearman rho: {rho:.4f}')
    print(f'  Mean B_std: v1={overlap["mean_levins_B_std"].mean():.3f}  '
          f'v2={overlap["mean_levins_B_std_v2"].mean():.3f}')

    all_results.append({'scenario': f'v2_{sc_name}', **res})

# ── Save comparison table ─────────────────────────────────────────────────────
compare_cols = ['scenario', 'n', 'lambda_est', 'beta', 'SE', 't_stat', 'p_value',
                'r2', 'delta_aic_vs_null', 'converged']
compare = pd.DataFrame([{c: r.get(c) for c in compare_cols} for r in all_results])
compare.to_csv(DATA_CME / '01_pgls_v2_compare.csv', index=False)

print('\n' + '='*70)
print('PRIMARY PGLS: V1 vs V2 COMPARISON')
print('='*70)
print(compare[['scenario','n','lambda_est','beta','p_value','converged']].to_string(index=False))
print()
print('Null hypothesis: β = 0 (no relationship between metal gene density and niche breadth)')
print('Expected sign:   β < 0 (higher metal gene density → lower niche breadth / more specialized)')
print()
print('Done. Results saved to 01_pgls_v2_compare.csv')
