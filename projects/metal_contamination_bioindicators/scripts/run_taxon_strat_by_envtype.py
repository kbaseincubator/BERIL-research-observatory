"""
run_taxon_strat_by_envtype.py

Re-runs the taxon EF analysis stratified by sample environment type:
  terrestrial — environments contains 'soil' but not 'aquatic' or 'animal'
  aquatic     — environments contains 'aquatic' (lake, river, marine, sediment)
  plant       — environments starts with 'plant' (but not soil)

Uses the full 180K CLR sample set joined to the environments metadata.
Only runs USA-USGS soil (usa_ma2) and EUR (eur_ma) since those have ≥2 studies.
Model: M3 (lat, lon, sg_ph, sg_cec, sg_clay, sg_soc) where covariates are available.
       For strata without SoilGrids coverage, falls back to M1.

Output: taxon_M3_{stratum}_{thr}_ef_{elem}_{level}_{region}.csv
  e.g.: taxon_M3_terrestrial_con_ef_cu_genus_eur_ma.csv
        taxon_M3_aquatic_con_ef_cu_genus_usa_ma2.csv

Note: 'soil' samples in the existing analysis ARE mostly terrestrial already
(the SoilGrids-joined subset is pre-filtered to soil). This script specifically
tests whether INCLUDING aquatic+plant samples in the full CLR set changes signals.
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
SG_COLS    = ['sg_ph', 'sg_cec', 'sg_clay', 'sg_soc']

CRUSTAL = {
    'Ag': 0.070, 'As': 1.8,  'Ba': 550,  'Be': 2.8,  'Bi': 0.17,
    'Cd': 0.098, 'Co': 29,   'Cr': 185,  'Cs': 3.7,  'Cu': 75,
    'Ga': 18,    'Ge': 1.4,  'Hg': 0.056,'In': 0.05, 'Li': 18,
    'Mn': 1400,  'Mo': 1.5,  'Nb': 19,   'Ni': 105,  'Pb': 20,
    'Rb': 82,    'Sb': 0.20, 'Sc': 30,   'Se': 0.12, 'Sn': 5.5,
    'Sr': 465,   'Ta': 1.5,  'Th': 10.7, 'Tl': 0.60, 'U':  2.8,
    'V':  230,   'W':  1.0,  'Y':  22,   'Zn': 80,   'Zr': 190,
}

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


def run_strat_analysis(df_samp, taxon_ids, taxon_clr_full, taxon_clr_cols,
                       exposure_col, study_col, min_n, sg_cols=None):
    """Fisher-z meta-analysis on stratified sample subset."""
    base_cols = list(set(['sample_id', study_col, 'lat', 'lon', exposure_col] +
                         (list(sg_cols) if sg_cols else [])))
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
    if sg_cols:
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

        if sg_cols:
            sg_arrs = []
            for c in sg_cols:
                v = sg_data[c][mask]
                v = np.where(np.isfinite(v), v, np.nanmean(v) if np.isfinite(v).any() else 0.0)
                sg_arrs.append(v)
            cov = np.column_stack([lat_vals[mask], lon_vals[mask]] + sg_arrs)
        else:
            cov = np.column_stack([lat_vals[mask], lon_vals[mask]])

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
        tax_ranks = np.empty_like(tax_work32)
        for j in range(tax_work32.shape[1]):
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


# =============================================================================
# Phase 0 — Load shared data
# =============================================================================
print("=" * 65)
print("Phase 0 — Shared data")
print("=" * 65)

# Load environments
env_df = pd.read_parquet(DATA / 'sample_environments.parquet')
print(f"  Environments: {len(env_df):,} samples")

# Define strata masks in the full CLR set
env_df['is_terrestrial'] = (
    env_df['environments'].str.contains('soil', na=False) &
    ~env_df['environments'].str.contains('aquatic|animal', na=False)
)
env_df['is_aquatic'] = (
    env_df['environments'].str.contains('aquatic', na=False) &
    ~env_df['environments'].str.contains('soil', na=False)
)
env_df['is_plant'] = (
    env_df['environments'].str.startswith('plant', na=False) &
    ~env_df['environments'].str.contains('soil|aquatic', na=False)
)

print(f"  Terrestrial (soil, non-aquatic): {env_df['is_terrestrial'].sum():,}")
print(f"  Aquatic (non-soil): {env_df['is_aquatic'].sum():,}")
print(f"  Plant (non-soil, non-aquatic): {env_df['is_plant'].sum():,}")

STRATA = {
    'terrestrial': 'is_terrestrial',
    'aquatic':     'is_aquatic',
    'plant':       'is_plant',
}

# Load CLR matrices
print("  Loading taxon CLR matrices …")
level_data = {}
for lname, lpath, _ in LEVELS:
    if not lpath.exists():
        print(f"MISSING: {lpath}")
        raise SystemExit(1)
    clr_df = pd.read_parquet(lpath)
    if 'sample_id' not in clr_df.columns:
        clr_df = clr_df.reset_index()
    clr_df = clr_df.merge(env_df[['sample_id', 'is_terrestrial', 'is_aquatic', 'is_plant']],
                          on='sample_id', how='left')
    taxon_cols = [c for c in clr_df.columns if c not in
                  ['sample_id', 'is_terrestrial', 'is_aquatic', 'is_plant']]
    level_data[lname] = {'df': clr_df, 'cols': taxon_cols, 'ids': taxon_cols}
    print(f"    {lname}: {len(clr_df):,} samples × {len(taxon_cols)} taxa")

# Load SoilGrids covariates (for M3 where available)
sg_all = pd.read_parquet(DATA / 'soilgrids_sample_covariates.parquet')


# =============================================================================
# Phase 1 — EUR (GEMAS): stratified analysis
# =============================================================================
print("\n" + "=" * 65)
print("Phase 1 — EUR (GEMAS) stratified")
print("=" * 65)

eur_sg = sg_all.query('34 <= lat <= 72 and -12 <= lon <= 45').copy()
gemas = pd.read_parquet(ENVDBS / 'gemas_data' / 'gemas_final.parquet')
gemas = gemas.rename(columns={'latitude': 'g_lat', 'longitude': 'g_lon'}).dropna(subset=['g_lat', 'g_lon'])
tree_eur = cKDTree(gemas[['g_lat', 'g_lon']].to_numpy())
dist_deg, idx_eur = tree_eur.query(eur_sg[['lat', 'lon']].to_numpy(), k=1)
dist_km = dist_deg * 111.0
eur_joined = eur_sg[dist_km <= MAX_KM].copy().reset_index(drop=True)
gemas_m = gemas.iloc[idx_eur[dist_km <= MAX_KM]].reset_index(drop=True)

elements_eur = []
for elem, crust in CRUSTAL.items():
    col = f'{elem}_ppm_AR'
    if col in gemas.columns:
        raw = gemas_m[col].values if col in gemas_m.columns else np.full(len(eur_joined), np.nan)
        eur_joined[f'ef_{elem.lower()}'] = np.log10(np.where(raw > 0, raw, np.nan) / crust)
        elements_eur.append(elem.lower())

print(f"  EUR joined: {len(eur_joined):,} samples, {eur_joined['study_id'].nunique()} studies, {len(elements_eur)} elements")

# For each stratum × level × element:
# The full CLR matrix already has all 180K samples; we filter to stratum samples
# and also restrict to those that have SoilGrids covariates (for M3)
# For aquatic and plant, SoilGrids coverage will be sparse — use M1 fallback.

for stratum_label, stratum_col in STRATA.items():
    for lname, linfo in level_data.items():
        # Stratum-specific CLR subset
        strat_clr = linfo['df'][linfo['df'][stratum_col] == True][['sample_id'] + linfo['cols']]
        print(f"\n  [{lname}] EUR {stratum_label}: {len(strat_clr):,} CLR samples in stratum")

        # Merge eur_joined sample IDs with stratum CLR
        strat_ids = set(strat_clr['sample_id'].tolist())
        eur_strat = eur_joined[eur_joined['sample_id'].isin(strat_ids)].copy()
        if eur_strat['study_id'].nunique() < 2:
            print(f"    Skipping: <2 studies in stratum")
            continue

        # Attach SoilGrids covariates where not already present
        missing_sg = [c for c in SG_COLS if c not in eur_strat.columns]
        if missing_sg:
            eur_strat = eur_strat.merge(sg_all[['sample_id'] + missing_sg], on='sample_id', how='left')
        sg_coverage = eur_strat[SG_COLS[0]].notna().mean() if SG_COLS[0] in eur_strat.columns else 0.0
        use_sg = sg_coverage > 0.5
        sg_cols_use = SG_COLS if use_sg else None

        print(f"    n={len(eur_strat):,}, studies={eur_strat['study_id'].nunique()}, "
              f"SG coverage={sg_coverage:.0%}, model={'M3' if use_sg else 'M1'}")

        for thr_label, min_n in [('con', MIN_N_CON), ('lib', MIN_N_LIB)]:
            for elem in elements_eur:
                col = f'ef_{elem}'
                if col not in eur_strat.columns:
                    continue
                model_label = 'M3' if use_sg else 'M1'
                out_f = DATA / f'taxon_{model_label}_{stratum_label}_{thr_label}_ef_{elem}_{lname}_eur_ma.csv'
                if out_f.exists():
                    continue
                res = run_strat_analysis(
                    eur_strat, linfo['ids'], strat_clr, linfo['cols'],
                    col, 'study_id', min_n, sg_cols=sg_cols_use
                )
                if len(res) == 0 or res['n_studies'].max() < 2:
                    continue
                n_sig = (res['q_value'] < 0.05).sum()
                print(f"    {model_label}/{stratum_label}/{thr_label}/{elem}: "
                      f"n_studies={res['n_studies'].max()}, n_sig={n_sig} → {out_f.name}")
                res.to_csv(out_f, index=False)

print("\nDone.")
