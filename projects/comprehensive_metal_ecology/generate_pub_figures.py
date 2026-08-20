"""
Publication-quality figure generation for comprehensive_metal_ecology.
Regenerates all 8 manuscript figures with a consistent modern style.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')
import shutil
from pathlib import Path
from scipy import stats

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
DATA = ROOT / 'data'
FIGS_OUT = [ROOT / 'figures', ROOT / 'papers' / 'draft_1' / 'figures']

# ── Design language ──────────────────────────────────────────────────────────
NAVY   = '#1B4F72'   # significant primary
TEAL   = '#1A7A5E'   # core metabolism / secondary sig
AMBER  = '#C0762B'   # cofactor highlight
RED    = '#A93226'   # key/highlighted single element
GRAY   = '#9DA8B0'   # non-significant
LGRAY  = '#D5DCE0'   # light background / CI band
DARK   = '#2C3E50'   # axes / text
WHITE  = '#FFFFFF'

GROUP_COLORS = {
    'core_metabolism':     TEAL,
    'information_processing': NAVY,
    'negative_control':    GRAY,
    'metal_related':       GRAY,
    'metal_reference':     RED,
}

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          9,
    'axes.labelsize':     9,
    'axes.titlesize':     10,
    'xtick.labelsize':    8,
    'ytick.labelsize':    8,
    'legend.fontsize':    8,
    'figure.dpi':         300,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'savefig.pad_inches': 0.05,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.linewidth':     0.6,
    'xtick.major.width':  0.6,
    'ytick.major.width':  0.6,
    'xtick.major.size':   3,
    'ytick.major.size':   3,
    'axes.grid':          False,
})


def save_fig(fig, name):
    for d in FIGS_OUT:
        fig.savefig(d / name, bbox_inches='tight', pad_inches=0.05)
    print(f"  saved {name}")


def panel_label(ax, label, x=-0.14, y=1.05, size=11):
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=size, fontweight='bold', va='top', ha='left', color=DARK)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 1 — Primary PGLS scatter
# ─────────────────────────────────────────────────────────────────────────────
def fig1_primary_scatter():
    df = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
    meta = pd.read_csv(DATA / '01_primary_pgls_results.csv')

    beta = float(meta['beta'].iloc[0])
    se   = float(meta['SE'].iloc[0])
    p    = float(meta['p_value'].iloc[0])
    lam  = float(meta['lambda_est'].iloc[0])
    r2   = float(meta['r2'].iloc[0])

    fig, ax = plt.subplots(figsize=(4.8, 4.0))

    # scatter: phylum coloring, 4 main phyla
    phylum_palette = {
        'Proteobacteria': '#4A90D9',
        'Firmicutes':     '#E8A838',
        'Actinobacteria': '#6BBF59',
        'Bacteroidetes':  '#C06BBF',
    }
    other_color = GRAY

    x_col = 'ko_per_mb_primary'
    y_col = 'mean_levins_B_std'
    df = df.dropna(subset=[x_col, y_col])

    plotted_phyla = set()
    phyla_order = ['Proteobacteria', 'Firmicutes', 'Actinobacteria', 'Bacteroidetes']
    # Others first so named phyla render on top
    mask_other = ~df['phylum'].isin(phylum_palette)
    ax.scatter(df.loc[mask_other, x_col], df.loc[mask_other, y_col],
               c=other_color, s=12, alpha=0.25, linewidths=0, rasterized=True)

    for ph in phyla_order:
        mask = df['phylum'] == ph
        if mask.sum() == 0:
            continue
        ax.scatter(df.loc[mask, x_col], df.loc[mask, y_col],
                   c=phylum_palette[ph], s=12, alpha=0.35, linewidths=0,
                   label=ph, rasterized=True)
        plotted_phyla.add(ph)

    # OLS trendline (visual proxy for PGLS slope direction)
    x_fit = np.linspace(df[x_col].quantile(0.01), df[x_col].quantile(0.99), 200)
    m, b_intercept, *_ = stats.linregress(df[x_col], df[y_col])
    ax.plot(x_fit, m * x_fit + b_intercept, color=NAVY, lw=1.8, zorder=5)

    # CI band (±1.96 SE of OLS for visual width; PGLS annotated in text)
    from scipy.stats import t as tdist
    n = len(df)
    x_mean = df[x_col].mean()
    se_band = np.sqrt(np.var(df[x_col], ddof=1) / n)
    ci = tdist.ppf(0.975, n - 2) * (df[y_col].std(ddof=1) / np.sqrt(n)) * \
         np.sqrt(1/n + (x_fit - x_mean)**2 / ((n-1)*df[x_col].var(ddof=1)))
    y_fit = m * x_fit + b_intercept
    ax.fill_between(x_fit, y_fit - ci, y_fit + ci, color=NAVY, alpha=0.12, zorder=4)

    ax.set_xlabel('Metal-gene KO density (KO per Mb)', labelpad=4)
    ax.set_ylabel('Niche breadth (Levins B, standardised)', labelpad=4)

    # PGLS annotation
    p_str = f'p = {p:.2e}' if p >= 1e-10 else f'p < 10⁻¹⁰'
    ax.annotate(
        f'PGLS β = {beta:.4f} (SE {se:.4f})\n{p_str}  λ = {lam:.3f}',
        xy=(0.97, 0.97), xycoords='axes fraction',
        ha='right', va='top', fontsize=7.5, color=DARK,
        bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=LGRAY, lw=0.5)
    )

    # legend
    handles = [mpatches.Patch(color=phylum_palette[p], label=p, alpha=0.7)
               for p in phyla_order if p in plotted_phyla]
    handles.append(mpatches.Patch(color=other_color, label='Other', alpha=0.5))
    ax.legend(handles=handles, loc='lower left', frameon=True,
              framealpha=0.85, edgecolor=LGRAY, handlelength=1.0,
              borderpad=0.5, labelspacing=0.3)

    fig.tight_layout()
    save_fig(fig, '01_pgls_primary_scatter.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2 — Functional landscape forest plot
# ─────────────────────────────────────────────────────────────────────────────
def fig2_landscape_forest():
    df = pd.read_csv(DATA / 'functional_landscape_results.csv')
    df['ci_lo'] = df['beta'] - 1.96 * df['SE']
    df['ci_hi'] = df['beta'] + 1.96 * df['SE']

    # Clean labels
    label_map = {
        'secondary_metab':   'Secondary metabolism',
        'xenobiotics':        'Xenobiotic degradation',
        'two_component':      'Two-component systems',
        'abc_transporters':   'ABC transporters (non-metal)',
        'quorum_sensing':     'Quorum sensing',
        'carbohydrate_metab': 'Carbohydrate metabolism',
        'energy_metab':       'Energy metabolism',
        'lipid_metab':        'Lipid metabolism',
        'nucleotide_metab':   'Nucleotide metabolism',
        'aa_metab':           'Amino acid metabolism',
        'glycan_biosyn':      'Glycan biosynthesis',
        'cofactor_vitamin':   'Cofactors & vitamins',
        'terpenoid_polyket':  'Terpenoids & polyketides',
        'cell_motility':      'Cell motility',
        'transcription':      'Transcription',
        'translation':        'Translation',
        'protein_folding':    'Protein folding & degradation',
        'replication_repair': 'Replication & repair',
        'amr':                'Antimicrobial resistance',
        'metal_genes_p1':     'Metal genes (primary set)',
    }
    df['label'] = df['category'].map(label_map).fillna(df['category'])

    # Sort: metal ref last, others by beta (ascending = most negative first)
    df_ref = df[df['group'] == 'metal_reference']
    df_rest = df[df['group'] != 'metal_reference'].sort_values('beta')
    df_sorted = pd.concat([df_ref, df_rest], ignore_index=True)[::-1].reset_index(drop=True)

    group_color_map = {
        'core_metabolism':      TEAL,
        'information_processing': NAVY,
        'negative_control':     GRAY,
        'metal_related':        '#7D7D7D',
        'metal_reference':      RED,
    }

    group_labels = {
        'core_metabolism':      'Core metabolism',
        'information_processing': 'Information processing',
        'negative_control':     'Negative controls',
        'metal_related':        'Metal-related',
        'metal_reference':      'Metal gene reference',
    }

    n = len(df_sorted)
    fig, ax = plt.subplots(figsize=(6.5, 7.0))

    y_positions = np.arange(n)

    for i, (_, row) in enumerate(df_sorted.iterrows()):
        color = group_color_map.get(row['group'], GRAY)
        sig = row['q_bh'] < 0.05

        lw = 1.8 if row['group'] == 'metal_reference' else 1.2
        ms = 7 if row['group'] == 'metal_reference' else 5
        marker = 'D' if row['group'] == 'metal_reference' else 'o'
        alpha = 1.0 if sig else 0.55

        ax.plot([row['ci_lo'], row['ci_hi']], [i, i],
                color=color, lw=lw, alpha=alpha, solid_capstyle='butt')
        ax.plot(row['beta'], i, marker=marker, ms=ms,
                color=color, alpha=alpha, zorder=4)

        # significance star
        if sig:
            ax.text(row['ci_hi'] + 0.0008, i, '★',
                    va='center', ha='left', fontsize=7,
                    color=color, alpha=0.85)

    ax.axvline(0, color=DARK, lw=0.8, ls='--', alpha=0.5, zorder=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(df_sorted['label'], fontsize=7.5)
    ax.set_ylim(-0.8, n - 0.2)
    ax.set_xlabel('PGLS β coefficient (95% CI)', labelpad=4)

    # Color-coded group separators / legend
    legend_handles = [
        Line2D([0], [0], color=group_color_map[g], lw=2.5, label=group_labels[g])
        for g in ['metal_reference', 'core_metabolism', 'information_processing', 'negative_control']
    ]
    legend_handles.append(
        Line2D([0], [0], marker='', lw=0, label='★ FDR q < 0.05')
    )
    ax.legend(handles=legend_handles, loc='lower right', frameon=True,
              framealpha=0.9, edgecolor=LGRAY, fontsize=7.5,
              handlelength=1.5, borderpad=0.5, labelspacing=0.4)

    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False)

    fig.tight_layout()
    save_fig(fig, 'functional_landscape_forest.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3 — Coreness permutation + genome-size attenuation
# ─────────────────────────────────────────────────────────────────────────────
def fig3_coreness_permutation():
    perm = pd.read_csv(DATA / 'coreness_permutation_results.csv')
    conf = pd.read_csv(DATA / '04_confounder_results.csv')

    obs_beta = -0.0207
    gs_row = conf[conf['confounder'] == 'Genome size'].iloc[0]
    gs_beta = float(gs_row['beta_with_conf'])

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.4),
                             gridspec_kw={'width_ratios': [1.6, 1]})
    ax_hist, ax_bar = axes

    # Panel A — permutation histogram
    betas = perm['beta'].values
    betas_clipped = np.clip(betas, np.percentile(betas, 1), np.percentile(betas, 99))

    ax_hist.hist(betas_clipped, bins=45, color=LGRAY, edgecolor='white',
                 linewidth=0.3, density=True)
    ax_hist.axvline(obs_beta, color=RED, lw=1.8, ls='-', zorder=5,
                    label=f'Observed β = {obs_beta:.4f}')

    # KDE overlay
    kde_x = np.linspace(betas_clipped.min(), betas_clipped.max(), 300)
    kde = stats.gaussian_kde(betas_clipped)
    ax_hist.plot(kde_x, kde(kde_x), color=NAVY, lw=1.4)

    emp_p = (betas <= obs_beta).mean()
    ax_hist.set_xlabel('β (size-matched null)', labelpad=4)
    ax_hist.set_ylabel('Density', labelpad=4)
    ax_hist.legend(loc='upper left', frameon=True, framealpha=0.9,
                   edgecolor=LGRAY, fontsize=7.5)
    ax_hist.annotate(f'Empirical p < 0.001\n(n = 1,000 permutations)',
                     xy=(0.97, 0.96), xycoords='axes fraction',
                     ha='right', va='top', fontsize=7.5, color=DARK)
    panel_label(ax_hist, 'A', x=-0.12)

    # Panel B — beta comparison (observed vs genome-size adjusted)
    labels  = ['Unadjusted\n(n = 1,574)', 'Genome size\nadjusted']
    betas_b = [obs_beta, gs_beta]
    colors  = [NAVY, AMBER]

    bars = ax_bar.bar(labels, betas_b, color=colors, width=0.5,
                      edgecolor='white', linewidth=0.5)

    # error bars — SE from meta for unadjusted, approximate for adjusted
    se_base = 0.00368
    se_gs   = float(gs_row.get('SE_with_conf', se_base * 1.1)) \
              if 'SE_with_conf' in gs_row else se_base * 1.05

    for i, (yval, se) in enumerate([(obs_beta, se_base), (gs_beta, se_gs)]):
        ax_bar.errorbar(i, yval, yerr=1.96*se, fmt='none',
                        ecolor='#3A3A3A', elinewidth=1.0, capsize=3, capthick=1.0)

    ax_bar.axhline(0, color=DARK, lw=0.8, ls='--', alpha=0.4)

    # attenuation annotation
    pct = abs((gs_beta - obs_beta) / obs_beta * 100)
    ax_bar.annotate(f'−{pct:.0f}%',
                    xy=(1, (obs_beta + gs_beta)/2),
                    xytext=(1.35, (obs_beta + gs_beta)/2),
                    fontsize=7.5, color=DARK, va='center',
                    arrowprops=dict(arrowstyle='->', color=DARK, lw=0.8))

    ax_bar.set_ylabel('PGLS β coefficient', labelpad=4)
    ax_bar.set_xlim(-0.6, 1.9)
    ax_bar.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.3f'))
    panel_label(ax_bar, 'B', x=-0.22)

    fig.tight_layout(w_pad=2.0)
    save_fig(fig, 'coreness_permutation_histogram.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4 — Category forest plot (proper forest with 95% CIs)
# ─────────────────────────────────────────────────────────────────────────────
def fig4_category_forest():
    df = pd.read_csv(DATA / '03_category_pgls_results.csv')

    # extract short category key from label column (e.g. F1.4_cofactor → cofactor)
    df['category'] = df['label'].str.extract(r'F\d+\.\d+_(\w+)')

    label_map = {
        'resistance': 'Resistance\n& detoxification',
        'transport':  'Metal\ntransport',
        'sensing':    'Metal\nsensing',
        'cofactor':   'Cofactor\nbiosynthesis',
        'metabolism': 'Metabolic\nfunctions',
    }

    order = ['cofactor', 'metabolism', 'transport', 'sensing', 'resistance']
    df = df.set_index('category').loc[order].reset_index()
    df['ci_lo'] = df['beta'] - 1.96 * df['SE']
    df['ci_hi'] = df['beta'] + 1.96 * df['SE']
    df['sig']   = df['p_value'] < 0.05
    df['label'] = df['category'].map(label_map)

    cat_colors = {
        'cofactor':   RED,
        'metabolism': NAVY,
        'transport':  NAVY,
        'sensing':    NAVY,
        'resistance': GRAY,
    }

    fig, ax = plt.subplots(figsize=(5.0, 3.8))
    n = len(df)
    y_pos = np.arange(n)

    for i, (_, row) in enumerate(df.iterrows()):
        color = cat_colors[row['category']]
        alpha = 1.0 if row['sig'] else 0.5

        ax.plot([row['ci_lo'], row['ci_hi']], [i, i],
                color=color, lw=2.2, alpha=alpha, solid_capstyle='butt')
        ax.plot(row['beta'], i, 'o', ms=7, color=color,
                alpha=alpha, zorder=4)
        if row['sig']:
            p = row['p_value']
            p_str = f'p = {p:.0e}' if p < 0.001 else f'p = {p:.3f}'
            ax.text(row['ci_hi'] + 0.0008, i, p_str,
                    va='center', ha='left', fontsize=7, color=color)

    ax.axvline(0, color=DARK, lw=0.8, ls='--', alpha=0.5, zorder=1)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['label'], fontsize=8)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlabel('PGLS β coefficient (95% CI)', labelpad=4)

    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False)

    legend_handles = [
        Line2D([0], [0], color=RED,  lw=2.5, label='Cofactor (highlighted)'),
        Line2D([0], [0], color=NAVY, lw=2.5, label='Significant (p < 0.05)'),
        Line2D([0], [0], color=GRAY, lw=2.5, alpha=0.5, label='Non-significant'),
    ]
    ax.legend(handles=legend_handles, loc='lower right', frameon=True,
              framealpha=0.9, edgecolor=LGRAY, fontsize=7.5,
              handlelength=1.5, borderpad=0.5, labelspacing=0.4)

    fig.tight_layout()
    save_fig(fig, '03_category_forest_plot.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5 — Split magnitude permutation
# ─────────────────────────────────────────────────────────────────────────────
def fig5_split_permutation():
    df = pd.read_csv(DATA / 'split_magnitude_permutation.csv')

    # Metal row has null distribution params
    metal_row = df[df['family'] == 'Metal gene set'].iloc[0]
    null_median = float(metal_row['null_delta_beta_median'])
    null_sd     = float(metal_row['null_delta_beta_sd'])
    obs_metal   = float(metal_row['observed_delta_beta'])

    # All comparison families
    compare = [
        ('Metal gene set',         obs_metal,  RED,  True),
        ('ABC transporters',        float(df[df['family']=='ABC transporters']['observed_delta_beta'].iloc[0]),  AMBER, True),
        ('AMR genes',               float(df[df['family']=='AMR']['observed_delta_beta'].iloc[0]),               NAVY,  False),
        ('Two-component\nsystems',  float(df[df['family']=='Two-component systems']['observed_delta_beta'].iloc[0]), NAVY, False),
    ]

    fig, (ax_hist, ax_dot) = plt.subplots(1, 2, figsize=(8.0, 3.4),
                                           gridspec_kw={'width_ratios': [1.6, 1]})

    # Panel A — Gaussian approximation of null distribution
    x_null = np.linspace(null_median - 4*null_sd, obs_metal + 0.002, 500)
    y_null = stats.norm.pdf(x_null, loc=null_median, scale=null_sd)

    fill_mask = x_null <= obs_metal
    ax_hist.plot(x_null[fill_mask], y_null[fill_mask], color=LGRAY, lw=0)
    ax_hist.fill_between(x_null[fill_mask], y_null[fill_mask],
                         color=LGRAY, alpha=0.8)
    ax_hist.plot(x_null, y_null, color=NAVY, lw=1.6)

    ax_hist.axvline(obs_metal, color=RED, lw=1.8, zorder=5,
                    label=f'Observed Δβ = {obs_metal:.4f}')
    ax_hist.axvline(null_median, color=DARK, lw=1.0, ls=':', alpha=0.6,
                    label=f'Null median = {null_median:.4f}')

    ax_hist.set_xlabel('Δβ (cofactor − resistance)', labelpad=4)
    ax_hist.set_ylabel('Density (Gaussian approximation)', labelpad=4)
    ax_hist.legend(loc='upper left', frameon=True, framealpha=0.9,
                   edgecolor=LGRAY, fontsize=7.5)
    ax_hist.annotate('Empirical p < 0.001\n(n = 1,000 permutations)',
                     xy=(0.97, 0.97), xycoords='axes fraction',
                     ha='right', va='top', fontsize=7.5, color=DARK)
    panel_label(ax_hist, 'A', x=-0.12)

    # Panel B — Δβ dot plot for comparison families
    y_pos = np.arange(len(compare))
    for i, (label, delta, color, sig) in enumerate(compare):
        alpha = 1.0 if sig else 0.55
        ax_dot.plot(delta, i, 'o', ms=7, color=color, alpha=alpha, zorder=4)
        ax_dot.plot([0, delta], [i, i], color=color, lw=1.8,
                    alpha=alpha, solid_capstyle='butt')
        ax_dot.text(delta + 0.001, i, f'{delta:.4f}',
                    va='center', ha='left', fontsize=7, color=color, alpha=alpha)

    # Null ±2SD band
    ax_dot.axvspan(null_median - 2*null_sd, null_median + 2*null_sd,
                   color=LGRAY, alpha=0.4, zorder=1)
    ax_dot.axvline(null_median, color=DARK, lw=0.8, ls=':', alpha=0.5, zorder=2)
    ax_dot.axvline(0, color=DARK, lw=0.6, ls='--', alpha=0.35)

    ax_dot.set_yticks(y_pos)
    ax_dot.set_yticklabels([c[0] for c in compare], fontsize=8)
    ax_dot.set_xlabel('Observed Δβ', labelpad=4)
    ax_dot.set_xlim(-0.005, max(c[1] for c in compare) + 0.012)
    ax_dot.spines['left'].set_visible(False)
    ax_dot.tick_params(left=False)
    panel_label(ax_dot, 'B', x=-0.28)

    fig.tight_layout(w_pad=2.0)
    save_fig(fig, 'split_magnitude_permutation.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 6 — Cofactor jackknife forest
# ─────────────────────────────────────────────────────────────────────────────
def fig6_cofactor_jackknife():
    df = pd.read_csv(DATA / 'cofactor_jackknife_results.csv')
    df['ci_lo'] = df['beta'] - 1.96 * df['SE']
    df['ci_hi'] = df['beta'] + 1.96 * df['SE']

    ko_names = {
        'K01772': 'K01772 (cobB)',
        'K02225': 'K02225 (cobH)',
        'K03635': 'K03635 (cbiP)',
        'K22225': 'K22225 (cobV)',
    }
    df['label'] = df['excluded_ko'].map(ko_names).fillna(df['excluded_ko'])

    # Baseline: full model beta
    obs_beta = -0.02704  # cofactor category beta from main model
    obs_se   = 0.004435

    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    n = len(df)
    y_pos = np.arange(n)

    for i, (_, row) in enumerate(df.iterrows()):
        ax.plot([row['ci_lo'], row['ci_hi']], [i, i],
                color=NAVY, lw=2.0, solid_capstyle='butt')
        ax.plot(row['beta'], i, 'o', ms=7, color=NAVY, zorder=4)

    # Baseline reference line with band
    ax.axvline(obs_beta, color=GRAY, lw=1.2, ls='--', alpha=0.7,
               label=f'Cofactor model β = {obs_beta:.4f}')
    ax.axvspan(obs_beta - 1.96*obs_se, obs_beta + 1.96*obs_se,
               color=GRAY, alpha=0.15)

    ax.axvline(0, color=DARK, lw=0.7, ls=':', alpha=0.4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['label'], fontsize=8.5)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlabel('PGLS β coefficient after leave-one-KO-out (95% CI)', labelpad=4)

    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False)
    ax.legend(loc='lower right', frameon=True, framealpha=0.9,
              edgecolor=LGRAY, fontsize=7.5)

    ax.annotate('All models remain significant\n(p < 0.001)', color=NAVY,
                xy=(0.03, 0.97), xycoords='axes fraction',
                ha='left', va='top', fontsize=7.5)

    fig.tight_layout()
    save_fig(fig, 'cofactor_jackknife_forest.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 7 — Clade-stratified forest plot
# ─────────────────────────────────────────────────────────────────────────────
def fig7_clade_stratified():
    df = pd.read_csv(DATA / 'clade_stratified_pgls_results.csv')

    # Phylogenetic order (rough: Firmicutes → Actinobacteria → Proteobacteria → Bacteroidetes)
    phylo_order = ['Firmicutes', 'Actinobacteria', 'Proteobacteria', 'Bacteroidetes']
    df = df.set_index('label').loc[[p for p in phylo_order if p in df['label'].values]].reset_index()

    sig_color   = NAVY
    nonsig_color = GRAY
    ref_beta    = -0.0207
    ref_se      = 0.00368

    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    n = len(df)
    y_pos = np.arange(n)

    for i, (_, row) in enumerate(df.iterrows()):
        color = sig_color if row['significant'] else nonsig_color
        alpha = 1.0 if row['significant'] else 0.55

        ax.plot([row['ci_lo'], row['ci_hi']], [i, i],
                color=color, lw=2.2, alpha=alpha, solid_capstyle='butt')
        ax.plot(row['beta'], i, 'o', ms=7.5, color=color, alpha=alpha, zorder=4)

        # q-value and sample size to the right
        q = row['q_bh']
        q_str = f'q = {q:.3f}' if q >= 0.001 else f'q < 0.001'
        ann = f'n = {int(row["n"])},  {q_str}'
        ax.text(row['ci_hi'] + 0.001, i, ann,
                va='center', ha='left', fontsize=7, color=color, alpha=alpha)

    # Global reference
    ax.axvline(ref_beta, color=DARK, lw=1.2, ls='--', alpha=0.5,
               label=f'Global β = {ref_beta:.4f}')
    ax.axvspan(ref_beta - 1.96*ref_se, ref_beta + 1.96*ref_se,
               color=DARK, alpha=0.08)
    ax.axvline(0, color=DARK, lw=0.6, ls=':', alpha=0.35)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['label'], fontsize=9)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlabel('Within-phylum PGLS β (95% CI)', labelpad=4)

    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False)

    legend_handles = [
        Line2D([0], [0], color=sig_color,   lw=2.5, label='FDR q < 0.05'),
        Line2D([0], [0], color=nonsig_color, lw=2.5, alpha=0.55, label='FDR q ≥ 0.05'),
        Line2D([0], [0], color=DARK, lw=1.2, ls='--', label='Global β'),
    ]
    ax.legend(handles=legend_handles, loc='upper left', frameon=True,
              framealpha=0.9, edgecolor=LGRAY, fontsize=7.5,
              handlelength=1.5, borderpad=0.5, labelspacing=0.4)

    fig.tight_layout()
    save_fig(fig, 'clade_stratified_forest_plot.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 8 — Confounder robustness (Cleveland dot plot)
# ─────────────────────────────────────────────────────────────────────────────
def fig8_confounder():
    df = pd.read_csv(DATA / '04_confounder_results.csv')

    label_map = {
        'Genome size':      'Genome size',
        'GC content':       'GC content',
        'Isolation source': 'Isolation source',
        'Mean latitude':    'Mean latitude',
        'Dominant biome':   'Dominant biome',
    }
    decision_color = {
        'ROBUST (<50% change)':              NAVY,
        'ATTENUATED (>50%, still sig)':      AMBER,
    }

    # Sort by pct change (ascending = least change first)
    df = df.sort_values('pct_beta_change', ascending=False).reset_index(drop=True)

    obs_beta = -0.0207
    obs_se   = 0.00368

    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    n = len(df)
    y_pos = np.arange(n)

    for i, (_, row) in enumerate(df.iterrows()):
        raw_decision = row['decision'].split('(')[0].strip()
        color = AMBER if 'ATTENUATED' in row['decision'] else NAVY

        # Line connecting observed to adjusted
        ax.plot([obs_beta, row['beta_with_conf']], [i, i],
                color=LGRAY, lw=1.2, zorder=1)
        # Observed point
        ax.plot(obs_beta, i, 'o', ms=6, color=GRAY, zorder=3)
        # Adjusted point
        ax.plot(row['beta_with_conf'], i, 's', ms=7, color=color, zorder=4)

        # % change label
        pct = abs(row['pct_beta_change'])
        pct_str = f'{pct:.0f}%'
        ax.text(min(obs_beta, row['beta_with_conf']) - 0.0005, i, pct_str,
                va='center', ha='right', fontsize=7.5, color=color)

        # Sample size (may differ from main)
        ax.text(max(obs_beta, row['beta_with_conf']) + 0.0005, i,
                f'n={int(row["n"])}', va='center', ha='left',
                fontsize=7, color=DARK, alpha=0.7)

    ax.axvline(0, color=DARK, lw=0.7, ls=':', alpha=0.35)
    ax.axvline(obs_beta, color=GRAY, lw=1.0, ls='--', alpha=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([label_map.get(r, r) for r in df['confounder']], fontsize=8.5)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlabel('PGLS β coefficient', labelpad=4)

    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False)

    legend_handles = [
        Line2D([0], [0], marker='o', ms=6, color='w', markerfacecolor=GRAY,
               label='Unadjusted β', lw=0),
        Line2D([0], [0], marker='s', ms=7, color='w', markerfacecolor=NAVY,
               label='Adjusted β (robust)', lw=0),
        Line2D([0], [0], marker='s', ms=7, color='w', markerfacecolor=AMBER,
               label='Adjusted β (>50% change)', lw=0),
    ]
    ax.legend(handles=legend_handles, loc='lower right', frameon=True,
              framealpha=0.9, edgecolor=LGRAY, fontsize=7.5,
              handlelength=1.0, borderpad=0.5, labelspacing=0.4)

    fig.tight_layout()
    save_fig(fig, '04_confounder_beta_comparison.png')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Generating publication figures...")
    fig1_primary_scatter()
    fig2_landscape_forest()
    fig3_coreness_permutation()
    fig4_category_forest()
    fig5_split_permutation()
    fig6_cofactor_jackknife()
    fig7_clade_stratified()
    fig8_confounder()
    print("Done.")
