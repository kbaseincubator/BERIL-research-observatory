#!/usr/bin/env python3
"""
PCA ordination of top-20 KO presence/absence colored by Hg and pH,
with envfit arrows for top 5 environmental variables.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUT = CME / 'confound_results'

METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']

# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
raw = pd.read_csv(OUT / 'mba_otu_raw.csv')
top20 = raw.nsmallest(20, 'q_fdr')[['ko_id', 'metal']].reset_index(drop=True)
top_ko_ids = top20.ko_id.unique().tolist()
print(f"  Top 20 pairs use {len(top_ko_ids)} unique KOs")

mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
genome_meta = genome_meta.merge(env_full, on='genome_id', how='left', suffixes=('', '_dup'))
dup_cols = [c for c in genome_meta.columns if c.endswith('_dup')]
genome_meta.drop(columns=dup_cols, inplace=True)

ko_wide = mg[mg.ko_id.isin(top_ko_ids)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='inner').reset_index()
del mg, ko_wide
print(f"  Genomes with all data: {len(genome_df):,}")

# ── PCA on KO presence/absence ──────────────────────────────────────
print("Running PCA...")
ko_matrix = genome_df[top_ko_ids].values
pca = PCA(n_components=2)
pcs = pca.fit_transform(ko_matrix)
genome_df['PC1'] = pcs[:, 0]
genome_df['PC2'] = pcs[:, 1]
var_exp = pca.explained_variance_ratio_ * 100
print(f"  PC1: {var_exp[0]:.1f}%, PC2: {var_exp[1]:.1f}%")

# ── Envfit: correlate env variables with PC axes ─────────────────────
print("Computing envfit arrows...")
envfit_vars = ['PF1_Hg', 'ph_h2o', 'organic_carbon_density',
               'mean_annual_temp_C', 'mean_annual_precip_mm', 'elevation_m',
               'PF1_Cd', 'PF1_Cu', 'PF1_As', 'clay_pct']
envfit_labels = {
    'PF1_Hg': 'Hg', 'PF1_Cd': 'Cd', 'PF1_Cu': 'Cu', 'PF1_As': 'As',
    'ph_h2o': 'pH', 'organic_carbon_density': 'Organic C',
    'mean_annual_temp_C': 'Temperature', 'mean_annual_precip_mm': 'Precipitation',
    'elevation_m': 'Elevation', 'clay_pct': 'Clay %',
}

envfit_results = []
for var in envfit_vars:
    if var not in genome_df.columns:
        continue
    vals = pd.to_numeric(genome_df[var], errors='coerce').values
    mask = np.isfinite(vals)
    if mask.sum() < 100:
        continue
    r1, p1 = stats.pearsonr(pcs[mask, 0], vals[mask])
    r2, p2 = stats.pearsonr(pcs[mask, 1], vals[mask])
    r2_total = r1**2 + r2**2
    envfit_results.append({
        'var': var, 'label': envfit_labels.get(var, var),
        'r_PC1': r1, 'r_PC2': r2, 'R2': r2_total,
        'is_metal': var.startswith('PF1_'),
    })

envfit_df = pd.DataFrame(envfit_results).sort_values('R2', ascending=False)
print(envfit_df[['label', 'R2', 'r_PC1', 'r_PC2']].to_string(index=False))

# Top 5 by R²
top5_env = envfit_df.head(5)

# ── Figure ───────────────────────────────────────────────────────────
print("\nMaking figure...")
fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

subsample_n = min(4000, len(genome_df))
rng = np.random.RandomState(42)
idx = rng.choice(len(genome_df), subsample_n, replace=False)

for ax_i, (ax, color_var, cmap_name, label, vmin, vmax) in enumerate([
    (axes[0], 'PF1_Hg', 'YlOrRd', 'Hg (mg/kg)', None, None),
    (axes[1], 'ph_h2o', 'RdYlBu_r', 'Soil pH', None, None),
]):
    vals = pd.to_numeric(genome_df[color_var], errors='coerce').values
    mask = np.isfinite(vals[idx])
    plot_idx = idx[mask]

    if vmin is None:
        vmin = np.percentile(vals[plot_idx], 2)
    if vmax is None:
        vmax = np.percentile(vals[plot_idx], 98)

    sc = ax.scatter(pcs[plot_idx, 0], pcs[plot_idx, 1],
                    c=vals[plot_idx], cmap=cmap_name,
                    vmin=vmin, vmax=vmax,
                    s=3, alpha=0.4, rasterized=True)
    cb = plt.colorbar(sc, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label(label, fontsize=10)

    # Envfit arrows
    arrow_scale = max(abs(pcs[plot_idx, 0]).max(), abs(pcs[plot_idx, 1]).max()) * 0.7
    for _, row in top5_env.iterrows():
        dx = row.r_PC1 * arrow_scale * np.sqrt(row.R2) / np.sqrt(max(row.r_PC1**2 + row.r_PC2**2, 1e-10))
        dy = row.r_PC2 * arrow_scale * np.sqrt(row.R2) / np.sqrt(max(row.r_PC1**2 + row.r_PC2**2, 1e-10))
        color = '#d62728' if row.is_metal else '#1f77b4'
        ax.annotate('', xy=(dx, dy), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        ax.text(dx * 1.12, dy * 1.12, row.label,
                fontsize=7, ha='center', va='center', color=color,
                fontweight='bold')

    ax.set_xlabel(f'PC1 ({var_exp[0]:.1f}%)', fontsize=10)
    ax.set_ylabel(f'PC2 ({var_exp[1]:.1f}%)', fontsize=10)
    panel = chr(65 + ax_i)
    ax.set_title(f'({panel}) Colored by {label}', fontsize=11)
    ax.axhline(0, color='grey', lw=0.3)
    ax.axvline(0, color='grey', lw=0.3)

# Legend for arrows
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='#d62728', lw=1.5, label='Metal (envfit)'),
    Line2D([0], [0], color='#1f77b4', lw=1.5, label='Environment (envfit)'),
]
axes[1].legend(handles=legend_elements, loc='lower right', fontsize=7)

fig.suptitle('KO Presence/Absence PCA — Top 20 Metal-Associated KOs', fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(OUT / 'ko_pca_ordination.pdf', dpi=300, bbox_inches='tight')
fig.savefig(OUT / 'ko_pca_ordination.png', dpi=150, bbox_inches='tight')
print(f"  Saved to {OUT / 'ko_pca_ordination.pdf'}")
print("DONE")
