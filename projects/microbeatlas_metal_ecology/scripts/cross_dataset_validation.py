#!/usr/bin/env python3
"""
cross_dataset_validation.py
----------------------------
Three diagnostic PGLS tests to identify what drives the sign reversal between
the primary isolate+Levins' B analysis and the MGnify MAG+biome_Shannon validation.

Test A  — Soil+rhizosphere MAGs only (same biome-Shannon metric, restricted environment)
Test B  — Primary Levins' B × MGnify KO/Mb  (fixes annotation method; swaps niche metric)
Test C  — MGnify biome_H × Primary AMRFinder cluster density  (fixes niche metric; swaps annotation)

Outputs:
  data/pgls_input_testA_soil.csv
  data/pgls_input_testB_hybrid_levinsB.csv
  data/pgls_input_testC_hybrid_biomeH.csv
  data/cross_dataset_validation_pgls.csv   (combined results, 9 rows)
"""

import os, subprocess, sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

DATA   = 'data'
TREE   = os.path.join(DATA, 'gtdb_bac_genus_pruned.tree')
R_BIN  = '/home/hmacgregor/r_env/bin/Rscript'
R_SCRIPT = 'scripts/pgls_mgnify_validation.R'

MIN_GENERA = 50   # minimum genera per test before running PGLS

# ── helpers ──────────────────────────────────────────────────────────────────

def zscore_col(series):
    vals = series.values.reshape(-1, 1)
    if np.nanstd(vals) < 1e-10:
        return np.full(len(vals), np.nan).flatten()
    return StandardScaler().fit_transform(vals).flatten()

def run_pgls(input_csv, label):
    out_csv = input_csv.replace('.csv', '_result.csv')
    result = subprocess.run(
        [R_BIN, R_SCRIPT, input_csv, TREE, out_csv],
        capture_output=True, text=True
    )
    print(f'\n--- [{label}] ---')
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    if result.returncode != 0:
        print('STDERR:', result.stderr[-500:])
        return None
    if not os.path.exists(out_csv):
        return None
    df = pd.read_csv(out_csv)
    df.insert(0, 'test', label)
    return df

# ── Test A: Soil + rhizosphere MAGs only ─────────────────────────────────────

print('\n===== Test A: Soil+rhizosphere MAGs =====')

SOIL_BIOMES = {'Soil', 'Tomato Rhizosphere', 'Maize Rhizosphere', 'Barley Rhizosphere'}

mag_meta = pd.read_csv(os.path.join(DATA, 'mgnify_mag_metal_traits.csv'),
                       usecols=['genome_id', 'biome_name', 'genus'])
soil_meta = mag_meta[mag_meta['biome_name'].isin(SOIL_BIOMES)].copy()
soil_meta['genus_lower'] = soil_meta['genus'].str.lower().str.strip()

# Biome Shannon entropy within soil subset
genus_biome = (soil_meta
               .groupby(['genus_lower', 'biome_name']).size()
               .unstack(fill_value=0))
mag_counts = genus_biome.sum(axis=1)
genus_biome_5 = genus_biome[mag_counts >= 5]
props = genus_biome_5.div(genus_biome_5.sum(axis=1), axis=0)
n_biomes = genus_biome_5.shape[1]
biome_H = -(props * np.log(props + 1e-300)).sum(axis=1)
biome_H_std = biome_H / np.log(n_biomes) if n_biomes > 1 else biome_H

soil_niche = pd.DataFrame({
    'genus_lower': biome_H_std.index,
    'biome_H_std': biome_H_std.values,
    'n_mags': mag_counts[biome_H_std.index].values
})
print(f'  Soil genera with ≥5 MAGs: {len(soil_niche)}')

# KO densities for soil MAGs
ko_dens = pd.read_csv(os.path.join(DATA, 'mgnify_mag_ko_density.csv'))
ko_dens['genus_lower'] = ko_dens['genus'].str.lower().str.strip()
soil_genome_ids = set(soil_meta['genome_id'])
soil_ko = ko_dens[ko_dens['genome_id'].isin(soil_genome_ids)].copy()
genus_ko_A = (soil_ko
              .groupby('genus_lower')[['ko_per_mb_total','ko_per_mb_tier1','ko_per_mb_tier2']]
              .mean().reset_index())

merged_A = (soil_niche
            .merge(genus_ko_A, on='genus_lower', how='inner')
            .dropna(subset=['biome_H_std'])
            .groupby('genus_lower', as_index=False)
            .agg({'biome_H_std':'mean','ko_per_mb_total':'mean',
                  'ko_per_mb_tier1':'mean','ko_per_mb_tier2':'mean'}))

for col in ['ko_per_mb_total','ko_per_mb_tier1','ko_per_mb_tier2']:
    merged_A[col+'_z'] = zscore_col(merged_A[col])

merged_A = merged_A.dropna(subset=['ko_per_mb_total_z'])
print(f'  Merged genera for PGLS: {len(merged_A)}')

path_A = os.path.join(DATA, 'pgls_input_testA_soil.csv')
merged_A[['genus_lower','biome_H_std','ko_per_mb_total_z',
          'ko_per_mb_tier1_z','ko_per_mb_tier2_z']].to_csv(path_A, index=False)

res_A = run_pgls(path_A, 'A_soil_only') if len(merged_A) >= MIN_GENERA else None

# ── Test B: Primary Levins' B × MGnify KO/Mb ─────────────────────────────────

print('\n===== Test B: Primary Levins B × MGnify KO/Mb =====')

genus_traits = pd.read_csv(os.path.join(DATA, 'genus_trait_table.csv'),
                           usecols=['genus_lower','mean_levins_B_std'])
genus_traits['genus_lower'] = genus_traits['genus_lower'].str.lower().str.strip()
genus_traits = genus_traits.dropna(subset=['mean_levins_B_std'])

# MGnify KO/Mb aggregated to genus level
genus_ko_B = (ko_dens
              .groupby('genus_lower')[['ko_per_mb_total','ko_per_mb_tier1','ko_per_mb_tier2']]
              .mean().reset_index())

merged_B = (genus_traits
            .merge(genus_ko_B, on='genus_lower', how='inner')
            .dropna()
            .groupby('genus_lower', as_index=False)
            .agg({'mean_levins_B_std':'mean','ko_per_mb_total':'mean',
                  'ko_per_mb_tier1':'mean','ko_per_mb_tier2':'mean'}))

merged_B = merged_B.rename(columns={'mean_levins_B_std': 'levins_B_std'})

for col in ['ko_per_mb_total','ko_per_mb_tier1','ko_per_mb_tier2']:
    merged_B[col+'_z'] = zscore_col(merged_B[col])

merged_B = merged_B.dropna(subset=['ko_per_mb_total_z'])
print(f'  Merged genera for PGLS: {len(merged_B)}')

# R script expects biome_H_std as response; rename for compatibility
merged_B['biome_H_std'] = merged_B['levins_B_std']

path_B = os.path.join(DATA, 'pgls_input_testB_hybrid_levinsB.csv')
merged_B[['genus_lower','biome_H_std','ko_per_mb_total_z',
          'ko_per_mb_tier1_z','ko_per_mb_tier2_z']].to_csv(path_B, index=False)

res_B = run_pgls(path_B, 'B_levinsB_mgnify_ko') if len(merged_B) >= MIN_GENERA else None

# ── Test C: MGnify biome_H × Primary AMRFinder cluster density ────────────────

print('\n===== Test C: MGnify biome_H × Primary AMRFinder cluster density =====')

# Primary AMRFinder: aggregate species_metal_amr to genus level
amr = pd.read_csv(os.path.join(DATA, 'species_metal_amr.csv'))
amr['genus_lower'] = amr['gtdb_genus'].str.lower().str.strip()

# Genome sizes for per-Mb normalization
gsize = pd.read_csv(os.path.join(DATA, 'genus_genome_size_gtdb.csv'))
gsize['genus_lower'] = gsize['genus_lower'].str.lower().str.strip()
gsize['genome_size_mb'] = gsize['mean_genome_size_bp'] / 1e6

amr_genus = (amr.groupby('genus_lower')
             .agg(clusters_per_genome=('clusters_per_genome','mean'),
                  n_defense=('n_defense_clusters','mean'),
                  n_homeostasis=('n_homeostasis_clusters','mean'))
             .reset_index())

amr_genus = amr_genus.merge(gsize[['genus_lower','genome_size_mb']], on='genus_lower', how='inner')
amr_genus['amr_per_mb_total']     = amr_genus['clusters_per_genome'] / amr_genus['genome_size_mb']
amr_genus['amr_per_mb_defense']   = amr_genus['n_defense']           / amr_genus['genome_size_mb']
amr_genus['amr_per_mb_homeostasis'] = amr_genus['n_homeostasis']     / amr_genus['genome_size_mb']

# MGnify biome_H (from full dataset, already computed)
biome_breadth = pd.read_csv(os.path.join(DATA, 'mgnify_genus_biome_breadth.csv'))
biome_breadth['genus_lower'] = biome_breadth['genus'].str.lower().str.strip()

merged_C = (biome_breadth[['genus_lower','biome_H_std']]
            .merge(amr_genus[['genus_lower','amr_per_mb_total',
                               'amr_per_mb_defense','amr_per_mb_homeostasis']],
                   on='genus_lower', how='inner')
            .dropna()
            .groupby('genus_lower', as_index=False)
            .agg({'biome_H_std':'mean','amr_per_mb_total':'mean',
                  'amr_per_mb_defense':'mean','amr_per_mb_homeostasis':'mean'}))

for col in ['amr_per_mb_total','amr_per_mb_defense','amr_per_mb_homeostasis']:
    merged_C[col+'_z'] = zscore_col(merged_C[col])

merged_C = merged_C.dropna(subset=['amr_per_mb_total_z'])
# Rename to match R script expectations (tier1 ≈ defense, tier2 ≈ homeostasis)
merged_C = merged_C.rename(columns={
    'amr_per_mb_total_z':       'ko_per_mb_total_z',
    'amr_per_mb_defense_z':     'ko_per_mb_tier1_z',
    'amr_per_mb_homeostasis_z': 'ko_per_mb_tier2_z',
})
print(f'  Merged genera for PGLS: {len(merged_C)}')

path_C = os.path.join(DATA, 'pgls_input_testC_hybrid_biomeH.csv')
merged_C[['genus_lower','biome_H_std','ko_per_mb_total_z',
          'ko_per_mb_tier1_z','ko_per_mb_tier2_z']].to_csv(path_C, index=False)

res_C = run_pgls(path_C, 'C_biomeH_amr_clusters') if len(merged_C) >= MIN_GENERA else None

# ── Combine and summarize ─────────────────────────────────────────────────────

print('\n===== Summary =====')
all_results = [r for r in [res_A, res_B, res_C] if r is not None]
if all_results:
    combined = pd.concat(all_results, ignore_index=True)
    out = os.path.join(DATA, 'cross_dataset_validation_pgls.csv')
    combined.to_csv(out, index=False)
    print(f'\nSaved: {out}')
    print(combined[['test','predictor','n_taxa','lambda','beta','p_value']].to_string(index=False))
else:
    print('No results to save.')
