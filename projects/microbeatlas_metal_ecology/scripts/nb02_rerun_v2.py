#!/usr/bin/env python3
"""
nb02_rerun_v2.py
-----------------
Recompute OTU niche breadth (Levins' B) using the full MicrobeAtlas v2 dataset
(arkinlab.microbeatlas.*, dot notation, 1.88M samples, 660M OTU rows) instead
of the old v1 subset (arkinlab_microbeatlas.*, underscore, 463K samples).

Key changes from NB02:
  - Source: local parquet files at /home/hmacgregor/data/microbeatlas/
  - Denominator: all samples that appear in otu_counts_long (not technology filter)
  - Environment mapping: parse v2 'environments' column → 13-cat Env_Level_1 equivalent
  - tundra environment included as new v2-only category

Outputs (in projects/microbeatlas_metal_ecology/data/):
  env_totals_v2.csv           — samples per env category (denominator)
  otu_env_matrix_v2.csv       — OTU × env detection counts
  otu_niche_breadth_v2.csv    — per-OTU Levins' B + taxonomy + full trait table
"""

import os
import sys
import gc
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from collections import defaultdict
from pathlib import Path

DATA       = Path(__file__).parent.parent / 'data'
MA_DATA    = Path('/home/hmacgregor/data/microbeatlas')
SM_PATH    = MA_DATA / 'sample_metadata.parquet'
OTU_PATH   = MA_DATA / 'otu_counts_long.parquet'
OM_PATH    = MA_DATA / 'otu_metadata.parquet'

# ── v1 baselines for comparison ───────────────────────────────────────────────
V1_MEAN_B_STD = 0.197
V1_N_OTUS     = 79104
V1_N_ENVS     = 13

# ── environment category mapping ─────────────────────────────────────────────
# v2 'environments' format: 'major;sub|major;sub|...'
# Take first pipe-separated entry; map major/sub to 13-category Env_Level_1 equivalent.

SOIL_SUBS = {
    'farm':          'farm',
    'field':         'field',
    'agricultural':  'agricultural',
    'agriculture':   'agricultural',
    'forest':        'forest',
    'peatland':      'peatland',
    'paddy':         'paddy',
    'shrub':         'shrub',
    'leaf':          'leaf',
    'litter':        'leaf',
    'flower':        'flower',
    'desert':        'desert',
    'tundra':        'tundra',   # new in v2
}

def parse_env_cat(env_str):
    """Map v2 environments string to Env_Level_1-compatible category."""
    if not isinstance(env_str, str):
        return None
    first = env_str.split('|')[0].strip()
    parts = first.split(';', 1)
    major = parts[0].strip() if parts else ''
    sub   = parts[1].strip() if len(parts) > 1 else ''

    if major == 'aquatic':
        return 'aquatic'
    if major == 'plant':
        return 'plant'
    if major == 'desert':
        return 'desert'
    if major == 'soil':
        return SOIL_SUBS.get(sub, 'soil')
    return None  # animal, human, host, lab → exclude


# ── Step 1: build sample → env_cat mapping from sample_metadata ──────────────
print('Step 1: reading sample_metadata.parquet ...')
sm = pd.read_parquet(SM_PATH, columns=['sample_id', 'environments'])
print(f'  Total samples: {len(sm):,}')

sm['env_cat'] = sm['environments'].map(parse_env_cat)
n_valid = sm['env_cat'].notna().sum()
print(f'  Samples with valid env_cat: {n_valid:,} ({n_valid/len(sm):.1%})')

# Build lookup dict (sample_id → env_cat); None entries are excluded
sample_to_env = dict(zip(sm['sample_id'], sm['env_cat']))
# Remove None values so .get() returns None for both missing and excluded
sample_to_env = {k: v for k, v in sample_to_env.items() if pd.notna(v)}
print(f'  Unique env_cat values: {sorted(set(sample_to_env.values()))}')
del sm
gc.collect()

# env_totals: count samples per env_cat (all samples that have env_cat, since
# v2 sample_metadata covers only samples that appear in otu_counts_long)
print('\nStep 2: computing env_totals from sample_metadata ...')
from collections import Counter
env_count = Counter(sample_to_env.values())
env_totals_v2 = (pd.DataFrame.from_dict(env_count, orient='index', columns=['n_total_samples'])
                   .rename_axis('Env_Level_1').sort_values('n_total_samples', ascending=False))
env_totals_v2.to_csv(DATA / 'env_totals_v2.csv')
print(env_totals_v2.to_string())


# ── Step 3: stream otu_counts_long → accumulate OTU × env_cat counts ─────────
# Each (otu_id, sample_id) pair is unique in otu_counts_long, so
# COUNT(DISTINCT sample_id) per (otu_id, env_cat) == COUNT(*) after join.
print('\nStep 3: streaming otu_counts_long.parquet (this takes ~5–10 min) ...')

pf = pq.ParquetFile(OTU_PATH)
accum = defaultdict(int)   # (otu_id, env_cat) → n_samples_detected
batch_size = 5_000_000
n_rows_total = 0
n_rows_kept  = 0

for i, batch in enumerate(pf.iter_batches(columns=['otu_id', 'sample_id'],
                                           batch_size=batch_size)):
    df = batch.to_pandas()
    n_rows_total += len(df)

    df['env_cat'] = df['sample_id'].map(sample_to_env)
    df = df[df['env_cat'].notna()]
    n_rows_kept += len(df)

    for (otu_id, env_cat), cnt in df.groupby(['otu_id', 'env_cat']).size().items():
        accum[(otu_id, env_cat)] += cnt

    if (i + 1) % 10 == 0:
        print(f'  batch {i+1}: {n_rows_total/1e6:.0f}M rows processed, '
              f'{n_rows_kept/1e6:.1f}M kept, {len(accum):,} OTU×env cells')

print(f'Done. {n_rows_total/1e6:.0f}M rows processed, {n_rows_kept/1e6:.1f}M kept.')
print(f'OTU × env cells: {len(accum):,}')

# Convert accumulator to DataFrame
otu_env_v2 = pd.DataFrame(
    [{'otu_id': k[0], 'Env_Level_1': k[1], 'n_samples_detected': v}
     for k, v in accum.items()]
)
del accum
gc.collect()

# Compute prevalence = n_samples_detected / n_total_samples_in_env
env_totals_dict = env_totals_v2['n_total_samples'].to_dict()
otu_env_v2['n_total_samples'] = otu_env_v2['Env_Level_1'].map(env_totals_dict)
otu_env_v2['prevalence'] = otu_env_v2['n_samples_detected'] / otu_env_v2['n_total_samples']

otu_env_v2.to_csv(DATA / 'otu_env_matrix_v2.csv', index=False)
print(f'Saved otu_env_matrix_v2.csv: {otu_env_v2.shape}')


# ── Step 4: compute Levins' B niche breadth (same formula as NB02) ────────────
print('\nStep 4: computing Levins\' B ...')

def levins_b(grp):
    p = grp['prevalence'].values
    q = p / p.sum()
    B = 1.0 / (q ** 2).sum()
    n = len(p)
    return pd.Series({
        'n_envs_detected':  n,
        'levins_B':         B,
        'levins_B_std':     (B - 1) / (n - 1) if n > 1 else 0.0,
        'dominant_env':     grp.loc[grp['prevalence'].idxmax(), 'Env_Level_1'],
        'max_prevalence':   p.max(),
        'mean_prevalence':  p.mean(),
    })

niche_v2 = (otu_env_v2.groupby('otu_id')
                       .apply(levins_b, include_groups=False)
                       .reset_index())


# ── Step 5: join taxonomy from otu_metadata ───────────────────────────────────
print('\nStep 5: joining taxonomy from otu_metadata.parquet ...')
om = pd.read_parquet(OM_PATH, columns=['otu_id', 'tax', 'n_cells', 'domain',
                                        'phylum', 'class', 'order', 'family',
                                        'genus', 'species'])

# v2 uses lowercase 'tax' vs v1 'Tax'; rename for consistency
om = om.rename(columns={'tax': 'Tax', 'n_cells': 'n_cells_by_counts'})

# is_organellar / is_unmapped heuristic (reproduce v1 logic from taxonomy string)
om['is_organellar'] = om['Tax'].str.lower().str.contains(
    'mitochond|chloroplast|plastid', na=False)
om['is_unmapped'] = om['domain'].isna() | (om['domain'].str.strip() == '')

niche_v2 = niche_v2.merge(om, on='otu_id', how='left')

# Load nitrifier annotations from v1 file if available (same OTU IDs)
nit_path = DATA / 'otu_niche_breadth.csv'
if nit_path.exists():
    nit_v1 = pd.read_csv(nit_path, usecols=['otu_id', 'nitrifier_role'])
    nit_v1 = nit_v1[nit_v1['nitrifier_role'].notna()]
    niche_v2 = niche_v2.merge(nit_v1, on='otu_id', how='left')
else:
    niche_v2['nitrifier_role'] = np.nan

niche_v2.to_csv(DATA / 'otu_niche_breadth_v2.csv', index=False)
print(f'Saved otu_niche_breadth_v2.csv: {niche_v2.shape}')


# ── Step 6: v1 vs v2 comparison ──────────────────────────────────────────────
print('\n' + '='*60)
print('V1 vs V2 COMPARISON')
print('='*60)
print(f'{"":30s} {"V1":>12s} {"V2":>12s}')
print(f'{"OTUs with niche breadth":30s} {V1_N_OTUS:>12,} {len(niche_v2):>12,}')
print(f'{"Env categories":30s} {V1_N_ENVS:>12d} {len(env_totals_v2):>12d}')
print(f'{"Mean Levins_B_std":30s} {V1_MEAN_B_STD:>12.3f} '
      f'{niche_v2["levins_B_std"].mean():>12.3f}')
print(f'{"Median Levins_B_std":30s} {"0.138":>12s} '
      f'{niche_v2["levins_B_std"].median():>12.3f}')

print('\nV2 env_totals (OTU-bearing samples per environment):')
print(env_totals_v2.to_string())

print('\nV1 env_totals (for reference):')
v1_et = pd.read_csv(DATA / 'env_totals.csv')
print(v1_et.sort_values('n_total_samples', ascending=False).to_string(index=False))

print('\nV2 Levins_B_std distribution:')
print(niche_v2['levins_B_std'].describe().round(3).to_string())

print('\nDone.')
