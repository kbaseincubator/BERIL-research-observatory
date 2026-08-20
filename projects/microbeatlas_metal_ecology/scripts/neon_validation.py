#!/usr/bin/env python3
"""
neon_validation.py
-------------------
Validates the primary per-Mb metal homeostasis finding using NEON soil MAGs
as an independent niche breadth source.

NEON advantage over MGnify: all-soil, well-classified ecosystem subtypes
(grassland, tundra, forest, desert, wetlands) across 20+ US sites — no gut
contamination that dominated the MGnify biome Shannon analysis.

Niche breadth: Shannon entropy of ecosystem_subtype distribution per GTDB genus.

Two PGLS tests (gene annotations from existing data, joined by GTDB genus):
  Test D  — NEON ecosystem_H × Primary AMRFinder cluster density (bakta_amr isolates)
  Test E  — NEON ecosystem_H × MGnify eggNOG KO/Mb (kescience_mgnify MAGs)

Outputs:
  data/neon_genus_ecosystem_breadth.csv
  data/pgls_input_testD_neon_amr.csv
  data/pgls_input_testE_neon_mgnify.csv
  data/neon_validation_pgls.csv
"""

import os, subprocess, sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# ── Spark setup ───────────────────────────────────────────────────────────────
try:
    spark
except NameError:
    sys.path.append('/opt/conda/lib/python3.13/site-packages')
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()

from pyspark.sql import functions as F

DATA     = 'data'
TREE     = os.path.join(DATA, 'gtdb_bac_genus_pruned.tree')
R_BIN    = '/home/hmacgregor/r_env/bin/Rscript'
R_SCRIPT = 'scripts/pgls_mgnify_validation.R'
MIN_MAGS = 3    # min MAGs per genus per ecosystem_subtype to count that subtype
MIN_GEN  = 50   # min genera for PGLS

# ── helpers ───────────────────────────────────────────────────────────────────

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

# ── Step 1: Extract NEON ecosystem niche breadth from Spark ──────────────────

print('\n===== Step 1: NEON ecosystem niche breadth =====')

neon_sdf = spark.sql('''
    SELECT
        LOWER(TRIM(gtdbtk_genus))   AS genus_lower,
        ecosystem_subtype,
        total_bases                  AS genome_length_bp,
        gene_count,
        completeness,
        contamination
    FROM kbase.nmdc_neon.neon_mag_catalog
    WHERE bin_quality IN ('HQ', 'MQ')
      AND gtdbtk_genus IS NOT NULL
      AND gtdbtk_genus != ''
      AND gtdbtk_genus != 'Unclassified'
      AND completeness >= 50.0
      AND contamination <= 10.0
      AND ecosystem_subtype IS NOT NULL
      AND ecosystem_subtype NOT IN ('Unclassified', '')
      AND total_bases > 0
''')

neon_df = neon_sdf.toPandas()
print(f'NEON HQ/MQ MAGs passing filters: {len(neon_df)}')
print(f'Unique genera: {neon_df["genus_lower"].nunique()}')
print(f'Ecosystem subtypes: {sorted(neon_df["ecosystem_subtype"].unique())}')

# Compute Shannon entropy of ecosystem_subtype distribution per genus
genus_eco = (neon_df
             .groupby(['genus_lower', 'ecosystem_subtype'])
             .size()
             .unstack(fill_value=0))

mag_counts = genus_eco.sum(axis=1)
genus_eco_5 = genus_eco[mag_counts >= 3]
props = genus_eco_5.div(genus_eco_5.sum(axis=1), axis=0)
n_subtypes = genus_eco_5.shape[1]
eco_H = -(props * np.log(props + 1e-300)).sum(axis=1)
eco_H_std = eco_H / np.log(n_subtypes) if n_subtypes > 1 else eco_H

neon_niche = pd.DataFrame({
    'genus_lower': eco_H_std.index,
    'eco_H_std':   eco_H_std.values,
    'n_mags':      mag_counts[eco_H_std.index].values,
    'n_sites':     genus_eco_5[genus_eco_5 > 0].count(axis=1).values,
})
print(f'\nGenera with ≥3 MAGs: {len(neon_niche)}')
print(f'Ecosystem subtype count: {n_subtypes}')
print(neon_niche.describe())

neon_niche.to_csv(os.path.join(DATA, 'neon_genus_ecosystem_breadth.csv'), index=False)
print(f'Saved: data/neon_genus_ecosystem_breadth.csv')

# ── Step 2: Test D — NEON ecosystem_H × Primary AMRFinder cluster density ────

print('\n===== Test D: NEON ecosystem_H × Primary AMRFinder cluster density =====')

amr = pd.read_csv(os.path.join(DATA, 'species_metal_amr.csv'))
amr['genus_lower'] = amr['gtdb_genus'].str.lower().str.strip()
gsize = pd.read_csv(os.path.join(DATA, 'genus_genome_size_gtdb.csv'))
gsize['genus_lower'] = gsize['genus_lower'].str.lower().str.strip()
gsize['genome_size_mb'] = gsize['mean_genome_size_bp'] / 1e6

amr_genus = (amr.groupby('genus_lower')
             .agg(clusters_per_genome=('clusters_per_genome', 'mean'),
                  n_defense=('n_defense_clusters', 'mean'),
                  n_homeostasis=('n_homeostasis_clusters', 'mean'))
             .reset_index())
amr_genus = amr_genus.merge(gsize[['genus_lower', 'genome_size_mb']], on='genus_lower', how='inner')
amr_genus['amr_per_mb_total']       = amr_genus['clusters_per_genome'] / amr_genus['genome_size_mb']
amr_genus['amr_per_mb_defense']     = amr_genus['n_defense']           / amr_genus['genome_size_mb']
amr_genus['amr_per_mb_homeostasis'] = amr_genus['n_homeostasis']       / amr_genus['genome_size_mb']

merged_D = (neon_niche[['genus_lower', 'eco_H_std']]
            .merge(amr_genus[['genus_lower', 'amr_per_mb_total',
                               'amr_per_mb_defense', 'amr_per_mb_homeostasis']],
                   on='genus_lower', how='inner')
            .dropna()
            .groupby('genus_lower', as_index=False)
            .agg({'eco_H_std': 'mean', 'amr_per_mb_total': 'mean',
                  'amr_per_mb_defense': 'mean', 'amr_per_mb_homeostasis': 'mean'}))

for col in ['amr_per_mb_total', 'amr_per_mb_defense', 'amr_per_mb_homeostasis']:
    merged_D[col + '_z'] = zscore_col(merged_D[col])

merged_D = merged_D.dropna(subset=['amr_per_mb_total_z'])
merged_D = merged_D.rename(columns={
    'eco_H_std':                  'biome_H_std',
    'amr_per_mb_total_z':         'ko_per_mb_total_z',
    'amr_per_mb_defense_z':       'ko_per_mb_tier1_z',
    'amr_per_mb_homeostasis_z':   'ko_per_mb_tier2_z',
})
print(f'Genera for PGLS: {len(merged_D)}')

path_D = os.path.join(DATA, 'pgls_input_testD_neon_amr.csv')
merged_D[['genus_lower', 'biome_H_std', 'ko_per_mb_total_z',
          'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z']].to_csv(path_D, index=False)

res_D = run_pgls(path_D, 'D_neon_ecosysH_amr') if len(merged_D) >= MIN_GEN else None

# ── Step 3: Test E — NEON ecosystem_H × MGnify eggNOG KO/Mb ─────────────────

print('\n===== Test E: NEON ecosystem_H × MGnify eggNOG KO/Mb =====')

ko_dens = pd.read_csv(os.path.join(DATA, 'mgnify_mag_ko_density.csv'))
ko_dens['genus_lower'] = ko_dens['genus'].str.lower().str.strip()
genus_ko = (ko_dens
            .groupby('genus_lower')[['ko_per_mb_total', 'ko_per_mb_tier1', 'ko_per_mb_tier2']]
            .mean().reset_index())

merged_E = (neon_niche[['genus_lower', 'eco_H_std']]
            .merge(genus_ko, on='genus_lower', how='inner')
            .dropna()
            .groupby('genus_lower', as_index=False)
            .agg({'eco_H_std': 'mean', 'ko_per_mb_total': 'mean',
                  'ko_per_mb_tier1': 'mean', 'ko_per_mb_tier2': 'mean'}))

for col in ['ko_per_mb_total', 'ko_per_mb_tier1', 'ko_per_mb_tier2']:
    merged_E[col + '_z'] = zscore_col(merged_E[col])

merged_E = merged_E.dropna(subset=['ko_per_mb_total_z'])
merged_E = merged_E.rename(columns={'eco_H_std': 'biome_H_std'})
print(f'Genera for PGLS: {len(merged_E)}')

path_E = os.path.join(DATA, 'pgls_input_testE_neon_mgnify.csv')
merged_E[['genus_lower', 'biome_H_std', 'ko_per_mb_total_z',
          'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z']].to_csv(path_E, index=False)

res_E = run_pgls(path_E, 'E_neon_ecosysH_mgnify_ko') if len(merged_E) >= MIN_GEN else None

# ── Combine and summarise ─────────────────────────────────────────────────────

print('\n===== Summary =====')
all_results = [r for r in [res_D, res_E] if r is not None]
if all_results:
    combined = pd.concat(all_results, ignore_index=True)
    out = os.path.join(DATA, 'neon_validation_pgls.csv')
    combined.to_csv(out, index=False)
    print(f'\nSaved: {out}')
    print(combined[['test', 'predictor', 'n_taxa', 'lambda', 'beta', 'p_value']].to_string(index=False))
else:
    print('No results produced.')
