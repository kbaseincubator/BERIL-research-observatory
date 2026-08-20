#!/usr/bin/env python3
"""
Generate forest plot of pathway-specific PGLS β coefficients for the 47-KO
expanded metal-cofactor analysis (§ss:cobalamin).

Five KEGG pathways:
  Cobalamin (M00122/M00924, 18 KOs)
  Fe–S cluster assembly (M00175/M00176)
  Heme (M00121/M00926)
  Molybdopterin (M00880)
  Siroheme (M00846)

Each pathway PGLS: mean_levins_B_std ~ pathway_z + genome_mb_z
Output:
  data/pathway_pgls_results.csv
  figures/fig_pathway_forest_plot.pdf
"""
import os, sys
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
FIG  = ROOT / 'figures'
TREE = DATA / 'gtdb_bac_genus_pruned.tree'

sys.path.insert(0, str(ROOT / 'scripts'))
from pgls_utils import run_pgls

PATHWAYS = [
    ('Cobalamin',           'cobalamin_z'),
    ('Fe–S cluster',   'fes_assembly_z'),
    ('Heme',                'heme_z'),
    ('Molybdopterin',       'molybdopterin_z'),
    ('Siroheme',            'siroheme_z'),
]

ALPHA = 0.05


def run_pathway_pgls() -> pd.DataFrame:
    pgls_in = pd.read_csv(DATA / '01_pgls_input_bacteria.csv',
                          usecols=['genus_lower', 'mean_levins_B_std', 'genome_mb_z'])
    expanded = pd.read_csv(DATA / 'expanded_kegg_metal_cofactor_densities.csv',
                           usecols=['genus_lower', 'mean_genome_mb',
                                    'cobalamin_z', 'fes_assembly_z',
                                    'heme_z', 'molybdopterin_z', 'siroheme_z'])
    df = pgls_in.merge(expanded, on='genus_lower', how='inner')
    df = df.dropna(subset=['mean_levins_B_std', 'genome_mb_z'])

    rows = []
    for label, col in PATHWAYS:
        subset = df.dropna(subset=[col])
        res = run_pgls(
            subset,
            tree_path=str(TREE),
            response='mean_levins_B_std',
            predictors=[col, 'genome_mb_z'],
            taxon_col='genus_lower',
        )
        beta = res['betas'][col]
        se   = res['SEs'][col]
        p    = res['p_values'][col]
        n    = res['n']
        lam  = res.get('lambda_est', float('nan'))
        rows.append({'pathway': label, 'col': col, 'n': n,
                     'lambda': lam, 'beta': beta, 'SE': se, 'p': p})
        print(f"  {label:<22} β={beta:+.4f}  SE={se:.4f}  p={p:.4f}  n={n}")

    return pd.DataFrame(rows)


def plot_forest(results: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 3.6))

    labels  = results['pathway'].tolist()
    betas   = results['beta'].values
    ses     = results['SE'].values
    pvals   = results['p'].values
    n_rows  = len(results)
    y_pos   = np.arange(n_rows)

    CI95 = 1.96 * ses
    sig  = pvals < ALPHA

    colors = ['#2166ac' if s else '#999999' for s in sig]

    for i, (y, b, ci, c, p) in enumerate(zip(y_pos, betas, CI95, colors, pvals)):
        ax.errorbar(b, y, xerr=ci, fmt='o', color=c, markersize=6,
                    linewidth=1.5, capsize=3, capthick=1.5, zorder=3)
        star = '*' if p < ALPHA else ''
        p_str = f'p = {p:.3f}{star}' if p >= 0.001 else f'p < 0.001{star}'
        ax.text(b + ci + 0.0005, y, f'  β={b:+.3f}, {p_str}',
                va='center', ha='left', fontsize=7.5, color=c)

    ax.axvline(0, color='black', linewidth=0.8, linestyle='--', zorder=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('PGLS β (pathway density → niche breadth)', fontsize=9)
    ax.set_title('Pathway-specific PGLS: 47-KO expanded metal-cofactor set',
                 fontsize=9, pad=6)

    sig_patch = mpatches.Patch(color='#2166ac', label=f'Significant (p < {ALPHA})')
    ns_patch  = mpatches.Patch(color='#999999', label='Not significant')
    ax.legend(handles=[sig_patch, ns_patch], fontsize=8, loc='lower right',
              framealpha=0.85)

    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='x', labelsize=8)

    # widen x-limits to make room for annotation text
    xlim = ax.get_xlim()
    ax.set_xlim(xlim[0] - 0.001, xlim[1] + 0.018)

    plt.tight_layout()
    out = FIG / 'fig_pathway_forest_plot.pdf'
    plt.savefig(out, dpi=300, bbox_inches='tight')
    print(f"Saved: {out}")
    plt.close()


def main() -> None:
    print("Running pathway-specific PGLS …")
    results = run_pathway_pgls()
    out_csv = DATA / 'pathway_pgls_results.csv'
    results.to_csv(out_csv, index=False)
    print(f"Saved: {out_csv}")
    print("\nGenerating forest plot …")
    plot_forest(results)


if __name__ == '__main__':
    main()
