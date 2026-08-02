#!/usr/bin/env python3
"""
Scatter: genome-level Fritz & Purvis D (x) vs genus-level Pagel's lambda (y)
275 curated metal KOs; 13 double-signal HGT candidates annotated.
Output: data/two_scale_phylo_D_vs_lambda.pdf  (7 x 6 in, vector)
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from adjustText import adjust_text

# ── Validated palette (light mode, --pairs all, all checks pass) ─────────────
# Slot 6 red / slot 1 blue / slot 2 aqua / slot 5 violet / slot 8 orange
# Aqua contrast WARN (2.74 on light surface) → relief via direct labels on 13 genes
SURFACE    = "#fcfcfb"
INK_PRI    = "#0b0b0b"
INK_SEC    = "#52514e"
INK_MUTED  = "#898781"
GRIDLINE   = "#e1e0d9"
AXIS_COLOR = "#c3c2b7"

COLORS = {
    "Resistance/Detoxification":  "#e34948",  # slot 6 red
    "Transport/Homeostasis":      "#2a78d6",  # slot 1 blue
    "Metal-dependent Metabolism": "#1baf7a",  # slot 2 aqua
    "Sensing/Regulation":         "#eb6834",  # slot 8 orange
    "Cofactor Biosynthesis":      "#4a3aa7",  # slot 5 violet
    "Unknown":                    AXIS_COLOR, # recessive muted (not a categorical slot)
}

LEGEND_LABELS = {
    "Resistance/Detoxification":  "Resistance / Detox.",
    "Transport/Homeostasis":      "Transport / Homeostasis",
    "Metal-dependent Metabolism": "Metal-dep. Metabolism",
    "Sensing/Regulation":         "Sensing / Regulation",
    "Cofactor Biosynthesis":      "Cofactor Biosynthesis",
    "Unknown":                    "Unknown",
}

LEGEND_ORDER = list(COLORS.keys())

DOUBLE_SIGNAL = {
    "nrsD", "merE", "merD", "gesB", "aoxB", "gesA",
    "shp", "iucD", "golS", "doxDA", "norB", "nicC", "nikB",
}

# ── Load & merge ─────────────────────────────────────────────────────────────
genome = pd.read_csv("data/fritz_purvis_D_genome.csv")
genus  = pd.read_csv("data/phylo_d_all_ko.csv")
df = genome.merge(genus, on="ko_id", suffixes=("_d", "_l"))
df["subcategory"]   = df["subcategory_d"]
df["gene_name"]     = df["gene_name_d"]
df["is_highlight"]  = df["gene_name"].isin(DOUBLE_SIGNAL)

# ── Figure & axes ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6), facecolor=SURFACE)
ax.set_facecolor(SURFACE)

for spine in ax.spines.values():
    spine.set_color(AXIS_COLOR)
    spine.set_linewidth(0.75)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# ── Background KOs (non-highlighted) ─────────────────────────────────────────
for subcat in LEGEND_ORDER:
    mask = (df["subcategory"] == subcat) & ~df["is_highlight"]
    if mask.sum() == 0:
        continue
    alpha = 0.30 if subcat == "Unknown" else 0.68
    ax.scatter(
        df.loc[mask, "D"],
        df.loc[mask, "lambda"],
        c=COLORS[subcat],
        s=28,
        alpha=alpha,
        edgecolors=SURFACE,
        linewidths=0.6,
        zorder=2,
        rasterized=True,
    )

# ── Highlighted 13 double-signal genes ──────────────────────────────────────
hl = df[df["is_highlight"]].copy()
for subcat in LEGEND_ORDER:
    mask = hl["subcategory"] == subcat
    if mask.sum() == 0:
        continue
    ax.scatter(
        hl.loc[mask, "D"],
        hl.loc[mask, "lambda"],
        c=COLORS[subcat],
        s=70,
        alpha=0.95,
        edgecolors=INK_SEC,
        linewidths=0.8,
        zorder=4,
    )

# ── Reference lines ───────────────────────────────────────────────────────────
ax.axvline(0.2, color=INK_MUTED, lw=0.85, ls="--", zorder=1, label="_nolegend_")
ax.axhline(0.3, color=INK_MUTED, lw=0.85, ls="--", zorder=1, label="_nolegend_")

# ── Labels for 13 highlighted genes ──────────────────────────────────────────
texts = []
for _, row in hl.iterrows():
    t = ax.text(
        row["D"],
        row["lambda"],
        row["gene_name"],
        fontsize=6.5,
        color=INK_PRI,
        ha="center",
        va="bottom",
        zorder=5,
    )
    texts.append(t)

adjust_text(
    texts,
    x=hl["D"].values,
    y=hl["lambda"].values,
    ax=ax,
    expand=(1.5, 1.8),
    arrowprops=dict(arrowstyle="-", color=INK_MUTED, lw=0.55),
    only_move={"text": "xy"},
)

# ── Spearman annotation ───────────────────────────────────────────────────────
ax.text(
    0.975, 0.035,
    "Spearman ρ = −0.041,  p = 0.49",
    transform=ax.transAxes,
    ha="right", va="bottom",
    fontsize=8, color=INK_SEC,
    style="italic",
)

# ── Legend ────────────────────────────────────────────────────────────────────
handles = [
    mpatches.Patch(
        facecolor=COLORS[s],
        edgecolor=SURFACE,
        linewidth=0.5,
        label=LEGEND_LABELS[s],
        alpha=0.85 if s != "Unknown" else 0.50,
    )
    for s in LEGEND_ORDER
]
leg = ax.legend(
    handles=handles,
    loc="upper right",
    frameon=True,
    framealpha=0.93,
    facecolor=SURFACE,
    edgecolor=GRIDLINE,
    fontsize=7.5,
    title="Subcategory",
    title_fontsize=8.0,
    borderpad=0.75,
    handlelength=1.1,
    handleheight=1.0,
    labelspacing=0.45,
)
leg.get_title().set_color(INK_SEC)
for text in leg.get_texts():
    text.set_color(INK_SEC)

# ── Axis labels & ticks ───────────────────────────────────────────────────────
ax.set_xlabel(
    "Fritz & Purvis D  (genome level, binary trait)",
    fontsize=10, color=INK_PRI, labelpad=9,
)
ax.set_ylabel(
    "Pagel's λ  (genus level, presence fraction)",
    fontsize=10, color=INK_PRI, labelpad=9,
)

ax.tick_params(axis="both", colors=INK_MUTED, labelsize=8, length=3, width=0.6)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_color(INK_MUTED)

ax.set_xlim(-0.05, 1.02)
ax.set_ylim(-0.04, 1.06)
ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

fig.tight_layout(pad=1.3)
out = "data/two_scale_phylo_D_vs_lambda.pdf"
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=SURFACE)
print(f"Saved: {out}")
