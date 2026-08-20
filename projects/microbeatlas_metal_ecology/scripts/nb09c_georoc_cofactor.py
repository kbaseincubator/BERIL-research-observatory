"""
NB09c: GeoROC × Cofactor Density Cross-Validation

Tests whether genera enriched in naturally high-metal environments (positive GeoROC
partial correlation) have higher cofactor gene density vs resistance gene density.
This directly tests the two-axis framework at the natural-environment level:
cofactor-dense genera should occupy naturally metal-rich niches (partial_r > 0),
while resistance gene density should not predict natural metal enrichment.

Input:
  - microbeatlas_metal_ecology/data/otu_georoc_tier1_6metal.csv
  - comprehensive_metal_ecology/data/non_exclusive_category_densities.csv
Output:
  - figures/fig_nb09c_georoc_cofactor.png
  - results/nb09c_georoc_cofactor_results.csv (printed summary)
"""
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

PROJECT_DIR = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology')
CME_DIR    = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
FIG_DIR    = PROJECT_DIR / 'figures'
FIG_DIR.mkdir(exist_ok=True)
RES_DIR    = PROJECT_DIR / 'results'
RES_DIR.mkdir(exist_ok=True)

# ── 1. Load ──────────────────────────────────────────────────────────────────
georoc    = pd.read_csv(PROJECT_DIR / 'data' / 'otu_georoc_tier1_6metal.csv')
densities = pd.read_csv(CME_DIR / 'data' / 'non_exclusive_category_densities.csv')

print(f"GeoROC: {georoc.shape}  columns: {list(georoc.columns)}")
print(f"Densities: {densities.shape}  columns: {list(densities.columns)}")
print(f"Metals: {sorted(georoc['exposure'].unique())}")
print(f"partial_r range: [{georoc['partial_r'].min():.3f}, {georoc['partial_r'].max():.3f}]")
print(f"p_adj_global < 0.05: {(georoc['p_adj_global'] < 0.05).sum():,} / {len(georoc):,}")

# ── 2. Join on genus ──────────────────────────────────────────────────────────
georoc['genus_lower'] = georoc['genus'].str.lower().str.strip()
merged = georoc.merge(
    densities[['genus_lower', 'ne_cofactor_z', 'ne_resistance_z', 'ne_metaldep_t12_z']],
    on='genus_lower', how='inner'
)
print(f"\nAfter genus join: {len(merged):,} pairs, {merged['genus_lower'].nunique():,} unique genera")
print(f"Coverage: {merged['genus_lower'].nunique()} / {georoc['genus'].str.lower().str.strip().nunique()} OTU genera matched")

# ── 3. Pair-level Spearman (all pairs) ───────────────────────────────────────
print("\n=== PAIR-LEVEL SPEARMAN (all pairs) ===")
for feat, label in [('ne_cofactor_z', 'Cofactor'), ('ne_resistance_z', 'Resistance'),
                    ('ne_metaldep_t12_z', 'Total metal-gene')]:
    r, p = stats.spearmanr(merged[feat], merged['partial_r'])
    print(f"  {label}: rho={r:+.4f}, p={p:.3e}  (n={len(merged):,})")

# ── 4. Genus-level aggregation (one row per genus, mean partial_r across metals) ─
genus_agg = (merged
    .groupby('genus_lower')
    .agg(
        mean_partial_r   = ('partial_r',      'mean'),
        n_metals         = ('partial_r',      'count'),
        ne_cofactor_z    = ('ne_cofactor_z',  'first'),
        ne_resistance_z  = ('ne_resistance_z','first'),
        ne_metaldep_t12_z= ('ne_metaldep_t12_z','first'),
    )
    .reset_index())

print(f"\n=== GENUS-LEVEL SPEARMAN (n={len(genus_agg)} genera) ===")
for feat, label in [('ne_cofactor_z', 'Cofactor'), ('ne_resistance_z', 'Resistance'),
                    ('ne_metaldep_t12_z', 'Total metal-gene')]:
    r, p = stats.spearmanr(genus_agg[feat], genus_agg['mean_partial_r'])
    print(f"  {label}: rho={r:+.4f}, p={p:.3e}")

# ── 5. Mann-Whitney: high-natural-metal vs low-natural-metal genera ───────────
high = genus_agg[genus_agg['mean_partial_r'] > 0]
low  = genus_agg[genus_agg['mean_partial_r'] < 0]
neutral = genus_agg[genus_agg['mean_partial_r'] == 0]
print(f"\n=== MANN-WHITNEY (high-metal n={len(high)}, low-metal n={len(low)}, neutral={len(neutral)}) ===")
for feat, label in [('ne_cofactor_z', 'Cofactor'), ('ne_resistance_z', 'Resistance')]:
    u, p = stats.mannwhitneyu(high[feat], low[feat], alternative='greater')
    print(f"  {label} (high > low?): U={u:.0f}, p={p:.4e}")
    print(f"    High-metal   median {label}: {high[feat].median():.4f}")
    print(f"    Low-metal    median {label}: {low[feat].median():.4f}")
    print(f"    Neutral      median {label}: {neutral[feat].median():.4f}" if len(neutral) > 0 else "")

# ── 6. Per-metal breakdown ────────────────────────────────────────────────────
print("\n=== PER-METAL GENUS-LEVEL SPEARMAN ===")
metal_results = []
for metal in sorted(merged['exposure'].unique()):
    g = (merged[merged['exposure'] == metal]
         .groupby('genus_lower')
         .agg(partial_r=('partial_r','mean'),
              ne_cofactor_z=('ne_cofactor_z','first'),
              ne_resistance_z=('ne_resistance_z','first'))
         .reset_index())
    r_c, p_c = stats.spearmanr(g['ne_cofactor_z'],   g['partial_r'])
    r_r, p_r = stats.spearmanr(g['ne_resistance_z'], g['partial_r'])
    metal_results.append({'metal': metal, 'n_genera': len(g),
                          'rho_cofactor': r_c, 'p_cofactor': p_c,
                          'rho_resistance': r_r, 'p_resistance': p_r})
    print(f"  {metal} (n={len(g):3d}): cofactor rho={r_c:+.3f} p={p_c:.3f} | "
          f"resistance rho={r_r:+.3f} p={p_r:.3f}")

# ── 7. Save results ──────────────────────────────────────────────────────────
genus_agg.to_csv(RES_DIR / 'nb09c_genus_georoc_density.csv', index=False)
pd.DataFrame(metal_results).to_csv(RES_DIR / 'nb09c_per_metal_spearman.csv', index=False)
print(f"\nSaved results to {RES_DIR}")

# ── 8. Figure ────────────────────────────────────────────────────────────────
try:
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    fig = plt.figure(figsize=(12, 5))
    gs  = gridspec.GridSpec(1, 2, figure=fig, wspace=0.4)

    ax1 = fig.add_subplot(gs[0])
    ax1.scatter(genus_agg['ne_cofactor_z'],    genus_agg['mean_partial_r'],
                alpha=0.4, s=15, color='steelblue', label='Cofactor')
    ax1.scatter(genus_agg['ne_resistance_z'],  genus_agg['mean_partial_r'],
                alpha=0.4, s=15, color='salmon',    label='Resistance')
    ax1.axhline(0, color='k', lw=0.5, ls='--')
    ax1.axvline(0, color='k', lw=0.5, ls='--')
    ax1.set_xlabel('Gene density z-score')
    ax1.set_ylabel('Mean GeoROC partial_r (natural metal enrichment)')
    ax1.set_title('Genus-level: GeoROC × gene density')
    ax1.legend()

    ax2 = fig.add_subplot(gs[1])
    df_res = pd.DataFrame(metal_results).sort_values('metal')
    x = np.arange(len(df_res))
    w = 0.35
    ax2.bar(x - w/2, df_res['rho_cofactor'],   w, color='steelblue', label='Cofactor')
    ax2.bar(x + w/2, df_res['rho_resistance'],  w, color='salmon',    label='Resistance')
    ax2.axhline(0, color='k', lw=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(df_res['metal'], rotation=30, ha='right')
    ax2.set_ylabel('Spearman rho (partial_r ~ density)')
    ax2.set_title('Per-metal breakdown')
    ax2.legend()

    fig.suptitle('NB09c: GeoROC natural metal enrichment vs cofactor/resistance density',
                 fontsize=11, y=1.02)
    fig.tight_layout()
    plt.savefig(FIG_DIR / 'fig_nb09c_georoc_cofactor.png', dpi=150, bbox_inches='tight')
    print(f"Saved figure to {FIG_DIR / 'fig_nb09c_georoc_cofactor.png'}")
    plt.close()
except Exception as e:
    print(f"Figure skipped: {e}")

print("\nDONE.")
