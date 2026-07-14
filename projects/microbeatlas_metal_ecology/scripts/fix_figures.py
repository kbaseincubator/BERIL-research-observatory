#!/usr/bin/env python3
"""Regenerate all figures with layout fixes.

Fixes applied:
  pagel_lambda_summary.png : x-axis tick labels rotated 30° to prevent overlap
  fig5_robustness.png      : Panel A left margin increased so y-tick labels are not clipped
  fig2_pgls_forest.png     : legend moved to upper-left to avoid overlapping β/p annotations
  fig3_synthesis.png       : group labels moved to left side of heatmap (no colorbar clash);
                             wspace increased so Panel A y-axis label doesn't bleed into B
  fig4_metal_types_scatter : PGLS text box moved to upper-right; annotations reduced to top-5
                             with larger offsets and repulsion so they don't overlap each other
                             or the text box
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
from scipy import stats as sp_stats
from scipy.stats import nct
from adjustText import adjust_text
from pathlib import Path

DATA    = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")
FIGURES = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/figures")

plt.rcParams.update({
    'font.family':     'DejaVu Sans',
    'font.size':       9,
    'axes.labelsize':  9,
    'axes.titlesize':  10,
    'legend.fontsize': 8,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'figure.dpi':      150,
    'savefig.dpi':     300,
    'savefig.bbox':    'tight',
})

# ── Shared label maps (from NB06 cell 4) ────────────────────────────────────
TRAIT_LABELS = {
    'mean_levins_B_std':         "Niche breadth\n(Levins' B_std)",
    'mean_n_envs':               'Habitat range\n(# environments)',
    'is_nitrifier':              'Nitrification\n(functional trait)',
    'mean_n_metal_amr_clusters': 'Metal AMR genes\n(cluster count)',
    'mean_metal_core_fraction':  'Metal AMR\n(core fraction)',
    'mean_n_metal_types':        'Metal type\ndiversity',
}
PRED_LABELS = {
    'mean_n_metal_amr_clusters_z': 'AMR clusters (z)',
    'mean_metal_core_fraction_z':  'Core AMR fraction (z)',
    'mean_n_metal_types_z':        'Metal type diversity (z)',
}
RESP_LABELS = {
    'mean_levins_B_std': "Levins' B_std",
    'mean_n_envs':       'Environments detected',
}
BONFERRONI = 0.05 / 6

TRAIT_ORDER = [
    'mean_levins_B_std', 'mean_n_envs', 'is_nitrifier',
    'mean_n_metal_amr_clusters', 'mean_metal_core_fraction', 'mean_n_metal_types',
]
DOMAINS = ['Bacteria', 'Archaea']
RESP_ORDER  = ['mean_levins_B_std', 'mean_n_envs']
PRED_ORDER  = ['mean_n_metal_amr_clusters_z', 'mean_metal_core_fraction_z', 'mean_n_metal_types_z']
RESP_COLORS = {'mean_levins_B_std': '#2166ac', 'mean_n_envs': '#d6604d'}
RESP_OFFSET = {'mean_levins_B_std': -0.14, 'mean_n_envs': +0.14}

def sig_stars(p):
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    return 'ns'

# ── Load shared data ─────────────────────────────────────────────────────────
lam_df   = pd.read_csv(DATA / 'pagel_lambda_results.csv')
pgls     = pd.read_csv(DATA / 'pgls_results.csv')
multi    = pd.read_csv(DATA / 'pgls_multi_results.csv')
pgls_sub = pd.read_csv(DATA / 'pgls_subset.csv')

lam_df['sig']  = lam_df['p_value'].map(sig_stars)
pgls['sig']    = pgls['p_value'].map(sig_stars)
multi['sig']   = multi['p_value'].map(sig_stars)

# ── Build heatmap matrices ───────────────────────────────────────────────────
lam_idx  = lam_df.set_index(['label', 'trait'])
n_traits  = len(TRAIT_ORDER)
n_domains = len(DOMAINS)
hm_lambda = pd.DataFrame(np.nan, index=TRAIT_ORDER, columns=DOMAINS)
hm_p      = pd.DataFrame(np.nan, index=TRAIT_ORDER, columns=DOMAINS)
hm_n      = pd.DataFrame(np.nan, index=TRAIT_ORDER, columns=DOMAINS)
for trait in TRAIT_ORDER:
    for domain in DOMAINS:
        key = (domain, trait)
        if key in lam_idx.index:
            row = lam_idx.loc[key]
            hm_lambda.loc[trait, domain] = row['lambda']
            hm_p.loc[trait, domain]      = row['p_value']
            hm_n.loc[trait, domain]      = row['n_taxa']

# ── Build y-positions for forest plots ──────────────────────────────────────
GAP    = 0.8
pred_y = {}
for ri, resp in enumerate(RESP_ORDER):
    base = ri * (3 + GAP)
    for pi, pred in enumerate(PRED_ORDER):
        pred_y[(resp, pred)] = base + (2 - pi)

ytick_pos, ytick_labels = [], []
for pi, pred in enumerate(PRED_ORDER):
    y_mid = np.mean([pred_y[(resp, pred)] for resp in RESP_ORDER])
    ytick_pos.append(y_mid)
    ytick_labels.append(PRED_LABELS[pred])

# ────────────────────────────────────────────────────────────────────────────
# FIX 1: pagel_lambda_summary.png — rotate x-axis tick labels
# ────────────────────────────────────────────────────────────────────────────
print("Generating pagel_lambda_summary.png ...")

genus_traits = pd.read_csv(DATA / 'genus_trait_table.csv')

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel a: bar chart
ax = axes[0]
colors_domain = {'Bacteria': 'steelblue', 'Archaea': 'tomato'}
TRAIT_SHORT = {
    'mean_levins_B_std':         'B_std (niche)',
    'mean_n_envs':               '# envs (habitat)',
    'is_nitrifier':              'Nitrif. (metabolism)',
    'mean_n_metal_amr_clusters': 'AMR clusters',
    'mean_metal_core_fraction':  'Core AMR fraction',
    'mean_n_metal_types':        'Metal types (div.)',
}
DOMAIN_SHORT = {'Bacteria': 'Bact.', 'Archaea': 'Arch.'}

bar_labels, bar_vals, bar_cols, bar_sigs = [], [], [], []
for _, row in lam_df.iterrows():
    short = (f"{DOMAIN_SHORT.get(row['label'], row['label'])} "
             f"{TRAIT_SHORT.get(row['trait'], row['trait'][:14])}")
    bar_labels.append(short)
    bar_vals.append(row['lambda'])
    bar_cols.append(colors_domain.get(row['label'], 'gray'))
    bar_sigs.append(sig_stars(row['p_value']))

ax.bar(range(len(bar_labels)), bar_vals, color=bar_cols, alpha=0.8, edgecolor='white')
ax.axhline(0, color='black', lw=0.8)
ax.axhline(1, color='black', lw=0.8, ls='--', label='λ=1 (Brownian motion)')
ax.set_xticks(range(len(bar_labels)))
# FIX: single-line labels + 90° rotation fully prevents overlap
ax.set_xticklabels(bar_labels, fontsize=7, rotation=90, ha='right')
ax.set_ylim(-0.05, 1.20)
ax.set_ylabel("Pagel's λ")
ax.set_title("Pagel's λ per trait × domain")
for i, (v, s) in enumerate(zip(bar_vals, bar_sigs)):
    ax.text(i, v + 0.03, s, ha='center', va='bottom', fontsize=8)
patches = [mpatches.Patch(color=v, label=k) for k, v in colors_domain.items()]
ax.legend(handles=patches, fontsize=7)

# Panel b: niche breadth distribution
ax = axes[1]
role_colors = {'AOA_step1': 'tomato', 'AOB_step1': 'darkorange', 'NOB_step2': 'steelblue'}
bg = genus_traits[genus_traits['is_nitrifier'] == 0]['mean_levins_B_std'].dropna()
ax.hist(bg, bins=40, color='lightgray', alpha=0.9, density=True,
        label=f'Non-nitrifiers (n={len(bg):,})')
for role, col in role_colors.items():
    vals = genus_traits[genus_traits['nitrifier_role'] == role]['mean_levins_B_std'].dropna()
    if len(vals) > 0:
        ax.axvline(vals.mean(), color=col, lw=2, ls='--',
                   label=f'{role} mean={vals.mean():.2f} (n={len(vals)})')
        ax.scatter(vals,
                   np.full(len(vals), 0.02 + list(role_colors.keys()).index(role) * 0.015),
                   color=col, zorder=5, s=60, alpha=0.9)
ax.set_xlabel("Mean Levins' B_std per genus")
ax.set_ylabel('Density')
ax.set_title('Niche breadth: nitrifiers vs background')
ax.legend(fontsize=7)

# Panel c: niche breadth vs environments
ax = axes[2]
for role, col in role_colors.items():
    sub = genus_traits[genus_traits['nitrifier_role'] == role]
    if len(sub) > 0:
        ax.scatter(sub['mean_n_envs'], sub['mean_levins_B_std'],
                   color=col, label=role, s=80, zorder=5,
                   edgecolors='black', lw=0.5)
        for _, row in sub.iterrows():
            ax.annotate(row['otu_genus'], (row['mean_n_envs'], row['mean_levins_B_std']),
                        fontsize=6, xytext=(3, 2), textcoords='offset points')
bg_sample = genus_traits[
    (genus_traits['is_nitrifier'] == 0) & (genus_traits['n_otus'] >= 3)
]
ax.scatter(bg_sample['mean_n_envs'], bg_sample['mean_levins_B_std'],
           color='lightgray', alpha=0.4, s=15, label='Non-nitrifier genera', zorder=1)
ax.set_xlabel('Mean environments detected')
ax.set_ylabel("Mean Levins' B_std")
ax.set_title('Niche breadth vs environment range')
ax.legend(fontsize=7)

plt.suptitle(
    "Pagel's λ: Phylogenetic Signal in Microbial Niche Breadth "
    "(GTDB r214 × MicrobeAtlas 98,919 OTUs)",
    y=1.02, fontsize=11)
plt.tight_layout()
plt.savefig(FIGURES / 'pagel_lambda_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved figures/pagel_lambda_summary.png")

# ────────────────────────────────────────────────────────────────────────────
# FIX 2: fig2_pgls_forest.png — legend moved to upper-left
# ────────────────────────────────────────────────────────────────────────────
print("Generating fig2_pgls_forest.png ...")

fig, ax = plt.subplots(figsize=(7.5, 5.5))

# Shade row where Bonferroni-significant result falls
for resp in RESP_ORDER:
    rsub_check = pgls[pgls['response'] == resp].set_index('predictor')
    for pred in PRED_ORDER:
        if pred not in rsub_check.index:
            continue
        row_check = rsub_check.loc[pred]
        if row_check['p_value'] < BONFERRONI:
            y_mid = pred_y[(resp, pred)]
            ax.axhspan(y_mid - 0.5, y_mid + 0.5,
                       color='#ddeeff', alpha=0.55, zorder=0, lw=0)

for resp in RESP_ORDER:
    col     = RESP_COLORS[resp]
    off     = RESP_OFFSET[resp]
    rsub    = pgls[pgls['response'] == resp].set_index('predictor')
    multi_r = (multi[multi['response'] == resp].set_index('predictor')
               if 'response' in multi.columns else pd.DataFrame())

    for pred in PRED_ORDER:
        y = pred_y[(resp, pred)] + off
        if pred not in rsub.index:
            continue
        row      = rsub.loc[pred]
        is_bonf  = row['p_value'] < BONFERRONI

        ax.errorbar(
            row['beta'], y, xerr=1.96 * row['SE'],
            fmt='o', color=col,
            markersize=9 if is_bonf else 5.5,
            capsize=3.5, linewidth=1.4,
            alpha=1.0 if is_bonf else 0.45,
            zorder=3
        )
        if is_bonf:
            ax.text(
                row['beta'] + 1.96 * row['SE'] + 0.001, y,
                f"β={row['beta']:+.3f}, p={row['p_value']:.1e}  ✱",
                va='center', ha='left', fontsize=8,
                color=col, fontweight='bold'
            )
        if len(multi_r) > 0 and pred in multi_r.index:
            mrow = multi_r.loc[pred]
            ym   = pred_y[(resp, pred)] - off
            ax.errorbar(
                mrow['beta'], ym, xerr=1.96 * mrow['SE'],
                fmt='^', color=col,
                markersize=6 if mrow['p_value'] < 0.05 else 4,
                capsize=3, linewidth=1.2, alpha=0.75, zorder=2
            )

# Group labels on the right
for ri, resp in enumerate(RESP_ORDER):
    ys = [pred_y[(resp, p)] for p in PRED_ORDER]
    ax.text(1.01, np.mean(ys) / (3 + GAP + 3 + GAP),
            RESP_LABELS[resp], color=RESP_COLORS[resp],
            va='center', ha='left', fontsize=9, fontweight='bold',
            transform=ax.get_yaxis_transform())

ax.axvline(0, color='black', lw=1, ls='--', alpha=0.7)
ax.set_yticks(ytick_pos)
ax.set_yticklabels(ytick_labels, fontsize=8.5)
ax.set_xlabel(r'PGLS $\beta$ ± 95% CI  (predictor z-scored)', fontsize=9)
ax.set_title('PGLS regression: metal AMR predictors vs niche breadth\n'
             'n = 606 bacterial genera (GTDB r214)', fontsize=10)

patches_leg = [mpatches.Patch(color=RESP_COLORS[r], label=RESP_LABELS[r]) for r in RESP_ORDER]
circle_patch = plt.Line2D([0], [0], marker='o', color='gray',
                           label='Simple model (●)', linestyle='none', markersize=6)
tri_patch    = plt.Line2D([0], [0], marker='^', color='gray',
                           label='Multi-predictor (▲)', linestyle='none',
                           markersize=6, alpha=0.75)
bonf_patch   = mpatches.Patch(color='#ddeeff', label=f'Bonferroni sig. (p<{BONFERRONI:.3f})')
# FIX: place legend BELOW the x-axis to avoid overlapping any CI bars
ax.legend(handles=patches_leg + [circle_patch, tri_patch, bonf_patch],
          fontsize=7.5, loc='upper center',
          bbox_to_anchor=(0.5, -0.14), ncol=3, framealpha=0.95)

ax.set_xlim(-0.04, 0.085)
fig.subplots_adjust(bottom=0.22)
plt.savefig(FIGURES / 'fig2_pgls_forest.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved figures/fig2_pgls_forest.png")

# ────────────────────────────────────────────────────────────────────────────
# FIX 3: fig3_synthesis.png — group labels left of heatmap; wider wspace
# ────────────────────────────────────────────────────────────────────────────
print("Generating fig3_synthesis.png ...")

# FIX: increase wspace so Panel A y-axis label doesn't bleed into Panel B
fig = plt.figure(figsize=(13, 6.5))
gs  = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 1.55], wspace=0.50)

ax_hm = fig.add_subplot(gs[0])
ax_fp = fig.add_subplot(gs[1])

cmap_hm = plt.cm.YlGnBu
vmin_hm, vmax_hm = 0.0, 1.0

for xi, domain in enumerate(DOMAINS):
    for yi, trait in enumerate(TRAIT_ORDER):
        lam_val = hm_lambda.loc[trait, domain]
        p_val   = hm_p.loc[trait, domain]
        n_val   = hm_n.loc[trait, domain]
        y_pos   = n_traits - 1 - yi

        if np.isnan(lam_val):
            ax_hm.add_patch(
                plt.Rectangle((xi - 0.5, y_pos - 0.5), 1, 1, color='#d0d0d0', zorder=1))
            ax_hm.text(xi, y_pos, 'n/a', ha='center', va='center',
                       fontsize=7.5, color='#555555')
        else:
            color = cmap_hm((lam_val - vmin_hm) / (vmax_hm - vmin_hm))
            ax_hm.add_patch(
                plt.Rectangle((xi - 0.5, y_pos - 0.5), 1, 1, color=color, zorder=1))
            tc = 'white' if lam_val > 0.62 else 'black'
            ax_hm.text(xi, y_pos, f'λ={lam_val:.2f}\n{sig_stars(p_val)}',
                       ha='center', va='center', fontsize=8,
                       color=tc, fontweight='bold', zorder=2)
            ax_hm.text(xi, y_pos - 0.31, f'n={int(n_val)}',
                       ha='center', va='center', fontsize=6, color=tc, zorder=2)

ax_hm.set_xlim(-0.5, n_domains - 0.5)
ax_hm.set_ylim(-0.5, n_traits - 0.5)
ax_hm.set_xticks(range(n_domains))
ax_hm.set_xticklabels(DOMAINS, fontsize=9, fontweight='bold')
ax_hm.set_yticks(range(n_traits))
ax_hm.set_yticklabels([TRAIT_LABELS[t] for t in reversed(TRAIT_ORDER)], fontsize=8)
ax_hm.tick_params(length=0)
ax_hm.axhline(n_traits - 3.5, color='black', lw=1.5, ls='--', alpha=0.45)
ax_hm.axhline(n_traits - 1.5, color='black', lw=1.5, ls=':',  alpha=0.35)

# FIX: place group labels on the LEFT of the heatmap (right side clashes with colorbar)
for label, y in [('Niche breadth', n_traits - 1.0),
                  ('Metabolism',   n_traits - 3.0),
                  ('Metal AMR',    n_traits - 5.0)]:
    ax_hm.text(-0.55, y, label,
               ha='right', va='center', fontsize=7, style='italic',
               color='#333333', transform=ax_hm.get_yaxis_transform())

sm_hm = ScalarMappable(cmap=cmap_hm, norm=mcolors.Normalize(vmin=vmin_hm, vmax=vmax_hm))
sm_hm.set_array([])
cbar = plt.colorbar(sm_hm, ax=ax_hm, orientation='vertical', fraction=0.045, pad=0.04)
cbar.set_label("Pagel's λ", fontsize=8)
cbar.set_ticks([0, 0.5, 1.0])
ax_hm.set_title("A   Phylogenetic signal (Pagel's λ)", loc='left',
                fontsize=9.5, fontweight='bold', pad=8)

# Panel B: PGLS forest
for resp in RESP_ORDER:
    col  = RESP_COLORS[resp]
    off  = RESP_OFFSET[resp]
    rsub = pgls[pgls['response'] == resp].set_index('predictor')
    mr   = (multi[multi['response'] == resp].set_index('predictor')
            if 'response' in multi.columns else pd.DataFrame())

    for pred in PRED_ORDER:
        y       = pred_y[(resp, pred)] + off
        if pred not in rsub.index:
            continue
        row     = rsub.loc[pred]
        is_bonf = row['p_value'] < BONFERRONI
        ax_fp.errorbar(
            row['beta'], y, xerr=1.96 * row['SE'],
            fmt='o', color=col,
            markersize=8 if is_bonf else 5,
            capsize=3, linewidth=1.3,
            alpha=1.0 if is_bonf else 0.4, zorder=3
        )
        if is_bonf:
            # FIX F3A: place annotation above & right of the data point, clear of
            # the CI bar.  The significant row is at the BOTTOM of the y-axis range,
            # so we nudge the label into the empty space one row higher.
            x_ann = row['beta'] + 1.96 * row['SE'] + 0.001
            y_ann = y + 0.55   # ~half a row-gap above the data point
            ax_fp.annotate(
                f"β={row['beta']:+.3f}, p={row['p_value']:.1e}",
                xy=(row['beta'], y),          # arrow tip at the data point
                xytext=(x_ann, y_ann),         # text in empty space above
                va='bottom', ha='left', fontsize=7,
                color=col, fontweight='bold',
                annotation_clip=False,
                bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                          edgecolor=col, linewidth=0.8, alpha=0.92),
                arrowprops=dict(arrowstyle='->', color=col, lw=0.8,
                                connectionstyle='arc3,rad=0.1')
            )
        if len(mr) > 0 and pred in mr.index:
            mrow = mr.loc[pred]
            ym   = pred_y[(resp, pred)] - off
            ax_fp.errorbar(
                mrow['beta'], ym, xerr=1.96 * mrow['SE'],
                fmt='^', color=col, markersize=5,
                capsize=2.5, linewidth=1.1, alpha=0.70, zorder=2
            )

ax_fp.axvline(0, color='black', lw=1, ls='--', alpha=0.7)
ax_fp.set_yticks(ytick_pos)
ax_fp.set_yticklabels(ytick_labels, fontsize=8)
# FIX F3B: clarify that predictor is z-scored but responses are on raw scales
ax_fp.set_xlabel(
    r'PGLS $\beta$ ± 95% CI  (predictor z-scored; response on raw scale)', fontsize=8.5)
ax_fp.set_title('B   PGLS: metal AMR vs niche breadth  (n = 606 bacterial genera)',
                loc='left', fontsize=9.5, fontweight='bold', pad=8)

# FIX F3B: legend clarifies raw scales
patches_resp = [
    mpatches.Patch(color=RESP_COLORS['mean_levins_B_std'],
                   label="Levins' B_std  [0–1 scale; β per SD predictor]"),
    mpatches.Patch(color=RESP_COLORS['mean_n_envs'],
                   label='Environments detected  [1–13 scale; β per SD predictor]'),
]
mk_circle = plt.Line2D([0], [0], marker='o', color='gray', linestyle='none',
                        markersize=6, label='Simple model (●)')
mk_tri    = plt.Line2D([0], [0], marker='^', color='gray', linestyle='none',
                        markersize=5, alpha=0.75, label='Multi-predictor (▲)')
ax_fp.legend(handles=patches_resp + [mk_circle, mk_tri], fontsize=6.5, loc='lower right')
ax_fp.text(0.01, 0.01,
           f'Filled circles = Bonferroni sig. (p < {BONFERRONI:.3f})',
           transform=ax_fp.transAxes, fontsize=6.5, color='gray')
ax_fp.set_xlim(-0.035, 0.075)

fig.savefig(FIGURES / 'fig3_synthesis.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved figures/fig3_synthesis.png")

# ────────────────────────────────────────────────────────────────────────────
# FIX 4: fig4_metal_types_scatter.png — text box upper-right; fewer annotations
# ────────────────────────────────────────────────────────────────────────────
print("Generating fig4_metal_types_scatter.png ...")

top_phyla  = pgls_sub['phylum'].value_counts().head(8).index.tolist()
tab_colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2',
              '#59a14f', '#edc948', '#b07aa1', '#ff9da7']
pal = dict(zip(top_phyla, tab_colors))
pgls_sub = pgls_sub.copy()
pgls_sub['point_color'] = pgls_sub['phylum'].map(pal).fillna('#cccccc')

fig, ax = plt.subplots(figsize=(7.5, 5.5))

# FIX F4: add horizontal jitter to reveal stacking at integer/half-integer x values
rng4 = np.random.default_rng(7)
jitter = rng4.uniform(-0.06, 0.06, size=len(pgls_sub))
ax.scatter(
    pgls_sub['mean_n_metal_types'] + jitter, pgls_sub['mean_levins_B_std'],
    c=pgls_sub['point_color'], alpha=0.35, s=22, linewidths=0, zorder=2
)

xv = pgls_sub['mean_n_metal_types']
yv = pgls_sub['mean_levins_B_std']
slope, intercept, r_ols, p_ols, _ = sp_stats.linregress(xv, yv)
xline = np.linspace(xv.min(), xv.max(), 200)
ax.plot(xline, slope * xline + intercept, 'k-', lw=2, alpha=0.55,
        label=f'OLS  r = {r_ols:.2f}, p = {p_ols:.2e}', zorder=3)

pgls_row = pgls[
    (pgls['response'] == 'mean_levins_B_std') &
    (pgls['predictor'] == 'mean_n_metal_types_z')
].iloc[0]

# PGLS text box upper-right
ax.text(0.98, 0.97,
        f"PGLS (controlling for phylogeny):\n"
        f"  β = {pgls_row['beta']:+.3f} ± {pgls_row['SE']:.3f} (SE)\n"
        f"  p = {pgls_row['p_value']:.2e}   λ = {pgls_row['lambda']:.2f}\n"
        f"  n = {int(pgls_row['n_taxa'])} bacterial genera",
        transform=ax.transAxes, ha='right', va='top', fontsize=8.5,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                  edgecolor='#2166ac', linewidth=1.5, alpha=0.92))

# FIX F4: use adjustText to push genus labels away from each other and data points
top5 = pgls_sub.nlargest(5, 'mean_levins_B_std').reset_index(drop=True)
texts = []
for _, row in top5.iterrows():
    t = ax.text(
        row['mean_n_metal_types'], row['mean_levins_B_std'],
        row['genus_lower'].capitalize(),
        fontsize=6.5, color='#333333', style='italic'
    )
    texts.append(t)
adjust_text(
    texts, ax=ax,
    expand_points=(1.8, 1.8), expand_text=(1.5, 1.5),
    arrowprops=dict(arrowstyle='-', color='#aaaaaa', lw=0.8),
    force_text=(0.3, 0.5), force_points=(0.2, 0.3),
    only_move={'points': 'y', 'texts': 'xy'}
)

ax.set_xlabel('Metal type diversity (mean # metal families resisted per species)', fontsize=9)
ax.set_ylabel("Mean Levins' niche breadth (B_std)", fontsize=9)
ax.set_title('Metal type diversity predicts ecological niche breadth\n'
             '(PGLS, GTDB r214 bacterial genus tree)', fontsize=10)

phylum_patches = [mpatches.Patch(color=c, label=p) for p, c in pal.items()]
phylum_patches.append(mpatches.Patch(color='#cccccc', label='Other phyla'))
leg1 = ax.legend(handles=phylum_patches, title='Phylum', fontsize=7,
                  title_fontsize=7.5, loc='lower right', ncol=2, framealpha=0.9)
ax.add_artist(leg1)
ax.legend(fontsize=8, loc='lower left')

plt.tight_layout()
plt.savefig(FIGURES / 'fig4_metal_types_scatter.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved figures/fig4_metal_types_scatter.png")

# ────────────────────────────────────────────────────────────────────────────
# FIX 5: fig5_robustness.png — increase left margin so Panel A labels are visible
# ────────────────────────────────────────────────────────────────────────────
print("Generating fig5_robustness.png ...")

COL_MAIN   = "#2166ac"
COL_RAR    = "#4dac26"
COL_ARC    = "#d01c8b"
COL_BONF   = "#f4a582"
ALPHA_BONF = 0.0083

rob  = pd.read_csv(DATA / "pgls_robustness_results.csv")
rar  = pd.read_csv(DATA / "pgls_rarefied_summary.csv")
prev = pd.read_csv(DATA / "pgls_prevalence_threshold_result.csv")

main_row = pgls[pgls["predictor"] == "mean_n_metal_types_z"].iloc[0]
cov_row  = rob[(rob["model"] == "B_std~types+n_species") &
               (rob["predictor"] == "mean_n_metal_types_z")].iloc[0]
arc_row  = rob[(rob["model"].str.startswith("arc_B_std~mean_n_metal_types")) &
               (rob["predictor"] == "mean_n_metal_types_z")].iloc[0]
rar_row  = rar.iloc[0]
prev_row = prev.iloc[0]

rar_beta = rar_row["median_beta"]
rar_se   = (rar_row["q75_beta"] - rar_row["q25_beta"]) / 2.0
rar_p    = rar_row["median_p"]

scenarios = [
    ("Original\n(n=606 genera)",                       main_row["beta"], main_row["SE"], main_row["p_value"],  COL_MAIN, "o"),
    ("+ n_species covariate\n(n=606 genera)",           cov_row["beta"],  cov_row["SE"],  cov_row["p_value"],   COL_MAIN, "s"),
    # FIX F5A: clarify that rarefaction reduces genomes per genus, not genera count
    ("1 genome/genus\n(rarefied; n=606 genera,\n200 iter., median shown)", rar_beta, rar_se, rar_p, COL_RAR, "^"),
    ("Strict niche breadth\n(≥5% prev.; n=379 genera)", prev_row["beta"], prev_row["SE"], prev_row["p_value"], COL_MAIN, "D"),
    ("Archaea\n(n=48 genera)",                         arc_row["beta"],  arc_row["SE"],  arc_row["p_value"],   COL_ARC,  "v"),
]

rar_sigma  = (rar_row["q75_beta"] - rar_row["q25_beta"]) / 1.35
n_iter     = int(rar_row["n_iterations"])
rng2       = np.random.default_rng(42)
sim_betas  = rng2.normal(loc=rar_row["median_beta"], scale=rar_sigma, size=n_iter)
n_bonf_sig = int(round(rar_row["frac_bonf_sig"] * n_iter))
rar_frac   = rar_row["frac_p_lt_0.05"]

beta_obs = arc_row["beta"]
se_obs   = arc_row["SE"]
n_obs    = int(arc_row["n_taxa"])
n_range  = np.arange(20, 1200, 5)

def power_at_n(n, beta=beta_obs, se_obs=se_obs, n_obs=n_obs, alpha=0.05):
    se_n  = se_obs * np.sqrt(n_obs / n)
    ncp   = beta / se_n
    t_crit = nct.ppf(1 - alpha / 2, df=n - 2, nc=0)
    return float(nct.sf(t_crit, df=n - 2, nc=ncp) + nct.cdf(-t_crit, df=n - 2, nc=ncp))

powers_05   = [power_at_n(n, alpha=0.05)       for n in n_range]
powers_bonf = [power_at_n(n, alpha=ALPHA_BONF) for n in n_range]
n80_05   = int(n_range[np.searchsorted(powers_05,   0.80)])
n80_bonf = int(n_range[np.searchsorted(powers_bonf, 0.80)])

fig = plt.figure(figsize=(15, 5))
# FIX: increase left margin from 0.06 to 0.22 so Panel A y-tick labels are not clipped
gs  = gridspec.GridSpec(1, 3, figure=fig, wspace=0.40,
                        left=0.22, right=0.97, top=0.90, bottom=0.18)

ax_a = fig.add_subplot(gs[0])
ax_b = fig.add_subplot(gs[1])
ax_c = fig.add_subplot(gs[2])

y_pos = list(range(len(scenarios)))[::-1]
for i, (label, beta, se, p_val, col, marker) in enumerate(scenarios):
    yi    = y_pos[i]
    ci_lo = beta - 1.96 * se
    ci_hi = beta + 1.96 * se
    if p_val < ALPHA_BONF:
        ax_a.axhspan(yi - 0.4, yi + 0.4, color=COL_BONF, alpha=0.25, zorder=0)
    elif p_val < 0.05:
        ax_a.axhspan(yi - 0.4, yi + 0.4, color="#d1e5f0", alpha=0.35, zorder=0)
    ax_a.plot([ci_lo, ci_hi], [yi, yi], color=col, lw=1.5, zorder=2)
    ax_a.scatter([beta], [yi], color=col, marker=marker, s=60, zorder=3)

ax_a.axvline(0, color="grey", lw=0.8, ls="--")
ax_a.set_yticks(y_pos)
ax_a.set_yticklabels([s[0] for s in scenarios], fontsize=8)
ax_a.set_xlabel("β (95% CI)", fontsize=9)
ax_a.set_title("A  Scenarios", fontsize=10, loc="left", fontweight="bold")
from matplotlib.patches import Patch
leg_elems = [
    Patch(facecolor=COL_BONF, alpha=0.5, label=f"p < {ALPHA_BONF} (Bonferroni)"),
    Patch(facecolor="#d1e5f0", alpha=0.5, label="p < 0.05"),
]
ax_a.legend(handles=leg_elems, fontsize=7, loc="lower right")

ax_b.hist(sim_betas, bins=30, color="#b2d8b2", edgecolor="white", lw=0.5)
bonf_thresh_beta = np.sort(sim_betas)[-n_bonf_sig] if n_bonf_sig > 0 else np.inf
bins_b = np.histogram(sim_betas, bins=30)
bin_edges = bins_b[1]
for left, right, cnt in zip(bin_edges[:-1], bin_edges[1:], bins_b[0]):
    if (left + right) / 2 >= bonf_thresh_beta:
        ax_b.bar((left + right) / 2, cnt, width=(right - left) * 0.95,
                 color=COL_BONF, alpha=0.8, edgecolor="white")
ax_b.axvline(rar_row["median_beta"], color=COL_RAR, lw=1.5, ls="-",
             label=f"Median β={rar_row['median_beta']:.4f}")
ax_b.axvline(main_row["beta"], color=COL_MAIN, lw=1.5, ls="--",
             label=f"Original β={main_row['beta']:.4f}")
ax_b.set_xlabel("β (rarefied iteration)", fontsize=9)
ax_b.set_ylabel("Count", fontsize=9)
ax_b.set_title("B  Rarefied PGLS (200 iterations)", fontsize=10, loc="left", fontweight="bold")
ax_b.legend(fontsize=7)
# FIX F5B: put statistics text in a proper boxed annotation aligned with median line
median_x = rar_row["median_beta"]
ax_b_ylim = ax_b.get_ylim()
# Place text box just above x-axis, left of median line to use empty space
ax_b.annotate(
    f"{int(rar_frac*100)}% iterations p < 0.05\n"
    f"{int(rar_row['frac_bonf_sig']*100)}% Bonferroni-sig.",
    xy=(median_x, 0),
    xytext=(-60, 18), textcoords='offset points',
    fontsize=8, va='bottom', ha='center',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#888888',
              linewidth=0.8, alpha=0.9),
    arrowprops=dict(arrowstyle='->', color='#666666', lw=0.8)
)

ax_c.plot(n_range, [p * 100 for p in powers_05],   color=COL_ARC, lw=2,
          label=f"α=0.05 (n₈₀={n80_05})")
ax_c.plot(n_range, [p * 100 for p in powers_bonf], color=COL_ARC, lw=2, ls="--",
          label=f"Bonferroni α={ALPHA_BONF} (n₈₀={n80_bonf})")
ax_c.axhline(80, color="grey", lw=0.8, ls=":")
ax_c.axvline(n_obs,    color="grey",  lw=1.2, ls=":",  label=f"Current n={n_obs}")
ax_c.axvline(n80_05,   color=COL_ARC, lw=1.0, ls=":",  alpha=0.5)
ax_c.axvline(n80_bonf, color=COL_ARC, lw=1.0, ls="--", alpha=0.5)
ax_c.set_xlabel("Number of archaeal genera", fontsize=9)
# FIX F5C: more descriptive y-axis label
ax_c.set_ylabel("Statistical Power (%)", fontsize=9)
# FIX F5C: title references that effect size is estimated from bacterial result
ax_c.set_title("C  Archaeal PGLS power\n"
               r"(β$_{true}$ estimated from bacterial effect: β=+0.0145)",
               fontsize=9, loc="left", fontweight="bold")
ax_c.set_xlim(0, 1200)
ax_c.set_ylim(0, 100)
ax_c.legend(fontsize=7)
ax_c.text(n_obs + 15, 15, f"n={n_obs}\n(11%)", fontsize=7, color="grey")

fig.savefig(FIGURES / "fig5_robustness.png", dpi=300)
plt.close()
print("  Saved figures/fig5_robustness.png")

print("\nAll figures regenerated.")
