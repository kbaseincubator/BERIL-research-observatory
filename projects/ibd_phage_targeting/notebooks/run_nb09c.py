"""NB09c — Sample-level paired metabolomics × metagenomics cross-feeding test.

Disambiguates the NB07c cross-feeding hypothesis (A. caccae × pathobiont
species-level coupling could reflect cross-feeding OR shared-environment).
Within paired HMP2 CSM* samples (metabolomics + MetaPhlAn3 metagenomics),
compute per (species, metabolite) Spearman ρ across samples and flag
"cross-feeding triangles" where both anchor and pathobiont species correlate
strongly and same-sign with a candidate intermediate metabolite.

Per plan v1.9 (no raw reads): uses cMD-fetched HMP2 MetaPhlAn3 abundance +
mart fact_metabolomics + ref_hmp2_metabolite_annotations.
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
# §0. Load paired HMP2 metabolomics × metagenomics + species + metabolite map
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load paired HMP2 metabolomics × MetaPhlAn3 metagenomics')

# Metabolomics
metab = pd.read_parquet(f'{MART}/fact_metabolomics.snappy.parquet')
metab = metab[metab['study_id'] == 'HMP2_METABOLOMICS'].copy()
metab['code'] = metab['sample_id'].str.replace('HMP2:', '', regex=False)

# Annotations
ann = pd.read_parquet(f'{MART}/ref_hmp2_metabolite_annotations.snappy.parquet')
named_ann = ann[ann['metabolite_name'].notna() & (ann['metabolite_name'].astype(str).str.strip() != '')].copy()
named_ids = set(named_ann['metabolite_id'])
log_section('0', f'HMP2 metabolomics rows: {metab.shape[0]}; named metabolite IDs: {len(named_ids)}')

# Species abundance (cMD R-package fetch)
ra = pd.read_csv(f'{EXT}/hmp2_ibdmdb_relative_abundance.tsv', sep='\t', index_col=0)
ra.index = ra.index.str.replace('species:', '', regex=False)
ra.columns = ra.columns.str.replace('_P$', '', regex=True)
# Deduplicate columns (some samples appear with both _P and non-_P forms after suffix strip)
ra = ra.loc[:, ~ra.columns.duplicated(keep='first')]
log_section('0', f'HMP2 MetaPhlAn3 abundance shape (dedup): {ra.shape} (species × samples)')

# Pair samples by code
metab_codes = set(metab['code'].unique())
ra_codes = set(ra.columns)
paired_codes = sorted(metab_codes & ra_codes)
log_section('0', f'Paired samples (metabolomics ∩ metagenomics): {len(paired_codes)}')

# Diagnosis labels for paired samples (via cMD HMP2 metadata)
md = pd.read_csv(f'{EXT}/hmp2_ibdmdb_sample_metadata.tsv', sep='\t')
md['code'] = md['sample_id'].str.replace('_P$', '', regex=True)
md_paired = md[md['code'].isin(paired_codes)][['code', 'subject_id', 'study_condition', 'disease_subtype']].drop_duplicates(subset='code')
log_section('0', f'  with diagnosis labels: {md_paired.shape[0]}')


# ---------------------------------------------------------------------------
# §1. Build paired matrix: samples × {NB07c species + named metabolites}
# ---------------------------------------------------------------------------
log_section('1', '## §1. Build paired sample × {NB07c species + named metabolites} matrix')

# NB07c E1_CD module species (anchors + pathobionts)
SPECIES_MAP = {
    'A. caccae (anchor)': 'Anaerostipes caccae',
    'B. nordii (anchor)': 'Bacteroides nordii',
    'H. hathewayi (pathobiont)': 'Hungatella hathewayi',
    'F. plautii (pathobiont)': 'Flavonifractor plautii',
    'E. bolteae (pathobiont)': 'Enterocloster bolteae',
    'E. lenta (pathobiont)': 'Eggerthella lenta',
    'M. gnavus (pathobiont)': '[Ruminococcus] gnavus',
    'E. coli (Tier-A core)': 'Escherichia coli',
}
species_present = {k: v for k, v in SPECIES_MAP.items() if v in ra.index}
log_section('1', f'NB07c species present in MetaPhlAn3: {len(species_present)} / {len(SPECIES_MAP)}')
for k, v in species_present.items():
    log_section('1', f'  {k}: {v}')

# Build species matrix (paired_codes × species)
sp_mat = ra.loc[[v for v in species_present.values()], paired_codes].T  # samples × species
sp_mat.columns = [k for k in species_present.keys()]
log_section('1', f'Species matrix: {sp_mat.shape}')

# Filter species: require at least 30 % prevalence
sp_prev = (sp_mat > 0).mean()
log_section('1', f'\nSpecies prevalence in paired samples:')
for c in sp_mat.columns:
    log_section('1', f'  {c}: {sp_prev[c]:.2f} ({(sp_mat[c]>0).sum()}/{len(sp_mat)})')

# Metabolite matrix: build pivoted log10 intensities for named metabolites only
metab_named = metab[metab['metabolite_id'].isin(named_ids) & metab['code'].isin(paired_codes)].copy()
log_section('1', f'\nMetabolomics rows on paired samples × named: {metab_named.shape[0]}')

# Sum if duplicate (sample, metabolite) — should not happen but just in case
metab_long = metab_named.groupby(['code', 'metabolite_id'])['intensity'].mean().reset_index()
metab_long['log_intensity'] = np.log10(metab_long['intensity'].clip(lower=0.01))
m_mat = metab_long.pivot(index='code', columns='metabolite_id', values='log_intensity')
m_mat = m_mat.reindex(paired_codes)
log_section('1', f'Metabolite matrix: {m_mat.shape}')

# Filter metabolites: require ≥30 % non-NaN coverage AND ≥10 % prevalence above intensity-baseline (>0.5 log10 above the matrix-wide minimum per metabolite)
prev_thr = 0.30
m_cov = m_mat.notna().mean()
m_keep = m_cov >= prev_thr
log_section('1', f'Metabolites with ≥{prev_thr*100:.0f}% non-NaN coverage: {m_keep.sum()} / {m_mat.shape[1]}')
m_mat = m_mat.loc[:, m_keep]


# ---------------------------------------------------------------------------
# §2. Per (species, metabolite) Spearman ρ
# ---------------------------------------------------------------------------
log_section('2', '## §2. Per (species, metabolite) Spearman ρ on paired samples')

# CLR-transform species (within each sample)
def clr(arr, eps=1e-6):
    arr = np.array(arr, dtype=float)
    arr = np.maximum(arr, eps)
    log_arr = np.log(arr)
    return log_arr - log_arr.mean()


sp_clr = sp_mat.copy()
for s in sp_clr.index:
    row = sp_mat.loc[s].values
    if row.sum() > 0:
        sp_clr.loc[s] = clr(row)
    else:
        sp_clr.loc[s] = 0.0

corr_rows = []
for sp_label in sp_mat.columns:
    sp_vals = sp_clr[sp_label].values
    for mid in m_mat.columns:
        m_vals = m_mat[mid].values
        # Use pairs where both are non-NaN
        mask = ~np.isnan(m_vals) & ~np.isnan(sp_vals)
        if mask.sum() < 50:
            continue
        rho, p = stats.spearmanr(sp_vals[mask], m_vals[mask])
        corr_rows.append({
            'species_label': sp_label,
            'metabolite_id': mid,
            'n': int(mask.sum()),
            'rho': round(float(rho), 4),
            'p': float(p),
        })

corr_df = pd.DataFrame(corr_rows)
log_section('2', f'Computed correlations: {corr_df.shape[0]} (species × metabolite × paired samples)')

# BH-FDR per species (each species tested against all metabolites)
def bh_fdr(p_arr):
    p_arr = np.array(p_arr)
    m = len(p_arr)
    order = np.argsort(p_arr)
    ranked = p_arr[order]
    fdr = np.minimum.accumulate((ranked[::-1] * m / np.arange(m, 0, -1)))[::-1]
    out = np.empty(m)
    out[order] = fdr
    return out


fdr_vals = []
for sp_label in corr_df['species_label'].unique():
    mask = corr_df['species_label'] == sp_label
    fdr_vals.append(pd.Series(bh_fdr(corr_df.loc[mask, 'p'].values), index=corr_df.index[mask]))
corr_df['fdr_within_sp'] = pd.concat(fdr_vals).sort_index()
corr_df = corr_df.merge(named_ann[['metabolite_id', 'metabolite_name', 'method', 'hmdb_id']], on='metabolite_id', how='left')
corr_df.to_csv(f'{OUT_DATA}/nb09c_species_metabolite_corr.tsv', sep='\t', index=False)

# Top correlations per species
log_section('2', f'\nTop 5 |ρ| metabolites per species (FDR<0.10):')
for sp_label in sp_mat.columns:
    sub = corr_df[(corr_df['species_label'] == sp_label) & (corr_df['fdr_within_sp'] < 0.10)]
    if not len(sub):
        log_section('2', f'\n{sp_label}: none at FDR<0.10')
        continue
    top = sub.reindex(sub['rho'].abs().sort_values(ascending=False).index).head(5)
    log_section('2', f'\n{sp_label} ({len(sub)} significant):')
    for _, r in top.iterrows():
        log_section('2', f"  ρ={r['rho']:+.3f}  FDR={r['fdr_within_sp']:.2g}  {r['metabolite_name']:<45s}  ({r['method']})")


# ---------------------------------------------------------------------------
# §3. Cross-feeding-triangle test: anchor + pathobiont same-sign correlation
# ---------------------------------------------------------------------------
log_section('3', '## §3. Cross-feeding-triangle test: same-sign anchor × pathobiont metabolite candidates')

ANCHORS = ['A. caccae (anchor)', 'B. nordii (anchor)']
PATHOBIONTS = ['H. hathewayi (pathobiont)', 'F. plautii (pathobiont)',
               'E. bolteae (pathobiont)', 'E. lenta (pathobiont)', 'M. gnavus (pathobiont)']

# Pivot to species × metabolite ρ matrix
rho_mat = corr_df.pivot(index='species_label', columns='metabolite_id', values='rho')
fdr_mat = corr_df.pivot(index='species_label', columns='metabolite_id', values='fdr_within_sp')

triangle_rows = []
for a in ANCHORS:
    if a not in rho_mat.index:
        continue
    for p in PATHOBIONTS:
        if p not in rho_mat.index:
            continue
        for mid in rho_mat.columns:
            r_a = rho_mat.loc[a, mid]
            r_p = rho_mat.loc[p, mid]
            f_a = fdr_mat.loc[a, mid]
            f_p = fdr_mat.loc[p, mid]
            if pd.isna(r_a) or pd.isna(r_p):
                continue
            # Cross-feeding-triangle criteria
            same_sign = (r_a * r_p) > 0
            both_strong = (abs(r_a) > 0.20) and (abs(r_p) > 0.20)
            both_sig = (f_a < 0.10) and (f_p < 0.10)
            if same_sign and both_strong and both_sig:
                triangle_rows.append({
                    'anchor': a,
                    'pathobiont': p,
                    'metabolite_id': mid,
                    'rho_anchor': round(float(r_a), 3),
                    'rho_pathobiont': round(float(r_p), 3),
                    'fdr_anchor': float(f_a),
                    'fdr_pathobiont': float(f_p),
                    'min_abs_rho': round(float(min(abs(r_a), abs(r_p))), 3),
                })

triangle_df = pd.DataFrame(triangle_rows)
if len(triangle_df):
    triangle_df = triangle_df.merge(named_ann[['metabolite_id', 'metabolite_name', 'method']], on='metabolite_id', how='left')
    triangle_df = triangle_df.sort_values('min_abs_rho', ascending=False)
    triangle_df.to_csv(f'{OUT_DATA}/nb09c_cross_feeding_triangles.tsv', sep='\t', index=False)
    log_section('3', f'Cross-feeding-triangle candidates (same-sign, both |ρ|>0.20, both FDR<0.10): {len(triangle_df)}')
    log_section('3', f'\nTop 30 by min(|ρ_anchor|, |ρ_pathobiont|):\n')
    for _, r in triangle_df.head(30).iterrows():
        a_short = r['anchor'].replace(' (anchor)', '')
        p_short = r['pathobiont'].replace(' (pathobiont)', '')
        log_section('3', f"  {a_short} & {p_short:<15s}: {r['metabolite_name']:<40s}  ρ_a={r['rho_anchor']:+.3f}  ρ_p={r['rho_pathobiont']:+.3f}")
else:
    log_section('3', 'No cross-feeding-triangle candidates at strict thresholds.')


# ---------------------------------------------------------------------------
# §4. Curated cross-feeding metabolite panel (focused test)
# ---------------------------------------------------------------------------
log_section('4', '## §4. Direction-of-association profile for cross-feeding-relevant metabolites')

# Curated panel — biologically motivated metabolites for the cross-feeding hypothesis
# (the names must match the metabolite_name column exactly, lowercase comparison)
PANEL = {
    'SCFAs (fermentation products)': ['butyrate', 'propionate', 'acetate', 'valerate', 'hexanoate', 'isovalerate', 'isobutyrate'],
    'Lactate (cross-feeding intermediate)': ['lactate'],
    'Bile acids — primary tauro-conjugated (F. plautii substrate pool)': [
        'taurocholate', 'taurochenodeoxycholate', 'tauroursodeoxycholate',
        'tauro-alpha-muricholate/tauro-beta-muricholate', 'taurine',
    ],
    'Bile acids — secondary (F. plautii product pool)': [
        'deoxycholate', 'lithocholate', 'chenodeoxycholate', 'hyodeoxycholate/ursodeoxycholate',
        'ketodeoxycholate',
    ],
    'TMA / choline / carnitine (H. hathewayi metabolic products)': [
        'choline', 'trimethylamine-N-oxide', 'betaine', 'carnitine',
        'C16 carnitine', 'C18:1 carnitine', 'alpha-glycerophosphocholine',
    ],
    'Polyamines (CD-up pool)': ['putrescine', 'N1-acetylspermine', 'N-acetylputrescine', 'spermine', 'spermidine'],
    'Tryptophan / indole (gut-bacteria-mediated AA metabolism)': [
        'tryptophan', 'indole-3-propionate', 'indoleacetate',
    ],
}

# Map metabolite_name → metabolite_id (case-insensitive)
name_to_id = {}
for _, r in named_ann.iterrows():
    nm = str(r['metabolite_name']).lower().strip()
    name_to_id.setdefault(nm, []).append(r['metabolite_id'])


def get_corr_row(species, metab_name):
    """Return ρ for (species_label, metab_name); take strongest |ρ| if multiple methods."""
    metab_ids = name_to_id.get(metab_name.lower(), [])
    if not metab_ids:
        return None
    rhos = []
    for mid in metab_ids:
        if mid in rho_mat.columns:
            r = rho_mat.loc[species, mid] if species in rho_mat.index else np.nan
            f = fdr_mat.loc[species, mid] if species in fdr_mat.index else np.nan
            if not pd.isna(r):
                rhos.append((r, f, mid))
    if not rhos:
        return None
    # Take maximum |ρ|
    return max(rhos, key=lambda x: abs(x[0]))


panel_rows = []
SPECIES_ORDER = ['A. caccae (anchor)', 'B. nordii (anchor)',
                 'H. hathewayi (pathobiont)', 'F. plautii (pathobiont)',
                 'E. bolteae (pathobiont)', 'E. lenta (pathobiont)',
                 'M. gnavus (pathobiont)', 'E. coli (Tier-A core)']

for theme, mlist in PANEL.items():
    log_section('4', f'\n=== {theme} ===')
    for m in mlist:
        line = f'  {m:<50s}'
        for s in SPECIES_ORDER:
            res = get_corr_row(s, m)
            if res is None:
                line += '  --   '
            else:
                rho, fdr, mid = res
                marker = '*' if fdr < 0.10 else ' '
                line += f'  {rho:+.2f}{marker}'
                panel_rows.append({
                    'theme': theme,
                    'metabolite': m,
                    'species_label': s,
                    'metabolite_id': mid,
                    'rho': round(float(rho), 3),
                    'fdr': float(fdr),
                })
        log_section('4', line)
    log_section('4', '  ' + ' ' * 50 + '  '.join(['  ' + s.split()[0][:5] for s in SPECIES_ORDER]))

panel_df = pd.DataFrame(panel_rows)
panel_df.to_csv(f'{OUT_DATA}/nb09c_cross_feeding_panel.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §5. NB07c hypothesis disambiguation
# ---------------------------------------------------------------------------
log_section('5', '## §5. NB07c hypothesis: cross-feeding vs shared-environment')

log_section('5', '''
NB07c found A. caccae × pathobiont species-level coupling:
  E. bolteae    +0.39
  H. hathewayi  +0.33
  M. gnavus     +0.31
  F. plautii    +0.29
  E. lenta      +0.08

Cross-feeding hypothesis (a): pathobiont substrates -> A. caccae butyrate.
Shared-environment hypothesis (b): both respond to same CD niche.

Disambiguation criteria (NB09c):
  - Cross-feeding: A. caccae & pathobiont share same-sign correlation with
    a candidate intermediate (lactate, mucin glycans, bile-acid metabolites);
    OR butyrate (the A. caccae product) anti-correlates with pathobionts
    (negative feedback) — neither perfectly clean.
  - Shared-environment: many metabolites correlate with BOTH species in the
    same sign without specific cross-feeding metabolites being prominent.
''')

# Count cross-feeding triangles per (anchor, pathobiont)
log_section('5', '\nCross-feeding-triangle candidates per (anchor × pathobiont):')
if len(triangle_df):
    pair_counts = triangle_df.groupby(['anchor', 'pathobiont']).size().reset_index(name='n_metabolites')
    log_section('5', pair_counts.to_string(index=False))
else:
    log_section('5', '  (none at strict thresholds)')


# ---------------------------------------------------------------------------
# §6. Verdict + figure
# ---------------------------------------------------------------------------
log_section('6', '## §6. Verdict + figure')

# Verdict
n_butyrate_corr_aca = panel_df.loc[(panel_df['metabolite'] == 'butyrate') & (panel_df['species_label'] == 'A. caccae (anchor)'), 'rho'].mean() if 'butyrate' in panel_df['metabolite'].values else None
n_lactate_corr_aca = panel_df.loc[(panel_df['metabolite'] == 'lactate') & (panel_df['species_label'] == 'A. caccae (anchor)'), 'rho'].mean() if 'lactate' in panel_df['metabolite'].values else None

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB09c — sample-level cross-feeding disambiguation for NB07c hypothesis',
    'n_paired_samples': len(paired_codes),
    'n_metabolites_tested': int(m_mat.shape[1]),
    'n_species_tested': int(sp_mat.shape[1]),
    'n_cross_feeding_triangles_strict': int(len(triangle_df)),
    'butyrate_acaccae_rho': float(n_butyrate_corr_aca) if n_butyrate_corr_aca is not None else None,
    'lactate_acaccae_rho': float(n_lactate_corr_aca) if n_lactate_corr_aca is not None else None,
}

# Headline interpretation
if len(triangle_df) > 100:
    verdict['narrative'] = (
        'MANY cross-feeding-triangle candidates — predominantly shared-environment '
        'rather than specific cross-feeding (large numbers of metabolites correlate '
        'with both anchor and pathobiont in the same direction). Specific cross-feeding '
        'cannot be confidently inferred from sample-level correlation alone.'
    )
elif len(triangle_df) > 10:
    verdict['narrative'] = (
        'PARTIAL cross-feeding-triangle support — modest number of candidate '
        'intermediates with same-sign correlation between anchor and pathobiont. '
        'Specific intermediate biology (lactate / mucin / bile-acid) requires '
        'targeted follow-up.'
    )
else:
    verdict['narrative'] = (
        'WEAK cross-feeding-triangle support at strict thresholds. The NB07c '
        'species-level coupling does not strongly disambiguate from shared-environment.'
    )

with open(f'{OUT_DATA}/nb09c_cross_feeding_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('6', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §7. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Panel A: heatmap of curated panel ρ across species
ax = axes[0]
panel_pivot = panel_df.pivot_table(index='metabolite', columns='species_label', values='rho', aggfunc='mean')
panel_pivot = panel_pivot.reindex(columns=SPECIES_ORDER)
# Order rows by theme (preserve curated order)
ordered_metabs = []
for theme, mlist in PANEL.items():
    for m in mlist:
        if m in panel_pivot.index:
            ordered_metabs.append(m)
panel_pivot = panel_pivot.reindex(ordered_metabs)

import seaborn as sns
short_species = [s.replace(' (anchor)', '*A').replace(' (pathobiont)', '*P').replace(' (Tier-A core)', '*T') for s in SPECIES_ORDER]
sns.heatmap(panel_pivot, cmap='RdBu_r', center=0, vmin=-0.5, vmax=0.5, annot=True, fmt='.2f',
            cbar_kws={'label': 'Spearman ρ (paired)'}, ax=ax, xticklabels=short_species,
            annot_kws={'fontsize': 7})
ax.set_title('A. Curated cross-feeding panel × species ρ (paired CSM* HMP2)')
ax.set_xlabel('')
ax.set_ylabel('')
ax.tick_params(axis='y', labelsize=7)

# Panel B: triangle candidates summary — top 25 by min |ρ|
ax = axes[1]
if len(triangle_df) > 0:
    top_tri = triangle_df.head(25)
    y = np.arange(len(top_tri))
    ax.scatter(top_tri['rho_anchor'], y, color='#7fb069', label='ρ(anchor × m)', s=60, alpha=0.8)
    ax.scatter(top_tri['rho_pathobiont'], y, color='#e76f51', label='ρ(pathobiont × m)', s=60, alpha=0.8)
    for i, r in top_tri.reset_index(drop=True).iterrows():
        ax.plot([r['rho_anchor'], r['rho_pathobiont']], [i, i], color='gray', linewidth=0.5, alpha=0.5)
    labels = [f'{r.metabolite_name[:25]} ({r.anchor.split()[1]}/{r.pathobiont.split()[1]})' for r in top_tri.itertuples()]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_xlabel('Spearman ρ')
    ax.set_title(f'B. Top 25 cross-feeding-triangle candidates ({len(triangle_df)} total)')
    ax.legend(loc='lower right', fontsize=8)
else:
    ax.text(0.5, 0.5, 'No triangles at strict thresholds', ha='center', va='center')
    ax.set_title('B. Cross-feeding-triangle candidates: 0')

fig.suptitle('NB09c — Sample-level paired metabolomics × metagenomics: NB07c cross-feeding disambiguation', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB09c_cross_feeding_disambiguation.png', dpi=120, bbox_inches='tight')
log_section('6', f'\nWrote {OUT_FIG}/NB09c_cross_feeding_disambiguation.png')

with open('/tmp/nb09c_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone. Wrote /tmp/nb09c_section_logs.json + 3 data files + 1 figure.')
