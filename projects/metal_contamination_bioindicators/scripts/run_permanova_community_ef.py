"""
run_permanova_community_ef.py

Multivariate community composition × metal EF — per-study conditional PERMANOVA.

For each study with ≥30 samples:
  1. Compute genus CLR Euclidean distance (= Aitchison distance)
  2. Run partial PERMANOVA: community ~ EF | lat + lon + sg_covariates
     - Residualise CLR matrix and EF on covariates separately
     - PERMANOVA on residualised CLR distances vs residualised EF
  3. Record R², F-stat, p-value (999 permutations)

Meta-analysis: weight R² by sample count across studies.

Also runs stratified by:
  terrestrial  — environments starts with 'soil' (but not aquatic)
  aquatic      — environments contains 'aquatic'
  all          — no filter (just the 28K SoilGrids soil subset)

Outputs:
  data/permanova_{model}_{stratum}_{elem}.csv
  data/permanova_summary_{model}_{stratum}.csv
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys, warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from sklearn.linear_model import LinearRegression
from statsmodels.stats.multitest import multipletests

DATA   = Path('projects/metal_contamination_bioindicators/data')
ENVDBS = Path.home() / 'data' / 'envdbs'
USGS   = ENVDBS / 'usgs_geochem'

MIN_N_STUDY  = 30    # min samples per study for PERMANOVA
N_PERMS      = 999   # permutations
MAX_KM       = 100.0
MAX_KM_AUS   = 50.0
MIN_SITES    = 50

SG_COLS = ['sg_ph', 'sg_cec', 'sg_clay', 'sg_soc']

CRUSTAL = {
    'Ag': 0.070, 'As': 1.8,  'Ba': 550,  'Be': 2.8,  'Bi': 0.17,
    'Cd': 0.098, 'Co': 29,   'Cr': 185,  'Cs': 3.7,  'Cu': 75,
    'Ga': 18,    'Ge': 1.4,  'Hg': 0.056,'In': 0.05, 'Li': 18,
    'Mn': 1400,  'Mo': 1.5,  'Nb': 19,   'Ni': 105,  'Pb': 20,
    'Rb': 82,    'Sb': 0.20, 'Sc': 30,   'Se': 0.12, 'Sn': 5.5,
    'Sr': 465,   'Ta': 1.5,  'Th': 10.7, 'Tl': 0.60, 'U':  2.8,
    'V':  230,   'W':  1.0,  'Y':  22,   'Zn': 80,   'Zr': 190,
}


# =============================================================================
# PERMANOVA helpers
# =============================================================================

def partial_residuals_matrix(Y, X):
    """Residualise each column of Y on X; return residual matrix."""
    valid = np.all(np.isfinite(X), axis=1) & np.all(np.isfinite(Y), axis=1)
    out = np.full_like(Y, np.nan, dtype='float64')
    if valid.sum() < 5:
        out[valid] = Y[valid] - Y[valid].mean(axis=0)
        return out
    lr = LinearRegression()
    lr.fit(X[valid], Y[valid])
    out[valid] = Y[valid] - lr.predict(X[valid])
    return out


def partial_residuals_vec(y, X):
    """Residualise scalar y on X; return residual vector."""
    valid = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    out = np.full(len(y), np.nan)
    if valid.sum() < 5:
        out[valid] = y[valid] - y[valid].mean()
        return out
    lr = LinearRegression()
    lr.fit(X[valid], y[valid])
    out[valid] = y[valid] - lr.predict(X[valid])
    return out


def permanova_one(D2, groups, n_perms=999):
    """
    One-way PERMANOVA on squared distance matrix D2 for binary groups.
    Uses vectorised SS computation: fast for 999 permutations.
    Returns (F_stat, p_value, R2).
    """
    n = len(groups)
    g1 = groups.astype(bool)
    g0 = ~g1
    n1, n0 = g1.sum(), g0.sum()

    total_ss = D2.sum() / (2 * n)

    def sw_binary(mask1, mask0):
        n1i = mask1.sum()
        n0i = mask0.sum()
        sw1 = D2[np.ix_(mask1, mask1)].sum() / (2 * n1i) if n1i > 1 else 0.0
        sw0 = D2[np.ix_(mask0, mask0)].sum() / (2 * n0i) if n0i > 1 else 0.0
        return sw1 + sw0

    sw_obs = sw_binary(g1, g0)
    sb_obs = total_ss - sw_obs
    R2_obs = sb_obs / total_ss if total_ss > 0 else 0.0
    F_obs  = (sb_obs / 1) / (sw_obs / (n - 2)) if sw_obs > 0 else 0.0

    count = 0
    rng = np.random.default_rng(42)
    for _ in range(n_perms):
        perm = rng.permutation(groups).astype(bool)
        sw_p = sw_binary(perm, ~perm)
        sb_p = total_ss - sw_p
        F_p = (sb_p / 1) / (sw_p / (n - 2)) if sw_p > 0 else 0.0
        if F_p >= F_obs:
            count += 1
    p_val = (count + 1) / (n_perms + 1)
    return F_obs, p_val, R2_obs


def run_permanova_study(clr_mat, ef_vec, lat, lon, sg_vals, model='M3'):
    """
    Per-study conditional PERMANOVA.
    - Residualise CLR and EF on covariates
    - Compute distance on residual CLR
    - Split EF into top/bottom tertile and run PERMANOVA
    Returns (F_stat, p_value, R2, n) or None if insufficient data.
    """
    valid = np.isfinite(ef_vec) & np.all(np.isfinite(clr_mat), axis=1)
    if valid.sum() < MIN_N_STUDY:
        return None

    ef_v = ef_vec[valid]
    clr_v = clr_mat[valid]
    lat_v = lat[valid]
    lon_v = lon[valid]
    sg_v  = sg_vals[valid]

    n = valid.sum()

    if model == 'M0':
        clr_r = clr_v - clr_v.mean(axis=0)
        ef_r  = ef_v - ef_v.mean()
    elif model == 'M1':
        cov = np.column_stack([lat_v, lon_v])
        clr_r = partial_residuals_matrix(clr_v, cov)
        ef_r  = partial_residuals_vec(ef_v, cov)
        nf = np.all(np.isfinite(clr_r), axis=1) & np.isfinite(ef_r)
        clr_r, ef_r, n = clr_r[nf], ef_r[nf], nf.sum()
    elif model == 'M3':
        cov = np.column_stack([lat_v, lon_v] + [sg_v[:, j] for j in range(sg_v.shape[1])])
        # impute NaN SG columns with column mean
        for j in range(cov.shape[1]):
            bad = ~np.isfinite(cov[:, j])
            if bad.any():
                cov[bad, j] = np.nanmean(cov[:, j]) if np.isfinite(cov[:, j]).any() else 0.0
        clr_r = partial_residuals_matrix(clr_v, cov)
        ef_r  = partial_residuals_vec(ef_v, cov)
        nf = np.all(np.isfinite(clr_r), axis=1) & np.isfinite(ef_r)
        clr_r, ef_r, n = clr_r[nf], ef_r[nf], nf.sum()

    if n < MIN_N_STUDY:
        return None

    # Distance matrix on residual CLR
    D = cdist(clr_r, clr_r, metric='euclidean')
    D2 = D ** 2

    # Split EF into high/low tertile (exclude middle)
    t33, t67 = np.percentile(ef_r, [33, 67])
    lo = ef_r <= t33
    hi = ef_r >= t67
    keep = lo | hi
    if (lo & keep).sum() < 5 or (hi & keep).sum() < 5:
        return None
    groups = np.where(hi[keep], 1, 0)
    D2_sub = D2[np.ix_(keep, keep)]

    F_stat, p_val, R2 = permanova_one(D2_sub, groups, N_PERMS)
    return F_stat, p_val, R2, int(keep.sum())


def meta_permanova(results_df):
    """
    Weighted meta-analysis of PERMANOVA R² across studies.
    Uses sample-count weighting and Fisher's combined p-value.
    """
    valid = results_df.dropna(subset=['R2', 'p_value', 'n_samples'])
    if len(valid) == 0:
        return dict(mean_R2=np.nan, pooled_p=np.nan, n_studies=0, n_samples_total=0)

    w = valid['n_samples'].values.astype('float64')
    R2 = valid['R2'].values
    mean_R2 = np.average(R2, weights=w)

    # Fisher's combined p
    from scipy.stats import chi2
    ps = np.clip(valid['p_value'].values, 1e-300, 1.0)
    chi_sq = -2 * np.sum(np.log(ps))
    df_chi = 2 * len(ps)
    pooled_p = 1 - chi2.cdf(chi_sq, df=df_chi)

    return dict(
        mean_R2=mean_R2,
        pooled_p=pooled_p,
        n_studies=len(valid),
        n_samples_total=int(w.sum()),
    )


# =============================================================================
# Phase 0 — Load shared data
# =============================================================================
print("=" * 65)
print("Phase 0 — Load shared data")
print("=" * 65)

sg = pd.read_parquet(DATA / 'soilgrids_sample_covariates.parquet')
print(f"  SoilGrids: {len(sg):,} samples, {sg['study_id'].nunique()} studies")

# Load environments for sample type stratification
env_df = pd.read_parquet(DATA / 'sample_environments.parquet')
sg = sg.merge(env_df[['sample_id', 'environments']], on='sample_id', how='left')
print(f"  Environment metadata merged: {sg['environments'].notna().sum():,} matched")

# Define strata
sg['is_terrestrial'] = (
    sg['environments'].str.contains('soil', na=False) &
    ~sg['environments'].str.contains('aquatic|animal', na=False)
)
sg['is_aquatic'] = sg['environments'].str.contains('aquatic', na=False)
print(f"  Terrestrial (soil, non-aquatic): {sg['is_terrestrial'].sum():,}")
print(f"  Aquatic: {sg['is_aquatic'].sum():,}")

# Load genus CLR matrix
print("  Loading genus CLR matrix …")
clr_full = pd.read_parquet(DATA / 'clr_matrix.parquet')
if 'sample_id' not in clr_full.columns:
    clr_full = clr_full.reset_index()
clr_cols = [c for c in clr_full.columns if c != 'sample_id']
print(f"  CLR: {len(clr_full):,} samples × {len(clr_cols)} genera")


# =============================================================================
# Phase 1 — USGS variants
# =============================================================================
print("\n" + "=" * 65)
print("Phase 1 — USGS")
print("=" * 65)

USGS_META = USGS / 'usgs_geochem.parquet'
USGS_MEAS = USGS / 'usgs_geochem_joined.parquet'

USGS_VARIANTS = [
    ('usa_soil', 'soil'),
    ('usa_terr', None),
]

if USGS_META.exists() and USGS_MEAS.exists():
    usa_sg = sg.query('24 <= lat <= 50 and -125 <= lon <= -66').copy()
    print(f"  USA SoilGrids: {len(usa_sg):,} samples, {usa_sg['study_id'].nunique()} studies")

    usgs_meta = pd.read_parquet(USGS_META, columns=['group_id', 'latitude', 'longitude', 'primary_class'])
    usgs_meta = (usgs_meta.dropna(subset=['latitude', 'longitude'])
                 [usgs_meta['latitude'].between(24, 50) &
                  usgs_meta['longitude'].between(-125, -66)]
                 .drop_duplicates('group_id').reset_index(drop=True))
    chem_all = pd.read_parquet(USGS_MEAS, columns=['group_id', 'species', 'qualified_value'])
    chem_all = chem_all[chem_all['group_id'].isin(set(usgs_meta['group_id']))].copy()
    chem_all['qualified_value'] = pd.to_numeric(chem_all['qualified_value'], errors='coerce')

    for suffix, class_filter in USGS_VARIANTS:
        print(f"\n  --- Variant: {suffix} ---")
        if class_filter is not None:
            meta_v = usgs_meta[usgs_meta['primary_class'] == class_filter].copy()
        else:
            meta_v = usgs_meta.copy()
        v_gids = set(meta_v['group_id'])
        chem_v = chem_all[chem_all['group_id'].isin(v_gids)].copy()

        sp_cov = chem_v.groupby('species')['group_id'].nunique()
        keep_sp = sorted(sp_cov[sp_cov >= MIN_SITES].index)
        chem_v = chem_v[chem_v['species'].isin(keep_sp)]
        chem_agg = chem_v.groupby(['group_id', 'species'])['qualified_value'].median().reset_index()
        chem_wide = chem_agg.pivot(index='group_id', columns='species', values='qualified_value').reset_index()
        sites_v = meta_v[['group_id', 'latitude', 'longitude']].merge(
            chem_wide, on='group_id', how='inner').dropna(subset=['latitude', 'longitude'])

        # Compute EF
        elements_v = []
        for sp in keep_sp:
            if sp in CRUSTAL and sp in sites_v.columns:
                raw = sites_v[sp].values
                sites_v[f'ef_{sp.lower()}'] = np.log10(np.where(raw > 0, raw, np.nan) / CRUSTAL[sp])
                elements_v.append(sp.lower())
        ef_cols_v = [c for c in sites_v.columns if c.startswith('ef_')]

        # NN join to SoilGrids
        tree_v = cKDTree(sites_v[['latitude', 'longitude']].to_numpy())
        dist_km, idx_v = tree_v.query(usa_sg[['lat', 'lon']].to_numpy(), k=1)
        dist_km *= 111.0
        usa_joined = usa_sg[dist_km <= MAX_KM].copy().reset_index(drop=True)
        idx_matched = idx_v[dist_km <= MAX_KM]
        sites_eff = sites_v.iloc[idx_matched][ef_cols_v].reset_index(drop=True)
        usa_joined = pd.concat([usa_joined.reset_index(drop=True), sites_eff], axis=1)

        # Merge CLR
        df = usa_joined.merge(clr_full, on='sample_id', how='inner')
        print(f"  Final: {len(df):,} samples, {df['study_id'].nunique()} studies, {len(elements_v)} elements")

        sg_mat = df[SG_COLS].values.astype('float64')
        lat_arr = df['lat'].values
        lon_arr = df['lon'].values
        clr_arr = df[clr_cols].values.astype('float64')

        for model in ['M0', 'M1', 'M3']:
            for stratum, stratum_mask_col in [('all', None), ('terrestrial', 'is_terrestrial')]:
                smask = (df[stratum_mask_col].values if stratum_mask_col else
                         np.ones(len(df), dtype=bool))

                summary_rows = []
                for elem in elements_v:
                    ef_col = f'ef_{elem}'
                    if ef_col not in df.columns:
                        continue
                    out_f = DATA / f'permanova_{model}_{stratum}_{suffix}_{elem}.csv'
                    if out_f.exists():
                        continue

                    ef_arr = df[ef_col].values
                    study_ids = df['study_id'].values
                    study_results = []

                    for sid in np.unique(study_ids):
                        smask_s = (study_ids == sid) & smask & np.isfinite(ef_arr)
                        if smask_s.sum() < MIN_N_STUDY:
                            continue
                        result = run_permanova_study(
                            clr_arr[smask_s], ef_arr[smask_s],
                            lat_arr[smask_s], lon_arr[smask_s],
                            sg_mat[smask_s], model=model
                        )
                        if result is None:
                            continue
                        F_stat, p_val, R2, n_samp = result
                        study_results.append({
                            'study_id': sid, 'element': elem, 'model': model,
                            'stratum': stratum, 'region': suffix,
                            'F_stat': F_stat, 'p_value': p_val, 'R2': R2,
                            'n_samples': n_samp
                        })

                    if study_results:
                        res_df = pd.DataFrame(study_results)
                        res_df.to_csv(out_f, index=False)
                        meta = meta_permanova(res_df)
                        print(f"    {model}/{stratum}/{elem}: {meta['n_studies']} studies, "
                              f"mean_R2={meta['mean_R2']:.4f}, pooled_p={meta['pooled_p']:.4f}")


# =============================================================================
# Phase 2 — EUR (GEMAS)
# =============================================================================
print("\n" + "=" * 65)
print("Phase 2 — EUR (GEMAS)")
print("=" * 65)

eur = sg.query('34 <= lat <= 72 and -12 <= lon <= 45').copy()
print(f"  EUR SoilGrids: {len(eur):,} samples, {eur['study_id'].nunique()} studies")

gemas_f = ENVDBS / 'gemas_data' / 'gemas_final.parquet'
if gemas_f.exists():
    gemas = pd.read_parquet(gemas_f).rename(columns={'latitude': 'g_lat', 'longitude': 'g_lon'})
    gemas = gemas.dropna(subset=['g_lat', 'g_lon']).reset_index(drop=True)

    tree_eur = cKDTree(gemas[['g_lat', 'g_lon']].to_numpy())
    dist_deg, idx_eur = tree_eur.query(eur[['lat', 'lon']].to_numpy(), k=1)
    dist_km = dist_deg * 111.0
    eur_joined = eur[dist_km <= MAX_KM].copy().reset_index(drop=True)
    idx_eur_m = idx_eur[dist_km <= MAX_KM]

    ef_cols_eur = []
    for elem, crust in CRUSTAL.items():
        col = f'{elem}_ppm_AR'
        if col in gemas.columns:
            raw = gemas[col].values
            gemas[f'ef_{elem.lower()}'] = np.log10(np.where(raw > 0, raw, np.nan) / crust)
            ef_cols_eur.append(f'ef_{elem.lower()}')
    elements_eur = [c.replace('ef_', '') for c in ef_cols_eur]
    gemas_eff = gemas.iloc[idx_eur_m][ef_cols_eur].reset_index(drop=True)
    eur_joined = pd.concat([eur_joined.reset_index(drop=True), gemas_eff], axis=1)
    eur_joined = eur_joined.merge(clr_full, on='sample_id', how='inner')
    print(f"  EUR final: {len(eur_joined):,} samples, {eur_joined['study_id'].nunique()} studies")

    sg_mat = eur_joined[SG_COLS].values.astype('float64')
    lat_arr = eur_joined['lat'].values
    lon_arr = eur_joined['lon'].values
    clr_arr = eur_joined[clr_cols].values.astype('float64')
    study_ids = eur_joined['study_id'].values

    for model in ['M0', 'M1', 'M3']:
        for stratum, stratum_mask_col in [('all', None), ('terrestrial', 'is_terrestrial')]:
            smask = (eur_joined[stratum_mask_col].values if stratum_mask_col else
                     np.ones(len(eur_joined), dtype=bool))
            for elem in elements_eur:
                ef_col = f'ef_{elem}'
                if ef_col not in eur_joined.columns:
                    continue
                out_f = DATA / f'permanova_{model}_{stratum}_eur_{elem}.csv'
                if out_f.exists():
                    continue
                ef_arr = eur_joined[ef_col].values
                study_results = []
                for sid in np.unique(study_ids):
                    smask_s = (study_ids == sid) & smask & np.isfinite(ef_arr)
                    if smask_s.sum() < MIN_N_STUDY:
                        continue
                    result = run_permanova_study(
                        clr_arr[smask_s], ef_arr[smask_s],
                        lat_arr[smask_s], lon_arr[smask_s],
                        sg_mat[smask_s], model=model
                    )
                    if result is None:
                        continue
                    F_stat, p_val, R2, n_samp = result
                    study_results.append({
                        'study_id': sid, 'element': elem, 'model': model,
                        'stratum': stratum, 'region': 'eur',
                        'F_stat': F_stat, 'p_value': p_val, 'R2': R2,
                        'n_samples': n_samp
                    })
                if study_results:
                    res_df = pd.DataFrame(study_results)
                    res_df.to_csv(out_f, index=False)
                    meta = meta_permanova(res_df)
                    print(f"    {model}/{stratum}/{elem}: {meta['n_studies']} studies, "
                          f"mean_R2={meta['mean_R2']:.4f}, pooled_p={meta['pooled_p']:.4f}")


# =============================================================================
# Aggregate summary
# =============================================================================
print("\n" + "=" * 65)
print("Summary")
print("=" * 65)

all_csvs = list(DATA.glob('permanova_M3_all_*.csv'))
print(f"Found {len(all_csvs)} M3/all result files")

summary_rows = []
for f in all_csvs:
    df = pd.read_csv(f)
    meta = meta_permanova(df)
    parts = f.stem.split('_')  # permanova_M3_all_{region}_{elem}
    elem = parts[-1]
    region = parts[-2]
    meta.update({'model': 'M3', 'stratum': 'all', 'region': region, 'element': elem})
    summary_rows.append(meta)

if summary_rows:
    summ = pd.DataFrame(summary_rows).sort_values('mean_R2', ascending=False)
    summ.to_csv(DATA / 'permanova_summary_M3_all.csv', index=False)
    print("\nTop PERMANOVA results (M3, all, by mean R²):")
    print(summ.head(20).to_string(index=False))

print("\nDone.")
