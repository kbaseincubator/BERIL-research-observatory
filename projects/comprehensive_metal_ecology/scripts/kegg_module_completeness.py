#!/usr/bin/env python3
"""
KEGG module completeness × environment analysis.
Compute module completeness from KO presence/absence, then test
module completeness × env vars using within-genus meta-analysis.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import json
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

# ── Step 1: Get KEGG module → KO mappings ────────────────────────────
print("Step 1: Fetching KEGG module definitions...")

import urllib.request
import re
import time

def fetch_kegg_module_list():
    """Get list of all KEGG modules."""
    cache = OUT / 'kegg_module_list.json'
    if cache.exists():
        return json.loads(cache.read_text())
    url = "https://rest.kegg.jp/list/module"
    data = urllib.request.urlopen(url, timeout=30).read().decode()
    modules = {}
    for line in data.strip().split('\n'):
        parts = line.split('\t')
        if len(parts) >= 2:
            mod_id = parts[0].replace('md:', '')
            modules[mod_id] = parts[1]
    cache.write_text(json.dumps(modules))
    return modules

def fetch_module_kos(mod_id):
    """Get KOs in a module."""
    cache = OUT / f'kegg_module_{mod_id}.json'
    if cache.exists():
        return json.loads(cache.read_text())
    url = f"https://rest.kegg.jp/link/ko/{mod_id}"
    try:
        data = urllib.request.urlopen(url, timeout=30).read().decode()
        kos = []
        for line in data.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) >= 2:
                ko = parts[1].replace('ko:', '')
                kos.append(ko)
        result = list(set(kos))
        cache.write_text(json.dumps(result))
        time.sleep(0.35)
        return result
    except Exception as e:
        return []

modules = fetch_kegg_module_list()
print(f"  Total KEGG modules: {len(modules)}")

# ── Step 2: Load KO matrix ───────────────────────────────────────────
print("\nStep 2: Loading KO matrix...")
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
genome_meta = genome_meta.merge(env_full, on='genome_id', how='left', suffixes=('', '_dup'))
genome_meta.drop(columns=[c for c in genome_meta.columns if c.endswith('_dup')], inplace=True)

# Get all KOs present per genome
genome_kos = mg.groupby('genome_id')['ko_id'].apply(set).to_dict()
all_ko_ids = set(mg.ko_id.unique())
print(f"  Genomes: {len(genome_meta):,}, unique KOs: {len(all_ko_ids):,}")
del mg

# ── Step 3: Compute module completeness ──────────────────────────────
print("\nStep 3: Computing module completeness...")

module_kos_map = {}
n_fetched = 0
for mod_id in sorted(modules.keys()):
    kos = fetch_module_kos(mod_id)
    represented = [k for k in kos if k in all_ko_ids]
    if len(represented) >= 5:
        module_kos_map[mod_id] = kos
    n_fetched += 1
    if n_fetched % 100 == 0:
        print(f"  Fetched {n_fetched}/{len(modules)} modules...")

print(f"  Modules with ≥5 represented KOs: {len(module_kos_map)}")

# Compute completeness per genome per module
print("  Computing completeness matrix...")
completeness = {}
genomes = list(genome_meta.genome_id)
for mod_id, kos in module_kos_map.items():
    mod_comp = []
    for gid in genomes:
        gko = genome_kos.get(gid, set())
        present = sum(1 for k in kos if k in gko)
        mod_comp.append(present / len(kos))
    completeness[mod_id] = mod_comp

comp_df = pd.DataFrame(completeness, index=genomes)
print(f"  Completeness matrix: {comp_df.shape[0]} genomes × {comp_df.shape[1]} modules")

# Filter to variable modules (not all 0 or all 1)
variable_modules = []
for col in comp_df.columns:
    std = comp_df[col].std()
    if std > 0.01:
        variable_modules.append(col)
print(f"  Variable modules (std > 0.01): {len(variable_modules)}")

# Merge with metadata
genome_df = genome_meta.set_index('genome_id').join(comp_df[variable_modules]).reset_index()

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index.tolist()
genus_idx = {g: genome_df.index[genome_df.genus == g].values.astype(int) for g in usable_genera}

# ── Step 4: Within-genus meta-analysis ───────────────────────────────
print(f"\nStep 4: Testing module × environment associations...")

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

        feat_m = feat[mask]
        resp_m = resp[mask]
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

    zs, ses = np.array([e[0] for e in effects]), np.array([e[1] for e in effects])
    ws = 1.0 / ses**2
    z_meta = np.sum(ws * zs) / np.sum(ws)
    se_meta = 1.0 / np.sqrt(np.sum(ws))
    p_meta = 2 * stats.norm.sf(abs(z_meta / se_meta))
    rho_meta = np.tanh(z_meta)

    return {'meta_rho': rho_meta, 'meta_p': p_meta, 'n_genera': len(effects)}

all_results = []
for env_var in ENV_RESPONSES:
    other_env = [c for c in ENV_COLS if c != env_var]
    full_control = ['genome_size'] + METALS + other_env

    for mod_id in variable_modules:
        raw = within_genus_meta(genome_df, genus_idx, mod_id, env_var)
        if raw is None:
            continue

        ctrl = within_genus_meta(genome_df, genus_idx, mod_id, env_var,
                                  covariates=full_control)

        all_results.append({
            'module': mod_id,
            'module_name': modules.get(mod_id, ''),
            'env_var': env_var,
            'n_kos': len(module_kos_map.get(mod_id, [])),
            'raw_rho': raw['meta_rho'],
            'raw_p': raw['meta_p'],
            'raw_n_genera': raw['n_genera'],
            'ctrl_rho': ctrl['meta_rho'] if ctrl else np.nan,
            'ctrl_p': ctrl['meta_p'] if ctrl else np.nan,
            'ctrl_n_genera': ctrl['n_genera'] if ctrl else 0,
        })

    tested_this = sum(1 for r in all_results if r['env_var'] == env_var)
    print(f"  {env_var}: {tested_this} module pairs tested")

res_df = pd.DataFrame(all_results)

if len(res_df) == 0:
    print("No testable module × env pairs found.")
    sys.exit(0)

# FDR
_, raw_fdr, _, _ = multipletests(res_df.raw_p, method='fdr_bh')
res_df['raw_q'] = raw_fdr

ctrl_mask = res_df.ctrl_p.notna()
ctrl_fdr = np.ones(len(res_df))
if ctrl_mask.sum() > 0:
    _, fdr_vals, _, _ = multipletests(res_df.loc[ctrl_mask, 'ctrl_p'], method='fdr_bh')
    ctrl_fdr[ctrl_mask] = fdr_vals
res_df['ctrl_q'] = ctrl_fdr

res_df.to_csv(OUT / 'kegg_module_env_results.csv', index=False)

# ── Results ──────────────────────────────────────────────────────────
n_tested = len(res_df)
n_raw = (res_df.raw_q < 0.05).sum()
n_ctrl = (res_df.ctrl_q < 0.05).sum()

print(f"\n{'='*60}")
print("RESULTS: KEGG Module Completeness × Environment")
print(f"{'='*60}")
print(f"  Modules tested: {res_df.module.nunique()}")
print(f"  Module × env pairs tested: {n_tested}")
print(f"  Raw significant (FDR<0.05): {n_raw}")
print(f"  Full control survivors: {n_ctrl}")

if n_ctrl > 0:
    print(f"\n  Top 10 surviving modules (controlled):")
    survivors = res_df[res_df.ctrl_q < 0.05].nsmallest(10, 'ctrl_q')
    for _, r in survivors.iterrows():
        name = r.module_name[:50] if len(r.module_name) > 50 else r.module_name
        print(f"    {r.module} × {r.env_var}: ρ={r.ctrl_rho:+.3f} q={r.ctrl_q:.2e} "
              f"({r.ctrl_n_genera}g, {r.n_kos} KOs) — {name}")
elif n_raw > 0:
    print(f"\n  Top 10 raw significant (none survive control):")
    top_raw = res_df[res_df.raw_q < 0.05].nsmallest(10, 'raw_q')
    for _, r in top_raw.iterrows():
        name = r.module_name[:50] if len(r.module_name) > 50 else r.module_name
        print(f"    {r.module} × {r.env_var}: ρ={r.raw_rho:+.3f} q={r.raw_q:.2e} — {name}")

# ── Figure ───────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# (A) Bar chart by env var
ax = axes[0]
categories = [v.replace('_', '\n') for v in ENV_RESPONSES]
raw_counts = [(res_df[(res_df.env_var == v) & (res_df.raw_q < 0.05)]).shape[0] for v in ENV_RESPONSES]
ctrl_counts = [(res_df[(res_df.env_var == v) & (res_df.ctrl_q < 0.05)]).shape[0] for v in ENV_RESPONSES]
x = np.arange(len(categories))
w = 0.35
ax.bar(x - w/2, raw_counts, w, label='Raw', color='#aec7e8')
ax.bar(x + w/2, ctrl_counts, w, label='Full control', color='#d62728')
for i, (rv, cv) in enumerate(zip(raw_counts, ctrl_counts)):
    if rv > 0: ax.text(i - w/2, rv + 0.3, str(rv), ha='center', fontsize=9)
    ax.text(i + w/2, cv + 0.3, str(cv), ha='center', fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=8)
ax.set_ylabel('Significant module associations')
ax.set_title('(A) Module × Environment: Raw vs Controlled')
ax.legend(fontsize=8)

# (B) Top modules
ax = axes[1]
if n_raw > 0:
    top = res_df.nsmallest(15, 'raw_p')
    top = top.sort_values('raw_p')
    labels = [f"{r.module}\n({r.env_var.split('_')[0]})" for _, r in top.iterrows()]
    colors = ['#d62728' if r.ctrl_q < 0.05 else '#aec7e8' for _, r in top.iterrows()]
    ax.barh(range(len(top)), top.raw_rho.abs(), color=colors)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel('|ρ| (raw meta-analysis)')
    ax.set_title('(B) Top 15 Modules by Raw Effect')
    ax.invert_yaxis()
else:
    ax.text(0.5, 0.5, 'No significant\nassociations', ha='center', va='center',
            transform=ax.transAxes, fontsize=14)
    ax.set_title('(B) No Significant Modules')

plt.tight_layout()
fig.savefig(OUT / 'kegg_module_env_figure.png', dpi=150, bbox_inches='tight')
fig.savefig(OUT / 'kegg_module_env_figure.pdf', dpi=300, bbox_inches='tight')
print(f"\n  Figure saved to {OUT / 'kegg_module_env_figure.pdf'}")
print("DONE")
