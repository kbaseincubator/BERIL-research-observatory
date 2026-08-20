"""
run_taxon_m3plus.py

M3+ model for taxon CLR × metal EF: adds sg_sand and sg_nitrogen to M3 covariates.
Runs all 5 taxonomic levels × 7 regions, con and lib thresholds.

Output files: taxon_M3plus_{thr}_{ef}_{elem}_{level}_{region}.csv
(Same structure as existing taxon_M3_* files, allowing direct comparison.)

Covariate sets:
  M3:    lat, lon, sg_ph, sg_cec, sg_clay, sg_soc
  M3plus: lat, lon, sg_ph, sg_cec, sg_clay, sg_soc, sg_sand, sg_nitrogen
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys, warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.stats import rankdata, norm
from sklearn.linear_model import LinearRegression
from statsmodels.stats.multitest import multipletests

DATA   = Path('projects/metal_contamination_bioindicators/data')
ENVDBS = Path.home() / 'data' / 'envdbs'
USGS   = ENVDBS / 'usgs_geochem'

MIN_N_CON  = 20
MIN_N_LIB  = 8
MIN_SITES  = 50
MAX_KM     = 100.0
MAX_KM_AUS = 50.0
N_PCA      = 5
SG_COLS    = ['sg_ph', 'sg_cec', 'sg_clay', 'sg_soc']
SG_COLS_PLUS = ['sg_ph', 'sg_cec', 'sg_clay', 'sg_soc', 'sg_sand', 'sg_nitrogen']
GLIM_F     = ENVDBS / 'global_lithology_glim.parquet'
NGSA_F     = Path('projects/comprehensive_metal_ecology/data/ngsa_geochemistry.csv')
CMMI_F     = Path('projects/microbeatlas_metal_ecology/data/cmmi_ores.csv')

CRUSTAL = {
    'Ag': 0.070, 'As': 1.8,  'Ba': 550,  'Be': 2.8,  'Bi': 0.17,
    'Cd': 0.098, 'Co': 29,   'Cr': 185,  'Cs': 3.7,  'Cu': 75,
    'Ga': 18,    'Ge': 1.4,  'Hg': 0.056,'In': 0.05, 'Li': 18,
    'Mn': 1400,  'Mo': 1.5,  'Nb': 19,   'Ni': 105,  'Pb': 20,
    'Rb': 82,    'Sb': 0.20, 'Sc': 30,   'Se': 0.12, 'Sn': 5.5,
    'Sr': 465,   'Ta': 1.5,  'Th': 10.7, 'Tl': 0.60, 'U':  2.8,
    'V':  230,   'W':  1.0,  'Y':  22,   'Zn': 80,   'Zr': 190,
}

CMMI_ELEM_MAP = {
    'as_ppm': 'as', 'cd_ppm': 'cd', 'co_ppm': 'co', 'cr_ppm': 'cr',
    'cu_ppm': 'cu', 'ni_ppm': 'ni', 'pb_ppm': 'pb', 'zn_ppm': 'zn',
}

USGS_VARIANTS = [
    ('usa_ma2',  'soil'),
    ('usa_terr', None),
    ('usa_sed',  'sediment'),
    ('usa_rock', 'rock'),
]

LEVELS = [
    ('genus',  DATA / 'clr_matrix.parquet',  'clr_'),
    ('family', DATA / 'clr_family.parquet',  'clr_'),
    ('order',  DATA / 'clr_order.parquet',   'clr_'),
    ('class',  DATA / 'clr_class.parquet',   'clr_'),
    ('phylum', DATA / 'clr_phylum.parquet',  'clr_'),
]


def partial_residuals(X, covariates):
    valid = np.isfinite(X) & np.all(np.isfinite(covariates), axis=1)
    if valid.sum() < 5:
        out = np.full(len(X), np.nan)
        out[valid] = X[valid] - X[valid].mean()
        return out
    lr = LinearRegression()
    lr.fit(covariates[valid], X[valid])
    resid = np.full(len(X), np.nan)
    resid[valid] = X[valid] - lr.predict(covariates[valid])
    return resid


def attach_glim(df, lat_col, lon_col, glim, tree_glim):
    _, idx = tree_glim.query(df[[lat_col, lon_col]].to_numpy(), k=1)
    df = df.copy()
    df['lith_class'] = glim['lithology_class'].iloc[idx].values
    dummies = pd.get_dummies(df['lith_class'], prefix='lith', drop_first=True).astype('float32')
    lith_full_cols = dummies.columns.tolist()
    df = pd.concat([df.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
    df['is_basic_plutonic'] = (df['lith_class'] == 'Basic Plutonic (PB)').astype('float32')
    return df, 'is_basic_plutonic', lith_full_cols


def run_taxon_m3plus(df_samp, taxon_ids, taxon_clr_full, taxon_clr_cols,
                     exposure_col, study_col, min_n):
    """M3+ model: M3 covariates + sg_sand + sg_nitrogen."""
    sg_cols = SG_COLS_PLUS
    base_cols = list(set(['sample_id', study_col, 'lat', 'lon', exposure_col] + sg_cols))
    available = [c for c in base_cols if c in df_samp.columns]

    df = (df_samp[available].dropna(subset=['lat', 'lon', exposure_col])
          .merge(taxon_clr_full[['sample_id'] + taxon_clr_cols], on='sample_id', how='inner'))
    df = df[np.isfinite(df[exposure_col])].reset_index(drop=True)
    if len(df) < min_n:
        return pd.DataFrame()

    TAX_ARR   = df[taxon_clr_cols].values.astype('float32')
    exp_vals  = df[exposure_col].values.astype('float64')
    study_ids = df[study_col].values
    lat_vals  = df['lat'].values.astype('float64')
    lon_vals  = df['lon'].values.astype('float64')

    sg_data = {}
    for c in sg_cols:
        sg_data[c] = df[c].values.astype('float64') if c in df.columns else np.full(len(df), np.nan)

    n_tax = len(taxon_ids)
    z_acc  = np.zeros(n_tax, 'float64')
    w_acc  = np.zeros(n_tax, 'float64')
    ns_acc = np.zeros(n_tax, int)
    nv_acc = np.zeros(n_tax, int)

    for sid in np.unique(study_ids):
        mask = study_ids == sid
        n_s  = mask.sum()
        if n_s < min_n:
            continue
        exp_s  = exp_vals[mask]
        tax_s  = TAX_ARR[mask].astype('float64')

        sg_arrs = []
        for c in sg_cols:
            v = sg_data[c][mask]
            v = np.where(np.isfinite(v), v, np.nanmean(v) if np.isfinite(v).any() else 0.0)
            sg_arrs.append(v)
        cov = np.column_stack([lat_vals[mask], lon_vals[mask]] + sg_arrs)

        exp_r = partial_residuals(exp_s, cov)
        valid_e = np.isfinite(exp_r)
        if valid_e.sum() < min_n:
            continue
        exp_work = exp_r[valid_e]
        tax_work = np.column_stack([
            partial_residuals(tax_s[:, j], cov)
            for j in range(tax_s.shape[1])])[valid_e]

        n = len(exp_work)
        exp_rank = rankdata(exp_work) - (n + 1) / 2.0
        exp_std  = exp_rank.std()
        if exp_std == 0:
            continue
        exp_rank /= (n * exp_std)
        tax_work32 = tax_work.astype('float32')
        n_t = tax_work32.shape[1]
        tax_ranks = np.empty_like(tax_work32)
        for j in range(n_t):
            tax_ranks[:, j] = rankdata(tax_work32[:, j]) - (n + 1) / 2.0
        tax_stds = tax_ranks.std(axis=0)
        tax_stds[tax_stds == 0] = np.nan
        rho_vec = exp_rank @ (tax_ranks - tax_ranks.mean(axis=0)) / tax_stds
        rho_vec = np.clip(rho_vec, -0.9999, 0.9999)
        z_vec   = np.arctanh(rho_vec)
        wt      = max(n - 3, 1)
        finite  = np.isfinite(z_vec)
        z_acc  += np.where(finite, wt * z_vec, 0.0)
        w_acc  += np.where(finite, wt, 0.0)
        ns_acc += finite.astype(int)
        nv_acc += np.where(finite, n, 0)

    valid = w_acc > 0
    if valid.sum() == 0:
        return pd.DataFrame()
    z_norm = np.where(valid, z_acc / w_acc, np.nan)
    z_stat = np.where(valid, z_norm * np.sqrt(w_acc), np.nan)
    p_val  = np.where(np.isfinite(z_stat), 2 * norm.sf(np.abs(z_stat)), np.nan)
    res = pd.DataFrame({'taxon': taxon_ids,
                        'mean_rho': np.tanh(z_norm),
                        'n_studies': ns_acc, 'n_samples': nv_acc,
                        'z_stat': z_stat, 'p_value': p_val})
    res = res[res['n_studies'] > 0].copy()
    valid_p = res['p_value'].notna()
    q_arr = np.full(len(res), np.nan)
    if valid_p.sum() > 0:
        _, q_vals, _, _ = multipletests(res.loc[valid_p, 'p_value'].values, method='fdr_bh')
        q_arr[valid_p.values] = q_vals
    res['q_value'] = q_arr
    return res.sort_values('p_value')


def run_region_m3plus(label, df_samp, elements, suffix,
                      taxon_clr_full, taxon_clr_cols, taxon_ids, level_name):
    print(f"\n  [{level_name}] Region: {label} | {len(df_samp):,} samp | "
          f"{df_samp['study_id'].nunique()} studies | {len(elements)} elements")

    for thr_label, min_n in [('con', MIN_N_CON), ('lib', MIN_N_LIB)]:
        for elem in elements:
            col = f'ef_{elem}'
            if col not in df_samp.columns:
                continue
            out_f = DATA / f'taxon_M3plus_{thr_label}_ef_{elem}_{level_name}_{suffix}.csv'
            if out_f.exists():
                continue
            res = run_taxon_m3plus(
                df_samp, taxon_ids, taxon_clr_full, taxon_clr_cols,
                col, 'study_id', min_n
            )
            n_sig = (res['q_value'] < 0.05).sum() if len(res) else 0
            n_stud = res['n_studies'].max() if len(res) else 0
            n_samp = res['n_samples'].max() if len(res) else 0
            # Skip if single-study
            if n_stud < 2:
                continue
            print(f"    M3plus/{thr_label}/{elem}: n={n_samp}, {n_stud} stud, "
                  f"{n_sig} q<0.05 → {out_f.name}")
            if len(res):
                res.to_csv(out_f, index=False)


# =============================================================================
# Phase 0 — Shared data
# =============================================================================
print("=" * 65)
print("Phase 0 — Shared data (M3+)")
print("=" * 65)

for lname, lpath, _ in LEVELS:
    if not lpath.exists():
        print(f"MISSING: {lpath}")
        raise SystemExit(1)

sg_all = pd.read_parquet(DATA / 'soilgrids_sample_covariates.parquet')
print(f"  SoilGrids samples: {len(sg_all):,}")
print(f"  sg_sand available: {'sg_sand' in sg_all.columns}")
print(f"  sg_nitrogen available: {'sg_nitrogen' in sg_all.columns}")

glim = pd.read_parquet(GLIM_F)
tree_glim = cKDTree(glim[['lat', 'lon']].to_numpy())

print("  Loading taxon CLR matrices …")
level_data = {}
for lname, lpath, _ in LEVELS:
    clr_df = pd.read_parquet(lpath)
    if 'sample_id' not in clr_df.columns:
        clr_df = clr_df.reset_index()
    taxon_cols = [c for c in clr_df.columns if c != 'sample_id']
    level_data[lname] = {'df': clr_df, 'cols': taxon_cols, 'ids': taxon_cols}
    print(f"    {lname}: {len(clr_df):,} samples × {len(taxon_cols)} taxa")


# =============================================================================
# Phase 1 — USGS variants
# =============================================================================
print("\n" + "=" * 65)
print("Phase 1 — USGS variants")
print("=" * 65)

USGS_META = USGS / 'usgs_geochem.parquet'
USGS_MEAS = USGS / 'usgs_geochem_joined.parquet'

if USGS_META.exists() and USGS_MEAS.exists():
    usa_sg = sg_all.query('24 <= lat <= 50 and -125 <= lon <= -66').copy()
    usa_sg, pb_col_usa, _ = attach_glim(usa_sg, 'lat', 'lon', glim, tree_glim)

    usgs_meta = pd.read_parquet(USGS_META, columns=['group_id', 'latitude', 'longitude', 'primary_class'])
    usgs_meta = (usgs_meta.dropna(subset=['latitude', 'longitude'])
                 [usgs_meta['latitude'].between(24, 50) & usgs_meta['longitude'].between(-125, -66)]
                 .drop_duplicates('group_id').reset_index(drop=True))
    chem_all = pd.read_parquet(USGS_MEAS, columns=['group_id', 'species', 'qualified_value'])
    chem_all = chem_all[chem_all['group_id'].isin(set(usgs_meta['group_id']))].copy()
    chem_all['qualified_value'] = pd.to_numeric(chem_all['qualified_value'], errors='coerce')

    for suffix, class_filter in USGS_VARIANTS:
        print(f"\n  --- Variant: {suffix} ---")
        meta_v = usgs_meta if class_filter is None else usgs_meta[usgs_meta['primary_class'] == class_filter]
        v_gids = set(meta_v['group_id'])
        chem_v = chem_all[chem_all['group_id'].isin(v_gids)].copy()

        sp_cov = chem_v.groupby('species')['group_id'].nunique()
        keep_sp = sorted(sp_cov[sp_cov >= MIN_SITES].index)
        if not keep_sp:
            continue
        chem_v = chem_v[chem_v['species'].isin(keep_sp)]
        chem_agg = chem_v.groupby(['group_id', 'species'])['qualified_value'].median().reset_index()
        chem_wide = chem_agg.pivot(index='group_id', columns='species', values='qualified_value').reset_index()
        sites_v = meta_v[['group_id', 'latitude', 'longitude']].merge(chem_wide, on='group_id', how='inner')

        elements_v = []
        for sp in keep_sp:
            if sp in CRUSTAL and sp in sites_v.columns:
                sites_v[f'ef_{sp.lower()}'] = np.log10(
                    np.where(sites_v[sp].values > 0, sites_v[sp].values, np.nan) / CRUSTAL[sp])
                elements_v.append(sp.lower())

        tree_v = cKDTree(sites_v[['latitude', 'longitude']].to_numpy())
        dist_km, idx_v = tree_v.query(usa_sg[['lat', 'lon']].to_numpy(), k=1)
        dist_km *= 111.0
        usa_joined_v = usa_sg[dist_km <= MAX_KM].copy().reset_index(drop=True)
        idx_v2 = idx_v[dist_km <= MAX_KM]
        ef_cols_v = [c for c in sites_v.columns if c.startswith('ef_')]
        sites_eff = sites_v.iloc[idx_v2][ef_cols_v].reset_index(drop=True)
        usa_joined_v = pd.concat([usa_joined_v.reset_index(drop=True), sites_eff], axis=1)
        print(f"  {len(usa_joined_v):,} samples within {MAX_KM} km, "
              f"{usa_joined_v['study_id'].nunique()} studies")

        for lname, linfo in level_data.items():
            run_region_m3plus(f'USA ({suffix})', usa_joined_v, elements_v, suffix,
                              linfo['df'], linfo['cols'], linfo['ids'], lname)

    import gc; gc.collect()


# =============================================================================
# Phase 2 — EUR: GEMAS
# =============================================================================
print("\n" + "=" * 65)
print("Phase 2 — EUR: GEMAS")
print("=" * 65)

eur = sg_all.query('34 <= lat <= 72 and -12 <= lon <= 45').copy()
gemas = pd.read_parquet(ENVDBS / 'gemas_data' / 'gemas_final.parquet')
gemas = gemas.rename(columns={'latitude': 'g_lat', 'longitude': 'g_lon'})
gemas = gemas.dropna(subset=['g_lat', 'g_lon']).reset_index(drop=True)

tree_eur = cKDTree(gemas[['g_lat', 'g_lon']].to_numpy())
dist_deg, gemas_idx = tree_eur.query(eur[['lat', 'lon']].to_numpy(), k=1)
dist_km = dist_deg * 111.0
eur_joined = eur[dist_km <= MAX_KM].copy().reset_index(drop=True)
gemas_matched = gemas.iloc[gemas_idx[dist_km <= MAX_KM]].reset_index(drop=True)

ef_cols_eur = []
for elem, crust in CRUSTAL.items():
    col = f'{elem}_ppm_AR'
    if col in gemas.columns:
        raw = gemas_matched[col].values if col in gemas_matched.columns else np.full(len(eur_joined), np.nan)
        eur_joined[f'ef_{elem.lower()}'] = np.log10(np.where(raw > 0, raw, np.nan) / crust)
        ef_cols_eur.append(elem.lower())
print(f"  EUR: {len(eur_joined):,} samples, {eur_joined['study_id'].nunique()} studies, {len(ef_cols_eur)} elements")

for lname, linfo in level_data.items():
    run_region_m3plus('EUR', eur_joined, ef_cols_eur, 'eur_ma',
                      linfo['df'], linfo['cols'], linfo['ids'], lname)

import gc; gc.collect()


# =============================================================================
# Phase 3 — AUS: NGSA (skip — insufficient studies)
# =============================================================================
print("\n  AUS: skipped (insufficient studies for meta-analysis)")


# =============================================================================
# Phase 4 — CMMI
# =============================================================================
print("\n" + "=" * 65)
print("Phase 4 — CMMI")
print("=" * 65)

if CMMI_F.exists():
    cmmi = pd.read_csv(CMMI_F)
    usa_cmmi_sg = sg_all.query('24 <= lat <= 50 and -125 <= lon <= -66').copy()

    lat_col = [c for c in cmmi.columns if 'lat' in c.lower()][0]
    lon_col = [c for c in cmmi.columns if 'lon' in c.lower()][0]
    cmmi = cmmi.dropna(subset=[lat_col, lon_col]).reset_index(drop=True)

    tree_cmmi = cKDTree(cmmi[[lat_col, lon_col]].to_numpy())
    dist_km, idx_cmmi = tree_cmmi.query(usa_cmmi_sg[['lat', 'lon']].to_numpy(), k=1)
    dist_km *= 111.0
    usa_cmmi_joined = usa_cmmi_sg[dist_km <= MAX_KM].copy().reset_index(drop=True)
    cmmi_matched = cmmi.iloc[idx_cmmi[dist_km <= MAX_KM]].reset_index(drop=True)

    elements_cmmi = []
    for src_col, elem in CMMI_ELEM_MAP.items():
        if src_col in cmmi_matched.columns:
            raw = cmmi_matched[src_col].values.astype('float64')
            crust = CRUSTAL.get(elem.capitalize(), CRUSTAL.get(elem.upper(), None))
            if crust:
                usa_cmmi_joined[f'ef_{elem}'] = np.log10(np.where(raw > 0, raw, np.nan) / crust)
                elements_cmmi.append(elem)

    print(f"  CMMI: {len(usa_cmmi_joined):,} samples, {usa_cmmi_joined['study_id'].nunique()} studies")

    for lname, linfo in level_data.items():
        run_region_m3plus('CMMI', usa_cmmi_joined, elements_cmmi, 'usa_cmmi',
                          linfo['df'], linfo['cols'], linfo['ids'], lname)

print("\nDone.")
