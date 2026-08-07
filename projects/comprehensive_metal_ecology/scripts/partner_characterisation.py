#!/usr/bin/env python3
"""
Partner characterisation analysis.
Top-50 metal-gene-rich focal genera vs phylum-matched control-50.
Soil stratum (strongest PGLS signal).
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
import sys, time
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import hypergeom, t as t_dist, mannwhitneyu, chi2_contingency
from statsmodels.stats.multitest import multipletests
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import warnings
warnings.filterwarnings('ignore')

BASE    = "/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology"
DATA    = f"{BASE}/data"
RES     = f"{BASE}/results"
MATRIX  = "/tmp/cooc_genus_sample_long.parquet"
ENV_MAP = "/tmp/cooc_sample_env.parquet"
FDR_ALPHA = 0.05
PHI_THRESH = 0.3   # strong-association filter for dense network
TOP_N_FALLBACK = 20  # per-focal fallback if phi>0.3 gives <5 partners

SOIL_ENVS = {'soil', 'agricultural', 'farm', 'paddy', 'field',
             'forest', 'shrub', 'peatland', 'desert'}

PHYLUM_COLORS = {
    'Proteobacteria': '#2a78d6',
    'Firmicutes':     '#e38b00',
    'Actinobacteria': '#2da44e',
    'Bacteroidetes':  '#8250df',
    'Aquificae':      '#cf222e',
    'Chlorobi':       '#0e7240',
    'Verrucomicrobia':'#bf8700',
    'Spirochaetes':   '#953800',
    'Other':          '#aaaaaa',
}

print("=" * 60)
print("Partner characterisation — soil stratum")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────
# Step 0: Load trait table
# ─────────────────────────────────────────────────────────────────
traits = pd.read_csv(f"{DATA}/01_pgls_input_bacteria.csv")
q75 = traits['ko_per_mb_primary'].quantile(0.75)
traits['is_top_quartile'] = traits['ko_per_mb_primary'] >= q75
print(f"Trait table: {len(traits)} genera, Q75 ko_per_mb = {q75:.3f}")

# ─────────────────────────────────────────────────────────────────
# Step 1: Build soil binary matrix & compute phi
# ─────────────────────────────────────────────────────────────────
CACHE_DIR = "/tmp/partchar_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_GENERA  = f"{CACHE_DIR}/genera.npy"
CACHE_SAMPLES = f"{CACHE_DIR}/samples.npy"
CACHE_PHI     = f"{CACHE_DIR}/phi.npy"
CACHE_SIG     = f"{CACHE_DIR}/sig_pos_mask.npy"
CACHE_TRIU_I  = f"{CACHE_DIR}/triu_i.npy"
CACHE_TRIU_J  = f"{CACHE_DIR}/triu_j.npy"
CACHE_ROWSUMS = f"{CACHE_DIR}/row_sums.npy"

if all(os.path.exists(p) for p in [CACHE_PHI, CACHE_SIG, CACHE_GENERA, CACHE_SAMPLES,
                                     CACHE_TRIU_I, CACHE_TRIU_J, CACHE_ROWSUMS]):
    print("  Loading cached soil matrix & phi...")
    all_genera  = np.load(CACHE_GENERA, allow_pickle=True).tolist()
    all_samples = np.load(CACHE_SAMPLES, allow_pickle=True).tolist()
    phi          = np.load(CACHE_PHI)
    sig_pos_mask = np.load(CACHE_SIG)
    triu_i       = np.load(CACHE_TRIU_I)
    triu_j       = np.load(CACHE_TRIU_J)
    row_sums     = np.load(CACHE_ROWSUMS)
    G, S = len(all_genera), len(all_samples)
    N_PAIRS = len(triu_i)
    g_idx = {g: i for i, g in enumerate(all_genera)}
    phi_sig = phi[sig_pos_mask]
    print(f"  Soil: {G} genera × {S:,} samples, {N_PAIRS:,} pairs (from cache)")
else:
    print("\n--- Building soil binary matrix ---")
    t0 = time.time()
    sg_all = pd.read_parquet(MATRIX)
    env_map = pd.read_parquet(ENV_MAP)
    env_map['Env_Level_1'] = env_map['Env_Level_1'].str.lower().str.strip()

    soil_acc = set(env_map[env_map['Env_Level_1'].isin(SOIL_ENVS)]['accession_id'])
    sg_soil = sg_all[sg_all['accession_id'].isin(soil_acc)].copy()
    prev = sg_soil.groupby('genus_lower')['accession_id'].nunique()
    sg_soil = sg_soil[sg_soil['genus_lower'].isin(prev[prev >= 10].index)].copy()

    all_genera  = sorted(sg_soil['genus_lower'].unique())
    all_samples = sorted(sg_soil['accession_id'].unique())
    G, S = len(all_genera), len(all_samples)
    g_idx = {g: i for i, g in enumerate(all_genera)}
    s_idx = {s: i for i, s in enumerate(all_samples)}
    print(f"  Soil: {G} genera × {S:,} samples  ({time.time()-t0:.1f}s)")

    row_idx = sg_soil['genus_lower'].map(g_idx).values
    col_idx = sg_soil['accession_id'].map(s_idx).values
    M = sp.csr_matrix((np.ones(len(sg_soil), dtype=np.uint8), (row_idx, col_idx)),
                      shape=(G, S), dtype=np.uint8)
    row_sums = np.asarray(M.sum(axis=1)).ravel()

    triu_i, triu_j = np.triu_indices(G, k=1)
    N_PAIRS = len(triu_i)
    print(f"  Pairs: {N_PAIRS:,}")

    print("  Computing co-occurrence counts...")
    coo_counts = (M.astype(np.int32) @ M.T.astype(np.int32)).toarray()
    np.fill_diagonal(coo_counts, 0)
    K_obs = coo_counts[triu_i, triu_j]
    N_i   = row_sums[triu_i]
    N_j   = row_sums[triu_j]

    print("  Hypergeometric FDR...")
    p_pos = np.zeros(N_PAIRS, dtype=np.float64)
    CHUNK = 1_000_000
    for start in range(0, N_PAIRS, CHUNK):
        end = min(start + CHUNK, N_PAIRS)
        p_pos[start:end] = hypergeom.sf(K_obs[start:end] - 1, S, N_i[start:end], N_j[start:end])
    _, p_pos_fdr, _, _ = multipletests(p_pos, method='fdr_bh')
    sig_pos_mask = p_pos_fdr < FDR_ALPHA

    print("  Computing phi...")
    denom = np.sqrt(N_i.astype(np.float64) * (S - N_i.astype(np.float64)) *
                    N_j.astype(np.float64) * (S - N_j.astype(np.float64)) + 1e-300)
    phi = (K_obs.astype(np.float64) * S - N_i.astype(np.float64) * N_j.astype(np.float64)) / denom
    phi = np.clip(phi, -1, 1)
    phi_sig = phi[sig_pos_mask]

    # Save cache
    np.save(CACHE_GENERA,  np.array(all_genera))
    np.save(CACHE_SAMPLES, np.array(all_samples))
    np.save(CACHE_PHI,     phi.astype(np.float32))
    np.save(CACHE_SIG,     sig_pos_mask)
    np.save(CACHE_TRIU_I,  triu_i)
    np.save(CACHE_TRIU_J,  triu_j)
    np.save(CACHE_ROWSUMS, row_sums)
    print("  Cache saved.")

print(f"  Sig+ pairs: {sig_pos_mask.sum():,} ({sig_pos_mask.sum()*100/N_PAIRS:.1f}%)")
print(f"  Phi in sig+ pairs: median={np.median(phi_sig):.4f}, "
      f"p90={np.percentile(phi_sig,90):.4f}, "
      f"p95={np.percentile(phi_sig,95):.4f}, "
      f">0.3: {(phi_sig>0.3).sum():,} ({(phi_sig>0.3).sum()*100/len(phi_sig):.2f}%)")

# ─────────────────────────────────────────────────────────────────
# Step 2: Select focal (top-50) and control-50 genera
# ─────────────────────────────────────────────────────────────────
print("\n--- Selecting focal and control genera ---")
soil_traits = traits[traits['genus_lower'].isin(all_genera)].copy()

# Top-50 by ko_per_mb_primary (from soil-present genera)
top50_df = soil_traits.nlargest(50, 'ko_per_mb_primary')
top50_set = set(top50_df['genus_lower'])
print(f"Top-50 focal: {len(top50_set)} genera (min ko_per_mb = {top50_df.ko_per_mb_primary.min():.2f})")

# Control-50: phylum-matched, median ko_per_mb_primary
median_ko = soil_traits['ko_per_mb_primary'].median()
sd_ko     = soil_traits['ko_per_mb_primary'].std()
ctrl_pool = soil_traits[
    (~soil_traits['genus_lower'].isin(top50_set)) &
    (soil_traits['ko_per_mb_primary'] >= median_ko - 0.5*sd_ko) &
    (soil_traits['ko_per_mb_primary'] <= median_ko + 0.5*sd_ko)
].copy()
print(f"Control pool (±0.5 SD of median): {len(ctrl_pool)} genera")

# Phylum-stratified sampling to match top-50 distribution
top50_phylum_counts = top50_df['phylum'].value_counts()
ctrl_rows = []
rng = np.random.default_rng(42)
for phy, n in top50_phylum_counts.items():
    pool_phy = ctrl_pool[ctrl_pool['phylum'] == phy]
    avail = min(n, len(pool_phy))
    if avail > 0:
        chosen = pool_phy.sample(avail, random_state=42)
        ctrl_rows.append(chosen)
# Fill remaining from any phylum
ctrl50_df = pd.concat(ctrl_rows, ignore_index=True) if ctrl_rows else pd.DataFrame()
n_needed = 50 - len(ctrl50_df)
if n_needed > 0:
    leftover = ctrl_pool[~ctrl_pool['genus_lower'].isin(set(ctrl50_df.get('genus_lower', [])))
                         ].sample(min(n_needed, len(ctrl_pool)), random_state=42)
    ctrl50_df = pd.concat([ctrl50_df, leftover], ignore_index=True)
ctrl50_set = set(ctrl50_df['genus_lower'])
print(f"Control-50: {len(ctrl50_set)} genera (median ko_per_mb = {ctrl50_df.ko_per_mb_primary.median():.2f})")
print(f"  Phylum dist: {dict(ctrl50_df.phylum.value_counts())}")

# ─────────────────────────────────────────────────────────────────
# Step 3: Extract partners for focal genera
# ─────────────────────────────────────────────────────────────────
print("\n--- Extracting partners ---")

def get_partners(focal_set, phi_arr, sig_arr, g_to_i, i_to_g, triu_i_arr, triu_j_arr,
                 phi_threshold=PHI_THRESH, top_n=TOP_N_FALLBACK):
    """
    For each genus in focal_set, return list of dicts with partner info.
    Uses phi > threshold; if genus has <5 such partners, falls back to top_n by phi.
    """
    # Build per-genus partner lists using the upper-triangle pairs
    # Need to look up pairs where focal genus is either i or j
    focal_idx = {g: g_to_i[g] for g in focal_set if g in g_to_i}

    # Build sig-phi mask
    strong_mask = sig_arr & (phi_arr > phi_threshold)

    # Precompute: for each genus index, which pairs involve it?
    # Build reverse lookup: gi -> list of (partner_j, phi, phi_strong)
    partner_dict = {gi: [] for gi in focal_idx.values()}

    for pair_k in range(len(triu_i_arr)):
        gi, gj = triu_i_arr[pair_k], triu_j_arr[pair_k]
        if gi in partner_dict or gj in partner_dict:
            is_sig   = bool(sig_arr[pair_k])
            phi_val  = float(phi_arr[pair_k])
            is_strong = bool(strong_mask[pair_k])
            if is_sig:
                if gi in partner_dict:
                    partner_dict[gi].append((gj, phi_val, is_strong))
                if gj in partner_dict:
                    partner_dict[gj].append((gi, phi_val, is_strong))

    rows = []
    for g, gi in focal_idx.items():
        partners = partner_dict[gi]
        # Filter: phi > threshold; fallback to top_n if <5
        strong = [(p, ph) for p, ph, strong in partners if strong]
        if len(strong) < 5:
            all_sorted = sorted(partners, key=lambda x: -x[1])[:top_n]
            used = [(p, ph) for p, ph, _ in all_sorted]
        else:
            used = strong
        for p_idx, p_phi in used:
            rows.append({'focal': g, 'partner': i_to_g[p_idx], 'phi': p_phi})
    return pd.DataFrame(rows)

i_to_g = {i: g for g, i in g_idx.items()}

print("  Building top-50 partner table (this may take 30-90s for 4.9M pairs)...")
t_p = time.time()
top50_partners = get_partners(top50_set, phi, sig_pos_mask, g_idx, i_to_g, triu_i, triu_j)
print(f"  Top-50 partners: {len(top50_partners):,} rows  ({time.time()-t_p:.0f}s)")

print("  Building control-50 partner table...")
ctrl50_partners = get_partners(ctrl50_set, phi, sig_pos_mask, g_idx, i_to_g, triu_i, triu_j)
print(f"  Control-50 partners: {len(ctrl50_partners):,} rows")

# ─────────────────────────────────────────────────────────────────
# Step 4: Add partner traits
# ─────────────────────────────────────────────────────────────────
print("\n--- Characterising partners ---")
trait_cols = ['genus_lower', 'ko_per_mb_primary', 'mean_levins_B_std', 'phylum', 'is_top_quartile']
t_sub = traits[trait_cols].rename(columns={'genus_lower': 'partner'})

top50_partners = top50_partners.merge(t_sub, on='partner', how='left')
ctrl50_partners = ctrl50_partners.merge(t_sub, on='partner', how='left')

# Per-focal-genus summary
def partner_summary(pdt, focal_df, label):
    grp = pdt.dropna(subset=['ko_per_mb_primary']).groupby('focal').agg(
        n_partners=('partner', 'count'),
        mean_partner_ko=('ko_per_mb_primary', 'mean'),
        mean_partner_B=('mean_levins_B_std', 'mean'),
        pct_top_quartile=('is_top_quartile', 'mean'),
    ).reset_index()
    # Add focal traits
    grp = grp.merge(focal_df[['genus_lower','ko_per_mb_primary','phylum','mean_levins_B_std']],
                    left_on='focal', right_on='genus_lower', how='left', suffixes=('','_focal'))
    grp['group'] = label
    return grp

top50_summary  = partner_summary(top50_partners,  top50_df,  'top50')
ctrl50_summary = partner_summary(ctrl50_partners, ctrl50_df, 'control')
all_summary    = pd.concat([top50_summary, ctrl50_summary], ignore_index=True)

print(f"\n  Top-50 partner summary (n focal={len(top50_summary)}):")
print(f"    Mean partner ko_per_mb: {top50_summary.mean_partner_ko.mean():.3f} ± {top50_summary.mean_partner_ko.std():.3f}")
print(f"    Mean partner B_std:     {top50_summary.mean_partner_B.mean():.3f}")
print(f"    % partners top-quartile:{top50_summary.pct_top_quartile.mean()*100:.1f}%")
print(f"\n  Control-50 partner summary (n focal={len(ctrl50_summary)}):")
print(f"    Mean partner ko_per_mb: {ctrl50_summary.mean_partner_ko.mean():.3f} ± {ctrl50_summary.mean_partner_ko.std():.3f}")
print(f"    Mean partner B_std:     {ctrl50_summary.mean_partner_B.mean():.3f}")
print(f"    % partners top-quartile:{ctrl50_summary.pct_top_quartile.mean()*100:.1f}%")

# ─────────────────────────────────────────────────────────────────
# Step 5: Statistical tests
# ─────────────────────────────────────────────────────────────────
print("\n--- Statistical tests ---")

# Mann-Whitney U on mean partner KO density
top50_x  = top50_summary['mean_partner_ko'].dropna().values
ctrl50_x = ctrl50_summary['mean_partner_ko'].dropna().values
stat_ko, p_ko = mannwhitneyu(top50_x, ctrl50_x, alternative='two-sided')
print(f"Mann-Whitney U (partner ko_per_mb): U={stat_ko:.0f}, p={p_ko:.4e}")

# Mann-Whitney U on % top-quartile partners
top50_tq  = top50_summary['pct_top_quartile'].dropna().values.astype(float)
ctrl50_tq = ctrl50_summary['pct_top_quartile'].dropna().values.astype(float)
stat_tq, p_tq = mannwhitneyu(top50_tq, ctrl50_tq, alternative='two-sided')
print(f"Mann-Whitney U (% top-quartile): U={stat_tq:.0f}, p={p_tq:.4e}")

# Partner phylum distributions — chi-square
top50_phylum_ct  = top50_partners['phylum'].value_counts()
ctrl50_phylum_ct = ctrl50_partners['phylum'].value_counts()
all_phy = sorted(set(top50_phylum_ct.index) | set(ctrl50_phylum_ct.index))
contingency = np.array([[top50_phylum_ct.get(p, 0) for p in all_phy],
                         [ctrl50_phylum_ct.get(p, 0) for p in all_phy]])
chi2_stat, p_chi2, _, _ = chi2_contingency(contingency)
print(f"Chi-square (phylum distribution): χ²={chi2_stat:.2f}, p={p_chi2:.4e}")

# Spearman: focal ko_per_mb vs mean partner ko_per_mb
from scipy.stats import spearmanr
rho_top, p_rho_top = spearmanr(top50_summary['ko_per_mb_primary'], top50_summary['mean_partner_ko'])
rho_all, p_rho_all = spearmanr(all_summary['ko_per_mb_primary'], all_summary['mean_partner_ko'])
print(f"Spearman (focal ko vs mean partner ko, top-50): ρ={rho_top:.3f}, p={p_rho_top:.4e}")
print(f"Spearman (focal ko vs mean partner ko, all-100): ρ={rho_all:.3f}, p={p_rho_all:.4e}")

# ─────────────────────────────────────────────────────────────────
# Step 6: Figures
# ─────────────────────────────────────────────────────────────────
print("\n--- Generating figures ---")

def phy_color(phylum):
    return PHYLUM_COLORS.get(phylum, PHYLUM_COLORS['Other'])

# ── Figure A: Bipartite network (top-10 focal × top-5 partners by phi) ──
fig_a, ax_a = plt.subplots(figsize=(9, 8))
ax_a.axis('off')

top10_focal = top50_df.nlargest(10, 'ko_per_mb_primary')['genus_lower'].tolist()
top10_partners_df = top50_partners[top50_partners['focal'].isin(top10_focal)].copy()
# Take top 5 partners per focal by phi
top10_partners_df = (top10_partners_df
    .sort_values('phi', ascending=False)
    .groupby('focal').head(5)
    .reset_index(drop=True))

partner_ko = top10_partners_df.set_index('partner')['ko_per_mb_primary'].to_dict()
partner_phylum = top10_partners_df.set_index('partner')['phylum'].to_dict()
all_partners_in_fig = sorted(top10_partners_df['partner'].unique())

# Layout: focal on left (x=0), partners on right (x=1)
n_f = len(top10_focal)
n_p = len(all_partners_in_fig)
focal_y  = {g: 1.0 - i / (n_f - 1) for i, g in enumerate(top10_focal)} if n_f > 1 else {top10_focal[0]: 0.5}
partner_y = {g: 1.0 - i / max(n_p - 1, 1) for i, g in enumerate(all_partners_in_fig)}

# KO-density colormap for partners
ko_vals = np.array([partner_ko.get(g, traits[traits.genus_lower==g]['ko_per_mb_primary'].values[0]
                                    if len(traits[traits.genus_lower==g]) else 8.0)
                     for g in all_partners_in_fig])
norm_ko = Normalize(vmin=ko_vals.min(), vmax=ko_vals.max())
cmap_ko = plt.cm.YlOrRd

# Draw edges
phi_vals = top10_partners_df['phi'].values
phi_norm = Normalize(vmin=phi_vals.min(), vmax=phi_vals.max())
for _, row in top10_partners_df.iterrows():
    fx, fy = 0.15, focal_y.get(row['focal'], 0.5)
    px, py = 0.85, partner_y.get(row['partner'], 0.5)
    lw = 0.5 + 3.0 * phi_norm(row['phi'])
    ax_a.plot([fx, px], [fy, py], color='#cccccc', lw=lw, alpha=0.6, zorder=1)

# Draw focal nodes
for g in top10_focal:
    fy = focal_y[g]
    ko = top50_df.set_index('genus_lower').loc[g, 'ko_per_mb_primary']
    phy = top50_df.set_index('genus_lower').loc[g, 'phylum']
    ax_a.scatter(0.15, fy, s=300, c=[phy_color(phy)], zorder=3, edgecolors='k', linewidths=0.7)
    ax_a.text(0.13, fy, f"{g}\n({ko:.1f})", ha='right', va='center', fontsize=7.5,
              fontweight='bold')

# Draw partner nodes
for g in all_partners_in_fig:
    py = partner_y[g]
    ko_g = partner_ko.get(g, np.nan)
    clr = cmap_ko(norm_ko(ko_g)) if not np.isnan(ko_g) else '#aaaaaa'
    ax_a.scatter(0.85, py, s=200, c=[clr], zorder=3, edgecolors='k', linewidths=0.5)
    ax_a.text(0.87, py, g, ha='left', va='center', fontsize=7.5)

# Legend: phylum colors (focal)
legend_phy = sorted(top10_partners_df['phylum'].dropna().unique()) + \
             sorted(top50_df.nlargest(10,'ko_per_mb_primary')['phylum'].unique())
legend_phy = list(dict.fromkeys(legend_phy))
patches = [mpatches.Patch(color=phy_color(p), label=p) for p in legend_phy]
ax_a.legend(handles=patches, title='Focal phylum', loc='lower left', fontsize=7.5,
            title_fontsize=8.5, framealpha=0.9)

# Colorbar: partner KO density
sm = ScalarMappable(cmap=cmap_ko, norm=norm_ko)
sm.set_array([])
cbar = fig_a.colorbar(sm, ax=ax_a, shrink=0.35, aspect=15, pad=0.01)
cbar.set_label('Partner ko/Mb', fontsize=8.5)

ax_a.set_xlim(-0.05, 1.15)
ax_a.set_title('Fig A — Bipartite co-occurrence network\n(top-10 metal-gene-rich focal genera, top-5 partners by φ, soil stratum)',
               fontsize=10, pad=10)
ax_a.text(0.15, -0.03, 'Focal genera\n(ko/Mb)', ha='center', va='top', fontsize=8, style='italic',
          transform=ax_a.transData)
ax_a.text(0.85, -0.03, 'Co-occurring\npartners', ha='center', va='top', fontsize=8, style='italic',
          transform=ax_a.transData)
fig_a.tight_layout()
fig_a.savefig(f"{RES}/partner_bipartite_network.pdf", dpi=150, bbox_inches='tight')
plt.close(fig_a)
print("  Saved partner_bipartite_network.pdf")

# ── Figure B: Scatter — focal ko_per_mb vs mean partner ko_per_mb ──
fig_b, ax_b = plt.subplots(figsize=(7, 5.5))
for grp, df_g, marker in [('Top-50', top50_summary, 'o'), ('Control-50', ctrl50_summary, 's')]:
    for phy in df_g['phylum'].unique():
        sub = df_g[df_g['phylum'] == phy]
        ax_b.scatter(sub['ko_per_mb_primary'], sub['mean_partner_ko'],
                     c=[phy_color(phy)]*len(sub), s=55, alpha=0.75, marker=marker,
                     label=f'{phy} ({grp})' if grp == 'Top-50' else None,
                     edgecolors='k', linewidths=0.4, zorder=3)

# Overlay regression line on all-100
from scipy.stats import linregress
x_all = all_summary['ko_per_mb_primary'].dropna()
y_all = all_summary['mean_partner_ko'].dropna()
common = all_summary.dropna(subset=['ko_per_mb_primary','mean_partner_ko'])
slope, intercept, r, p_lr, _ = linregress(common['ko_per_mb_primary'], common['mean_partner_ko'])
xr = np.linspace(common['ko_per_mb_primary'].min(), common['ko_per_mb_primary'].max(), 100)
ax_b.plot(xr, intercept + slope * xr, 'k--', lw=1.5, label=f'OLS (r={r:.3f}, p={p_lr:.2e})', zorder=4)

# Separate markers for top-50 vs control-50 in legend
ax_b.scatter([], [], c='grey', s=55, marker='o', label='Top-50 focal', edgecolors='k', linewidths=0.4)
ax_b.scatter([], [], c='grey', s=55, marker='s', label='Control-50', edgecolors='k', linewidths=0.4)

ax_b.set_xlabel('Focal ko/Mb (metal-gene density)', fontsize=11)
ax_b.set_ylabel('Mean partner ko/Mb', fontsize=11)
ax_b.set_title('Fig B — Focal metal-gene density vs mean partner density\n(soil stratum)', fontsize=10)
handles, labels = ax_b.get_legend_handles_labels()
# Keep only phyla + regression + markers
ax_b.legend(handles, labels, fontsize=7.5, ncol=2, loc='upper right')
ax_b.spines[['top', 'right']].set_visible(False)
fig_b.tight_layout()
fig_b.savefig(f"{RES}/partner_focal_vs_partner_scatter.pdf", dpi=150, bbox_inches='tight')
plt.close(fig_b)
print("  Saved partner_focal_vs_partner_scatter.pdf")

# ── Figure C: Boxplot — per-partner ko/Mb for top-50 vs control-50 ──
fig_c, ax_c = plt.subplots(figsize=(6, 5))
data_top  = top50_partners['ko_per_mb_primary'].dropna().values
data_ctrl = ctrl50_partners['ko_per_mb_primary'].dropna().values
bp = ax_c.boxplot([data_top, data_ctrl], labels=['Top-50 focal', 'Control-50'],
                  patch_artist=True, notch=True, bootstrap=1000,
                  medianprops=dict(color='black', lw=2),
                  flierprops=dict(marker='.', markersize=2, alpha=0.3))
bp['boxes'][0].set_facecolor('#2a78d680')
bp['boxes'][1].set_facecolor('#aaaaaa80')

# Annotate p-value
top50_vec  = top50_partners['ko_per_mb_primary'].dropna().values.astype(float)
ctrl50_vec = ctrl50_partners['ko_per_mb_primary'].dropna().values.astype(float)
_, pv = mannwhitneyu(top50_vec, ctrl50_vec, alternative='two-sided')
pstr = f"p = {pv:.2e}" if pv >= 1e-10 else f"p < 10⁻¹⁰"
ax_c.annotate(f"MWU {pstr}", xy=(1.5, max(np.percentile(data_top,95), np.percentile(data_ctrl,95)) + 0.5),
              ha='center', fontsize=10)

ax_c.set_ylabel('Partner ko/Mb (metal-gene density)', fontsize=11)
ax_c.set_title('Fig C — Partner metal-gene density\nvs focal group (soil stratum)', fontsize=10)
ax_c.spines[['top', 'right']].set_visible(False)
fig_c.tight_layout()
fig_c.savefig(f"{RES}/partner_ko_density_boxplot.pdf", dpi=150, bbox_inches='tight')
plt.close(fig_c)
print("  Saved partner_ko_density_boxplot.pdf")

# ─────────────────────────────────────────────────────────────────
# Step 7: Write report
# ─────────────────────────────────────────────────────────────────
print("\n--- Writing report ---")

def fmt_p(p):
    if p < 0.001: return f"{p:.2e}***"
    elif p < 0.01: return f"{p:.3f}**"
    elif p < 0.05: return f"{p:.3f}*"
    return f"{p:.3f}"

# Determine direction
top50_mean_pk = top50_summary.mean_partner_ko.mean()
ctrl50_mean_pk = ctrl50_summary.mean_partner_ko.mean()
direction = "higher" if top50_mean_pk > ctrl50_mean_pk else "lower"

top50_pct_tq   = top50_summary.pct_top_quartile.mean()*100
ctrl50_pct_tq  = ctrl50_summary.pct_top_quartile.mean()*100

top50_top_phy   = top50_partners['phylum'].value_counts().index[0]
top50_top_phy_n = top50_partners['phylum'].value_counts().iloc[0]
top50_total_p   = top50_partners['phylum'].notna().sum()

# Top 5 partners (by phi) across all top-50 focal genera
top5_global = (top50_partners.groupby('partner').agg(
    n_focal=('focal', 'nunique'),
    mean_phi=('phi', 'mean'),
    ko_per_mb=('ko_per_mb_primary', 'mean'),
    phylum=('phylum', 'first')
).reset_index().sort_values('mean_phi', ascending=False).head(10))

lines = [
    "# Partner Characterisation Report",
    "",
    "*Generated by `scripts/partner_characterisation.py`*",
    "",
    "---",
    "",
    "## Methods",
    "",
    "**Stratum:** Soil only (soil, agricultural, farm, paddy, field, forest, shrub, peatland, desert); ",
    f"{G:,} genera × {S:,} samples (matched to main PGLS analysis where soil signal was strongest: β=210.5, p=8.2×10⁻⁴¹).",
    "",
    f"**Focal genera:** Top 50 by `ko_per_mb_primary` from the {len(soil_traits):,} soil-present genera in the PGLS table.",
    "",
    f"**Control genera:** 50 genera with `ko_per_mb_primary` within ±0.5 SD of the median ({median_ko:.2f}), "
    f"phylum-matched to the top-50 distribution where possible.",
    "",
    f"**Co-occurrence filter:** Hypergeometric FDR < 5% (Veech 2013). Network density: "
    f"{sig_pos_mask.sum()*100/N_PAIRS:.1f}% sig+ pairs (>20% → applied stricter filter). "
    f"Kept partners with φ > {PHI_THRESH} (strong association); "
    f"fell back to top-{TOP_N_FALLBACK} partners by φ if fewer than 5 passed the threshold.",
    "",
    f"**φ distribution in sig+ pairs:** median = {np.median(phi_sig):.4f}, "
    f"90th percentile = {np.percentile(phi_sig,90):.4f}, "
    f">0.3: {(phi_sig>0.3).sum():,} pairs ({(phi_sig>0.3).sum()*100/len(phi_sig):.2f}% of sig+).",
    "",
    "---",
    "",
    "## Results",
    "",
    "### Step 1–2: Focal and control genera",
    "",
    "| Group | n | Mean ko/Mb | Median ko/Mb | Phylum distribution |",
    "|-------|---|-----------|-------------|---------------------|",
    f"| Top-50 | {len(top50_set)} | {top50_df.ko_per_mb_primary.mean():.2f} | "
    f"{top50_df.ko_per_mb_primary.median():.2f} | "
    f"{'; '.join(f'{p}:{n}' for p,n in top50_df.phylum.value_counts().items())} |",
    f"| Control-50 | {len(ctrl50_set)} | {ctrl50_df.ko_per_mb_primary.mean():.2f} | "
    f"{ctrl50_df.ko_per_mb_primary.median():.2f} | "
    f"{'; '.join(f'{p}:{n}' for p,n in ctrl50_df.phylum.value_counts().items())} |",
    "",
    "### Step 3–4: Partner characterisation",
    "",
    "| Metric | Top-50 focal | Control-50 |",
    "|--------|-------------|------------|",
    f"| Total unique partners | {top50_partners.partner.nunique():,} | {ctrl50_partners.partner.nunique():,} |",
    f"| Mean partner ko/Mb (per focal genus) | {top50_mean_pk:.3f} ± {top50_summary.mean_partner_ko.std():.3f} | "
    f"{ctrl50_mean_pk:.3f} ± {ctrl50_summary.mean_partner_ko.std():.3f} |",
    f"| Mean partner B_std | {top50_summary.mean_partner_B.mean():.3f} | "
    f"{ctrl50_summary.mean_partner_B.mean():.3f} |",
    f"| % partners in top quartile (ko/Mb) | {top50_pct_tq:.1f}% | {ctrl50_pct_tq:.1f}% |",
    f"| Dominant partner phylum | {top50_partners.phylum.value_counts().index[0]} "
    f"({top50_partners.phylum.value_counts().iloc[0]/top50_total_p*100:.1f}%) | "
    f"{ctrl50_partners.phylum.value_counts().index[0]} "
    f"({ctrl50_partners.phylum.value_counts().iloc[0]/ctrl50_partners.phylum.notna().sum()*100:.1f}%) |",
    "",
    "**Top 10 most-shared partners of top-50 focal genera (by mean φ):**",
    "",
    "| Partner | n focal | Mean φ | ko/Mb | Phylum |",
    "|---------|---------|--------|-------|--------|",
]
for _, r in top5_global.iterrows():
    lines.append(f"| {r['partner']} | {int(r['n_focal'])} | {r['mean_phi']:.4f} | "
                 f"{r['ko_per_mb']:.2f} | {r['phylum']} |")

lines += [
    "",
    "### Step 5: Statistical tests",
    "",
    "| Test | Statistic | p-value |",
    "|------|-----------|---------|",
    f"| Mann-Whitney U: partner ko/Mb (top-50 vs control-50) | U = {stat_ko:.0f} | {fmt_p(p_ko)} |",
    f"| Mann-Whitney U: % top-quartile partners | U = {stat_tq:.0f} | {fmt_p(p_tq)} |",
    f"| Chi-square: partner phylum distribution | χ² = {chi2_stat:.2f} | {fmt_p(p_chi2)} |",
    f"| Spearman: focal ko/Mb ~ mean partner ko/Mb (top-50) | ρ = {rho_top:.3f} | {fmt_p(p_rho_top)} |",
    f"| Spearman: focal ko/Mb ~ mean partner ko/Mb (all 100) | ρ = {rho_all:.3f} | {fmt_p(p_rho_all)} |",
    "",
    "---",
    "",
    "## Interpretation",
    "",
]

# Interpret direction of partner KO density
if direction == "higher":
    guild_conclusion = (
        f"Partners of metal-gene-rich genera have systematically {direction} mean metal-gene density "
        f"({top50_mean_pk:.3f} vs {ctrl50_mean_pk:.3f} ko/Mb; MWU p={p_ko:.2e}), "
        f"and a higher proportion are themselves top-quartile specialists "
        f"({top50_pct_tq:.1f}% vs {ctrl50_pct_tq:.1f}%). "
        "This is consistent with a **shared metal-tolerance guild**: genera that invest heavily in "
        "metal-resistance machinery preferentially co-occur with similarly adapted neighbours. "
        "However, the correlation between focal KO density and mean partner KO density within the top-50 "
        f"(ρ = {rho_top:.3f}, p = {p_rho_top:.2e}) is "
        + ("moderate, suggesting co-occurrence is not strictly assortative by investment level — "
           "some high-KO focal genera still partner with lower-KO genera."
           if abs(rho_top) < 0.4 else
           "strong, suggesting near-assortative co-occurrence by metal-gene investment level.")
    )
else:
    guild_conclusion = (
        f"Despite their elevated metal-gene density, the focal genera have {direction} mean partner "
        f"ko/Mb ({top50_mean_pk:.3f}) than control genera ({ctrl50_mean_pk:.3f}; MWU p={p_ko:.2e}). "
        "This argues against a tight metal-tolerance guild and instead suggests that metal-gene-rich genera "
        "are embedded in **broadly adapted communities** rather than co-localising exclusively with other specialists."
    )

dominant_phylum = top50_partners['phylum'].value_counts().index[0]
phylum_share    = top50_partners['phylum'].value_counts().iloc[0] / top50_total_p * 100

lines += [
    f"{guild_conclusion}",
    "",
    f"Partner phyla show a strong {dominant_phylum} bias among top-50 focal partners "
    f"({phylum_share:.1f}% of partner instances), which is also the dominant phylum in the trait table "
    f"overall ({traits.phylum.value_counts().index[0]}: {traits.phylum.value_counts().iloc[0]/len(traits)*100:.0f}% of genera). "
    f"Chi-square test on the phylum contingency table (top-50 vs control partners) gives "
    f"χ² = {chi2_stat:.2f}, p = {p_chi2:.2e}, indicating that partner phylum composition differs "
    "significantly between the two focal groups.",
    "",
    "The soil stratum — used here because it showed the strongest PGLS effect on co-occurrence "
    "(sig_pos_partners β = 210.5, t = 13.8, p = 8.2×10⁻⁴¹, λ = 0.57) — likely captures "
    "genuine soil community assembly rather than the near-complete co-occurrence patterns seen "
    "in the 'all' and 'env' strata (38–42% sig+ pairs across all genera). Nevertheless, the soil "
    "co-occurrence network remained dense enough that betweenness and clustering coefficients "
    "are degenerate; co-occurrence count and phi-degree remain the primary informative metrics.",
    "",
    "---",
    "",
    "## Figures",
    "",
    "- **Figure A** (`partner_bipartite_network.pdf`): Bipartite co-occurrence network for top-10 focal genera × top-5 partners by φ. Focal node colour = phylum. Partner node colour = ko/Mb (YlOrRd scale). Edge width ∝ φ.",
    "- **Figure B** (`partner_focal_vs_partner_scatter.pdf`): Focal ko/Mb vs mean partner ko/Mb for all 100 genera. Points coloured by phylum; OLS regression overlaid.",
    f"- **Figure C** (`partner_ko_density_boxplot.pdf`): Partner ko/Mb distribution for top-50 vs control-50 focal groups. MWU p = {fmt_p(p_ko)}.",
]

with open(f"{RES}/partner_characterisation_report.md", 'w') as f:
    f.write('\n'.join(lines))

print("  Saved partner_characterisation_report.md")
print("\n=== Partner characterisation complete ===")
