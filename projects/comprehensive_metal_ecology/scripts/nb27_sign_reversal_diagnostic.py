"""
NB27 sign-reversal diagnostic (2026-08-09).

Mechanistically explains why n_biomes (v1, β=+0.215) and n_envs_v2 (β=−0.148)
give opposite signs in the inverse PGLS (ko_per_mb_primary ~ niche characteristics).

Key question: is the reversal caused by genome-size confounding or by qualitative
differences in which taxa rank high on each metric?
"""

import pandas as pd
import numpy as np
from scipy import stats
from numpy.linalg import lstsq
from pathlib import Path

ROOT  = Path(__file__).resolve().parents[3]
DATA  = ROOT / "projects/comprehensive_metal_ecology/data"
MA    = ROOT / "projects/microbeatlas_metal_ecology/data"

pgls_in  = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
niche_v1 = pd.read_csv(DATA / "nb27_niche_characteristics.csv",
                        usecols=["genus_lower", "n_biomes", "n_detected"])

nb_v2 = pd.read_csv(MA / "otu_niche_breadth_v2_env_only.csv",
                    usecols=["genus_v1compat", "n_envs_detected", "levins_B_std"])
nb_v2 = nb_v2[nb_v2["genus_v1compat"].notna() & (nb_v2["genus_v1compat"].str.strip() != "")]
nb_v2["genus_lower"] = nb_v2["genus_v1compat"].str.lower().str.strip()
nenvs = nb_v2.groupby("genus_lower").agg(
    n_envs_v2=("n_envs_detected", "mean"),
    n_otus=("n_envs_detected", "count"),
).reset_index()

df = (pgls_in[["genus_lower", "ko_per_mb_primary", "mean_genome_mb", "mean_levins_B_std"]]
      .merge(niche_v1, on="genus_lower", how="left")
      .merge(nenvs, on="genus_lower", how="left"))
df = df[df["n_biomes"].notna() & df["n_envs_v2"].notna()].copy()
print(f"Working dataset: n={len(df)} genera\n")

# ── 1. Basic cross-metric correlation ─────────────────────────────────────────
r, p = stats.pearsonr(df["n_biomes"], df["n_envs_v2"])
rho, pp = stats.spearmanr(df["n_biomes"], df["n_envs_v2"])
print(f"n_biomes vs n_envs_v2: Pearson r={r:.3f} (p={p:.2e}), Spearman ρ={rho:.3f} (p={pp:.2e})")

# ── 2. Genome size correlations ────────────────────────────────────────────────
d = df[df["mean_genome_mb"].notna()].copy()
print(f"\nGenome size (mean_genome_mb) correlations:")
for col in ("n_biomes", "n_envs_v2"):
    rho2, p2 = stats.spearmanr(d[col], d["mean_genome_mb"])
    print(f"  {col} vs genome: ρ={rho2:.3f} (p={p2:.2e})")

# ── 3. KO density correlations ─────────────────────────────────────────────────
print(f"\nKO density correlations:")
for col in ("n_biomes", "n_envs_v2"):
    rho3, p3 = stats.spearmanr(d[col], d["ko_per_mb_primary"])
    print(f"  {col} vs KO/Mb: ρ={rho3:.3f} (p={p3:.2e})")

# ── 4. Partial correlation controlling for log_genome ─────────────────────────
def residualise(x, cov):
    A = np.column_stack([np.ones(len(cov)), cov])
    coef, _, _, _ = lstsq(A, x, rcond=None)
    return x - A @ coef

d3 = d[["n_biomes", "n_envs_v2", "ko_per_mb_primary", "mean_genome_mb"]].dropna().copy()
log_g = np.log(d3["mean_genome_mb"].values)
r_nb, p_nb  = stats.pearsonr(residualise(d3["n_biomes"].values, log_g),
                              residualise(d3["ko_per_mb_primary"].values, log_g))
r_ne, p_ne  = stats.pearsonr(residualise(d3["n_envs_v2"].values, log_g),
                              residualise(d3["ko_per_mb_primary"].values, log_g))
print(f"\nPartial correlation (controlling for log_genome_size):")
print(f"  n_biomes  ↔ KO/Mb | genome: r={r_nb:.3f} (p={p_nb:.2e})")
print(f"  n_envs_v2 ↔ KO/Mb | genome: r={r_ne:.3f} (p={p_ne:.2e})")

# ── 5. Exemplar genera ─────────────────────────────────────────────────────────
print("\nTop 10 by n_biomes:")
cols = ["genus_lower", "n_biomes", "n_envs_v2", "mean_genome_mb", "ko_per_mb_primary"]
print(d.nlargest(10, "n_biomes")[cols].to_string(index=False))

print("\nTop 10 by n_envs_v2:")
print(d.nlargest(10, "n_envs_v2")[cols].to_string(index=False))

d["nb_z"] = (d["n_biomes"] - d["n_biomes"].mean()) / d["n_biomes"].std()
d["ne_z"] = (d["n_envs_v2"] - d["n_envs_v2"].mean()) / d["n_envs_v2"].std()
d["delta"] = d["nb_z"] - d["ne_z"]
print("\nTop 10 where n_biomes >> n_envs_v2 (drive positive v1 β):")
print(d.nlargest(10, "delta")[cols].to_string(index=False))
print("\nTop 10 where n_envs_v2 >> n_biomes (drive negative v2 β):")
print(d.nsmallest(10, "delta")[cols].to_string(index=False))
