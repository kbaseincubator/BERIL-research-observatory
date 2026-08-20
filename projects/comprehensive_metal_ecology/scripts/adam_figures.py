"""
Adam Arkin PI update figures — metal resistance vs metabolism story.
Generates 4 PDFs in projects/comprehensive_metal_ecology/figures/
"""
import sys
sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H, grid_h

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from statsmodels.stats.multitest import multipletests

apply_style()

BASE = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
DATA = BASE / 'data'
FIGS = BASE / 'figures'

# ── load data ─────────────────────────────────────────────────────────────────
cat   = pd.read_csv(DATA / '03_category_pgls_results.csv')
land  = pd.read_csv(DATA / 'functional_landscape_results.csv')

PKO_BASE = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
base_ko = pd.read_csv(PKO_BASE / 'ckpt_spire_adj_ko_associations.csv')
adj_ko  = pd.read_csv(PKO_BASE / 'ckpt_spire_sg_adj_ko_associations.csv')

def bh_fdr(df):
    rows = []
    for metal_name, grp in df.groupby('metal'):
        grp = grp[grp['p_value'].between(0, 1)].copy()
        if len(grp) == 0:
            continue
        _, fdr, _, _ = multipletests(grp['p_value'].values, method='fdr_bh')
        grp['fdr'] = fdr
        rows.append(grp)
    return pd.concat(rows)

base_ko = bh_fdr(base_ko)
adj_ko  = bh_fdr(adj_ko)
base_sig = base_ko[base_ko['fdr'] < 0.05].copy()
adj_sig  = adj_ko[adj_ko['fdr'] < 0.05].copy()


# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 — Category forest plot
# ══════════════════════════════════════════════════════════════════════════════
CAT_ORDER = ['F1.4_cofactor', 'F1.5_metabolism', 'F1.2_transport',
             'F1.3_sensing',  'F1.1_resistance']
CAT_LABELS = {
    'F1.4_cofactor':    'Cofactor biosynthesis\n(cobalamin/B12)',
    'F1.5_metabolism':  'Metal-dependent\nmetabolism',
    'F1.2_transport':   'Transport &\nhomeostasis',
    'F1.3_sensing':     'Sensing &\nregulation',
    'F1.1_resistance':  'Resistance &\ndetoxification',
}
P_LABELS = {
    'F1.4_cofactor':   'p = 1×10⁻⁹',
    'F1.5_metabolism': 'p = 7×10⁻⁵',
    'F1.2_transport':  'p = 1×10⁻⁵',
    'F1.3_sensing':    'p = 7×10⁻⁴',
    'F1.1_resistance': 'p = 0.66  (null)',
}

cat_plot = cat.set_index('label').loc[CAT_ORDER].copy()
betas = cat_plot['beta'].values
ses   = cat_plot['SE'].values
ci95  = ses * 1.96

colors = [PALETTE[1] if k == 'F1.1_resistance' else PALETTE[0] for k in CAT_ORDER]

fig, ax = plt.subplots(figsize=(FIGW['1.5col'], ROW_H * 1.15))
y_pos = np.arange(len(CAT_ORDER))

for i, (β, ci, color) in enumerate(zip(betas, ci95, colors)):
    ax.barh(i, β, xerr=ci, color=color, alpha=0.85,
            edgecolor='k', linewidth=0.5, height=0.55,
            error_kw={'elinewidth': 1.2, 'capsize': 3, 'ecolor': 'k'})

ax.axvline(0, color='gray', lw=0.8, ls='--')

# p-value annotations: place just right of the zero line (inside the right margin)
for i, (label, β, ci) in enumerate(zip(CAT_ORDER, betas, ci95)):
    p_text = P_LABELS[label]
    color = PALETTE[1] if label == 'F1.1_resistance' else PALETTE[0]
    # Always place to the right side so nothing overlaps with bars
    ax.text(0.002, i, p_text, va='center', ha='left', fontsize=7, color=color)

ax.set_yticks(y_pos)
ax.set_yticklabels([CAT_LABELS[k] for k in CAT_ORDER], fontsize=8)
ax.set_xlabel('PGLS β (effect on niche breadth)', fontsize=9)
ax.set_title('Functional category split:\nniche breadth ~ metal gene density (1,574 genera)', fontsize=10)
ax.invert_yaxis()
ax.set_xlim(-0.053, 0.028)

legend_elements = [
    mpatches.Patch(facecolor=PALETTE[0], edgecolor='k', lw=0.5, label='Significant (FDR < 5%)'),
    mpatches.Patch(facecolor=PALETTE[1], edgecolor='k', lw=0.5, label='Null (p = 0.66)'),
]
ax.legend(handles=legend_elements, fontsize=8, loc='lower left',
          bbox_to_anchor=(0.0, -0.01))

# Permutation note placed below the legend in figure space
ax.annotate('Permutation test: Δβ(cofactor − resistance) = 0.035\n'
            '0 / 1,000 random gene-set splits exceed this value (p < 0.001)',
            xy=(0.02, 0.02), xycoords='axes fraction',
            fontsize=7, color='#404040', style='italic',
            ha='left', va='bottom')

grid_h(ax)
fig.tight_layout()
save(fig, FIGS / 'adam_fig1_category_forest')
print('Saved adam_fig1_category_forest.pdf')


# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 — Functional landscape
# ══════════════════════════════════════════════════════════════════════════════
land2 = land.copy()

GROUP_COLOR = {
    'negative_control':        PALETTE[3],   # amber
    'core_metabolism':         PALETTE[4],   # sky blue
    'information_processing':  PALETTE[4],
    'metal_related':           PALETTE[1],   # orange (AMR = null)
    'metal_reference':         PALETTE[0],   # blue (our metal gene set)
}
GROUP_LABEL = {
    'negative_control':        'Non-metal reference',
    'core_metabolism':         'Core metabolism',
    'information_processing':  'Core metabolism',
    'metal_related':           'AMR / metal-adjacent',
    'metal_reference':         'Metal genes (this study)',
}

# Short single-line labels — NO newlines so they don't crowd each other
CAT_NAMES = {
    'secondary_metab':    'Secondary metabolism',
    'xenobiotics':        'Xenobiotics (AMR)',
    'two_component':      'Two-component systems',
    'abc_transporters':   'ABC transporters (non-metal)',
    'quorum_sensing':     'Quorum sensing',
    'carbohydrate_metab': 'Carbohydrate metab.',
    'energy_metab':       'Energy metab.',
    'lipid_metab':        'Lipid metab.',
    'nucleotide_metab':   'Nucleotide metab.',
    'aa_metab':           'Amino acid metab.',
    'glycan_biosyn':      'Glycan biosyn.',
    'cofactor_vitamin':   'Cofactors & vitamins',
    'terpenoid_polyket':  'Terpenoids & polyketides',
    'cell_motility':      'Cell motility',
    'transcription':      'Transcription',
    'translation':        'Translation (ribosome)',
    'protein_folding':    'Protein folding',
    'replication_repair': 'Replication & repair',
    'amr':                'Beta-lactam AMR',
    'metal_genes_p1':     'Metal genes — this study',
}

land2['color']  = land2['group'].map(GROUP_COLOR)
land2['glabel'] = land2['group'].map(GROUP_LABEL)
land2['clabel'] = land2['category'].map(CAT_NAMES).fillna(land2['category'])
land2 = land2.sort_values('beta', ascending=True).reset_index(drop=True)
n_cats = len(land2)

# Tall enough for single-line 8pt labels with spacing
fig_h = max(ROW_H * 2.2, n_cats * 0.28)
fig, ax = plt.subplots(figsize=(FIGW['full'], fig_h))

for i, row in land2.iterrows():
    ci = row['SE'] * 1.96
    ax.barh(i, row['beta'], xerr=ci,
            color=row['color'], alpha=0.85,
            edgecolor='k', linewidth=0.5, height=0.65,
            error_kw={'elinewidth': 0.9, 'capsize': 2, 'ecolor': 'k'})

ax.axvline(0, color='gray', lw=0.8, ls='--')
ax.set_yticks(np.arange(n_cats))
ax.set_yticklabels(land2['clabel'].tolist(), fontsize=8)
ax.set_xlabel('PGLS β (effect on ecological niche breadth)', fontsize=9)
ax.set_title('Functional landscape: gene categories vs ecological specialization\n'
             '(negative β = gene-dense genera are habitat specialists)', fontsize=10)

seen = []
legend_elements = []
for group, color in GROUP_COLOR.items():
    lbl = GROUP_LABEL[group]
    if lbl not in seen:
        legend_elements.append(mpatches.Patch(facecolor=color, edgecolor='k', lw=0.5, label=lbl))
        seen.append(lbl)
ax.legend(handles=legend_elements, fontsize=8, loc='lower right')

grid_h(ax)
fig.tight_layout()
save(fig, FIGS / 'adam_fig2_functional_landscape')
print('Saved adam_fig2_functional_landscape.pdf')


# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 — Per-KO pH robustness
# ══════════════════════════════════════════════════════════════════════════════
merged = base_sig.merge(
    adj_sig[['ko_id', 'metal', 'beta', 'fdr']].rename(
        columns={'beta': 'beta_adj', 'fdr': 'fdr_adj'}),
    on=['ko_id', 'metal'], how='left'
)
merged['survives'] = merged['beta_adj'].notna()

surv = merged[merged['survives']].copy()
surv['abs_beta'] = surv['beta'].abs()
surv = surv.sort_values('abs_beta', ascending=False).head(10)

conf = merged[~merged['survives']].copy()
conf['abs_beta'] = conf['beta'].abs()
conf = conf.sort_values('abs_beta', ascending=False).head(8)

subset = pd.concat([surv, conf]).reset_index(drop=True)

KO_DESC = {
    'K19147': 'arsB (As extrusion)',
    'K08363': 'merA (Hg reductase)',
    'K10007': 'merT (Hg transporter)',
    'K10006': 'merC (Hg importer)',
    'K07093': 'MerR-HTH regulator',
    'K14335': 'zntA (Pb/Zn ATPase)',
    'K00425': 'coxA (cyt. c oxidase)',
    'K00426': 'coxB (cyt. c oxidase)',
    'K16013': 'arsC2 (arsenate red.)',
    'K16014': 'arsH (NADPH oxidored.)',
    'K01547': 'ppaC (pyrophosphatase)',
    'K02011': 'fecE (Fe-ABC ATPase)',
    'K02012': 'fecB (Fe-ABC binding)',
    'K02755': 'pstA (Hg/Phos. trans.)',
    'K02756': 'pstB (Hg/Phos. ATPase)',
    'K02757': 'pstC (Hg/Phos. perm.)',
    'K02021': 'fepG (Fe/Pb transport.)',
    'K03820': 'lolA (Pb outer-memb.)',
    'K01548': 'kdpB (Pb K⁺-ATPase)',
    'K08217': 'arsA (As ATPase)',
    'K15733': 'arsI (As lyase)',
    'K06201': 'merP (Hg chaperone)',
}
metal_short = {'PF1_As': 'As', 'PF1_Hg': 'Hg', 'PF1_Pb': 'Pb',
               'PF1_Cr': 'Cr', 'PF1_Cu': 'Cu'}

subset['label'] = (
    subset['ko_id'].map(KO_DESC).fillna(subset['ko_id'])
    + ' × '
    + subset['metal'].map(metal_short).fillna(subset['metal'])
)
subset['color'] = subset['survives'].map({True: PALETTE[0], False: PALETTE[1]})

n_surv = subset['survives'].sum()   # 10
n_conf = (~subset['survives']).sum()  # 8
n_total = len(subset)

fig, ax = plt.subplots(figsize=(FIGW['2col'], ROW_H * 1.9))
y_pos = np.arange(n_total)

for i, row in subset.iterrows():
    ci_base = row['se'] * 1.96
    ax.barh(i, row['beta'], xerr=ci_base,
            color=row['color'], alpha=0.85,
            edgecolor='k', linewidth=0.5, height=0.65,
            error_kw={'elinewidth': 1.0, 'capsize': 2.5, 'ecolor': 'k'})
    if row['survives'] and pd.notna(row.get('beta_adj')):
        ax.plot(row['beta_adj'], i, 'D', color='white', ms=5,
                markeredgecolor=PALETTE[0], markeredgewidth=1.2)

ax.axvline(0, color='gray', lw=0.8, ls='--')

# Clean divider between survivors and confounded, with section labels
divider_y = n_surv - 0.5
ax.axhline(divider_y, color='gray', lw=1.0, ls=':')

# Section labels in the right margin (outside plot area).
# invert_yaxis() makes data y=0 appear at physical top (axes fraction ≈ 1).
# Survivors occupy y=0..n_surv-1 → mid-fraction = 1 - n_surv/(2*n_total)
# Confounded occupy y=n_surv..n_total-1 → mid-fraction = n_conf/(2*n_total)
ax.text(1.01, 1 - n_surv / (2 * n_total), 'Survives\npH control',
        transform=ax.transAxes, fontsize=7, color=PALETTE[0],
        va='center', ha='left', fontweight='bold')
ax.text(1.01, n_conf / (2 * n_total), 'pH-\nconfounded',
        transform=ax.transAxes, fontsize=7, color=PALETTE[1],
        va='center', ha='left', fontweight='bold')

ax.set_yticks(y_pos)
ax.set_yticklabels(subset['label'].tolist(), fontsize=7.5)
ax.set_xlabel('β (logistic regression: MAG presence vs soil metal concentration)', fontsize=9)
ax.set_title('Per-KO associations: SPIRE MAGs × soil metals\n'
             'Bar = baseline β;  ◆ = pH-adjusted β;  69 → 31 pairs survive pH control',
             fontsize=10)

legend_elements = [
    mpatches.Patch(facecolor=PALETTE[0], edgecolor='k', lw=0.5,
                   label='Survives pH control (robust)'),
    mpatches.Patch(facecolor=PALETTE[1], edgecolor='k', lw=0.5,
                   label='pH-confounded (not actionable)'),
    plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='white',
               markeredgecolor=PALETTE[0], markeredgewidth=1.2, ms=5,
               label='pH-adjusted β'),
]
ax.legend(handles=legend_elements, fontsize=8,
          bbox_to_anchor=(0.5, -0.06), loc='upper center', ncol=3)
ax.invert_yaxis()
grid_h(ax)
fig.tight_layout(rect=[0, 0.06, 1, 1])
save(fig, FIGS / 'adam_fig3_pko_ph_robustness')
print('Saved adam_fig3_pko_ph_robustness.pdf')


# ══════════════════════════════════════════════════════════════════════════════
# Figure 4 — Utility summary: community level (null) vs KO level (signal)
# ══════════════════════════════════════════════════════════════════════════════
tier_labels = [
    'Resistance-only\n(BacMET; 112 KOs)',
    'All metal genes\n(P1 reference; 140 KOs)',
    'Constitutive metal\n(excl. resistance; ~110 KOs)',
]
tier_betas = [-0.011110, -0.020700, -0.027033]
tier_ses   = [ 0.005655,  0.003677,  0.004924]
tier_ci95  = [s * 1.96 for s in tier_ses]
tier_pvals = ['p = 0.050', 'p = 2×10⁻⁸', 'p = 5×10⁻⁸']
tier_colors = [PALETTE[1], PALETTE[3], PALETTE[0]]

metals_plot = ['Hg', 'As', 'Pb', 'Cr', 'Cu']
metal_map_r = {'PF1_Hg': 'Hg', 'PF1_As': 'As', 'PF1_Pb': 'Pb',
               'PF1_Cr': 'Cr', 'PF1_Cu': 'Cu'}
base_counts = base_sig.groupby('metal').size().rename(index=metal_map_r)
adj_counts  = adj_sig.groupby('metal').size().rename(index=metal_map_r)
surv_base = [base_counts.get(m, 0) for m in metals_plot]
surv_adj  = [adj_counts.get(m, 0) for m in metals_plot]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FIGW['2col'], ROW_H * 1.15))

# ── Left: tier comparison ──────────────────────────────────────────────────
y_pos_t = np.arange(len(tier_labels))
for i, (β, ci, color) in enumerate(zip(tier_betas, tier_ci95, tier_colors)):
    ax1.barh(i, β, xerr=ci, color=color, alpha=0.85,
             edgecolor='k', linewidth=0.5, height=0.55,
             error_kw={'elinewidth': 1.2, 'capsize': 3, 'ecolor': 'k'})

ax1.axvline(0, color='gray', lw=0.8, ls='--')
ax1.set_yticks(y_pos_t)
ax1.set_yticklabels(tier_labels, fontsize=8)
ax1.set_xlabel('PGLS β (niche breadth prediction)', fontsize=9)
ax1.set_title('Community-level ecology:\nresistance genes ≈ null', fontsize=10)
ax1.invert_yaxis()

# p-value annotations placed to the right of the zero axis (outside bars)
for i, (pval, β, color) in enumerate(zip(tier_pvals, tier_betas, tier_colors)):
    ax1.text(0.001, i, pval, va='center', ha='left', fontsize=7, color=color)

ax1.set_xlim(-0.044, 0.020)
grid_h(ax1)

# ── Right: survival counts ─────────────────────────────────────────────────
x = np.arange(len(metals_plot))
w = 0.32
bars_b = ax2.bar(x - w/2, surv_base, width=w, color=PALETTE[3], alpha=0.85,
                 edgecolor='k', linewidth=0.5, label='Baseline sig. (FDR < 5%)')
bars_a = ax2.bar(x + w/2, surv_adj,  width=w, color=PALETTE[0], alpha=0.85,
                 edgecolor='k', linewidth=0.5, label='Survives pH control')

ax2.set_xticks(x)
ax2.set_xticklabels(metals_plot, fontsize=8)
ax2.set_xlabel('Soil metal', fontsize=9)
ax2.set_ylabel('No. significant KO–metal pairs', fontsize=9)
ax2.set_title('Contamination detection:\nKO-level resolution works', fontsize=10)
ax2.legend(fontsize=8, loc='upper right')
grid_h(ax2)

# Count labels above bars
for xi, (b, a) in enumerate(zip(surv_base, surv_adj)):
    if b > 0:
        ax2.text(xi - w/2, b + 0.3, str(b), ha='center', fontsize=7,
                 color='#606060')
    if a > 0:
        ax2.text(xi + w/2, a + 0.3, str(a), ha='center', fontsize=7,
                 color='#606060')

fig.suptitle('Resistance genes: community level vs individual KO level', fontsize=11,
             fontweight='bold', y=1.02)
fig.tight_layout()
save(fig, FIGS / 'adam_fig4_utility_summary')
print('Saved adam_fig4_utility_summary.pdf')

print('\nAll figures done.')
