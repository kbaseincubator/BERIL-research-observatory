"""
Negative-Binomial GLM with genome-size offset (Adam Arkin 2026-08-06 feedback).

The primary PGLS predictor (ko_per_mb_primary) is a ratio: KO count / genome size.
The denominator (genome size) correlates negatively with niche breadth, creating a
structural bias: even if absolute KO count were uncorrelated with niche breadth,
per-Mb density would still be negatively associated because specialists have smaller
genomes.

This script fits count models that treat genome size as an exposure (offset) rather
than dividing it out of the response:
  log E[n_ko] = α + β·B_std + log(genome_mb)

If β < 0 and significant → the absolute count itself is lower in narrow-niche genera,
and the ratio-variable bias does NOT explain the full signal.
If β ≈ 0 → the signal is consistent with pure genome-size scaling.

Models:
  M0: NB GLM (no genome correction)         — baseline
  M1: NB GLM + offset(log(genome_mb))       — proper count model
  M2: NB GLM + offset + genome_mb covariate — double-control (analog to NB23 OLS)
  M3: OLS ko_per_mb ~ B_std                 — what PGLS is estimating (no phylogeny)

Data:  data/01_pgls_input_bacteria.csv, data/01_genus_ko_density_spark.csv
Output: data/nb_glm_results.csv, figures/fig_nb_glm_genome_size_diagnostic.pdf
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson
from pathlib import Path

sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

DATA = Path("data")
FIGS = Path("figures")

# ── Load and join data ────────────────────────────────────────────────────────
pgls = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
dens = pd.read_csv(DATA / "01_genus_ko_density_spark.csv")

df = pgls.merge(
    dens[["genus_lower", "n_ko_primary", "mean_genome_mb"]].rename(
        columns={"mean_genome_mb": "genome_mb_d"}
    ),
    on="genus_lower",
    how="inner",
)
print(f"n genera: {len(df)}")

# Standardise niche breadth (same z-scoring as PGLS predictor_z)
B = df["mean_levins_B_std"].values
B_z = (B - B.mean()) / B.std()
y = df["n_ko_primary"].values.astype(int)
genome_mb = df["mean_genome_mb"].values
log_genome = np.log(genome_mb)
# z-score genome size for the covariate model
genome_z = (genome_mb - genome_mb.mean()) / genome_mb.std()
ko_per_mb = df["ko_per_mb_primary"].values

# ── Fit models ────────────────────────────────────────────────────────────────
results = {}

# M0: NB GLM, no genome correction
X0 = sm.add_constant(B_z)
m0 = NegativeBinomial(y, X0).fit(disp=False)
results["M0: NB (no genome)"] = {
    "beta_B":  m0.params[1],
    "se_B":    m0.bse[1],
    "z_B":     m0.tvalues[1],
    "p_B":     m0.pvalues[1],
    "alpha":   m0.params.get("alpha", np.nan),
    "AIC":     m0.aic,
    "note":    "no genome correction",
}

# M1: NB GLM with offset (genome size as exposure)
X1 = sm.add_constant(B_z)
m1 = NegativeBinomial(y, X1, offset=log_genome).fit(disp=False)
results["M1: NB + offset(log_genome)"] = {
    "beta_B":  m1.params[1],
    "se_B":    m1.bse[1],
    "z_B":     m1.tvalues[1],
    "p_B":     m1.pvalues[1],
    "alpha":   m1.params.get("alpha", np.nan),
    "AIC":     m1.aic,
    "note":    "offset = log(genome_mb); models KO rate directly",
}

# M2: NB GLM + offset + genome_mb as covariate (double control)
X2 = sm.add_constant(np.column_stack([B_z, genome_z]))
m2 = NegativeBinomial(y, X2, offset=log_genome).fit(disp=False)
results["M2: NB + offset + genome_cov"] = {
    "beta_B":  m2.params[1],
    "se_B":    m2.bse[1],
    "z_B":     m2.tvalues[1],
    "p_B":     m2.pvalues[1],
    "beta_g":  m2.params[2],
    "se_g":    m2.bse[2],
    "AIC":     m2.aic,
    "note":    "offset + genome_mb as covariate; analog to NB23 OLS",
}

# M3: OLS ko_per_mb ~ B_z (no phylogenetic correction; what PGLS is estimating)
X3 = sm.add_constant(B_z)
m3 = sm.OLS(ko_per_mb, X3).fit()
results["M3: OLS ko_per_mb"] = {
    "beta_B":  m3.params[1],
    "se_B":    m3.bse[1],
    "z_B":     m3.tvalues[1],
    "p_B":     m3.pvalues[1],
    "alpha":   np.nan,
    "AIC":     m3.aic,
    "note":    "OLS (no phylogeny); reference for PGLS beta=-0.021",
}

print("\n── Model comparison ──────────────────────────────────────────────────")
print(f"{'Model':<35} {'β_niche':>8} {'SE':>7} {'p':>10} {'AIC':>9}")
print("-" * 75)
for name, r in results.items():
    sig = "***" if r["p_B"] < 0.001 else ("**" if r["p_B"] < 0.01 else
          ("*" if r["p_B"] < 0.05 else "ns"))
    print(f"{name:<35} {r['beta_B']:>+8.4f} {r['se_B']:>7.4f} {r['p_B']:>10.4e} {sig}  AIC={r['AIC']:>9.1f}")

print(f"\nFor comparison: PGLS β = −0.021, p = 2.1×10⁻⁸ (phylogenetically corrected)")
print(f"OLS M3 β = {results['M3: OLS ko_per_mb']['beta_B']:+.4f} → PGLS is more conservative (smaller magnitude)")

# M1 log-rate-ratio → approximate ko_per_mb effect
beta_m1 = results["M1: NB + offset(log_genome)"]["beta_B"]
mean_rate = (y / genome_mb).mean()
approx_delta = mean_rate * (np.exp(beta_m1) - 1)
print(f"\nM1 interpretation: exp({beta_m1:.4f}) = {np.exp(beta_m1):.4f}")
print(f"  → {(np.exp(beta_m1)-1)*100:.1f}% change in KO rate per SD of niche breadth")
print(f"  → Δko_per_mb ≈ {approx_delta:.3f} per SD B_std (at mean rate {mean_rate:.2f} KO/Mb)")

# Save summary table
summary_rows = []
for name, r in results.items():
    summary_rows.append({"model": name, **r})
pd.DataFrame(summary_rows).to_csv(DATA / "nb_glm_results.csv", index=False)
print(f"\nSaved → data/nb_glm_results.csv")

# ── Figure: KO rate vs niche breadth (observed + model predictions) ───────────
fig, axs = plt.subplots(1, 2, figsize=(FIGW["2col"], ROW_H))

# Left: scatter ko_per_mb vs B_std with M1 prediction line
niche_grid = np.linspace(B.min(), B.max(), 200)
B_z_grid = (niche_grid - B.mean()) / B.std()
genome_mean_log = np.log(genome_mb.mean())

# M1 prediction at mean genome size
X1_grid = np.column_stack([np.ones(200), B_z_grid])
pred_m1 = m1.predict(X1_grid, offset=np.full(200, genome_mean_log))
pred_m1_rate = pred_m1 / np.exp(genome_mean_log)  # convert back to per-Mb rate

# M3 OLS prediction
X3_grid = np.column_stack([np.ones(200), B_z_grid])
pred_m3 = m3.predict(X3_grid)

# Bin observed data
n_bins = 20
bins = pd.qcut(B, n_bins, duplicates="drop")
obs_binned = pd.DataFrame({"B": B, "rate": ko_per_mb, "bin": bins}).groupby("bin").agg(
    B_mid=("B", "median"), rate_mean=("rate", "mean"), rate_se=("rate", "sem")
)

ax = axs[0]
ax.scatter(obs_binned["B_mid"], obs_binned["rate_mean"],
           color=PALETTE[0], s=30, zorder=4, edgecolor="k", linewidth=0.4,
           label="Observed (binned means)")
ax.errorbar(obs_binned["B_mid"], obs_binned["rate_mean"],
            yerr=1.96 * obs_binned["rate_se"],
            fmt="none", color=PALETTE[0], alpha=0.4, lw=0.8)
ax.plot(niche_grid, pred_m1_rate, color=PALETTE[1], lw=1.5,
        label=f"M1: NB + offset (β={beta_m1:+.3f})")
ax.plot(niche_grid, pred_m3, color=PALETTE[2], lw=1.5, ls="--",
        label=f"M3: OLS (β={results['M3: OLS ko_per_mb']['beta_B']:+.3f})")
ax.set_xlabel("Levins B_std (niche breadth)")
ax.set_ylabel("KO rate (ko per Mb genome)")
ax.set_title("Observed rates vs NB + offset prediction")
ax.legend(fontsize=7, loc="upper right", framealpha=0.7)

# Right: forest plot of beta_B across models with CIs
model_names = list(results.keys())
betas = [results[m]["beta_B"] for m in model_names]
ses   = [results[m]["se_B"]   for m in model_names]
pvals = [results[m]["p_B"]    for m in model_names]
colors = [PALETTE[2] if "M1" in m else (PALETTE[0] if "M3" in m else PALETTE[3])
          for m in model_names]

ax2 = axs[1]
y_pos = range(len(model_names))
for i, (b, s, p, col) in enumerate(zip(betas, ses, pvals, colors)):
    ax2.errorbar(b, i, xerr=1.96 * s, fmt="o", color=col,
                 capsize=3, capthick=0.8, markersize=6,
                 markeredgecolor="k", markeredgewidth=0.5, lw=1.2)
    sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
    ax2.annotate(f"β={b:+.3f} ({sig})", xy=(b + 0.001, i),
                 xytext=(4, 0), textcoords="offset points",
                 fontsize=7, va="center")

ax2.axvline(0, color="gray", lw=0.8, ls="--")
ax2.axvline(-0.021, color="gray", lw=0.8, ls=":", alpha=0.6)
ax2.annotate("PGLS β=−0.021", xy=(-0.021, len(model_names) - 0.3),
             fontsize=6, color="gray", ha="center")
ax2.set_yticks(list(y_pos))
ax2.set_yticklabels(model_names, fontsize=7)
ax2.set_xlabel("β for niche breadth (Levins B_std)")
ax2.set_title("β comparison across model specifications")

fig.suptitle(
    "NB GLM with genome-size offset: does absolute KO count track niche breadth?\n"
    "(addresses ratio-variable bias in per-Mb density predictor)",
    y=1.01,
)
plt.tight_layout()
save(fig, FIGS / "fig_nb_glm_genome_size_diagnostic")
print(f"Figure saved → {FIGS}/fig_nb_glm_genome_size_diagnostic.pdf")
