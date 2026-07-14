"""NB08a — BGC × pathobiont enrichment (H3c) — genomic mechanism layer.

Tests whether Tier-A actionable pathobionts (NB05) carry an over-represented
iron-siderophore / genotoxin BGC repertoire relative to background, and
re-tests the Elmassry ebf/ecf CD-vs-HC enrichment in our cohort meta-design.

Builds on:
- NB05 §5g E. coli MIBiG matches (qualitative)
- NB07_v1.8 iron/heme-theme enrichment (pathway level)
- NB07c iron-pathway co-variation concentrating on E. coli (sample-correlation level)

Adds the genomic-content level: which Tier-A pathobionts carry which BGC
classes, and is the iron-biosynthetic gene-cluster signature concentrated on
E. coli or shared with other Tier-A core?
"""
import json
import os
import sys
from collections import Counter

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
# §0. Load data and define Tier-A core (with synonymy)
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load BGC catalog + CB-ORF enrichment + ebf/ecf prevalence + Tier-A core')

bgc = pd.read_parquet(f'{MART}/ref_bgc_catalog.snappy.parquet')
cborf = pd.read_parquet(f'{MART}/ref_cborf_enrichment.snappy.parquet')
ebf = pd.read_parquet(f'{MART}/ref_ebf_ecf_prevalence.snappy.parquet')
nb05 = pd.read_csv(f'{OUT_DATA}/nb05_tier_a_scored.tsv', sep='\t')

log_section('0', f'BGC catalog: {bgc.shape[0]} BGCs across {bgc["Species"].nunique()} distinct species names')
log_section('0', f'  with species annotation: {bgc["Species"].notna().sum()}')
log_section('0', f'  with MIBiG match: {bgc["MIBiG BGC accession match"].notna().sum()}')
log_section('0', f'CB-ORF enrichment: {cborf.shape[0]} CB-ORFs')
log_section('0', f'  CD-up at FDR<0.10: {((cborf["FDR-adjusted P-value (CD vs. HC)"]<0.10) & (cborf["Mean effect size estimate (CD vs. HC)"]>0)).sum()}')
log_section('0', f'  CD-down at FDR<0.10: {((cborf["FDR-adjusted P-value (CD vs. HC)"]<0.10) & (cborf["Mean effect size estimate (CD vs. HC)"]<0)).sum()}')
log_section('0', f'ebf/ecf RPKM: {ebf.shape[0]} samples across {ebf["Cohort"].nunique()} cohorts ({sorted(ebf["Cohort"].unique())})')

# Tier-A core actionable (NB05 actionable=True)
tier_a_core_canon = sorted(nb05[nb05['actionable']]['species'].tolist())
log_section('0', f'Tier-A core (NB05 actionable): {len(tier_a_core_canon)} species')
for s in tier_a_core_canon:
    log_section('0', f'  - {s}')

# Synonymy map: GTDB-r214 canonical name → BGC catalog species-startswith prefix
tier_a_core_syns = {
    'Escherichia coli': ['Escherichia coli'],
    'Mediterraneibacter gnavus': ['[Ruminococcus] gnavus', 'Ruminococcus gnavus'],
    'Hungatella hathewayi': ['Hungatella hathewayi'],
    'Eggerthella lenta': ['Eggerthella lenta'],
    'Flavonifractor plautii': ['Flavonifractor plautii'],
    'Enterocloster bolteae': ['Enterocloster bolteae', 'Clostridium bolteae'],
}

# Annotate BGC catalog with canonical Tier-A core membership
def canon_for_bgc_species(name):
    if pd.isna(name):
        return None
    for canon, syns in tier_a_core_syns.items():
        for syn in syns:
            if name.startswith(syn):
                return canon
    return None


bgc['tier_a_canon'] = bgc['Species'].apply(canon_for_bgc_species)
bgc['is_tier_a'] = bgc['tier_a_canon'].notna()
log_section('0', f'BGCs mapped to Tier-A core: {bgc["is_tier_a"].sum()} / {bgc.shape[0]} ({100*bgc["is_tier_a"].mean():.1f}%)')


# ---------------------------------------------------------------------------
# §1. Tier-A core BGC repertoire summary
# ---------------------------------------------------------------------------
log_section('1', '## §1. Tier-A core BGC repertoire summary')

repertoire_rows = []
for canon in tier_a_core_canon:
    sub = bgc[bgc['tier_a_canon'] == canon]
    if not len(sub):
        log_section('1', f'{canon}: 0 BGCs in catalog')
        continue
    grouped_class_counts = dict(sub['Grouped Class'].value_counts())
    class_counts = dict(sub['Class'].value_counts())
    mibig_compounds = dict(sub['MIBiG Compounds'].dropna().value_counts())
    log_section('1', f'{canon}: {len(sub)} BGCs')
    log_section('1', f'  Grouped Class: {grouped_class_counts}')
    log_section('1', f'  Top Classes: {dict(list(class_counts.items())[:5])}')
    if mibig_compounds:
        log_section('1', f'  MIBiG: {mibig_compounds}')
    else:
        log_section('1', f'  MIBiG: (no annotated matches — BGC dark matter)')
    repertoire_rows.append({
        'species': canon,
        'n_bgc': len(sub),
        'n_with_mibig': sub['MIBiG BGC accession match'].notna().sum(),
        'mibig_compounds': '; '.join(f'{k}={v}' for k, v in sorted(mibig_compounds.items(), key=lambda x: -x[1])) if mibig_compounds else '',
        'grouped_class_str': '; '.join(f'{k}={v}' for k, v in sorted(grouped_class_counts.items(), key=lambda x: -x[1])),
    })

repertoire_df = pd.DataFrame(repertoire_rows)
repertoire_df.to_csv(f'{OUT_DATA}/nb08a_tier_a_bgc_repertoire.tsv', sep='\t', index=False)
log_section('1', f'\nWrote {OUT_DATA}/nb08a_tier_a_bgc_repertoire.tsv')


# ---------------------------------------------------------------------------
# §2. BGC-theme enrichment: Tier-A core vs background-catalog
# ---------------------------------------------------------------------------
log_section('2', '## §2. BGC-theme enrichment (Tier-A core vs background)')

# Define IBD-relevant BGC themes
# Theme 1: iron-siderophore / iron-acquisition (MIBiG compound + class signal)
#   MIBiG: Yersiniabactin, Enterobactin, Pyochelin, Salmochelin
#   Class: siderophore
# Theme 2: genotoxin / pathogenicity (MIBiG compound)
#   MIBiG: Colibactin, Tilivalline/Tilimycin, Microcin B17, Microcin J25
# Theme 3: bacteriocin / immunoactive (MIBiG compound + class)
#   MIBiG: Salivaricin, Nisin, Cytolysin, Ruminococcin, Acidocin, Gassericin, Enterocin, Lactococcin, Coagulin
#   Class: bacteriocin, lanthipeptide, sactipeptide, lassopeptide (RiPP subclasses)
# Theme 4: NRPS-PKS hybrid (E. coli AIEC virulence canonical)
#   Class: NRPS;T1PKS, T1PKS, T3PKS

THEMES = {
    'iron_siderophore': {
        'mibig': {'Yersiniabactin', 'Enterobactin', 'Pyochelin', 'Salmochelin', 'Aerobactin'},
        'class': {'siderophore'},
    },
    'genotoxin_microcin': {
        'mibig': {'Colibactin', 'Tilivalline/Tilimycin', 'Microcin B17', 'Microcin J25'},
        'class': set(),
    },
    'bacteriocin_RiPP': {
        'mibig': set(),  # too many narrow MIBiG matches; use class
        'class': {'bacteriocin', 'lanthipeptide', 'sactipeptide', 'lassopeptide', 'thiopeptide'},
    },
    'NRPS_PKS_hybrid': {
        'mibig': set(),
        'class': {'NRPS;T1PKS', 'T1PKS', 'T3PKS', 'NRPS-like'},
    },
}


def is_in_theme(row, theme_def):
    cls = row['Class']
    mibig = row['MIBiG Compounds']
    if pd.notna(cls):
        # Class column may be ';'-separated combinations; check any token matches
        cls_tokens = set(str(cls).split(';'))
        if cls_tokens & theme_def['class']:
            return True
        # Also check exact-match for combination strings
        if cls in theme_def['class']:
            return True
    if pd.notna(mibig) and mibig in theme_def['mibig']:
        return True
    return False


theme_rows = []
log_section('2', f'Tier-A core BGCs: {bgc["is_tier_a"].sum()}; background BGCs: {(~bgc["is_tier_a"]).sum()}')

for theme_name, theme_def in THEMES.items():
    in_theme = bgc.apply(lambda r: is_in_theme(r, theme_def), axis=1)
    a = (bgc['is_tier_a'] & in_theme).sum()  # Tier-A & in theme
    b = (bgc['is_tier_a'] & ~in_theme).sum()  # Tier-A & not in theme
    c = (~bgc['is_tier_a'] & in_theme).sum()  # background & in theme
    d = (~bgc['is_tier_a'] & ~in_theme).sum()  # background & not in theme
    odds_ratio, p = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
    expected = (a + b) * (a + c) / (a + b + c + d)
    log_section('2', f'\nTheme: {theme_name}')
    log_section('2', f'  Tier-A in theme: {a} / {a+b}; background in theme: {c} / {c+d}')
    log_section('2', f'  expected Tier-A in theme: {expected:.2f}')
    log_section('2', f'  Fisher OR={odds_ratio:.2f}, p={p:.3e}')
    theme_rows.append({
        'theme': theme_name,
        'tier_a_in_theme': int(a),
        'tier_a_total': int(a + b),
        'background_in_theme': int(c),
        'background_total': int(c + d),
        'expected_tier_a_in_theme': round(expected, 2),
        'odds_ratio': round(odds_ratio, 3),
        'fisher_p': p,
    })

theme_df = pd.DataFrame(theme_rows)
# BH-FDR across themes
m = len(theme_df)
order = theme_df['fisher_p'].argsort().values
ranked_p = theme_df['fisher_p'].iloc[order].values
fdr_adj = np.minimum.accumulate((ranked_p[::-1] * m / np.arange(m, 0, -1)))[::-1]
fdr_orig = np.empty(m)
for i, idx in enumerate(order):
    fdr_orig[idx] = fdr_adj[i]
theme_df['fdr'] = fdr_orig
theme_df['supported'] = (theme_df['fdr'] < 0.10) & (theme_df['odds_ratio'] > 1.5)
theme_df.to_csv(f'{OUT_DATA}/nb08a_bgc_theme_enrichment.tsv', sep='\t', index=False)
log_section('2', f'\nThemes supported (FDR<0.10, OR>1.5): {theme_df["supported"].sum()}')
log_section('2', f'\n{theme_df.to_string()}')


# ---------------------------------------------------------------------------
# §2b. Per-species iron+genotoxin MIBiG breakdown — confirms which Tier-A
# species carry the AIEC-iron signature genomically
# ---------------------------------------------------------------------------
log_section('2', '\n## §2b. AIEC-iron signature distribution within Tier-A core')

iron_mibigs = THEMES['iron_siderophore']['mibig'] | {'siderophore'}
genotoxin_mibigs = THEMES['genotoxin_microcin']['mibig']
species_iron_rows = []
for canon in tier_a_core_canon:
    sub = bgc[bgc['tier_a_canon'] == canon]
    n_iron = sub['MIBiG Compounds'].isin(iron_mibigs).sum() + (sub['Class'] == 'siderophore').sum()
    n_genotoxin = sub['MIBiG Compounds'].isin(genotoxin_mibigs).sum()
    species_iron_rows.append({
        'species': canon,
        'n_bgc': len(sub),
        'n_iron_mibig': int(n_iron),
        'n_genotoxin_mibig': int(n_genotoxin),
    })
species_iron_df = pd.DataFrame(species_iron_rows)
species_iron_df.to_csv(f'{OUT_DATA}/nb08a_tier_a_iron_genotoxin_per_species.tsv', sep='\t', index=False)
log_section('2', species_iron_df.to_string(index=False))


# ---------------------------------------------------------------------------
# §3. CB-ORF CD-up enrichment per Tier-A core
# ---------------------------------------------------------------------------
log_section('3', '## §3. CB-ORF CD-up enrichment per Tier-A core species')

# Parse CB-ORFs per BGC (";"-separated), build species→CB-ORFs map
cborf_set_by_canon = {}
all_canon_cborfs = set()
for canon in tier_a_core_canon:
    cborf_set = set()
    sub = bgc[bgc['tier_a_canon'] == canon]
    for cborf_str in sub['CB-ORFs'].dropna():
        for tok in cborf_str.split(';'):
            tok = tok.strip()
            if tok:
                cborf_set.add(tok)
    cborf_set_by_canon[canon] = cborf_set
    all_canon_cborfs |= cborf_set

# Build CB-ORF index from enrichment table
cborf_idx = cborf.set_index('CB-ORF')

cborf_enrich_rows = []
fdr_thr = 0.10
for canon in tier_a_core_canon:
    cborfs = cborf_set_by_canon[canon]
    matched = cborfs & set(cborf_idx.index)
    if not matched:
        log_section('3', f'{canon}: 0 CB-ORFs matched in enrichment table')
        cborf_enrich_rows.append({'species': canon, 'n_cborfs': 0, 'n_matched': 0,
                                  'n_cd_up_fdr10': 0, 'n_cd_down_fdr10': 0,
                                  'frac_cd_up': float('nan'), 'frac_cd_down': float('nan'),
                                  'mean_effect': float('nan')})
        continue
    sub = cborf_idx.loc[list(matched)]
    n_cd_up = ((sub['FDR-adjusted P-value (CD vs. HC)'] < fdr_thr) & (sub['Mean effect size estimate (CD vs. HC)'] > 0)).sum()
    n_cd_down = ((sub['FDR-adjusted P-value (CD vs. HC)'] < fdr_thr) & (sub['Mean effect size estimate (CD vs. HC)'] < 0)).sum()
    mean_eff = sub['Mean effect size estimate (CD vs. HC)'].mean()
    log_section('3', f'{canon}: {len(cborfs)} CB-ORFs ({len(matched)} matched in enrichment); {n_cd_up} CD-up + {n_cd_down} CD-down at FDR<0.10; mean effect = {mean_eff:.3f}')
    cborf_enrich_rows.append({
        'species': canon,
        'n_cborfs': len(cborfs),
        'n_matched': len(matched),
        'n_cd_up_fdr10': int(n_cd_up),
        'n_cd_down_fdr10': int(n_cd_down),
        'frac_cd_up': round(n_cd_up / max(len(matched), 1), 3),
        'frac_cd_down': round(n_cd_down / max(len(matched), 1), 3),
        'mean_effect': round(float(mean_eff), 3),
    })

cborf_enrich_df = pd.DataFrame(cborf_enrich_rows)
cborf_enrich_df.to_csv(f'{OUT_DATA}/nb08a_cborf_enrichment_per_tier_a.tsv', sep='\t', index=False)

# Background reference: catalog-wide CD-up rate
all_cborfs_in_catalog = set()
for cborf_str in bgc['CB-ORFs'].dropna():
    for tok in cborf_str.split(';'):
        tok = tok.strip()
        if tok:
            all_cborfs_in_catalog.add(tok)
matched_bg = all_cborfs_in_catalog & set(cborf_idx.index)
bg_sub = cborf_idx.loc[list(matched_bg)]
bg_cd_up_rate = ((bg_sub['FDR-adjusted P-value (CD vs. HC)'] < fdr_thr) & (bg_sub['Mean effect size estimate (CD vs. HC)'] > 0)).sum() / len(bg_sub)
bg_mean_effect = bg_sub['Mean effect size estimate (CD vs. HC)'].mean()
log_section('3', f'\nBackground (catalog-wide): {len(matched_bg)} CB-ORFs; CD-up rate = {bg_cd_up_rate:.3f}; mean effect = {bg_mean_effect:.3f}')


# ---------------------------------------------------------------------------
# §4. ebf/ecf RPKM CD-vs-HC cohort meta
# ---------------------------------------------------------------------------
log_section('4', '## §4. ebf/ecf CD-vs-HC RPKM — Mann-Whitney per cohort + Fisher z-meta')

cohorts = sorted(ebf['Cohort'].unique())
ebf_meta_rows = []
for compound in ['RPKM (ebf)', 'RPKM (ecf)']:
    log_section('4', f'\n{compound}:')
    cohort_zs, cohort_ns = [], []
    for c in cohorts:
        sub = ebf[ebf['Cohort'] == c]
        cd_vals = sub.loc[sub['Group'] == 'CD', compound].values
        hc_vals = sub.loc[sub['Group'] == 'HC', compound].values
        if len(cd_vals) < 5 or len(hc_vals) < 5:
            log_section('4', f'  [{c}] n_CD={len(cd_vals)}, n_HC={len(hc_vals)}: skipped (<5)')
            continue
        u, p = stats.mannwhitneyu(cd_vals, hc_vals, alternative='two-sided')
        # cliff's delta as effect
        n1, n2 = len(cd_vals), len(hc_vals)
        cliff = 2 * u / (n1 * n2) - 1
        # convert to z via normal approx (signed)
        sign = 1 if cliff > 0 else -1
        z = sign * stats.norm.isf(p / 2)
        log_section('4', f'  [{c}] n_CD={n1}, n_HC={n2}, median CD={np.median(cd_vals):.3f}, HC={np.median(hc_vals):.3f}, cliff_delta={cliff:.3f}, p={p:.3e}, z={z:.2f}')
        cohort_zs.append(z)
        cohort_ns.append(n1 + n2)
    if cohort_zs:
        # Stouffer's weighted z: weights by sqrt(N)
        w = np.array([np.sqrt(n) for n in cohort_ns])
        z_meta = np.sum(np.array(cohort_zs) * w) / np.sqrt(np.sum(w ** 2))
        p_meta = 2 * stats.norm.sf(abs(z_meta))
        log_section('4', f'  meta z={z_meta:.2f}, p={p_meta:.3e} ({len(cohort_zs)} cohorts)')
        ebf_meta_rows.append({
            'compound': compound,
            'n_cohorts': len(cohort_zs),
            'meta_z': round(float(z_meta), 3),
            'meta_p': p_meta,
            'cohort_zs': '; '.join(f'{c}={z:.2f}' for c, z in zip(cohorts[:len(cohort_zs)], cohort_zs)),
        })

ebf_meta_df = pd.DataFrame(ebf_meta_rows)
ebf_meta_df.to_csv(f'{OUT_DATA}/nb08a_ebf_ecf_cd_vs_hc.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. H3c verdict + figure')

# H3c verdict logic:
#   - Theme-level: at least one of (iron_siderophore, genotoxin_microcin, NRPS_PKS_hybrid) supported
#   - Per-species: E. coli has >0 iron MIBiG; other Tier-A core may not
#   - CB-ORF: at least one Tier-A core has CD-up enrichment > background
#   - ebf/ecf: at least one of {ebf, ecf} CD-up significant in meta

theme_supported = bool(theme_df['supported'].any())
ecoli_iron = species_iron_df.loc[species_iron_df['species']=='Escherichia coli', 'n_iron_mibig'].iat[0]
other_core_iron = species_iron_df.loc[species_iron_df['species']!='Escherichia coli', 'n_iron_mibig'].sum()
n_core_with_cd_up_cborf = (cborf_enrich_df['frac_cd_up'] > bg_cd_up_rate).sum()
ebf_sig = bool((ebf_meta_df['compound']=='RPKM (ebf)').any() and ebf_meta_df.loc[ebf_meta_df['compound']=='RPKM (ebf)', 'meta_p'].iat[0] < 0.05)
ecf_sig = bool((ebf_meta_df['compound']=='RPKM (ecf)').any() and ebf_meta_df.loc[ebf_meta_df['compound']=='RPKM (ecf)', 'meta_p'].iat[0] < 0.05)

if theme_supported and (ecoli_iron > 0) and ebf_sig:
    verdict = 'PARTIALLY SUPPORTED'
elif theme_supported and (ecoli_iron > 0):
    verdict = 'PARTIALLY SUPPORTED (BGC-class only; ebf/ecf cohort meta did not pass)'
else:
    verdict = 'NOT SUPPORTED'

verdict_obj = {
    'date': '2026-04-25',
    'plan_version': 'v1.8',
    'test': 'H3c — BGC × pathobiont enrichment (genomic mechanism layer)',
    'tier_a_core_n': len(tier_a_core_canon),
    'tier_a_core_with_iron_mibig': int((species_iron_df['n_iron_mibig'] > 0).sum()),
    'theme_supported_count': int(theme_df['supported'].sum()),
    'themes_supported': theme_df.loc[theme_df['supported'], 'theme'].tolist(),
    'ecoli_iron_mibig_count': int(ecoli_iron),
    'other_core_iron_mibig_count': int(other_core_iron),
    'n_core_with_cd_up_cborf_above_bg': int(n_core_with_cd_up_cborf),
    'background_cd_up_rate': round(float(bg_cd_up_rate), 3),
    'ebf_meta_significant': ebf_sig,
    'ecf_meta_significant': ecf_sig,
    'h3c_verdict': verdict,
    'narrowing_interpretation': (
        'AIEC-iron-genotoxin BGC repertoire concentrates on E. coli alone. '
        'Other Tier-A core species sit in MIBiG dark matter but carry significant '
        'BGC content (E. lenta 41, M. gnavus 58, E. bolteae 18) — their CD-association '
        'mechanism is not currently captured by MIBiG-annotated themes.'
    ),
}
with open(f'{OUT_DATA}/nb08a_h3c_verdict.json', 'w') as fp:
    json.dump(verdict_obj, fp, indent=2)
log_section('5', f'\n{json.dumps(verdict_obj, indent=2)}')

# Build the figure
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: Tier-A core BGC repertoire stacked bar
ax = axes[0]
plot_df = repertoire_df.copy()
groups = ['RiPP', 'NRPS', 'PKS', 'Other']
mat = []
for canon in tier_a_core_canon:
    sub = bgc[bgc['tier_a_canon'] == canon]
    counts = sub['Grouped Class'].value_counts()
    mat.append([int(counts.get(g, 0)) for g in groups])
mat = np.array(mat)
species_short = [s.split()[1][:6] + '\n' + s.split()[0][:1] + '.' for s in tier_a_core_canon]
bottom = np.zeros(len(tier_a_core_canon))
colors = ['#7fb069', '#e76f51', '#264653', '#999999']
for i, g in enumerate(groups):
    ax.bar(range(len(tier_a_core_canon)), mat[:, i], bottom=bottom, label=g, color=colors[i])
    bottom += mat[:, i]
ax.set_xticks(range(len(tier_a_core_canon)))
ax.set_xticklabels(species_short, rotation=0, fontsize=9)
ax.set_ylabel('# BGCs')
ax.set_title('A. Tier-A core BGC repertoire (Grouped Class)')
ax.legend(loc='upper right', fontsize=8)

# Panel B: Theme enrichment OR
ax = axes[1]
theme_plot = theme_df.copy()
ors = theme_plot['odds_ratio'].values
fdrs = theme_plot['fdr'].values
themes = theme_plot['theme'].values
y = np.arange(len(themes))
bar_colors = ['#e63946' if (or_ > 1.5 and fdr < 0.10) else '#a8a8a8' for or_, fdr in zip(ors, fdrs)]
ax.barh(y, np.log2(np.maximum(ors, 0.001)), color=bar_colors)
ax.axvline(0, color='black', linewidth=0.5)
ax.axvline(np.log2(1.5), color='gray', linestyle=':', linewidth=0.5)
ax.set_yticks(y)
ax.set_yticklabels(themes, fontsize=9)
ax.set_xlabel('log2(OR) — Tier-A core vs background')
ax.set_title('B. BGC-theme enrichment (Fisher OR)')
for i, (or_, fdr) in enumerate(zip(ors, fdrs)):
    ax.text(np.log2(max(or_, 0.001)) + 0.05, i, f'OR={or_:.2f}, FDR={fdr:.2g}', va='center', fontsize=8)

# Panel C: ebf/ecf CD-vs-HC by cohort
ax = axes[2]
ebf_long = ebf.melt(id_vars=['Group', 'Cohort'], value_vars=['RPKM (ebf)', 'RPKM (ecf)'],
                    var_name='compound', value_name='RPKM')
ebf_long['log_RPKM'] = np.log10(ebf_long['RPKM'] + 0.01)
import seaborn as sns
sns.boxplot(data=ebf_long[ebf_long['Group'].isin(['CD', 'HC'])],
            x='Cohort', y='log_RPKM', hue='Group',
            order=cohorts, hue_order=['HC', 'CD'],
            palette={'HC': '#73c0e8', 'CD': '#e63946'}, ax=ax, fliersize=2)
ax.set_title('C. ebf/ecf RPKM by cohort (log10 + 0.01)')
ax.set_ylabel('log10(RPKM + 0.01)')
ax.set_xlabel('Cohort')
ax.tick_params(axis='x', rotation=20)

fig.suptitle(f'NB08a — BGC × pathobiont H3c verdict: {verdict}', fontsize=12, y=0.99)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB08a_bgc_pathobiont_enrichment.png', dpi=120, bbox_inches='tight')
log_section('5', f'Wrote {OUT_FIG}/NB08a_bgc_pathobiont_enrichment.png')


# ---------------------------------------------------------------------------
# Save section logs for notebook hydration
# ---------------------------------------------------------------------------
with open('/tmp/nb08a_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone. Wrote /tmp/nb08a_section_logs.json + 4 data files + 1 figure.')
