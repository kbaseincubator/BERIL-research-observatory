#!/usr/bin/env python3
"""
GrowDB DRAM traits × metal associations.
2,093 MAGs with metabolic traits, 163 samples with lat/lon.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.spatial import cKDTree
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUT = CME / 'confound_results'

METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
METAL_SHORT = {'PF1_Hg': 'Hg', 'PF1_As': 'As', 'PF1_Cu': 'Cu',
               'PF1_Cr': 'Cr', 'PF1_Cd': 'Cd', 'PF1_Pb': 'Pb'}

# ── Export from Spark ────────────────────────────────────────────────
print("Loading GrowDB data from Spark...")
from berdl_notebook_utils import get_spark_session
spark = get_spark_session()

# DRAM traits
dram = spark.sql("SELECT * FROM msyscolo_grow.growdb_dram_traits").toPandas()
print(f"  DRAM traits: {len(dram)} MAGs")

# Sample metadata (lat/lon)
sample_meta = spark.sql("""
    SELECT SampleName, Latitude, Longitude
    FROM msyscolo_grow.growdb_sample_metadata
    WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
""").toPandas()
sample_meta['Latitude'] = pd.to_numeric(sample_meta['Latitude'], errors='coerce')
sample_meta['Longitude'] = pd.to_numeric(sample_meta['Longitude'], errors='coerce')
sample_meta = sample_meta.dropna(subset=['Latitude', 'Longitude'])
print(f"  Samples with coords: {len(sample_meta)}")

# MAG inventory (links genome to sample)
mag_inv = spark.sql("SELECT genome, Study FROM msyscolo_grow.growdb_mag_inventory").toPandas()

# Taxonomy
tax = spark.sql("SELECT * FROM msyscolo_grow.growdb_taxonomy_gtdb").toPandas()
print(f"  Taxonomy: {len(tax)} MAGs")

spark.stop()

# ── Parse sample from genome name ────────────────────────────────────
print("\nLinking MAGs to samples...")
# Genome names follow pattern: samplename_suffix_bin.XX
# The sample name is embedded in the genome name.
# Try matching by checking which sample names are substrings of genome names.
genome_sample = []
for _, row in dram.iterrows():
    genome = row['genome']
    matched = None
    for _, smeta in sample_meta.iterrows():
        sname = smeta['SampleName']
        if sname in genome:
            matched = sname
            break
    if matched:
        genome_sample.append({
            'genome': genome,
            'SampleName': matched,
            'lat': sample_meta[sample_meta.SampleName == matched].Latitude.values[0],
            'lon': sample_meta[sample_meta.SampleName == matched].Longitude.values[0],
        })

gs_df = pd.DataFrame(genome_sample)
print(f"  MAGs linked to samples with coords: {len(gs_df)}/{len(dram)}")

if len(gs_df) < 50:
    print("  Too few geolocated MAGs for meaningful analysis.")
    print("DONE (insufficient data)")
    sys.exit(0)

# ── Spatial join to metal concentrations ─────────────────────────────
print("\nSpatial join to metal concentrations...")
# Use the envdbs metal data
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
# We need lat/lon → metal mapping. Use existing MGnify genome coords as reference.
projects_data = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
mg = pd.read_parquet(projects_data / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'latitude', 'longitude'] + METALS)
mg_coords = mg.drop_duplicates('genome_id')[['latitude', 'longitude'] + METALS].dropna()

# KDTree nearest-neighbor join
tree = cKDTree(np.deg2rad(mg_coords[['latitude', 'longitude']].values))
growdb_coords = np.deg2rad(gs_df[['lat', 'lon']].values)
dists, idxs = tree.query(growdb_coords)
EARTH_R = 6371
max_dist_km = 50

gs_df['nn_dist_km'] = dists * EARTH_R
gs_df['nn_idx'] = idxs
matched = gs_df[gs_df.nn_dist_km < max_dist_km].copy()
for metal in METALS:
    matched[metal] = mg_coords[metal].values[matched.nn_idx.values]
print(f"  MAGs within {max_dist_km}km of MGnify genome: {len(matched)}/{len(gs_df)}")

# Merge DRAM traits
merged = matched.merge(dram, on='genome', how='left')

# Parse taxonomy for genus
if 'Taxonomy' in merged.columns:
    merged['genus'] = merged.Taxonomy.str.split(';').str[-2].str.strip()
    merged['genus'] = merged.genus.str.replace(r'^g__', '', regex=True)

# DRAM trait columns
trait_cols = ['Aerobic', 'Microaerophillic', 'Photosynthetic', 'Methanotroph',
              'Nitrifier', 'N_reducer', 'S_Reducer', 'S_Oxidizer',
              'Obligate_Fermenter', 'DNRA', 'Iron_Oxidizer']

# Convert TRUE/FALSE strings to boolean
for col in trait_cols:
    if col in merged.columns:
        merged[col] = merged[col].map({'TRUE': 1, 'FALSE': 0, True: 1, False: 0})
        merged[col] = pd.to_numeric(merged[col], errors='coerce')

print(f"\n  Final dataset: {len(merged)} MAGs with traits + metals")

# ── Test trait × metal associations ──────────────────────────────────
print("\nTesting trait × metal associations...")
results = []
for trait in trait_cols:
    if trait not in merged.columns:
        continue
    t_vals = merged[trait].values
    if np.nanstd(t_vals) == 0:
        continue

    for metal in METALS:
        m_vals = pd.to_numeric(merged[metal], errors='coerce').values
        mask = np.isfinite(m_vals) & np.isfinite(t_vals)
        if mask.sum() < 20:
            continue

        rho, p = stats.spearmanr(t_vals[mask], m_vals[mask])
        # Point-biserial for binary traits
        if len(np.unique(t_vals[mask])) == 2:
            t_stat, p_pb = stats.pointbiserialr(t_vals[mask].astype(int), m_vals[mask])
        else:
            t_stat, p_pb = rho, p

        results.append({
            'trait': trait,
            'metal': METAL_SHORT[metal],
            'rho': rho,
            'p': p,
            'n': mask.sum(),
            'trait_prev': t_vals[mask].mean(),
        })

res_df = pd.DataFrame(results)
if len(res_df) > 0:
    _, fdr, _, _ = multipletests(res_df.p, method='fdr_bh')
    res_df['q'] = fdr
    res_df.to_csv(OUT / 'growdb_dram_metal_associations.csv', index=False)

    n_sig = (res_df.q < 0.05).sum()
    print(f"\n{'='*60}")
    print("RESULTS: GrowDB DRAM Traits × Metal Associations")
    print(f"{'='*60}")
    print(f"  MAGs analyzed: {len(merged)}")
    print(f"  Trait × metal pairs tested: {len(res_df)}")
    print(f"  Significant (FDR<0.05): {n_sig}")

    if n_sig > 0:
        print(f"\n  Significant associations:")
        for _, r in res_df[res_df.q < 0.05].sort_values('q').iterrows():
            print(f"    {r.trait} × {r.metal}: ρ={r.rho:+.3f} q={r.q:.2e} "
                  f"(n={r.n}, prev={r.trait_prev:.1%})")
    else:
        print("\n  No significant associations found.")
        print("  Top 5 by p-value:")
        for _, r in res_df.nsmallest(5, 'p').iterrows():
            print(f"    {r.trait} × {r.metal}: ρ={r.rho:+.3f} p={r.p:.3f} q={r.q:.3f} "
                  f"(n={r.n})")

    # Figure
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot = res_df.pivot(index='trait', columns='metal', values='rho')
    pivot = pivot.reindex(columns=['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb'])
    im = ax.imshow(pivot.values, cmap='RdBu_r', vmin=-0.3, vmax=0.3, aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)
    plt.colorbar(im, ax=ax, label='Spearman ρ', shrink=0.8)

    # Mark significant cells
    q_pivot = res_df.pivot(index='trait', columns='metal', values='q')
    q_pivot = q_pivot.reindex(columns=['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb'])
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            if not np.isnan(q_pivot.values[i, j]) and q_pivot.values[i, j] < 0.05:
                ax.text(j, i, '*', ha='center', va='center', fontsize=14, fontweight='bold')

    ax.set_title(f'GrowDB DRAM Traits × Metal Concentrations\n({len(merged)} MAGs)')
    plt.tight_layout()
    fig.savefig(OUT / 'growdb_dram_heatmap.png', dpi=150, bbox_inches='tight')
    fig.savefig(OUT / 'growdb_dram_heatmap.pdf', dpi=300, bbox_inches='tight')
    print(f"\n  Figure saved to {OUT / 'growdb_dram_heatmap.pdf'}")

print("DONE")
