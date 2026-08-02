"""
Presentation-quality figure: top 20 CatBoost KOs overlaid onto KEGG pathway modules.

Row labels live inside ax_mod (clip_on=False) so they extend left into the margin
without overlapping the colored strip or the heatmap.

Saves: figures/kegg_pathway_overlay_slide.pdf
       figures/kegg_pathway_overlay_slide.png
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm

# ── constants ────────────────────────────────────────────────────────────────
VALIDATION_KOS = {"K01772", "K09883", "K07796", "K19575", "K09823"}

MODULE_MAP = {
    "K09883": "Porphyrin / Cobalamin",
    "K00595": "Porphyrin / Cobalamin",
    "K01772": "Porphyrin / Cobalamin",
    "K22552": "Porphyrin / Cobalamin",
    "K07644": "Cu / Ag efflux (cus)",
    "K07796": "Cu / Ag efflux (cus)",
    "K07665": "Cu / Ag efflux (cus)",
    "K02011": "Metal transport",
    "K02012": "Metal transport",
    "K07243": "Metal transport",
    "K02007": "Metal transport",
    "K05802": "Metal transport",
    "K09823": "Metal transport",
    "K19575": "Sensing / stress / other",
    "K04080": "Sensing / stress / other",
    "K00108": "Sensing / stress / other",
    "K05836": "Sensing / stress / other",
    "K03543": "Sensing / stress / other",
    "K01935": "Sensing / stress / other",
    "K17229": "Sensing / stress / other",
}
MODULE_ORDER = [
    "Porphyrin / Cobalamin",
    "Cu / Ag efflux (cus)",
    "Metal transport",
    "Sensing / stress / other",
]
MODULE_COLORS = {
    "Porphyrin / Cobalamin":   "#B85450",
    "Cu / Ag efflux (cus)":   "#C08030",
    "Metal transport":          "#4878A6",
    "Sensing / stress / other": "#5A9B5A",
}

COL_ORDER = [
    "CSU_As","CSU_Cd","CSU_Cr","CSU_Cu","CSU_Hg","CSU_Pb",
    "GEOROC_Co","GEOROC_Cr","GEOROC_Cu","GEOROC_Ni","GEOROC_Pb","GEOROC_Zn",
    "Soil_pH","Temperature","Env_PC1",
]
# Mobile = CSU mobility-fractionated; BR = bedrock (GEOROC)
COL_LABELS = [
    "Mobile As","Mobile Cd","Mobile Cr","Mobile Cu","Mobile Hg","Mobile Pb",
    "BR Co","BR Cr","BR Cu","BR Ni","BR Pb","BR Zn",
    "Soil pH","Temp","Env PC1",
]
COL_GROUPS = [
    ("Mobile metals (CSU)",     0,  5),
    ("Bedrock metals (GEOROC)",  6, 11),
    ("Climate / soil",          12, 14),
]

# ── load data ────────────────────────────────────────────────────────────────
pri = pd.read_csv("data/ko_prioritization_scores.csv")
cb  = pd.read_csv("data/catboost_single_ko_ranking.csv")

top20 = pri.nlargest(20, "composite").copy()
top20["module"]      = top20["ko"].map(MODULE_MAP).fillna("Sensing / stress / other")
top20["module_rank"] = top20["module"].map({m: i for i, m in enumerate(MODULE_ORDER)})
top20 = top20.sort_values(["module_rank","composite"], ascending=[True,False]).reset_index(drop=True)

def make_label(row):
    gn = str(row["gene_name"]) if pd.notna(row["gene_name"]) else row["ko"]
    star = "  ★" if row["ko"] in VALIDATION_KOS else ""
    return f"{gn}  ({row['ko']}){star}"

top20["label"] = top20.apply(make_label, axis=1)

rho = (
    cb[cb["ko"].isin(top20["ko"])]
    .pivot_table(index="ko", columns="env_response", values="avg_rho", aggfunc="mean")
    .reindex(index=top20["ko"], columns=COL_ORDER)
)

n_rows = len(top20)
n_cols = len(COL_ORDER)

# ── figure layout ────────────────────────────────────────────────────────────
# left=0.25 gives 3.875" of left margin; row labels (≈1.8") extend into it.
# [ax_mod (strip + labels) | ax_heat | ax_nsig | gap | ax_cb]
fig = plt.figure(figsize=(15.5, 7.5), facecolor="white")

gs = gridspec.GridSpec(
    1, 5,
    left=0.25, right=0.878,
    bottom=0.22, top=0.87,
    width_ratios=[0.45, 9.0, 0.75, 0.15, 0.30],
    wspace=0.035,
)
ax_mod  = fig.add_subplot(gs[0, 0])
ax_heat = fig.add_subplot(gs[0, 1])
ax_nsig = fig.add_subplot(gs[0, 2])
ax_cb   = fig.add_subplot(gs[0, 4])

# ── heatmap ──────────────────────────────────────────────────────────────────
vabs = 0.27
norm = TwoSlopeNorm(vmin=-vabs, vcenter=0, vmax=vabs)
im = ax_heat.imshow(
    rho.values, cmap=plt.cm.RdBu_r, norm=norm,
    aspect="auto", interpolation="nearest",
)

# Minor gridlines
ax_heat.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
ax_heat.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
ax_heat.grid(which="minor", color="#d8d8d8", linewidth=0.5)
ax_heat.tick_params(which="minor", bottom=False, left=False)

# Vertical column-group separators
for _, first, _ in COL_GROUPS[1:]:
    ax_heat.axvline(first - 0.5, color="#888888", linewidth=1.0, zorder=5)

# Horizontal module-group separators
boundaries = top20.groupby("module_rank").apply(lambda df: df.index[-1]).tolist()
for b in boundaries[:-1]:
    ax_heat.axhline(b + 0.5, color="#666666", linewidth=1.2, zorder=5)

# X-axis
ax_heat.set_xticks(range(n_cols))
ax_heat.set_xticklabels(COL_LABELS, rotation=45, ha="right",
                        fontsize=9.5, color="#333333")
ax_heat.tick_params(axis="x", length=0)

# No y-tick labels — they live in ax_mod (below)
ax_heat.set_yticks([])
ax_heat.yaxis.set_visible(False)

# Column group labels above heatmap (transAxes, y > 1)
for grp_label, first, last in COL_GROUPS:
    x_mid = (first + last + 1) / 2.0 / n_cols
    x_l   = first / n_cols + 0.01
    x_r   = (last + 1) / n_cols - 0.01
    ax_heat.text(x_mid, 1.032, grp_label,
                 transform=ax_heat.transAxes,
                 ha="center", va="bottom", fontsize=9.5, color="#555555")
    ax_heat.plot([x_l, x_r], [1.015, 1.015],
                 transform=ax_heat.transAxes, clip_on=False,
                 color="#aaaaaa", linewidth=0.9)

ax_heat.spines[["top","left","bottom","right"]].set_visible(False)

# ── module color strip + row labels (ax_mod) ─────────────────────────────────
# xlim = (0, 1); colored strip = x 0.72–1.0; labels at x=0.68 (ha='right',
# clip_on=False) → they extend leftward into the figure left margin.
ax_mod.set_xlim(0, 1)
ax_mod.set_ylim(-0.5, n_rows - 0.5)
ax_mod.invert_yaxis()
ax_mod.axis("off")

# Colored module blocks (right 28% of ax_mod)
strip_x0 = 0.74
for rank, grp_df in top20.groupby("module_rank"):
    start = grp_df.index[0]
    end   = grp_df.index[-1]
    n_grp = end - start + 1
    ax_mod.add_patch(plt.Rectangle(
        (strip_x0, start - 0.42), 1.0 - strip_x0, n_grp - 0.17,
        color=MODULE_COLORS[MODULE_ORDER[rank]], zorder=2, clip_on=False,
    ))

# White separators between module groups in the strip
for b in boundaries[:-1]:
    ax_mod.plot([strip_x0, 1.0], [b + 0.5, b + 0.5],
                color="white", linewidth=2.5, zorder=3, clip_on=False)

# Row labels (extend left into margin via clip_on=False)
for i, row in top20.iterrows():
    color = MODULE_COLORS[row["module"]]
    fw    = "bold" if row["ko"] in VALIDATION_KOS else "normal"
    ax_mod.text(
        strip_x0 - 0.04, i, top20.at[i, "label"],
        ha="right", va="center",
        fontsize=9.5, color=color, fontweight=fw,
        clip_on=False,
    )

# ── n_sig bar chart ──────────────────────────────────────────────────────────
ax_nsig.set_xlim(0, 15)
ax_nsig.set_ylim(-0.5, n_rows - 0.5)
ax_nsig.invert_yaxis()

for i, row in top20.iterrows():
    n = int(row["n_significant_responses"])
    ax_nsig.barh(i, n, height=0.65, left=0,
                 color=MODULE_COLORS[row["module"]], alpha=0.75, edgecolor="none")
    if n >= 2:
        ax_nsig.text(n + 0.3, i, str(n), va="center", ha="left",
                     fontsize=8.5, color="#444444")

for b in boundaries[:-1]:
    ax_nsig.axhline(b + 0.5, color="#666666", linewidth=1.2, zorder=5)

ax_nsig.set_xlabel("n sig.\nresponses", fontsize=9, labelpad=4)
ax_nsig.set_xticks([0, 5, 10, 15])
ax_nsig.tick_params(labelsize=8, left=False, labelleft=False, length=3)
ax_nsig.spines[["top","right","left"]].set_visible(False)
ax_nsig.spines["bottom"].set_linewidth(0.7)
ax_nsig.spines["bottom"].set_color("#888888")

# ── colorbar ─────────────────────────────────────────────────────────────────
cb_obj = plt.colorbar(im, cax=ax_cb, orientation="vertical")
cb_obj.set_label("Spearman ρ  (LOPO)", fontsize=9, labelpad=6)
cb_obj.ax.tick_params(labelsize=8.5)
cb_obj.set_ticks([-0.25, -0.15, 0, 0.15, 0.25])
cb_obj.ax.axhline(0, color="white", linewidth=1.2, zorder=10)

# ── legend (inside figure, bottom centre) ────────────────────────────────────
legend_patches = [
    mpatches.Patch(color=MODULE_COLORS[m], label=m) for m in MODULE_ORDER
]
legend_patches.append(
    mpatches.Patch(facecolor="none", edgecolor="none",
                   label="★ = prioritized for validation")
)
fig.legend(
    handles=legend_patches,
    loc="lower center",
    ncol=3,
    fontsize=9,
    frameon=False,
    bbox_to_anchor=(0.52, 0.005),
    handlelength=1.0,
    handletextpad=0.5,
    columnspacing=1.8,
)

# ── title / subtitle ─────────────────────────────────────────────────────────
fig.text(0.52, 0.965,
         "Top 20 metal-gene KOs: two coherent KEGG pathway modules",
         ha="center", va="top",
         fontsize=14, fontweight="bold", color="#1a1a1a")
fig.text(0.52, 0.924,
         "Cross-phylum LOPO Spearman ρ  ·  single-KO CatBoost  ·  15 environmental responses",
         ha="center", va="top",
         fontsize=10.5, color="#555555")

# ── save (no bbox_inches="tight" — frame is exactly 15.5×7.5") ───────────────
out = "figures/kegg_pathway_overlay_slide"
plt.savefig(out + ".pdf", dpi=150, facecolor="white")
plt.savefig(out + ".png", dpi=150, facecolor="white")
print(f"Saved {out}.pdf and .png")
plt.close()
