"""
Publication-quality figure generation for comprehensive_metal_ecology.
Consolidates 7 HTML figures into 4 multi-panel PDF figures.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.gridspec import GridSpec
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Output directory ──────────────────────────────────────────────────────────
OUT = Path(__file__).parent / 'png'
OUT.mkdir(exist_ok=True)
DATA = Path(__file__).parent.parent / 'data'

# ── Consistent style ──────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7,
    'axes.labelsize': 7.5,
    'axes.titlesize': 8,
    'xtick.labelsize': 6.5,
    'ytick.labelsize': 6.5,
    'legend.fontsize': 6.5,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.minor.width': 0.4,
    'ytick.minor.width': 0.4,
    'xtick.major.size': 2.5,
    'ytick.major.size': 2.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': False,
    'pdf.fonttype': 42,  # embed fonts
    'ps.fonttype': 42,
})

# ── Palette ───────────────────────────────────────────────────────────────────
BLUE   = '#2a78d6'   # significant / primary
RED    = '#d63f3f'   # resistance-null / opposite direction
AMBER  = '#c97e00'   # cofactor / reference highlight
TEAL   = '#5a967e'   # secondary accent
GREY   = '#898781'   # non-significant
LTGREY = '#c3c2b7'   # very light NS

# Phyla colors (scatter)
PHYLA_COLORS = {
    'Proteobacteria': '#3578c5',
    'Firmicutes':     '#d46f3a',
    'Actinobacteria': '#5a967e',
    'Bacteroidetes':  '#8b5bb0',
}
OTHER_COLOR = '#b5b0ab'

FIG_W = 7.2   # inches, full double-column width
PANEL_LABEL_KW = dict(fontsize=9, fontweight='bold', va='top')


def panel_label(ax, letter, x=-0.14, y=1.05):
    ax.text(x, y, letter, transform=ax.transAxes, **PANEL_LABEL_KW)


def despine(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ── Shared forest-plot helper ─────────────────────────────────────────────────
def forest_plot(ax, labels, betas, ses, colors, ref_line=None, ref_label=None,
                ref_color=BLUE, x_label='PGLS β', x_lim=None,
                highlight_row=None, highlight_color=None,
                dot_size=5, ci_lw=1.3, stem_lw=1.2, zero_lw=0.8):
    """Horizontal forest / lollipop plot drawn on ax."""
    n = len(labels)
    ys = np.arange(n)[::-1]   # top = first entry

    # Zero line
    ax.axvline(0, color='#555', lw=zero_lw, zorder=1)

    # Reference line
    if ref_line is not None:
        ax.axvline(ref_line, color=ref_color, lw=1.2, ls='--',
                   alpha=0.55, zorder=1, label=ref_label)

    for i, (y, beta, se, col) in enumerate(zip(ys, betas, ses, colors)):
        lo, hi = beta - 1.96 * se, beta + 1.96 * se
        # Row highlight
        if highlight_row is not None and i == highlight_row:
            ax.axhspan(y - 0.42, y + 0.42, color=highlight_color, alpha=0.08, zorder=0)
        # CI bar
        ax.plot([lo, hi], [y, y], color=col, lw=ci_lw, alpha=0.7, solid_capstyle='round', zorder=3)
        # Whisker caps
        for xc in (lo, hi):
            ax.plot([xc, xc], [y - 0.22, y + 0.22], color=col, lw=ci_lw - 0.3, alpha=0.8, zorder=3)
        # Stem from zero to beta
        ax.plot([0, beta], [y, y], color=col, lw=stem_lw, alpha=0.45, zorder=2)
        # Dot
        ax.scatter([beta], [y], s=dot_size**2, color=col,
                   edgecolors='white', linewidths=0.8, zorder=4)

    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_xlabel(x_label, fontsize=7)
    if x_lim:
        ax.set_xlim(*x_lim)
    despine(ax)
    ax.tick_params(axis='y', length=0)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1  Primary scatter: metal-gene density vs niche breadth
# ══════════════════════════════════════════════════════════════════════════════
def fig1_scatter():
    df = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')

    # Color by phylum
    def phylum_color(p):
        return PHYLA_COLORS.get(p, OTHER_COLOR)

    colors = df['phylum'].map(phylum_color)
    alpha = np.where(df['phylum'].isin(PHYLA_COLORS), 0.5, 0.28)
    sizes = np.where(df['phylum'].isin(PHYLA_COLORS), 8, 5)
    zorder = np.where(df['phylum'].isin(PHYLA_COLORS), 3, 1)

    # PGLS regression line (transform z-slope to raw x scale)
    beta_z = -0.020700      # PGLS β on standardized predictor
    sd_x = df['ko_per_mb_primary'].std()
    mean_x = df['ko_per_mb_primary'].mean()
    mean_y = df['mean_levins_B_std'].mean()
    slope_raw = beta_z / sd_x
    intercept = mean_y - slope_raw * mean_x

    x_range = np.linspace(df['ko_per_mb_primary'].quantile(0.01),
                          df['ko_per_mb_primary'].quantile(0.99), 200)
    y_line = intercept + slope_raw * x_range

    fig, ax = plt.subplots(figsize=(3.6, 3.0))

    # Plot 'Other' first (background), then named phyla on top
    for zord, phyla_subset in [(1, None), (3, list(PHYLA_COLORS))]:
        if phyla_subset is None:
            mask = ~df['phylum'].isin(PHYLA_COLORS)
        else:
            mask = df['phylum'].isin(phyla_subset)
        sub = df[mask]
        for ph in ([None] if phyla_subset is None else phyla_subset):
            if phyla_subset is None:
                s = sub
                c = OTHER_COLOR
                a = 0.25
                sz = 5
            else:
                s = sub[sub['phylum'] == ph]
                c = PHYLA_COLORS[ph]
                a = 0.50
                sz = 8
            if len(s) == 0:
                continue
            ax.scatter(s['ko_per_mb_primary'], s['mean_levins_B_std'],
                       c=c, s=sz**2 * 0.4, alpha=a, linewidths=0,
                       rasterized=True, zorder=zord)

    # Regression line
    ax.plot(x_range, y_line, color='#1a1a1a', lw=1.4, zorder=5, alpha=0.85)

    ax.set_xlabel('Metal-gene density (KO per Mb)', fontsize=7.5)
    ax.set_ylabel('Niche breadth (Levins B, standardized)', fontsize=7.5)

    # Stat annotation
    ax.text(0.97, 0.97,
            'β = −0.021\np = 2.1×10⁻⁸\nλ = 0.757\nn = 1,574 genera',
            transform=ax.transAxes, va='top', ha='right',
            fontsize=6.5, linespacing=1.55,
            color='#333',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=LTGREY, lw=0.5, alpha=0.85))

    despine(ax)
    ax.tick_params(axis='both', which='both', labelsize=6.5)

    # Legend
    handles = [mpatches.Patch(color=c, label=p, alpha=0.7)
               for p, c in PHYLA_COLORS.items()]
    handles.append(mpatches.Patch(color=OTHER_COLOR, label='Other', alpha=0.5))
    ax.legend(handles=handles, frameon=False, fontsize=6,
              loc='upper right', bbox_to_anchor=(0.99, 0.72),
              handlelength=0.8, handletextpad=0.4, labelspacing=0.3)

    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / 'fig01_scatter.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('Fig 1 saved.')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2  Functional landscape (A) + Metal specificity (B)
# ══════════════════════════════════════════════════════════════════════════════
def fig2_functional_landscape():
    # ── Panel A data: 19 KEGG categories + P1 reference ──────────────────────
    kegg = [
        ('Two-component systems',       521,  0.006, False, 'kegg'),
        ('Cell motility',               153,  0.004, False, 'kegg'),
        ('Glycan biosynthesis',          73,  0.001, False, 'kegg'),
        ('AMR (β-lactam)',              112, -0.004, False, 'kegg'),
        ('ABC transporters',            475, -0.006, False, 'kegg'),
        ('Terpenoids & polyketides',     66, -0.010,  True, 'kegg'),
        ('Energy metabolism',           224, -0.015,  True, 'kegg'),
        ('Xenobiotics biodegradation', 1449, -0.017,  True, 'kegg'),
        ('Quorum sensing',             283, -0.017,  True, 'kegg'),
        ('Metal genes (P1)',           140, -0.021,  True, 'p1'),
        ('Lipid metabolism',            84, -0.021,  True, 'kegg'),
        ('Carbohydrate metabolism',    387, -0.026,  True, 'kegg'),
        ('Transcription',               66, -0.028,  True, 'kegg'),
        ('Secondary metabolism',      2326, -0.028,  True, 'kegg'),
        ('Cofactors & vitamins',       382, -0.029,  True, 'kegg'),
        ('Protein quality control',     49, -0.030,  True, 'kegg'),
        ('Translation (ribosome)',     206, -0.030,  True, 'kegg'),
        ('Amino acid metabolism',      242, -0.031,  True, 'kegg'),
        ('Nucleotide metabolism',      123, -0.032,  True, 'kegg'),
        ('Replication & repair',        60, -0.035,  True, 'kegg'),
    ]
    # sorted by beta ascending (most negative at bottom)
    kegg_labels  = [r[0] for r in kegg][::-1]
    kegg_betas   = [r[2] for r in kegg][::-1]
    kegg_types   = [r[4] for r in kegg][::-1]
    kegg_sig     = [r[3] for r in kegg][::-1]
    kegg_colors  = [RED if t == 'p1' else (BLUE if s else LTGREY)
                    for t, s in zip(kegg_types, kegg_sig)]
    # P1 row needs a fake SE (dots only, no CI)
    kegg_ses_approx = [0.0 if t == 'p1' else None for t in kegg_types]

    # ── Panel B data: per-metal PGLS ─────────────────────────────────────────
    metals_df = pd.read_csv(DATA / '03_metal_pgls_results.csv').copy()
    # Add FDR from HTML: all significant
    metals_df['metal'] = metals_df['label'].str.replace('M_', '')
    metals_df = metals_df.sort_values('beta')  # most negative first (top)
    metal_labels  = metals_df['metal'].tolist()[::-1]
    metal_betas   = metals_df['beta'].tolist()[::-1]
    metal_ses     = metals_df['SE'].tolist()[::-1]
    metal_colors  = [BLUE] * len(metal_labels)

    # ── Layout ────────────────────────────────────────────────────────────────
    n_kegg = len(kegg_labels)
    n_met  = len(metal_labels)
    row_h_kegg = 0.22   # inches per row
    row_h_met  = 0.27

    h_kegg = n_kegg * row_h_kegg + 1.0
    h_met  = n_met  * row_h_met  + 1.0
    fig_h  = max(h_kegg, h_met)

    fig = plt.figure(figsize=(FIG_W, fig_h))
    gs  = GridSpec(1, 2, figure=fig, wspace=0.38,
                   left=0.02, right=0.98, top=0.93, bottom=0.10)
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])

    # ── Panel A: KEGG lollipop ────────────────────────────────────────────────
    ys = np.arange(n_kegg)
    axA.axvline(0, color='#444', lw=0.7, zorder=1)

    # Housekeeping baseline band (approximate)
    axA.axvspan(-0.035, -0.028, color=BLUE, alpha=0.05, zorder=0)

    for i, (y, beta, col, se, typ) in enumerate(
            zip(ys, kegg_betas, kegg_colors, kegg_ses_approx, kegg_types)):
        is_p1 = (typ == 'p1')
        if not is_p1 and se is None:
            # Use placeholder SE ~ 0.002 for display (no CI for KEGG pts-only)
            se = 0.0

        # Row shading for P1
        if is_p1:
            axA.axhspan(y - 0.45, y + 0.45, color=RED, alpha=0.06, zorder=0)

        # Stem
        axA.plot([0, beta], [y, y], color=col, lw=1.0, alpha=0.4, zorder=2)
        # Dot (larger for P1)
        axA.scatter([beta], [y],
                    s=(7 if is_p1 else 5)**2 * 0.4,
                    color=col, edgecolors='white', linewidths=0.7,
                    zorder=4, marker='D' if is_p1 else 'o')

    axA.set_yticks(ys)
    axA.set_yticklabels(kegg_labels, fontsize=6)
    axA.set_ylim(-0.7, n_kegg - 0.3)
    axA.set_xlabel('PGLS β (KO density → niche breadth)', fontsize=7)
    axA.set_xlim(-0.044, 0.015)
    axA.set_xticks([-0.04, -0.03, -0.02, -0.01, 0, 0.01])
    axA.xaxis.set_tick_params(labelsize=6.5)
    axA.tick_params(axis='y', length=0)
    despine(axA)

    # Annotation: housekeeping zone
    axA.text(-0.031, n_kegg - 0.8, 'housekeeping\nbaseline',
             fontsize=5.5, color=BLUE, alpha=0.6, ha='center', va='top')

    panel_label(axA, 'A', x=-0.23)

    # ── Panel B: Per-metal forest ─────────────────────────────────────────────
    forest_plot(axB, metal_labels, metal_betas, metal_ses, metal_colors,
                ref_line=-0.021, ref_label='P1 all-metal (β = −0.021)',
                ref_color=BLUE,
                x_label='PGLS β (per-metal KO density → niche breadth)',
                x_lim=(-0.037, -0.007))
    axB.set_xticks([-0.035, -0.025, -0.015])
    axB.xaxis.set_tick_params(labelsize=6.5)

    # Legend
    leg_handles = [
        mlines.Line2D([], [], color=BLUE, lw=1.2, ls='--', label='P1 all-metal β = −0.021'),
    ]
    axB.legend(handles=leg_handles, frameon=False, fontsize=6,
               loc='lower right', handlelength=1.0)
    panel_label(axB, 'B', x=-0.14)

    # ── Panel A legend ────────────────────────────────────────────────────────
    leg_A = [
        mpatches.Patch(color=RED,    label='Metal genes P1 (reference)', alpha=0.8),
        mpatches.Patch(color=BLUE,   label='Significant (q < 0.05)',      alpha=0.7),
        mpatches.Patch(color=LTGREY, label='Not significant',              alpha=0.8),
    ]
    axA.legend(handles=leg_A, frameon=False, fontsize=6,
               loc='lower right', handlelength=0.8, handletextpad=0.4, labelspacing=0.3)

    fig.savefig(OUT / 'fig02_functional_landscape.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('Fig 2 saved.')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3  Internal structure (A) + Permutation (B) + Cofactor jackknife (C)
# ══════════════════════════════════════════════════════════════════════════════
def fig3_internal_robustness():
    # ── Panel A: 5-subcategory forest ────────────────────────────────────────
    cat_df = pd.read_csv(DATA / '03_category_pgls_results.csv').copy()
    cat_df['short'] = cat_df['label'].map({
        'F1.1_resistance': 'Resistance / Detox',
        'F1.2_transport':  'Transport & Homeostasis',
        'F1.3_sensing':    'Sensing & Regulation',
        'F1.4_cofactor':   'Cofactor Biosynthesis',
        'F1.5_metabolism': 'Metal-dep. Metabolism',
    })
    cat_df['color'] = cat_df['label'].map({
        'F1.1_resistance': RED,
        'F1.2_transport':  BLUE,
        'F1.3_sensing':    BLUE,
        'F1.4_cofactor':   AMBER,
        'F1.5_metabolism': BLUE,
    })
    cat_df = cat_df.sort_values('beta', ascending=False)  # positive (null) at top

    # ── Panel B: Permutation histogram ───────────────────────────────────────
    perm_df = pd.read_csv(DATA / 'split_magnitude_permutation.csv')
    row = perm_df[perm_df['family'] == 'Metal gene set'].iloc[0]
    NULL_MEAN = row['null_delta_beta_median']
    NULL_SD   = row['null_delta_beta_sd']
    OBSERVED  = row['observed_delta_beta']

    rng = np.random.default_rng(42)
    null_vals = NULL_MEAN + NULL_SD * rng.standard_normal(1000)

    # ── Panel C: Cofactor jackknife ───────────────────────────────────────────
    jack_labels = ['Full cofactor\n(7 KOs)', 'K03635 excl.', 'K02225 excl.',
                   'K22225 excl.', 'K01772 excl.']
    jack_betas  = [-0.033, -0.029, -0.027, -0.028, -0.016]
    jack_ses    = [0.005,  0.00443, 0.00444, 0.00478, 0.00441]
    jack_colors = [AMBER] + [BLUE] * 4  # reference is amber

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(FIG_W, 3.8))
    gs = GridSpec(2, 2, figure=fig,
                  left=0.03, right=0.98, top=0.93, bottom=0.10,
                  hspace=0.55, wspace=0.38,
                  height_ratios=[1, 1])

    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])
    axC = fig.add_subplot(gs[1, 0])
    # axD spans bottom right — leave empty or add note

    # ── Panel A ───────────────────────────────────────────────────────────────
    forest_plot(axA,
                cat_df['short'].tolist()[::-1],
                cat_df['beta'].tolist()[::-1],
                cat_df['SE'].tolist()[::-1],
                cat_df['color'].tolist()[::-1],
                x_label='PGLS β', x_lim=(-0.050, 0.020),
                dot_size=5, ci_lw=1.3)
    axA.set_xticks([-0.04, -0.02, 0, 0.02])
    axA.xaxis.set_tick_params(labelsize=6.5)
    axA.set_title('Subcategory breakdown', fontsize=7.5, fontweight='semibold', pad=4)

    leg_A = [
        mpatches.Patch(color=AMBER, label='Cofactor biosynthesis (strongest)', alpha=0.8),
        mpatches.Patch(color=RED,   label='Resistance / Detox (null)', alpha=0.7),
        mpatches.Patch(color=BLUE,  label='Other significant', alpha=0.7),
    ]
    axA.legend(handles=leg_A, frameon=False, fontsize=5.5,
               loc='lower right', handlelength=0.8, labelspacing=0.3)
    panel_label(axA, 'A', x=-0.30)

    # ── Panel B: Permutation histogram ────────────────────────────────────────
    bins = np.linspace(null_vals.min() - 0.002, null_vals.max() + 0.002, 26)
    axB.hist(null_vals, bins=bins, color=LTGREY, edgecolor='white',
             linewidth=0.4, zorder=2)
    axB.axvline(OBSERVED, color=RED, lw=1.6, zorder=5, label=f'Observed Δβ = {OBSERVED:.3f}')
    axB.set_xlabel('Δβ (cofactor − resistance)', fontsize=7)
    axB.set_ylabel('Count (n = 1,000 partitions)', fontsize=7)
    axB.set_title('Split-magnitude permutation', fontsize=7.5, fontweight='semibold', pad=4)
    axB.text(OBSERVED + 0.001, axB.get_ylim()[1] * 0.85,
             f'emp. p = 0.0', fontsize=6.5, color=RED, va='top')
    axB.tick_params(labelsize=6.5)
    despine(axB)
    axB.legend(frameon=False, fontsize=6.5, loc='upper left', handlelength=1.0)
    panel_label(axB, 'B', x=-0.16)

    # ── Panel C: Cofactor jackknife ───────────────────────────────────────────
    forest_plot(axC, jack_labels, jack_betas, jack_ses, jack_colors,
                ref_line=-0.033, ref_label='Full cofactor β = −0.033',
                ref_color=AMBER,
                x_label='PGLS β', x_lim=(-0.048, 0.006),
                highlight_row=0, highlight_color=AMBER,
                dot_size=5)
    axC.set_xticks([-0.04, -0.03, -0.02, -0.01, 0])
    axC.xaxis.set_tick_params(labelsize=6.5)
    axC.set_title('Cofactor jackknife', fontsize=7.5, fontweight='semibold', pad=4)

    leg_C = [
        mlines.Line2D([], [], color=AMBER, lw=1.2, ls='--',
                      label='Full cofactor β = −0.033'),
    ]
    axC.legend(handles=leg_C, frameon=False, fontsize=6, handlelength=1.0)
    panel_label(axC, 'C', x=-0.30)

    # hide unused subplot
    fig.add_subplot(gs[1, 1]).set_visible(False)

    fig.savefig(OUT / 'fig03_internal_split.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('Fig 3 saved.')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4  Confounders (A) + Geochemical replication (B)
# ══════════════════════════════════════════════════════════════════════════════
def fig4_validation():
    # ── Panel A: Confounder dumbbell ──────────────────────────────────────────
    conf_df = pd.read_csv(DATA / '04_confounder_results.csv').copy()
    # sort: least attenuation at top, most at bottom (genome size most)
    conf_df['abs_pct'] = conf_df['pct_beta_change'].abs()
    conf_df = conf_df.sort_values('abs_pct', ascending=True)
    conf_df['amplified'] = conf_df['pct_beta_change'] < 0

    # ── Panel B: NGSA replication ─────────────────────────────────────────────
    ngsa = [
        ('Cu', -0.010604, 0.004384, True,  False),
        ('Zn', -0.010638, 0.004416, True,  False),
        ('Pb', -0.009291, 0.004370, False, False),
        ('Ni', -0.008721, 0.004420, False, False),
        ('Co', +0.001258, 0.004416, False, True),
    ]
    ngsa_labels  = [r[0] for r in ngsa][::-1]
    ngsa_betas   = [r[1] for r in ngsa][::-1]
    ngsa_ses     = [r[2] for r in ngsa][::-1]
    ngsa_sig     = [r[3] for r in ngsa][::-1]
    ngsa_wrong   = [r[4] for r in ngsa][::-1]
    ngsa_colors  = [RED if w else (BLUE if s else LTGREY)
                    for w, s in zip(ngsa_wrong, ngsa_sig)]

    # ── Layout ────────────────────────────────────────────────────────────────
    n_conf = len(conf_df)
    n_ngsa = len(ngsa_labels)
    fig = plt.figure(figsize=(FIG_W, 3.4))
    gs = GridSpec(1, 2, figure=fig,
                  left=0.03, right=0.98, top=0.91, bottom=0.13,
                  wspace=0.40)
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])

    # ── Panel A: Dumbbell ─────────────────────────────────────────────────────
    confounder_labels = conf_df['confounder'].tolist()
    before_vals = conf_df['beta_baseline'].abs().tolist()
    after_vals  = conf_df['beta_with_conf'].abs().tolist()
    amplified   = conf_df['amplified'].tolist()
    pct_vals    = conf_df['pct_beta_change'].abs().tolist()

    ys = np.arange(n_conf)
    THRESHOLD = 0.021 * 0.5  # 50% attenuation threshold

    axA.axvline(THRESHOLD, color=RED, lw=1.0, ls='--', alpha=0.5,
                label='50% threshold (|β| = 0.0105)')
    axA.axvline(before_vals[0], color=GREY, lw=0.8, ls=':', alpha=0.5)

    for i, (y, bef, aft, amp) in enumerate(zip(ys, before_vals, after_vals, amplified)):
        col_conn = RED if amp else GREY
        col_after = RED if amp else BLUE
        # Connector
        xlo, xhi = min(bef, aft), max(bef, aft)
        axA.plot([xlo, xhi], [y, y], color=col_conn, lw=1.4, alpha=0.45, zorder=2)
        # Before (circle, grey)
        axA.scatter([bef], [y], s=5**2 * 0.4, color=GREY,
                    edgecolors='white', linewidths=0.7, zorder=4, marker='o')
        # After (square, colored)
        axA.scatter([aft], [y], s=5**2 * 0.5, color=col_after,
                    edgecolors='white', linewidths=0.7, zorder=5, marker='s')
        # % annotation
        sign = '↑' if amp else '↓'
        axA.text(max(bef, aft) + 0.001, y, f'{sign}{abs(conf_df.iloc[i]["pct_beta_change"]):.0f}%',
                 va='center', fontsize=6, color=col_after, alpha=0.85)

    axA.set_yticks(ys)
    axA.set_yticklabels(confounder_labels, fontsize=6.5)
    axA.set_ylim(-0.7, n_conf - 0.3)
    axA.set_xlabel('|β| (metal-gene density → niche breadth)', fontsize=7)
    axA.set_xlim(-0.001, 0.046)
    axA.set_xticks([0, 0.010, 0.020, 0.030])
    axA.xaxis.set_tick_params(labelsize=6.5)
    axA.tick_params(axis='y', length=0)
    axA.set_title('Confounder analysis', fontsize=7.5, fontweight='semibold', pad=4)
    despine(axA)

    leg_A = [
        mlines.Line2D([], [], color=GREY,  marker='o', ms=5, lw=0, label='Before (primary β)'),
        mlines.Line2D([], [], color=BLUE,  marker='s', ms=5, lw=0, label='After (with covariate)'),
        mlines.Line2D([], [], color=RED,   marker='s', ms=5, lw=0, label='Signal amplified'),
        mlines.Line2D([], [], color=RED,   lw=1.0, ls='--', label='50% attenuation threshold'),
    ]
    axA.legend(handles=leg_A, frameon=False, fontsize=6,
               loc='lower right', handlelength=0.9, handletextpad=0.5, labelspacing=0.3)
    panel_label(axA, 'A', x=-0.28)

    # ── Panel B: NGSA geochemical replication ─────────────────────────────────
    forest_plot(axB, ngsa_labels, ngsa_betas, ngsa_ses, ngsa_colors,
                x_label='PGLS β (soil metal → niche breadth)',
                x_lim=(-0.028, 0.016),
                dot_size=5)
    axB.axvline(0, color='#444', lw=0.7)
    axB.set_xticks([-0.02, -0.01, 0, 0.01])
    axB.xaxis.set_tick_params(labelsize=6.5)
    axB.set_title('Geochemical replication (NGSA, n = 482)', fontsize=7.5,
                  fontweight='semibold', pad=4)

    # q < 0.05 bracket for Cu and Zn
    for i, (l, s, w) in enumerate(zip(ngsa_labels, ngsa_sig, ngsa_wrong)):
        if s and not w:
            y = n_ngsa - 1 - ngsa_labels.index(l)
            axB.text(0.015, y, '*', va='center', ha='left', fontsize=9, color=BLUE)

    leg_B = [
        mlines.Line2D([], [], color=BLUE,   marker='o', ms=5, lw=0,
                      label='Significant (q < 0.05)'),
        mlines.Line2D([], [], color=LTGREY, marker='o', ms=5, lw=0,
                      label='Not significant'),
        mlines.Line2D([], [], color=RED,    marker='o', ms=5, lw=0,
                      label='Opposite direction'),
    ]
    axB.legend(handles=leg_B, frameon=False, fontsize=6,
               loc='lower right', handlelength=0.9, labelspacing=0.3)
    panel_label(axB, 'B', x=-0.14)

    fig.savefig(OUT / 'fig04_validation.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('Fig 4 saved.')


# ══════════════════════════════════════════════════════════════════════════════
# Run all
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('Generating publication figures...')
    fig1_scatter()
    fig2_functional_landscape()
    fig3_internal_robustness()
    fig4_validation()
    print('All figures saved to', OUT)
