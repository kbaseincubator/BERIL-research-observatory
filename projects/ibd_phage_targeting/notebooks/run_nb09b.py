"""NB09b — Cross-cohort metabolomics bridge.

Test whether NB09a §12 polyamine + PUFA + tauro-BA + acyl-carnitine signatures
replicate in FRANZOSA_2019 (220 participants × CD/UC/Control). Match HMP2 named
metabolites to Franzosa peaks by m/z within method (±0.005 Da tolerance);
recompute Franzosa CD-vs-Control DA at participant level and report
cross-cohort sign-concordance per metabolite + per theme.

DAVE_SAMP_METABOLOMICS dropped from this analysis: 30 samples, mouse ileal
tissue (AKR/J model) — not human IBD CD-vs-HC replication target.

Per plan v1.9 no raw reads.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJ = '/home/aparkin/BERIL-research-observatory-ibd/projects/ibd_phage_targeting'
MART = '/home/aparkin/data/CrohnsPhage'
OUT_DATA = f'{PROJ}/data'
OUT_FIG = f'{PROJ}/figures'
SECTION_LOGS = {}


def log_section(key, msg):
    SECTION_LOGS.setdefault(key, '')
    SECTION_LOGS[key] += msg + '\n'
    print(msg)


# ---------------------------------------------------------------------------
# §0. Load HMP2 annotations + Franzosa metabolomics + sample/participant meta
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load Franzosa + HMP2 named annotations + sample / participant metadata')

m = pd.read_parquet(f'{MART}/fact_metabolomics.snappy.parquet')
franz = m[m['study_id'] == 'FRANZOSA_2019'].copy()
log_section('0', f'Franzosa metabolomics: {franz.shape[0]} rows × {franz["sample_id"].nunique()} samples × {franz["metabolite_id"].nunique()} metabolites')

ann = pd.read_parquet(f'{MART}/ref_hmp2_metabolite_annotations.snappy.parquet')
ann_named = ann[ann['metabolite_name'].notna() & (ann['metabolite_name'].astype(str).str.strip() != '')].copy()
ann_named['mz'] = pd.to_numeric(ann_named['mz'], errors='coerce')
ann_named['rt'] = pd.to_numeric(ann_named['rt'], errors='coerce')
log_section('0', f'HMP2 named annotations: {len(ann_named)} (with m/z + RT)')

# Parse Franzosa metabolite_id format "[mz]_[rt]"
def parse_id(s):
    parts = s.split('_')
    if len(parts) == 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return np.nan, np.nan
    return np.nan, np.nan


franz_ids = franz[['metabolite_id', 'method']].drop_duplicates().copy()
franz_ids[['mz', 'rt']] = franz_ids['metabolite_id'].apply(lambda s: pd.Series(parse_id(s)))
log_section('0', f'Franzosa parsed metabolite IDs: {franz_ids["mz"].notna().sum()} of {len(franz_ids)}')

# Sample-level CD/UC/Control labels via dim_samples + dim_participants
ds = pd.read_parquet(f'{MART}/dim_samples.snappy.parquet')
dp = pd.read_parquet(f'{MART}/dim_participants.snappy.parquet')
ds_franz = ds[ds['study_id'] == 'FRANZOSA_2019'][['sample_id', 'participant_id']].copy()
dp_franz = dp[dp['study_id'] == 'FRANZOSA_2019'][['participant_id', 'diagnosis']].copy()
sample_meta = ds_franz.merge(dp_franz, on='participant_id', how='left')
log_section('0', f'\nFranzosa samples × participant × diagnosis: {sample_meta.shape}')
log_section('0', f'  Diagnosis: {sample_meta["diagnosis"].value_counts(dropna=False).to_dict()}')

# Subject-level: 1 sample per participant (first; if multiple, mean)
log_section('0', f'  Distinct participants: {sample_meta["participant_id"].nunique()}')


# ---------------------------------------------------------------------------
# §1. Match HMP2 named metabolites to Franzosa peaks by m/z (within method)
# ---------------------------------------------------------------------------
log_section('1', '## §1. Match HMP2 named metabolites to Franzosa peaks by m/z (±0.005 Da, same method)')

MZ_TOL = 0.005
matched_rows = []
for _, h in ann_named.iterrows():
    f_method = franz_ids[franz_ids['method'] == h['method']]
    if len(f_method) == 0 or pd.isna(h['mz']):
        continue
    dmz = (f_method['mz'] - h['mz']).abs()
    cand = f_method[dmz < MZ_TOL]
    if not len(cand):
        continue
    cand = cand.copy()
    cand['dmz'] = (cand['mz'] - h['mz'])
    best = cand.iloc[(cand['dmz'].abs()).argsort()].iloc[0]
    matched_rows.append({
        'hmp2_metabolite_id': h['metabolite_id'],
        'metabolite_name': h['metabolite_name'],
        'method': h['method'],
        'hmdb_id': h['hmdb_id'],
        'franz_metabolite_id': best['metabolite_id'],
        'n_franz_candidates_at_mz': int(len(cand)),
        'dmz': float(best['dmz']),
    })

mat = pd.DataFrame(matched_rows)
log_section('1', f'Matched HMP2-named -> Franzosa peaks: {len(mat)} (out of {len(ann_named)} named)')
log_section('1', f'  unique HMP2 metabolites: {mat["hmp2_metabolite_id"].nunique()}')
log_section('1', f'  unique Franzosa peaks (after dedup): {mat["franz_metabolite_id"].nunique()}')


# ---------------------------------------------------------------------------
# §2. Build Franzosa participant × metabolite matrix; compute CD-vs-Control DA
# ---------------------------------------------------------------------------
log_section('2', '## §2. Franzosa CD-vs-Control DA on the matched-to-HMP2-named subset')

# Filter Franzosa to matched IDs; aggregate per (participant, metabolite_id) by mean
matched_franz_ids = set(mat['franz_metabolite_id'])
franz_sub = franz[franz['metabolite_id'].isin(matched_franz_ids)].copy()
franz_sub = franz_sub.merge(sample_meta[['sample_id', 'participant_id', 'diagnosis']], on='sample_id', how='inner')
log_section('2', f'Franzosa rows on matched metabolites: {franz_sub.shape[0]}')
log_section('2', f'  participants with measurements: {franz_sub["participant_id"].nunique()}')
log_section('2', f'  diagnosis distribution: {franz_sub.drop_duplicates(subset="participant_id")["diagnosis"].value_counts().to_dict()}')

# log10 + 0.01
franz_sub['log_int'] = np.log10(franz_sub['intensity'].clip(lower=0.01))

# Aggregate to (participant, metabolite_id) — mean log intensity (in case of multiple visits)
agg = franz_sub.groupby(['participant_id', 'metabolite_id', 'diagnosis'], as_index=False)['log_int'].mean()

# Pivot to (participant, diagnosis) × metabolite_id
mat_franz = agg.pivot_table(index=['participant_id', 'diagnosis'], columns='metabolite_id', values='log_int', aggfunc='mean')
mat_franz = mat_franz.reset_index()
log_section('2', f'\nFranzosa participant × matched-metabolite matrix: {mat_franz.shape}')

# CD-vs-Control DA per matched metabolite
metab_cols = [c for c in mat_franz.columns if c not in ('participant_id', 'diagnosis')]
cd_mask = mat_franz['diagnosis'] == 'CD'
hc_mask = mat_franz['diagnosis'] == 'Control'
log_section('2', f'  n_CD={cd_mask.sum()}; n_Control={hc_mask.sum()}')

results = []
for c in metab_cols:
    cd_vals = mat_franz.loc[cd_mask, c].dropna().values
    hc_vals = mat_franz.loc[hc_mask, c].dropna().values
    if len(cd_vals) < 10 or len(hc_vals) < 10:
        continue
    u, p = stats.mannwhitneyu(cd_vals, hc_vals, alternative='two-sided')
    n1, n2 = len(cd_vals), len(hc_vals)
    cliff = 2 * u / (n1 * n2) - 1
    results.append({
        'franz_metabolite_id': c,
        'n_cd': n1,
        'n_hc': n2,
        'median_cd': round(float(np.median(cd_vals)), 3),
        'median_hc': round(float(np.median(hc_vals)), 3),
        'cliff_delta_franz': round(float(cliff), 3),
        'mw_p_franz': float(p),
    })

franz_da = pd.DataFrame(results)
# BH-FDR
m_n = len(franz_da)
order = franz_da['mw_p_franz'].argsort().values
ranked = franz_da['mw_p_franz'].iloc[order].values
fdr_adj = np.minimum.accumulate((ranked[::-1] * m_n / np.arange(m_n, 0, -1)))[::-1]
fdr_arr = np.empty(m_n)
for i, idx in enumerate(order):
    fdr_arr[idx] = fdr_adj[i]
franz_da['fdr_franz'] = fdr_arr
log_section('2', f'\nFranzosa CD-vs-Control DA on matched panel: {len(franz_da)} testable')
log_section('2', f'  passing FDR<0.10 + |cliff|>0.20: {((franz_da["fdr_franz"]<0.10) & (franz_da["cliff_delta_franz"].abs()>0.20)).sum()}')


# ---------------------------------------------------------------------------
# §3. Cross-cohort sign-concordance with NB09a HMP2 result
# ---------------------------------------------------------------------------
log_section('3', '## §3. Cross-cohort sign-concordance: HMP2 NB09a vs Franzosa NB09b')

hmp2_da = pd.read_csv(f'{OUT_DATA}/nb09a_metab_da_cd_vs_nonibd.tsv', sep='\t')

merged = mat.merge(hmp2_da[['metabolite_id', 'cliff_delta', 'fdr', 'passes', 'metabolite_name']],
                    left_on='hmp2_metabolite_id', right_on='metabolite_id', how='left',
                    suffixes=('', '_hmp2dup'))
merged = merged.rename(columns={'cliff_delta': 'cliff_delta_hmp2', 'fdr': 'fdr_hmp2', 'passes': 'passes_hmp2'})
merged = merged.drop(columns=['metabolite_id', 'metabolite_name_hmp2dup'], errors='ignore')

# Join with Franzosa DA
merged = merged.merge(franz_da, on='franz_metabolite_id', how='left')

# Sign concordance
merged['sign_match'] = np.sign(merged['cliff_delta_hmp2']) == np.sign(merged['cliff_delta_franz'])
merged['both_significant'] = (merged['fdr_hmp2'] < 0.10) & (merged['fdr_franz'] < 0.10)

n_pairs_with_franz = merged['cliff_delta_franz'].notna().sum()
n_sign_match = merged['sign_match'].sum()
log_section('3', f'\nMatched pairs with Franzosa DA: {n_pairs_with_franz}')
log_section('3', f'  Sign-concordant (HMP2 cliff and Franzosa cliff same sign): {n_sign_match} ({100*n_sign_match/max(n_pairs_with_franz,1):.0f}%)')

# Top concordant CD-up pairs
log_section('3', f'\nTop CD-up sign-concordant matches (HMP2 cliff > 0 AND Franzosa cliff > 0, sorted by min cliff):')
cd_up_concord = merged[(merged['cliff_delta_hmp2'] > 0) & (merged['cliff_delta_franz'] > 0)].copy()
cd_up_concord['min_cliff'] = cd_up_concord[['cliff_delta_hmp2', 'cliff_delta_franz']].min(axis=1)
cd_up_concord = cd_up_concord.sort_values('min_cliff', ascending=False)
log_section('3', cd_up_concord[['metabolite_name', 'method', 'cliff_delta_hmp2', 'cliff_delta_franz', 'fdr_hmp2', 'fdr_franz']].head(20).to_string(index=False))

# Top concordant CD-down pairs
log_section('3', f'\nTop CD-down sign-concordant matches (HMP2 cliff < 0 AND Franzosa cliff < 0):')
cd_dn_concord = merged[(merged['cliff_delta_hmp2'] < 0) & (merged['cliff_delta_franz'] < 0)].sort_values('cliff_delta_hmp2')
log_section('3', cd_dn_concord[['metabolite_name', 'method', 'cliff_delta_hmp2', 'cliff_delta_franz', 'fdr_hmp2', 'fdr_franz']].head(10).to_string(index=False))

merged.to_csv(f'{OUT_DATA}/nb09b_cross_cohort_concordance.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §4. Theme-level cross-cohort replication
# ---------------------------------------------------------------------------
log_section('4', '## §4. Theme-level cross-cohort replication (curated panels)')

# Use the same theme keywords as NB09a §3
THEMES = {
    'polyamines': ['putrescine', 'spermine', 'spermidine', 'cadaverine', 'agmatine', 'acetylspermine', 'acetylputrescine', 'anserine', 'carnosine'],
    'long_chain_PUFA': ['arachidonate', 'adrenate', 'docosapentaenoate', 'docosahexaenoa', 'eicosapentaenoa', 'linoleate', 'oleate', 'linolenate', 'stearate', 'palmitate'],
    'bile_acids_primary': ['cholate', 'tauro', 'glyco', 'taurine', 'muricholate'],
    'bile_acids_secondary': ['lithocholate', 'deoxycholate', 'ketodeoxycholate'],
    'tma_choline': ['choline', 'trimethylamine', 'TMAO', 'betaine', 'phosphochol', 'glycerophosphochol'],
    'acyl_carnitines': ['carnitine'],
    'lipid_classes': [' CE', ' SM', ' TAG', ' DAG', 'ceramide', 'sphingomyelin', 'cholesteryl', 'phosphatidyl'],
    'urobilin_porphyrin': ['urobilin', 'bilirubin'],
    'tryptophan_indole': ['tryptophan', 'indole', 'kynureni'],
    'aromatic_AA_metabolites': ['phenylacet', 'tyrosine', 'phenyllactate', 'p-cresol', 'p-hydroxyphenyl'],
}


def assign_theme(name):
    if pd.isna(name):
        return []
    nl = str(name).lower()
    found = []
    for theme, kws in THEMES.items():
        if any(kw.lower() in nl for kw in kws):
            found.append(theme)
    return found


merged['themes'] = merged['metabolite_name'].apply(assign_theme)

theme_rows = []
for theme in THEMES:
    in_theme = merged[merged['themes'].apply(lambda x: theme in x)]
    in_theme_with_franz = in_theme[in_theme['cliff_delta_franz'].notna()]
    if len(in_theme_with_franz) == 0:
        continue
    n_total = len(in_theme_with_franz)
    n_cd_up_hmp2 = (in_theme_with_franz['cliff_delta_hmp2'] > 0).sum()
    n_cd_up_franz = (in_theme_with_franz['cliff_delta_franz'] > 0).sum()
    n_concord = in_theme_with_franz['sign_match'].sum()
    median_franz_cliff = float(in_theme_with_franz['cliff_delta_franz'].median())
    theme_rows.append({
        'theme': theme,
        'n_matched_in_theme': int(n_total),
        'n_CD_up_HMP2': int(n_cd_up_hmp2),
        'n_CD_up_Franz': int(n_cd_up_franz),
        'n_sign_concord': int(n_concord),
        'pct_sign_concord': round(100*n_concord/n_total, 1),
        'median_franz_cliff': round(median_franz_cliff, 3),
    })

theme_df = pd.DataFrame(theme_rows).sort_values('pct_sign_concord', ascending=False)
log_section('4', f'\nPer-theme cross-cohort replication:\n')
log_section('4', theme_df.to_string(index=False))
theme_df.to_csv(f'{OUT_DATA}/nb09b_theme_replication.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. Cross-cohort replication verdict')

# Strict replication: a metabolite "replicates" if both HMP2 and Franzosa have FDR<0.10 AND same sign AND |cliff|>0.20
strict_replications = merged[(merged['fdr_hmp2'] < 0.10) & (merged['fdr_franz'] < 0.10) &
                              (merged['cliff_delta_hmp2'].abs() > 0.20) & (merged['cliff_delta_franz'].abs() > 0.20) &
                              merged['sign_match']].copy()
log_section('5', f'\nStrict replications (both FDR<0.10 + |cliff|>0.20 + sign-match): {len(strict_replications)}')
if len(strict_replications):
    log_section('5', strict_replications[['metabolite_name', 'method', 'cliff_delta_hmp2', 'cliff_delta_franz', 'fdr_hmp2', 'fdr_franz']].to_string(index=False))

# Sign-concordance only (loose replication)
sign_concord_relaxed = merged[merged['cliff_delta_franz'].notna() & merged['sign_match']]
total_with_franz = merged['cliff_delta_franz'].notna().sum()
log_section('5', f'\nSign-concordance (loose): {len(sign_concord_relaxed)} of {total_with_franz} ({100*len(sign_concord_relaxed)/max(total_with_franz,1):.0f}%)')

# Theme-level replication: which themes have ≥75% sign concordance?
themes_replicating = theme_df[theme_df['pct_sign_concord'] >= 75]
log_section('5', f'\nThemes with ≥75% sign concordance:\n')
log_section('5', themes_replicating.to_string(index=False))

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB09b — cross-cohort metabolomics bridge HMP2 (NB09a) → FRANZOSA_2019',
    'n_HMP2_named_metabolites': len(ann_named),
    'n_matched_to_franzosa_by_mz': len(mat),
    'n_with_franzosa_DA': int(total_with_franz),
    'n_strict_replications': int(len(strict_replications)),
    'pct_sign_concordance_overall': round(100*len(sign_concord_relaxed)/max(total_with_franz,1), 1),
    'themes_replicating_above_75pct': themes_replicating['theme'].tolist(),
    'theme_replication_summary': theme_df.to_dict(orient='records'),
    'franzosa_n_cd': int(cd_mask.sum()),
    'franzosa_n_hc': int(hc_mask.sum()),
}
verdict['narrative'] = (
    f'Cross-cohort sign-concordance overall is {verdict["pct_sign_concordance_overall"]:.0f}%, '
    f'with {len(themes_replicating)} of {len(theme_df)} themes ≥75% concordant. '
    f'Strict replications (both FDR<0.10 + |cliff|>0.20): {len(strict_replications)}.'
)

with open(f'{OUT_DATA}/nb09b_cross_cohort_verdict.json', 'w') as fp_out:
    json.dump(verdict, fp_out, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Panel A: cross-cohort cliff_delta scatter (HMP2 vs Franzosa)
ax = axes[0]
plot_df = merged.dropna(subset=['cliff_delta_hmp2', 'cliff_delta_franz']).copy()

# Color by theme membership
plot_df['theme_color'] = '#a8a8a8'
theme_colors = {
    'polyamines': '#e63946', 'long_chain_PUFA': '#f4a261',
    'bile_acids_primary': '#264653', 'bile_acids_secondary': '#2a9d8f',
    'lipid_classes': '#8a4f7d', 'acyl_carnitines': '#e9c46a',
    'urobilin_porphyrin': '#1d3557',
}
for theme, color in theme_colors.items():
    mask = plot_df['themes'].apply(lambda x: theme in x)
    plot_df.loc[mask, 'theme_color'] = color

ax.scatter(plot_df['cliff_delta_hmp2'], plot_df['cliff_delta_franz'],
           c=plot_df['theme_color'], s=30, alpha=0.7, edgecolors='black', linewidth=0.3)
ax.axhline(0, color='gray', linewidth=0.5, linestyle=':')
ax.axvline(0, color='gray', linewidth=0.5, linestyle=':')
# Diagonal
ax.plot([-1, 1], [-1, 1], 'k--', linewidth=0.5, alpha=0.3)
ax.set_xlabel('HMP2 cliff δ (NB09a, CD vs nonIBD)')
ax.set_ylabel('Franzosa cliff δ (NB09b, CD vs Control)')
ax.set_title(f'A. Cross-cohort cliff δ ({len(plot_df)} matched metabolites; {100*len(sign_concord_relaxed)/max(total_with_franz,1):.0f}% sign-concord)')

# Annotate key metabolites
for _, r in plot_df.iterrows():
    nm = str(r['metabolite_name'])
    nm_low = nm.lower()
    if any(kw in nm_low for kw in ['arachidon', 'adren', 'docosa', 'eicos', 'urobilin',
                                    'litho', 'deoxychol', 'cheno', 'ketodeoxy', 'taurine']):
        ax.annotate(nm[:25], (r['cliff_delta_hmp2'], r['cliff_delta_franz']),
                    fontsize=6, alpha=0.75, xytext=(2, 2), textcoords='offset points')

# Legend
from matplotlib.patches import Patch
legend_elems = [Patch(facecolor=color, label=theme) for theme, color in theme_colors.items()]
legend_elems.append(Patch(facecolor='#a8a8a8', label='other / unclassified'))
ax.legend(handles=legend_elems, loc='lower right', fontsize=6)

# Panel B: per-theme sign-concordance bar
ax = axes[1]
theme_plot = theme_df.copy()
theme_plot = theme_plot.sort_values('pct_sign_concord', ascending=True)
y = np.arange(len(theme_plot))
colors = ['#2a9d8f' if v >= 75 else '#e9c46a' if v >= 50 else '#e63946' for v in theme_plot['pct_sign_concord']]
ax.barh(y, theme_plot['pct_sign_concord'], color=colors)
ax.axvline(50, color='gray', linewidth=0.5, linestyle=':')
ax.axvline(75, color='gray', linewidth=0.5, linestyle=':')
labels = [f'{r["theme"]} (n={r["n_matched_in_theme"]})' for _, r in theme_plot.iterrows()]
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel('% sign-concordant (HMP2 cliff sign matches Franzosa cliff sign)')
ax.set_title('B. Per-theme cross-cohort sign-concordance')
for i, r in enumerate(theme_plot.itertuples()):
    ax.text(r.pct_sign_concord + 1, i, f'{r.n_sign_concord}/{r.n_matched_in_theme}', va='center', fontsize=7)

fig.suptitle(f'NB09b — Cross-cohort replication: HMP2 NB09a → Franzosa 2019', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB09b_cross_cohort_metabolomics.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB09b_cross_cohort_metabolomics.png')

with open('/tmp/nb09b_section_logs.json', 'w') as fp_out:
    json.dump(SECTION_LOGS, fp_out, indent=2)
print(f'\nDone.')
