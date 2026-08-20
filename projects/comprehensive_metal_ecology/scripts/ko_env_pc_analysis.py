#!/usr/bin/env python3
"""
KO × environmental-PC association scan.
PCA on 5 env vars → test 26 target KOs × 3 PCs with metal control.
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
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
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
ENV_VARS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
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
genome_meta.drop(columns=[c for c in genome_meta.columns if c.endswith('_dup')], inplace=True)

target_ko_ids = list(TARGET_KOS.keys())
ko_wide = mg[mg.ko_id.isin(target_ko_ids)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
del mg, ko_wide

# Also get top 20 KOs from raw scan for comparison
raw = pd.read_csv(OUT / 'mba_otu_raw.csv')
top20_hg = raw[raw.metal == 'Hg'].nsmallest(20, 'q_fdr')
top20_ko_ids = top20_hg.ko_id.unique().tolist()

# Reload those KOs too
mg2 = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                      columns=['genome_id', 'ko_id', 'present'])
ko_wide2 = mg2[mg2.ko_id.isin(top20_ko_ids)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
for col in ko_wide2.columns:
    if col not in genome_df.columns:
        vals = ko_wide2[col].reindex(genome_df.set_index('genome_id').index).fillna(0).values
        genome_df[col] = vals
del mg2, ko_wide2

print(f"  Genomes: {len(genome_df):,}")

# ── Step 1: Environmental PCA ────────────────────────────────────────
print("\nStep 1: Environmental PCA...")
env_data = genome_df[ENV_VARS].apply(pd.to_numeric, errors='coerce')
env_mask = env_data.notna().all(axis=1)
print(f"  Genomes with complete env data: {env_mask.sum()}/{len(genome_df)}")

scaler = StandardScaler()
env_scaled = scaler.fit_transform(env_data[env_mask])

pca = PCA(n_components=3)
pcs = pca.fit_transform(env_scaled)
var_exp = pca.explained_variance_ratio_ * 100

print(f"\n  Variance explained:")
for i in range(3):
    print(f"    PC{i+1}: {var_exp[i]:.1f}%")

loadings = pd.DataFrame(pca.components_.T,
                        index=ENV_VARS,
                        columns=['PC1', 'PC2', 'PC3'])
print(f"\n  Variable loadings:")
print(loadings.to_string())

# Add PCs to genome_df
for i in range(3):
    genome_df.loc[env_mask, f'envPC{i+1}'] = pcs[:, i]

genome_df = genome_df.reset_index(drop=True)
genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index.tolist()
genus_idx = {g: genome_df.index[genome_df.genus == g].values.astype(int) for g in usable_genera}
print(f"  Usable genera: {len(usable_genera)}")

# ── Step 2: Within-genus meta-analysis ───────────────────────────────
print("\nStep 2: KO × envPC meta-analysis...")

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
            ko_resid = ko_m - X @ lstsq(X, ko_m, rcond=None)[0]
            if ko_resid.std() == 0 or resp_m.std() == 0:
                continue
            rho, _ = stats.pearsonr(ko_resid, resp_m)
        else:
            rho, _ = stats.spearmanr(ko_m, resp_m)

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


pc_cols = ['envPC1', 'envPC2', 'envPC3']
all_kos = list(set(target_ko_ids + top20_ko_ids))
available_kos = [k for k in all_kos if k in genome_df.columns]

results = []
for pc in pc_cols:
    for ko_id in available_kos:
        # Raw (genome_size only)
        raw_res = within_genus_meta(genome_df, genus_idx, ko_id, pc,
                                     covariates=['genome_size'])
        if raw_res is None:
            continue

        # Metal-controlled
        ctrl_res = within_genus_meta(genome_df, genus_idx, ko_id, pc,
                                      covariates=['genome_size'] + METALS)

        results.append({
            'ko_id': ko_id,
            'ko_name': TARGET_KOS.get(ko_id, ''),
            'is_target': ko_id in target_ko_ids,
            'pc': pc,
            'raw_rho': raw_res['meta_rho'],
            'raw_p': raw_res['meta_p'],
            'raw_n_genera': raw_res['n_genera'],
            'ctrl_rho': ctrl_res['meta_rho'] if ctrl_res else np.nan,
            'ctrl_p': ctrl_res['meta_p'] if ctrl_res else np.nan,
            'ctrl_n_genera': ctrl_res['n_genera'] if ctrl_res else 0,
        })

    print(f"  {pc}: {sum(1 for r in results if r['pc'] == pc)} pairs tested")

res_df = pd.DataFrame(results)

# FDR
_, raw_fdr, _, _ = multipletests(res_df.raw_p, method='fdr_bh')
res_df['raw_q'] = raw_fdr

ctrl_mask = res_df.ctrl_p.notna()
ctrl_fdr = np.ones(len(res_df))
if ctrl_mask.sum() > 0:
    _, fdr_vals, _, _ = multipletests(res_df.loc[ctrl_mask, 'ctrl_p'], method='fdr_bh')
    ctrl_fdr[ctrl_mask] = fdr_vals
res_df['ctrl_q'] = ctrl_fdr

res_df.to_csv(OUT / 'ko_env_pc_results.csv', index=False)

# ── Step 3: Results ──────────────────────────────────────────────────
n_tested = len(res_df)
n_raw_sig = (res_df.raw_q < 0.05).sum()
n_ctrl_sig = (res_df.ctrl_q < 0.05).sum()

print(f"\n{'='*60}")
print("RESULTS: KO × Environmental PC Scan")
print(f"{'='*60}")
print(f"  Pairs tested: {n_tested}")
print(f"  Raw significant (genome_size controlled, FDR<0.05): {n_raw_sig}")
print(f"  Metal-controlled survivors: {n_ctrl_sig}")

if n_ctrl_sig > 0:
    print(f"\n  Top 10 metal-controlled survivors:")
    survivors = res_df[res_df.ctrl_q < 0.05].nsmallest(10, 'ctrl_q')
    for _, r in survivors.iterrows():
        name = f" ({r.ko_name})" if r.ko_name else ""
        print(f"    {r.ko_id}{name} × {r.pc}: "
              f"ρ={r.ctrl_rho:+.3f} q={r.ctrl_q:.2e} ({r.ctrl_n_genera}g)")

# Step 4: Cross-reference top 10 KO×Hg with envPC associations
print(f"\n  Cross-reference: Top 10 KO×Hg pairs → environmental PC associations")
print(f"  {'KO':<8} {'Hg ρ':>8} {'PC1 ρ':>8} {'PC1 q':>10} {'PC2 ρ':>8} {'PC2 q':>10}")
print(f"  {'-'*54}")
for _, hg_row in top20_hg.head(10).iterrows():
    ko = hg_row.ko_id
    hg_rho = hg_row.meta_rho
    pc1_row = res_df[(res_df.ko_id == ko) & (res_df.pc == 'envPC1')]
    pc2_row = res_df[(res_df.ko_id == ko) & (res_df.pc == 'envPC2')]
    pc1_rho = pc1_row.ctrl_rho.values[0] if len(pc1_row) else np.nan
    pc1_q = pc1_row.ctrl_q.values[0] if len(pc1_row) else np.nan
    pc2_rho = pc2_row.ctrl_rho.values[0] if len(pc2_row) else np.nan
    pc2_q = pc2_row.ctrl_q.values[0] if len(pc2_row) else np.nan
    print(f"  {ko:<8} {hg_rho:+.3f}   {pc1_rho:+.3f}   {pc1_q:.2e}   {pc2_rho:+.3f}   {pc2_q:.2e}")

# ── Step 5: Figures ──────────────────────────────────────────────────
print("\nMaking figures...")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# (A) PC loadings
ax = axes[0]
x = np.arange(len(ENV_VARS))
w = 0.25
short_names = ['pH', 'Organic C', 'Clay %', 'Temperature', 'Precipitation']
for i, pc in enumerate(['PC1', 'PC2', 'PC3']):
    ax.barh(x + i*w, loadings[pc], w, label=f'{pc} ({var_exp[i]:.0f}%)')
ax.set_yticks(x + w)
ax.set_yticklabels(short_names, fontsize=9)
ax.set_xlabel('Loading')
ax.set_title('(A) Environmental PC Loadings')
ax.legend(fontsize=8)
ax.axvline(0, color='grey', lw=0.5)

# (B) Scatter: KO×Hg ρ vs KO×PC1 ρ
ax = axes[1]
hg_rhos = []
pc1_rhos = []
ko_labels = []
for _, hg_row in top20_hg.iterrows():
    ko = hg_row.ko_id
    pc1_row = res_df[(res_df.ko_id == ko) & (res_df.pc == 'envPC1')]
    if len(pc1_row) == 0:
        continue
    hg_rhos.append(hg_row.meta_rho)
    pc1_rhos.append(pc1_row.raw_rho.values[0])
    ko_labels.append(ko)

ax.scatter(hg_rhos, pc1_rhos, s=30, c='#d62728', alpha=0.7)
for i, label in enumerate(ko_labels[:10]):
    ax.annotate(label, (hg_rhos[i], pc1_rhos[i]), fontsize=6,
                xytext=(3, 3), textcoords='offset points')

if len(hg_rhos) > 2:
    r, p = stats.pearsonr(hg_rhos, pc1_rhos)
    ax.set_title(f'(B) KO×Hg ρ vs KO×PC1 ρ\n(r={r:.2f}, p={p:.2e})')
else:
    ax.set_title('(B) KO×Hg ρ vs KO×PC1 ρ')
ax.set_xlabel('KO × Hg ρ (raw meta-analysis)')
ax.set_ylabel('KO × envPC1 ρ (genome_size controlled)')
ax.axhline(0, color='grey', lw=0.3)
ax.axvline(0, color='grey', lw=0.3)

# (C) Summary bar: raw vs metal-controlled
ax = axes[2]
for i, pc in enumerate(pc_cols):
    sub = res_df[res_df.pc == pc]
    n_raw = (sub.raw_q < 0.05).sum()
    n_ctrl = (sub.ctrl_q < 0.05).sum()
    ax.bar(i - 0.15, n_raw, 0.3, color='#aec7e8', label='Raw' if i == 0 else '')
    ax.bar(i + 0.15, n_ctrl, 0.3, color='#d62728', label='Metal-controlled' if i == 0 else '')
    ax.text(i - 0.15, n_raw + 0.3, str(n_raw), ha='center', fontsize=9)
    ax.text(i + 0.15, n_ctrl + 0.3, str(n_ctrl), ha='center', fontsize=9)

ax.set_xticks(range(3))
ax.set_xticklabels([f'PC{i+1}\n({var_exp[i-1] if i > 0 else var_exp[0]:.0f}%)' for i in range(3)])
ax.set_ylabel('Significant KO×PC pairs (FDR<0.05)')
ax.set_title('(C) KO×envPC: Raw vs Metal-Controlled')
ax.legend(fontsize=8)

plt.tight_layout()
fig.savefig(OUT / 'ko_env_pc_figure.pdf', dpi=300, bbox_inches='tight')
fig.savefig(OUT / 'ko_env_pc_figure.png', dpi=150, bbox_inches='tight')
print(f"  Saved to {OUT / 'ko_env_pc_figure.pdf'}")
print("DONE")
