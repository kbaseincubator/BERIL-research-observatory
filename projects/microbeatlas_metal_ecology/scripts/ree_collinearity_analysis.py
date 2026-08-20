#!/usr/bin/env python3
"""
ree_collinearity_analysis.py

6-part REE collinearity analysis using existing outputs.

Parts:
  1. Pairwise REE correlation matrix (concentration data, 634 samples)
  2. KO sharing: how many sig pairs are shared across REE pairs
  3. PCA of REE concentrations — scree + biplot
  4. Overlap inflation: unique KOs vs KO-REE pairs
  5. Hit stability: do high-Ce KOs also pass FDR for other REE?
  6. Summary table

All outputs → data/ree_collinearity/
"""
import sys
sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

DATA  = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm')
FIGS  = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/figures')
OUT   = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/ree_collinearity')
OUT.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

REE_ORDER = ['La','Ce','Pr','Nd','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Y','Sc']

print("Loading data...")
usgs = pd.read_csv(DATA / 'gam_results_usgs_all.csv')
conc = pd.read_csv(DATA / 'usgs_concentrations_634.csv')

ree_present = [r for r in REE_ORDER if r in usgs.metal.unique() and f'{r}_ppm' in conc.columns]
ree_cols    = [f'{r}_ppm' for r in ree_present]  # column names in concentration file
print(f"REE in dataset: {ree_present} ({len(ree_present)})")

# ── 1. Pairwise REE correlations (concentrations) ─────────────────────────────
print("\n[1] Pairwise REE correlations...")
ree_conc = conc[ree_cols].apply(np.log1p)  # log-transform; same order as ree_present
n_ree = len(ree_present)

corr_r   = np.full((n_ree, n_ree), np.nan)
corr_p   = np.full((n_ree, n_ree), np.nan)
n_pairs  = np.full((n_ree, n_ree), 0, dtype=int)

for i, a in enumerate(ree_present):
    for j, b in enumerate(ree_present):
        ca, cb = f'{a}_ppm', f'{b}_ppm'
        if i == j:
            corr_r[i, j] = 1.0; corr_p[i, j] = 0.0; n_pairs[i,j] = conc[ca].notna().sum()
            continue
        mask = conc[ca].notna() & conc[cb].notna()
        if mask.sum() >= 10:
            r, p = stats.spearmanr(np.log1p(conc.loc[mask, ca]), np.log1p(conc.loc[mask, cb]))
            corr_r[i, j] = r; corr_p[i, j] = p; n_pairs[i, j] = mask.sum()

corr_df = pd.DataFrame(corr_r, index=ree_present, columns=ree_present)
corr_df.to_csv(OUT / 'ree_spearman_corr.csv')
print(f"  Median off-diagonal r: {np.nanmedian(corr_r[np.triu_indices(n_ree, k=1)]):.3f}")
strong_pairs = [(ree_present[i], ree_present[j], corr_r[i,j])
                for i,j in zip(*np.triu_indices(n_ree, k=1)) if corr_r[i,j] > 0.85]
print(f"  Pairs with r>0.85: {len(strong_pairs)}")
for a, b, r in strong_pairs[:8]:
    print(f"    {a}×{b}: r={r:.3f}")

# Figure 1: correlation heatmap
fig, ax = plt.subplots(figsize=(FIGW['1.5col'], FIGW['1.5col']))
im = ax.imshow(corr_r, vmin=0, vmax=1, cmap='YlOrRd', aspect='equal')
ax.set_xticks(range(n_ree)); ax.set_xticklabels(ree_present, rotation=45, ha='right')
ax.set_yticks(range(n_ree)); ax.set_yticklabels(ree_present)
plt.colorbar(im, ax=ax, label="Spearman r", shrink=0.8, pad=0.02)
ax.set_title("REE concentration correlations\n(log-transformed, n=634 soil samples)", fontsize=10)
fig.suptitle("REE Collinearity: Spearman Correlations", fontsize=11, fontweight='bold', y=1.02)
save(fig, FIGS / 'fig_nb_ree_corr_heatmap')

# ── 2. KO sharing matrix ──────────────────────────────────────────────────────
print("\n[2] KO sharing matrix...")
sig_sets = {}
for m in ree_present:
    sig_sets[m] = set(usgs.loc[(usgs.metal == m) & (usgs.q_BH_full < 0.05), 'ko_id'])

n_sig = {m: len(s) for m, s in sig_sets.items()}
print(f"  Sig KOs per REE: {n_sig}")

overlap = np.zeros((n_ree, n_ree), dtype=int)
jaccard = np.zeros((n_ree, n_ree))
for i, a in enumerate(ree_present):
    for j, b in enumerate(ree_present):
        inter = len(sig_sets[a] & sig_sets[b])
        union = len(sig_sets[a] | sig_sets[b])
        overlap[i, j] = inter
        jaccard[i, j] = inter / union if union > 0 else 0.0

overlap_df = pd.DataFrame(overlap, index=ree_present, columns=ree_present)
jaccard_df = pd.DataFrame(jaccard, index=ree_present, columns=ree_present)
overlap_df.to_csv(OUT / 'ree_ko_overlap_count.csv')
jaccard_df.to_csv(OUT / 'ree_ko_jaccard.csv')
print(f"  Ce–Y KO overlap: {overlap_df.loc['Ce','Y']}, Jaccard: {jaccard_df.loc['Ce','Y']:.3f}")
print(f"  Ce–Lu KO overlap: {overlap_df.loc['Ce','Lu']}, Jaccard: {jaccard_df.loc['Ce','Lu']:.3f}")

# Figure 2: overlap heatmap
fig, axes = plt.subplots(1, 2, figsize=(FIGW['2col'], ROW_H))
im1 = axes[0].imshow(np.log1p(overlap), cmap='Blues', aspect='equal')
axes[0].set_xticks(range(n_ree)); axes[0].set_xticklabels(ree_present, rotation=45, ha='right')
axes[0].set_yticks(range(n_ree)); axes[0].set_yticklabels(ree_present)
plt.colorbar(im1, ax=axes[0], label="log(shared KOs + 1)", shrink=0.8)
axes[0].set_title("Shared sig KOs (count)", fontsize=10)

im2 = axes[1].imshow(jaccard, vmin=0, vmax=1, cmap='Blues', aspect='equal')
axes[1].set_xticks(range(n_ree)); axes[1].set_xticklabels(ree_present, rotation=45, ha='right')
axes[1].set_yticks(range(n_ree)); axes[1].set_yticklabels(ree_present)
plt.colorbar(im2, ax=axes[1], label="Jaccard index", shrink=0.8)
axes[1].set_title("Jaccard similarity", fontsize=10)
fig.suptitle("REE Collinearity: KO-level overlap", fontsize=11, fontweight='bold', y=1.02)
save(fig, FIGS / 'fig_nb_ree_ko_overlap')

# ── 3. PCA of REE concentrations ──────────────────────────────────────────────
print("\n[3] PCA of REE concentrations...")
ree_mask = conc[ree_cols].notna().all(axis=1)
X_raw = conc.loc[ree_mask, ree_cols].apply(np.log1p).values
n_pca = ree_mask.sum()
print(f"  Samples with all REE: {n_pca}")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)
pca = PCA()
scores = pca.fit_transform(X_scaled)
ev = pca.explained_variance_ratio_

print(f"  PC1 variance explained: {ev[0]*100:.1f}%")
print(f"  PC1+PC2: {(ev[0]+ev[1])*100:.1f}%")
print(f"  PC loadings (PC1): {dict(zip(ree_present, pca.components_[0].round(3)))}")

# Save scores for later use (conditional test)
pca_scores_df = pd.DataFrame({
    'sample_id': conc.loc[ree_mask, 'sample_id'].values if 'sample_id' in conc.columns else conc.index[ree_mask].astype(str),
    'pc1': scores[:, 0],
    'pc2': scores[:, 1],
    'pc3': scores[:, 2] if scores.shape[1] > 2 else np.nan,
})
pca_scores_df.to_csv(OUT / 'ree_pca_scores.csv', index=False)

# Figure 3: scree + biplot
fig, axes = plt.subplots(1, 2, figsize=(FIGW['2col'], ROW_H))
# Scree
n_plot = min(10, len(ev))
axes[0].bar(range(1, n_plot+1), ev[:n_plot]*100, color=PALETTE[0], edgecolor='k', linewidth=0.5)
axes[0].axhline(5, color='gray', lw=0.8, ls='--')
axes[0].set_xlabel("Principal component")
axes[0].set_ylabel("Variance explained (%)")
axes[0].set_title("Scree plot", fontsize=10)
from figure_style import grid_h
grid_h(axes[0])

# Loadings scatter (PC1 vs PC2)
lc1, lc2 = pca.components_[0], pca.components_[1]
for k, r in enumerate(ree_present):
    axes[1].annotate(r, (lc1[k], lc2[k]), fontsize=7.5, ha='center', va='center',
                     color=PALETTE[0])
    axes[1].arrow(0, 0, lc1[k]*0.85, lc2[k]*0.85, head_width=0.01,
                  color=PALETTE[0], alpha=0.6, linewidth=0.7)
axes[1].axhline(0, color='gray', lw=0.6); axes[1].axvline(0, color='gray', lw=0.6)
axes[1].set_xlabel(f"PC1 ({ev[0]*100:.1f}%)")
axes[1].set_ylabel(f"PC2 ({ev[1]*100:.1f}%)")
axes[1].set_title("PCA loadings", fontsize=10)
fig.suptitle("REE Collinearity: PCA of concentrations", fontsize=11, fontweight='bold', y=1.02)
save(fig, FIGS / 'fig_nb_ree_pca')

# ── 4. Overlap inflation metric ───────────────────────────────────────────────
print("\n[4] Overlap inflation...")
ree_sig_all = usgs[(usgs.metal.isin(ree_present)) & (usgs.q_BH_full < 0.05)]
total_pairs = len(ree_sig_all)
unique_kos  = ree_sig_all.ko_id.nunique()
inflation   = total_pairs / unique_kos if unique_kos > 0 else np.nan
print(f"  Total sig KO×REE pairs: {total_pairs}")
print(f"  Unique KOs sig for any REE: {unique_kos}")
print(f"  Inflation factor: {inflation:.2f}x (avg REE per unique KO)")

# Distribution of REE-count per KO
from collections import Counter
ko_ree_counts = Counter(ree_sig_all.ko_id.values)
ree_count_dist = Counter(ko_ree_counts.values())
print("  Distribution (# REE : # KOs):")
for cnt in sorted(ree_count_dist.keys()):
    print(f"    {cnt} REE: {ree_count_dist[cnt]} KOs")

# Which KOs hit all or most REE?
top_kos = sorted(ko_ree_counts.items(), key=lambda x: -x[1])[:10]
print("  Top KOs by REE breadth:")
for ko, n in top_kos:
    metals_hit = list(ree_sig_all[ree_sig_all.ko_id == ko].metal.values)
    print(f"    {ko}: {n} REE — {metals_hit}")

# Save KO-REE breadth table
breadth_df = pd.DataFrame([
    {'ko_id': ko, 'n_ree_sig': cnt,
     'ree_list': ','.join(sorted(ree_sig_all[ree_sig_all.ko_id==ko].metal.values))}
    for ko, cnt in ko_ree_counts.items()
]).sort_values('n_ree_sig', ascending=False)
breadth_df.to_csv(OUT / 'ree_ko_breadth.csv', index=False)

# Figure 4: bar chart of distribution
fig, ax = plt.subplots(figsize=(FIGW['1col'], ROW_H))
xs = sorted(ree_count_dist.keys())
ys = [ree_count_dist[x] for x in xs]
ax.bar(xs, ys, color=PALETTE[1], edgecolor='k', linewidth=0.5)
ax.set_xlabel("# REE metals significant")
ax.set_ylabel("# KOs")
ax.set_title(f"KO breadth across REE\n(inflation {inflation:.1f}×)", fontsize=10)
grid_h(ax)
save(fig, FIGS / 'fig_nb_ree_ko_breadth')

# ── 5. Hit stability: are Ce-driven hits just Ce-abundant samples? ─────────────
print("\n[5] Hit stability: Ce vs non-Ce top-REE comparison...")
# Compare q values for KOs sig in Ce vs the same KOs for Y (most dissimilar REE)
# to see if Ce-specific hits are real or collinearity artifacts

# KOs sig in Ce but NOT in Y
ce_only = sig_sets.get('Ce', set()) - sig_sets.get('Y', set())
y_only  = sig_sets.get('Y', set()) - sig_sets.get('Ce', set())
both    = sig_sets.get('Ce', set()) & sig_sets.get('Y', set())
print(f"  Ce-only KOs: {len(ce_only)}, Y-only: {len(y_only)}, shared: {len(both)}")

# For shared KOs: correlation of log-q values between Ce and Y?
shared_ko_df = ree_sig_all[ree_sig_all.ko_id.isin(both)].pivot_table(
    index='ko_id', columns='metal', values='q_BH_full')
if 'Ce' in shared_ko_df.columns and 'Y' in shared_ko_df.columns:
    r_ce_y, p_ce_y = stats.spearmanr(
        np.log10(shared_ko_df['Ce'].dropna() + 1e-300),
        np.log10(shared_ko_df['Y'].dropna() + 1e-300))
    print(f"  q(Ce) vs q(Y) correlation for shared KOs: r={r_ce_y:.3f} p={p_ce_y:.2e}")

# Correlation of effect sizes (delta_r2_full) across REE for shared KOs
shared_full = ree_sig_all[ree_sig_all.ko_id.isin(both)]
dr2_pivot = shared_full.pivot_table(index='ko_id', columns='metal', values='delta_r2_full')
available_for_corr = [m for m in ['Ce','Y','Lu','Tb','La'] if m in dr2_pivot.columns]
if len(available_for_corr) >= 2:
    from itertools import combinations
    print("  delta_R2 correlations (shared KOs):")
    for a, b in combinations(available_for_corr[:5], 2):
        mask = dr2_pivot[a].notna() & dr2_pivot[b].notna()
        if mask.sum() >= 5:
            r, p = stats.spearmanr(dr2_pivot.loc[mask, a], dr2_pivot.loc[mask, b])
            print(f"    {a}×{b}: r={r:.3f} (n={mask.sum()})")

# ── 6. Summary table ──────────────────────────────────────────────────────────
print("\n[6] Summary table...")
summary_rows = []
for m in ree_present:
    n_m = n_sig[m]
    pct_shared_with_ce = (len(sig_sets[m] & sig_sets.get('Ce',set())) / n_m * 100) if n_m > 0 else 0
    median_r_to_ce = corr_df.loc[m, 'Ce'] if 'Ce' in corr_df.columns else np.nan
    summary_rows.append({
        'REE': m, 'n_sig': n_m,
        'pct_shared_with_Ce': round(pct_shared_with_ce, 1),
        'spearman_r_to_Ce': round(median_r_to_ce, 3),
        'jaccard_with_Ce': round(jaccard_df.loc[m, 'Ce'] if 'Ce' in jaccard_df.columns else 0, 3),
    })
summary_df = pd.DataFrame(summary_rows).sort_values('n_sig', ascending=False)
summary_df.to_csv(OUT / 'ree_collinearity_summary.csv', index=False)
print(summary_df.to_string(index=False))

# Figure 5: correlation r vs n_sig scatter
fig, ax = plt.subplots(figsize=(FIGW['1col'], ROW_H))
for i, row in summary_df.iterrows():
    ax.scatter(row['spearman_r_to_Ce'], row['n_sig'],
               color=PALETTE[0], edgecolors='k', linewidths=0.5, s=40, zorder=3)
    if row['n_sig'] >= 50:
        ax.annotate(row['REE'], (row['spearman_r_to_Ce'], row['n_sig']),
                    fontsize=7.5, xytext=(4, 0), textcoords='offset points')
ax.set_xlabel("Spearman r to Ce (concentration)")
ax.set_ylabel("# sig KO×REE pairs (FDR<0.05)")
ax.set_title("REE hits correlate with\nconcentration collinearity", fontsize=10)
grid_h(ax)
save(fig, FIGS / 'fig_nb_ree_hits_vs_r')

print("\n=== REE collinearity analysis complete ===")
print(f"Outputs: {OUT}")
print(f"Figures: {FIGS}/fig_nb_ree_*.pdf")
print(f"\nKey findings:")
print(f"  PC1 explains {ev[0]*100:.1f}% of REE variance")
print(f"  Median off-diagonal Spearman r: {np.nanmedian(corr_r[np.triu_indices(n_ree, k=1)]):.3f}")
print(f"  Inflation factor: {inflation:.2f}x ({total_pairs} pairs, {unique_kos} unique KOs)")
print(f"  Ce dominates: {n_sig.get('Ce',0)} of {total_pairs} REE hits ({n_sig.get('Ce',0)/total_pairs*100:.1f}%)")
