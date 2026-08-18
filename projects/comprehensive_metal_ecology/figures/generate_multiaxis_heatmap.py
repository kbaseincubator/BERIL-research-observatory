"""Regenerate fig01_multiaxis_heatmap.pdf at compact (single-column) size."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

OUT = Path(__file__).parent

# ── Data (values read from original figure) ─────────────────────────────────
rows = [
    "Resistance",
    "Metal-dep metabolism",
    "Core metabolism",
    "Non-metal cofactor",
    "Metal cofactor\n(curated, 9 KOs)",
    "Metal cofactor\n(expanded, 47 KOs)",
]
cols = [
    "Cross-biome\nniche breadth\n(Levins' B)",
    "Geochemical\nbreadth\n(Env PC1)",
    "Soil niche\nbreadth",
    "Co-occurrence\ndegree",
]

beta = np.array([
    [+0.007, +0.073, +0.004, +4.10],
    [+0.002, +0.056, +0.004, +3.21],
    [-0.006, +0.022, -0.002, -0.92],
    [-0.029, +0.003, +0.001, -2.10],
    [-0.006, +0.018, -0.003, +5.71],
    [-0.011, +0.014, -0.003, +7.87],
])

sig = [
    ["",    "*",  "",   "***"],
    ["",    "†",  "",   "**" ],
    ["",    "",   "",   ""   ],
    ["***", "",   "",   ""   ],
    ["",    "",   "*",  "***"],
    ["*",   "",   "*",  "***"],
]

def fmt_beta(v, col_idx):
    """Format beta value: 3 decimal places for small axes, 2 for degree."""
    if col_idx == 3:          # co-occurrence degree
        return f"{v:+.2f}"
    return f"{v:+.3f}"

# ── Column-normalise to z-scores for colour mapping ──────────────────────────
col_mean = beta.mean(axis=0)
col_std  = beta.std(axis=0, ddof=1)
col_std[col_std == 0] = 1.0
z = (beta - col_mean) / col_std

# ── Figure layout ─────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 6,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

nrows, ncols = len(rows), len(cols)
FIG_W = 3.5   # single-column width (inches)
FIG_H = 2.8

fig = plt.figure(figsize=(FIG_W, FIG_H))

# Allocate axes manually for precise control
# left margin fraction for row labels
L = 0.38   # ~1.33" for row labels
R = 0.01   # right margin
T = 0.26   # top header fraction
B = 0.30   # bottom fraction (colorbar + note)

heatmap_rect = [L, B, 1 - L - R, 1 - T - B]
ax = fig.add_axes(heatmap_rect)

# ── Heatmap via imshow ────────────────────────────────────────────────────────
cmap = plt.cm.RdBu_r
z_max = max(abs(z).max(), 0.1)
norm = TwoSlopeNorm(vmin=-z_max, vcenter=0, vmax=z_max)

im = ax.imshow(z, cmap=cmap, norm=norm, aspect="auto",
               interpolation="nearest")

# white grid lines between cells
for r in range(nrows + 1):
    ax.axhline(r - 0.5, color="white", lw=0.8)
for c in range(ncols + 1):
    ax.axvline(c - 0.5, color="white", lw=0.8)

# ── Cell annotations ─────────────────────────────────────────────────────────
FS = 5.0   # cell font size
for r in range(nrows):
    for c in range(ncols):
        colour = cmap(norm(z[r, c]))
        lum = 0.299*colour[0] + 0.587*colour[1] + 0.114*colour[2]
        tc = "white" if lum < 0.45 else "black"

        bstr = fmt_beta(beta[r, c], c)
        star = sig[r][c]

        yoffset = 0.15 if star else 0.0
        ax.text(c, r + yoffset, bstr, ha="center", va="center",
                fontsize=FS, fontweight="bold", color=tc)
        if star:
            ax.text(c, r - 0.22, star, ha="center", va="center",
                    fontsize=FS, color=tc)

# ── Axes ticks / labels ───────────────────────────────────────────────────────
ax.set_xticks(range(ncols))
ax.set_xticklabels(cols, fontsize=5.0, ha="center",
                   multialignment="center", linespacing=1.1)
ax.set_yticks(range(nrows))
ax.set_yticklabels(rows, fontsize=5.2, ha="right")
ax.tick_params(axis="both", length=0, pad=3)
ax.xaxis.tick_top()
ax.xaxis.set_label_position("top")

# ── Colorbar ─────────────────────────────────────────────────────────────────
cbar_left   = L
cbar_width  = 1 - L - R
cbar_bottom = 0.14
cbar_height = 0.07
cbar_ax = fig.add_axes([cbar_left, cbar_bottom, cbar_width, cbar_height])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=-z_max, vmax=z_max))
cb = plt.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cb.ax.tick_params(labelsize=4.5, length=2, width=0.4)
cb.set_label("Standardized β coefficient (z-score)", fontsize=4.8, labelpad=2)
cb.outline.set_linewidth(0.4)
cb.set_ticks([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5])

# ── Footer note ───────────────────────────────────────────────────────────────
fig.text(0.5, 0.01,
         "PGLS with Pagel's λ (ML), GTDB r214 genus tree, n = 1,547–1,574 genera",
         ha="center", va="bottom", fontsize=4.3, style="italic")

out_path = OUT / "fig01_multiaxis_heatmap.pdf"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"Saved {out_path}  ({out_path.stat().st_size // 1024}K)")
