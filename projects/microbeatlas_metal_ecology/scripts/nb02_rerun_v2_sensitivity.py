#!/usr/bin/env python3
"""
nb02_rerun_v2_sensitivity.py
-----------------------------
Extended v2 niche breadth rerun testing:
  A. env_only      — environmental samples, no lat/lon filter  (already in otu_env_matrix_v2.csv)
  B. env_latlon    — environmental samples WITH lat/lon
  C. host_incl     — environmental + host-associated samples (animal/*,human/* included)
  D. host_latlon   — host-inclusive + lat/lon filter

Taxonomy tested:
  - v1-compat: genus extracted from Tax string (6th field; NaN if taxonomy < genus depth)
                same logic as original NB02 → compatible with genus_trait_table.csv
  - v2-gtdb:   genus from otu_metadata.parquet 'genus' column (GTDB-assigned)

All Levins B computations use the same formula as NB02.

Outputs (in projects/microbeatlas_metal_ecology/data/):
  otu_env_matrix_v2_{scenario}.csv    — OTU × env detection counts per scenario
  otu_niche_breadth_v2_{scenario}.csv — Levins B per scenario
  nb02_v2_sensitivity_summary.csv     — comparison table across all scenarios
"""

import gc
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from collections import defaultdict
from pathlib import Path

DATA    = Path(__file__).parent.parent / 'data'
MA_DATA = Path('/home/hmacgregor/data/microbeatlas')
SM_PATH = MA_DATA / 'sample_metadata.parquet'
OTU_PATH = MA_DATA / 'otu_counts_long.parquet'
OM_PATH  = MA_DATA / 'otu_metadata.parquet'

# ── Environment mappings ──────────────────────────────────────────────────────
SOIL_SUBS = {
    'farm': 'farm', 'field': 'field',
    'agricultural': 'agricultural', 'agriculture': 'agricultural',
    'forest': 'forest', 'peatland': 'peatland', 'paddy': 'paddy',
    'shrub': 'shrub', 'leaf': 'leaf', 'litter': 'leaf', 'flower': 'flower',
    'desert': 'desert', 'tundra': 'tundra',
}

HOST_CATS = {'animal', 'human', 'host', 'lab'}

def parse_env(env_str, include_host=False):
    """
    Parse v2 environments string → (env_cat_env_only, env_cat_host_incl).
    Returns (None, None) for unclassifiable entries.
    """
    if not isinstance(env_str, str):
        return None, None
    first = env_str.split('|')[0].strip()
    parts = first.split(';', 1)
    major = parts[0].strip() if parts else ''
    sub   = parts[1].strip() if len(parts) > 1 else ''

    if major == 'aquatic':
        return 'aquatic', 'aquatic'
    if major == 'plant':
        return 'plant', 'plant'
    if major == 'desert':
        return 'desert', 'desert'
    if major == 'soil':
        cat = SOIL_SUBS.get(sub, 'soil')
        return cat, cat
    if major in HOST_CATS:
        host_cat = f'host_{sub}' if sub else 'host_animal'
        return None, host_cat  # env_only=None, host_incl=host_cat
    return None, None  # unclassifiable


# ── Step 1: build sample maps ─────────────────────────────────────────────────
print('Step 1: reading sample_metadata.parquet ...')
sm = pd.read_parquet(SM_PATH, columns=['sample_id', 'environments', 'lat', 'lon'])
print(f'  Total: {len(sm):,}')

has_latlon = sm['lat'].notna() & sm['lon'].notna()
print(f'  With lat AND lon: {has_latlon.sum():,} ({has_latlon.mean():.1%})')

# Apply env parsing
parsed = sm['environments'].apply(parse_env)
sm['env_cat_env']  = [p[0] for p in parsed]  # environmental only
sm['env_cat_host'] = [p[1] for p in parsed]  # host-inclusive (env or host)
sm['has_latlon']   = has_latlon

# Build sample lookup dicts
# Each dict: sample_id → env_cat (None = excluded)
maps = {
    'env_only':   dict(zip(sm['sample_id'], sm['env_cat_env'])),
    'env_latlon': dict(zip(
        sm.loc[has_latlon, 'sample_id'],
        sm.loc[has_latlon, 'env_cat_env']
    )),
    'host_incl':  dict(zip(sm['sample_id'], sm['env_cat_host'])),
    'host_latlon': dict(zip(
        sm.loc[has_latlon, 'sample_id'],
        sm.loc[has_latlon, 'env_cat_host']
    )),
}

# Remove None values
for key in maps:
    maps[key] = {k: v for k, v in maps[key].items() if pd.notna(v)}

print('\nSample counts per scenario:')
for sc, m in maps.items():
    print(f'  {sc:15s}: {len(m):>8,} samples')

del sm
gc.collect()

# ── Step 2: env_totals per scenario (sample metadata as denominator) ──────────
print('\nStep 2: env_totals per scenario ...')
from collections import Counter
env_totals = {}
for sc, m in maps.items():
    cnt = Counter(m.values())
    env_totals[sc] = dict(cnt)

print('  env_only top-3:', sorted(env_totals['env_only'].items(), key=lambda x:-x[1])[:3])
print('  env_latlon top-3:', sorted(env_totals['env_latlon'].items(), key=lambda x:-x[1])[:3])
print('  host_incl top-3:', sorted(env_totals['host_incl'].items(), key=lambda x:-x[1])[:3])

# ── Step 3: single streaming pass through otu_counts_long ────────────────────
print('\nStep 3: streaming otu_counts_long.parquet (ONE pass, all scenarios) ...')

# accumulate {scenario: {(otu_id, env_cat): count}}
accums = {sc: defaultdict(int) for sc in maps}
n_rows_total = 0

pf = pq.ParquetFile(OTU_PATH)
for i, batch in enumerate(pf.iter_batches(columns=['otu_id', 'sample_id'],
                                            batch_size=5_000_000)):
    df = batch.to_pandas()
    n_rows_total += len(df)

    for sc, smap in maps.items():
        env_col = df['sample_id'].map(smap)
        mask = env_col.notna()
        sub = df[mask].copy()
        sub['env_cat'] = env_col[mask]
        for (otu_id, env_cat), cnt in sub.groupby(['otu_id', 'env_cat']).size().items():
            accums[sc][(otu_id, env_cat)] += cnt

    if (i + 1) % 20 == 0:
        print(f'  batch {i+1}: {n_rows_total/1e6:.0f}M rows | '
              + ' | '.join(f'{sc}: {len(accums[sc]):,}' for sc in list(maps)[:2]))

print(f'Done. {n_rows_total/1e6:.0f}M rows processed.')

# ── Step 4: compute Levins B for each scenario ────────────────────────────────
def compute_levins(accum, env_total_dict):
    rows = [{'otu_id': k[0], 'Env_Level_1': k[1], 'n_samples_detected': v}
            for k, v in accum.items()]
    otu_env = pd.DataFrame(rows)
    otu_env['n_total_samples'] = otu_env['Env_Level_1'].map(env_total_dict)
    otu_env['prevalence'] = otu_env['n_samples_detected'] / otu_env['n_total_samples']

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
        })

    niche = otu_env.groupby('otu_id').apply(levins_b, include_groups=False).reset_index()
    return otu_env, niche


# ── Step 5: load taxonomy for joining ────────────────────────────────────────
print('\nStep 5: loading taxonomy ...')
om = pd.read_parquet(OM_PATH, columns=['otu_id', 'tax', 'genus', 'n_cells',
                                        'domain', 'phylum', 'family'])
om = om.rename(columns={'tax': 'Tax', 'genus': 'genus_gtdb', 'n_cells': 'n_cells_by_counts'})

# v1-compat genus: 6th semicolon-delimited field (0-indexed = 5)
def v1_genus_from_tax(tax_str):
    if not isinstance(tax_str, str): return None
    parts = [p.strip() for p in tax_str.split(';')]
    # Return field[5] if exists (genus level) only when len >= 6
    if len(parts) >= 6:
        g = parts[5]
        # Exclude if it's a species (contains space)
        return g if g and ' ' not in g else (parts[4] if len(parts) >= 5 else None)
    return None

om['genus_v1compat'] = om['Tax'].apply(v1_genus_from_tax)
om['is_organellar'] = om['Tax'].str.lower().str.contains(
    'mitochond|chloroplast|plastid', na=False)
om['is_unmapped'] = om['domain'].isna() | (om['domain'].str.strip() == '')

# Load nitrifier roles from v1
nit_v1 = pd.read_csv(DATA / 'otu_niche_breadth.csv',
                      usecols=['otu_id', 'nitrifier_role', 'kingdom']).set_index('otu_id')

print(f'  v1-compat genus assigned: {om["genus_v1compat"].notna().sum():,} / {len(om):,}')
print(f'  GTDB genus assigned: {om["genus_gtdb"].notna().sum():,} / {len(om):,}')

# ── Step 6: save per-scenario outputs ────────────────────────────────────────
summary_rows = []

for sc in maps:
    print(f'\nProcessing scenario: {sc} ...')
    otu_env, niche = compute_levins(accums[sc], env_totals[sc])

    # Join taxonomy
    niche = niche.merge(om[['otu_id','Tax','genus_v1compat','genus_gtdb',
                              'n_cells_by_counts','domain','phylum',
                              'is_organellar','is_unmapped']], on='otu_id', how='left')
    niche = niche.merge(nit_v1[['nitrifier_role','kingdom']], on='otu_id', how='left')

    # Save OTU-level outputs
    otu_env.to_csv(DATA / f'otu_env_matrix_v2_{sc}.csv', index=False)
    niche.to_csv(DATA / f'otu_niche_breadth_v2_{sc}.csv', index=False)

    # Genus aggregation (v1-compat taxonomy)
    mask = (
        ~niche['is_unmapped'].fillna(False) &
        ~niche['is_organellar'].fillna(False) &
        niche['genus_v1compat'].notna() &
        (niche['genus_v1compat'].str.strip() != '')
    )
    niche_g = niche[mask]
    n_genera_v1 = niche_g['genus_v1compat'].nunique()

    # Genus aggregation (GTDB taxonomy)
    mask_gtdb = (
        ~niche['is_unmapped'].fillna(False) &
        ~niche['is_organellar'].fillna(False) &
        niche['genus_gtdb'].notna() &
        (niche['genus_gtdb'].str.strip() != '')
    )
    n_genera_gtdb = niche[mask_gtdb]['genus_gtdb'].nunique()

    summary_rows.append({
        'scenario':        sc,
        'n_samples':       len(maps[sc]),
        'n_env_cats':      len(env_totals[sc]),
        'n_otu_env_cells': len(otu_env),
        'n_otus':          niche['otu_id'].nunique(),
        'mean_B_std':      niche['levins_B_std'].mean(),
        'median_B_std':    niche['levins_B_std'].median(),
        'n_genera_v1compat': n_genera_v1,
        'n_genera_gtdb':   n_genera_gtdb,
    })

    print(f'  Saved: {len(otu_env):,} OTU×env rows, {len(niche):,} OTUs')
    print(f'  Mean Levins B_std: {niche["levins_B_std"].mean():.3f}  '
          f'Genera (v1-compat): {n_genera_v1:,}  (GTDB): {n_genera_gtdb:,}')

# ── Step 7: print comparison ──────────────────────────────────────────────────
summary = pd.DataFrame(summary_rows)
summary.to_csv(DATA / 'nb02_v2_sensitivity_summary.csv', index=False)

print('\n' + '='*80)
print('V2 SENSITIVITY COMPARISON')
print('='*80)
print(summary.to_string(index=False))
print()
print('V1 baseline: n_otus=79,104  mean_B_std=0.197  median_B_std=0.138  n_genera_v1compat=2,851')
print()
print('Done. All outputs saved to data/ directory.')
