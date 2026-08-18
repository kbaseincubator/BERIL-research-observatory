"""
Community-level CWM validation with CSU PF1 mobile metals and NGSA total soil metals.
Companion to analysis_robustness_species_community.py (Analysis 2, which used GEOROC bedrock).

Outputs:
  data/cwm_community_validation_results.csv  — updated with CSU and NGSA rows
  cwm_mobile_metals_validation.md            — comparison tables and SI interpretation
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
import statsmodels.regression.linear_model as _sm_lm
import statsmodels.tools.tools as _sm_tools
from statsmodels.stats.multitest import multipletests

# ── statsmodels shim (avoids broken statsmodels.api on this install) ──────────
class _SM:
    @staticmethod
    def OLS(endog, exog):
        return _sm_lm.OLS(endog, exog)
    @staticmethod
    def add_constant(x):
        return _sm_tools.add_constant(x)

sm = _SM()

PROJECT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
DATA = PROJECT / 'data'


# ── Load and deduplicate CWM sample data ──────────────────────────────────────
cwm_df = pd.read_csv(DATA / 'h3a_cwm_sample_data.csv').drop_duplicates(subset='sample_id')
print(f'CWM samples (deduplicated): {len(cwm_df):,}')

# ── Load prior GEOROC results for comparison table ────────────────────────────
georoc_df = pd.read_csv(DATA / 'cwm_community_validation_results.csv')
# Keep only GEOROC rows (in case the file already has CSU/NGSA rows from a prior run)
if 'source' in georoc_df.columns:
    georoc_df = georoc_df[georoc_df['source'] == 'GEOROC_bedrock'].copy()
else:
    georoc_df['source'] = 'GEOROC_bedrock'
print(f'GEOROC baseline results: {len(georoc_df)} metals')


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: run Models A and B for a given metal column
# ═══════════════════════════════════════════════════════════════════════════════
def run_cwm_models(df, metal_col, source_label, metal_name, min_samples=30):
    """OLS Models A (aggregate ko) and B (resistance+cofactor split).

    Returns dict of results or None if too few samples.
    """
    needed = ['cwm_ko', 'cwm_cofactor', 'cwm_resistance', 'soil_pH', metal_col]
    sub = df[[c for c in needed if c in df.columns]].copy()
    sub = sub.rename(columns={metal_col: 'metal_val'})
    sub = sub.dropna(subset=['cwm_ko', 'cwm_cofactor', 'cwm_resistance', 'metal_val'])
    sub = sub[sub['metal_val'] >= 0]   # remove impossible negatives
    n = len(sub)
    if n < min_samples:
        return None

    sub['log_metal']         = np.log10(sub['metal_val'] + 1)
    sub['cwm_ko_z']          = stats.zscore(sub['cwm_ko'])
    sub['cwm_cofactor_z']    = stats.zscore(sub['cwm_cofactor'])
    sub['cwm_resistance_z']  = stats.zscore(sub['cwm_resistance'])

    has_ph = ('soil_pH' in sub.columns) and (sub['soil_pH'].notna().sum() >= 0.3 * n)

    # Model A — aggregate primary KO density
    try:
        X_a = sm.add_constant(sub['cwm_ko_z'])
        m_a = sm.OLS(sub['log_metal'], X_a).fit()
        beta_ko = float(m_a.params['cwm_ko_z'])
        p_ko    = float(m_a.pvalues['cwm_ko_z'])
        r2_a    = float(m_a.rsquared)
    except Exception:
        beta_ko = p_ko = r2_a = np.nan

    # Model B — resistance/cofactor split (+pH where available)
    try:
        if has_ph:
            sub_b = sub.dropna(subset=['soil_pH']).copy()
            sub_b['soil_pH_z'] = stats.zscore(sub_b['soil_pH'])
            X_b = sm.add_constant(sub_b[['cwm_resistance_z', 'cwm_cofactor_z', 'soil_pH_z']])
            m_b = sm.OLS(sub_b['log_metal'], X_b).fit()
            n_b = len(sub_b)
        else:
            X_b = sm.add_constant(sub[['cwm_resistance_z', 'cwm_cofactor_z']])
            m_b = sm.OLS(sub['log_metal'], X_b).fit()
            n_b = n
        beta_res = float(m_b.params.get('cwm_resistance_z', np.nan))
        p_res    = float(m_b.pvalues.get('cwm_resistance_z', np.nan))
        beta_cof = float(m_b.params.get('cwm_cofactor_z', np.nan))
        p_cof    = float(m_b.pvalues.get('cwm_cofactor_z', np.nan))
        r2_b     = float(m_b.rsquared)
    except Exception:
        beta_res = p_res = beta_cof = p_cof = r2_b = np.nan
        n_b = n

    return {
        'source':               source_label,
        'metal':                metal_name,
        'n_samples_modelA':     n,
        'n_samples_modelB':     n_b,
        'beta_cwm_ko':          round(beta_ko, 6),
        'p_cwm_ko':             p_ko,
        'r2_modelA':            round(r2_a, 6),
        'beta_cwm_resistance':  round(beta_res, 6),
        'p_cwm_resistance':     p_res,
        'beta_cwm_cofactor':    round(beta_cof, 6),
        'p_cwm_cofactor':       p_cof,
        'r2_modelB':            round(r2_b, 6),
        'soil_pH_included':     has_ph,
    }


def apply_fdr(df):
    """Apply BH-FDR across metals in-place."""
    for col_p, col_q in [('p_cwm_ko',          'q_cwm_ko'),
                          ('p_cwm_resistance',   'q_cwm_resistance'),
                          ('p_cwm_cofactor',     'q_cwm_cofactor')]:
        if col_p not in df.columns:
            continue
        mask = df[col_p].notna()
        if mask.sum() > 1:
            _, q, _, _ = multipletests(df.loc[mask, col_p], method='fdr_bh')
            df.loc[mask, col_q] = q
        elif mask.sum() == 1:
            df.loc[mask, col_q] = df.loc[mask, col_p]
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS A — CSU PF1 mobile (bioavailable) metal fractions
# ═══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('A. CSU PF1 Mobile Metals')
print('='*60)

csu_raw = pd.read_parquet(DATA / 'csu_sample_lookup.parquet')
cwm_csu = cwm_df.merge(csu_raw, left_on='sample_id', right_on='accession_id', how='inner')
print(f'CWM × CSU matched: {len(cwm_csu):,} samples')

CSU_METALS = {
    'As': 'PF1_As',
    'Cd': 'PF1_Cd',
    'Cr': 'PF1_Cr',
    'Cu': 'PF1_Cu',
    'Hg': 'PF1_Hg',
    'Pb': 'PF1_Pb',
}

csu_results = []
for metal_name, col in CSU_METALS.items():
    r = run_cwm_models(cwm_csu, col, 'CSU_PF1_mobile', metal_name)
    if r is None:
        print(f'  {metal_name}: <30 samples — skip')
        continue
    csu_results.append(r)
    print(f'  {metal_name}: n={r["n_samples_modelA"]:,}  β(ko)={r["beta_cwm_ko"]:+.4f} p={r["p_cwm_ko"]:.3e}  '
          f'β(res)={r["beta_cwm_resistance"]:+.4f} p={r["p_cwm_resistance"]:.3e}  '
          f'β(cof)={r["beta_cwm_cofactor"]:+.4f} p={r["p_cwm_cofactor"]:.3e}')

csu_df_res = pd.DataFrame(csu_results)
if len(csu_df_res) > 0:
    csu_df_res = apply_fdr(csu_df_res)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS B — NGSA total soil metals (Australia, spatial join ≤50 km)
# ═══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('B. NGSA Total Soil Metals (Australia spatial join ≤50 km)')
print('='*60)

NGSA_MAX_KM = 50.0
NGSA_METALS = {
    'Cu': 'Cu_ppm', 'Zn': 'Zn_ppm', 'Pb': 'Pb_ppm',
    'Cd': 'Cd_ppm', 'Ni': 'Ni_ppm', 'Co': 'Co_ppm',
    'As': 'As_ppm', 'Cr': 'Cr_ppm', 'Hg': 'Hg_ppm',
}

ngsa_raw = pd.read_csv(DATA / 'ngsa_geochemistry.csv').dropna(subset=['lat', 'lon'])
print(f'NGSA sites: {len(ngsa_raw)}')

# Restrict CWM to Australia bounding box
cwm_au = cwm_df[
    cwm_df['lat'].notna() & cwm_df['lon'].notna() &
    cwm_df['lat'].between(-44.0, -10.0) &
    cwm_df['lon'].between(113.0, 154.0)
].copy()
print(f'CWM samples in Australian bounding box: {len(cwm_au):,}')

ngsa_df_res = pd.DataFrame()

if len(cwm_au) >= 30:
    # Convert to 3D unit-sphere for KD-tree (exact for haversine nearest-neighbour)
    def to_xyz(lat_deg, lon_deg):
        lat = np.radians(np.asarray(lat_deg, dtype=float))
        lon = np.radians(np.asarray(lon_deg, dtype=float))
        return np.stack([np.cos(lat)*np.cos(lon),
                         np.cos(lat)*np.sin(lon),
                         np.sin(lat)], axis=-1)

    ngsa_xyz = to_xyz(ngsa_raw['lat'].values, ngsa_raw['lon'].values)
    cwm_xyz  = to_xyz(cwm_au['lat'].values,   cwm_au['lon'].values)

    tree = cKDTree(ngsa_xyz)
    chord_dist, idxs = tree.query(cwm_xyz, k=1)

    # chord_dist to km: chord = 2*R*sin(theta/2), so theta = 2*arcsin(chord/2/R)
    R_km = 6371.0
    gc_km = 2 * R_km * np.arcsin(np.clip(chord_dist / 2, 0, 1))

    cwm_au = cwm_au.copy()
    cwm_au['_ngsa_dist_km'] = gc_km
    cwm_au['_ngsa_idx']     = idxs

    within_au = cwm_au[cwm_au['_ngsa_dist_km'] <= NGSA_MAX_KM].copy()
    print(f'CWM samples within {NGSA_MAX_KM} km of NGSA site: {len(within_au):,}')

    if len(within_au) >= 30:
        ngsa_reset = ngsa_raw.reset_index(drop=True)
        for col in NGSA_METALS.values():
            if col in ngsa_reset.columns:
                within_au[f'ngsa_{col}'] = ngsa_reset.loc[within_au['_ngsa_idx'].values, col].values

        ngsa_results = []
        for metal_name, col in NGSA_METALS.items():
            ngsa_col = f'ngsa_{col}'
            if ngsa_col not in within_au.columns:
                continue
            r = run_cwm_models(within_au, ngsa_col, 'NGSA_total_soil', metal_name)
            if r is None:
                print(f'  {metal_name}: <30 samples — skip')
                continue
            ngsa_results.append(r)
            print(f'  {metal_name}: n={r["n_samples_modelA"]:,}  β(ko)={r["beta_cwm_ko"]:+.4f} p={r["p_cwm_ko"]:.3e}  '
                  f'β(res)={r["beta_cwm_resistance"]:+.4f} p={r["p_cwm_resistance"]:.3e}  '
                  f'β(cof)={r["beta_cwm_cofactor"]:+.4f} p={r["p_cwm_cofactor"]:.3e}')

        ngsa_df_res = pd.DataFrame(ngsa_results)
        if len(ngsa_df_res) > 0:
            ngsa_df_res = apply_fdr(ngsa_df_res)
    else:
        print(f'Insufficient samples within threshold ({len(within_au)} < 30); NGSA skipped.')
else:
    print('No Australian CWM samples found; NGSA analysis skipped.')


# ═══════════════════════════════════════════════════════════════════════════════
# Save combined CSV
# ═══════════════════════════════════════════════════════════════════════════════
frames = [georoc_df, csu_df_res]
if len(ngsa_df_res) > 0:
    frames.append(ngsa_df_res)
combined = pd.concat(frames, ignore_index=True, sort=False)
combined.to_csv(DATA / 'cwm_community_validation_results.csv', index=False)
print(f'\nCombined results saved: {len(combined)} total rows '
      f'({len(georoc_df)} GEOROC + {len(csu_df_res)} CSU + {len(ngsa_df_res)} NGSA)')


# ═══════════════════════════════════════════════════════════════════════════════
# Markdown report
# ═══════════════════════════════════════════════════════════════════════════════
def fmt_p(p):
    if pd.isna(p): return 'NA'
    if p < 0.001:  return f'{p:.2e}'
    return f'{p:.4f}'

def sig_label(p):
    if pd.isna(p): return ''
    if p < 0.001:  return ' ***'
    if p < 0.01:   return ' **'
    if p < 0.05:   return ' *'
    if p < 0.10:   return ' †'
    return ''

def fmt_b(b, p):
    if pd.isna(b): return 'NA'
    return f'{b:+.4f}{sig_label(p)}'

lines = []
lines.append('# Community CWM Validation — CSU Mobile Metals and NGSA Total Soil Metals\n')
lines.append('## Overview\n')
lines.append('Re-analysis of the community-level CWM regression (Analysis 2) using ecologically relevant '
             'metal predictors. The prior Analysis 2 used GEOROC bedrock concentrations, which reflect '
             'geological substrate rather than bioavailable metal stress. Two additional predictors are tested: '
             '(1) CSU PF1 mobile (bioavailable) metal fractions spatially assigned to MicrobeAtlas samples via '
             'sample accession ID; and (2) NGSA measured total soil metal concentrations (Australia only, '
             'spatial join ≤50 km).\n')

# ── CSU results ───────────────────────────────────────────────────────────────
lines.append('---\n')
lines.append('## Analysis A — CSU PF1 Mobile Metal Fractions\n')
lines.append('**Predictor**: CSU PF1 bioavailable fraction (dimensionless, 0–0.5). '
             'Joined directly to MicrobeAtlas CWM samples via accession ID. '
             f'**n matched**: {len(cwm_csu):,} samples.\n')

if len(csu_df_res) > 0:
    lines.append('### Model A — Aggregate CWM metal-gene density\n')
    lines.append('`log10(PF1_metal + 1) ~ cwm_ko_per_mb_z`\n')
    lines.append('| Metal | N samples | β(CWM_ko) | p | q (BH) |')
    lines.append('|-------|-----------|-----------|---|--------|')
    for _, row in csu_df_res.iterrows():
        b = row['beta_cwm_ko']; p = row['p_cwm_ko']; q = row.get('q_cwm_ko', np.nan)
        lines.append(f'| {row["metal"]} | {int(row["n_samples_modelA"]):,} | '
                     f'{fmt_b(b, p)} | {fmt_p(p)} | {fmt_p(q)} |')
    lines.append('')
    lines.append('*\\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10*\n')

    lines.append('### Model B — Resistance/cofactor split\n')
    lines.append('`log10(PF1_metal + 1) ~ cwm_resistance_z + cwm_cofactor_z [+ soil_pH]`\n')
    lines.append('| Metal | N | β(resistance) | p | q | β(cofactor) | p | q |')
    lines.append('|-------|---|--------------|---|---|-------------|---|---|')
    for _, row in csu_df_res.iterrows():
        ph = '+pH' if row.get('soil_pH_included', False) else ''
        br = row['beta_cwm_resistance']; pr = row['p_cwm_resistance']; qr = row.get('q_cwm_resistance', np.nan)
        bc = row['beta_cwm_cofactor'];   pc = row['p_cwm_cofactor'];   qc = row.get('q_cwm_cofactor', np.nan)
        lines.append(f'| {row["metal"]}{ph} | {int(row["n_samples_modelB"]):,} | '
                     f'{fmt_b(br, pr)} | {fmt_p(pr)} | {fmt_p(qr)} | '
                     f'{fmt_b(bc, pc)} | {fmt_p(pc)} | {fmt_p(qc)} |')
    lines.append('')
    lines.append('*+pH = soil pH covariate included; \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10*\n')
else:
    lines.append('*No CSU metals met the ≥30 sample threshold.*\n')

# ── NGSA results ──────────────────────────────────────────────────────────────
lines.append('---\n')
lines.append('## Analysis B — NGSA Total Soil Metals (Australia, ≤50 km spatial join)\n')
if len(ngsa_df_res) > 0:
    lines.append(f'**Spatial join**: CWM samples within {NGSA_MAX_KM} km of an NGSA site. '
                 f'**n matched**: {len(within_au):,} CWM samples (Australian subset).\n')
    lines.append('### Model A\n')
    lines.append('`log10(NGSA_metal_ppm + 1) ~ cwm_ko_per_mb_z`\n')
    lines.append('| Metal | N samples | β(CWM_ko) | p | q (BH) |')
    lines.append('|-------|-----------|-----------|---|--------|')
    for _, row in ngsa_df_res.iterrows():
        b = row['beta_cwm_ko']; p = row['p_cwm_ko']; q = row.get('q_cwm_ko', np.nan)
        lines.append(f'| {row["metal"]} | {int(row["n_samples_modelA"]):,} | '
                     f'{fmt_b(b, p)} | {fmt_p(p)} | {fmt_p(q)} |')
    lines.append('')
    lines.append('*\\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10*\n')

    lines.append('### Model B\n')
    lines.append('`log10(NGSA_metal_ppm + 1) ~ cwm_resistance_z + cwm_cofactor_z [+ soil_pH]`\n')
    lines.append('| Metal | N | β(resistance) | p | q | β(cofactor) | p | q |')
    lines.append('|-------|---|--------------|---|---|-------------|---|---|')
    for _, row in ngsa_df_res.iterrows():
        ph = '+pH' if row.get('soil_pH_included', False) else ''
        br = row['beta_cwm_resistance']; pr = row['p_cwm_resistance']; qr = row.get('q_cwm_resistance', np.nan)
        bc = row['beta_cwm_cofactor'];   pc = row['p_cwm_cofactor'];   qc = row.get('q_cwm_cofactor', np.nan)
        lines.append(f'| {row["metal"]}{ph} | {int(row["n_samples_modelB"]):,} | '
                     f'{fmt_b(br, pr)} | {fmt_p(pr)} | {fmt_p(qr)} | '
                     f'{fmt_b(bc, pc)} | {fmt_p(pc)} | {fmt_p(qc)} |')
    lines.append('')
else:
    lines.append('*NGSA analysis not completed (insufficient CWM samples within 50 km of NGSA sites).*\n')

# ── Comparison table (overlapping metals) ──────────────────────────────────────
lines.append('---\n')
lines.append('## Comparison: GEOROC bedrock vs CSU mobile vs NGSA total soil\n')
lines.append('Model B resistance and cofactor β for metals with data in ≥2 sources.\n')

# Build lookup dicts
def make_lookup(df, source_col='source', metal_col='metal'):
    if df is None or len(df) == 0:
        return {}
    return {row[metal_col]: row.to_dict() for _, row in df.iterrows()}

georoc_lu = make_lookup(georoc_df)
csu_lu    = make_lookup(csu_df_res)
ngsa_lu   = make_lookup(ngsa_df_res) if len(ngsa_df_res) > 0 else {}

all_metals = sorted(set(list(georoc_lu) + list(csu_lu) + list(ngsa_lu)))

header = ('| Metal | GEOROC β(res) | GEOROC p | '
          'CSU β(res) | CSU p | '
          'NGSA β(res) | NGSA p | '
          'GEOROC β(cof) | GEOROC p | '
          'CSU β(cof) | CSU p | '
          'NGSA β(cof) | NGSA p |')
sep = ('|-------|--------------|----------|'
       '-----------|-------|'
       '------------|--------|'
       '--------------|----------|'
       '-----------|-------|'
       '------------|--------|')
lines.append(header)
lines.append(sep)

for m in all_metals:
    gr = georoc_lu.get(m, {})
    cs = csu_lu.get(m, {})
    ng = ngsa_lu.get(m, {})

    def cell_b(d, key='beta_cwm_resistance', pkey='p_cwm_resistance'):
        if not d: return '—'
        return fmt_b(d.get(key, np.nan), d.get(pkey, np.nan))

    def cell_p(d, pkey='p_cwm_resistance'):
        if not d: return '—'
        p = d.get(pkey, np.nan)
        return fmt_p(p)

    row_str = (f'| {m} | '
               f'{cell_b(gr)} | {cell_p(gr)} | '
               f'{cell_b(cs)} | {cell_p(cs)} | '
               f'{cell_b(ng)} | {cell_p(ng)} | '
               f'{cell_b(gr, "beta_cwm_cofactor", "p_cwm_cofactor")} | '
               f'{cell_p(gr, "p_cwm_cofactor")} | '
               f'{cell_b(cs, "beta_cwm_cofactor", "p_cwm_cofactor")} | '
               f'{cell_p(cs, "p_cwm_cofactor")} | '
               f'{cell_b(ng, "beta_cwm_cofactor", "p_cwm_cofactor")} | '
               f'{cell_p(ng, "p_cwm_cofactor")} |')
    lines.append(row_str)

lines.append('')
lines.append('*\\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10. '
             '— = metal not available in that source.*\n')

# ── Interpretation ────────────────────────────────────────────────────────────
lines.append('---\n')
lines.append('## Interpretation\n')

# Summarise CSU directions
if len(csu_df_res) > 0:
    n_csu = len(csu_df_res)
    pos_res_csu = (csu_df_res['beta_cwm_resistance'] > 0).sum()
    neg_cof_csu = (csu_df_res['beta_cwm_cofactor'] < 0).sum()
    sig_res_csu = (csu_df_res['p_cwm_resistance'] < 0.05).sum()
    sig_cof_csu = (csu_df_res['p_cwm_cofactor'] < 0.05).sum()
    sig_res_q_csu = (csu_df_res.get('q_cwm_resistance', pd.Series([np.nan]*n_csu)) < 0.05).sum()
    sig_cof_q_csu = (csu_df_res.get('q_cwm_cofactor', pd.Series([np.nan]*n_csu)) < 0.05).sum()

    # Compare with GEOROC directions
    georoc_pos_res = (georoc_df['beta_cwm_resistance'] > 0).sum()
    georoc_neg_cof = (georoc_df['beta_cwm_cofactor'] < 0).sum()
    n_georoc = len(georoc_df)

    lines.append('### CSU PF1 mobile metal fractions\n')
    lines.append(f'CSU PF1 bioavailable metal fractions were joined to {len(cwm_csu):,} CWM samples via '
                 f'direct accession-ID matching, testing {n_csu} metals. '
                 f'For **resistance CWM**: {pos_res_csu}/{n_csu} metals show positive β (vs {georoc_pos_res}/{n_georoc} for GEOROC); '
                 f'{sig_res_csu} individually significant at p < 0.05 ({sig_res_q_csu} at BH q < 0.05). '
                 f'For **cofactor CWM**: {neg_cof_csu}/{n_csu} metals show negative β (vs {georoc_neg_cof}/{n_georoc} for GEOROC); '
                 f'{sig_cof_csu} individually significant at p < 0.05 ({sig_cof_q_csu} at BH q < 0.05).\n')

    # Determine overall conclusion
    csu_resist_better = pos_res_csu > georoc_pos_res
    csu_cofact_better = neg_cof_csu > georoc_neg_cof

    if pos_res_csu >= n_csu * 0.5 and neg_cof_csu >= n_csu * 0.5:
        conclusion_csu = (
            'The CSU mobile metal analysis shows a **stronger and more directionally consistent** signal '
            'than the GEOROC bedrock analysis: resistance-enriched communities tend to inhabit areas with '
            'higher bioavailable metal fractions (consistent with metal stress selection), while cofactor-enriched '
            'communities do not. This pattern directly supports the genus-level finding that mobile (bioavailable) '
            'metals, rather than geological bedrock concentrations, are the ecologically relevant predictor of '
            'community metal-gene investment. The community-level signal emerges specifically when a biologically '
            'meaningful metal metric is used, corroborating the interpretation that metal bioavailability drives '
            'the observed genus-level association.'
        )
    elif pos_res_csu > georoc_pos_res or neg_cof_csu > georoc_neg_cof:
        conclusion_csu = (
            'The CSU mobile metal analysis shows a **partially stronger signal** relative to GEOROC bedrock: '
            f'resistance CWM direction is positive for {pos_res_csu}/{n_csu} metals (vs {georoc_pos_res}/{n_georoc} GEOROC) '
            f'and cofactor CWM direction is negative for {neg_cof_csu}/{n_csu} metals (vs {georoc_neg_cof}/{n_georoc} GEOROC). '
            'The improvement is modest, suggesting that the community-level CWM signal is not strongly contingent '
            'on the choice of metal predictor and that the weak signal observed with GEOROC bedrock concentrations '
            'reflects a genuine limitation of the community-level approach rather than purely a metal-metric artefact. '
            'Possible explanations include spatial scale mismatch between community composition data and metal '
            'measurements, dominance of unmeasured environmental drivers (moisture, carbon, pH), or that '
            'community assembly at the broad biome level integrates metal signals too weakly to recover the '
            'genus-level evolutionary signal.'
        )
    else:
        conclusion_csu = (
            'The CSU mobile metal analysis does **not show a stronger signal** than GEOROC bedrock: '
            f'resistance CWM direction is positive for {pos_res_csu}/{n_csu} metals '
            f'and cofactor CWM direction is negative for {neg_cof_csu}/{n_csu} metals, '
            'similar to or weaker than GEOROC. This indicates that the weak community-level CWM signal is not '
            'explained by the choice of metal predictor, and instead reflects a genuine mismatch between the '
            'community-level CWM approach and the genus-level evolutionary pattern in P1. '
            'The genus-level PGLS niche-breadth signal and the community-level metal-concentration regression '
            'are testing conceptually distinct hypotheses (evolutionary niche specialisation vs community assembly '
            'response to metal gradients), and their lack of congruence at the community level is not '
            'unexpected given the spatial scale mismatch and the many unmeasured mediators (pH, SOM, redox, '
            'metal speciation) between bulk metal concentrations and microbial community composition.'
        )
    lines.append(conclusion_csu + '\n')

else:
    lines.append('CSU mobile metal analysis did not produce results.\n')

if len(ngsa_df_res) > 0:
    n_ngsa = len(ngsa_df_res)
    pos_res_ng = (ngsa_df_res['beta_cwm_resistance'] > 0).sum()
    neg_cof_ng = (ngsa_df_res['beta_cwm_cofactor'] < 0).sum()
    sig_res_ng = (ngsa_df_res['p_cwm_resistance'] < 0.05).sum()
    sig_cof_ng = (ngsa_df_res['p_cwm_cofactor'] < 0.05).sum()

    lines.append('### NGSA total soil metals (Australia)\n')
    lines.append(f'NGSA measured total soil concentrations were spatially joined to {len(within_au):,} '
                 f'Australian CWM samples (≤{NGSA_MAX_KM} km), testing {n_ngsa} metals. '
                 f'Resistance CWM: positive β for {pos_res_ng}/{n_ngsa} metals ({sig_res_ng} sig. at p<0.05). '
                 f'Cofactor CWM: negative β for {neg_cof_ng}/{n_ngsa} metals ({sig_cof_ng} sig. at p<0.05). '
                 'The Australian-restricted sample provides a geographic sensitivity check. '
                 'Results should be interpreted cautiously given the limited geographic footprint.\n')

lines.append('### SI paragraph (suggested text)\n')
lines.append('> **Community-level CWM validation with bioavailable and total soil metals.** '
             'We repeated Analysis 2 using two additional metal predictors to test whether the choice of '
             'metal metric explains the weak community-level signal observed with GEOROC bedrock concentrations. '
             f'CSU PF1 bioavailable (mobile) metal fractions (n = {len(cwm_csu):,} samples with accession-matched '
             'CSU data) were used as a predictor of community-weighted mean (CWM) metal-gene density. ')

if len(csu_df_res) > 0:
    lines.append(f'> CWM resistance density was positively associated with bioavailable metal fractions '
                 f'for {pos_res_csu}/{n_csu} metals ({sig_res_csu} individually significant at p < 0.05, '
                 f'{sig_res_q_csu} at BH q < 0.05), and CWM cofactor density was negatively associated '
                 f'for {neg_cof_csu}/{n_csu} metals ({sig_cof_csu} significant). ')

if len(ngsa_df_res) > 0:
    lines.append(f'> NGSA total soil metal concentrations (Australia only, n = {len(within_au):,} '
                 f'CWM samples within {int(NGSA_MAX_KM)} km of an NGSA site) showed resistance CWM '
                 f'positively associated with {pos_res_ng}/{n_ngsa} metals ({sig_res_ng} significant) '
                 f'and cofactor CWM negatively associated with {neg_cof_ng}/{n_ngsa} metals ({sig_cof_ng} significant). ')

lines.append('> Overall, ' + (
    'the directional consistency improved with CSU bioavailable metal fractions relative to GEOROC bedrock '
    'concentrations, consistent with the genus-level finding that mobile metals are the ecologically relevant predictor. '
    if len(csu_df_res) > 0 and pos_res_csu >= n_csu * 0.5 else
    'the community-level CWM signal remained weak across metal predictors, suggesting that this reflects '
    'a scale mismatch between community-level assembly and the genus-level evolutionary signal rather than an artefact '
    'of the specific metal metric. '
) + 'The CWM approach integrates metal exposure signals at the biome level and is subject to '
    'confounding by unmeasured variables (pH, organic matter, redox state, metal speciation) that mediate '
    'the relationship between metal concentrations and microbial community composition. '
    'Results are reported for completeness but do not alter the primary conclusions, which are based on the '
    'genus-level PGLS analysis.\n')

report_text = '\n'.join(lines)
out_path = PROJECT / 'cwm_mobile_metals_validation.md'
out_path.write_text(report_text)
print(f'\nReport written to: {out_path}')
print('Done.')
