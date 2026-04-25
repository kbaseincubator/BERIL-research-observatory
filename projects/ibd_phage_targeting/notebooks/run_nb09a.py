"""NB09a — HMP2 metabolomics CD-vs-nonIBD differential abundance (H3d-DA).

Per plan v1.7 H3d-DA: per-metabolite CD-vs-nonIBD within HMP2; subject-level
analysis (first-occurrence sample per subject); BH-FDR + cliff_delta; per-theme
Fisher's exact enrichment on 6 IBD-relevant chemical-class themes.

Tests whether the metabolite axes that distinguish CD from nonIBD in HMP2 are
coherent with the iron-acquisition / TMA-choline / butyrate / bile-acid /
fatty-acid-amide themes already established by NB07-NB08a.
"""
import json
import sys
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
# §0. Load HMP2 metabolomics + annotations + sample→subject map
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load HMP2 metabolomics + sample→subject mapping + diagnosis')

# HMP2 metabolomics (long format)
metab = pd.read_parquet(f'{MART}/fact_metabolomics.snappy.parquet')
metab = metab[metab['study_id'] == 'HMP2_METABOLOMICS'].copy()
log_section('0', f'HMP2 metabolomics rows: {metab.shape[0]} ({metab["sample_id"].nunique()} samples × {metab["metabolite_id"].nunique()} metabolite IDs)')

# Annotations: 81867 rows; 592 named with HMDB
ann = pd.read_parquet(f'{MART}/ref_hmp2_metabolite_annotations.snappy.parquet')
named_ann = ann[ann['metabolite_name'].notna() & (ann['metabolite_name'].astype(str).str.strip() != '')].copy()
log_section('0', f'Named metabolites: {len(named_ann)} / {len(ann)} (HMDB-annotated)')

# Sample → subject → diagnosis map via cMD HMP2 metadata
ds = pd.read_parquet(f'{MART}/dim_samples.snappy.parquet')
hmp2_metab_samples = ds[ds['study_id'] == 'HMP2_METABOLOMICS'].copy()
hmp2_metab_samples['code'] = hmp2_metab_samples['sample_id'].str.replace('HMP2:', '', regex=False)

cmd_md = pd.read_csv(f'{EXT}/hmp2_ibdmdb_sample_metadata.tsv', sep='\t')
cmd_md['code'] = cmd_md['sample_id'].str.replace('_P', '', regex=False)
cmd_md_uniq = cmd_md.drop_duplicates(subset='code')[['code', 'subject_id', 'study_condition', 'disease_subtype', 'visit_number']]

merged = hmp2_metab_samples[['sample_id', 'code']].merge(cmd_md_uniq, on='code', how='inner')
log_section('0', f'Sample-level CD/UC/HC labels matched: {merged.shape[0]} / {hmp2_metab_samples.shape[0]} samples')
log_section('0', f'  Subjects with at least 1 matched sample: {merged["subject_id"].nunique()}')

# Subject-level: 1 sample per subject (lowest visit_number, fallback first row)
merged['visit_int'] = pd.to_numeric(merged['visit_number'], errors='coerce')
merged = merged.sort_values(['subject_id', 'visit_int']).copy()
subj_first = merged.groupby('subject_id', as_index=False).first()
log_section('0', f'Subject-level first-occurrence samples: {subj_first.shape[0]}')
log_section('0', f'  Diagnosis distribution: {subj_first["disease_subtype"].fillna("nonIBD").value_counts().to_dict()}')

# Define cd / nonibd / uc subject sets
subj_first['dx'] = subj_first['disease_subtype'].fillna('nonIBD')
subj_first.loc[subj_first['study_condition'] == 'control', 'dx'] = 'nonIBD'
cd_subjects = set(subj_first[subj_first['dx'] == 'CD']['subject_id'])
nonibd_subjects = set(subj_first[subj_first['dx'] == 'nonIBD']['subject_id'])
uc_subjects = set(subj_first[subj_first['dx'] == 'UC']['subject_id'])
log_section('0', f'\nFinal contrast groups (subject-level): CD={len(cd_subjects)}, nonIBD={len(nonibd_subjects)}, UC={len(uc_subjects)} (UC excluded from primary contrast)')


# ---------------------------------------------------------------------------
# §1. Build subject × metabolite matrix on named metabolites
# ---------------------------------------------------------------------------
log_section('1', '## §1. Subject × metabolite matrix (named metabolites only, first sample per subject)')

# Filter metabolomics to named metabolite IDs + matched samples
named_ids = set(named_ann['metabolite_id'])
metab_named = metab[metab['metabolite_id'].isin(named_ids)].copy()
log_section('1', f'Rows after named-metabolite filter: {metab_named.shape[0]}')

# Filter to subject-level first-occurrence samples
subj_sample_ids = set(subj_first['sample_id'])
metab_subj = metab_named[metab_named['sample_id'].isin(subj_sample_ids)].copy()
log_section('1', f'Rows on subject-level samples: {metab_subj.shape[0]}')

# Pivot: samples (rows) × metabolites (cols) using log10-intensity
metab_subj['log_intensity'] = np.log10(metab_subj['intensity'].clip(lower=0.01))
mat = metab_subj.pivot_table(index='sample_id', columns='metabolite_id', values='log_intensity', aggfunc='mean')
log_section('1', f'Subject × metabolite matrix: {mat.shape}')

# Map sample_id → diagnosis
sample_dx = subj_first.set_index('sample_id')['dx'].to_dict()
mat_dx = pd.Series([sample_dx.get(s, 'nonIBD') for s in mat.index], index=mat.index)
log_section('1', f'Diagnosis distribution: {mat_dx.value_counts().to_dict()}')


# ---------------------------------------------------------------------------
# §2. Per-metabolite Mann-Whitney CD vs nonIBD + cliff_delta + BH-FDR
# ---------------------------------------------------------------------------
log_section('2', '## §2. Per-metabolite CD-vs-nonIBD Mann-Whitney + cliff_delta + BH-FDR')

cd_mask = mat_dx == 'CD'
nonibd_mask = mat_dx == 'nonIBD'
log_section('2', f'n_CD={cd_mask.sum()}; n_nonIBD={nonibd_mask.sum()}')

results = []
for mid in mat.columns:
    cd_vals = mat.loc[cd_mask, mid].dropna().values
    hc_vals = mat.loc[nonibd_mask, mid].dropna().values
    if len(cd_vals) < 5 or len(hc_vals) < 5:
        continue
    u, p = stats.mannwhitneyu(cd_vals, hc_vals, alternative='two-sided')
    n1, n2 = len(cd_vals), len(hc_vals)
    cliff = 2 * u / (n1 * n2) - 1
    median_cd = float(np.median(cd_vals))
    median_hc = float(np.median(hc_vals))
    results.append({
        'metabolite_id': mid,
        'n_cd': n1, 'n_hc': n2,
        'median_cd_log10intensity': round(median_cd, 3),
        'median_hc_log10intensity': round(median_hc, 3),
        'cliff_delta': round(cliff, 3),
        'mw_p': p,
    })

res_df = pd.DataFrame(results)
log_section('2', f'Tested metabolites: {len(res_df)} (with ≥5 samples in each group)')

# BH-FDR
m = len(res_df)
sorted_idx = res_df['mw_p'].argsort().values
ranked_p = res_df['mw_p'].iloc[sorted_idx].values
fdr_adj = np.minimum.accumulate((ranked_p[::-1] * m / np.arange(m, 0, -1)))[::-1]
fdr_orig = np.empty(m)
for i, idx in enumerate(sorted_idx):
    fdr_orig[idx] = fdr_adj[i]
res_df['fdr'] = fdr_orig

# Annotate
res_df = res_df.merge(named_ann[['metabolite_id', 'metabolite_name', 'hmdb_id', 'method']], on='metabolite_id', how='left')

# Direction labels
res_df['direction'] = np.where(res_df['cliff_delta'] > 0, 'CD-up', 'CD-down')
res_df['passes'] = (res_df['fdr'] < 0.10) & (res_df['cliff_delta'].abs() > 0.20)

n_pass = res_df['passes'].sum()
n_cd_up = ((res_df['passes']) & (res_df['cliff_delta'] > 0)).sum()
n_cd_down = ((res_df['passes']) & (res_df['cliff_delta'] < 0)).sum()
log_section('2', f'Passing FDR<0.10 & |cliff_delta|>0.20: {n_pass} ({n_cd_up} CD-up, {n_cd_down} CD-down)')

# Top hits
log_section('2', f'\nTop 20 CD-up:')
top_up = res_df[res_df['passes'] & (res_df['cliff_delta'] > 0)].nlargest(20, 'cliff_delta')
log_section('2', top_up[['metabolite_name', 'method', 'cliff_delta', 'fdr']].to_string(index=False))
log_section('2', f'\nTop 20 CD-down:')
top_down = res_df[res_df['passes'] & (res_df['cliff_delta'] < 0)].nsmallest(20, 'cliff_delta')
log_section('2', top_down[['metabolite_name', 'method', 'cliff_delta', 'fdr']].to_string(index=False))

res_df.to_csv(f'{OUT_DATA}/nb09a_metab_da_cd_vs_nonibd.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §3. Theme overlay: 6 IBD-relevant chemical classes
# ---------------------------------------------------------------------------
log_section('3', '## §3. Theme overlay (chemical-class assignment for 592 named metabolites)')

# Theme keyword sets (case-insensitive substring match on metabolite_name)
THEMES = {
    'bile_acids': ['cholat', 'cholic', 'lithochol', 'chenodeoxychol', 'urodeoxychol', 'hyodeoxychol', 'taurochol', 'glycochol', 'taurine-conjug', 'glycine-conjug',
                   'tauroursodeoxy', 'tauro-', 'glyco-', 'cholate', 'muricholate', 'taurine'],
    'short_chain_fatty_acids': ['butyrat', 'propionat', 'acetat', 'valerate', 'pentanoa', 'hexanoa', 'caproate', 'butanoa', 'isovalerate', 'isobutyrate'],
    'tma_choline': ['choline', 'trimethylamine', 'TMAO', 'betaine', 'phosphochol', 'glycerophosphochol'],
    'tryptophan_indole': ['tryptophan', 'indole', 'kynureni', 'serotonin', 'indoleacet', 'indolepropion', 'indolelactate'],
    'fatty_acid_amides': ['palmitoylethanolam', 'oleamide', 'anandamide', 'arachidonoyl', 'oleoylethanolam', '-ethanolamide', 'NAE', 'OEA', 'PEA'],
    'aromatic_AA_metabolites': ['phenylacet', 'tyrosine', 'phenylalanine', 'phenyllactate', 'p-cresol', 'p-hydroxyphenyl'],
    # Newly added themes based on observed CD-up signal in §2:
    'polyamines': ['putrescine', 'spermine', 'spermidine', 'cadaverine', 'agmatine', 'acetylspermine', 'acetylputrescine', 'anserine', 'carnosine'],
    'acyl_carnitines': ['carnitine', 'acetylcarnitine'],
    'long_chain_PUFA': ['arachidonate', 'adrenate', 'docosapentaenoate', 'docosahexaenoa', 'eicosapentaenoa', 'linoleate', 'oleate', 'linolenate', 'stearate', 'palmitate'],
    'lipid_classes': [' CE', ' SM', ' TAG', ' DAG', ' MAG', 'ceramide', 'sphingomyelin', 'cholesteryl', 'phosphatidyl'],
    'urobilin_porphyrin': ['urobilin', 'bilirubin', 'biliverdin', 'protoporphyrin', 'coproporphyrin'],
}


def assign_themes(name):
    if pd.isna(name):
        return []
    nl = str(name).lower()
    themes = []
    for theme, kws in THEMES.items():
        for kw in kws:
            if kw.lower() in nl:
                themes.append(theme)
                break
    return themes


named_ann['themes'] = named_ann['metabolite_name'].apply(assign_themes)
named_ann['n_themes'] = named_ann['themes'].apply(len)
res_df['themes'] = res_df['metabolite_name'].apply(assign_themes)
res_df['themes_str'] = res_df['themes'].apply(lambda x: ';'.join(x) if x else '')

# Per-theme counts
log_section('3', '\nPer-theme metabolite counts (any of 592 named):')
for theme in THEMES:
    n_in = named_ann['themes'].apply(lambda x: theme in x).sum()
    n_pass = res_df[res_df['passes']].apply(lambda r: theme in r['themes'], axis=1).sum() if len(res_df) else 0
    log_section('3', f'  {theme}: {n_in} background, {n_pass} passing CD-DA')


# ---------------------------------------------------------------------------
# §4. Per-theme Fisher's exact enrichment
# ---------------------------------------------------------------------------
log_section('4', '## §4. Per-theme Fisher\'s exact (CD-up × in-theme) + BH-FDR')

theme_rows = []
for theme in THEMES:
    in_theme = res_df['themes'].apply(lambda x: theme in x)
    cd_up_passing = res_df['passes'] & (res_df['cliff_delta'] > 0)
    a = (in_theme & cd_up_passing).sum()
    b = (in_theme & ~cd_up_passing).sum()
    c = (~in_theme & cd_up_passing).sum()
    d = (~in_theme & ~cd_up_passing).sum()
    if (a + c) == 0:
        continue
    or_, p = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
    expected = (a + b) * (a + c) / (a + b + c + d) if (a + b + c + d) else 0
    theme_rows.append({
        'theme': theme,
        'in_theme_total': int(a + b),
        'cd_up_in_theme': int(a),
        'cd_up_total': int(a + c),
        'expected_cd_up_in_theme': round(expected, 2),
        'odds_ratio': round(or_, 3),
        'fisher_p': p,
        'direction': 'CD-up',
    })
    # Also test CD-down
    cd_down_passing = res_df['passes'] & (res_df['cliff_delta'] < 0)
    a = (in_theme & cd_down_passing).sum()
    b = (in_theme & ~cd_down_passing).sum()
    c = (~in_theme & cd_down_passing).sum()
    d = (~in_theme & ~cd_down_passing).sum()
    if (a + c) == 0:
        continue
    or_, p = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
    theme_rows.append({
        'theme': theme,
        'in_theme_total': int(a + b),
        'cd_up_in_theme': int(a),
        'cd_up_total': int(a + c),
        'expected_cd_up_in_theme': round((a + b) * (a + c) / (a + b + c + d), 2) if (a + b + c + d) else 0,
        'odds_ratio': round(or_, 3),
        'fisher_p': p,
        'direction': 'CD-down',
    })

theme_df = pd.DataFrame(theme_rows)
m = len(theme_df)
sorted_idx = theme_df['fisher_p'].argsort().values
ranked_p = theme_df['fisher_p'].iloc[sorted_idx].values
fdr_adj = np.minimum.accumulate((ranked_p[::-1] * m / np.arange(m, 0, -1)))[::-1]
fdr_orig = np.empty(m)
for i, idx in enumerate(sorted_idx):
    fdr_orig[idx] = fdr_adj[i]
theme_df['fdr'] = fdr_orig
theme_df['supported'] = (theme_df['fdr'] < 0.10) & (theme_df['odds_ratio'] > 1.5)
theme_df.to_csv(f'{OUT_DATA}/nb09a_metab_theme_enrichment.tsv', sep='\t', index=False)

log_section('4', f'\nThemes supported (FDR<0.10, OR>1.5): {theme_df["supported"].sum()}\n')
log_section('4', theme_df.to_string(index=False))


# ---------------------------------------------------------------------------
# §5. Per-theme passing-metabolite list (audit)
# ---------------------------------------------------------------------------
log_section('5', '## §5. Per-theme passing metabolites (audit)')

for theme in THEMES:
    passing_in_theme = res_df[res_df['passes'] & res_df['themes'].apply(lambda x: theme in x)]
    if len(passing_in_theme) > 0:
        log_section('5', f'\n{theme} ({len(passing_in_theme)} passing):')
        for _, r in passing_in_theme.sort_values('cliff_delta', key=abs, ascending=False).iterrows():
            arrow = '↑' if r['cliff_delta'] > 0 else '↓'
            log_section('5', f'  {arrow} {r["metabolite_name"]:<45s}  cliff={r["cliff_delta"]:+.3f}  FDR={r["fdr"]:.2e}  ({r["method"]})')


# ---------------------------------------------------------------------------
# §6. Verdict
# ---------------------------------------------------------------------------
log_section('6', '## §6. H3d-DA verdict + figure')

# Recompute pass counts directly from res_df to avoid stale-scalar bug
n_pass_final = int(res_df['passes'].sum())
n_cd_up_final = int(((res_df['passes']) & (res_df['cliff_delta'] > 0)).sum())
n_cd_down_final = int(((res_df['passes']) & (res_df['cliff_delta'] < 0)).sum())

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'H3d-DA — HMP2 metabolomics CD-vs-nonIBD per-metabolite differential abundance',
    'n_subjects_cd': len(cd_subjects),
    'n_subjects_nonibd': len(nonibd_subjects),
    'n_metabolites_named_tested': len(res_df),
    'n_metabolites_passing_FDR10_cliff20': n_pass_final,
    'n_cd_up': n_cd_up_final,
    'n_cd_down': n_cd_down_final,
    'themes_supported_count': int(theme_df['supported'].sum()),
    'themes_supported': theme_df.loc[theme_df['supported'], ['theme', 'direction', 'odds_ratio', 'fdr']].to_dict(orient='records'),
}

# Headline narrative
if n_pass_final >= 50 and theme_df['supported'].any():
    verdict['h3d_da_verdict'] = 'SUPPORTED'
elif n_pass_final >= 10 and theme_df['supported'].any():
    verdict['h3d_da_verdict'] = 'PARTIAL'
elif n_pass_final >= 10:
    verdict['h3d_da_verdict'] = 'PARTIAL — DA passes but no theme-level enrichment'
else:
    verdict['h3d_da_verdict'] = 'NOT SUPPORTED'

with open(f'{OUT_DATA}/nb09a_h3d_da_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('6', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §7. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: volcano-style scatter (cliff_delta vs -log10(FDR))
ax = axes[0]
res_plot = res_df.dropna(subset=['cliff_delta', 'fdr']).copy()
res_plot['neglog_fdr'] = -np.log10(res_plot['fdr'].clip(lower=1e-30))
colors = []
for _, r in res_plot.iterrows():
    if r['passes']:
        colors.append('#e63946' if r['cliff_delta'] > 0 else '#3a86ff')
    else:
        colors.append('#cccccc')
ax.scatter(res_plot['cliff_delta'], res_plot['neglog_fdr'], c=colors, s=12, alpha=0.7)
ax.axhline(-np.log10(0.10), color='gray', linestyle=':', linewidth=0.5)
ax.axvline(0.2, color='gray', linestyle=':', linewidth=0.5)
ax.axvline(-0.2, color='gray', linestyle=':', linewidth=0.5)
ax.set_xlabel('Cliff\'s δ (CD vs nonIBD)')
ax.set_ylabel('-log10(FDR)')
ax.set_title(f'A. Volcano: {n_cd_up} CD-up + {n_cd_down} CD-down (FDR<0.10, |δ|>0.2)')

# Annotate key metabolites
key_metabs = ['lactate', 'butyrate', 'acetate', 'taurocholate', 'lithocholate', 'deoxycholate',
              'trimethylamine-N-oxide', 'choline', 'tryptophan', 'indole-3-propionate',
              'palmitoylethanolamide']
for kw in key_metabs:
    sub = res_plot[res_plot['metabolite_name'].astype(str).str.lower() == kw.lower()]
    if len(sub):
        for _, r in sub.iterrows():
            ax.annotate(kw, (r['cliff_delta'], r['neglog_fdr']),
                        fontsize=7, alpha=0.8, xytext=(2, 2), textcoords='offset points')

# Panel B: theme enrichment OR
ax = axes[1]
theme_plot = theme_df.copy()
theme_plot = theme_plot.sort_values(['direction', 'odds_ratio'])
y = np.arange(len(theme_plot))
labels = [f'{t}\n({d})' for t, d in zip(theme_plot['theme'], theme_plot['direction'])]
colors = ['#e63946' if r['supported'] and r['direction'] == 'CD-up' else
          '#3a86ff' if r['supported'] and r['direction'] == 'CD-down' else
          '#a8a8a8' for _, r in theme_plot.iterrows()]
ax.barh(y, np.log2(np.maximum(theme_plot['odds_ratio'], 0.001)), color=colors)
ax.axvline(0, color='black', linewidth=0.5)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel('log2(OR)')
ax.set_title('B. Theme enrichment (CD-up & CD-down)')
for i, r in enumerate(theme_plot.itertuples()):
    ax.text(np.log2(max(r.odds_ratio, 0.001)) + 0.05, i, f'OR={r.odds_ratio:.1f}, FDR={r.fdr:.2g}', va='center', fontsize=7)

# Panel C: top CD-up + CD-down metabolites bar
ax = axes[2]
top_n = 15
top_pass = pd.concat([
    res_df[res_df['passes']].nlargest(top_n, 'cliff_delta'),
    res_df[res_df['passes']].nsmallest(top_n, 'cliff_delta')
]).sort_values('cliff_delta')
y = np.arange(len(top_pass))
colors = ['#e63946' if c > 0 else '#3a86ff' for c in top_pass['cliff_delta']]
ax.barh(y, top_pass['cliff_delta'], color=colors)
ax.set_yticks(y)
ax.set_yticklabels(top_pass['metabolite_name'].astype(str).str[:35], fontsize=7)
ax.axvline(0, color='black', linewidth=0.5)
ax.set_xlabel('Cliff\'s δ (CD vs nonIBD)')
ax.set_title(f'C. Top {top_n} CD-up + Top {top_n} CD-down')

fig.suptitle(f'NB09a — HMP2 metabolomics CD-vs-nonIBD H3d-DA: {verdict["h3d_da_verdict"]}', fontsize=12, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB09a_metabolomics_cd_vs_nonibd.png', dpi=120, bbox_inches='tight')
log_section('6', f'\nWrote {OUT_FIG}/NB09a_metabolomics_cd_vs_nonibd.png')

with open('/tmp/nb09a_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone. Wrote /tmp/nb09a_section_logs.json + 3 data files + 1 figure.')
