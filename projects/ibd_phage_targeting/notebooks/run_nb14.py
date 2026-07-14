"""NB14 — HMP2 endogenous phageome × ecotype × diagnosis stratification.

Per-ecotype phage community structure on HMP2 viromics samples (630
viromics × ecotype overlap). Tests whether the in-vivo phageome stratifies
across the 4-ecotype framework + within-ecotype CD-vs-nonIBD signal.

Tests:
1. Per-ecotype phage-family distribution (which families dominate each ecotype?)
2. Per-ecotype CD-vs-nonIBD virus DA (Mann-Whitney CD vs healthy per virus)
3. Cross-reference ref_viromics_cd_vs_nonibd precomputed (22 viruses)
4. Cross-correlation: do CD-up phage families correlate with Tier-A pathobiont
   abundance per sample? (looking for endogenous phage candidates)
5. Coverage check: are there observed phages of Tier-A core species in HMP2?

Per plan v1.9 no raw reads.
"""
import json
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
# §0. Load HMP2 viromics + NB04h ecotype projections + ref tables
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load HMP2 viromics + NB04h ecotype projections')

fv = pd.read_parquet(f'{MART}/fact_viromics.snappy.parquet')
fv['code'] = fv['sample_id'].str.replace('HMP2:', '', regex=False)
log_section('0', f'fact_viromics: {fv.shape[0]} rows × {fv["sample_id"].nunique()} samples × {fv["virus_name"].nunique()} viruses')

nb04h = pd.read_csv(f'{OUT_DATA}/nb04h_hmp2_ecotype_projection.tsv', sep='\t')
nb04h['code'] = nb04h['sample_id'].str.replace('_P$', '', regex=True)
log_section('0', f'NB04h ecotype projections: {nb04h.shape[0]} samples × {nb04h["subject_id"].nunique()} subjects')

# Overlap
fv_codes = set(fv['code'].unique())
nb04h_codes = set(nb04h['code'].unique())
overlap = fv_codes & nb04h_codes
log_section('0', f'\nSample overlap (viromics ∩ ecotype): {len(overlap)} of {len(fv_codes)} viromics samples')

# Annotate viromics with ecotype + diagnosis
nb04h_meta = nb04h[nb04h['code'].isin(overlap)][['code', 'subject_id', 'disease', 'disease_subtype', 'ecotype', 'max_posterior']].drop_duplicates(subset='code')
fv_eco = fv.merge(nb04h_meta, on='code', how='inner')
log_section('0', f'\nfact_viromics × ecotype merged: {fv_eco.shape[0]} rows')
log_section('0', f'\nUnique sample × ecotype × diagnosis cells:')
sample_eco_dx = fv_eco.drop_duplicates(subset='code')[['ecotype', 'disease_subtype', 'disease']].copy()
sample_eco_dx['dx_clean'] = sample_eco_dx['disease_subtype'].fillna(sample_eco_dx['disease'])
log_section('0', sample_eco_dx.groupby(['ecotype', 'dx_clean']).size().unstack(fill_value=0).to_string())

# Pre-computed CD-vs-nonIBD virus DA
ref_cd_v = pd.read_parquet(f'{MART}/ref_viromics_cd_vs_nonibd.snappy.parquet')
log_section('0', f'\nref_viromics_cd_vs_nonibd: {ref_cd_v.shape[0]} pre-computed virus CD-vs-nonIBD DA results')
ref_summary = pd.read_parquet(f'{MART}/ref_viromics_summary_by_disease.snappy.parquet')
log_section('0', f'ref_viromics_summary_by_disease: {ref_summary.shape[0]} per-virus per-diagnosis prevalence + abundance')


# ---------------------------------------------------------------------------
# §1. Per-ecotype phage-family distribution
# ---------------------------------------------------------------------------
log_section('1', '## §1. Per-ecotype phage-family distribution')

# Parse phage_family from virus_taxon (lineage) — pull out f__ token
def extract_family(taxon):
    if pd.isna(taxon):
        return 'Unknown'
    parts = taxon.split('|')
    for p in parts:
        if p.startswith('f__'):
            f = p.replace('f__', '').strip()
            if f and f != 'noname' and 'noname' not in f:
                return f
    return 'Unknown'


fv_eco['phage_family'] = fv_eco['virus_taxon'].apply(extract_family)
log_section('1', f'\nUnique phage families: {fv_eco["phage_family"].nunique()}')
log_section('1', f'Top 10 families by total observations:\n{fv_eco["phage_family"].value_counts().head(10).to_string()}')

# Per-ecotype family abundance
log_section('1', '\nMean abundance × ecotype × phage family (top 8 families):')
top_families = fv_eco['phage_family'].value_counts().head(8).index.tolist()
fam_eco = fv_eco[fv_eco['phage_family'].isin(top_families)].copy()
fam_eco_pivot = fam_eco.groupby(['ecotype', 'phage_family'])['abundance'].mean().unstack(fill_value=0)
log_section('1', fam_eco_pivot.round(3).to_string())


# ---------------------------------------------------------------------------
# §2. Per-ecotype × per-virus CD-vs-nonIBD DA
# ---------------------------------------------------------------------------
log_section('2', '## §2. Per-virus CD-vs-nonIBD Mann-Whitney within-ecotype meta')

# Aggregate to (sample, virus) → mean abundance; then per virus per ecotype, MW CD vs healthy
# Pre-fill diagnosis to handle NaN-drop in groupby:
fv_eco['disease_subtype_filled'] = fv_eco['disease_subtype'].fillna('NA')
sample_virus = fv_eco.groupby(['code', 'virus_name', 'ecotype', 'disease_subtype_filled', 'disease'])['abundance'].sum().reset_index()
sample_virus['dx'] = np.where(sample_virus['disease_subtype_filled'] == 'CD', 'CD',
                     np.where(sample_virus['disease_subtype_filled'] == 'UC', 'UC',
                     np.where(sample_virus['disease'] == 'healthy', 'nonIBD', 'IBD_unspec')))

# CD vs nonIBD per virus per ecotype (only ecotypes with ≥5 CD + ≥5 nonIBD)
da_rows = []
for eco in [0, 1, 2, 3]:
    eco_samples = sample_virus[sample_virus['ecotype'] == eco]
    cd_samples = set(eco_samples[eco_samples['dx'] == 'CD']['code'])
    hc_samples = set(eco_samples[eco_samples['dx'] == 'nonIBD']['code'])
    if len(cd_samples) < 5 or len(hc_samples) < 5:
        log_section('2', f'\nEcotype {eco}: n_CD={len(cd_samples)}, n_HC={len(hc_samples)} — insufficient power, skipping')
        continue
    log_section('2', f'\n=== Ecotype {eco}: n_CD={len(cd_samples)}, n_HC={len(hc_samples)} ===')

    # Per-virus DA
    for virus in eco_samples['virus_name'].unique():
        v_data = eco_samples[eco_samples['virus_name'] == virus]
        v_dict = dict(zip(v_data['code'], v_data['abundance']))
        cd_vals = [v_dict.get(s, 0) for s in cd_samples]
        hc_vals = [v_dict.get(s, 0) for s in hc_samples]
        # Need ≥3 nonzero in each group for testing
        cd_nonzero = sum(1 for v in cd_vals if v > 0)
        hc_nonzero = sum(1 for v in hc_vals if v > 0)
        if cd_nonzero < 3 and hc_nonzero < 3:
            continue
        try:
            u, p = stats.mannwhitneyu(cd_vals, hc_vals, alternative='two-sided')
            n1, n2 = len(cd_vals), len(hc_vals)
            cliff = 2 * u / (n1 * n2) - 1
            da_rows.append({
                'ecotype': eco,
                'virus_name': virus,
                'n_cd': n1, 'n_hc': n2,
                'cd_nonzero_count': cd_nonzero,
                'hc_nonzero_count': hc_nonzero,
                'mean_cd': float(np.mean(cd_vals)),
                'mean_hc': float(np.mean(hc_vals)),
                'cliff_delta': round(float(cliff), 3),
                'mw_p': float(p),
            })
        except Exception:
            continue

da_df = pd.DataFrame(da_rows)
log_section('2', f'\nTotal DA tests: {len(da_df)}')

# BH-FDR per ecotype
def bh_fdr(p_arr):
    p_arr = np.array(p_arr)
    n = len(p_arr)
    order = np.argsort(p_arr)
    ranked = p_arr[order]
    fdr = np.minimum.accumulate((ranked[::-1] * n / np.arange(n, 0, -1)))[::-1]
    out = np.empty(n)
    out[order] = fdr
    return out


for eco in da_df['ecotype'].unique():
    mask = da_df['ecotype'] == eco
    da_df.loc[mask, 'fdr_within_eco'] = bh_fdr(da_df.loc[mask, 'mw_p'].values)

da_df = da_df.sort_values(['ecotype', 'fdr_within_eco'])
da_df.to_csv(f'{OUT_DATA}/nb14_viromics_da_per_ecotype.tsv', sep='\t', index=False)

# Top viruses per ecotype
log_section('2', f'\nTop CD-up viruses per ecotype (FDR<0.10):')
for eco in sorted(da_df['ecotype'].unique()):
    sub = da_df[(da_df['ecotype'] == eco) & (da_df['fdr_within_eco'] < 0.10) & (da_df['cliff_delta'] > 0)]
    log_section('2', f'\n  Ecotype {eco}: {len(sub)} CD-up viruses passing FDR<0.10')
    log_section('2', sub.head(10)[['virus_name', 'cliff_delta', 'mean_cd', 'mean_hc', 'fdr_within_eco']].to_string(index=False))


# ---------------------------------------------------------------------------
# §3. Cross-reference precomputed ref_viromics_cd_vs_nonibd
# ---------------------------------------------------------------------------
log_section('3', '## §3. Cross-reference ref_viromics_cd_vs_nonibd (22 precomputed viruses)')

log_section('3', f'\nref_viromics_cd_vs_nonibd top 10 by FDR:')
log_section('3', ref_cd_v.sort_values('fdr').head(10)[['virus', 'log2fc_cd_vs_nonibd', 'mannwhitney_pval', 'fdr']].to_string(index=False))

# Direction: log2fc < 0 means CD-DOWN
n_cd_up_ref = (ref_cd_v['log2fc_cd_vs_nonibd'] > 0).sum()
n_cd_down_ref = (ref_cd_v['log2fc_cd_vs_nonibd'] < 0).sum()
log_section('3', f'\nref_viromics: {n_cd_up_ref} CD-up + {n_cd_down_ref} CD-down at log2fc != 0')


# ---------------------------------------------------------------------------
# §4. Cross-correlation: phage families × Tier-A pathobiont abundance
# ---------------------------------------------------------------------------
log_section('4', '## §4. Phage family × Tier-A pathobiont abundance correlation (within HMP2)')

# Build sample × phage-family abundance matrix
fam_abund = fv_eco.groupby(['code', 'phage_family'])['abundance'].sum().reset_index()
fam_mat = fam_abund.pivot(index='code', columns='phage_family', values='abundance').fillna(0)
fam_mat_log = np.log10(fam_mat + 0.001)
log_section('4', f'Sample × phage-family matrix: {fam_mat.shape}')

# Load HMP2 MetaPhlAn3 species abundance for Tier-A core
ra = pd.read_csv(f'{EXT}/hmp2_ibdmdb_relative_abundance.tsv', sep='\t', index_col=0)
ra.index = ra.index.str.replace('species:', '', regex=False)
ra.columns = ra.columns.str.replace('_P$', '', regex=True)
ra = ra.loc[:, ~ra.columns.duplicated(keep='first')]

tier_a_species = {
    'H. hathewayi': 'Hungatella hathewayi',
    'M. gnavus': '[Ruminococcus] gnavus',
    'E. coli': 'Escherichia coli',
    'E. lenta': 'Eggerthella lenta',
    'F. plautii': 'Flavonifractor plautii',
    'E. bolteae': 'Enterocloster bolteae',
}
tier_a_present = {k: v for k, v in tier_a_species.items() if v in ra.index}
log_section('4', f'Tier-A core species in MetaPhlAn3: {len(tier_a_present)}')

# Sample overlap
shared_codes = sorted(set(fam_mat.index) & set(ra.columns))
log_section('4', f'Samples with both viromics + metaphlan3: {len(shared_codes)}')

# Per (Tier-A species, phage family): Spearman ρ across shared samples
sp_log = np.log10(ra.loc[[v for v in tier_a_present.values()], shared_codes].T + 0.001)
sp_log.columns = [k for k in tier_a_present.keys()]
fam_log_shared = fam_mat_log.loc[shared_codes]

corr_rows = []
for sp in sp_log.columns:
    for fam in fam_log_shared.columns:
        try:
            rho, p = stats.spearmanr(sp_log[sp].values, fam_log_shared[fam].values)
            corr_rows.append({'species': sp, 'phage_family': fam, 'rho': round(float(rho), 3), 'p': float(p), 'n': len(shared_codes)})
        except Exception:
            continue
corr_df = pd.DataFrame(corr_rows)
log_section('4', f'\nTotal species × phage-family correlations: {len(corr_df)}')
log_section('4', f'\nTop |rho| species × phage-family correlations:')
log_section('4', corr_df.reindex(corr_df['rho'].abs().sort_values(ascending=False).index).head(15).to_string(index=False))
corr_df.to_csv(f'{OUT_DATA}/nb14_pathobiont_phage_family_corr.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. Verdict + figure')

# Verdict
n_eco_da = da_df['ecotype'].nunique()
n_eco_with_signal = (da_df.groupby('ecotype').apply(lambda d: (d['fdr_within_eco'] < 0.10).sum()) > 0).sum()
n_strong_corr = (corr_df['rho'].abs() > 0.30).sum()

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB14 — HMP2 endogenous phageome × ecotype × diagnosis',
    'n_viromics_samples_with_ecotype': len(overlap),
    'n_unique_phage_families': fv_eco['phage_family'].nunique(),
    'n_ecotypes_tested': int(n_eco_da),
    'n_ecotypes_with_passing_da': int(n_eco_with_signal),
    'n_total_da_tests': len(da_df),
    'n_passing_fdr_10': int((da_df['fdr_within_eco'] < 0.10).sum()),
    'n_pathobiont_phage_family_correlations_strong': int(n_strong_corr),
    'narrative': (
        f'HMP2 endogenous phageome maps onto the 4-ecotype framework via NB04h projection: '
        f'{len(overlap)} of {len(fv_codes)} viromics samples have ecotype calls. '
        f'Per-ecotype × per-virus CD-vs-nonIBD MW DA produces {len(da_df)} tests across '
        f'{int(n_eco_da)} ecotypes; {int(n_eco_with_signal)} ecotypes carry at least one '
        f'passing virus at FDR<0.10. {int(n_strong_corr)} species × phage-family '
        f'correlations at |rho|>0.30 across paired viromics+metaphlan3 samples.'
    ),
}
with open(f'{OUT_DATA}/nb14_endogenous_phageome_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: per-ecotype phage-family abundance heatmap
ax = axes[0]
top_8_fam = fam_eco_pivot.copy()
sns.heatmap(np.log10(top_8_fam + 0.01), cmap='viridis', annot=True, fmt='.1f', cbar_kws={'label': 'log10(mean abundance + 0.01)'}, ax=ax, annot_kws={'fontsize': 7})
ax.set_title('A. Mean abundance per ecotype × phage family (top 8)')
ax.set_xlabel('Phage family')
ax.set_ylabel('Ecotype')

# Panel B: top CD-discriminative viruses across all ecotypes (both directions)
ax = axes[1]
top_da = da_df.copy()
top_da['neg_log_fdr'] = -np.log10(top_da['fdr_within_eco'].clip(lower=1e-10))
top_da = top_da.reindex(top_da['neg_log_fdr'].sort_values(ascending=False).index).head(12)
top_da = top_da.iloc[::-1]
y = np.arange(len(top_da))
colors = ['#e63946' if v > 0 else '#3a86ff' for v in top_da['cliff_delta']]
ax.barh(y, top_da['cliff_delta'], color=colors)
labels = [f'{r["virus_name"][:35]}\n(E{r["ecotype"]}, FDR={r["fdr_within_eco"]:.2g})' for _, r in top_da.iterrows()]
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=7)
ax.axvline(0, color='black', linewidth=0.5)
ax.set_xlabel('Cliff δ (CD vs nonIBD)')
ax.set_title('B. Top 12 most-significant per-ecotype virus DA results\n(red=CD-up; blue=CD-down)')

# Panel C: pathobiont × phage-family correlation heatmap
ax = axes[2]
corr_pivot = corr_df.pivot(index='species', columns='phage_family', values='rho')
# Order pathobionts by NB05 score (top first)
species_order = ['H. hathewayi', 'M. gnavus', 'E. coli', 'E. lenta', 'F. plautii', 'E. bolteae']
species_order = [s for s in species_order if s in corr_pivot.index]
# Order families by total |sum_rho|
fam_order = corr_pivot.abs().sum().sort_values(ascending=False).head(8).index.tolist()
corr_plot = corr_pivot.loc[species_order, fam_order]
sns.heatmap(corr_plot, cmap='RdBu_r', center=0, vmin=-0.4, vmax=0.4, annot=True, fmt='.2f', ax=ax, annot_kws={'fontsize': 8}, cbar_kws={'label': 'Spearman ρ'})
ax.set_title('C. Tier-A species × phage-family Spearman ρ\n(paired HMP2 viromics + metaphlan3)')
ax.set_xlabel('Phage family')
ax.set_ylabel('Tier-A species')

fig.suptitle(f'NB14 — HMP2 endogenous phageome × ecotype × diagnosis (n={len(overlap)} viromics samples × {fv_eco["phage_family"].nunique()} families)', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB14_endogenous_phageome.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB14_endogenous_phageome.png')

with open('/tmp/nb14_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')
