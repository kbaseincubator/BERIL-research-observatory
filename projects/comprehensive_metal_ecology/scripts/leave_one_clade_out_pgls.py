"""
Leave-one-clade-out PGLS diagnostic (Uyeda, Zenil-Ferguson & Pennell 2018 Syst Biol 67:1091).

Model: log(n_ko + 0.5) ~ B_z + log_genome   (GLS with Pagel's lambda, fixed=0.757618)
Method: direct GLS via matrix algebra — avoids nlme iteration overhead.
  V_lambda = lambda * C_phylo + (1 - lambda) * I    (C_phylo = phylo correlation matrix)
  beta = (X' V^{-1} X)^{-1} X' V^{-1} y
  Vcov(beta) = sigma2 * (X' V^{-1} X)^{-1}
  sigma2 = RSS / (n - p)   where RSS = (y - X beta)' V^{-1} (y - X beta)

Reference lambda: 0.757618 from NB01 ML estimation.
"""

import numpy as np
import pandas as pd
from scipy import linalg, stats
from pathlib import Path

# Try dendropy (fast tree reading), fall back to ete3 or subprocess+R
try:
    import dendropy
    USE_DENDROPY = True
except ImportError:
    USE_DENDROPY = False

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "projects/comprehensive_metal_ecology/data"

LAMBDA_FULL = 0.757618  # ML estimate from NB01

# ── Load PGLS data ─────────────────────────────────────────────────────────────
pgls_df = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
dens_df = pd.read_csv(DATA / "01_genus_ko_density_spark.csv")

df = pgls_df[["genus_lower", "mean_levins_B_std", "mean_genome_mb", "phylum"]].merge(
    dens_df[["genus_lower", "n_ko_primary"]],
    on="genus_lower"
)
print(f"Loaded {len(df)} genera, {df.phylum.nunique()} phyla")

# ── Read VCV matrix via R (one call, then use in Python) ──────────────────────
# We use R just to read the tree and compute vcv, then pass back as CSV.
import subprocess, tempfile, os

tree_path = DATA / "gtdb_bac_genus_pruned.tree"
vcv_cache = DATA / "gtdb_bac_genus_vcv_corr.npy"
tips_cache = DATA / "gtdb_bac_genus_vcv_tips.csv"

if vcv_cache.exists() and tips_cache.exists():
    print("Loading cached VCV matrix...")
    corr_mat = np.load(vcv_cache)
    tips = pd.read_csv(tips_cache)["tip"].tolist()
    print(f"  VCV loaded: {corr_mat.shape[0]} tips")
else:
    print("Computing VCV via R (one-time; will be cached)...")
    r_script = f"""
suppressMessages(library(ape))
tree <- read.tree("{tree_path}")
vcv_mat <- vcv(tree)
d <- sqrt(diag(vcv_mat))
corr_mat <- vcv_mat / outer(d, d)
tips <- rownames(corr_mat)
write.csv(data.frame(tip=tips), "{tips_cache}", row.names=FALSE)
# Save as flat binary: row-major double
writeBin(as.vector(t(corr_mat)), "{vcv_cache}.bin", size=8)
cat(sprintf("VCV saved: %d tips\\n", length(tips)))
"""
    with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as f:
        f.write(r_script)
        r_tmp = f.name
    result = subprocess.run(
        ["/home/hmacgregor/r_env/bin/Rscript", r_tmp],
        capture_output=True, text=True, timeout=300
    )
    os.unlink(r_tmp)
    print(result.stdout.strip())
    if result.returncode != 0:
        raise RuntimeError(f"R VCV computation failed:\n{result.stderr}")

    tips = pd.read_csv(tips_cache)["tip"].tolist()
    n_tree = len(tips)
    corr_mat = np.frombuffer(
        open(str(vcv_cache) + ".bin", "rb").read(), dtype=np.float64
    ).reshape(n_tree, n_tree)
    np.save(vcv_cache, corr_mat)
    os.remove(str(vcv_cache) + ".bin")
    print(f"  Cached VCV: {n_tree} tips")

# ── Align data to tree ─────────────────────────────────────────────────────────
tip_idx = {t: i for i, t in enumerate(tips)}
df = df[df["genus_lower"].isin(tip_idx)].copy()
df["tip_i"] = df["genus_lower"].map(tip_idx)

# Prepare variables
df["B_z"]        = (df["mean_levins_B_std"] - df["mean_levins_B_std"].mean()) / df["mean_levins_B_std"].std()
df["log_genome"] = np.log(df["mean_genome_mb"])
df["log_nko"]    = np.log(df["n_ko_primary"] + 0.5)

print(f"Aligned genera: {len(df)}")

# ── Direct GLS function ────────────────────────────────────────────────────────
def fit_gls_fixed_lambda(y, X, vcv_idx, lam, corr_full):
    """
    Fit GLS: y ~ X with Pagel's lambda (fixed).
    vcv_idx: integer indices into corr_full for the subset.
    Uses Cholesky whitening — avoids forming n×n V_inv (O(n²) after Cholesky).
    """
    n, p = X.shape
    C = corr_full[np.ix_(vcv_idx, vcv_idx)]
    V = lam * C + (1.0 - lam) * np.eye(n)
    L = linalg.cholesky(V, lower=True)
    # Whiten X and y: z = L^{-1} @ v  (triangular solve, O(n²))
    z_X = linalg.solve_triangular(L, X, lower=True)
    z_y = linalg.solve_triangular(L, y, lower=True)
    # X'V^{-1}X = z_X'z_X  (p×p, trivial); X'V^{-1}y = z_X'z_y
    XtVX = z_X.T @ z_X
    XtVy = z_X.T @ z_y
    beta = linalg.solve(XtVX, XtVy, assume_a='pos')
    z_resid = z_y - z_X @ beta
    rss    = float(z_resid @ z_resid)
    sigma2 = rss / (n - p)
    vcov   = sigma2 * linalg.inv(XtVX)   # p×p inverse, trivial
    se     = np.sqrt(np.diag(vcov))
    t_val  = beta / se
    p_val  = 2 * (1 - stats.t.cdf(np.abs(t_val), df=n - p))
    return {
        "beta": beta[1],
        "se":   se[1],
        "t":    t_val[1],
        "p":    p_val[1],
        "n":    n,
    }

# ── Full model ─────────────────────────────────────────────────────────────────
df_sorted = df.sort_values("tip_i")
y_full    = df_sorted["log_nko"].values
X_full    = np.column_stack([
    np.ones(len(df_sorted)),
    df_sorted["B_z"].values,
    df_sorted["log_genome"].values
])
idx_full  = df_sorted["tip_i"].values

print("\nFitting full model (fixed lambda=0.757618)...")
full_res = fit_gls_fixed_lambda(y_full, X_full, idx_full, LAMBDA_FULL, corr_mat)
print(f"  Full: beta(B_z)={full_res['beta']:+.5f}  SE={full_res['se']:.5f}  "
      f"p={full_res['p']:.3e}  n={full_res['n']}")

# ── Leave-one-phylum-out ───────────────────────────────────────────────────────
phylum_counts = df["phylum"].value_counts()
drop_phyla    = phylum_counts[phylum_counts >= 10].index.tolist()
print(f"\nPhylum counts (n>=10): {dict(phylum_counts[phylum_counts >= 10])}")
print(f"Testing {len(drop_phyla)} leave-out phyla...\n")

rows = []
# Full model row
rows.append({
    "dropped_phylum": "None (full model)",
    "n_dropped": 0,
    "n_remaining": full_res["n"],
    "beta_Bz": round(full_res["beta"], 5),
    "se_Bz":   round(full_res["se"],   5),
    "t_Bz":    round(full_res["t"],    3),
    "p_Bz":    round(full_res["p"],    6),
    "significant_p05": full_res["p"] < 0.05,
    "same_direction":  True,
})

for phy in drop_phyla:
    sub = df[df["phylum"] != phy].sort_values("tip_i")
    n_dropped = int((df["phylum"] == phy).sum())
    y_sub   = sub["log_nko"].values
    X_sub   = np.column_stack([
        np.ones(len(sub)),
        sub["B_z"].values,
        sub["log_genome"].values
    ])
    idx_sub = sub["tip_i"].values

    try:
        res = fit_gls_fixed_lambda(y_sub, X_sub, idx_sub, LAMBDA_FULL, corr_mat)
        same_dir = np.sign(res["beta"]) == np.sign(full_res["beta"])
        sig05    = res["p"] < 0.05
        flag = "DIR_STABLE" if same_dir else "DIR_FLIP!"
        print(f"  Drop {phy:<30s} (n={n_dropped:3d}) -> "
              f"beta={res['beta']:+.5f}  SE={res['se']:.5f}  "
              f"p={res['p']:.3e}  n={res['n']}  {flag}")
        rows.append({
            "dropped_phylum": phy,
            "n_dropped": n_dropped,
            "n_remaining": res["n"],
            "beta_Bz": round(res["beta"], 5),
            "se_Bz":   round(res["se"],   5),
            "t_Bz":    round(res["t"],    3),
            "p_Bz":    round(res["p"],    6),
            "significant_p05": sig05,
            "same_direction": same_dir,
        })
    except Exception as e:
        print(f"  Drop {phy}: FAILED — {e}")
        rows.append({
            "dropped_phylum": phy, "n_dropped": n_dropped, "n_remaining": len(sub),
            "beta_Bz": None, "se_Bz": None, "t_Bz": None, "p_Bz": None,
            "significant_p05": None, "same_direction": None,
        })

out = pd.DataFrame(rows)

# ── Summary ────────────────────────────────────────────────────────────────────
n_tested = len(out) - 1
n_stable = int(out.iloc[1:]["same_direction"].sum())
n_sig    = int(out.iloc[1:]["significant_p05"].sum())

print(f"\n=== SUMMARY ===")
print(out[["dropped_phylum","n_dropped","n_remaining","beta_Bz","se_Bz","p_Bz",
           "significant_p05","same_direction"]].to_string(index=False))
print(f"\nDirection stable in {n_stable}/{n_tested} leave-one-phylum-out fits")
print(f"Significant (p<0.05) in {n_sig}/{n_tested} leave-one-phylum-out fits")

out_path = DATA / "clade_leave_one_out_pgls.csv"
out.to_csv(out_path, index=False)
print(f"\nSaved -> {out_path}")
