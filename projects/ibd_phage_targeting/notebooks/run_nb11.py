"""NB11 — HMP2 serology × Tier-A pathobiont (H3e).

Per plan v1.7 H3e: serology (anti-flagellin / anti-LPS / anti-microbial
antibodies) × Tier-A pathobiont abundance correlation, n=67 subjects across
3 sites (CCHMC/Harvard/Emory), site as covariate, effect threshold |r|>0.40
calibrated to n=67 power 0.80 at α=0.05. Single-cohort caveat structural.

Per plan v1.9 (no raw reads): uses cMD-fetched HMP2 MetaPhlAn3 abundance +
mart fact_serology.

Falsifiability per plan v1.7:
  - SUPPORTED if ≥1 (assay × Tier-A core species) pair has |r|>0.40 AND
    FDR<0.10 AND survives the site-covariate adjustment
  - NOT-SUPPORTED if no pair clears both thresholds

The 6 EU-deduplicated serology axes are: ANCA EU, ASCA (combined panel),
CBir1 EU, IgA ASCA EU, IgG ASCA EU, OmpC EU. Plus the binary positives if
distinct directional info.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJ = '/home/aparkin/BERIL-research-observatory-ibd/projects/ibd_phage_targeting'
MART = '/home/aparkin/data/CrohnsPhage'
EXT = '/home/aparkin/data/CrohnsPhage_ext'
OUT_DATA = f'{PROJ}/data'
OUT_FIG = f'{PROJ}/figures'
SECTION_LOGS = {}


def log_section(key, msg):
    SECTION_LOGS.setdefault(key, '')
    SECTION_LOGS[key] += msg + '\n'
    print(msg)


# ---------------------------------------------------------------------------
# §0. Load fact_serology + cMD HMP2 metadata + relative abundance
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load fact_serology + cMD HMP2 MetaPhlAn3 abundance')

sero = pd.read_parquet(f'{MART}/fact_serology.snappy.parquet')
sero = sero.copy()
sero['subject_id'] = sero['participant_id'].str.replace('HMP2:', '', regex=False)
log_section('0', f'fact_serology: {sero.shape[0]} measurements; {sero["subject_id"].nunique()} subjects; {sero["assay"].nunique()} assays')
log_section('0', f'  Sites: {sero["site"].value_counts().to_dict()}')

md = pd.read_csv(f'{EXT}/hmp2_ibdmdb_sample_metadata.tsv', sep='\t')
md['code'] = md['sample_id'].str.replace('_P$', '', regex=True)

ra = pd.read_csv(f'{EXT}/hmp2_ibdmdb_relative_abundance.tsv', sep='\t', index_col=0)
ra.index = ra.index.str.replace('species:', '', regex=False)
ra.columns = ra.columns.str.replace('_P$', '', regex=True)
ra = ra.loc[:, ~ra.columns.duplicated(keep='first')]
log_section('0', f'HMP2 MetaPhlAn3 abundance: {ra.shape}')

# Map subject_id → metaPhlAn3 sample codes
serology_subjects = sorted(sero['subject_id'].unique())
md_for_serology = md[md['subject_id'].isin(serology_subjects)].copy()
log_section('0', f'\nMetaPhlAn3 samples for {len(serology_subjects)} serology subjects: {md_for_serology.shape[0]}')
log_section('0', f'  with abundance data: {md_for_serology["code"].isin(ra.columns).sum()}')

# Subject → list of MetaPhlAn3 sample codes
subj_samples = md_for_serology[md_for_serology['code'].isin(ra.columns)].groupby('subject_id')['code'].apply(list).to_dict()
subjects_with_metag = sorted(subj_samples.keys())
log_section('0', f'  subjects with at least 1 metaPhlAn3 sample: {len(subjects_with_metag)} of {len(serology_subjects)}')

# Subject → first diagnosis
subj_dx = md_for_serology.drop_duplicates(subset='subject_id').set_index('subject_id')[['study_condition', 'disease_subtype']]


# ---------------------------------------------------------------------------
# §1. Build subject × {Tier-A species, NB07c module, serology assay} matrices
# ---------------------------------------------------------------------------
log_section('1', '## §1. Build subject-level matrices')

# Tier-A core (NB05 actionable) + NB07c module species
SPECIES_MAP = {
    'H. hathewayi': 'Hungatella hathewayi',
    'M. gnavus': '[Ruminococcus] gnavus',
    'E. coli': 'Escherichia coli',
    'E. lenta': 'Eggerthella lenta',
    'F. plautii': 'Flavonifractor plautii',
    'E. bolteae': 'Enterocloster bolteae',
    'A. caccae (anchor)': 'Anaerostipes caccae',
    'B. nordii (anchor)': 'Bacteroides nordii',
}
species_present = {k: v for k, v in SPECIES_MAP.items() if v in ra.index}
log_section('1', f'Species present in MetaPhlAn3: {len(species_present)} / {len(SPECIES_MAP)}')

# Build subject × species matrix using mean (log10 + 0.001) abundance over visits
subj_species_rows = []
for subj in subjects_with_metag:
    samples = subj_samples[subj]
    row = {'subject_id': subj}
    for label, sp_name in species_present.items():
        if sp_name in ra.index:
            vals = ra.loc[sp_name, samples].values
            mean_abund = np.mean(vals)
            log_mean = np.log10(mean_abund + 0.001)
            row[label] = log_mean
        else:
            row[label] = np.nan
    subj_species_rows.append(row)
sp_mat = pd.DataFrame(subj_species_rows).set_index('subject_id')
log_section('1', f'Subject × species matrix: {sp_mat.shape}')

# Serology axes — 6 EU-deduped
SEROLOGY_AXES = {
    'ANCA': ['ANCA EU'],
    'ASCA': ['ASCA Panel'],  # binary panel; supplement with IgA + IgG below
    'CBir1': ['Cbir1 EU'],
    'IgA_ASCA': ['IgA ASCA EU'],
    'IgG_ASCA': ['IgG ASCA EU'],
    'OmpC': ['OmpC. EU'],
}

# Subject × assay aggregates (mean of EU values over visits)
subj_sero_rows = []
for subj in subjects_with_metag:
    sub_sero = sero[sero['subject_id'] == subj]
    row = {'subject_id': subj}
    site_vals = sub_sero['site'].dropna().value_counts()
    row['site'] = site_vals.idxmax() if len(site_vals) > 0 else 'Unknown'
    for axis, assays in SEROLOGY_AXES.items():
        vals = sub_sero[sub_sero['assay'].isin(assays)]['value']
        if len(vals):
            row[axis] = float(vals.mean())
        else:
            row[axis] = np.nan
    subj_sero_rows.append(row)
sero_mat = pd.DataFrame(subj_sero_rows).set_index('subject_id')

# Restrict to subjects with at least 1 serology measurement on at least 3 axes
valid_subjects = sero_mat[sero_mat[list(SEROLOGY_AXES.keys())].notna().sum(axis=1) >= 3].index
sero_mat = sero_mat.loc[valid_subjects]
sp_mat = sp_mat.loc[valid_subjects]
log_section('1', f'\nFinal valid subjects: {len(valid_subjects)}')
log_section('1', f'  Site distribution: {sero_mat["site"].value_counts().to_dict()}')
log_section('1', f'  Serology axis coverage: {sero_mat[list(SEROLOGY_AXES.keys())].notna().sum().to_dict()}')


# ---------------------------------------------------------------------------
# §2. Site-adjusted (assay × species) Pearson and Spearman
# ---------------------------------------------------------------------------
log_section('2', '## §2. Per-(assay × species) site-adjusted partial correlation')

# Add site dummy variables
site_dummies = pd.get_dummies(sero_mat['site'], prefix='site', drop_first=True)


def partial_corr(x, y, covariates_df):
    """Partial Pearson correlation of x vs y, controlling for columns in covariates_df.
    Implementation: residualize x and y on covariates via OLS, then Pearson on residuals."""
    df = pd.concat([
        pd.Series(x, name='x', index=covariates_df.index),
        pd.Series(y, name='y', index=covariates_df.index),
        covariates_df,
    ], axis=1).dropna()
    if len(df) < 10:
        return np.nan, np.nan, len(df)
    # Add intercept
    X_cov = np.column_stack([np.ones(len(df)), df[covariates_df.columns].values.astype(float)])
    # Residualize x
    bx, *_ = np.linalg.lstsq(X_cov, df['x'].values, rcond=None)
    rx = df['x'].values - X_cov @ bx
    # Residualize y
    by, *_ = np.linalg.lstsq(X_cov, df['y'].values, rcond=None)
    ry = df['y'].values - X_cov @ by
    if rx.std() < 1e-9 or ry.std() < 1e-9:
        return np.nan, np.nan, len(df)
    rho, p = stats.pearsonr(rx, ry)
    return rho, p, len(df)


species_labels = list(species_present.keys())
assay_labels = list(SEROLOGY_AXES.keys())

corr_rows = []
for assay in assay_labels:
    if assay not in sero_mat.columns:
        continue
    y = sero_mat[assay]
    for sp in species_labels:
        if sp not in sp_mat.columns:
            continue
        x = sp_mat[sp]
        # Spearman raw
        df_pair = pd.concat([x, y], axis=1).dropna()
        if len(df_pair) < 20:
            continue
        rho_sp, p_sp = stats.spearmanr(df_pair.iloc[:, 0], df_pair.iloc[:, 1])
        # Pearson partial controlling for site
        r_p, p_p, n_p = partial_corr(x.values, y.values, site_dummies)
        corr_rows.append({
            'assay': assay,
            'species': sp,
            'n': len(df_pair),
            'spearman_rho': round(float(rho_sp), 3),
            'spearman_p': float(p_sp),
            'partial_pearson_r': round(float(r_p), 3) if not np.isnan(r_p) else np.nan,
            'partial_pearson_p': float(p_p) if not np.isnan(p_p) else np.nan,
            'n_partial': int(n_p),
        })

corr_df = pd.DataFrame(corr_rows)

# BH-FDR on partial Pearson p-values
m = corr_df['partial_pearson_p'].dropna().shape[0]
if m > 0:
    pvals = corr_df['partial_pearson_p'].values
    valid_mask = ~np.isnan(pvals)
    pvals_valid = pvals[valid_mask]
    order = np.argsort(pvals_valid)
    ranked = pvals_valid[order]
    fdr_adj = np.minimum.accumulate((ranked[::-1] * m / np.arange(m, 0, -1)))[::-1]
    fdr_full = np.full(len(pvals), np.nan)
    valid_indices = np.where(valid_mask)[0]
    for i, idx in enumerate(order):
        fdr_full[valid_indices[idx]] = fdr_adj[i]
    corr_df['fdr'] = fdr_full
else:
    corr_df['fdr'] = np.nan

corr_df['supported'] = (corr_df['fdr'] < 0.10) & (corr_df['partial_pearson_r'].abs() > 0.40)

log_section('2', f'Total (assay × species) tests: {len(corr_df)}')
log_section('2', f'Tests at |r|>0.40 (raw threshold): {(corr_df["partial_pearson_r"].abs() > 0.40).sum()}')
log_section('2', f'Tests at FDR<0.10: {(corr_df["fdr"] < 0.10).sum()}')
log_section('2', f'Supported (|r|>0.40 AND FDR<0.10): {corr_df["supported"].sum()}')

# Top hits
log_section('2', f'\nAll (assay × species) results sorted by |partial_pearson_r|:\n')
log_section('2', corr_df.sort_values('partial_pearson_r', key=abs, ascending=False)[['assay', 'species', 'n', 'spearman_rho', 'partial_pearson_r', 'fdr', 'supported']].to_string(index=False))

corr_df.to_csv(f'{OUT_DATA}/nb11_serology_species_correlations.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §3. Site-stratified breakdown (per-site partial r) for top pairs
# ---------------------------------------------------------------------------
log_section('3', '## §3. Site-stratified per-pair check (top 10 by |partial r|)')

top10 = corr_df.sort_values('partial_pearson_r', key=abs, ascending=False).head(10)
site_rows = []
for _, r in top10.iterrows():
    assay = r['assay']
    sp = r['species']
    for site in sero_mat['site'].unique():
        site_mask = sero_mat['site'] == site
        x_site = sp_mat.loc[site_mask, sp]
        y_site = sero_mat.loc[site_mask, assay]
        df_site = pd.concat([x_site, y_site], axis=1).dropna()
        if len(df_site) < 10:
            site_rows.append({'assay': assay, 'species': sp, 'site': site, 'n': len(df_site), 'rho': np.nan, 'p': np.nan})
            continue
        rho, p = stats.spearmanr(df_site.iloc[:, 0], df_site.iloc[:, 1])
        site_rows.append({'assay': assay, 'species': sp, 'site': site, 'n': len(df_site), 'rho': round(float(rho), 3), 'p': float(p)})

site_df = pd.DataFrame(site_rows)
log_section('3', site_df.to_string(index=False))
site_df.to_csv(f'{OUT_DATA}/nb11_serology_site_stratified.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §4. Disease-subtype check — does serology track diagnosis?
# ---------------------------------------------------------------------------
log_section('4', '## §4. Serology axis × diagnosis (sanity check on cohort)')

dx_check = sero_mat.join(subj_dx, how='left')
log_section('4', f'\nDiagnosis distribution in {len(dx_check)} valid subjects:')
log_section('4', dx_check['disease_subtype'].fillna('NA').value_counts().to_string())
log_section('4', dx_check['study_condition'].fillna('NA').value_counts().to_string())

log_section('4', f'\nMean serology by disease_subtype:')
for axis in assay_labels:
    if axis in dx_check.columns:
        means = dx_check.groupby('disease_subtype')[axis].mean()
        log_section('4', f'  {axis}: {means.to_dict()}')


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. H3e verdict + figure')

n_supported = int(corr_df['supported'].sum())
n_tested = len(corr_df)
top_pair = corr_df.sort_values('partial_pearson_r', key=abs, ascending=False).iloc[0] if len(corr_df) else None

if n_supported >= 1:
    verdict_str = f'SUPPORTED — {n_supported} (assay × species) pair(s) at |r|>0.40 AND FDR<0.10'
elif (corr_df['partial_pearson_r'].abs() > 0.30).any():
    verdict_str = 'PARTIAL — moderate correlations (|r|>0.30) but none meeting strict |r|>0.40+FDR<0.10 threshold'
else:
    verdict_str = 'NOT SUPPORTED — no (assay × species) pair clears |r|>0.40+FDR<0.10'

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'H3e — HMP2 serology × Tier-A pathobiont correlation (n=67 across 3 sites, site as covariate)',
    'n_subjects_with_metag_and_serology': len(valid_subjects),
    'n_assay_species_tests': n_tested,
    'n_supported_strict': n_supported,
    'n_with_abs_r_above_03': int((corr_df['partial_pearson_r'].abs() > 0.30).sum()),
    'top_pair': {
        'assay': top_pair['assay'] if top_pair is not None else None,
        'species': top_pair['species'] if top_pair is not None else None,
        'partial_r': float(top_pair['partial_pearson_r']) if top_pair is not None else None,
        'fdr': float(top_pair['fdr']) if top_pair is not None else None,
    } if top_pair is not None else None,
    'h3e_verdict': verdict_str,
}
with open(f'{OUT_DATA}/nb11_h3e_verdict.json', 'w') as fp_out:
    json.dump(verdict, fp_out, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Panel A: heatmap of partial Pearson r
ax = axes[0]
heat = corr_df.pivot_table(index='species', columns='assay', values='partial_pearson_r')
sns.heatmap(heat, cmap='RdBu_r', center=0, vmin=-0.6, vmax=0.6, annot=True, fmt='.2f',
            cbar_kws={'label': 'Partial Pearson r (site-adjusted)'}, ax=ax,
            annot_kws={'fontsize': 8})
ax.set_title(f'A. Site-adjusted partial r (n={len(valid_subjects)} subjects)')
ax.set_xlabel('Serology axis')
ax.set_ylabel('Species')

# Panel B: top 10 pairs with thresholds
ax = axes[1]
top_n = 10
plot_df = corr_df.sort_values('partial_pearson_r', key=abs, ascending=False).head(top_n).iloc[::-1]
y = np.arange(len(plot_df))
colors = ['#e63946' if r['supported'] else ('#ffb703' if abs(r['partial_pearson_r']) > 0.30 else '#a8a8a8') for _, r in plot_df.iterrows()]
ax.barh(y, plot_df['partial_pearson_r'], color=colors)
labels = [f'{r["species"]} × {r["assay"]}' for _, r in plot_df.iterrows()]
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8)
ax.axvline(0, color='black', linewidth=0.5)
ax.axvline(0.40, color='gray', linestyle=':', linewidth=0.5)
ax.axvline(-0.40, color='gray', linestyle=':', linewidth=0.5)
ax.set_xlabel('Partial Pearson r (site-adjusted)')
ax.set_title(f'B. Top {top_n} pairs by |r|; |r|>0.40 = strict threshold')
for i, r in plot_df.reset_index(drop=True).iterrows():
    ax.text(r['partial_pearson_r'] + (0.02 if r['partial_pearson_r'] > 0 else -0.02), i,
            f'FDR={r["fdr"]:.2g}', va='center', fontsize=7,
            ha='left' if r['partial_pearson_r'] > 0 else 'right')

fig.suptitle(f'NB11 — HMP2 serology × Tier-A pathobiont (H3e): {verdict_str.split(" — ")[0]}', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB11_serology_pathobiont.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB11_serology_pathobiont.png')

with open('/tmp/nb11_section_logs.json', 'w') as fp_out:
    json.dump(SECTION_LOGS, fp_out, indent=2)
print(f'\nDone.')
