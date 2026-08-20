"""Compare lab fitness effects of core vs. accessory KOs in ENIGMA soil isolates vs. E. coli (Keio).

Core/accessory classification: n_organisms quartiles (empirical prevalence in the fitness DB).
  Core        n_organisms >= 26 (top quartile)
  Intermediate  6-25
  Accessory   n_organisms <= 5 (bottom quartile)

Outputs
-------
data/core_accessory_fitness.csv         per-KO table with both group mean_t + tier
figures/fig_core_accessory_violin.pdf   grouped violin: ENIGMA vs Keio by tier
figures/fig_core_accessory_scatter.pdf  scatter ENIGMA vs Keio, coloured by tier
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"

import sys
from pathlib import Path

ROOT = Path("/home/hmacgregor/BERIL-research-observatory")
PROJ = ROOT / "projects/per_ko_metal_associations"
DATA = PROJ / "data"
FIGS = PROJ / "figures"
FIGS.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "tools"))
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

# ── 1. Load ──────────────────────────────────────────────────────────────────

raw = pd.read_parquet(DATA / "all_ko_fitness_raw.parquet")
summary = pd.read_csv(DATA / "all_ko_fitness_summary.csv")

ENIGMA_SOIL = {o for o in raw[raw["source_db"] == "enigma_fitprivate"]["orgId"].unique()
               if o != "Keio"}
KEIO = {"Keio"}

# ── 2. Per-KO group mean_t ────────────────────────────────────────────────────

enigma_stats = (
    raw[raw["orgId"].isin(ENIGMA_SOIL)]
    .groupby("ko_id")["t_stat"]
    .agg(enigma_mean_t="mean", enigma_min_t="min", enigma_n_obs="count")
    .reset_index()
)

keio_stats = (
    raw[raw["orgId"].isin(KEIO)]
    .groupby("ko_id")["t_stat"]
    .agg(keio_mean_t="mean", keio_min_t="min", keio_n_obs="count")
    .reset_index()
)

# ── 3. Merge with summary ─────────────────────────────────────────────────────

keep_cols = [
    "ko_id", "n_organisms", "category", "gene_name", "is_resistance",
    "is_transport", "is_cofactor", "arc4_survivor", "in_core94",
    "in_arc4_survivors", "in_arc3b_sig",
]
meta = summary[keep_cols].copy()

df = (
    meta
    .merge(enigma_stats, on="ko_id", how="left")
    .merge(keio_stats,   on="ko_id", how="left")
)

# ── 4. Core / accessory classification ───────────────────────────────────────

Q25 = df["n_organisms"].quantile(0.25)   # 5
Q75 = df["n_organisms"].quantile(0.75)   # 26

def tier(n):
    if pd.isna(n):
        return "Unknown"
    if n <= Q25:
        return "Accessory"
    if n >= Q75:
        return "Core"
    return "Intermediate"

df["genome_tier"] = df["n_organisms"].apply(tier)

# Δt for overlapping KOs
df["delta_t"] = df["enigma_mean_t"] - df["keio_mean_t"]

df.to_csv(DATA / "core_accessory_fitness.csv", index=False)
print(f"Saved {DATA / 'core_accessory_fitness.csv'}: {len(df)} KOs")

# ── 5. Summary statistics ─────────────────────────────────────────────────────

TIER_ORDER = ["Core", "Intermediate", "Accessory"]
TIER_COLORS = {
    "Core":         PALETTE[0],
    "Intermediate": PALETTE[2],
    "Accessory":    PALETTE[1],
}

print("\n=== N KOs per tier ===")
print(df["genome_tier"].value_counts()[TIER_ORDER])

both_mask = df["enigma_mean_t"].notna() & df["keio_mean_t"].notna()
overlap = df[both_mask].copy()
print(f"\nKOs with data in BOTH groups: {len(overlap)}")

for t in TIER_ORDER:
    sub = overlap[overlap["genome_tier"] == t]
    if len(sub) < 5:
        continue
    e = sub["enigma_mean_t"].dropna()
    k = sub["keio_mean_t"].dropna()
    d = sub["delta_t"].dropna()
    stat, p = stats.mannwhitneyu(e, k, alternative="two-sided")
    print(f"\n{t} (n={len(sub)}):")
    print(f"  ENIGMA mean_t: {e.mean():.2f} ± {e.std():.2f}")
    print(f"  Keio   mean_t: {k.mean():.2f} ± {k.std():.2f}")
    print(f"  Δt = ENIGMA − Keio: {d.mean():.2f} ± {d.std():.2f}")
    print(f"  Mann-Whitney U = {stat:.0f}, p = {p:.3g}")

# ── 6. Figure 1: Violin — ENIGMA vs Keio, panelled by tier ──────────────────

fig, axes = plt.subplots(1, 3, figsize=(FIGW["full"], ROW_H), sharey=True)

for ax, tier_label in zip(axes, TIER_ORDER):
    sub = df[df["genome_tier"] == tier_label]
    data_e = sub["enigma_mean_t"].dropna().values
    data_k = sub["keio_mean_t"].dropna().values

    c = TIER_COLORS[tier_label]
    positions = [1, 2]
    parts = ax.violinplot(
        [data_e, data_k],
        positions=positions,
        widths=0.6,
        showmedians=False,
        showextrema=False,
    )
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(PALETTE[0] if i == 0 else PALETTE[3])
        pc.set_edgecolor("k")
        pc.set_linewidth(0.5)
        pc.set_alpha(0.7)

    for i, (data, pos) in enumerate([(data_e, 1), (data_k, 2)]):
        q25, med, q75 = np.percentile(data, [25, 50, 75])
        ax.vlines(pos, q25, q75, lw=2, color="k", zorder=3)
        ax.scatter([pos], [med], s=20, color="w", edgecolors="k", lw=0.8, zorder=4)

    ax.axhline(-2, color="gray", lw=0.8, ls="--")
    ax.set_xticks([1, 2])
    ax.set_xticklabels(["ENIGMA\nsoil", "E. coli\n(Keio)"], fontsize=8)
    ax.set_title(f"{tier_label}\n(n={len(sub)})", fontsize=10)
    ax.set_xlabel("")

    ne = len(data_e)
    nk = len(data_k)
    ax.annotate(f"n={ne}", xy=(1, ax.get_ylim()[0]), fontsize=8, color="#808080",
                ha="center", va="bottom")
    ax.annotate(f"n={nk}", xy=(2, ax.get_ylim()[0]), fontsize=8, color="#808080",
                ha="center", va="bottom")

    if ax == axes[0]:
        ax.set_ylabel("Mean t-statistic (metal fitness)", fontsize=9)

handles = [
    mpatches.Patch(facecolor=PALETTE[0], edgecolor="k", lw=0.5, label="ENIGMA soil isolates"),
    mpatches.Patch(facecolor=PALETTE[3], edgecolor="k", lw=0.5, label="E. coli (Keio)"),
]
fig.legend(handles=handles, loc="upper right", fontsize=8, frameon=False)
fig.suptitle("Lab fitness effects by genome tier: ENIGMA soil isolates vs. E. coli", y=1.02)
save(fig, FIGS / "fig_core_accessory_violin")
print("\nSaved fig_core_accessory_violin.pdf")

# ── 7. Figure 2: Scatter ENIGMA vs Keio, coloured by tier ───────────────────

fig, ax = plt.subplots(figsize=(FIGW["2col"], ROW_H))

for t in TIER_ORDER:
    sub = overlap[overlap["genome_tier"] == t]
    ax.scatter(
        sub["keio_mean_t"], sub["enigma_mean_t"],
        color=TIER_COLORS[t], edgecolors="k", linewidths=0.3,
        s=22, alpha=0.75, label=f"{t} (n={len(sub)})", zorder=3
    )

# Label Arc4 survivors in overlap
arc4_sub = overlap[overlap["in_arc4_survivors"] == True]
for _, row in arc4_sub.iterrows():
    ax.annotate(
        row["gene_name"] if pd.notna(row["gene_name"]) else row["ko_id"],
        xy=(row["keio_mean_t"], row["enigma_mean_t"]),
        fontsize=7, color="darkred",
        xytext=(4, 4), textcoords="offset points"
    )

# Hit threshold lines
ax.axhline(-2, color="gray", lw=0.8, ls="--")
ax.axvline(-2, color="gray", lw=0.8, ls="--")
ax.axline((0, 0), slope=1, color="gray", lw=0.6, ls=":")

lim_min = min(overlap["keio_mean_t"].min(), overlap["enigma_mean_t"].min()) - 0.5
lim_max = max(overlap["keio_mean_t"].max(), overlap["enigma_mean_t"].max()) + 0.5
ax.set_xlim(lim_min, lim_max)
ax.set_ylim(lim_min, lim_max)

ax.set_xlabel("E. coli (Keio) mean metal fitness t-stat", fontsize=9)
ax.set_ylabel("ENIGMA soil isolates mean metal fitness t-stat", fontsize=9)
ax.set_title("ENIGMA vs. Keio fitness: core vs. accessory KOs", fontsize=10)

# Quadrant labels
ax.text(0.97, 0.03, "Keio only\nhit", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=7, color="#808080")
ax.text(0.03, 0.97, "ENIGMA only\nhit", transform=ax.transAxes,
        ha="left", va="top", fontsize=7, color="#808080")
ax.text(0.03, 0.03, "Both\nhit", transform=ax.transAxes,
        ha="left", va="bottom", fontsize=7, color="#808080")

ax.legend(fontsize=8, frameon=False, loc="upper left")

# Pearson r
r, p_r = stats.pearsonr(overlap["keio_mean_t"], overlap["enigma_mean_t"])
ax.annotate(f"r = {r:.2f}, n = {len(overlap)}", xy=(0.97, 0.97),
            xycoords="axes fraction", ha="right", va="top", fontsize=8, color="#808080")

save(fig, FIGS / "fig_core_accessory_scatter")
print("Saved fig_core_accessory_scatter.pdf")

# ── 8. Figure 3: Δt by tier (ENIGMA advantage for accessory?) ───────────────

fig, ax = plt.subplots(figsize=(FIGW["1col"], ROW_H))

tier_delta = []
for t in TIER_ORDER:
    sub = overlap[overlap["genome_tier"] == t]["delta_t"].dropna()
    tier_delta.append(sub.values)

parts = ax.violinplot(tier_delta, positions=[1, 2, 3], widths=0.55,
                      showmedians=False, showextrema=False)
for i, (pc, t) in enumerate(zip(parts["bodies"], TIER_ORDER)):
    pc.set_facecolor(TIER_COLORS[t])
    pc.set_edgecolor("k")
    pc.set_linewidth(0.5)
    pc.set_alpha(0.75)

for i, (data, pos) in enumerate(zip(tier_delta, [1, 2, 3])):
    q25, med, q75 = np.percentile(data, [25, 50, 75])
    ax.vlines(pos, q25, q75, lw=2, color="k", zorder=3)
    ax.scatter([pos], [med], s=20, color="w", edgecolors="k", lw=0.8, zorder=4)
    ax.annotate(f"n={len(data)}", xy=(pos, ax.get_ylim()[0]),
                fontsize=8, color="#808080", ha="center", va="bottom")

    stat, p = stats.wilcoxon(data, alternative="two-sided")
    stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
    ax.annotate(stars, xy=(pos, max(data) + 0.2), ha="center", fontsize=8)

ax.axhline(0, color="gray", lw=0.8, ls="--")
ax.set_xticks([1, 2, 3])
ax.set_xticklabels(TIER_ORDER, fontsize=8)
ax.set_xlabel("Genome tier (by n_organisms in fitness DB)", fontsize=9)
ax.set_ylabel("Δt  (ENIGMA − Keio mean t-stat)", fontsize=9)
ax.set_title("ENIGMA fitness advantage by tier\n(negative = ENIGMA more depleted)", fontsize=10)

save(fig, FIGS / "fig_core_accessory_delta_t")
print("Saved fig_core_accessory_delta_t.pdf")

print("\nDone.")
