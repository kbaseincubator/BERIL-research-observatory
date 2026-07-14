"""NB09d — H3d-clust metabolite-feature ecotype LOSO stability.

Per plan v1.7 H3d-clust: do metabolite-derived ecotypes achieve higher
LOSO/bootstrap stability than the 0.113 taxonomic-ecotype baseline (NB04f)?
If yes, the metabolite-feature framework is more cross-cohort-portable than
the taxonomic-feature framework.

Method:
1. Pool HMP2 + Franzosa metabolomics on the 122 m/z-bridge metabolites (NB09b)
2. PCA + K=4 K-means refit on pooled data
3. Bootstrap stability: 80%-subsample × 30 iterations → ARI
4. Cross-cohort projection stability: fit on HMP2-only, project Franzosa;
   fit on Franzosa-only, project HMP2; ARI vs full-pooled-fit
5. Compare to NB04f taxonomic-ecotype LOSO ARI 0.113 baseline

Per plan v1.9 (no raw reads): uses precomputed mart tables only.

Falsifiability:
- SUPPORTED if cross-cohort or bootstrap ARI > 0.20 (substantially above
  the 0.113 taxonomic baseline)
- PARTIAL if 0.10 ≤ ARI ≤ 0.20 (comparable to taxonomic baseline)
- NOT SUPPORTED if ARI < 0.10 (worse than taxonomic baseline)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

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
# §0. Load NB09b m/z-matched metabolite panel + pooled metabolomics
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load NB09b m/z-bridge + pooled HMP2 + Franzosa metabolomics')

mat = pd.read_csv(f'{OUT_DATA}/nb09b_cross_cohort_concordance.tsv', sep='\t')
log_section('0', f'NB09b matched pairs: {mat.shape[0]} (HMP2-name × Franzosa-peak)')
log_section('0', f'  unique HMP2 metabolite IDs: {mat["hmp2_metabolite_id"].nunique()}')
log_section('0', f'  unique Franzosa peak IDs: {mat["franz_metabolite_id"].nunique()}')

# Load fact_metabolomics
m = pd.read_parquet(f'{MART}/fact_metabolomics.snappy.parquet')

# HMP2: get sample × HMP2-named-metabolite intensity (subject-level)
hmp2 = m[m['study_id'] == 'HMP2_METABOLOMICS'].copy()
hmp2 = hmp2[hmp2['metabolite_id'].isin(set(mat['hmp2_metabolite_id']))]
hmp2['code'] = hmp2['sample_id'].str.replace('HMP2:', '', regex=False)

# Subject mapping for HMP2
md_h = pd.read_csv(f'{EXT}/hmp2_ibdmdb_sample_metadata.tsv', sep='\t')
md_h['code'] = md_h['sample_id'].str.replace('_P$', '', regex=True)
md_h_uniq = md_h.drop_duplicates(subset='code')[['code', 'subject_id', 'study_condition', 'disease_subtype']]
hmp2 = hmp2.merge(md_h_uniq, on='code', how='inner')

# Aggregate HMP2 to subject × metabolite (mean log10 intensity over visits)
hmp2['log_int'] = np.log10(hmp2['intensity'].clip(lower=0.01))
hmp2_subj = hmp2.groupby(['subject_id', 'metabolite_id'], as_index=False)['log_int'].mean()
hmp2_subj_meta = hmp2.drop_duplicates(subset='subject_id')[['subject_id', 'study_condition', 'disease_subtype']]

# Pivot HMP2 → subject × HMP2-metabolite-id
hmp2_mat = hmp2_subj.pivot(index='subject_id', columns='metabolite_id', values='log_int')
log_section('0', f'\nHMP2 subject-level matrix: {hmp2_mat.shape}')
log_section('0', f'  HMP2 diagnosis distribution: {hmp2_subj_meta["disease_subtype"].fillna("nonIBD").value_counts().to_dict()}')

# Map HMP2 metabolite IDs to Franzosa peak IDs via NB09b
hmp2_to_franz = mat.set_index('hmp2_metabolite_id')['franz_metabolite_id'].to_dict()
hmp2_mat_renamed = hmp2_mat.rename(columns=hmp2_to_franz)
# Some HMP2 IDs map to the same Franzosa peak (n_franz_candidates_at_mz > 1) — collapse duplicates by mean
hmp2_mat_renamed = hmp2_mat_renamed.T.groupby(level=0).mean().T

# Franzosa: get participant × Franzosa-peak intensity
ds = pd.read_parquet(f'{MART}/dim_samples.snappy.parquet')
dp = pd.read_parquet(f'{MART}/dim_participants.snappy.parquet')
franz = m[m['study_id'] == 'FRANZOSA_2019'].copy()
franz = franz[franz['metabolite_id'].isin(set(mat['franz_metabolite_id']))]
ds_franz = ds[ds['study_id'] == 'FRANZOSA_2019'][['sample_id', 'participant_id']]
dp_franz = dp[dp['study_id'] == 'FRANZOSA_2019'][['participant_id', 'diagnosis']]
franz = franz.merge(ds_franz, on='sample_id', how='left').merge(dp_franz, on='participant_id', how='left')
franz['log_int'] = np.log10(franz['intensity'].clip(lower=0.01))
franz_subj = franz.groupby(['participant_id', 'metabolite_id'], as_index=False)['log_int'].mean()
franz_subj_meta = franz.drop_duplicates(subset='participant_id')[['participant_id', 'diagnosis']]

franz_mat = franz_subj.pivot(index='participant_id', columns='metabolite_id', values='log_int')
log_section('0', f'\nFranzosa participant-level matrix: {franz_mat.shape}')
log_section('0', f'  Franzosa diagnosis: {franz_subj_meta["diagnosis"].value_counts().to_dict()}')

# Find columns common to both (after Franzosa-rename of HMP2 cols)
common_cols = sorted(set(hmp2_mat_renamed.columns) & set(franz_mat.columns))
log_section('0', f'\nCommon Franzosa-peak columns (after HMP2 → Franzosa renaming): {len(common_cols)}')

# Build pooled matrix: rows = subject_id (HMP2) or participant_id (Franzosa); cols = common Franzosa peaks
hmp2_pool = hmp2_mat_renamed[common_cols].copy()
hmp2_pool.index = ['HMP2:' + s for s in hmp2_pool.index]
hmp2_pool['cohort'] = 'HMP2'
hmp2_pool['diagnosis'] = hmp2_subj_meta.set_index('subject_id').reindex([s.replace('HMP2:', '') for s in hmp2_pool.index])['disease_subtype'].fillna('nonIBD').values

franz_pool = franz_mat[common_cols].copy()
franz_pool.index = ['FRANZ:' + s for s in franz_pool.index]
franz_pool['cohort'] = 'Franzosa'
franz_pool['diagnosis'] = franz_subj_meta.set_index('participant_id').reindex([s.replace('FRANZ:', '') for s in franz_pool.index])['diagnosis'].values

pooled = pd.concat([hmp2_pool, franz_pool], axis=0)
log_section('0', f'\nPooled subject × metabolite matrix: {pooled.shape}')
log_section('0', f'  cohort × diagnosis:')
log_section('0', pooled.groupby(['cohort', 'diagnosis']).size().to_string())


# ---------------------------------------------------------------------------
# §1. PCA + K-means K=4 on pooled metabolite matrix
# ---------------------------------------------------------------------------
log_section('1', '## §1. PCA + K-means K=4 on pooled metabolite matrix')

X = pooled[common_cols].copy()
# Replace NaN with column-mean
X = X.fillna(X.mean())

# Standardize (z-score per metabolite)
scaler = StandardScaler()
X_z = scaler.fit_transform(X)

# PCA to 15 components (similar to NB01b methodology)
pca = PCA(n_components=15, random_state=0)
X_pca = pca.fit_transform(X_z)
log_section('1', f'PCA: 15 components explain {pca.explained_variance_ratio_.sum()*100:.1f}% variance')
log_section('1', f'  Per-PC: {[f"{v*100:.1f}" for v in pca.explained_variance_ratio_]}')

# K-means K=4
km = KMeans(n_clusters=4, random_state=0, n_init=20)
clusters_full = km.fit_predict(X_pca)
log_section('1', f'\nK-means K=4 cluster sizes: {pd.Series(clusters_full).value_counts().to_dict()}')

# Cross-tabulate with cohort × diagnosis
ct = pd.crosstab(
    pd.Series(clusters_full, name='cluster', index=pooled.index),
    [pooled['cohort'], pooled['diagnosis'].fillna('nonIBD')],
    dropna=False,
)
log_section('1', f'\nCluster × (cohort, diagnosis) cross-tab:\n{ct.to_string()}')


# ---------------------------------------------------------------------------
# §2. Cross-cohort projection LOSO ARI
# ---------------------------------------------------------------------------
log_section('2', '## §2. Cross-cohort projection LOSO ARI')

# Setup: for each cohort hold-out:
#   1. Fit PCA + KMeans on the OTHER cohort
#   2. Transform held-out cohort with the SAME PCA + KMeans
#   3. Compare those held-out predictions to the full-pooled-fit predictions
#      restricted to the held-out cohort
hmp2_idx = pooled['cohort'] == 'HMP2'
franz_idx = pooled['cohort'] == 'Franzosa'

X_hmp2 = X_z[hmp2_idx.values]
X_franz = X_z[franz_idx.values]
clusters_full_hmp2 = clusters_full[hmp2_idx.values]
clusters_full_franz = clusters_full[franz_idx.values]


def fit_predict(train_X, test_X):
    pca_loc = PCA(n_components=min(15, train_X.shape[0]-1), random_state=0)
    pca_loc.fit(train_X)
    train_pca = pca_loc.transform(train_X)
    test_pca = pca_loc.transform(test_X)
    km_loc = KMeans(n_clusters=4, random_state=0, n_init=20)
    km_loc.fit(train_pca)
    return km_loc.predict(test_pca), km_loc.predict(train_pca)


# Hold out HMP2 → fit on Franzosa → project HMP2
proj_hmp2_from_franz, _ = fit_predict(X_franz, X_hmp2)
ari_hmp2_loo = adjusted_rand_score(clusters_full_hmp2, proj_hmp2_from_franz)
log_section('2', f'\nHold-out HMP2 (fit Franzosa, project HMP2):')
log_section('2', f'  ARI vs full-pooled-fit clusters: {ari_hmp2_loo:.3f}')

# Hold out Franzosa → fit on HMP2 → project Franzosa
proj_franz_from_hmp2, _ = fit_predict(X_hmp2, X_franz)
ari_franz_loo = adjusted_rand_score(clusters_full_franz, proj_franz_from_hmp2)
log_section('2', f'\nHold-out Franzosa (fit HMP2, project Franzosa):')
log_section('2', f'  ARI vs full-pooled-fit clusters: {ari_franz_loo:.3f}')

mean_loo_ari = (ari_hmp2_loo + ari_franz_loo) / 2
log_section('2', f'\nMean cross-cohort LOSO ARI: {mean_loo_ari:.3f}')
log_section('2', f'  vs taxonomic baseline (NB04f LOSO ARI = 0.113): {"HIGHER" if mean_loo_ari > 0.113 else "comparable" if mean_loo_ari > 0.05 else "lower"}')


# ---------------------------------------------------------------------------
# §3. Bootstrap stability — 80%-subsample × 30 iterations
# ---------------------------------------------------------------------------
log_section('3', '## §3. Bootstrap stability (80%-subsample × 30 iterations)')

n_total = len(pooled)
n_sub = int(0.8 * n_total)
n_iter = 30
boot_aris = []
rng = np.random.default_rng(0)

for i in range(n_iter):
    idx = rng.choice(n_total, n_sub, replace=False)
    X_sub = X_z[idx]
    pca_loc = PCA(n_components=15, random_state=0)
    X_sub_pca = pca_loc.fit_transform(X_sub)
    km_loc = KMeans(n_clusters=4, random_state=0, n_init=20)
    sub_clusters = km_loc.fit_predict(X_sub_pca)
    full_clusters_sub = clusters_full[idx]
    boot_aris.append(adjusted_rand_score(full_clusters_sub, sub_clusters))

boot_mean = np.mean(boot_aris)
boot_median = np.median(boot_aris)
log_section('3', f'\nBootstrap ARIs (n={n_iter}):')
log_section('3', f'  mean = {boot_mean:.3f}; median = {boot_median:.3f}; range = [{min(boot_aris):.3f}, {max(boot_aris):.3f}]')
log_section('3', f'  vs NB04f taxonomic bootstrap ARI ≈ 0.16: {"HIGHER" if boot_mean > 0.16 else "comparable"}')


# ---------------------------------------------------------------------------
# §4. Cluster-diagnosis informativeness
# ---------------------------------------------------------------------------
log_section('4', '## §4. Cluster × diagnosis informativeness (chi-squared)')

# Test whether clusters carry diagnosis info
dx_clean = pooled['diagnosis'].fillna('nonIBD').replace({'control': 'nonIBD', 'Control': 'nonIBD'})
ct_dx = pd.crosstab(pd.Series(clusters_full, index=pooled.index, name='cluster'), dx_clean)
chi2, p_chi, dof, _ = stats.chi2_contingency(ct_dx.values)
log_section('4', f'\nCluster × diagnosis cross-tab:\n{ct_dx.to_string()}')
log_section('4', f'\nχ²({dof}) = {chi2:.2f}, p = {p_chi:.3e}')

# Per-cluster CD enrichment
log_section('4', f'\nPer-cluster CD fraction:')
for k in sorted(set(clusters_full)):
    mask = clusters_full == k
    n_total_k = mask.sum()
    n_cd = ((dx_clean.values == 'CD') & mask).sum()
    log_section('4', f'  cluster {k}: {n_cd}/{n_total_k} ({100*n_cd/max(n_total_k,1):.1f}%) CD')


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. H3d-clust verdict + figure')

if mean_loo_ari > 0.20:
    verdict_str = 'SUPPORTED — metabolite-feature LOSO ARI substantially above 0.113 taxonomic baseline'
elif mean_loo_ari > 0.10:
    verdict_str = 'PARTIAL — metabolite-feature LOSO ARI comparable to taxonomic 0.113 baseline'
else:
    verdict_str = 'NOT SUPPORTED — metabolite-feature LOSO ARI below taxonomic 0.113 baseline'

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'H3d-clust — metabolite-feature ecotype LOSO stability vs taxonomic 0.113 baseline',
    'pooled_n_subjects': n_total,
    'common_metabolite_features': len(common_cols),
    'pca_n_components': 15,
    'pca_var_explained': float(pca.explained_variance_ratio_.sum()),
    'kmeans_K': 4,
    'cluster_sizes': pd.Series(clusters_full).value_counts().to_dict(),
    'cross_cohort_LOSO_ARI_HMP2_held_out': round(float(ari_hmp2_loo), 3),
    'cross_cohort_LOSO_ARI_Franzosa_held_out': round(float(ari_franz_loo), 3),
    'mean_LOSO_ARI': round(float(mean_loo_ari), 3),
    'bootstrap_mean_ARI': round(float(boot_mean), 3),
    'bootstrap_median_ARI': round(float(boot_median), 3),
    'taxonomic_NB04f_LOSO_ARI_baseline': 0.113,
    'taxonomic_NB04b_bootstrap_ARI_baseline': 0.16,
    'cluster_diagnosis_chi2': round(float(chi2), 3),
    'cluster_diagnosis_p': float(p_chi),
    'h3d_clust_verdict': verdict_str,
}
with open(f'{OUT_DATA}/nb09d_h3d_clust_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))

# Save assignments for downstream
pooled_out = pooled.copy()
pooled_out['metabolite_cluster'] = clusters_full
pooled_out[['cohort', 'diagnosis', 'metabolite_cluster']].to_csv(f'{OUT_DATA}/nb09d_metabolite_ecotype_assignments.tsv', sep='\t')


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: PCA scatter colored by metabolite-cluster
ax = axes[0]
colors = ['#e63946', '#264653', '#2a9d8f', '#f4a261']
for k in sorted(set(clusters_full)):
    mask = clusters_full == k
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1], c=colors[k], label=f'cluster {k}', s=30, alpha=0.6, edgecolors='black', linewidth=0.3)
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
ax.set_title(f'A. PCA colored by metabolite K=4 cluster (pooled n={n_total})')
ax.legend(loc='upper right', fontsize=8)

# Panel B: cluster × diagnosis stacked bar (per cluster)
ax = axes[1]
ct_norm = ct_dx.div(ct_dx.sum(axis=1), axis=0) * 100
dx_order = [c for c in ['nonIBD', 'CD', 'UC'] if c in ct_norm.columns]
dx_colors = {'nonIBD': '#73c0e8', 'CD': '#e63946', 'UC': '#f4a261'}
bottom = np.zeros(ct_norm.shape[0])
for dx in dx_order:
    if dx not in ct_norm.columns:
        continue
    ax.bar(ct_norm.index, ct_norm[dx], bottom=bottom, label=dx, color=dx_colors[dx])
    bottom += ct_norm[dx].values
ax.set_xlabel('Metabolite cluster')
ax.set_ylabel('% diagnosis composition')
ax.set_title(f'B. Diagnosis composition per cluster (χ²={chi2:.1f}, p={p_chi:.2g})')
ax.legend()

# Panel C: stability summary
ax = axes[2]
metrics = {
    'Cross-cohort LOSO\n(HMP2 held out)': ari_hmp2_loo,
    'Cross-cohort LOSO\n(Franzosa held out)': ari_franz_loo,
    'Bootstrap mean\n(80% subsample × 30)': boot_mean,
    'NB04f taxonomic\nLOSO baseline': 0.113,
    'NB04b taxonomic\nbootstrap baseline': 0.16,
}
y = np.arange(len(metrics))
colors2 = ['#2a9d8f' if v > 0.20 else '#e9c46a' if v > 0.10 else '#e76f51' for v in metrics.values()]
ax.barh(y, list(metrics.values()), color=colors2)
ax.axvline(0.113, color='black', linestyle=':', linewidth=0.5, label='taxonomic 0.113')
ax.set_yticks(y)
ax.set_yticklabels(list(metrics.keys()), fontsize=8)
ax.set_xlabel('ARI')
ax.set_title('C. Stability metrics — metabolite vs taxonomic ecotypes')
for i, v in enumerate(metrics.values()):
    ax.text(v + 0.005, i, f'{v:.3f}', va='center', fontsize=8)
ax.legend(loc='lower right', fontsize=7)

fig.suptitle(f'NB09d — H3d-clust metabolite-feature ecotype stability: {verdict_str.split(" — ")[0]}', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB09d_metabolite_ecotype_stability.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB09d_metabolite_ecotype_stability.png')

with open('/tmp/nb09d_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')
