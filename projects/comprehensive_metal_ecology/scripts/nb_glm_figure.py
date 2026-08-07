"""
Figure for NB GLM genome-size offset diagnostic (uses pre-computed predictions from R).
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

DATA = Path("data")
FIGS = Path("figures")

pred = pd.read_csv(DATA / "nb_glm_predictions.csv")
res  = pd.read_csv(DATA / "nb_glm_results.csv")

# ── Figure: 2 panels ──────────────────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(FIGW["2col"], ROW_H))

# ── Left: observed KO rate vs niche breadth, with M0/M1 fitted rates ──────────
B = pred["levins_B_std"].values
rate_obs = pred["ko_rate_obs"].values
rate_m1  = pred["ko_rate_pred_m1"].values
rate_m0  = pred["ko_rate_pred_m0"].values

# Bin into 20 quantile bins
n_bins = 20
bins = pd.qcut(B, n_bins, duplicates="drop")
df_bin = pd.DataFrame({"B": B, "obs": rate_obs, "m1": rate_m1, "m0": rate_m0, "bin": bins})
agg = df_bin.groupby("bin").agg(
    B_mid=("B", "median"),
    obs_mean=("obs", "mean"), obs_se=("obs", "sem"),
    m1_mean=("m1", "mean"),
    m0_mean=("m0", "mean"),
).reset_index()

ax = axs[0]
ax.scatter(agg["B_mid"], agg["obs_mean"], color=PALETTE[0], s=28,
           edgecolor="k", linewidth=0.4, zorder=4, label="Observed (bin means)")
ax.errorbar(agg["B_mid"], agg["obs_mean"], yerr=1.96 * agg["obs_se"],
            fmt="none", color=PALETTE[0], alpha=0.4, lw=0.8)

# Smooth M1 and M0 lines using binned predictions
ax.plot(agg["B_mid"], agg["m1_mean"], color=PALETTE[1], lw=1.5,
        label="M1: NB + offset  (β=−0.097***)")
ax.plot(agg["B_mid"], agg["m0_mean"], color=PALETTE[3], lw=1.2, ls="--",
        label="M0: NB no offset (β=+0.025*)")

ax.set_xlabel("Levins B_std (niche breadth)")
ax.set_ylabel("Metal KO rate (KOs per Mb genome)")
ax.set_title("Absolute KO count ÷ genome size vs niche breadth")
ax.legend(fontsize=7, loc="upper right", framealpha=0.7)

# ── Right: forest plot — β across models ──────────────────────────────────────
model_labels = {
    "M0: NB (no genome)":            "M0: NB\n(no genome correction)",
    "M1: NB + offset(log_genome)":   "M1: NB + offset\n(genome as exposure)",
    "M2: NB + offset + genome_cov":  "M2: NB + offset\n+ genome covariate",
    "M3: OLS ko_per_mb":             "M3: OLS ko_per_mb\n(≈ non-phylog. PGLS)",
}
model_colors = {
    "M0: NB (no genome)":           PALETTE[3],
    "M1: NB + offset(log_genome)":  PALETTE[1],
    "M2: NB + offset + genome_cov": PALETTE[2],
    "M3: OLS ko_per_mb":            PALETTE[0],
}

ax2 = axs[1]
for i, row in res.iterrows():
    b   = row["beta_B"]
    se  = row["se_B"]
    p   = row["p_B"]
    col = model_colors.get(row["model"], PALETTE[0])
    lbl = model_labels.get(row["model"], row["model"])
    sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
    ax2.errorbar(b, i, xerr=1.96 * se, fmt="o", color=col,
                 capsize=3, capthick=0.8, markersize=6,
                 markeredgecolor="k", markeredgewidth=0.5, lw=1.2, zorder=4)
    ax2.annotate(f"{sig}", xy=(b + 1.96*se + 0.005, i),
                 fontsize=8, va="center", color=col)

ax2.axvline(0, color="gray", lw=0.8, ls="--")
ax2.axvline(-0.021/8.61, color="gray", lw=0.6, ls=":", alpha=0.5)
ax2.set_yticks(list(range(len(res))))
ax2.set_yticklabels([model_labels.get(m, m) for m in res["model"]], fontsize=7.5)
ax2.set_xlabel("β for Levins B_std (per SD niche breadth)\n[NB: log rate ratio; OLS: Δko_per_mb]")
ax2.set_title("β across model specifications")
ax2.annotate("PGLS\n(phylog.)\nβ=−0.021", xy=(-0.021/8.61, 3.7),
             fontsize=6, color="gray", ha="center")

fig.suptitle(
    "NB GLM with genome-size offset: does ratio-variable bias explain the CME signal?\n"
    "M1 confirms: absolute KO rate is lower in broad-niche genera (β=−0.097, p=5×10⁻²⁰)",
    y=1.02,
)
plt.tight_layout()
save(fig, FIGS / "fig_nb_glm_genome_size_diagnostic")
print(f"Figure saved → {FIGS}/fig_nb_glm_genome_size_diagnostic.pdf")
