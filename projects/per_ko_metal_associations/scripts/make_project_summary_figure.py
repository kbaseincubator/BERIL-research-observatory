"""Project summary figure for per_ko_metal_associations.

Five-panel multi-figure:
  Row 0: Hypothesis scorecard (H1–H6)
  Row 1: (A) Sig pairs per metal  (B) Beta stability  (C) Cross-dataset
  Row 2: (D) Top Hg adjusted hits  (E) Cross-metal KO dot chart
"""

from __future__ import annotations

import glob
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
FIG_DIR  = PROJECT_DIR / 'figures'
FIG_DIR.mkdir(exist_ok=True)

EGGNOG_WORK = PROJECT_DIR.parent / 'metagenomic_environment_prediction' / 'data' / 'all_env_ko_annotations_work'

# ── Color system (palette.md reference) ──────────────────────────────────
SURFACE     = '#fcfcfb'
GRID        = '#e1e0d9'
INK         = '#0b0b0b'
INK_SEC     = '#52514e'
INK_MUTED   = '#898781'
BASELINE    = '#c3c2b7'
STATUS_GOOD = '#0ca30c'
STATUS_CRIT = '#d03b3b'
# Categorical slots 1-6 for metals (palette.md)
# Aqua (#1baf7a) and yellow (#eda100) are sub-3:1 → direct labels required
METAL_COLS   = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']
METAL_COLORS = {
    'PF1_As': '#2a78d6',  # slot 1 blue
    'PF1_Cd': '#1baf7a',  # slot 2 aqua   — direct-label required
    'PF1_Cr': '#eda100',  # slot 3 yellow  — direct-label required
    'PF1_Cu': '#008300',  # slot 4 green
    'PF1_Hg': '#4a3aa7',  # slot 5 violet
    'PF1_Pb': '#e34948',  # slot 6 red
}
METAL_LABELS = {
    'PF1_As': 'As', 'PF1_Cd': 'Cd', 'PF1_Cr': 'Cr',
    'PF1_Cu': 'Cu', 'PF1_Hg': 'Hg', 'PF1_Pb': 'Pb',
}
# Model comparison: slots 1 (blue) vs 8 (orange)
COLOR_UNADJ = '#2a78d6'
COLOR_ADJ   = '#eb6834'

# ── Load data ─────────────────────────────────────────────────────────────
print('Loading data …')
mg_unadj = pd.read_csv(DATA_DIR / 'mgnify_all_ko_associations.csv')
mg_adj   = pd.read_csv(DATA_DIR / 'mgnify_adj_ko_associations.csv')
sp_unadj = pd.read_csv(DATA_DIR / 'spire_all_ko_associations.csv')
sp_adj   = pd.read_csv(DATA_DIR / 'spire_adj_ko_associations.csv')

# ── KO name lookup ────────────────────────────────────────────────────────
def build_ko_lookup(ko_ids: list[str]) -> dict[str, str]:
    target = set(ko_ids)
    records: dict[str, str] = {}
    parquets = sorted(glob.glob(str(EGGNOG_WORK / '*.parquet')))
    random.shuffle(parquets)
    for fp in parquets:
        if len(records) >= len(target):
            break
        try:
            df = pd.read_parquet(fp, columns=['ko_id', 'Preferred_name'])
            df = df[df['ko_id'].isin(target - set(records))].drop_duplicates('ko_id')
            for _, row in df.iterrows():
                if row['Preferred_name']:
                    records[row['ko_id']] = row['Preferred_name']
        except Exception:
            continue
    return records

# ── Hypothesis data ───────────────────────────────────────────────────────
HYPOTHESES = [
    {'id': 'H1', 'result': 'SUPPORTED',
     'value': '219 sig pairs', 'detail': 'MGnify FDR q<0.05\n(threshold ≥20)'},
    {'id': 'H2', 'result': 'NOT SUPPORTED',
     'value': 'ρ = 0.059', 'detail': 'MGnify × SPIRE β\n(threshold ρ>0.2)'},
    {'id': 'H3', 'result': 'NOT SUPPORTED',
     'value': 'OR = 1.52', 'detail': 'Curated KO enrichment\n(Fisher p=0.39)'},
    {'id': 'H4', 'result': 'SUPPORTED',
     'value': '138 / 219', 'detail': 'Survive lat. adjustment\n(threshold ≥10)'},
    {'id': 'H5', 'result': 'SUPPORTED',
     'value': 'ρ = 0.923', 'detail': 'β stability adj vs unadj\n(threshold ρ>0.5)'},
    {'id': 'H6', 'result': 'NOT SUPPORTED',
     'value': 'adj ρ = 0.049', 'detail': 'Adj. cross-dataset β\n(< unadj ρ=0.059)'},
]

# ── Precompute values ─────────────────────────────────────────────────────
sig_unadj_n = {m: (mg_unadj[mg_unadj['metal']==m]['q_value'] < 0.05).sum()
               for m in METAL_COLS}
sig_adj_n   = {m: (mg_adj[mg_adj['metal']==m]['q_value'] < 0.05).sum()
               for m in METAL_COLS}

# Beta stability (H5): H1-significant pairs
merged_betas = mg_unadj.merge(
    mg_adj[['ko_id','metal','beta','q_value']].rename(
        columns={'beta':'beta_adj','q_value':'q_adj'}),
    on=['ko_id','metal']
).rename(columns={'beta':'beta_unadj','q_value':'q_unadj'})
sig_pairs = merged_betas[merged_betas['q_unadj'] < 0.05].dropna(
    subset=['beta_unadj','beta_adj'])

# Cross-dataset beta (H2): shared KO-metal pairs with non-null betas in both
mg_b = mg_unadj[['ko_id','metal','beta']].rename(columns={'beta':'beta_mg'})
sp_b = sp_unadj[['ko_id','metal','beta']].rename(columns={'beta':'beta_sp'})
cross = mg_b.merge(sp_b, on=['ko_id','metal']).dropna(subset=['beta_mg','beta_sp'])
rho_cross, _ = spearmanr(cross['beta_mg'], cross['beta_sp'])

# Top Hg adjusted hits
hg_adj = mg_adj[(mg_adj['metal']=='PF1_Hg') & (mg_adj['q_value']<0.05)].copy()
hg_top = hg_adj.nsmallest(14, 'p_value').copy()
print(f'  Building KO name lookup for {len(hg_top)} top Hg KOs …')
ko_names = build_ko_lookup(hg_top['ko_id'].tolist())
# Actual KEGG KOs for mercury resistance operon
MER_KOS = {'K00786','K07788','K07789','K06045','K07093','K08677','K08716'}
# Potassium-transporting ATPase operon — top adjusted Hg hits (unexpected)
KDP_KOS = {'K01546','K01547','K01548','K01555','K16080'}
hg_top['name'] = hg_top['ko_id'].map(ko_names).fillna(hg_top['ko_id'])
hg_top['is_mer'] = hg_top['ko_id'].isin(MER_KOS)
hg_top['is_kdp'] = hg_top['ko_id'].isin(KDP_KOS)
hg_top = hg_top.sort_values('beta')

# Cross-metal KO dot chart: compute actual betas
CROSS_KOS = ['K02402','K02403','K01252','K13634','K05596','K03600',
             'K01546','K05590','K02822']
METALS_CROSS = ['PF1_As','PF1_Cd','PF1_Cr','PF1_Hg','PF1_Pb']
cross_data = mg_unadj[mg_unadj['ko_id'].isin(CROSS_KOS)][
    ['ko_id','metal','beta','q_value']].copy()
# Add adjusted Hg betas for K01546
for m in METALS_CROSS:
    rows_adj = mg_adj[(mg_adj['ko_id'].isin(CROSS_KOS)) &
                      (mg_adj['metal']==m)][['ko_id','metal','beta','q_value']].copy()
    rows_adj['model'] = 'adj'
    cross_data_adj = rows_adj
cross_ko_names = build_ko_lookup(CROSS_KOS)
print('Data loading complete.')

# ═══════════════════════════════════════════════════════════════════════════
# Figure layout
# ═══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(18, 13), facecolor=SURFACE)
gs = gridspec.GridSpec(
    3, 3,
    figure=fig,
    height_ratios=[1.5, 4.5, 4.5],
    hspace=0.52, wspace=0.38,
    left=0.06, right=0.97, top=0.94, bottom=0.06,
)

# ── Shared axis style helper ───────────────────────────────────────────────
def style_ax(ax):
    ax.set_facecolor(SURFACE)
    ax.spines[['top','right']].set_visible(False)
    ax.spines['left'].set_color(BASELINE)
    ax.spines['bottom'].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, labelsize=8)
    ax.xaxis.label.set_color(INK_SEC)
    ax.yaxis.label.set_color(INK_SEC)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 0: Hypothesis scorecard (full-width axes, invisible, used for title only)
# ═══════════════════════════════════════════════════════════════════════════
ax_hdr = fig.add_subplot(gs[0, :])
ax_hdr.set_axis_off()
ax_hdr.set_xlim(0, 6)
ax_hdr.set_ylim(0, 1)
ax_hdr.set_facecolor(SURFACE)

fig.text(0.5, 0.975, 'Per-KO Metal Associations — Project Overview',
         ha='center', va='top', fontsize=15, fontweight='bold', color=INK,
         transform=fig.transFigure)
fig.text(
    0.5, 0.956,
    '8,585 MGnify MAGs × 6,451 KOs × 6 metals  ·  logistic regression  ·  '
    'FDR per metal  ·  latitude-adjusted replication',
    ha='center', va='top', fontsize=9, color=INK_SEC,
    transform=fig.transFigure,
)

# Draw 6 hypothesis tiles inside ax_hdr data coordinates
card_w, card_h = 0.82, 0.72
gap = 1.0
for i, h in enumerate(HYPOTHESES):
    cx = i * gap + 0.09
    cy = 0.12
    supported = h['result'] == 'SUPPORTED'
    fill   = '#e6f7e6' if supported else '#fce8e8'
    border = STATUS_GOOD if supported else STATUS_CRIT
    symbol = '✓' if supported else '✗'

    rect = FancyBboxPatch((cx, cy), card_w, card_h,
                          boxstyle='round,pad=0.04',
                          facecolor=fill, edgecolor=border, linewidth=1.5,
                          transform=ax_hdr.transData, zorder=2)
    ax_hdr.add_patch(rect)

    # H-id (top-left)
    ax_hdr.text(cx + 0.06, cy + card_h - 0.07, h['id'],
                fontsize=11, fontweight='bold', color=INK,
                va='top', ha='left', transform=ax_hdr.transData)
    # Symbol (top-right)
    ax_hdr.text(cx + card_w - 0.06, cy + card_h - 0.05, symbol,
                fontsize=14, color=border,
                va='top', ha='right', transform=ax_hdr.transData)
    # Value (center)
    ax_hdr.text(cx + card_w/2, cy + card_h/2 + 0.03, h['value'],
                fontsize=9.5, fontweight='semibold', color=INK,
                ha='center', va='center', transform=ax_hdr.transData)
    # Detail (bottom)
    ax_hdr.text(cx + card_w/2, cy + 0.07, h['detail'],
                fontsize=7.5, color=INK_SEC,
                ha='center', va='bottom', transform=ax_hdr.transData,
                linespacing=1.3)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 1A: Significant pairs per metal — grouped bar, symlog scale
# ═══════════════════════════════════════════════════════════════════════════
ax_sig = fig.add_subplot(gs[1, 0])
style_ax(ax_sig)

metals_x = [METAL_LABELS[m] for m in METAL_COLS]
y_u = [sig_unadj_n[m] for m in METAL_COLS]
y_a = [sig_adj_n[m]   for m in METAL_COLS]
x   = np.arange(len(METAL_COLS))
w   = 0.35

bars_u = ax_sig.bar(x - w/2, y_u, width=w,
                    color=COLOR_UNADJ, alpha=0.55,
                    edgecolor=COLOR_UNADJ, linewidth=0.8, label='Unadjusted')
bars_a = ax_sig.bar(x + w/2, y_a, width=w,
                    color=COLOR_ADJ, alpha=0.85,
                    edgecolor='none', label='Lat. adjusted')

ax_sig.set_yscale('symlog', linthresh=10)
ax_sig.set_xticks(x)
ax_sig.set_xticklabels(metals_x, fontsize=9)
ax_sig.set_ylabel('FDR-significant pairs (q<0.05)', fontsize=8.5)
ax_sig.set_title('(A)  Significant KO-metal pairs per metal',
                 fontsize=9.5, fontweight='bold', color=INK, pad=6, loc='left')
ax_sig.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax_sig.set_axisbelow(True)
ax_sig.legend(fontsize=8, frameon=False, labelcolor=INK_SEC, loc='upper left')

# Direct labels — all bars (required by relief rule for aqua/yellow)
for xi, (yu, ya) in enumerate(zip(y_u, y_a)):
    if yu > 0:
        ax_sig.text(xi - w/2, yu * 1.3 + 0.5, str(yu),
                    ha='center', va='bottom', fontsize=7, color=INK)
    if ya > 0:
        ax_sig.text(xi + w/2, ya * 1.3 + 0.5, str(ya),
                    ha='center', va='bottom', fontsize=7, color=INK)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 1B: Beta stability scatter (H5) — H1-significant pairs
# ═══════════════════════════════════════════════════════════════════════════
ax_beta = fig.add_subplot(gs[1, 1])
style_ax(ax_beta)

rho_h5, _ = spearmanr(sig_pairs['beta_unadj'], sig_pairs['beta_adj'])

for m in METAL_COLS:
    sub = sig_pairs[sig_pairs['metal'] == m]
    if sub.empty:
        continue
    survived = sub['q_adj'] < 0.05
    # Surface ring: edgecolors=SURFACE, lw=1.5
    ax_beta.scatter(sub.loc[survived, 'beta_unadj'], sub.loc[survived, 'beta_adj'],
                    c=METAL_COLORS[m], s=28, alpha=0.85,
                    edgecolors=SURFACE, linewidths=1.0,
                    label=METAL_LABELS[m])
    ax_beta.scatter(sub.loc[~survived, 'beta_unadj'], sub.loc[~survived, 'beta_adj'],
                    facecolors='none', edgecolors=METAL_COLORS[m],
                    s=18, alpha=0.55, linewidths=0.7)

lim = max(
    abs(sig_pairs['beta_unadj'].quantile(0.97)),
    abs(sig_pairs['beta_adj'].quantile(0.97)),
) * 1.15
ax_beta.set_xlim(-lim, lim)
ax_beta.set_ylim(-lim, lim)
ax_beta.plot([-lim, lim], [-lim, lim], color=BASELINE, lw=0.9, ls='--')
ax_beta.axhline(0, color=GRID, lw=0.5)
ax_beta.axvline(0, color=GRID, lw=0.5)

ax_beta.text(0.05, 0.97, f'ρ = {rho_h5:.3f}', transform=ax_beta.transAxes,
             fontsize=9.5, va='top', color=INK, fontweight='bold')
ax_beta.text(0.05, 0.89, f'n = {len(sig_pairs)}  (H1-sig pairs)',
             transform=ax_beta.transAxes, fontsize=7.5, va='top', color=INK_SEC)

n_survive = (sig_pairs['q_adj'] < 0.05).sum()
ax_beta.text(0.05, 0.82, f'● {n_survive} still q<0.05',
             transform=ax_beta.transAxes, fontsize=7.5, va='top', color=INK_SEC)
ax_beta.text(0.05, 0.76, f'○ {len(sig_pairs)-n_survive} lost sig',
             transform=ax_beta.transAxes, fontsize=7.5, va='top', color=INK_SEC)

ax_beta.set_xlabel('β unadjusted', fontsize=8.5)
ax_beta.set_ylabel('β latitude-adjusted', fontsize=8.5)
ax_beta.set_title('(B)  H5: Beta stability\n(H1-significant KO-metal pairs)',
                  fontsize=9.5, fontweight='bold', color=INK, pad=6, loc='left')
ax_beta.legend(fontsize=7, frameon=False, loc='lower right',
               labelcolor=INK_SEC, markerscale=1.2,
               handletextpad=0.3, borderpad=0.3)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 1C: Cross-dataset beta scatter (H2)
# ═══════════════════════════════════════════════════════════════════════════
ax_cross = fig.add_subplot(gs[1, 2])
style_ax(ax_cross)

# 2D density hexbin (too many points for a clear scatter)
# Use per-metal scatter with small alpha; enough to see the cloud
for m in METAL_COLS:
    sub = cross[cross['metal'] == m]
    if len(sub) < 2:
        continue
    ax_cross.scatter(sub['beta_mg'], sub['beta_sp'],
                     c=METAL_COLORS[m], s=6, alpha=0.30,
                     edgecolors='none', label=METAL_LABELS[m])

lim2 = max(
    cross['beta_mg'].abs().quantile(0.97),
    cross['beta_sp'].abs().quantile(0.97),
) * 1.2
ax_cross.set_xlim(-lim2, lim2)
ax_cross.set_ylim(-lim2, lim2)
ax_cross.plot([-lim2, lim2], [-lim2, lim2], color=BASELINE, lw=0.9, ls='--')
ax_cross.axhline(0, color=GRID, lw=0.5)
ax_cross.axvline(0, color=GRID, lw=0.5)

ax_cross.text(0.05, 0.97, f'ρ = {rho_cross:.3f}', transform=ax_cross.transAxes,
              fontsize=9.5, va='top', color=INK, fontweight='bold')
ax_cross.text(0.05, 0.89, f'n = {len(cross):,}  (shared KO-metal pairs)',
              transform=ax_cross.transAxes, fontsize=7.5, va='top', color=INK_SEC)

ax_cross.set_xlabel('β MGnify', fontsize=8.5)
ax_cross.set_ylabel('β SPIRE', fontsize=8.5)
ax_cross.set_title('(C)  H2: Cross-dataset β agreement',
                   fontsize=9.5, fontweight='bold', color=INK, pad=6, loc='left')
ax_cross.legend(fontsize=7, frameon=False, loc='lower right',
                labelcolor=INK_SEC, markerscale=2.5,
                handletextpad=0.3, borderpad=0.3)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 2D: Top Hg adjusted hits (mer operon emphasis)
# ═══════════════════════════════════════════════════════════════════════════
ax_hg = fig.add_subplot(gs[2, 0:2])
style_ax(ax_hg)

COLOR_KDP = '#1baf7a'   # slot 2 aqua — kdp operon (top unexpected hits)
hg_colors = []
for _, row in hg_top.iterrows():
    if row['is_kdp'] and row['beta'] > 0:
        hg_colors.append(COLOR_KDP)   # aqua for kdp operon
    elif row['is_mer'] and row['beta'] > 0:
        hg_colors.append(METAL_COLORS['PF1_Hg'])  # violet for mer
    elif row['beta'] > 0:
        hg_colors.append('#aaa8d8')  # de-emphasis for other Hg+
    else:
        hg_colors.append(STATUS_CRIT)  # red for Hg-depleted

y_pos = list(range(len(hg_top)))
ax_hg.barh(y_pos, hg_top['beta'].values,
           color=hg_colors, height=0.62,
           edgecolor='none')

ax_hg.set_yticks(y_pos)
ax_hg.set_yticklabels(hg_top['name'].values, fontsize=8.5)
ax_hg.axvline(0, color=BASELINE, lw=1.0)
ax_hg.set_xlabel('β (log-odds, latitude-adjusted)', fontsize=8.5)
ax_hg.set_title(
    '(D)  Top Mercury associations — latitude-adjusted model\n'
    '(aqua = kdp operon  ·  violet = mer operon  ·  red = Hg-depleted  ·  gray = other)',
    fontsize=9.5, fontweight='bold', color=INK, pad=6, loc='left',
)
ax_hg.xaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax_hg.set_axisbelow(True)

# Legend — placed upper left to avoid overlapping bars on the right
kdp_p   = mpatches.Patch(color=COLOR_KDP,               label='kdp operon (K+ ATPase — top hit)')
mer_p   = mpatches.Patch(color=METAL_COLORS['PF1_Hg'],  label='mer operon (Hg resistance)')
other_p = mpatches.Patch(color='#aaa8d8',               label='Other Hg-enriched')
neg_p   = mpatches.Patch(color=STATUS_CRIT,             label='Hg-depleted')
ax_hg.legend(handles=[kdp_p, mer_p, other_p, neg_p], fontsize=8, frameon=False,
             loc='upper left', labelcolor=INK_SEC)

# Annotate beta values selectively (top 3 and bottom 1)
for idx, (yi, (_, row)) in enumerate(zip(y_pos, hg_top.iterrows())):
    if idx >= len(y_pos) - 3 or idx == 0:
        ax_hg.text(row['beta'] + (0.3 if row['beta'] > 0 else -0.3),
                   yi, f'{row["beta"]:.1f}',
                   va='center', ha='left' if row['beta'] > 0 else 'right',
                   fontsize=7.5, color=INK)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 2E: Cross-metal KO dot chart (actual betas)
# ═══════════════════════════════════════════════════════════════════════════
ax_dot = fig.add_subplot(gs[2, 2])
style_ax(ax_dot)

# Build pivot of betas for selected cross-metal KOs (unadjusted, per metal)
pivot = cross_data[cross_data['metal'].isin(METALS_CROSS)].copy()
pivot['name'] = pivot['ko_id'].map(cross_ko_names).fillna(pivot['ko_id'])
pivot['label'] = pivot.apply(
    lambda r: f"{r['name']} ({r['ko_id']})" if r['name'] != r['ko_id']
              else r['ko_id'],
    axis=1)

# Order KOs by first METAL_CROSS appearance and significance
ko_order = (pivot.groupby('ko_id')['metal'].nunique()
            .reindex(CROSS_KOS, fill_value=0)
            .sort_values(ascending=False).index.tolist())

# Get label for each ko_id
ko_label = {ko: pivot[pivot['ko_id']==ko]['label'].iloc[0]
            if ko in pivot['ko_id'].values else ko
            for ko in ko_order}

cmap = plt.cm.RdBu_r
max_abs = pivot['beta'].abs().quantile(0.97)
norm = plt.Normalize(-max_abs, max_abs)

for yi, ko in enumerate(reversed(ko_order)):
    sub = pivot[pivot['ko_id'] == ko]
    for _, row in sub.iterrows():
        if row['metal'] not in METALS_CROSS:
            continue
        xi = METALS_CROSS.index(row['metal'])
        color = cmap(norm(row['beta']))
        sig = row['q_value'] < 0.05
        mk = '*' if row['q_value'] < 0.001 else ('o' if sig else 's')
        sz = 160 if row['q_value'] < 0.001 else (90 if sig else 35)
        ax_dot.scatter(xi, yi, c=[color], s=sz, marker=mk,
                       edgecolors=SURFACE, linewidths=1.0, zorder=3)

ax_dot.set_xticks(range(len(METALS_CROSS)))
ax_dot.set_xticklabels([METAL_LABELS[m] for m in METALS_CROSS], fontsize=9.5)
ax_dot.set_yticks(range(len(ko_order)))
ax_dot.set_yticklabels(
    [ko_label[ko] for ko in reversed(ko_order)], fontsize=8)
ax_dot.set_xlim(-0.5, len(METALS_CROSS) - 0.5)
ax_dot.set_ylim(-0.5, len(ko_order) - 0.5)
ax_dot.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
ax_dot.yaxis.grid(True, color=GRID, lw=0.5, zorder=0)
ax_dot.set_axisbelow(True)
ax_dot.set_title('(E)  Cross-metal KO patterns\n(blue=depleted  ·  red=enriched  ·  ★ q<0.001)',
                 fontsize=9.5, fontweight='bold', color=INK, pad=6, loc='left')

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cb = fig.colorbar(sm, ax=ax_dot, shrink=0.55, pad=0.03, aspect=15)
cb.set_label('β (log-odds)', fontsize=7.5, color=INK_SEC)
cb.ax.tick_params(labelsize=7, colors=INK_MUTED)

# ── Save ──────────────────────────────────────────────────────────────────
out = FIG_DIR / 'project_summary.png'
fig.savefig(out, dpi=180, bbox_inches='tight', facecolor=SURFACE)
plt.close(fig)
print(f'Saved: {out}')
