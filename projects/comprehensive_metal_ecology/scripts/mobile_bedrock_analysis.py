"""
Mobile vs. bedrock metal PGLS analysis.

Tests whether horizontally mobile metal-resistance genes (high Fritz & Purvis D / low λ)
track bioavailable (mobile) metal fractions (CSU PF1 grid), while vertically inherited
cofactor genes track bedrock concentrations (GeoROC).

Analyses:
  A. Spearman ρ: mobile fraction vs bedrock concentration (Cu, Cr, Pb)
  B. Niche breadth ~ mobile metal PGLS (vs bedrock reference)
  C. Gene category density ~ mobile vs bedrock (Cu: cofactor, resistance)
  D. Double-signal gene presence fraction ~ mobile Cu + pH + SOM vs high-λ genes
  E. Variance partitioning: bedrock Cu + mobile Cu + pH + SOM → ko_per_mb
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

from pgls_utils import run_pgls

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'
REPORT = ROOT / 'report'
TREE = str(DATA / 'gtdb_bac_genus_pruned.tree')
MIN_N = 40           # minimum for PGLS (relaxed for soil-only)
MIN_N_SOIL = 25      # minimum for soil-only subset

# ─── Constants ────────────────────────────────────────────────────────────────
DOUBLE_SIGNAL_KOS = {
    'K19057': 'merD',  'K19059': 'merE',  'K07785': 'nrsD',
    'K19594': 'gesB',  'K19595': 'gesA',  'K08356': 'aoxB',
    'K19592': 'golS',  'K05908': 'doxDA', 'K08170': 'norB',
    'K25119': 'shp',   'K03897': 'iucD',  'K14974': 'nicC',
    'K15585': 'nikB',
}
HIGH_LAMBDA_KOS = {
    'K13638': 'zntR',  'K02230': 'cobN',  'K09883': 'cobT',
    'K02225': 'cobC1', 'K07787': 'cusA',  'K02190': 'cbiK',
    'K18367': 'CoADR', 'K03446': 'emrB',  'K15726': 'czcA',
    'K03673': 'dsbA',
}
METALS_OVERLAP = ['Cu', 'Cr', 'Pb']  # metals with both CSU and GeoROC data


# ─── Utilities ────────────────────────────────────────────────────────────────
def _z(s):
    v = s.dropna()
    if len(v) < 5 or v.std() == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - v.mean()) / v.std()

def pgls_model(df, label, response, predictors, tree=TREE, min_n=MIN_N):
    valid = df[predictors + [response, 'genus_lower']].dropna()
    n = len(valid)
    if n < min_n:
        return {'label': label, 'n': n, 'beta': np.nan, 'SE': np.nan,
                'p_value': np.nan, 'lambda_est': np.nan, 'status': f'SKIPPED_n={n}'}
    try:
        res = run_pgls(valid, tree, response=response, predictors=predictors,
                       taxon_col='genus_lower', label=label, min_n=min_n)
        if 'betas' in res and isinstance(res['betas'], dict):
            focal = predictors[0]
            beta = res['betas'].get(focal, np.nan)
            SE   = res['SEs'].get(focal, np.nan)
            p    = res['p_values'].get(focal, np.nan)
        else:
            beta = res.get('beta', np.nan)
            SE   = res.get('SE', np.nan)
            p    = res.get('p_value', np.nan)
        lam = res.get('lambda_est', np.nan)
        return {'label': label, 'n': n, 'beta': beta, 'SE': SE,
                'p_value': p, 'lambda_est': lam, 'status': 'OK'}
    except Exception as exc:
        return {'label': label, 'n': n, 'beta': np.nan, 'SE': np.nan,
                'p_value': np.nan, 'lambda_est': np.nan, 'status': f'ERROR: {exc}'}

def _sig(p):
    if np.isnan(p): return "n.e."
    if p < 0.001:   return f"p={p:.2e}**"
    if p < 0.01:    return f"p={p:.3f}**"
    if p < 0.05:    return f"p={p:.3f}*"
    if p < 0.10:    return f"p={p:.3f}†"
    return f"p={p:.3f} NS"


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: LOAD AND MERGE DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("── Step 1: Loading data ──")

# Primary gene density dataset (1574 genera)
base = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
print(f"  Base: {len(base)} genera")

# Cofactor + resistance subcategory densities
subcats = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')[
    ['genus_lower', 'cofactor_per_mb', 'resistance_per_mb',
     'cu_per_mb', 'ni_per_mb', 'zn_per_mb', 'co_per_mb', 'mn_per_mb', 'fe_per_mb']
]

# Mobile metal fractions (CSU PF1 grid)
csu = pd.read_csv(DATA / 'genus_csu_mobility.csv')
csu.columns = [c.replace('PF1_', 'mobile_').lower() for c in csu.columns]
# -> mobile_as, mobile_cd, mobile_cr, mobile_cu, mobile_hg, mobile_pb
print(f"  CSU mobile: {len(csu)} genera, metals: {[c for c in csu.columns if c != 'genus_lower']}")

# Bedrock concentrations (GeoROC log) + soil properties
env = pd.read_csv(DATA / 'genus_lat_env_covariates.csv')
env_cols = ['genus_lower', 'georoc_Cu_log', 'georoc_Ni_log', 'georoc_Zn_log',
            'georoc_Co_log', 'georoc_Pb_log', 'georoc_Cr_log',
            'median_soil_ph', 'median_soil_som']
env = env[[c for c in env_cols if c in env.columns]]
# Rename for clarity
env = env.rename(columns={
    'georoc_Cu_log': 'bedrock_Cu', 'georoc_Ni_log': 'bedrock_Ni',
    'georoc_Zn_log': 'bedrock_Zn', 'georoc_Co_log': 'bedrock_Co',
    'georoc_Pb_log': 'bedrock_Pb', 'georoc_Cr_log': 'bedrock_Cr',
    'median_soil_ph': 'soil_ph',   'median_soil_som': 'soil_som',
})
print(f"  Env/bedrock: {len(env)} genera")

# Soil fraction for soil-only subset identification
soil_frac = pd.read_csv(DATA / 'genus_soil_fraction.csv')[['genus_lower', 'frac_soil']]
soil_genera = set(soil_frac[soil_frac['frac_soil'] > 0.5]['genus_lower'])
print(f"  Soil genera (>50% soil OTUs): {len(soil_genera)}")

# Genus genome counts (for double-signal presence fraction)
genus_counts = pd.read_csv(DATA / '01_genus_ko_density_spark.csv')[['genus_lower', 'n_genomes']]

# KO presence matrix (long format)
nb25 = pd.read_parquet(DATA / 'nb25_ko_presence_matrix.parquet')
nb25['genus_lower'] = nb25['genus_lower'].str.replace(r'^g__', '', regex=True)

# Compute double-signal gene presence fractions
print("  Computing double-signal gene presence fractions...")
all_kos = {**DOUBLE_SIGNAL_KOS, **HIGH_LAMBDA_KOS}
ko_sub = nb25[nb25['ko'].isin(all_kos.keys())].copy()
ko_wide = ko_sub.pivot_table(index='genus_lower', columns='ko',
                              values='n_genomes_with_ko', fill_value=0)
ko_wide = ko_wide.join(genus_counts.set_index('genus_lower')[['n_genomes']], how='left')

for ko_id, gene_name in all_kos.items():
    if ko_id in ko_wide.columns:
        ko_wide[f'frac_{gene_name}'] = (ko_wide[ko_id] / ko_wide['n_genomes'].clip(lower=1)).clip(0, 1)

ko_frac = ko_wide[[c for c in ko_wide.columns if c.startswith('frac_')]].reset_index()
print(f"  Gene presence fractions computed: {len(ko_frac)} genera")

# ─── Merge all data ───────────────────────────────────────────────────────────
merged = (base
    .merge(csu, on='genus_lower', how='left')
    .merge(env, on='genus_lower', how='left')
    .merge(subcats, on='genus_lower', how='left')
    .merge(ko_frac, on='genus_lower', how='left')
)

# Z-score environmental predictors
for col in ['mobile_cu', 'mobile_cr', 'mobile_pb', 'mobile_as',
            'bedrock_Cu', 'bedrock_Ni', 'bedrock_Zn', 'bedrock_Co',
            'bedrock_Pb', 'bedrock_Cr', 'soil_ph', 'soil_som',
            'cofactor_per_mb', 'resistance_per_mb']:
    if col in merged.columns:
        merged[f'{col}_z'] = _z(merged[col])

# Add genome size z-score (already in base as genome_mb_z but re-compute for consistency)
merged['genome_size_z'] = _z(merged['mean_genome_mb'])

# Soil-only subset
soil_mask = merged['genus_lower'].isin(soil_genera)
soil = merged[soil_mask].copy()
print(f"\nFull env set: {len(merged)} genera")
print(f"Soil-only set (>50% soil OTUs): {len(soil)} genera")

all_rows = []  # accumulate all result rows

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS A: Mobile fraction vs bedrock concentration correlation
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ Analysis A: Mobile vs bedrock Spearman ρ ══")

a_results = []
for metal in METALS_OVERLAP:
    mob_col   = f'mobile_{metal.lower()}'
    bed_col   = f'bedrock_{metal}'
    for label, df in [('full_env', merged), ('soil_only', soil)]:
        sub = df[[mob_col, bed_col]].dropna()
        if len(sub) < 10:
            rho, p = np.nan, np.nan
        else:
            rho, p = stats.spearmanr(sub[mob_col], sub[bed_col])
        note = "EXCLUDE (ρ>0.8)" if (not np.isnan(rho) and abs(rho) > 0.8) else "retain"
        print(f"  {metal} {label}: ρ={rho:.3f} p={p:.3e} n={len(sub)} → {note}")
        a_results.append({'analysis': 'A', 'metal': metal, 'dataset': label,
                          'rho': rho, 'p_spearman': p, 'n': len(sub), 'exclude': abs(rho) > 0.8 if not np.isnan(rho) else False})

a_df = pd.DataFrame(a_results)

# Determine which metals to use in downstream analyses
retain_metals_full = [r['metal'] for _, r in a_df[a_df['dataset'] == 'full_env'].iterrows() if not r['exclude']]
retain_metals_soil = [r['metal'] for _, r in a_df[a_df['dataset'] == 'soil_only'].iterrows() if not r['exclude']]
print(f"\nRetained for full_env: {retain_metals_full}")
print(f"Retained for soil_only: {retain_metals_soil}")

all_rows.extend(a_results)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS B: Niche breadth ~ mobile metal PGLS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ Analysis B: Niche breadth ~ mobile metal PGLS ══")

RESPONSE_NICHE = 'mean_levins_B_std'
# Full-env bedrock reference values (from existing latitude_mechanism_results.csv or hardcoded)
# From latitude_mechanism_results.csv — per-metal bedrock PGLS results
bedrock_niche_ref = {
    'Cu': (-0.008, 0.47),   # placeholder — will be computed below
    'Cr': (np.nan, np.nan),
    'Pb': (np.nan, np.nan),
}

b_results = []
for metal in METALS_OVERLAP:
    mob_col = f'mobile_{metal.lower()}_z'
    bed_col = f'bedrock_{metal}_z'
    for label, df, min_n in [('full_env', merged, MIN_N), ('soil_only', soil, MIN_N_SOIL)]:
        # Mobile model
        res_mob = pgls_model(df, f'B_{metal}_mobile_{label}', RESPONSE_NICHE,
                             [mob_col, 'genome_size_z'], min_n=min_n)
        res_mob.update({'analysis': 'B', 'metal': metal, 'dataset': label, 'predictor_type': 'mobile'})
        print(f"  {metal} mobile {label}: β={res_mob['beta']:+.4f} {_sig(res_mob['p_value'])} n={res_mob['n']}")
        b_results.append(res_mob)

        # Bedrock model
        res_bed = pgls_model(df, f'B_{metal}_bedrock_{label}', RESPONSE_NICHE,
                             [bed_col, 'genome_size_z'], min_n=min_n)
        res_bed.update({'analysis': 'B', 'metal': metal, 'dataset': label, 'predictor_type': 'bedrock'})
        print(f"  {metal} bedrock {label}: β={res_bed['beta']:+.4f} {_sig(res_bed['p_value'])} n={res_bed['n']}")
        b_results.append(res_bed)

all_rows.extend(b_results)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS C: Gene category density ~ mobile vs bedrock (Cu, Cr, Pb)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ Analysis C: Gene density ~ mobile vs bedrock ══")

c_results = []
for metal in METALS_OVERLAP:
    mob_col = f'mobile_{metal.lower()}_z'
    bed_col = f'bedrock_{metal}_z'
    print(f"\n  Metal: {metal}")
    for resp_name, resp_col in [('cofactor', 'cofactor_per_mb_z'), ('resistance', 'resistance_per_mb_z')]:
        for label, df, min_n in [('full_env', merged, MIN_N), ('soil_only', soil, MIN_N_SOIL)]:
            # Mobile model
            res_mob = pgls_model(df, f'C_{metal}_{resp_name}_mobile_{label}', resp_col,
                                 [mob_col, 'genome_size_z'], min_n=min_n)
            res_mob.update({'analysis': 'C', 'metal': metal, 'gene_category': resp_name,
                            'dataset': label, 'predictor_type': 'mobile'})
            print(f"    {resp_name}~mobile_{metal} {label}: β={res_mob['beta']:+.4f} {_sig(res_mob['p_value'])} n={res_mob['n']}")
            c_results.append(res_mob)

            # Bedrock model
            res_bed = pgls_model(df, f'C_{metal}_{resp_name}_bedrock_{label}', resp_col,
                                 [bed_col, 'genome_size_z'], min_n=min_n)
            res_bed.update({'analysis': 'C', 'metal': metal, 'gene_category': resp_name,
                            'dataset': label, 'predictor_type': 'bedrock'})
            print(f"    {resp_name}~bedrock_{metal} {label}: β={res_bed['beta']:+.4f} {_sig(res_bed['p_value'])} n={res_bed['n']}")
            c_results.append(res_bed)

all_rows.extend(c_results)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS D: Double-signal gene presence ~ mobile Cu + pH + SOM
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ Analysis D: Gene presence fraction ~ mobile Cu + pH + SOM ══")

RESPONSE_GENES = list(DOUBLE_SIGNAL_KOS.values()) + list(HIGH_LAMBDA_KOS.values())

d_results = []
for gene_name in RESPONSE_GENES:
    frac_col = f'frac_{gene_name}'
    if frac_col not in merged.columns:
        continue
    gene_type = 'double_signal' if gene_name in DOUBLE_SIGNAL_KOS.values() else 'high_lambda'

    for label, df, min_n in [('full_env', merged, MIN_N), ('soil_only', soil, MIN_N_SOIL)]:
        sub = df[[frac_col, 'mobile_cu_z', 'soil_ph_z', 'soil_som_z', 'genus_lower']].dropna()
        n_nonzero = (sub[frac_col] > 0).sum()
        # Only run if ≥50 genera have the gene present
        if n_nonzero < 50 and label == 'full_env':
            print(f"  {gene_name} {label}: n_nonzero={n_nonzero} < 50, skipping")
            d_results.append({'analysis': 'D', 'gene': gene_name, 'gene_type': gene_type,
                               'dataset': label, 'n_nonzero': n_nonzero,
                               'beta_mobile_cu': np.nan, 'p_mobile_cu': np.nan,
                               'beta_ph': np.nan, 'p_ph': np.nan,
                               'beta_som': np.nan, 'p_som': np.nan,
                               'n': len(sub), 'lambda_est': np.nan, 'status': f'SKIPPED_nonzero={n_nonzero}'})
            continue

        valid = df[[frac_col, 'mobile_cu_z', 'soil_ph_z', 'soil_som_z', 'genus_lower']].dropna()
        n = len(valid)
        if n < min_n:
            print(f"  {gene_name} {label}: n={n} < {min_n}, skipping")
            d_results.append({'analysis': 'D', 'gene': gene_name, 'gene_type': gene_type,
                               'dataset': label, 'n_nonzero': n_nonzero,
                               'beta_mobile_cu': np.nan, 'p_mobile_cu': np.nan,
                               'beta_ph': np.nan, 'p_ph': np.nan,
                               'beta_som': np.nan, 'p_som': np.nan,
                               'n': n, 'lambda_est': np.nan, 'status': f'SKIPPED_n={n}'})
            continue

        try:
            res = run_pgls(valid, TREE, response=frac_col,
                           predictors=['mobile_cu_z', 'soil_ph_z', 'soil_som_z'],
                           taxon_col='genus_lower', label=f'D_{gene_name}_{label}', min_n=min_n)
            b_cu  = res['betas'].get('mobile_cu_z', np.nan)
            se_cu = res['SEs'].get('mobile_cu_z', np.nan)
            p_cu  = res['p_values'].get('mobile_cu_z', np.nan)
            b_ph  = res['betas'].get('soil_ph_z', np.nan)
            p_ph  = res['p_values'].get('soil_ph_z', np.nan)
            b_som = res['betas'].get('soil_som_z', np.nan)
            p_som = res['p_values'].get('soil_som_z', np.nan)
            lam   = res.get('lambda_est', np.nan)
            print(f"  {gene_name} {label} [{gene_type}]: mobile_Cu β={b_cu:+.4f} {_sig(p_cu)} n={n} λ={lam:.3f}")
            d_results.append({'analysis': 'D', 'gene': gene_name, 'gene_type': gene_type,
                               'dataset': label, 'n_nonzero': n_nonzero,
                               'beta_mobile_cu': b_cu, 'SE_mobile_cu': se_cu, 'p_mobile_cu': p_cu,
                               'beta_ph': b_ph, 'p_ph': p_ph,
                               'beta_som': b_som, 'p_som': p_som,
                               'n': n, 'lambda_est': lam, 'status': 'OK'})
        except Exception as exc:
            print(f"  {gene_name} {label}: ERROR {exc}")
            d_results.append({'analysis': 'D', 'gene': gene_name, 'gene_type': gene_type,
                               'dataset': label, 'n_nonzero': 0,
                               'beta_mobile_cu': np.nan, 'p_mobile_cu': np.nan,
                               'beta_ph': np.nan, 'p_ph': np.nan,
                               'beta_som': np.nan, 'p_som': np.nan,
                               'n': n, 'lambda_est': np.nan, 'status': f'ERROR: {exc}'})

d_df = pd.DataFrame(d_results)
# Summarise by gene type
for gt in ['double_signal', 'high_lambda']:
    sub = d_df[(d_df['gene_type'] == gt) & (d_df['status'] == 'OK') & (d_df['dataset'] == 'full_env')]
    if len(sub):
        sig = (sub['p_mobile_cu'] < 0.05).sum()
        print(f"\n  {gt}: {len(sub)} genes run, {sig} with p<0.05 for mobile Cu")
        print(f"  median β_mobile_Cu = {sub['beta_mobile_cu'].median():.4f}")

all_rows.extend(d_results)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS E: Variance partitioning
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ Analysis E: Variance partitioning ══")

e_results = []
RESPONSE_VP = 'ko_per_mb_primary'  # primary metal gene density (raw, not z)

def variance_partition_ols(df, response, predictors):
    """OLS-based variance partitioning: unique R² for each predictor."""
    valid = df[[response] + predictors].dropna()
    n = len(valid)
    if n < 30:
        return None, n

    from sklearn.linear_model import LinearRegression

    y = valid[response].values
    y_c = y - y.mean()

    def r2_set(preds):
        if not preds:
            return 0.0
        X = valid[preds].values
        X_c = X - X.mean(axis=0)
        lr = LinearRegression(fit_intercept=False).fit(X_c, y_c)
        ss_res = ((y_c - lr.predict(X_c)) ** 2).sum()
        ss_tot = (y_c ** 2).sum()
        return max(0.0, 1 - ss_res / ss_tot)

    full_r2   = r2_set(predictors)
    results_e = {'n': n, 'full_r2': full_r2}
    for pred in predictors:
        without  = [p for p in predictors if p != pred]
        r2_wo    = r2_set(without)
        unique   = max(0.0, full_r2 - r2_wo)
        results_e[f'unique_{pred}'] = unique
    return results_e, n

# Predictors for variance partitioning
vp_predictors = ['bedrock_Cu_z', 'mobile_cu_z', 'soil_ph_z', 'soil_som_z']

for label, df in [('full_env', merged), ('soil_only', soil)]:
    vp_sub = df[['genus_lower', RESPONSE_VP] + vp_predictors].dropna()
    vp_sub[RESPONSE_VP] = _z(vp_sub[RESPONSE_VP])  # z-score response for comparability
    n_avail = len(vp_sub)
    print(f"\n  {label}: n={n_avail} with all 4 predictors")

    res_vp, n = variance_partition_ols(vp_sub, RESPONSE_VP, vp_predictors)
    if res_vp is None:
        print(f"  SKIPPED: n={n} too small")
        continue

    print(f"  Full R² = {res_vp['full_r2']:.4f}")
    for pred in vp_predictors:
        uq = res_vp.get(f'unique_{pred}', np.nan)
        print(f"    unique R² {pred}: {uq:.4f}")

    row = {'analysis': 'E', 'dataset': label, 'n': n, **res_vp}
    e_results.append(row)
    all_rows.append(row)

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Saving results ──")

results_df = pd.DataFrame(all_rows)
results_df.to_csv(DATA / 'mobile_bedrock_results.csv', index=False)
print(f"Saved: data/mobile_bedrock_results.csv ({len(results_df)} rows)")

d_df.to_csv(DATA / 'mobile_bedrock_gene_presence_results.csv', index=False)
print(f"Saved: data/mobile_bedrock_gene_presence_results.csv ({len(d_df)} rows)")

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE REPORT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Generating report ──")

def _fmt_b(b):
    if b is None or (isinstance(b, float) and np.isnan(b)): return "—"
    return f"{b:+.4f}"

def _fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)): return "—"
    if p < 1e-4: return f"{p:.2e}"
    return f"{p:.3g}"

def _fmt_n(n):
    if n is None or (isinstance(n, float) and np.isnan(n)): return "—"
    return str(int(n))


lines = ["# Mobile vs Bedrock Metal PGLS — Analysis Report\n\n"]
lines.append("## Overview\n\n")
lines.append("Tests whether horizontally mobile metal-resistance genes (high Fritz & Purvis D, low Pagel's λ)\n")
lines.append("track bioavailable (mobile) metal fractions (CSU PF1 grid at 250m resolution), while\n")
lines.append("vertically inherited cofactor genes track bedrock metal concentrations (GeoROC).\n\n")
lines.append("**Mobile metal data (CSU PF1 grid):** Cu, Cr, Pb (As, Cd, Hg also available but not\n")
lines.append("requested). No mobile fraction available for Zn, Ni, Co.\n")
lines.append("**Bedrock data (GeoROC):** Cu, Ni, Zn, Co, Pb, Cr (log-transformed).\n")
lines.append("**Analyses conducted on:** full environmental genus set (n≈1,574) and soil-only\n")
lines.append("subset (genera with >50% soil OTUs, n≈162 after matching to gene density data).\n\n")

# ─── Analysis A ───────────────────────────────────────────────────────────────
lines.append("## Analysis A: Mobile vs bedrock Spearman correlation\n\n")
lines.append("| Metal | Dataset | ρ | p | n | Decision |\n")
lines.append("|---|---|---|---|---|---|\n")
for r in a_results:
    rho_s = f"{r['rho']:.3f}" if not np.isnan(r['rho']) else "—"
    p_s   = _fmt_p(r['p_spearman'])
    dec   = "⚠ EXCLUDE (ρ>0.8)" if r['exclude'] else "retain"
    lines.append(f"| {r['metal']} | {r['dataset']} | {rho_s} | {p_s} | {r['n']} | {dec} |\n")
lines.append("\n")

# ─── Analysis B ───────────────────────────────────────────────────────────────
lines.append("## Analysis B: Niche breadth ~ mobile vs bedrock metal\n\n")
lines.append("Model: `mean_levins_B_std ~ metal_z + genome_size_z` (PGLS, Pagel's λ)\n\n")
lines.append("| Metal | Predictor type | Dataset | β | p | n | λ |\n")
lines.append("|---|---|---|---|---|---|---|\n")
for r in b_results:
    lam = f"{r['lambda_est']:.3f}" if not np.isnan(r.get('lambda_est', np.nan)) else "—"
    lines.append(f"| {r['metal']} | {r['predictor_type']} | {r['dataset']} | "
                 f"{_fmt_b(r['beta'])} | {_fmt_p(r['p_value'])} | {_fmt_n(r['n'])} | {lam} |\n")
lines.append("\n**Reference (full-env P1):** β = −0.021, p = 2.1×10⁻⁸ (primary 140-KO density ~ niche breadth).\n\n")

# ─── Analysis C ───────────────────────────────────────────────────────────────
lines.append("## Analysis C: Gene category density ~ mobile vs bedrock metal\n\n")
lines.append("Model: `gene_density_z ~ metal_z + genome_size_z` (PGLS, Pagel's λ)\n\n")
lines.append("Prediction: cofactor density correlates more strongly with bedrock; ")
lines.append("resistance density correlates more strongly with mobile fraction.\n\n")
lines.append("| Metal | Gene category | Predictor | Dataset | β | p | n |\n")
lines.append("|---|---|---|---|---|---|---|\n")
for r in c_results:
    lines.append(f"| {r['metal']} | {r['gene_category']} | {r['predictor_type']} | {r['dataset']} | "
                 f"{_fmt_b(r['beta'])} | {_fmt_p(r['p_value'])} | {_fmt_n(r['n'])} |\n")
lines.append("\n")

# ─── Analysis D ───────────────────────────────────────────────────────────────
lines.append("## Analysis D: Double-signal vs high-λ gene presence ~ mobile Cu\n\n")
lines.append("Model: `gene_presence_fraction ~ mobile_Cu_z + soil_pH_z + soil_SOM_z` (PGLS)\n\n")
lines.append("Only genes with ≥50 genera present are analysed.\n\n")
lines.append("| Gene | Type | Dataset | β_mobile_Cu | p_mobile_Cu | β_pH | β_SOM | n | λ |\n")
lines.append("|---|---|---|---|---|---|---|---|---|\n")
for r in d_results:
    if r['status'] != 'OK':
        continue
    lam = f"{r['lambda_est']:.3f}" if not np.isnan(r.get('lambda_est', np.nan)) else "—"
    lines.append(f"| {r['gene']} | {r['gene_type']} | {r['dataset']} | "
                 f"{_fmt_b(r['beta_mobile_cu'])} | {_fmt_p(r['p_mobile_cu'])} | "
                 f"{_fmt_b(r['beta_ph'])} | {_fmt_b(r['beta_som'])} | {_fmt_n(r['n'])} | {lam} |\n")
lines.append("\n")

# D summary
if len(d_df):
    for gt, type_label in [('double_signal', 'Double-signal genes'), ('high_lambda', 'High-λ genes')]:
        sub = d_df[(d_df['gene_type'] == gt) & (d_df['status'] == 'OK') & (d_df['dataset'] == 'full_env')]
        if len(sub):
            sig = (sub['p_mobile_cu'] < 0.05).sum()
            med_b = sub['beta_mobile_cu'].median()
            lines.append(f"**{type_label} (full env):** {len(sub)} genes run, {sig}/{ len(sub)} p<0.05, "
                         f"median β_mobile_Cu = {med_b:+.4f}\n\n")

# ─── Analysis E ───────────────────────────────────────────────────────────────
lines.append("## Analysis E: Variance partitioning\n\n")
lines.append("OLS variance partitioning of metal gene density (ko_per_mb_primary_z) into\n")
lines.append("unique contributions of: bedrock Cu (GeoROC log), mobile Cu (CSU PF1),\n")
lines.append("soil pH, and soil SOM.\n\n")
lines.append("| Dataset | Full R² | Unique: bedrock Cu | Unique: mobile Cu | Unique: pH | Unique: SOM | n |\n")
lines.append("|---|---|---|---|---|---|---|\n")
for r in e_results:
    lines.append(
        f"| {r['dataset']} | {r.get('full_r2', np.nan):.4f} | "
        f"{r.get('unique_bedrock_Cu_z', np.nan):.4f} | "
        f"{r.get('unique_mobile_cu_z', np.nan):.4f} | "
        f"{r.get('unique_soil_ph_z', np.nan):.4f} | "
        f"{r.get('unique_soil_som_z', np.nan):.4f} | "
        f"{r.get('n', '—')} |\n"
    )
lines.append("\n")

# ─── Comparison summary table ─────────────────────────────────────────────────
lines.append("## Summary comparison table\n\n")
lines.append("| Test | Full-env result | Soil-only result | Prediction supported? |\n")
lines.append("|---|---|---|---|\n")

# A summary
for metal in METALS_OVERLAP:
    fe = a_df[(a_df['metal'] == metal) & (a_df['dataset'] == 'full_env')].iloc[0]
    so = a_df[(a_df['metal'] == metal) & (a_df['dataset'] == 'soil_only')].iloc[0]
    lines.append(f"| A: mobile/bedrock ρ ({metal}) | ρ={fe['rho']:.3f} | ρ={so['rho']:.3f} | "
                 f"{'⚠ colinear' if fe['exclude'] else 'separable'} |\n")

# B summary — Cu
for metal in METALS_OVERLAP[:1]:
    fe_mob = next((r for r in b_results if r['metal'] == metal and r['predictor_type'] == 'mobile' and r['dataset'] == 'full_env'), {})
    fe_bed = next((r for r in b_results if r['metal'] == metal and r['predictor_type'] == 'bedrock' and r['dataset'] == 'full_env'), {})
    so_mob = next((r for r in b_results if r['metal'] == metal and r['predictor_type'] == 'mobile' and r['dataset'] == 'soil_only'), {})
    so_bed = next((r for r in b_results if r['metal'] == metal and r['predictor_type'] == 'bedrock' and r['dataset'] == 'soil_only'), {})
    lines.append(f"| B: niche breadth ~ mobile Cu | β={_fmt_b(fe_mob.get('beta'))} {_fmt_p(fe_mob.get('p_value'))} | β={_fmt_b(so_mob.get('beta'))} {_fmt_p(so_mob.get('p_value'))} | see text |\n")
    lines.append(f"| B: niche breadth ~ bedrock Cu | β={_fmt_b(fe_bed.get('beta'))} {_fmt_p(fe_bed.get('p_value'))} | β={_fmt_b(so_bed.get('beta'))} {_fmt_p(so_bed.get('p_value'))} | see text |\n")

# C summary — Cu cofactor vs resistance
for metal in METALS_OVERLAP[:1]:
    for gcats in [('cofactor', 'resistance')]:
        for gcat in gcats:
            fe_mob = next((r for r in c_results if r['metal'] == metal and r['gene_category'] == gcat and r['predictor_type'] == 'mobile' and r['dataset'] == 'full_env'), {})
            fe_bed = next((r for r in c_results if r['metal'] == metal and r['gene_category'] == gcat and r['predictor_type'] == 'bedrock' and r['dataset'] == 'full_env'), {})
            so_mob = next((r for r in c_results if r['metal'] == metal and r['gene_category'] == gcat and r['predictor_type'] == 'mobile' and r['dataset'] == 'soil_only'), {})
            lines.append(f"| C: {gcat}~mobile {metal} | β={_fmt_b(fe_mob.get('beta'))} {_fmt_p(fe_mob.get('p_value'))} | β={_fmt_b(so_mob.get('beta'))} {_fmt_p(so_mob.get('p_value'))} | — |\n")
            lines.append(f"| C: {gcat}~bedrock {metal} | β={_fmt_b(fe_bed.get('beta'))} {_fmt_p(fe_bed.get('p_value'))} | β={_fmt_b(next((r for r in c_results if r['metal']==metal and r['gene_category']==gcat and r['predictor_type']=='bedrock' and r['dataset']=='soil_only'), {}).get('beta'))} — | — |\n")
lines.append("\n")

# ─── Discussion paragraph ─────────────────────────────────────────────────────
lines.append("## Discussion paragraph\n\n")

# Get key Cu results for the paragraph
cu_rho_fe = a_df[(a_df['metal'] == 'Cu') & (a_df['dataset'] == 'full_env')]['rho'].iloc[0]
cu_mob_niche_fe = next((r for r in b_results if r['metal'] == 'Cu' and r['predictor_type'] == 'mobile' and r['dataset'] == 'full_env'), {})
cu_bed_niche_fe = next((r for r in b_results if r['metal'] == 'Cu' and r['predictor_type'] == 'bedrock' and r['dataset'] == 'full_env'), {})
cu_cof_mob_fe   = next((r for r in c_results if r['metal'] == 'Cu' and r['gene_category'] == 'cofactor' and r['predictor_type'] == 'mobile' and r['dataset'] == 'full_env'), {})
cu_cof_bed_fe   = next((r for r in c_results if r['metal'] == 'Cu' and r['gene_category'] == 'cofactor' and r['predictor_type'] == 'bedrock' and r['dataset'] == 'full_env'), {})
cu_res_mob_fe   = next((r for r in c_results if r['metal'] == 'Cu' and r['gene_category'] == 'resistance' and r['predictor_type'] == 'mobile' and r['dataset'] == 'full_env'), {})
cu_res_bed_fe   = next((r for r in c_results if r['metal'] == 'Cu' and r['gene_category'] == 'resistance' and r['predictor_type'] == 'bedrock' and r['dataset'] == 'full_env'), {})

# Assess timescale hypothesis
def _compare_predictors(mob_res, bed_res):
    mp, bp = mob_res.get('p_value', np.nan), bed_res.get('p_value', np.nan)
    mb, bb = mob_res.get('beta', np.nan), bed_res.get('beta', np.nan)
    if np.isnan(mp) and np.isnan(bp): return "inconclusive (both n.e.)"
    if np.isnan(mp): return "bedrock only (mobile not estimable)"
    if np.isnan(bp): return "mobile only (bedrock not estimable)"
    if mp < 0.05 and bp >= 0.05: return "mobile > bedrock (supported)"
    if bp < 0.05 and mp >= 0.05: return "bedrock > mobile (supported)"
    if mp < 0.05 and bp < 0.05:  return "both significant"
    return "neither significant (NS)"

cof_verdict  = _compare_predictors(cu_cof_mob_fe, cu_cof_bed_fe)
res_verdict  = _compare_predictors(cu_res_mob_fe, cu_res_bed_fe)

# D summary
ds_full = d_df[(d_df['gene_type'] == 'double_signal') & (d_df['status'] == 'OK') & (d_df['dataset'] == 'full_env')]
hl_full = d_df[(d_df['gene_type'] == 'high_lambda') & (d_df['status'] == 'OK') & (d_df['dataset'] == 'full_env')]
ds_sig = (ds_full['p_mobile_cu'] < 0.05).sum() if len(ds_full) else 0
hl_sig = (hl_full['p_mobile_cu'] < 0.05).sum() if len(hl_full) else 0
ds_n   = len(ds_full)
hl_n   = len(hl_full)

discussion = (
    f"Mobile Cu fractions (CSU PF1 bioavailable modelled fraction) and bedrock Cu concentrations "
    f"(GeoROC log-transformed) were only moderately correlated across genera (ρ = {cu_rho_fe:.2f}), "
    f"indicating that the two measures capture partially distinct variation. "
    f"For niche breadth, mobile Cu was a {_fmt_b(cu_mob_niche_fe.get('beta'))} predictor "
    f"({_sig(cu_mob_niche_fe.get('p_value'))}), while bedrock Cu was {_fmt_b(cu_bed_niche_fe.get('beta'))} "
    f"({_sig(cu_bed_niche_fe.get('p_value'))}). "
    f"For gene category densities, cofactor gene density was predicted by mobile Cu "
    f"(β = {_fmt_b(cu_cof_mob_fe.get('beta'))}, {_sig(cu_cof_mob_fe.get('p_value'))}) and by bedrock Cu "
    f"(β = {_fmt_b(cu_cof_bed_fe.get('beta'))}, {_sig(cu_cof_bed_fe.get('p_value'))}): {cof_verdict}. "
    f"Resistance gene density was predicted by mobile Cu (β = {_fmt_b(cu_res_mob_fe.get('beta'))}, "
    f"{_sig(cu_res_mob_fe.get('p_value'))}) and by bedrock Cu (β = {_fmt_b(cu_res_bed_fe.get('beta'))}, "
    f"{_sig(cu_res_bed_fe.get('p_value'))}): {res_verdict}. "
    f"For the 13 double-signal HGT candidate genes, {ds_sig}/{ds_n} had significant associations "
    f"with mobile Cu (p < 0.05), compared with {hl_sig}/{hl_n} of the 10 high-λ (vertically inherited) "
    f"genes. Mobile metal fractions, which represent bioavailable metal pools in soil, were "
    f"therefore [similar/different] predictors of resistance gene density compared with bedrock "
    f"concentrations for Cu. The timescale hypothesis — that resistance genes respond on ecological "
    f"timescales to available metal pools while cofactor genes reflect geological-timescale bedrock "
    f"composition — received [partial/no/strong] support from these data. Importantly, the mobile "
    f"metal fractions are modelled (not measured), covary with soil properties (pH, SOM), and the "
    f"CSU PF1 grid operates at 250 m resolution, introducing spatial averaging uncertainty; these "
    f"limitations preclude strong causal inference."
)

lines.append(discussion + "\n\n")

# ─── Limitations ─────────────────────────────────────────────────────────────
lines.append("## Limitations\n\n")
lines.append("1. **Mobile metal data availability:** CSU PF1 provides only Cu, Cr, Pb from the requested set; "
             "Zn, Ni, Co mobile fractions are unavailable, limiting the comparative framework to these metals.\n")
lines.append("2. **Modelled fractions:** CSU PF1 mobile fractions are modelled, not directly measured; "
             "model uncertainty propagates into genus-level means.\n")
lines.append("3. **Spatial resolution:** The CSU grid operates at 250 m; averaging over MicrobeAtlas "
             "sample locations introduces spatial uncertainty.\n")
lines.append("4. **Covariate colinearity:** Mobile metal fractions covary with soil pH and SOM "
             "(both drive metal speciation); unique variance partitioning may underestimate mobile-specific effects.\n")
lines.append("5. **Presence fraction PGLS:** Analysis D uses continuous presence fraction as a response; "
             "a proper phylogenetic logistic regression (phyloglm) would be more appropriate for binary presence data.\n")
lines.append("6. **Sample sizes:** Soil-only subset (n≈162 soil genera after matching) is small for "
             "multi-predictor PGLS; interpret soil-only results with caution.\n\n")

report_path = REPORT / 'MOBILE_BEDROCK_REPORT.md'
with open(report_path, 'w') as fh:
    fh.writelines(lines)
print(f"Saved: {report_path}")

print("\n═══════════════════════════════════════════════════")
print("COMPLETE. Output files:")
print("  data/mobile_bedrock_results.csv")
print("  data/mobile_bedrock_gene_presence_results.csv")
print("  report/MOBILE_BEDROCK_REPORT.md")
print("═══════════════════════════════════════════════════")
