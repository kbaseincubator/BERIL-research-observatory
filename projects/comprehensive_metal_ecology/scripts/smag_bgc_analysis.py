#!/usr/bin/env python3
"""
SMAG BGC (biosynthetic gene cluster) × metal/environment analysis.
Uses 40K soil MAGs from refdata.smag with 43K antiSMASH BGC predictions.
Tests whether BGC richness and specific BGC types (siderophores, NRPS, etc.)
associate with soil metal concentrations and environmental variables,
using within-genus inverse-variance meta-analysis.
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
PKOM = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
OUT = CME / 'confound_results'
OUT.mkdir(parents=True, exist_ok=True)

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 5
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
ENV_COLS = ['sg_phh2o_0_5cm_mean', 'sg_soc_0_5cm_mean', 'sg_clay_0_5cm_mean',
            'clim_t2m', 'clim_prectotcorr']
ENV_LABELS = {'sg_phh2o_0_5cm_mean': 'pH', 'sg_soc_0_5cm_mean': 'SOC',
              'sg_clay_0_5cm_mean': 'Clay%', 'clim_t2m': 'Temp', 'clim_prectotcorr': 'Precip'}

# ── Step 1: Load SMAG data from Spark ───────────────────────────────
print("Step 1: Loading SMAG data from Spark...")

try:
    from berdl_notebook_utils import get_spark_session
    spark = get_spark_session()
except Exception as e:
    print(f"Spark init error: {e}")
    sys.exit(1)

# MAG metadata with coords and taxonomy
msm = spark.table("refdata.smag.mag_sample_map").toPandas()
print(f"  mag_sample_map: {len(msm)} MAGs")

# BGC predictions
bgc = spark.table("refdata.smag.bgc").toPandas()
print(f"  BGC predictions: {len(bgc)}")

# Environment data (SoilGrids + climate)
env = spark.table("refdata.smag.sample_environment").toPandas()
print(f"  sample_environment: {len(env)} samples")

spark.stop()

# ── Step 2: Filter to soil MAGs with coordinates ────────────────────
print("\nStep 2: Filtering to soil MAGs with coordinates...")

soil_ecosystems = ['Agricultural Land', 'Forest', 'Grassland', 'Tundra',
                   'Shrubland', 'Bare Land', 'Soil', 'tundra biome']
msm_soil = msm[msm.ecosystem.isin(soil_ecosystems) & msm.lat.notna() & msm.lon.notna()].copy()
print(f"  Soil MAGs with coords: {len(msm_soil)}")

# Quality filter: completeness >= 50, contamination <= 10
msm_soil = msm_soil[
    (msm_soil.checkm2_completeness >= 50) &
    (msm_soil.checkm2_contamination <= 10)
].copy()
print(f"  After quality filter (comp≥50, cont≤10): {len(msm_soil)}")

# ── Step 3: Spatial join to metal concentrations ────────────────────
print("\nStep 3: Spatial join to FOREGS/GEMAS metal concentrations...")

# Load MGnify metal data as reference points
mgnify_meta = pd.read_parquet(
    PKOM / 'mgnify_all_ko_matrix.parquet',
    columns=['genome_id', 'latitude', 'longitude'] + METALS
).drop_duplicates('genome_id')

metal_sites = mgnify_meta.dropna(subset=['latitude', 'longitude'] + METALS)
metal_coords = metal_sites[['latitude', 'longitude']].values
metal_tree = cKDTree(np.radians(metal_coords) * 6371)

smag_coords = msm_soil[['lat', 'lon']].values.astype(float)
smag_tree_pts = np.radians(smag_coords) * 6371

dists, idxs = metal_tree.query(smag_tree_pts, k=1)
MAX_DIST_KM = 50
mask = dists < MAX_DIST_KM

msm_matched = msm_soil.iloc[mask].copy()
metal_matched = metal_sites.iloc[idxs[mask]].reset_index(drop=True)
for col in METALS:
    msm_matched[col] = metal_matched[col].values

print(f"  MAGs within {MAX_DIST_KM}km of metal data: {len(msm_matched)}")

# ── Step 4: Join environment data ───────────────────────────────────
print("\nStep 4: Joining environment data...")

# env has sample-level data; link via sample column
env_dedup = env.drop_duplicates('sample')[['sample'] + ENV_COLS].copy()
for c in ENV_COLS:
    env_dedup[c] = pd.to_numeric(env_dedup[c], errors='coerce')

# Extract sample from MAG's sample column
msm_matched = msm_matched.merge(env_dedup, on='sample', how='left', suffixes=('', '_env'))

env_complete = msm_matched.dropna(subset=ENV_COLS)
print(f"  MAGs with complete env data: {len(env_complete)}")

# ── Step 5: Build BGC feature matrix ───────────────────────────────
print("\nStep 5: Building BGC feature matrix...")

# Count BGCs per MAG by type
bgc_in_dataset = bgc[bgc.mag.isin(env_complete.mag_id)].copy()
print(f"  BGCs in matched MAGs: {len(bgc_in_dataset)}")

# Total BGC count per MAG
bgc_total = bgc_in_dataset.groupby('mag').size().rename('bgc_total')

# Count per BGC class
bgc_class_counts = bgc_in_dataset.pivot_table(
    index='mag', columns='big_scape_class', aggfunc='size', fill_value=0
)
bgc_class_counts.columns = [f'bgc_{c.replace("-", "_").replace(" ", "_")}' for c in bgc_class_counts.columns]

# Count per product type (top types + siderophore)
important_products = ['terpene', 'NRPS', 'NRPS-like', 'T1PKS', 'T3PKS',
                      'siderophore', 'RiPP-like', 'arylpolyene', 'betalactone',
                      'ectoine', 'ladderane', 'phosphonate']
for prod in important_products:
    col = f'bgc_prod_{prod.replace("-", "_")}'
    bgc_class_counts[col] = bgc_in_dataset[
        bgc_in_dataset.product_prediction.str.contains(prod, na=False, case=False)
    ].groupby('mag').size().reindex(bgc_class_counts.index, fill_value=0)

# Presence/absence for siderophore (key metal-relevant feature)
bgc_class_counts['has_siderophore'] = (bgc_class_counts.get('bgc_prod_siderophore', 0) > 0).astype(int)

# Merge with metadata
genome_df = env_complete.set_index('mag_id').copy()
genome_df['bgc_total'] = bgc_total.reindex(genome_df.index, fill_value=0)
for col in bgc_class_counts.columns:
    genome_df[col] = bgc_class_counts[col].reindex(genome_df.index, fill_value=0)

genome_df = genome_df.reset_index()
genome_df.rename(columns={'index': 'mag_id'} if 'index' in genome_df.columns else {}, inplace=True)
if 'mag_id' not in genome_df.columns and genome_df.index.name == 'mag_id':
    genome_df = genome_df.reset_index()

# Extract genus
genome_df['genus'] = genome_df['gtdb202_genus'].fillna('g__')
genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index.tolist()
usable_genera = [g for g in usable_genera if g != 'g__']
genus_idx = {g: genome_df.index[genome_df.genus == g].values.astype(int) for g in usable_genera}

print(f"  Final dataset: {len(genome_df)} MAGs, {len(usable_genera)} usable genera")
print(f"  BGC features: {[c for c in genome_df.columns if c.startswith('bgc_') or c == 'has_siderophore']}")

# ── Step 6: Within-genus meta-analysis ──────────────────────────────
print("\nStep 6: Testing BGC × metal and BGC × environment associations...")

def within_genus_meta(genome_df, genus_idx, feature_col, response_col, covariates=None):
    feat_vals = pd.to_numeric(genome_df[feature_col], errors='coerce').values
    resp_vals = pd.to_numeric(genome_df[response_col], errors='coerce').values
    effects = []

    for genus, idx in genus_idx.items():
        feat = feat_vals[idx]
        resp = resp_vals[idx]
        mask = np.isfinite(resp) & np.isfinite(feat)

        if covariates:
            for c in covariates:
                if c in genome_df.columns:
                    cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx]
                    mask &= np.isfinite(cv)

        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue
        if feat[mask].std() < 1e-10:
            continue

        feat_m, resp_m = feat[mask], resp[mask]
        n = mask.sum()

        if covariates:
            from numpy.linalg import lstsq
            cov_matrix = np.column_stack([
                pd.to_numeric(genome_df[c], errors='coerce').values[idx][mask]
                for c in covariates if c in genome_df.columns
            ])
            if n < cov_matrix.shape[1] + 3:
                continue
            X = np.column_stack([np.ones(n), cov_matrix])
            resp_m = resp_m - X @ lstsq(X, resp_m, rcond=None)[0]
            feat_resid = feat_m - X @ lstsq(X, feat_m, rcond=None)[0]
            if feat_resid.std() < 1e-10 or resp_m.std() < 1e-10:
                continue
            rho, _ = stats.pearsonr(feat_resid, resp_m)
        else:
            rho, _ = stats.spearmanr(feat_m, resp_m)

        z = np.arctanh(np.clip(rho, -0.999, 0.999))
        se = 1.0 / np.sqrt(n - 3) if n > 3 else 1.0
        effects.append((z, se, n))

    if len(effects) < MIN_GENERA:
        return None

    zs = np.array([e[0] for e in effects])
    ses = np.array([e[1] for e in effects])
    ws = 1.0 / ses**2
    z_meta = np.sum(ws * zs) / np.sum(ws)
    se_meta = 1.0 / np.sqrt(np.sum(ws))
    p_meta = 2 * stats.norm.sf(abs(z_meta / se_meta))
    rho_meta = np.tanh(z_meta)
    return {'meta_rho': rho_meta, 'meta_p': p_meta, 'n_genera': len(effects)}

# BGC features to test
bgc_features = ['bgc_total', 'has_siderophore']
bgc_features += [c for c in genome_df.columns if c.startswith('bgc_') and c != 'bgc_total']
bgc_features = [f for f in bgc_features if genome_df[f].std() > 0.01]

# Response variables: metals + environment
response_vars = METALS + ENV_COLS
response_labels = {m: m.replace('PF1_', '') for m in METALS}
response_labels.update(ENV_LABELS)

all_results = []
for feat in bgc_features:
    for resp in response_vars:
        is_metal = resp in METALS
        other_covs = [m for m in METALS if m != resp] if is_metal else METALS
        env_covs = ENV_COLS if is_metal else [c for c in ENV_COLS if c != resp]

        raw = within_genus_meta(genome_df, genus_idx, feat, resp)
        if raw is None:
            continue

        # Controlled: genome_size + other metals + env
        ctrl_covs = ['genome_size'] + other_covs + env_covs
        ctrl = within_genus_meta(genome_df, genus_idx, feat, resp, covariates=ctrl_covs)

        all_results.append({
            'bgc_feature': feat,
            'response': resp,
            'response_label': response_labels.get(resp, resp),
            'is_metal': is_metal,
            'raw_rho': raw['meta_rho'],
            'raw_p': raw['meta_p'],
            'raw_n_genera': raw['n_genera'],
            'ctrl_rho': ctrl['meta_rho'] if ctrl else np.nan,
            'ctrl_p': ctrl['meta_p'] if ctrl else np.nan,
            'ctrl_n_genera': ctrl['n_genera'] if ctrl else 0,
        })

res_df = pd.DataFrame(all_results)

if len(res_df) == 0:
    print("No testable BGC × response pairs found.")
    sys.exit(0)

# FDR correction (handle NaN p-values)
raw_valid = res_df.raw_p.notna()
res_df['raw_q'] = np.nan
if raw_valid.sum() > 0:
    _, fdr_vals, _, _ = multipletests(res_df.loc[raw_valid, 'raw_p'], method='fdr_bh')
    res_df.loc[raw_valid, 'raw_q'] = fdr_vals

ctrl_valid = res_df.ctrl_p.notna()
res_df['ctrl_q'] = np.nan
if ctrl_valid.sum() > 0:
    _, fdr_vals, _, _ = multipletests(res_df.loc[ctrl_valid, 'ctrl_p'], method='fdr_bh')
    res_df.loc[ctrl_valid, 'ctrl_q'] = fdr_vals

res_df.to_csv(OUT / 'smag_bgc_associations.csv', index=False)

# ── Results ──────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("RESULTS: SMAG BGC × Metal/Environment Associations")
print(f"{'='*60}")
print(f"  MAGs analyzed: {len(genome_df)}")
print(f"  Usable genera: {len(usable_genera)}")
print(f"  BGC features tested: {res_df.bgc_feature.nunique()}")
print(f"  Pairs tested: {len(res_df)}")

# Separate metal vs env
metal_res = res_df[res_df.is_metal]
env_res = res_df[~res_df.is_metal]

print(f"\n  --- Metal associations ---")
print(f"  Pairs tested: {len(metal_res)}")
n_raw_metal = (metal_res.raw_q < 0.05).sum()
n_ctrl_metal = (metal_res.ctrl_q < 0.05).sum()
print(f"  Raw significant (FDR<0.05): {n_raw_metal}")
print(f"  Controlled survivors: {n_ctrl_metal}")

if n_raw_metal > 0:
    top = metal_res.nsmallest(10, 'raw_p')
    for _, r in top.iterrows():
        surv = "***" if r.ctrl_q < 0.05 else ""
        print(f"    {r.bgc_feature} × {r.response_label}: ρ={r.raw_rho:+.3f} q={r.raw_q:.2e} "
              f"(ctrl ρ={r.ctrl_rho:+.3f} q={r.ctrl_q:.2e}) {surv}")

print(f"\n  --- Environment associations ---")
print(f"  Pairs tested: {len(env_res)}")
n_raw_env = (env_res.raw_q < 0.05).sum()
n_ctrl_env = (env_res.ctrl_q < 0.05).sum()
print(f"  Raw significant (FDR<0.05): {n_raw_env}")
print(f"  Controlled survivors: {n_ctrl_env}")

if n_raw_env > 0:
    top = env_res.nsmallest(10, 'raw_p')
    for _, r in top.iterrows():
        surv = "***" if r.ctrl_q < 0.05 else ""
        print(f"    {r.bgc_feature} × {r.response_label}: ρ={r.raw_rho:+.3f} q={r.raw_q:.2e} "
              f"(ctrl ρ={r.ctrl_rho:+.3f} q={r.ctrl_q:.2e}) {surv}")

# Siderophore results specifically
print(f"\n  --- Siderophore-specific results ---")
sid_res = res_df[res_df.bgc_feature.str.contains('siderophore')]
if len(sid_res) > 0:
    for _, r in sid_res.iterrows():
        print(f"    {r.bgc_feature} × {r.response_label}: raw ρ={r.raw_rho:+.3f} q={r.raw_q:.2e} | "
              f"ctrl ρ={r.ctrl_rho:+.3f} q={r.ctrl_q:.2e}")

# ── Figure ───────────────────────────────────────────────────────────
print("\nCreating figure...")

fig, axes = plt.subplots(1, 3, figsize=(16, 6))

# (A) Heatmap of raw effect sizes for key BGC types × metals
ax = axes[0]
key_features = ['bgc_total', 'has_siderophore', 'bgc_NRPS', 'bgc_Terpene',
                'bgc_RiPPs', 'bgc_PKSI', 'bgc_Others', 'bgc_PKSother']
key_features = [f for f in key_features if f in res_df.bgc_feature.unique()]
metal_labels = [m.replace('PF1_', '') for m in METALS]

heatmap_data = np.full((len(key_features), len(METALS)), np.nan)
sig_mask = np.full_like(heatmap_data, False, dtype=bool)
for i, feat in enumerate(key_features):
    for j, metal in enumerate(METALS):
        row = res_df[(res_df.bgc_feature == feat) & (res_df.response == metal)]
        if len(row) > 0:
            heatmap_data[i, j] = row.iloc[0].raw_rho
            sig_mask[i, j] = row.iloc[0].raw_q < 0.05

im = ax.imshow(heatmap_data, cmap='RdBu_r', vmin=-0.3, vmax=0.3, aspect='auto')
ax.set_xticks(range(len(metal_labels)))
ax.set_xticklabels(metal_labels, fontsize=9)
ax.set_yticks(range(len(key_features)))
ax.set_yticklabels([f.replace('bgc_', '').replace('_', ' ') for f in key_features], fontsize=8)
for i in range(len(key_features)):
    for j in range(len(METALS)):
        if sig_mask[i, j]:
            ax.text(j, i, '*', ha='center', va='center', fontsize=14, fontweight='bold')
plt.colorbar(im, ax=ax, shrink=0.7, label='ρ')
ax.set_title('(A) BGC × Metal (raw)')

# (B) Heatmap for environment
ax = axes[1]
heatmap_env = np.full((len(key_features), len(ENV_COLS)), np.nan)
sig_env = np.full_like(heatmap_env, False, dtype=bool)
for i, feat in enumerate(key_features):
    for j, env_var in enumerate(ENV_COLS):
        row = res_df[(res_df.bgc_feature == feat) & (res_df.response == env_var)]
        if len(row) > 0:
            heatmap_env[i, j] = row.iloc[0].raw_rho
            sig_env[i, j] = row.iloc[0].raw_q < 0.05

im2 = ax.imshow(heatmap_env, cmap='RdBu_r', vmin=-0.3, vmax=0.3, aspect='auto')
ax.set_xticks(range(len(ENV_COLS)))
ax.set_xticklabels([ENV_LABELS[c] for c in ENV_COLS], fontsize=9)
ax.set_yticks(range(len(key_features)))
ax.set_yticklabels([f.replace('bgc_', '').replace('_', ' ') for f in key_features], fontsize=8)
for i in range(len(key_features)):
    for j in range(len(ENV_COLS)):
        if sig_env[i, j]:
            ax.text(j, i, '*', ha='center', va='center', fontsize=14, fontweight='bold')
plt.colorbar(im2, ax=ax, shrink=0.7, label='ρ')
ax.set_title('(B) BGC × Environment (raw)')

# (C) Bar: raw vs controlled significant counts
ax = axes[2]
categories = ['Metal\n(raw)', 'Metal\n(ctrl)', 'Env\n(raw)', 'Env\n(ctrl)']
counts = [n_raw_metal, n_ctrl_metal, n_raw_env, n_ctrl_env]
colors = ['#aec7e8', '#d62728', '#aec7e8', '#d62728']
bars = ax.bar(categories, counts, color=colors)
for bar, cnt in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            str(cnt), ha='center', fontsize=11)
ax.set_ylabel('Significant associations (FDR<0.05)')
ax.set_title('(C) Raw vs Controlled')

plt.suptitle(f'SMAG: BGC × Metal/Environment ({len(genome_df)} MAGs, {len(usable_genera)} genera)',
             fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(OUT / 'smag_bgc_associations.png', dpi=150, bbox_inches='tight')
fig.savefig(OUT / 'smag_bgc_associations.pdf', dpi=300, bbox_inches='tight')
print(f"  Figure saved to {OUT / 'smag_bgc_associations.pdf'}")
print("DONE")
