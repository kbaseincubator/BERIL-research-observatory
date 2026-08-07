"""
Genome-size scaling diagnostic (Adam Arkin, 2026-08-06 feedback).

For each of the 20 KEGG landscape categories:
  1. Reconstruct genus-level KO count = ko_per_mb * mean_genome_mb
  2. Fit log(count) ~ log(genome_size) to get scaling exponent a
  3. Compute (1 - a): how much of category density variation is genome-size-driven

Then regress PGLS β (from NB18 landscape) against (1 - a).
If R² > ~0.7, the landscape gradient is genome-size scaling, not biology.
"""

import sys
sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

PROJ = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
DATA = PROJ / 'data'
FIGS = PROJ / 'figures'

# ── Load genus-level genome size data ─────────────────────────────────────────
# IMPORTANT: restrict to genera in the PGLS analysis (bacteria with niche breadth
# data). The full genus set (8,257 genera incl. archaea) gives very different
# scaling exponents than the PGLS subset (1,574 bacteria).
pgls_input = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
pgls_genera = set(pgls_input['genus_lower'].dropna().str.strip())
print(f'PGLS genera: {len(pgls_genera)}')

genus_size = pd.read_csv(DATA / '01_genus_ko_density_spark.csv')
genus_size = genus_size[['genus_lower', 'mean_genome_mb', 'n_ko_primary']].dropna()
genus_size['genus_lower'] = genus_size['genus_lower'].str.strip()
genus_size = genus_size[genus_size['mean_genome_mb'] > 0]
# Restrict to PGLS genera
genus_size = genus_size[genus_size['genus_lower'].isin(pgls_genera)]
print(f'genus_size after PGLS restriction: {len(genus_size)} rows')

# ── Category → landscape file mapping ─────────────────────────────────────────
CATEGORIES = [
    ('Amino acid metabolism',             'landscape_aa_metab_density.csv'),
    ('Replication & repair',              'landscape_replication_repair_density.csv'),
    ('Nucleotide metabolism',             'landscape_nucleotide_metab_density.csv'),
    ('Cofactor & vitamin biosyn.',        'landscape_cofactor_vitamin_density.csv'),
    ('Translation',                       'landscape_translation_density.csv'),
    ('Protein folding',                   'landscape_protein_folding_density.csv'),
    ('Secondary metabolism',              'landscape_secondary_metab_density.csv'),
    ('Metal genes (primary set, 140 KO)', None),   # use n_ko_primary directly
    ('Transcription',                     'landscape_transcription_density.csv'),
    ('Carbohydrate metabolism',           'landscape_carbohydrate_metab_density.csv'),
    ('Lipid metabolism',                  'landscape_lipid_metab_density.csv'),
    ('Xenobiotics metabolism',            'landscape_xenobiotics_density.csv'),
    ('Terpenoid/polyketide',              'landscape_terpenoid_polyket_density.csv'),
    ('Quorum sensing',                    'landscape_quorum_sensing_density.csv'),
    ('ABC transporters',                  'landscape_abc_transporters_density.csv'),
    ('Glycan biosynthesis',               'landscape_glycan_biosyn_density.csv'),
    ('Energy metabolism',                 'landscape_energy_metab_density.csv'),
    ('Cell motility',                     'landscape_cell_motility_density.csv'),
    ('AMR genes',                         'landscape_amr_density.csv'),
    ('Two-component systems',             'landscape_two_component_density.csv'),
]

# ── Load PGLS β values ─────────────────────────────────────────────────────────
ranking = pd.read_csv(DATA / 'kegg_category_pgls_ranking_updated.csv')
beta_map = dict(zip(ranking['category'], ranking['beta']))

# ── Compute scaling exponents ──────────────────────────────────────────────────
results = []

for cat, fname in CATEGORIES:
    beta = beta_map.get(cat)
    if beta is None:
        print(f'WARNING: no β for {cat}')
        continue

    if fname is None:
        # Metal genes: use n_ko_primary directly
        df = genus_size[['genus_lower', 'mean_genome_mb', 'n_ko_primary']].copy()
        df = df[(df['mean_genome_mb'] > 0) & (df['n_ko_primary'] > 0)].dropna()
        log_count = np.log(df['n_ko_primary'].values)
        log_size  = np.log(df['mean_genome_mb'].values)
        n = len(df)
    else:
        ldf = pd.read_csv(DATA / fname)
        ldf['genus_lower'] = ldf['genus_lower'].astype(str).str.strip()
        ldf = ldf[(ldf['genus_lower'] != '') & (ldf['genus_lower'] != 'nan')]
        ldf = ldf[ldf['ko_per_mb'] > 0].dropna(subset=['ko_per_mb'])

        merged = ldf.merge(genus_size[['genus_lower', 'mean_genome_mb']],
                           on='genus_lower', how='inner')
        merged['ko_count'] = merged['ko_per_mb'] * merged['mean_genome_mb']
        merged = merged[(merged['ko_count'] > 0) & (merged['mean_genome_mb'] > 0)]

        log_count = np.log(merged['ko_count'].values)
        log_size  = np.log(merged['mean_genome_mb'].values)
        n = len(merged)

    if n < 30:
        print(f'WARNING: only {n} genera for {cat}; skipping')
        continue

    slope, intercept, r, p, se = stats.linregress(log_size, log_count)

    results.append({
        'category':      cat,
        'beta':          beta,
        'a':             slope,
        'one_minus_a':   1 - slope,
        'n_genera':      n,
        'scaling_r2':    r ** 2,
        'scaling_p':     p,
    })
    print(f'{cat:42s}  β={beta:+.4f}  a={slope:.3f}  (1-a)={1-slope:.3f}  '
          f'n={n}  scaling_R²={r**2:.3f}')

results_df = pd.DataFrame(results)
results_df.to_csv(DATA / 'genome_size_scaling_diagnostic.csv', index=False)

# ── Diagnostic regression: β ~ (1 - a) ────────────────────────────────────────
x = results_df['one_minus_a'].values
y = results_df['beta'].values

slope_d, intercept_d, r_d, p_d, _ = stats.linregress(x, y)
r2_d = r_d ** 2

print(f'\n{"="*60}')
print(f'DIAGNOSTIC RESULT')
print(f'  β ~ (1 - a):  R² = {r2_d:.3f},  p = {p_d:.4f}')
print(f'  Slope = {slope_d:.4f},  Intercept = {intercept_d:.4f}')
if r2_d > 0.7:
    print('  *** R² > 0.7 — genome-size scaling dominates the landscape ***')
elif r2_d > 0.4:
    print('  *** R² 0.4–0.7 — genome-size is a substantial contributor ***')
else:
    print('  *** R² < 0.4 — genome-size NOT the primary driver ***')
print(f'{"="*60}')

# ── Plot ───────────────────────────────────────────────────────────────────────
# Short labels for the scatter
LABELS = {
    'Amino acid metabolism':             'AA metab',
    'Replication & repair':              'Replication',
    'Nucleotide metabolism':             'Nucleotide',
    'Cofactor & vitamin biosyn.':        'Cofactor',
    'Translation':                       'Translation',
    'Protein folding':                   'Prot. folding',
    'Secondary metabolism':              'Secondary',
    'Metal genes (primary set, 140 KO)': 'Metal genes',
    'Transcription':                     'Transcription',
    'Carbohydrate metabolism':           'Carbohydrate',
    'Lipid metabolism':                  'Lipid',
    'Xenobiotics metabolism':            'Xenobiotics',
    'Terpenoid/polyketide':              'Terpenoid',
    'Quorum sensing':                    'Quorum sens.',
    'ABC transporters':                  'ABC transport',
    'Glycan biosynthesis':               'Glycan',
    'Energy metabolism':                 'Energy',
    'Cell motility':                     'Motility',
    'AMR genes':                         'AMR',
    'Two-component systems':             'Two-comp.',
}

fig, axs = plt.subplots(1, 2, figsize=(FIGW['2col'], ROW_H))

# ── Left panel: scatter β vs (1 - a) ──────────────────────────────────────────
ax = axs[0]
is_metal = results_df['category'] == 'Metal genes (primary set, 140 KO)'

ax.scatter(results_df.loc[~is_metal, 'one_minus_a'],
           results_df.loc[~is_metal, 'beta'],
           color=PALETTE[0], s=30, zorder=3, edgecolor='k', linewidth=0.4)
ax.scatter(results_df.loc[is_metal, 'one_minus_a'],
           results_df.loc[is_metal, 'beta'],
           color=PALETTE[2], s=50, zorder=4, edgecolor='k', linewidth=0.6,
           label='Metal genes')

# Fit line
x_fit = np.linspace(x.min() - 0.05, x.max() + 0.05, 100)
ax.plot(x_fit, slope_d * x_fit + intercept_d,
        color='gray', lw=0.8, ls='--', zorder=2)

# Annotate R²
ax.annotate(f'$R^2 = {r2_d:.2f}$\n$p = {p_d:.3f}$',
            xy=(0.05, 0.95), xycoords='axes fraction',
            ha='left', va='top', fontsize=8, color='#808080')

# Label key points
label_cats = {'Metal genes (primary set, 140 KO)', 'Replication & repair',
              'Two-component systems', 'AMR genes', 'Translation',
              'Amino acid metabolism', 'Transcription'}
for _, row in results_df.iterrows():
    if row['category'] in label_cats:
        lbl = LABELS.get(row['category'], row['category'])
        # Adjust nudge for crowded points
        xoff = 4 if row['one_minus_a'] < 0.9 else -4
        ha   = 'left' if xoff > 0 else 'right'
        ax.annotate(lbl, xy=(row['one_minus_a'], row['beta']),
                    xytext=(xoff, 0), textcoords='offset points',
                    fontsize=6.5, va='center', ha=ha)

# Annotate the key anomaly: Translation has the lowest a (most invariant)
# but is NOT the most negative beta — contradicts pure genome-size artifact
transl = results_df[results_df['category'] == 'Translation'].iloc[0]
ax.annotate('Most invariant\n(a=0.037) but\nnot most negative β',
            xy=(transl['one_minus_a'], transl['beta']),
            xytext=(-35, -18), textcoords='offset points',
            fontsize=6, color=PALETTE[3],
            arrowprops=dict(arrowstyle='->', color=PALETTE[3], lw=0.7))

ax.axhline(0, color='gray', lw=0.8, ls='--')
ax.set_xlabel('Genome-size sensitivity (1 − scaling exponent $a$)')
ax.set_ylabel('PGLS β (niche breadth ~ gene density)')
ax.set_title('Genome-size scaling diagnostic')

# ── Right panel: bar chart of scaling exponents by category ───────────────────
ax2 = axs[1]
row_sorted = results_df.sort_values('a')
colors = [PALETTE[2] if c == 'Metal genes (primary set, 140 KO)' else PALETTE[0]
          for c in row_sorted['category']]
bars = ax2.barh(range(len(row_sorted)), row_sorted['a'],
                color=colors, edgecolor='k', linewidth=0.5, height=0.7)
ax2.set_yticks(range(len(row_sorted)))
ax2.set_yticklabels([LABELS.get(c, c) for c in row_sorted['category']], fontsize=7)
ax2.axvline(1, color='gray', lw=0.8, ls='--')
ax2.axvline(0, color='k', lw=0.4)
ax2.set_xlabel('Scaling exponent $a$  [log(KO count) ~ log(genome size)]')
ax2.set_title('Gene count scaling with genome size')
ax2.annotate('a = 1: density stays constant\na = 0: invariant count',
             xy=(0.98, 0.02), xycoords='axes fraction',
             ha='right', va='bottom', fontsize=7, color='#808080')

fig.suptitle('Do genome-size scaling artifacts explain the landscape gradient?',
             y=1.02)
plt.tight_layout()
save(fig, FIGS / 'fig_genome_size_scaling_diagnostic')
print(f'\nFigure saved to {FIGS / "fig_genome_size_scaling_diagnostic.pdf"}')
