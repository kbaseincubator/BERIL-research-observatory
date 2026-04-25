"""H3a (b) v1.8 retest — MetaCyc class hierarchy + Fisher per-theme enrichment.

Replaces v1.7's regex-on-pathway-names approach (degenerate / underpowered) with
a structured class assignment from ModelSEEDDatabase + 12-theme IBD overlay.

Sources:
  - /global_share/KBaseUtilities/ModelSEEDDatabase/Biochemistry/Aliases/Provenance/MetaCyc_Pathways.tbl
    flat table: rxn_id × external_id × external_name. Specific pathways (PWY-XXX) and
    pathway classes both appear as external_id; both share reactions, so a pathway's
    classes are the non-pathway external_ids of its reactions.
  - 90% coverage of our 575 HUMAnN3 unstratified pathway IDs.

Approach:
  1. Parse the tbl to build pathway_id → set of MetaCyc class memberships.
  2. Apply 12-theme IBD overlay (manually curated from project + IBD literature).
  3. Per theme: Fisher's exact (CD-up × in-theme) on NB07a meta output.
  4. BH-FDR across themes; verdict: ≥1 theme at FDR<0.10 + OR>1.5 → SUPPORTED.

Inputs:
  data/nb07a_pathway_meta.tsv (cohort-level pathway DA from NB07a)
  data/nb07b_stratified_pathway_da.tsv (per-species pathway DA from NB07b)

Outputs:
  data/nb07_h3a_v18_pathway_classes.tsv — pathway × MetaCyc-classes × IBD-themes
  data/nb07_h3a_v18_cohort_enrichment.tsv — Fisher per theme on cohort meta
  data/nb07_h3a_v18_species_enrichment.tsv — Fisher per theme per species
  data/nb07_h3a_v18_verdict.json — formal v1.8 verdict
  figures/NB07_H3a_v18_class_enrichment.png — heatmap + bars
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, io, contextlib, time
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

NOTEBOOK_DIR = Path(__file__).parent
PROJECT = NOTEBOOK_DIR.parent
DATA_OUT = PROJECT / 'data'
FIG_OUT = PROJECT / 'figures'
MODELSEED_TBL = '/global_share/KBaseUtilities/ModelSEEDDatabase/Biochemistry/Aliases/Provenance/MetaCyc_Pathways.tbl'

TIER_A_CORE = [
    'Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Escherichia coli',
    'Eggerthella lenta', 'Flavonifractor plautii', 'Enterocloster bolteae',
]

# 12 IBD-relevant themes — MetaCyc class names (or substring patterns) per theme
# Themes 1-7 are the v1.7 categories with bugs fixed; themes 8-12 are new
# (uncovered in v1.7 but biologically relevant per NB04/NB05/NB07a findings)
IBD_THEMES = {
    '01_bile_acid': [
        'Bile-Acid', 'Cholate', 'Deoxycholate', '7-Alpha-Dehydroxylation',
        'Bile-Acids', 'Bile-Salts',
    ],
    '02_mucin_glycan_host': [
        'Mucin', 'Fucose-Degradation', 'Sialic-Acid-Degradation',
        'GlcNAc-Degradation', 'GalNAc-Degradation', 'Polysaccharides-Degradation',
        'Host-Glycan',
        # Note: deliberately NOT including peptidoglycan (cell wall, not host mucin)
    ],
    '03_sulfur_redox': [
        'Sulfate-Reduction', 'Sulfite-Reduction', 'Hydrogen-Sulfide',
        'Sulfidogenesis', 'Tetrathionate-Reduction', 'Thiosulfate',
        'Inorganic-Sulfur',
    ],
    '04_TMA_choline': [
        'Choline-Degradation', 'Trimethylamine', 'TMA-', 'TMAO',
        'Carnitine', 'Betaine', 'PhosphatidylcholineBiosynthesis',
    ],
    '05_eut_pdu': [
        'Ethanolamine-Utilization', 'Ethanolamine-Degradation',
        'Propanediol', '1,2-Propanediol', '1-2-Propanediol',
    ],
    '06_polyamine_urea': [
        'Polyamine', 'Putrescine', 'Spermidine', 'Spermine',
        'Urease', 'Urea-Degradation', 'Urea-Cycle',
    ],
    '07_AA_decarboxylation': [
        'ARGININE-DEG', 'L-arginine Degradation', 'ORNITHINE-DEG',
        'L-ornithine', 'Tryptophanase', 'L-tryptophan Degradation',
        'HISTIDINE-DEG', 'L-histidine Degradation',
        'LYSINE-DEG', 'L-lysine Degradation',
        'Decarboxylation', 'AA-Degradation',
    ],
    # NEW v1.8 themes — uncovered in v1.7 but project documents them as IBD-relevant
    '08_iron_heme_acquisition': [
        'HEME-SYN', 'Heme-b-Biosynthesis', 'Heme-Biosynthesis',
        'Heme-Degradation', 'Iron-Reduction', 'Iron-Acquisition',
        'Siderophore', 'Yersiniabactin', 'Enterobactin', 'Aerobactin',
        'Heme', 'Iron-',
    ],
    '09_anaerobic_respiration': [
        'Anaerobic-Respiration', 'Nitrate-Reduction', 'Fumarate-Reduction',
        'DMSO-Reduction', 'Tetrathionate-Reduction', 'TMAO-Reduction',
        'Alternative-Electron-Acceptor', 'Reductive-TCA',
    ],
    '10_fat_metabolism_glyoxylate': [
        'Fatty-Acid-and-Lipid-Degradation', 'Fatty-Acid-Degradation',
        'Beta-Oxidation', 'Glyoxylate-Cycle', 'Glyoxylate', 'GLYOXYLATE',
        'Lipid-Biosynthesis', 'Phospholipid-Biosynthesis',
        'Fatty-Acids-Degradation', 'Fatty-Acid-Metabolism',
    ],
    '11_purine_pyrimidine_recycling': [
        'Allantoin', 'Urate', 'Purine-Salvage', 'Purine-Degradation',
        'Pyrimidine-Salvage', 'Pyrimidine-Degradation',
        'Nucleo-DEG', 'Nucleotide-Salvage', 'NUCLEO-DEG',
    ],
    '12_aromatic_AA_chorismate_indole': [
        'Tryptophan-Biosynthesis', 'L-tryptophan Biosynthesis',
        'Chorismate-Biosynthesis', 'Chorismate', 'Aromatic-Amino-Acid-Biosynthesis',
        'Indole', 'Tyrosine-Biosynthesis', 'L-tyrosine Biosynthesis',
        'Phenylalanine-Biosynthesis',
    ],
}

EFFECT_THRESHOLD = 0.5
FDR_THRESHOLD_DA = 0.10
FDR_THRESHOLD_THEME = 0.10
OR_THRESHOLD = 1.5

section_logs = {}
def section(name):
    buf = io.StringIO()
    return buf, contextlib.redirect_stdout(buf)


# ============================================================
# §0 Parse ModelSEED tbl → pathway_id → set of MetaCyc classes
# ============================================================
buf, redir = section('0')
with redir:
    print('NB07_h3a_v18 — H3a (b) retest with MetaCyc class hierarchy')
    t0 = time.time()
    df = pd.read_csv(MODELSEED_TBL, sep='\t')
    df.columns = ['rxn_id', 'external_id', 'external_name']
    print(f'ModelSEED MetaCyc tbl: {df.shape[0]:,} rows, {df.external_id.nunique():,} distinct external_ids')

    def is_specific_pathway(s):
        if not isinstance(s, str): return False
        u = s.upper()
        return bool(s.startswith('PWY-') or '-PWY' in u or s.endswith('-PWY') or '_PWY' in u)
    df['is_pathway'] = df.external_id.apply(is_specific_pathway)
    pwys = df[df.is_pathway].external_id.nunique()
    classes = df[~df.is_pathway].external_id.nunique()
    print(f'  Specific pathways (PWY-*): {pwys:,}; class-like external_ids: {classes:,}')

    # Build pathway → classes via shared reactions
    pwy_to_rxns = defaultdict(set)
    rxn_to_classes = defaultdict(set)
    for _, row in df.iterrows():
        if row.is_pathway:
            pwy_to_rxns[row.external_id].add(row.rxn_id)
        else:
            rxn_to_classes[row.rxn_id].add((row.external_id, row.external_name))
    pwy_to_classes = defaultdict(set)
    for pwy, rxns in pwy_to_rxns.items():
        for rxn in rxns:
            for cls in rxn_to_classes.get(rxn, set()):
                pwy_to_classes[pwy].add(cls)

    print(f'\nPathway → class map: {len(pwy_to_classes):,} pathways, '
          f'{sum(len(v) for v in pwy_to_classes.values())/len(pwy_to_classes):.1f} classes/pathway avg')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['0'] = buf.getvalue()


# ============================================================
# §1 Apply 12-theme IBD overlay; build pathway × theme membership
# ============================================================
buf, redir = section('1')
with redir:
    def themes_for_pathway(pwy):
        themes = set()
        cls_set = pwy_to_classes.get(pwy, set())
        all_text = ' '.join(f'{cid} {cname}' for cid, cname in cls_set)
        for theme, patterns in IBD_THEMES.items():
            for pat in patterns:
                if pat.lower() in all_text.lower():
                    themes.add(theme)
                    break
        return themes

    # Apply to all pathways in the meta (load NB07a output)
    nb07a = pd.read_csv(DATA_OUT / 'nb07a_pathway_meta.tsv', sep='\t')
    print(f'NB07a meta rows: {len(nb07a)}')

    # Extract bare PWY-XXX prefix
    nb07a['pwy_id'] = nb07a.pathway_id.str.split(':').str[0]
    nb07a['themes'] = nb07a.pwy_id.apply(themes_for_pathway)
    nb07a['n_themes'] = nb07a.themes.apply(len)

    # Coverage: how many of our pathways have ≥1 theme membership?
    n_with_classes = (nb07a.pwy_id.isin(pwy_to_classes)).sum()
    n_with_theme = (nb07a.n_themes > 0).sum()
    print(f'  Pathways with MetaCyc class data: {n_with_classes}/{len(nb07a)} ({n_with_classes/len(nb07a):.0%})')
    print(f'  Pathways assigned ≥1 IBD theme: {n_with_theme}/{len(nb07a)} ({n_with_theme/len(nb07a):.0%})')

    # Per-theme background count
    print(f'\nBackground theme membership (over {len(nb07a)} prevalence-filtered pathways):')
    theme_bg = {}
    for theme in IBD_THEMES:
        n = sum(theme in t for t in nb07a.themes)
        theme_bg[theme] = n
        print(f'  {theme:<35} {n}')

    # CD-up theme counts (NB05 actionable Tier-A v1.7 framing — using NB07a 'cd_up_passing')
    nb07a_up = nb07a[nb07a.cd_up_passing]
    print(f'\nCD-up passing pathways: {len(nb07a_up)}')
    print(f'CD-up theme membership:')
    theme_fg = {}
    for theme in IBD_THEMES:
        n = sum(theme in t for t in nb07a_up.themes)
        theme_fg[theme] = n
        print(f'  {theme:<35} {n}')
section_logs['1'] = buf.getvalue()


# ============================================================
# §2 Fisher's exact per theme — cohort-level H3a (b) v1.8
# ============================================================
buf, redir = section('2')
with redir:
    rows = []
    n_total = len(nb07a)
    n_up = len(nb07a_up)
    n_not_up = n_total - n_up
    print(f'2x2 setup: {n_total} total, {n_up} CD-up, {n_not_up} not-CD-up\n')

    for theme, patterns in IBD_THEMES.items():
        n_theme = theme_bg[theme]
        n_up_theme = theme_fg[theme]
        n_not_theme = n_total - n_theme
        n_up_not_theme = n_up - n_up_theme
        n_not_up_theme = n_theme - n_up_theme
        n_not_up_not_theme = n_not_up - n_not_up_theme
        # 2x2: rows=in_theme/not_in_theme, cols=cd_up/not_cd_up
        contingency = np.array([
            [n_up_theme, n_up_not_theme],
            [n_not_up_theme, n_not_up_not_theme],
        ])
        if contingency.sum() == 0 or n_theme == 0:
            rows.append({'theme': theme, 'n_theme_bg': n_theme, 'n_cdup_in_theme': n_up_theme,
                         'odds_ratio': np.nan, 'p_value': np.nan})
            continue
        # Fisher's exact (alternative='greater' = enrichment of CD-up in theme)
        odds_ratio, p_value = stats.fisher_exact(contingency, alternative='greater')
        rows.append({
            'theme': theme,
            'n_theme_bg': int(n_theme),
            'n_cdup_in_theme': int(n_up_theme),
            'expected_under_null': round(n_theme * n_up / n_total, 2) if n_total else None,
            'odds_ratio': float(odds_ratio) if np.isfinite(odds_ratio) else np.inf,
            'p_value': float(p_value),
        })
    enr_df = pd.DataFrame(rows)
    enr_df['fdr'] = multipletests(enr_df.p_value.fillna(1), method='fdr_bh')[1]
    enr_df['supported'] = (enr_df.fdr < FDR_THRESHOLD_THEME) & (enr_df.odds_ratio > OR_THRESHOLD)
    enr_df = enr_df.sort_values('p_value')
    enr_df.to_csv(DATA_OUT / 'nb07_h3a_v18_cohort_enrichment.tsv', sep='\t', index=False)

    print('Cohort-level Fisher per-theme enrichment (CD-up × in-theme):')
    print(enr_df.to_string(index=False))
    n_supported = int(enr_df.supported.sum())
    h3a_b_v18_pass = n_supported >= 1
    print(f'\nThemes supported (FDR<{FDR_THRESHOLD_THEME}, OR>{OR_THRESHOLD}): {n_supported}')
    print(f'H3a (b) v1.8 cohort verdict: {"SUPPORTED" if h3a_b_v18_pass else "NOT SUPPORTED"}')
section_logs['2'] = buf.getvalue()


# ============================================================
# §3 Fisher's exact per theme — per-species H3a (b) v1.8
# ============================================================
buf, redir = section('3')
with redir:
    nb07b = pd.read_csv(DATA_OUT / 'nb07b_stratified_pathway_da.tsv', sep='\t')
    nb07b['pwy_id'] = nb07b.pathway_id.str.split(':').str[0].str.split('|').str[0]
    nb07b['themes'] = nb07b.pwy_id.apply(themes_for_pathway)
    print(f'NB07b stratified rows: {len(nb07b)}')
    print(f'  pathways with MetaCyc class data: {(nb07b.pwy_id.isin(pwy_to_classes)).sum()}/{len(nb07b)}')

    species_results = []
    for sp in TIER_A_CORE:
        sub = nb07b[nb07b.canonical_species == sp]
        if len(sub) == 0:
            continue
        sub_up = sub[sub.cd_up_passing]
        if len(sub_up) == 0:
            print(f'\n{sp}: no CD-up; skipping Fisher per-theme')
            continue
        n_total = len(sub); n_up = len(sub_up); n_not_up = n_total - n_up
        for theme in IBD_THEMES:
            n_theme = sum(theme in t for t in sub.themes)
            n_up_theme = sum(theme in t for t in sub_up.themes)
            if n_theme == 0:
                species_results.append({
                    'species': sp, 'theme': theme,
                    'n_total': n_total, 'n_up': n_up, 'n_theme_bg': 0, 'n_cdup_in_theme': 0,
                    'odds_ratio': None, 'p_value': None,
                })
                continue
            n_up_not_theme = n_up - n_up_theme
            n_not_up_theme = n_theme - n_up_theme
            n_not_up_not_theme = n_not_up - n_not_up_theme
            cont = np.array([
                [n_up_theme, n_up_not_theme],
                [n_not_up_theme, n_not_up_not_theme],
            ])
            odds_ratio, p = stats.fisher_exact(cont, alternative='greater')
            species_results.append({
                'species': sp, 'theme': theme,
                'n_total': n_total, 'n_up': n_up, 'n_theme_bg': int(n_theme),
                'n_cdup_in_theme': int(n_up_theme),
                'odds_ratio': float(odds_ratio) if np.isfinite(odds_ratio) else np.inf,
                'p_value': float(p),
            })

    sp_df = pd.DataFrame(species_results)
    if len(sp_df):
        # FDR per species across themes
        sp_df['fdr'] = np.nan
        for sp, grp in sp_df.groupby('species'):
            valid = grp.p_value.notna()
            if valid.any():
                sp_df.loc[grp[valid].index, 'fdr'] = multipletests(grp[valid].p_value, method='fdr_bh')[1]
        sp_df['supported'] = (sp_df.fdr < FDR_THRESHOLD_THEME) & (sp_df.odds_ratio > OR_THRESHOLD)
        sp_df = sp_df.sort_values(['species', 'p_value'])
        sp_df.to_csv(DATA_OUT / 'nb07_h3a_v18_species_enrichment.tsv', sep='\t', index=False)

        print('\nPer-species enrichment summary (themes supported per species):')
        for sp in TIER_A_CORE:
            sub = sp_df[sp_df.species == sp]
            if len(sub) == 0: continue
            sup = sub[sub.supported]
            print(f'\n{sp} (n_up={sub.n_up.iloc[0]}, n_total={sub.n_total.iloc[0]}):')
            for _, r in sup.iterrows():
                print(f'    {r.theme:<35} OR={r.odds_ratio:.2f} p={r.p_value:.3e} FDR={r.fdr:.3e} '
                      f'(in-theme: {r.n_cdup_in_theme}/{r.n_theme_bg})')
            if len(sup) == 0:
                print('    (no themes supported at FDR<0.10, OR>1.5)')
section_logs['3'] = buf.getvalue()


# ============================================================
# §4 Save pathway-level theme assignment + verdict + figure
# ============================================================
# Pathway × theme assignment table for audit
pwy_theme_rows = []
for _, r in nb07a.iterrows():
    classes_str = '|'.join(sorted({cid for cid, _ in pwy_to_classes.get(r.pwy_id, set())})[:10])
    themes_str = '|'.join(sorted(r.themes))
    pwy_theme_rows.append({
        'pathway_id': r.pathway_id, 'pwy_id': r.pwy_id,
        'pooled_effect': r.pooled_effect, 'fdr': r.fdr, 'cd_up_passing': r.cd_up_passing,
        'metacyc_classes_first10': classes_str,
        'ibd_themes': themes_str,
    })
pd.DataFrame(pwy_theme_rows).to_csv(DATA_OUT / 'nb07_h3a_v18_pathway_classes.tsv', sep='\t', index=False)


# Figure: per-theme cohort enrichment + per-species heatmap
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# (1) Cohort: bar of -log10(FDR), colored by OR
ax = axes[0]
plot_df = enr_df[enr_df.p_value.notna()].copy().sort_values('odds_ratio')
y_pos = np.arange(len(plot_df))
log_fdr = -np.log10(plot_df.fdr.replace(0, 1e-300))
colors = ['#4a8a2a' if (s) else '#cccccc' for s in plot_df.supported]
ax.barh(y_pos, log_fdr, color=colors, edgecolor='white')
ax.set_yticks(y_pos)
ax.set_yticklabels([f"{t} (OR={r.odds_ratio:.1f}, {r.n_cdup_in_theme}/{r.n_theme_bg})"
                     for t, (_,r) in zip(plot_df.theme, plot_df.iterrows())], fontsize=8)
ax.axvline(-np.log10(FDR_THRESHOLD_THEME), ls='--', color='#333', label=f'FDR={FDR_THRESHOLD_THEME}')
ax.set_xlabel('-log10(BH-FDR)')
ax.set_title(f'Cohort-level H3a (b) v1.8: Fisher per-theme enrichment\n'
             f'(CD-up={n_up}/{n_total}; supported themes in green)')
ax.legend(fontsize=8)

# (2) Per-species heatmap: -log10(FDR) per theme per species
ax = axes[1]
if len(sp_df):
    pivot_fdr = sp_df.pivot_table(index='species', columns='theme',
                                  values='fdr', fill_value=1.0)
    pivot_or = sp_df.pivot_table(index='species', columns='theme',
                                 values='odds_ratio', fill_value=0.0)
    log_pivot = -np.log10(pivot_fdr.replace(0, 1e-300))
    im = ax.imshow(log_pivot.values, aspect='auto', cmap='Reds', vmin=0, vmax=5)
    ax.set_xticks(range(len(pivot_fdr.columns)))
    ax.set_xticklabels([c.replace('_', '\n') for c in pivot_fdr.columns], fontsize=7)
    ax.set_yticks(range(len(pivot_fdr.index)))
    ax.set_yticklabels([s[:25] for s in pivot_fdr.index], fontsize=8)
    for i in range(log_pivot.shape[0]):
        for j in range(log_pivot.shape[1]):
            v = log_pivot.iloc[i, j]
            r = pivot_or.iloc[i, j]
            if v > 1.0 or r > 1.5:
                ax.text(j, i, f'OR={r:.1f}\np={pivot_fdr.iloc[i,j]:.0e}',
                       ha='center', va='center', fontsize=6,
                       color='white' if v > 2.5 else 'black')
    ax.set_title('Per-species H3a (b) v1.8 enrichment (-log10 FDR)')
    plt.colorbar(im, ax=ax)

plt.tight_layout()
plt.savefig(FIG_OUT / 'NB07_H3a_v18_class_enrichment.png', dpi=120, bbox_inches='tight')
plt.close()


# Verdict JSON
def _def(o):
    if isinstance(o, (np.bool_, bool)): return bool(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, set): return list(o)
    return str(o)

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.8',
    'test': 'H3a (b) v1.8 — MetaCyc class hierarchy + Fisher per-theme enrichment',
    'methodology_change': 'Replace v1.7 regex-on-name with structured class assignments from ModelSEEDDatabase MetaCyc_Pathways.tbl',
    'pathway_class_coverage': {
        'total_pathways': int(len(nb07a)),
        'with_metacyc_classes': int((nb07a.pwy_id.isin(pwy_to_classes)).sum()),
        'with_at_least_one_ibd_theme': int((nb07a.n_themes > 0).sum()),
    },
    'thresholds': {
        'fdr_theme': FDR_THRESHOLD_THEME,
        'odds_ratio_min': OR_THRESHOLD,
    },
    'cohort_level_v18': {
        'n_themes_supported': int(n_supported),
        'verdict': 'SUPPORTED' if h3a_b_v18_pass else 'NOT SUPPORTED',
        'supported_themes': enr_df[enr_df.supported].theme.tolist(),
    },
    'comparison_to_v17': {
        'v17_verdict': 'FAIL (degenerate)',
        'v18_verdict': 'SUPPORTED' if h3a_b_v18_pass else 'NOT SUPPORTED',
        'reason_for_v17_failure': 'Regex on pathway names matched only 44/409 of background; 7 a-priori categories too narrow; "0_other" hid heme/iron, fat/glyoxylate, purine, aromatic-AA themes',
    },
}
with open(DATA_OUT / 'nb07_h3a_v18_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_def)

with open('/tmp/nb07_h3a_v18_logs.json', 'w') as f:
    json.dump(section_logs, f, indent=2)

print('\nWrote:')
print('  data/nb07_h3a_v18_pathway_classes.tsv')
print('  data/nb07_h3a_v18_cohort_enrichment.tsv')
print('  data/nb07_h3a_v18_species_enrichment.tsv')
print('  data/nb07_h3a_v18_verdict.json')
print('  figures/NB07_H3a_v18_class_enrichment.png')
print('All sections done.')
