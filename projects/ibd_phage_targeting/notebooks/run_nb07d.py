"""NB07d — MOFA+-style HMP2 multi-omics joint factor analysis (taxonomy + metabolomics).

Per plan v1.7 NB07d: joint-factor analysis on HMP2 taxonomy + pathways +
metabolomics; ecotype as covariate (not factor target). Per plan v1.9 no
raw reads.

Scope adjustment: HMP2 pathway abundance is NOT in the mart
(fact_pathway_abundance contains CMD_IBD_PATHWAYS only — HMP2 pathways would
require raw HUMAnN3 reprocessing which is dropped per v1.9). This notebook
runs a 2-modality joint factor analysis on (HMP2 taxonomy + HMP2 metabolomics)
on the 106 paired CSM* subjects established in NB09c.

mofapy2 is not installed in the environment; use sklearn CCA + PCA on stacked
modalities as a simplified MOFA+ proxy. CCA finds linear combinations of
features in each modality that are maximally correlated (canonical pairs);
PCA on stacked z-scored modality-PCs gives joint factors that capture
cross-modality co-variation.

Tests:
1. CCA between CLR-transformed taxonomy and log-metabolite; 4 canonical pairs
2. Examine factor loadings: do top loadings recapitulate iron-acquisition
   (E. coli ↔ iron metabolites) or bile-acid 7α-dehydroxylation
   (F. plautii / E. lenta / E. bolteae ↔ secondary BAs) narratives?
3. Annotate samples on factor scores: diagnosis + ecotype + sex + age
4. Test factor × diagnosis association (Mann-Whitney CD vs nonIBD)

Compare to NB09c cross-corroborated mechanism findings.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cross_decomposition import CCA

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
# §0. Load paired HMP2 metaphlan3 + metabolomics + diagnosis
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load paired HMP2 metaphlan3 + metabolomics + diagnosis')

# Metabolomics
m = pd.read_parquet(f'{MART}/fact_metabolomics.snappy.parquet')
metab = m[m['study_id'] == 'HMP2_METABOLOMICS'].copy()
metab['code'] = metab['sample_id'].str.replace('HMP2:', '', regex=False)

# Annotations
ann = pd.read_parquet(f'{MART}/ref_hmp2_metabolite_annotations.snappy.parquet')
named_ann = ann[ann['metabolite_name'].notna() & (ann['metabolite_name'].astype(str).str.strip() != '')].copy()
named_ids = set(named_ann['metabolite_id'])

# cMD HMP2 metadata
md = pd.read_csv(f'{EXT}/hmp2_ibdmdb_sample_metadata.tsv', sep='\t')
md['code'] = md['sample_id'].str.replace('_P$', '', regex=True)

# Relative abundance
ra = pd.read_csv(f'{EXT}/hmp2_ibdmdb_relative_abundance.tsv', sep='\t', index_col=0)
ra.index = ra.index.str.replace('species:', '', regex=False)
ra.columns = ra.columns.str.replace('_P$', '', regex=True)
ra = ra.loc[:, ~ra.columns.duplicated(keep='first')]

# Paired subjects (intersection of metabolomics + metaphlan3)
metab_codes = set(metab['code'].unique())
ra_codes = set(ra.columns)
paired_codes = sorted(metab_codes & ra_codes)
log_section('0', f'Paired HMP2 samples (metab ∩ metaphlan3): {len(paired_codes)}')

# Subject-level diagnosis
md_paired = md[md['code'].isin(paired_codes)].drop_duplicates(subset='code')[['code', 'subject_id', 'study_condition', 'disease_subtype']]
md_paired['dx'] = md_paired['disease_subtype'].fillna('nonIBD')
md_paired.loc[md_paired['study_condition'] == 'control', 'dx'] = 'nonIBD'

# Aggregate to subject level (first occurrence per subject)
subj_first = md_paired.groupby('subject_id', as_index=False).first()
subj_codes = subj_first['code'].tolist()
log_section('0', f'Subject-level (first-occurrence) samples: {subj_first.shape[0]}')
log_section('0', f'  Diagnosis: {subj_first["dx"].value_counts().to_dict()}')


# ---------------------------------------------------------------------------
# §1. Build modality matrices
# ---------------------------------------------------------------------------
log_section('1', '## §1. Build modality matrices')

# Modality 1: MetaPhlAn3 species relative abundance — CLR-transformed
sp_mat = ra[subj_codes].T  # samples × species
log_section('1', f'Raw species matrix: {sp_mat.shape}')

# Filter species: ≥10 % prevalence
sp_prev = (sp_mat > 0).mean()
keep_sp = sp_prev >= 0.10
sp_mat_filt = sp_mat.loc[:, keep_sp]
log_section('1', f'After ≥10% prevalence filter: {sp_mat_filt.shape}')

# CLR transformation
def clr_row(arr, eps=1e-6):
    arr = np.maximum(arr, eps)
    log_arr = np.log(arr)
    return log_arr - log_arr.mean()


sp_clr = sp_mat_filt.apply(clr_row, axis=1)
log_section('1', f'CLR-transformed species matrix: {sp_clr.shape}')

# Modality 2: HMP2 named metabolites — log10 intensity
metab_named = metab[metab['metabolite_id'].isin(named_ids) & metab['code'].isin(subj_codes)].copy()
metab_named['log_int'] = np.log10(metab_named['intensity'].clip(lower=0.01))
metab_subj = metab_named.groupby(['code', 'metabolite_id'], as_index=False)['log_int'].mean()
m_mat = metab_subj.pivot(index='code', columns='metabolite_id', values='log_int')
m_mat = m_mat.reindex(subj_codes)
log_section('1', f'Metabolite matrix raw: {m_mat.shape}')

# Filter metabolites: ≥30 % non-NaN coverage
m_cov = m_mat.notna().mean()
keep_m = m_cov >= 0.30
m_mat_filt = m_mat.loc[:, keep_m]
log_section('1', f'After ≥30% coverage filter: {m_mat_filt.shape}')

# Impute remaining NaN with column-mean (subject-level matrix should have minimal missing after the prevalence filter)
m_mat_filt = m_mat_filt.fillna(m_mat_filt.mean())

# Standardize within modality
sc_sp = StandardScaler()
sc_m = StandardScaler()
sp_z = sc_sp.fit_transform(sp_clr.values)
m_z = sc_m.fit_transform(m_mat_filt.values)

# Diagnosis labels aligned to subj_codes
dx_aligned = subj_first.set_index('code').loc[subj_codes, 'dx'].values
log_section('1', f'\nFinal modality matrices: species ({sp_z.shape}) + metabolites ({m_z.shape})')
log_section('1', f'  Diagnosis: {pd.Series(dx_aligned).value_counts().to_dict()}')


# ---------------------------------------------------------------------------
# §2. CCA — 4 canonical pairs between modalities
# ---------------------------------------------------------------------------
log_section('2', '## §2. CCA — 4 canonical pairs (taxonomy ↔ metabolomics)')

# Reduce species first via PCA to make CCA stable (n_features > n_samples otherwise)
n_subj = sp_z.shape[0]
n_pca = min(30, n_subj - 1)
sp_pca = PCA(n_components=n_pca, random_state=0)
sp_pcs = sp_pca.fit_transform(sp_z)
m_pca = PCA(n_components=n_pca, random_state=0)
m_pcs = m_pca.fit_transform(m_z)
log_section('2', f'Per-modality PCA to {n_pca} components: species explains {sp_pca.explained_variance_ratio_.sum()*100:.1f}%, metabolites explains {m_pca.explained_variance_ratio_.sum()*100:.1f}%')

# CCA on PCs
n_cc = 4
cca = CCA(n_components=n_cc, max_iter=500)
cca.fit(sp_pcs, m_pcs)
sp_cc, m_cc = cca.transform(sp_pcs, m_pcs)

# Canonical correlations
canon_corrs = []
for i in range(n_cc):
    r, p = stats.pearsonr(sp_cc[:, i], m_cc[:, i])
    canon_corrs.append((r, p))
log_section('2', f'\nCanonical correlations (4 components):')
for i, (r, p) in enumerate(canon_corrs):
    log_section('2', f'  CC{i+1}: r = {r:.3f}, p = {p:.3e}')


# ---------------------------------------------------------------------------
# §3. Joint factor scores (mean of paired CC scores)
# ---------------------------------------------------------------------------
log_section('3', '## §3. Joint factor scores + diagnosis association')

# Joint factor: mean of (sp_cc, m_cc) per CC index — reflects shared variation
joint_factors = (sp_cc + m_cc) / 2

# Test factor × diagnosis association
log_section('3', f'\nFactor × diagnosis Mann-Whitney CD-vs-nonIBD:')
factor_dx_rows = []
for i in range(n_cc):
    cd_vals = joint_factors[dx_aligned == 'CD', i]
    hc_vals = joint_factors[dx_aligned == 'nonIBD', i]
    uc_vals = joint_factors[dx_aligned == 'UC', i]
    if len(cd_vals) >= 5 and len(hc_vals) >= 5:
        u, p = stats.mannwhitneyu(cd_vals, hc_vals, alternative='two-sided')
        n1, n2 = len(cd_vals), len(hc_vals)
        cliff = 2 * u / (n1 * n2) - 1
        log_section('3', f'  CC{i+1}: cliff_delta = {cliff:+.3f}, MW p = {p:.3e}; UC mean factor = {uc_vals.mean():.2f}')
        factor_dx_rows.append({'cc': i+1, 'cliff_cd_vs_nonibd': round(float(cliff), 3), 'mw_p': float(p),
                               'mean_cd': float(cd_vals.mean()), 'mean_uc': float(uc_vals.mean()), 'mean_nonibd': float(hc_vals.mean()),
                               'canon_r': round(float(canon_corrs[i][0]), 3)})


# ---------------------------------------------------------------------------
# §4. Top species and metabolite loadings per CC
# ---------------------------------------------------------------------------
log_section('4', '## §4. Top species and metabolite loadings per canonical component')

# Project canonical-component weights back to original feature space
# CC weight in PC space → multiply by PCA components → original feature space
species_names = sp_clr.columns.tolist()
metab_names_in_mat = m_mat_filt.columns.tolist()
metab_id_to_name = named_ann.set_index('metabolite_id')['metabolite_name'].to_dict()

# Canonical loadings on original features
sp_loadings_origfeat = sp_pca.components_.T @ cca.x_weights_   # (n_features, n_cc)
m_loadings_origfeat = m_pca.components_.T @ cca.y_weights_   # (n_features, n_cc)

loadings_rows = []
for i in range(n_cc):
    sp_load = pd.Series(sp_loadings_origfeat[:, i], index=species_names).sort_values(key=abs, ascending=False)
    m_load = pd.Series(m_loadings_origfeat[:, i], index=metab_names_in_mat).sort_values(key=abs, ascending=False)
    log_section('4', f'\n=== CC{i+1} top species (by |loading|): ===')
    for s in sp_load.head(10).index:
        log_section('4', f'  {sp_load[s]:+.3f}  {s}')
    log_section('4', f'\n=== CC{i+1} top metabolites (by |loading|): ===')
    for mid in m_load.head(10).index:
        nm = metab_id_to_name.get(mid, mid)
        log_section('4', f'  {m_load[mid]:+.3f}  {nm}')
    # Save top-15 loadings per CC
    for s in sp_load.head(15).index:
        loadings_rows.append({'cc': i+1, 'modality': 'species', 'feature': s, 'loading': round(float(sp_load[s]), 4)})
    for mid in m_load.head(15).index:
        nm = metab_id_to_name.get(mid, mid)
        loadings_rows.append({'cc': i+1, 'modality': 'metabolite', 'feature': nm, 'loading': round(float(m_load[mid]), 4)})

loadings_df = pd.DataFrame(loadings_rows)
loadings_df.to_csv(f'{OUT_DATA}/nb07d_cca_loadings.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §5. Cross-reference to NB07-pillar findings
# ---------------------------------------------------------------------------
log_section('5', '## §5. Cross-reference to NB07-pillar narratives')

# Iron-acquisition narrative: do any CCs have E. coli + iron metabolites co-loading?
# Bile-acid narrative: do any CCs have F. plautii / E. lenta / E. bolteae + secondary BAs?

iron_metabolite_keywords = ['heme', 'iron', 'sider', 'bilirubin']  # urobilin is a bilirubin product
ba_secondary_keywords = ['lithocholate', 'deoxycholate', 'ketodeoxycholate', 'chenodeoxycholate']
ba_primary_keywords = ['taurocholate', 'taurochol', 'tauro-alpha', 'tauro-beta', 'tauroursodeoxy', 'cholate']
polyamine_keywords = ['putrescine', 'spermine', 'spermidine', 'cadaverine', 'acetylsperm', 'acetylputrescine', 'anserine']
pufa_keywords = ['arachidonate', 'adrenate', 'docosahexaeno', 'docosapentaeno', 'eicosapentaeno']

key_species = ['Escherichia coli', '[Ruminococcus] gnavus', 'Hungatella hathewayi',
               'Eggerthella lenta', 'Flavonifractor plautii', 'Enterocloster bolteae',
               'Anaerostipes caccae', 'Bacteroides nordii']


def loading_in_set(loading_series, keywords):
    """Return list of (feature, loading) where feature name matches any keyword (case-insensitive substring)."""
    out = []
    for k, v in loading_series.items():
        nm = str(k).lower()
        if any(kw.lower() in nm for kw in keywords):
            out.append((k, float(v)))
    return out


for i in range(n_cc):
    sp_load = pd.Series(sp_loadings_origfeat[:, i], index=species_names)
    m_load_named = pd.Series([metab_id_to_name.get(mid, mid) for mid in metab_names_in_mat], index=metab_names_in_mat)
    m_load_name_idx = pd.Series(m_loadings_origfeat[:, i], index=[metab_id_to_name.get(mid, mid) for mid in metab_names_in_mat])

    log_section('5', f'\n=== CC{i+1} ({canon_corrs[i][0]:.2f}) — narrative cross-reference ===')
    # Tier-A core species loadings
    log_section('5', f'  Tier-A core + anchor species loadings:')
    for sp in key_species:
        if sp in sp_load.index:
            log_section('5', f'    {sp_load[sp]:+.3f}  {sp}')
    # Theme-relevant metabolites
    for theme, kws in [('iron/bilirubin', iron_metabolite_keywords),
                      ('BA secondary', ba_secondary_keywords),
                      ('BA primary tauro', ba_primary_keywords),
                      ('polyamines', polyamine_keywords),
                      ('long-chain PUFA', pufa_keywords)]:
        hits = loading_in_set(m_load_name_idx, kws)
        if hits:
            log_section('5', f'  Top {theme} metabolite loadings:')
            for nm, v in sorted(hits, key=lambda x: -abs(x[1]))[:4]:
                log_section('5', f'    {v:+.3f}  {nm}')


# ---------------------------------------------------------------------------
# §6. Verdict + figure
# ---------------------------------------------------------------------------
log_section('6', '## §6. Verdict + figure')

# Verdict logic:
#  - If at least 2 canonical pairs have r > 0.5 AND at least 1 CC has CD-vs-nonIBD cliff |delta| > 0.3
#    → joint factor analysis recovers cross-modality structure aligned with diagnosis
n_strong_canon = sum(1 for r, _ in canon_corrs if r > 0.5)
n_dx_assoc = sum(1 for row in factor_dx_rows if abs(row['cliff_cd_vs_nonibd']) > 0.3 and row['mw_p'] < 0.05)
if n_strong_canon >= 2 and n_dx_assoc >= 1:
    verdict_str = 'PILOT SUCCESSFUL — multi-modal joint factors capture cross-modality structure with diagnosis association'
elif n_strong_canon >= 1:
    verdict_str = 'PILOT PARTIAL — canonical correlations strong but diagnosis-association of factors is modest'
else:
    verdict_str = 'PILOT WEAK — joint factors do not capture strong cross-modality structure on this subject set'

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB07d — HMP2 multi-modality joint factor pilot (taxonomy + metabolomics; pathway not in mart)',
    'n_subjects': int(n_subj),
    'n_species_features': int(sp_z.shape[1]),
    'n_metabolite_features': int(m_z.shape[1]),
    'n_pca_components_per_modality': int(n_pca),
    'n_canonical_pairs': int(n_cc),
    'canonical_correlations': [round(float(r), 3) for r, _ in canon_corrs],
    'factor_diagnosis_associations': factor_dx_rows,
    'pilot_verdict': verdict_str,
    'note': 'HMP2 pathway abundance is NOT in the mart (fact_pathway_abundance contains CMD_IBD_PATHWAYS only); 3-modality MOFA+ as planned in v1.7 is not feasible per plan v1.9 no-raw-reads. Falls back to 2-modality (taxonomy + metabolomics).',
}
with open(f'{OUT_DATA}/nb07d_mofa_pilot_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('6', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §7. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: CC1 vs CC2 scatter colored by diagnosis
ax = axes[0]
dx_colors = {'CD': '#e63946', 'UC': '#f4a261', 'nonIBD': '#73c0e8'}
for dx in ['nonIBD', 'UC', 'CD']:
    mask = dx_aligned == dx
    if mask.sum():
        ax.scatter(joint_factors[mask, 0], joint_factors[mask, 1], c=dx_colors[dx],
                  label=f'{dx} (n={mask.sum()})', s=30, alpha=0.7, edgecolors='black', linewidth=0.3)
ax.set_xlabel(f'CC1 (canon r={canon_corrs[0][0]:.2f})')
ax.set_ylabel(f'CC2 (canon r={canon_corrs[1][0]:.2f})')
ax.set_title(f'A. Joint factor space (CC1 × CC2; n={n_subj} subjects)')
ax.legend(loc='upper right', fontsize=8)
ax.axhline(0, color='gray', linewidth=0.5, linestyle=':')
ax.axvline(0, color='gray', linewidth=0.5, linestyle=':')

# Panel B: Top species loadings on CC1 (most-CD-associated factor if any)
# Pick the CC with highest |cliff_cd_vs_nonibd|
if factor_dx_rows:
    top_cc = max(range(len(factor_dx_rows)), key=lambda i: abs(factor_dx_rows[i]['cliff_cd_vs_nonibd']))
else:
    top_cc = 0

ax = axes[1]
sp_load = pd.Series(sp_loadings_origfeat[:, top_cc], index=species_names).sort_values(key=abs, ascending=False).head(15)
y = np.arange(len(sp_load))[::-1]
colors = ['#e63946' if v > 0 else '#3a86ff' for v in sp_load]
ax.barh(y, sp_load.values, color=colors)
ax.set_yticks(y)
ax.set_yticklabels([s[:30] for s in sp_load.index], fontsize=7)
ax.axvline(0, color='black', linewidth=0.5)
ax.set_xlabel(f'CC{top_cc+1} loading')
cliff_at_top = factor_dx_rows[top_cc]['cliff_cd_vs_nonibd'] if factor_dx_rows else 0
ax.set_title(f'B. CC{top_cc+1} top 15 species loadings (cliff CD-vs-nonIBD = {cliff_at_top:+.2f})')

# Panel C: Top metabolite loadings on the same CC
ax = axes[2]
m_load = pd.Series(m_loadings_origfeat[:, top_cc], index=[metab_id_to_name.get(mid, mid) for mid in metab_names_in_mat]).sort_values(key=abs, ascending=False).head(15)
y = np.arange(len(m_load))[::-1]
colors = ['#e63946' if v > 0 else '#3a86ff' for v in m_load]
ax.barh(y, m_load.values, color=colors)
ax.set_yticks(y)
ax.set_yticklabels([str(s)[:30] for s in m_load.index], fontsize=7)
ax.axvline(0, color='black', linewidth=0.5)
ax.set_xlabel(f'CC{top_cc+1} loading')
ax.set_title(f'C. CC{top_cc+1} top 15 metabolite loadings')

fig.suptitle(f'NB07d — HMP2 2-modality joint factor pilot (taxonomy + metabolomics): {verdict_str.split(" — ")[0]}', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB07d_mofa_pilot.png', dpi=120, bbox_inches='tight')
log_section('6', f'\nWrote {OUT_FIG}/NB07d_mofa_pilot.png')

# Save scores
score_df = pd.DataFrame({
    'subject_code': subj_codes,
    'diagnosis': dx_aligned,
    'CC1_species': sp_cc[:, 0], 'CC1_metab': m_cc[:, 0], 'CC1_joint': joint_factors[:, 0],
    'CC2_species': sp_cc[:, 1], 'CC2_metab': m_cc[:, 1], 'CC2_joint': joint_factors[:, 1],
    'CC3_species': sp_cc[:, 2], 'CC3_metab': m_cc[:, 2], 'CC3_joint': joint_factors[:, 2],
    'CC4_species': sp_cc[:, 3], 'CC4_metab': m_cc[:, 3], 'CC4_joint': joint_factors[:, 3],
})
score_df.to_csv(f'{OUT_DATA}/nb07d_subject_factor_scores.tsv', sep='\t', index=False)

with open('/tmp/nb07d_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')
