"""
Subcategory random-effects meta-analysis (Hadfield & Nakagawa 2010 J Evol Biol 23:494).

Adam Arkin (2026-08-06) flagged that the subcategory Kruskal-Wallis test on per-KO β values
ignores precision — a KO with SE=0.001 and one with SE=0.200 get equal weight.

This script replaces the KW test with a random-effects meta-analytic model:
  β_i = μ_c(i) + u_i + ε_i
  u_i ~ N(0, τ²)        [between-KO heterogeneity]
  ε_i ~ N(0, SE_i²)     [known measurement error]

Estimator: DerSimonian-Laird for τ², then inverse-variance weighted means and Q_between test.

Data:  data/39_per_ko_levinsB_pgls.csv   (118 KOs, per-KO PGLS β and SE)
Outputs:
  data/subcategory_meta_analysis.csv       — subcategory weighted means and CIs
  figures/fig_subcategory_forest_plot.pdf  — forest plot (replaces raw KW figure)
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

DATA = Path("data")
FIGS = Path("figures")

# ── Load per-KO PGLS results ──────────────────────────────────────────────────
df = pd.read_csv(DATA / "39_per_ko_levinsB_pgls.csv")
df = df.dropna(subset=["beta", "SE"]).copy()
df = df[df["SE"] > 0].reset_index(drop=True)
print(f"Loaded {len(df)} KOs with valid β and SE")

beta = df["beta"].values
SE   = df["SE"].values
w_fe = 1.0 / SE**2   # fixed-effects weights

# ── DerSimonian-Laird τ² estimator ────────────────────────────────────────────
mu_fe  = np.dot(w_fe, beta) / w_fe.sum()
Q_tot  = np.sum(w_fe * (beta - mu_fe)**2)
n_ko   = len(df)
df_Q   = n_ko - 1
C      = w_fe.sum() - np.sum(w_fe**2) / w_fe.sum()
tau2   = max(0.0, (Q_tot - df_Q) / C)
tau    = np.sqrt(tau2)
I2     = max(0.0, (Q_tot - df_Q) / Q_tot) * 100.0

print(f"\n── Heterogeneity ─────────────────────────────────────────────────────")
print(f"  Q_total = {Q_tot:.2f}, df = {df_Q}, p = {1-stats.chi2.cdf(Q_tot, df_Q):.4f}")
print(f"  τ² (DL) = {tau2:.6f},  τ = {tau:.4f}")
print(f"  I²      = {I2:.1f}%")

# ── Random-effects weights ────────────────────────────────────────────────────
w_re = 1.0 / (SE**2 + tau2)
mu_grand = np.dot(w_re, beta) / w_re.sum()

# ── Subcategory estimates (weighted means) ────────────────────────────────────
CAT_ORDER = [
    "Cofactor Biosynthesis",
    "Metal-dependent Metabolism",
    "Transport/Homeostasis",
    "Sensing/Regulation",
    "Resistance/Detoxification",
]
# Short display labels
LABELS = {
    "Cofactor Biosynthesis":         "Cofactor",
    "Metal-dependent Metabolism":    "Metal metab.",
    "Transport/Homeostasis":         "Transport",
    "Sensing/Regulation":            "Sensing",
    "Resistance/Detoxification":     "Resistance",
}
CAT_COLORS = {cat: PALETTE[i] for i, cat in enumerate(CAT_ORDER)}

cat_rows = []
for cat in CAT_ORDER:
    mask = (df["subcategory"] == cat).values
    if not mask.any():
        continue
    wc   = w_re[mask]
    bc   = beta[mask]
    sEc  = SE[mask]
    Wc   = wc.sum()
    mu_c = np.dot(wc, bc) / Wc
    se_c = 1.0 / np.sqrt(Wc)
    z_c  = mu_c / se_c
    p_c  = 2 * (1 - stats.norm.cdf(abs(z_c)))
    Qw_c = np.sum(wc * (bc - mu_c)**2)
    cat_rows.append({
        "subcategory": cat,
        "n_ko":        int(mask.sum()),
        "mu":          mu_c,
        "se":          se_c,
        "ci_lo":       mu_c - 1.96 * se_c,
        "ci_hi":       mu_c + 1.96 * se_c,
        "z":           z_c,
        "p":           p_c,
        "Q_within":    Qw_c,
    })

cat_df = pd.DataFrame(cat_rows).set_index("subcategory")

# ── Between-subcategory Q test ────────────────────────────────────────────────
Q_within   = cat_df["Q_within"].sum()
Q_between  = Q_tot - Q_within
df_between = len(cat_df) - 1
p_between  = 1 - stats.chi2.cdf(Q_between, df_between)

print(f"\n── Between-subcategory test ──────────────────────────────────────────")
print(f"  Q_between = {Q_between:.3f}, df = {df_between}, p = {p_between:.4e}")
print(f"\n── Subcategory weighted means ────────────────────────────────────────")
display = cat_df[["n_ko", "mu", "se", "ci_lo", "ci_hi", "z", "p"]].round(4)
print(display.to_string())

# ── Save results ──────────────────────────────────────────────────────────────
cat_df_out = cat_df.reset_index()
cat_df_out["tau2"] = tau2
cat_df_out["I2"]   = I2
cat_df_out["Q_between"] = Q_between
cat_df_out["p_between"] = p_between
cat_df_out.to_csv(DATA / "subcategory_meta_analysis.csv", index=False)
print(f"\nSaved → data/subcategory_meta_analysis.csv")

# ── Forest plot ───────────────────────────────────────────────────────────────
# Layout: categories listed top-to-bottom (most-negative first)
# Individual KO estimates as thin horizontal lines (no marker to reduce clutter)
# Subcategory summaries as filled squares

plot_order = cat_df.sort_values("mu").index.tolist()  # most-negative at top

# Build y-axis mapping: each category gets a block
# Within each block: individual KOs stacked, then summary square
y_pos_per_ko  = {}
y_pos_summary = {}
y_tick_positions = []
y_tick_labels = []
y = 0

ko_y_data = []   # (y, beta, se, color)
summ_data  = []  # (y, mu, se, color, label)

for cat in plot_order:
    mask = (df["subcategory"] == cat).values
    ko_betas = beta[mask]
    ko_SEs   = SE[mask]
    ko_w     = w_re[mask]
    n_c      = mask.sum()
    color    = CAT_COLORS.get(cat, PALETTE[0])

    # Sort individual KOs by β (ascending) within category
    order = np.argsort(ko_betas)
    for b, s in zip(ko_betas[order], ko_SEs[order]):
        ko_y_data.append((y, b, s, color))
        y += 1

    # Gap then summary
    y_gap = y + 0.4
    mu_c = cat_df.loc[cat, "mu"]
    se_c = cat_df.loc[cat, "se"]
    summ_data.append((y_gap, mu_c, se_c, color, LABELS.get(cat, cat)))
    y_tick_positions.append(y_gap)
    y_tick_labels.append(
        f"{LABELS.get(cat, cat)} (n={cat_df.loc[cat,'n_ko']})"
        f"\nμ={mu_c:+.3f} [{cat_df.loc[cat,'ci_lo']:+.3f}, {cat_df.loc[cat,'ci_hi']:+.3f}]"
    )
    y += 2.2   # gap between categories

total_height = max(y * 0.18, ROW_H * 1.5)
fig, ax = plt.subplots(figsize=(FIGW["2col"], total_height))

# Individual KO CIs (thin gray lines)
for y_val, b, s, color in ko_y_data:
    ax.plot([b - 1.96*s, b + 1.96*s], [y_val, y_val],
            color=color, alpha=0.25, lw=0.6, solid_capstyle="round")
    ax.scatter(b, y_val, color=color, s=8, zorder=3, edgecolor="none", alpha=0.4)

# Subcategory summary squares (diamonds)
for y_val, mu_c, se_c, color, lbl in summ_data:
    ci_lo = mu_c - 1.96 * se_c
    ci_hi = mu_c + 1.96 * se_c
    ax.plot([ci_lo, ci_hi], [y_val, y_val], color=color, lw=1.8, zorder=5)
    ax.scatter(mu_c, y_val, color=color, s=80, marker="D",
               zorder=6, edgecolor="k", linewidth=0.5)

# Reference lines
ax.axvline(0, color="gray", lw=0.8, ls="--", zorder=1)

# Y-axis: category summary positions
ax.set_yticks(y_tick_positions)
ax.set_yticklabels(y_tick_labels, fontsize=7)
ax.set_xlabel("PGLS β (niche breadth ~ KO presence/density)")
ax.set_ylabel("")

# Annotate Q_between
ax.annotate(
    f"$Q_{{between}}$ = {Q_between:.1f}, df = {df_between}, p = {p_between:.1e}\n"
    f"$τ²$ = {tau2:.4f}, $I²$ = {I2:.0f}%",
    xy=(0.98, 0.02), xycoords="axes fraction",
    ha="right", va="bottom", fontsize=8, color="#444444",
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="lightgray", lw=0.6),
)

fig.suptitle(
    "Subcategory random-effects meta-analysis: per-KO Levins B ~ metal gene density\n"
    "(replaces Kruskal-Wallis unweighted test; DerSimonian-Laird τ²)",
    y=1.01, fontsize=10,
)
plt.tight_layout()
save(fig, FIGS / "fig_subcategory_forest_plot")
print(f"Figure saved → {FIGS}/fig_subcategory_forest_plot.pdf")

print("\nDone.")
