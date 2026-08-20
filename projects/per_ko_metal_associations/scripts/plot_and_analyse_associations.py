"""Plot top KO-metal associations and print brief functional analysis.

Reads mgnify_all_ko_associations.csv (unadjusted, FDR-corrected).
Builds a KO→description lookup from eggnog parquets.
Saves figures to figures/.
"""

from __future__ import annotations

import glob
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT   = PROJECT_DIR.parent
DATA_DIR    = PROJECT_DIR / 'data'
FIG_DIR     = PROJECT_DIR / 'figures'
FIG_DIR.mkdir(exist_ok=True)

EGGNOG_WORK = REPO_ROOT / 'metagenomic_environment_prediction' / 'data' / 'all_env_ko_annotations_work'
Q_THRESH    = 0.05
TOP_N       = 12   # top hits per metal in barplot

METAL_LABELS = {
    'PF1_As': 'Arsenic (As)',
    'PF1_Cd': 'Cadmium (Cd)',
    'PF1_Cr': 'Chromium (Cr)',
    'PF1_Cu': 'Copper (Cu)',
    'PF1_Hg': 'Mercury (Hg)',
    'PF1_Pb': 'Lead (Pb)',
}
METAL_COLORS = {
    'PF1_As': '#d95f02',
    'PF1_Cd': '#7570b3',
    'PF1_Cr': '#1b9e77',
    'PF1_Cu': '#e7298a',
    'PF1_Hg': '#66a61e',
    'PF1_Pb': '#e6ab02',
}


# ── 1. Build KO description lookup ──────────────────────────────────────────

def build_ko_descriptions(assoc_df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame [ko_id, preferred_name, description] from eggnog parquets."""
    target_kos = set(assoc_df['ko_id'].unique())
    records: dict[str, dict] = {}

    parquet_files = sorted(glob.glob(str(EGGNOG_WORK / '*.parquet')))
    random.shuffle(parquet_files)  # avoid reading the same order every time

    for fpath in parquet_files:
        if len(records) >= len(target_kos):
            break
        try:
            df = pd.read_parquet(fpath, columns=['ko_id', 'Preferred_name', 'Description'])
            df = df[df['ko_id'].isin(target_kos - set(records.keys()))]
            for _, row in df.drop_duplicates('ko_id').iterrows():
                records[row['ko_id']] = {
                    'preferred_name': row['Preferred_name'] or '',
                    'description':    (row['Description'] or '')[:120],
                }
        except Exception:
            continue

    lookup = pd.DataFrame.from_dict(records, orient='index').reset_index()
    lookup.columns = ['ko_id', 'preferred_name', 'description']
    return lookup


# ── 2. Volcano plots ─────────────────────────────────────────────────────────

def plot_volcanos(assoc_df: pd.DataFrame, lookup: pd.DataFrame) -> None:
    metals = [m for m in METAL_LABELS if m in assoc_df['metal'].unique()]
    n_metals = len(metals)
    ncols = 3
    nrows = int(np.ceil(n_metals / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 4.5 * nrows))
    axes = axes.flatten()

    for ax, metal in zip(axes, metals):
        sub = assoc_df[assoc_df['metal'] == metal].dropna(subset=['beta', 'p_value'])
        sub = sub.merge(lookup, on='ko_id', how='left')

        sig_mask  = sub['q_value'] < Q_THRESH
        neg_mask  = sig_mask & (sub['beta'] < 0)
        pos_mask  = sig_mask & (sub['beta'] > 0)

        log_p = -np.log10(sub['p_value'].clip(lower=1e-300))

        # Background
        ax.scatter(sub.loc[~sig_mask, 'beta'], log_p[~sig_mask],
                   c='#cccccc', s=6, alpha=0.5, linewidths=0, rasterized=True)
        # Significant negative
        ax.scatter(sub.loc[neg_mask, 'beta'], log_p[neg_mask],
                   c='#3182bd', s=18, alpha=0.8, linewidths=0)
        # Significant positive
        ax.scatter(sub.loc[pos_mask, 'beta'], log_p[pos_mask],
                   c='#e6550d', s=18, alpha=0.8, linewidths=0)

        # Label top 5 by p-value
        top = sub[sig_mask].nsmallest(5, 'p_value')
        for _, row in top.iterrows():
            name = row.get('preferred_name') or row['ko_id']
            lp = -np.log10(max(row['p_value'], 1e-300))
            ax.annotate(name, xy=(row['beta'], lp),
                        xytext=(4, 2), textcoords='offset points',
                        fontsize=6.5, color='#333333',
                        arrowprops=dict(arrowstyle='-', color='#aaaaaa', lw=0.5))

        ax.axhline(-np.log10(Q_THRESH), ls='--', lw=0.8, color='#999999')
        ax.axvline(0, ls='-', lw=0.4, color='#cccccc')
        ax.set_xlabel('Log odds (β)', fontsize=9)
        ax.set_ylabel('−log₁₀(p)', fontsize=9)
        n_sig = sig_mask.sum()
        n_neg = neg_mask.sum()
        n_pos = pos_mask.sum()
        ax.set_title(f'{METAL_LABELS[metal]}\n'
                     f'{n_neg} neg  {n_pos} pos  ({n_sig} FDR q<0.05)',
                     fontsize=9)
        ax.tick_params(labelsize=8)

    for ax in axes[n_metals:]:
        ax.set_visible(False)

    fig.suptitle('Genome-wide KO–metal associations (MGnify, unadjusted)',
                 fontsize=11, y=1.01)
    fig.tight_layout()
    out = FIG_DIR / 'volcano_ko_metal_associations.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {out}')


# ── 3. Top-hits lollipop per metal ───────────────────────────────────────────

def plot_top_hits(assoc_df: pd.DataFrame, lookup: pd.DataFrame) -> None:
    sig = assoc_df[assoc_df['q_value'] < Q_THRESH].copy()
    sig = sig.merge(lookup, on='ko_id', how='left')
    sig['label'] = sig.apply(
        lambda r: f"{r['preferred_name'] or r['ko_id']}  ({r['ko_id']})", axis=1)
    sig['log_or'] = np.log2(sig['odds_ratio'].clip(lower=1e-6, upper=1e6))

    metals = [m for m in METAL_LABELS if m in sig['metal'].unique()]
    if not metals:
        print('No significant associations to plot.')
        return

    n_metals = len(metals)
    fig, axes = plt.subplots(1, n_metals, figsize=(4.5 * n_metals, 8),
                             sharey=False)
    if n_metals == 1:
        axes = [axes]

    for ax, metal in zip(axes, metals):
        sub = sig[sig['metal'] == metal].copy()
        # Top N by |log_or|, sorted for display
        sub = sub.nlargest(TOP_N, 'log_or')
        sub = sub.sort_values('log_or')

        colors = ['#3182bd' if v < 0 else '#e6550d' for v in sub['log_or']]
        y = range(len(sub))
        ax.barh(list(y), sub['log_or'].values, color=colors,
                height=0.6, alpha=0.85)
        ax.set_yticks(list(y))
        ax.set_yticklabels(sub['label'].values, fontsize=7.5)
        ax.axvline(0, color='black', lw=0.8)
        ax.set_xlabel('log₂(odds ratio)', fontsize=9)
        ax.set_title(METAL_LABELS[metal], fontsize=10, color=METAL_COLORS[metal],
                     fontweight='bold')
        ax.tick_params(labelsize=8)

    fig.suptitle(f'Top {TOP_N} positive associations per metal (FDR q<0.05)',
                 fontsize=11, y=1.01)
    fig.tight_layout()
    out = FIG_DIR / 'top_ko_associations_per_metal.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {out}')


# ── 4. Cross-metal overlap dot chart ────────────────────────────────────────

def plot_shared_kos(assoc_df: pd.DataFrame, lookup: pd.DataFrame) -> None:
    """KOs significant in ≥2 metals: show beta per metal as dot chart."""
    sig = assoc_df[assoc_df['q_value'] < Q_THRESH][['ko_id', 'metal', 'beta', 'q_value']]
    ko_metal_counts = sig.groupby('ko_id')['metal'].nunique()
    shared_kos = ko_metal_counts[ko_metal_counts >= 2].index

    if len(shared_kos) == 0:
        print('No KOs significant across ≥2 metals.')
        return

    sub = sig[sig['ko_id'].isin(shared_kos)].merge(lookup, on='ko_id', how='left')
    sub['label'] = sub.apply(
        lambda r: f"{r['preferred_name'] or r['ko_id']} ({r['ko_id']})", axis=1)

    metals = sorted(sub['metal'].unique())
    labels_ordered = (sub.groupby('label')['metal'].nunique()
                        .sort_values(ascending=False).index.tolist())

    fig, ax = plt.subplots(figsize=(8, max(4, 0.55 * len(labels_ordered))))
    cmap = plt.cm.RdBu_r

    max_abs = sub['beta'].abs().max()
    norm = plt.Normalize(-max_abs, max_abs)

    for yi, label in enumerate(labels_ordered):
        row = sub[sub['label'] == label]
        for _, r in row.iterrows():
            xi = metals.index(r['metal'])
            color = cmap(norm(r['beta']))
            sig_marker = '*' if r['q_value'] < 0.001 else ('o' if r['q_value'] < Q_THRESH else 's')
            ax.scatter(xi, yi, c=[color], s=120, marker=sig_marker,
                       edgecolors='black', linewidths=0.4)

    ax.set_xticks(range(len(metals)))
    ax.set_xticklabels([METAL_LABELS.get(m, m) for m in metals], rotation=30,
                       ha='right', fontsize=9)
    ax.set_yticks(range(len(labels_ordered)))
    ax.set_yticklabels(labels_ordered, fontsize=8)
    ax.set_title('KOs significant in ≥2 metals\n(color = β: blue=negative, red=positive)',
                 fontsize=10)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label='β (log odds)', shrink=0.6)
    fig.tight_layout()
    out = FIG_DIR / 'shared_ko_multi_metal.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {out}')


# ── 5. Print functional analysis ─────────────────────────────────────────────

def print_analysis(assoc_df: pd.DataFrame, lookup: pd.DataFrame) -> None:
    sig = assoc_df[assoc_df['q_value'] < Q_THRESH].copy()
    sig = sig.merge(lookup, on='ko_id', how='left')
    sig['label'] = sig.apply(
        lambda r: r['preferred_name'] if pd.notna(r.get('preferred_name')) and r['preferred_name'] else r['ko_id'],
        axis=1)

    print('\n' + '='*70)
    print('BRIEF FUNCTIONAL ANALYSIS — TOP KO-METAL ASSOCIATIONS')
    print('='*70)

    metals = ['PF1_Hg','PF1_Pb','PF1_As','PF1_Cd','PF1_Cr','PF1_Cu']
    for metal in metals:
        sub = sig[sig['metal'] == metal].sort_values('q_value')
        if len(sub) == 0:
            print(f'\n{METAL_LABELS[metal]}: no significant associations')
            continue
        n_neg = (sub['beta'] < 0).sum()
        n_pos = (sub['beta'] > 0).sum()
        print(f'\n{METAL_LABELS[metal]}  ({len(sub)} sig: {n_pos} positive, {n_neg} negative)')
        print('-' * 60)
        for _, r in sub.head(8).iterrows():
            direction = '▲ positive' if r['beta'] > 0 else '▼ negative'
            desc = (r.get('description') or '')[:80]
            print(f"  {r['ko_id']:8s}  {r['label']:15s}  {direction}  "
                  f"OR={r['odds_ratio']:.2e}  q={r['q_value']:.2e}")
            if desc:
                print(f"           {desc}")

    # Cross-metal KOs
    ko_counts = sig.groupby('ko_id')['metal'].nunique()
    shared = ko_counts[ko_counts >= 2].index
    if len(shared):
        print(f'\n--- KOs significant in ≥2 metals ---')
        for ko in shared:
            rows = sig[sig['ko_id'] == ko].sort_values('metal')
            name = rows.iloc[0]['label']
            desc = (rows.iloc[0].get('description') or '')[:70]
            metals_str = ', '.join(
                f"{METAL_LABELS[r['metal']].split(' (')[0]} {'▲' if r['beta'] > 0 else '▼'}"
                for _, r in rows.iterrows()
            )
            print(f"  {ko:8s}  {name:15s}  [{metals_str}]")
            if desc:
                print(f"           {desc}")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Loading associations ...')
    assoc = pd.read_csv(DATA_DIR / 'mgnify_all_ko_associations.csv')
    print(f'  {len(assoc):,} rows, {(assoc.q_value < Q_THRESH).sum()} FDR-significant')

    print('Building KO description lookup from eggnog parquets ...')
    lookup = build_ko_descriptions(assoc)
    print(f'  Descriptions found for {len(lookup):,} / '
          f'{assoc.ko_id.nunique():,} KOs')

    print('Plotting volcanos ...')
    plot_volcanos(assoc, lookup)

    print('Plotting top hits ...')
    plot_top_hits(assoc, lookup)

    print('Plotting shared KOs ...')
    plot_shared_kos(assoc, lookup)

    print_analysis(assoc, lookup)
    print('\nDone.')
