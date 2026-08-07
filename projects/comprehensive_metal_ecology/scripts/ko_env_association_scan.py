#!/usr/bin/env python3
"""
Within-genus KO × environment association scan for 26 target KOs.
Tests each KO against pH, OC, clay, temp, precip with full env+metal control.
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
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUT = CME / 'confound_results'

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 8
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']

ENV_RESPONSES = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
                 'mean_annual_temp_C', 'mean_annual_precip_mm']

TARGET_KOS = {
    'K01546': 'kdpA', 'K01547': 'kdpB', 'K01548': 'kdpC',
    'K07646': 'kdpD', 'K07667': 'kdpE',
    'K04651': 'hypA', 'K04652': 'hypB', 'K04653': 'hypC',
    'K04654': 'hypD', 'K04655': 'hypE', 'K04656': 'hypF',
    'K06188': 'aqpZ', 'K01531': 'mgtA', 'K07241': 'hoxN/nixA',
    'K08364': 'merP', 'K01535': 'PMA1/PMA2', 'K01114': 'plc',
    'K05275': 'pdxDH', 'K06215': 'pdxS/pdx1',
    'K07497': 'IS_transposase1', 'K07486': 'IS_transposase2',
    'K07481': 'IS5_transposase',
    'K15461': 'mnmC', 'K06213': 'mgtE', 'K02863': 'rplA', 'K03498': 'trkH',
}

# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
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

target_ko_ids = list(TARGET_KOS.keys())
ko_wide = mg[mg.ko_id.isin(target_ko_ids)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
del mg, ko_wide

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index.tolist()
genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera}
print(f"  Genomes: {len(genome_df):,}, usable genera: {len(usable_genera)}")

available_kos = [k for k in target_ko_ids if k in genome_df.columns]
print(f"  Target KOs available: {len(available_kos)}/{len(target_ko_ids)}")

# ── Within-genus meta-analysis ───────────────────────────────────────
def within_genus_meta(genome_df, genus_idx, ko_id, response_col, covariates=None):
    ko_vals = genome_df[ko_id].values
    resp_vals = pd.to_numeric(genome_df[response_col], errors='coerce').values

    effects = []
    for genus, idx in genus_idx.items():
        ko = ko_vals[idx]
        resp = resp_vals[idx]
        mask = np.isfinite(resp)

        if covariates:
            for c in covariates:
                if c in genome_df.columns:
                    cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx]
                    mask &= np.isfinite(cv)

        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue
        if ko[mask].std() == 0:
            continue

        ko_m = ko[mask]
        resp_m = resp[mask]

        if covariates:
            cov_matrix = np.column_stack([
                pd.to_numeric(genome_df[c], errors='coerce').values[idx][mask]
                for c in covariates if c in genome_df.columns
            ])
            n_covs = cov_matrix.shape[1]
            if mask.sum() < n_covs + 3:
                continue
            from numpy.linalg import lstsq
            X = np.column_stack([np.ones(mask.sum()), cov_matrix])
            _, res_resp, _, _ = lstsq(X, resp_m, rcond=None)
            resp_m = resp_m - X @ lstsq(X, resp_m, rcond=None)[0]
            ko_resid = ko_m - X @ lstsq(X, ko_m, rcond=None)[0]
            if ko_resid.std() == 0 or resp_m.std() == 0:
                continue
            rho, _ = stats.pearsonr(ko_resid, resp_m)
        else:
            rho, _ = stats.spearmanr(ko_m, resp_m)

        n = mask.sum()
        z = np.arctanh(np.clip(rho, -0.999, 0.999))
        se = 1.0 / np.sqrt(n - 3) if n > 3 else 1.0
        effects.append((z, se, n))

    if len(effects) < MIN_GENERA:
        return None

    zs, ses, ns = zip(*effects)
    zs, ses = np.array(zs), np.array(ses)
    ws = 1.0 / ses**2
    z_meta = np.sum(ws * zs) / np.sum(ws)
    se_meta = 1.0 / np.sqrt(np.sum(ws))
    p_meta = 2 * stats.norm.sf(abs(z_meta / se_meta))
    rho_meta = np.tanh(z_meta)

    return {'meta_rho': rho_meta, 'meta_p': p_meta, 'n_genera': len(effects)}


# ── Run scans ────────────────────────────────────────────────────────
print("\nRunning association scans...")

all_results = []
for env_var in ENV_RESPONSES:
    other_env = [c for c in ENV_COLS if c != env_var]
    full_control_covs = ['genome_size'] + METALS + other_env

    for ko_id in available_kos:
        # Raw
        raw = within_genus_meta(genome_df, genus_idx, ko_id, env_var)
        if raw is None:
            continue

        # Full control (all metals + all other env vars)
        ctrl = within_genus_meta(genome_df, genus_idx, ko_id, env_var,
                                 covariates=full_control_covs)

        all_results.append({
            'ko_id': ko_id,
            'ko_name': TARGET_KOS.get(ko_id, ''),
            'env_var': env_var,
            'raw_rho': raw['meta_rho'],
            'raw_p': raw['meta_p'],
            'raw_n_genera': raw['n_genera'],
            'ctrl_rho': ctrl['meta_rho'] if ctrl else np.nan,
            'ctrl_p': ctrl['meta_p'] if ctrl else np.nan,
            'ctrl_n_genera': ctrl['n_genera'] if ctrl else 0,
        })

    print(f"  {env_var}: {sum(1 for r in all_results if r['env_var'] == env_var)} pairs tested")

res_df = pd.DataFrame(all_results)

# FDR correction
_, raw_fdr, _, _ = multipletests(res_df.raw_p, method='fdr_bh')
res_df['raw_q'] = raw_fdr

ctrl_mask = res_df.ctrl_p.notna()
ctrl_fdr = np.ones(len(res_df))
if ctrl_mask.sum() > 0:
    _, fdr_vals, _, _ = multipletests(res_df.loc[ctrl_mask, 'ctrl_p'], method='fdr_bh')
    ctrl_fdr[ctrl_mask] = fdr_vals
res_df['ctrl_q'] = ctrl_fdr

res_df.to_csv(OUT / 'ko_env_target_scan.csv', index=False)

# ── Results ──────────────────────────────────────────────────────────
n_tested = len(res_df)
n_raw_sig = (res_df.raw_q < 0.05).sum()
n_ctrl_sig = (res_df.ctrl_q < 0.05).sum()

print(f"\n{'='*60}")
print("RESULTS: Target KO × Environment Association Scan")
print(f"{'='*60}")
print(f"  Pairs tested: {n_tested}")
print(f"  Raw significant (FDR<0.05): {n_raw_sig}")
print(f"  Full control survivors: {n_ctrl_sig}")

if n_ctrl_sig > 0:
    print(f"\n  Top surviving pairs (controlled):")
    survivors = res_df[res_df.ctrl_q < 0.05].nsmallest(10, 'ctrl_q')
    for _, r in survivors.iterrows():
        print(f"    {r.ko_id} ({r.ko_name}) × {r.env_var}: "
              f"ρ={r.ctrl_rho:+.3f} q={r.ctrl_q:.2e} ({r.ctrl_n_genera}g)")

# Comparison table
print(f"\n  Comparison: Metal vs Environment Associations (26 target KOs)")
print(f"  {'Variable':<25} {'Raw sig':>10} {'Controlled':>12}")
print(f"  {'-'*47}")

# Load metal results for target KOs
metal_raw = pd.read_csv(OUT / 'mba_otu_raw.csv')
metal_ks = pd.read_csv(OUT / 'mba_otu_kitchen_sink.csv')
target_metal_raw = metal_raw[metal_raw.ko_id.isin(available_kos)]
target_metal_ks = metal_ks[metal_ks.ko_id.isin(available_kos)]
n_metal_raw = (target_metal_raw.q_fdr < 0.05).sum()
n_metal_ctrl = (target_metal_ks.q_fdr < 0.05).sum()
print(f"  {'Metals (6 combined)':<25} {n_metal_raw:>10} {n_metal_ctrl:>12}")

for env_var in ENV_RESPONSES:
    sub = res_df[res_df.env_var == env_var]
    n_r = (sub.raw_q < 0.05).sum()
    n_c = (sub.ctrl_q < 0.05).sum()
    print(f"  {env_var:<25} {n_r:>10} {n_c:>12}")

# ── Figure ───────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
categories = ['Metals\n(6 combined)'] + [v.replace('_', '\n') for v in ENV_RESPONSES]
raw_counts = [n_metal_raw]
ctrl_counts = [n_metal_ctrl]
for env_var in ENV_RESPONSES:
    sub = res_df[res_df.env_var == env_var]
    raw_counts.append((sub.raw_q < 0.05).sum())
    ctrl_counts.append((sub.ctrl_q < 0.05).sum())

x = np.arange(len(categories))
w = 0.35
bars1 = ax.bar(x - w/2, raw_counts, w, label='Raw', color='#aec7e8')
bars2 = ax.bar(x + w/2, ctrl_counts, w, label='Full control', color='#d62728')

for bar, val in zip(bars1, raw_counts):
    if val > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(val), ha='center', va='bottom', fontsize=9)
for bar, val in zip(bars2, ctrl_counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            str(val), ha='center', va='bottom', fontsize=9)

ax.set_ylabel('Significant KO associations (FDR<0.05)')
ax.set_title('Target KO Associations: Metals vs. Environment\n(26 target KOs, within-genus meta-analysis)')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=8)
ax.legend()

plt.tight_layout()
fig.savefig(OUT / 'ko_env_target_comparison.png', dpi=150, bbox_inches='tight')
fig.savefig(OUT / 'ko_env_target_comparison.pdf', dpi=300, bbox_inches='tight')
print(f"\n  Figure saved to {OUT / 'ko_env_target_comparison.pdf'}")
print("DONE")
