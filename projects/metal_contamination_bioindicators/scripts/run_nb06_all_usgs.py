"""
NB06 expanded: MicrobeAtlas × all USGS elements, full controls.

Replaces the pre-baked usa_samples_usgs.parquet (7 metals) with an inline
BallTree spatial join to usgs_geochem_joined.parquet, testing every USGS
element that has sufficient site coverage across USA MicrobeAtlas samples.

Controls (same as run_nb06_controlled.py):
  1. Levins' B (coreness/ubiquity proxy)
  2. Detection-weighted mean lat/lon
  3. Detection-weighted mean sg_pH, sg_SOC, sg_clay
"""
import os, sys
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.neighbors import BallTree
from statsmodels.stats.multitest import multipletests

ROOT     = Path('/home/hmacgregor/BERIL-research-observatory')
DATA     = ROOT / 'projects/metal_contamination_bioindicators/data'
FIGS     = ROOT / 'projects/metal_contamination_bioindicators/figures'
TREE     = ROOT / 'projects/comprehensive_metal_ecology/data/gtdb_bac_genus_pruned.tree'
CME_DATA = ROOT / 'projects/comprehensive_metal_ecology/data'
BERDL    = Path.home() / 'data/envdbs'

sys.path.insert(0, str(ROOT / 'tools'))
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

sys.path.insert(0, str(ROOT / 'projects/comprehensive_metal_ecology/scripts'))
from pgls_utils import run_pgls

COFACTOR_KOS   = ['K02225', 'K03635', 'K03638', 'K03750', 'K03831']
RESISTANCE_KOS = ['K03325', 'K03446', 'K07665', 'K07785', 'K07787',
                  'K07798', 'K08365', 'K15725', 'K15726', 'K15727',
                  'K16264', 'K17686', 'K19591', 'K19594', 'K19595']

RADIUS_KM  = 25.0
MIN_SITES  = 200   # min unique USGS sites with data for an element to include it
MIN_SAMPLES = 30   # min detected samples per genus
MIN_GENERA  = 15   # min genera per element for PGLS

COV_COLS = ['lat', 'lon', 'sg_pH', 'sg_SOC', 'sg_clay']

# ── 1. Load analysis_matrix (CLR + covariates) ────────────────────────────────
print('Loading analysis_matrix …')
mat = pd.read_parquet(DATA / 'analysis_matrix.parquet')
clr_cols = [c for c in mat.columns if c.startswith('clr_')]
genera   = [c[4:] for c in clr_cols]
print(f'  {len(mat):,} total samples, {len(genera)} CLR genera')

usa_mat = mat[
    mat['lat'].between(24.0, 50.0) &
    mat['lon'].between(-125.0, -65.0)
].copy()
print(f'  {len(usa_mat):,} USA samples')
del mat

# ── 2. Spatial join: MicrobeAtlas → nearest USGS soil site ≤25km ──────────────
print('\nBuilding USGS soil BallTree …')
sites = pd.read_parquet(BERDL / 'usgs_geochem.parquet',
                        columns=['group_id', 'latitude', 'longitude', 'primary_class'])
soil = sites[sites['primary_class'] == 'soil'].dropna(
    subset=['latitude', 'longitude']).copy()
print(f'  USGS soil sites: {len(soil):,}')

soil_rad = np.radians(soil[['latitude', 'longitude']].values)
tree = BallTree(soil_rad, metric='haversine')

samp_rad = np.radians(usa_mat[['lat', 'lon']].values)
dist_rad, idx = tree.query(samp_rad, k=1)
dist_km = dist_rad[:, 0] * 6371.0

usa_mat['usgs_dist_km']  = dist_km
usa_mat['usgs_group_id'] = soil['group_id'].iloc[idx[:, 0]].values
matched = usa_mat[usa_mat['usgs_dist_km'] <= RADIUS_KM].copy()
print(f'  Matched samples: {len(matched):,} / {len(usa_mat):,} ({100*len(matched)/len(usa_mat):.1f}%)')
print(f'  Unique USGS sites: {matched["usgs_group_id"].nunique():,}')
del usa_mat

# ── 3. Load all chemical measurements for matched sites ───────────────────────
print('\nLoading usgs_geochem_joined for matched group_ids …')
matched_gids = set(matched['usgs_group_id'])
chem = pd.read_parquet(BERDL / 'usgs_geochem_joined.parquet',
                       columns=['group_id', 'species', 'qualified_value'])
chem = chem[
    chem['group_id'].isin(matched_gids) &
    chem['qualified_value'].notna() &
    chem['qualified_value'].gt(0)
].copy()
print(f'  Measurement rows: {len(chem):,}')

sp_cov = chem.groupby('species')['group_id'].nunique()
keep_species = sorted(sp_cov[sp_cov >= MIN_SITES].index)
print(f'  Elements with ≥{MIN_SITES} sites: {len(keep_species)}')
print(f'  → {keep_species}')

chem = chem[chem['species'].isin(keep_species)].copy()
chem_agg = (chem.groupby(['group_id', 'species'])['qualified_value']
            .median().reset_index())
chem_wide = (chem_agg.pivot(index='group_id', columns='species',
                             values='qualified_value')
             .reset_index())
chem_wide.columns.name = None
print(f'  USGS sites × species table: {chem_wide.shape}')

# ── 4. Merge chemical data → samples ──────────────────────────────────────────
matched = matched.merge(chem_wide, left_on='usgs_group_id',
                        right_on='group_id', how='left')
print(f'  Merged sample table: {matched.shape}')

for sp in keep_species:
    if sp in matched.columns:
        matched[f'logppm_{sp}'] = np.log1p(matched[sp].clip(lower=0))

# ── 5. Detection arrays ───────────────────────────────────────────────────────
print('\nComputing detection arrays …')
clr_arr  = matched[clr_cols].to_numpy(dtype=np.float64)
col_mins = np.nanmin(clr_arr, axis=0, keepdims=True)
col_sds  = np.nanstd(clr_arr, axis=0, keepdims=True)
detected = clr_arr > (col_mins + 2 * col_sds)
wt_arr   = np.exp(np.where(np.isnan(clr_arr), -np.inf, clr_arr))
print(f'  Detection rate: {detected.mean():.3f}')

# ── 6. Per-genus detection-weighted means ─────────────────────────────────────
logppm_cols = [f'logppm_{sp}' for sp in keep_species if f'logppm_{sp}' in matched.columns]
logppm_arrs = {sp: matched[f'logppm_{sp}'].to_numpy(dtype=np.float64)
               for sp in keep_species if f'logppm_{sp}' in matched.columns}
cov_arr     = matched[COV_COLS].to_numpy(dtype=np.float64)
cov_valid   = ~np.isnan(cov_arr)

print(f'Computing per-genus weighted means ({len(genera)} genera × {len(keep_species)} elements) …')
ef_rows  = []
cov_rows = []
for gi, genus in enumerate(genera):
    det = detected[:, gi]
    if det.sum() < MIN_SAMPLES:
        continue
    w = wt_arr[det, gi]
    if w.sum() == 0:
        continue

    cov_row = {'genus_lower': genus}
    for ci, col in enumerate(COV_COLS):
        vm = det & cov_valid[:, ci]
        wv = wt_arr[vm, gi]
        cov_row[f'mean_{col}'] = (np.average(cov_arr[vm, ci], weights=wv)
                                  if vm.sum() > 0 and wv.sum() > 0 else np.nan)
    cov_rows.append(cov_row)

    for sp, ppm_v in logppm_arrs.items():
        valid = det & ~np.isnan(ppm_v)
        n     = int(valid.sum())
        if n < MIN_SAMPLES:
            continue
        wv = wt_arr[valid, gi]
        if wv.sum() == 0:
            continue
        ef_rows.append({'genus_lower': genus, 'element': sp,
                        'mean_logppm': np.average(ppm_v[valid], weights=wv),
                        'n_samples': n})

genus_ef   = pd.DataFrame(ef_rows)
genus_covs = pd.DataFrame(cov_rows)
print(f'  EF rows: {len(genus_ef):,}')
print(f'  COV rows: {len(genus_covs):,}')

genus_ef_wide = (genus_ef.pivot(index='genus_lower', columns='element', values='mean_logppm')
                 .reset_index())
genus_ef_wide.columns = (['genus_lower'] +
                         [f'mean_logppm_{c}' for c in genus_ef_wide.columns[1:]])
print('\nGenera per element:')
for sp in keep_species:
    c = f'mean_logppm_{sp}'
    if c in genus_ef_wide.columns:
        n = genus_ef_wide[c].notna().sum()
        if n >= MIN_GENERA:
            print(f'  {sp:4s}: {n} genera')

# ── 7. Load cached KO density + Levins' B ────────────────────────────────────
print('\nLoading KO density cache …')
ko_genus = pd.read_parquet(DATA / 'usa_ef_ko_genus_density.parquet')

def tier_density(df, ko_set):
    sub  = df[df['ko'].isin(ko_set)]
    dens = sub.groupby('genus_lower')['cond_density'].sum().reset_index()
    return dens.rename(columns={'cond_density': 'density'})

cof_dens = tier_density(ko_genus, COFACTOR_KOS).rename(columns={'density': 'cofactor_density'})
res_dens = tier_density(ko_genus, RESISTANCE_KOS).rename(columns={'density': 'resistance_density'})

cme_input = pd.read_csv(CME_DATA / '01_pgls_input_bacteria.csv',
    usecols=['genus_lower', 'mean_genome_mb', 'mean_levins_B_std'])

genus_table = (
    genus_ef_wide
    .merge(cof_dens, on='genus_lower', how='inner')
    .merge(res_dens, on='genus_lower', how='inner')
    .merge(cme_input, on='genus_lower', how='left')
    .merge(genus_covs, on='genus_lower', how='left')
)
print(f'Genus table: {genus_table.shape}')
print(f'  levins_B available: {genus_table["mean_levins_B_std"].notna().sum()}')

for col in ['cofactor_density', 'resistance_density', 'mean_genome_mb',
            'mean_levins_B_std', 'mean_lat', 'mean_lon',
            'mean_sg_pH', 'mean_sg_SOC', 'mean_sg_clay']:
    μ, σ = genus_table[col].mean(), genus_table[col].std()
    genus_table[f'{col}_z'] = (genus_table[col] - μ) / σ if σ > 0 else 0.0

genus_table.to_csv(DATA / 'nb06_all_usgs_input.csv', index=False)
print('Saved: nb06_all_usgs_input.csv')

# ── 8. PGLS ───────────────────────────────────────────────────────────────────
tree_path  = str(TREE.resolve())
BASE_COVS  = ['mean_genome_mb_z']
FULL_COVS  = ['mean_genome_mb_z', 'mean_levins_B_std_z',
              'mean_lat_z', 'mean_lon_z',
              'mean_sg_pH_z', 'mean_sg_SOC_z', 'mean_sg_clay_z']

elements_to_test = [sp for sp in keep_species
                    if f'mean_logppm_{sp}' in genus_table.columns and
                       genus_table[f'mean_logppm_{sp}'].notna().sum() >= MIN_GENERA]
print(f'\nElements to test: {len(elements_to_test)} — {elements_to_test}')

results_rows = []
for element in elements_to_test:
    resp_col  = f'mean_logppm_{element}'
    pred_cols = (['genus_lower', resp_col,
                  'cofactor_density_z', 'resistance_density_z'] + FULL_COVS)
    df_sub = genus_table[pred_cols].dropna().copy()
    print(f'\n{element}: n_genera={len(df_sub)}')
    if len(df_sub) < MIN_GENERA:
        print('  Skipping')
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
                results_rows.append(dict(element=element, tier=tier,
                                         model=model_name, beta=beta, se=se,
                                         p_value=pval, lambda_est=lam,
                                         n_genera=res['n']))
            except Exception as e:
                print(f'  {model_name:4s} {tier:10s}: FAILED — {e}')
                results_rows.append(dict(element=element, tier=tier,
                                         model=model_name,
                                         beta=np.nan, se=np.nan,
                                         p_value=np.nan, lambda_est=np.nan,
                                         n_genera=np.nan))

results_df = pd.DataFrame(results_rows)

if len(results_df) == 0 or 'model' not in results_df.columns:
    print('No PGLS results — check pipeline above.')
    sys.exit(0)

# FDR within each (model × tier) block
for model_name in ['base', 'full']:
    for tier in ['Cofactor', 'Resistance']:
        mask  = (results_df['model'] == model_name) & (results_df['tier'] == tier)
        pv    = results_df.loc[mask, 'p_value'].values
        valid  = ~np.isnan(pv)
        fdr    = np.full(len(pv), np.nan)
        if valid.sum() > 1:
            _, fdr[valid], _, _ = multipletests(pv[valid], method='fdr_bh')
        results_df.loc[mask, 'fdr_q'] = fdr

results_df.to_csv(DATA / 'nb06_all_usgs_results.csv', index=False)
print('\n' + '='*70)
print('NB06 ALL-USGS — FULL MODEL (p<0.20 sorted by p-value)')
print('='*70)
full = results_df[results_df['model'] == 'full'].dropna(subset=['p_value'])
full = full.sort_values('p_value')
print(full[full['p_value'] < 0.20][
    ['element','tier','beta','se','p_value','fdr_q','n_genera']
].to_string(index=False, float_format='{:.4f}'.format))

# ── 9. Forest plot (full model) ───────────────────────────────────────────────
full_cof = results_df[(results_df['model']=='full') &
                       (results_df['tier']=='Cofactor')].dropna(subset=['beta'])
el_order = full_cof.sort_values('beta')['element'].tolist()
n_el = len(el_order)

if n_el > 0:
    fig, axs = plt.subplots(1, 2,
                             figsize=(FIGW['2col'], max(ROW_H, 0.28 * n_el + 0.8)),
                             sharey=True, gridspec_kw={'wspace': 0.05})

    for ax, tier in zip(axs, ['Cofactor', 'Resistance']):
        sub = results_df[(results_df['model']=='full') &
                         (results_df['tier']==tier)].set_index('element')
        col = PALETTE[0] if tier == 'Cofactor' else PALETTE[1]

        for yi, el in enumerate(el_order):
            if el not in sub.index or np.isnan(sub.loc[el, 'beta']):
                continue
            b  = sub.loc[el, 'beta']
            ci = 1.96 * sub.loc[el, 'se']
            pv = sub.loc[el, 'p_value']
            qv = sub.loc[el, 'fdr_q']
            n  = int(sub.loc[el, 'n_genera'])
            sig     = '†' if pv < 0.05 else ''
            fdr_sig = '*' if (not np.isnan(qv) and qv < 0.2) else ''
            ax.errorbar(b, yi, xerr=ci, fmt='o', color=col,
                        capsize=3, capthick=1.2, lw=1.5, ms=5)
            ax.text(b + ci + 0.001, yi,
                    f'{sig}{fdr_sig} p={pv:.2g} n={n}',
                    va='center', fontsize=6)

        ax.axvline(0, color='gray', lw=0.8, ls='--')
        ax.set_yticks(range(n_el))
        ax.set_yticklabels(el_order, fontsize=7)
        ax.set_xlabel('PGLS β (full model)', fontsize=9)
        ax.set_title(f'{tier} KO density', fontsize=10)

    axs[0].invert_yaxis()
    fig.suptitle('MicrobeAtlas × all USGS elements: KO density → log-ppm\n'
                 f'(full controls; {MIN_GENERA}+ genera; {len(elements_to_test)} elements tested)',
                 y=1.02, fontsize=10, fontweight='bold')
    save(fig, FIGS / 'fig_nb06_all_usgs_forest')
    print('\nSaved: fig_nb06_all_usgs_forest.pdf')

print('\nDone.')
