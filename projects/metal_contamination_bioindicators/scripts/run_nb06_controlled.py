"""
NB06 controlled: MicrobeAtlas × USGS PGLS with full controls.

Extends NB06 with three controls:
  1. Levins' B (coreness/ubiquity proxy from CME)
  2. Detection-weighted mean lat/lon (geography)
  3. Detection-weighted mean sg_pH, sg_SOC, sg_clay (soil chemistry)

Expands metals to all 7 in usa_samples_usgs: As, Cd, Cr, Cu, Ni, Pb, Zn.
Runs base model (genome_mb only) and full model (all controls).
"""
import os, sys
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from statsmodels.stats.multitest import multipletests

ROOT  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = ROOT / 'projects/metal_contamination_bioindicators/data'
FIGS  = ROOT / 'projects/metal_contamination_bioindicators/figures'
TREE  = ROOT / 'projects/comprehensive_metal_ecology/data/gtdb_bac_genus_pruned.tree'
CME_DATA = ROOT / 'projects/comprehensive_metal_ecology/data'

sys.path.insert(0, str(ROOT / 'tools'))
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

sys.path.insert(0, str(ROOT / 'projects/comprehensive_metal_ecology/scripts'))
from pgls_utils import run_pgls

COFACTOR_KOS   = ['K02225', 'K03635', 'K03638', 'K03750', 'K03831']
RESISTANCE_KOS = ['K03325', 'K03446', 'K07665', 'K07785', 'K07787',
                  'K07798', 'K08365', 'K15725', 'K15726', 'K15727',
                  'K16264', 'K17686', 'K19591', 'K19594', 'K19595']
ALL_USGS_METALS = ['as', 'cd', 'cr', 'cu', 'ni', 'pb', 'zn']
COV_COLS        = ['lat', 'lon', 'sg_pH', 'sg_SOC', 'sg_clay']
MIN_SAMPLES     = 30

# ── 1. Load USA merged dataset ────────────────────────────────────────────────
print('Loading analysis_matrix …')
mat = pd.read_parquet(DATA / 'analysis_matrix.parquet')
clr_cols = [c for c in mat.columns if c.startswith('clr_')]
genera   = [c[4:] for c in clr_cols]

usa_mat = mat[
    mat['lat'].between(24.0, 50.0) &
    mat['lon'].between(-125.0, -65.0)
].copy()
print(f'  {len(usa_mat):,} USA samples, {len(genera)} CLR genera')
del mat

usgs_cols = [f'usgs_raw_{m}' for m in ALL_USGS_METALS]
usgs = pd.read_parquet(DATA / 'usa_samples_usgs.parquet',
                       columns=['sample_id', 'usgs_dist_km'] + usgs_cols)
merged = usa_mat.merge(usgs, on='sample_id', how='inner')
print(f'  Merged: {len(merged):,} samples')

for m in ALL_USGS_METALS:
    col = f'usgs_raw_{m}'
    merged[f'logppm_{m}'] = np.log1p(merged[col].clip(lower=0))

# ── 2. Detection arrays ───────────────────────────────────────────────────────
clr_arr  = merged[clr_cols].to_numpy(dtype=np.float64)
col_mins = np.nanmin(clr_arr, axis=0, keepdims=True)
col_sds  = np.nanstd(clr_arr, axis=0, keepdims=True)
detected = clr_arr > (col_mins + 2 * col_sds)
wt_arr   = np.exp(np.where(np.isnan(clr_arr), -np.inf, clr_arr))
print(f'  Detection rate: {detected.mean():.3f}')

# ── 3. Per-genus weighted means: log-ppm + covariates ────────────────────────
logppm_arrs = {m: merged[f'logppm_{m}'].to_numpy(dtype=np.float64)
               for m in ALL_USGS_METALS}
cov_arr   = merged[COV_COLS].to_numpy(dtype=np.float64)
cov_valid = ~np.isnan(cov_arr)

print('Computing per-genus means …')
ef_rows  = []
cov_rows = []

for gi, genus in enumerate(genera):
    det = detected[:, gi]
    if det.sum() < MIN_SAMPLES:
        continue
    w   = wt_arr[det, gi]
    if w.sum() == 0:
        continue

    # covariates
    cov_row = {'genus_lower': genus}
    for ci, col in enumerate(COV_COLS):
        vm = det & cov_valid[:, ci]
        wv = wt_arr[vm, gi]
        cov_row[f'mean_{col}'] = (np.average(cov_arr[vm, ci], weights=wv)
                                  if vm.sum() > 0 and wv.sum() > 0 else np.nan)
    cov_rows.append(cov_row)

    # log-ppm per element
    for m in ALL_USGS_METALS:
        ppm_v = logppm_arrs[m]
        valid = det & ~np.isnan(ppm_v)
        n     = int(valid.sum())
        if n < MIN_SAMPLES:
            continue
        wv = wt_arr[valid, gi]
        if wv.sum() == 0:
            continue
        ef_rows.append({'genus_lower': genus, 'element': m,
                        'mean_logppm': np.average(ppm_v[valid], weights=wv),
                        'n_samples': n})

genus_ef   = pd.DataFrame(ef_rows)
genus_covs = pd.DataFrame(cov_rows)

genus_ef_wide = (genus_ef.pivot(index='genus_lower', columns='element', values='mean_logppm')
                 .reset_index())
genus_ef_wide.columns = (['genus_lower'] +
                         [f'mean_logppm_{c}' for c in genus_ef_wide.columns[1:]])
print(f'EF wide: {genus_ef_wide.shape}')
print(f'Genera per element:')
for m in ALL_USGS_METALS:
    c = f'mean_logppm_{m}'
    if c in genus_ef_wide.columns:
        print(f'  {m.upper()}: {genus_ef_wide[c].notna().sum()} genera')

# ── 4. Load cached Spark KO density ──────────────────────────────────────────
ko_genus = pd.read_parquet(DATA / 'usa_ef_ko_genus_density.parquet')

def tier_density(df, ko_set):
    sub  = df[df['ko'].isin(ko_set)]
    dens = sub.groupby('genus_lower')['cond_density'].sum().reset_index()
    return dens.rename(columns={'cond_density': 'density'})

cof_dens = tier_density(ko_genus, COFACTOR_KOS).rename(columns={'density': 'cofactor_density'})
res_dens = tier_density(ko_genus, RESISTANCE_KOS).rename(columns={'density': 'resistance_density'})

# ── 5. Build genus table ──────────────────────────────────────────────────────
cme_input = pd.read_csv(CME_DATA / '01_pgls_input_bacteria.csv',
    usecols=['genus_lower', 'mean_genome_mb', 'phylum', 'mean_levins_B_std'])

genus_table = (
    genus_ef_wide
    .merge(cof_dens, on='genus_lower', how='inner')
    .merge(res_dens, on='genus_lower', how='inner')
    .merge(cme_input, on='genus_lower', how='left')
    .merge(genus_covs, on='genus_lower', how='left')
)
print(f'\nGenus table: {genus_table.shape}')
print(f'  levins_B available: {genus_table["mean_levins_B_std"].notna().sum()}')

for col in ['cofactor_density', 'resistance_density', 'mean_genome_mb',
            'mean_levins_B_std', 'mean_lat', 'mean_lon',
            'mean_sg_pH', 'mean_sg_SOC', 'mean_sg_clay']:
    μ, σ = genus_table[col].mean(), genus_table[col].std()
    genus_table[f'{col}_z'] = (genus_table[col] - μ) / σ if σ > 0 else 0.0

genus_table.to_csv(DATA / 'usa_ef_pgls_controlled_input.csv', index=False)
print('Saved: usa_ef_pgls_controlled_input.csv')

# ── 6. PGLS ───────────────────────────────────────────────────────────────────
tree_path = str(TREE.resolve())

BASE_COVS = ['mean_genome_mb_z']
FULL_COVS = ['mean_genome_mb_z', 'mean_levins_B_std_z',
             'mean_lat_z', 'mean_lon_z',
             'mean_sg_pH_z', 'mean_sg_SOC_z', 'mean_sg_clay_z']

results_rows = []
elements_tested = [m for m in ALL_USGS_METALS
                   if f'mean_logppm_{m}' in genus_table.columns]

for element in elements_tested:
    resp_col = f'mean_logppm_{element}'
    all_pred_cols = (['genus_lower', resp_col,
                      'cofactor_density_z', 'resistance_density_z'] + FULL_COVS)
    df_sub = genus_table[all_pred_cols].dropna().copy()
    print(f'\n{element.upper()}: n_genera={len(df_sub)}')
    if len(df_sub) < 15:
        print('  Skipping — too few genera')
        continue

    for model_name, extra_covs in [('base', BASE_COVS), ('full', FULL_COVS)]:
        for tier, pred in [('Cofactor', 'cofactor_density_z'),
                            ('Resistance', 'resistance_density_z')]:
            try:
                res = run_pgls(df_sub, tree_path,
                               response=resp_col,
                               predictors=[pred] + extra_covs,
                               taxon_col='genus_lower')
                beta = res['betas'][pred]
                se   = res['SEs'][pred]
                pval = res['p_values'][pred]
                lam  = res.get('lambda_est', float('nan'))
                print(f'  {model_name:4s} {tier:10s}: β={beta:+.4f} p={pval:.3g} λ={lam:.3f}')
                results_rows.append(dict(element=element.upper(), tier=tier,
                                         model=model_name, beta=beta, se=se,
                                         p_value=pval, lambda_est=lam,
                                         n_genera=res['n']))
            except Exception as e:
                print(f'  {model_name:4s} {tier:10s}: FAILED — {e}')
                results_rows.append(dict(element=element.upper(), tier=tier,
                                         model=model_name, beta=np.nan, se=np.nan,
                                         p_value=np.nan, lambda_est=np.nan,
                                         n_genera=np.nan))

results_df = pd.DataFrame(results_rows)

# FDR within each (model × tier) block
for model_name in ['base', 'full']:
    for tier in ['Cofactor', 'Resistance']:
        mask = (results_df['model'] == model_name) & (results_df['tier'] == tier)
        pv   = results_df.loc[mask, 'p_value'].values
        valid = ~np.isnan(pv)
        fdr   = np.full(len(pv), np.nan)
        if valid.sum() > 1:
            _, fdr[valid], _, _ = multipletests(pv[valid], method='fdr_bh')
        results_df.loc[mask, 'fdr_q'] = fdr

results_df.to_csv(DATA / 'usa_ef_pgls_controlled_results.csv', index=False)
print('\n' + '='*65)
print('NB06 CONTROLLED PGLS — full model, by element and tier')
print('='*65)
print(results_df[results_df['model'] == 'full'].to_string(
    index=False, float_format='{:.4f}'.format))

# ── 7. Forest plot (full model only) ─────────────────────────────────────────
full_res = results_df[results_df['model'] == 'full'].copy()
element_order = sorted(full_res['element'].dropna().unique())
n_el = len(element_order)

fig, axs = plt.subplots(1, 2, figsize=(FIGW['2col'], max(ROW_H, 0.35 * n_el + 0.5)),
                         sharey=True, gridspec_kw={'wspace': 0.05})

for ax, tier in zip(axs, ['Cofactor', 'Resistance']):
    sub = full_res[full_res['tier'] == tier].set_index('element')
    col = PALETTE[0] if tier == 'Cofactor' else PALETTE[1]

    for yi, el in enumerate(element_order):
        if el not in sub.index or np.isnan(sub.loc[el, 'beta']):
            continue
        b   = sub.loc[el, 'beta']
        ci  = 1.96 * sub.loc[el, 'se']
        pv  = sub.loc[el, 'p_value']
        qv  = sub.loc[el, 'fdr_q']
        n   = int(sub.loc[el, 'n_genera'])
        sig = '†' if pv < 0.05 else ''
        fdr_sig = '*' if (not np.isnan(qv) and qv < 0.2) else ''
        ax.errorbar(b, yi, xerr=ci, fmt='o', color=col,
                    capsize=3, capthick=1.2, lw=1.5, ms=6)
        ax.text(b + ci + 0.005, yi,
                f'{sig}{fdr_sig} p={pv:.2g} n={n}',
                va='center', fontsize=7)

    ax.axvline(0, color='gray', lw=0.8, ls='--')
    ax.set_yticks(range(n_el))
    ax.set_yticklabels(element_order, fontsize=9)
    ax.set_xlabel('PGLS β (full model)', fontsize=9)
    ax.set_title(f'{tier} KO density', fontsize=10)

axs[0].invert_yaxis()
fig.suptitle('MicrobeAtlas × USGS: KO density → element log-ppm\n(full controls: genome, Levins B, lat/lon, soil chemistry)',
             y=1.02, fontsize=10, fontweight='bold')
save(fig, FIGS / 'fig_nb06_controlled_forest')
print('Saved: fig_nb06_controlled_forest.pdf')
print('\nDone.')
