"""
Random-effects meta-regression of Pagel's lambda across KEGG functional subcategories.

Reference: Hadfield & Nakagawa 2010 J Evol Biol 23:494-508;
           DerSimonian & Laird 1986 Control Clin Trials 7:177-188

Model: lambda_i ~ subcategory (fixed moderator) + u_i (random KO effect)
Sampling variance: vi = 1 / (n_genera - 3)
tau2: DerSimonian-Laird method-of-moments estimate
"""

import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "projects/comprehensive_metal_ecology/data"

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA / "phylo_d_all_ko.csv")
print(f"Loaded {len(df)} metal KOs")
print(df['subcategory'].value_counts())

df = df[df['subcategory'] != 'Unknown'].copy()
print(f"\nAfter excluding Unknown: {len(df)} KOs")

# ── Sampling variance approximation ───────────────────────────────────────────
df['vi'] = 1.0 / (df['n_genera'] - 3).clip(lower=1)

# ── Reference level and design matrix ─────────────────────────────────────────
cats_ordered = ['Cofactor Biosynthesis', 'Metal-dependent Metabolism',
                'Resistance/Detoxification', 'Sensing/Regulation',
                'Transport/Homeostasis']
df['subcategory'] = pd.Categorical(df['subcategory'], categories=cats_ordered)

yi = df['lambda'].values
vi = df['vi'].values

# Design matrix (subcategory dummy, Cofactor Biosynthesis = intercept)
X = np.column_stack([
    np.ones(len(df)),
    (df['subcategory'] == 'Metal-dependent Metabolism').astype(float).values,
    (df['subcategory'] == 'Resistance/Detoxification').astype(float).values,
    (df['subcategory'] == 'Sensing/Regulation').astype(float).values,
    (df['subcategory'] == 'Transport/Homeostasis').astype(float).values,
])
col_names = ['(Intercept)', 'Metal-dep_Metab', 'Resistance/Detox',
             'Sensing/Reg', 'Transport/Homeo']

def fit_wls(yi, vi_total, X):
    """Weighted least squares with weights 1/vi_total."""
    W = np.diag(1.0 / vi_total)
    XtW = X.T @ W
    XtWX_inv = np.linalg.inv(XtW @ X)
    beta = XtWX_inv @ (XtW @ yi)
    vcov = XtWX_inv
    return beta, vcov

def dl_tau2(yi, vi, X):
    """DerSimonian-Laird method-of-moments estimate of tau2."""
    W0 = np.diag(1.0 / vi)
    beta0, _ = fit_wls(yi, vi, X)
    resid = yi - X @ beta0
    Q = resid @ W0 @ resid  # Cochran Q
    p = X.shape[1]
    k = len(yi)
    # Trace term for DL formula
    XtW0X = X.T @ W0 @ X
    c = np.trace(W0) - np.trace(np.linalg.inv(XtW0X) @ X.T @ W0 @ W0 @ X)
    tau2 = max(0.0, (Q - (k - p)) / c)
    return tau2, Q, k - p

# ── Model 0: Intercept only ────────────────────────────────────────────────────
X0 = np.ones((len(df), 1))
tau2_0, Q0, df0 = dl_tau2(yi, vi, X0)
beta0, vcov0 = fit_wls(yi, vi + tau2_0, X0)
se0 = np.sqrt(np.diag(vcov0))
print(f"\n=== Model 0: Intercept-only ===")
print(f"Overall mean lambda = {beta0[0]:.4f} [{beta0[0]-1.96*se0[0]:.4f}, {beta0[0]+1.96*se0[0]:.4f}]")
print(f"tau2 = {tau2_0:.4f}")
# I2 = tau2 / (tau2 + typical_vi)
typical_vi = np.median(vi)
I2_0 = 100 * tau2_0 / (tau2_0 + typical_vi)
print(f"I2 (approx) = {I2_0:.1f}%")
print(f"Cochran Q({df0}) = {Q0:.2f}")

# ── Model 1: Subcategory moderator ────────────────────────────────────────────
tau2_1, Q1_residual, df1_resid = dl_tau2(yi, vi, X)
beta1, vcov1 = fit_wls(yi, vi + tau2_1, X)
se1 = np.sqrt(np.diag(vcov1))
z1 = beta1 / se1
p1 = 2 * (1 - stats.norm.cdf(np.abs(z1)))

print(f"\n=== Model 1: Subcategory moderator ===")
print(f"tau2 = {tau2_1:.4f}")
I2_1 = 100 * tau2_1 / (tau2_1 + typical_vi)
print(f"I2 (approx) = {I2_1:.1f}%")
print(f"Residual Q({df1_resid}) = {Q1_residual:.2f}")

print(f"\nCoefficients:")
for name, b, se, z, p in zip(col_names, beta1, se1, z1, p1):
    stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    print(f"  {name:<30s}  b={b:+.4f}  SE={se:.4f}  z={z:+.2f}  p={p:.4f}  {stars}")

# ── Omnibus moderator test (Wald QM) ──────────────────────────────────────────
# Test the 4 slope coefficients jointly
W_star = np.diag(1.0 / (vi + tau2_1))
XtWsX = X.T @ W_star @ X
beta_slopes = beta1[1:]
# Submatrix for slopes
vcov_slopes = np.linalg.inv(XtWsX[1:, 1:])
QM = beta_slopes @ np.linalg.solve(vcov_slopes, beta_slopes)
df_QM = len(beta_slopes)
p_QM = 1 - stats.chi2.cdf(QM, df_QM)
print(f"\n=== Omnibus moderator test (Wald) ===")
print(f"QM({df_QM}) = {QM:.3f}, p = {p_QM:.4f}")

# ── R2 analog (variance explained by subcategory) ─────────────────────────────
R2 = max(0.0, (tau2_0 - tau2_1) / tau2_0) if tau2_0 > 0 else 0.0
print(f"\nR2 analog (variance explained by subcategory): {R2*100:.1f}%")

# ── Per-subcategory predicted means ───────────────────────────────────────────
print(f"\n=== Per-subcategory predicted lambda ===")
pred_rows = []
for i, cat in enumerate(cats_ordered):
    x_row = np.zeros(len(beta1))
    x_row[0] = 1.0
    if i > 0:
        x_row[i] = 1.0
    pred_mean = float(x_row @ beta1)
    pred_se   = np.sqrt(x_row @ vcov1 @ x_row)
    n_ko      = (df['subcategory'] == cat).sum()
    pred_rows.append({
        'subcategory': cat,
        'pred_lambda': round(pred_mean, 4),
        'ci_lo': round(pred_mean - 1.96 * pred_se, 4),
        'ci_hi': round(pred_mean + 1.96 * pred_se, 4),
        'n_ko': int(n_ko)
    })
    print(f"  {cat:<35s}: {pred_mean:.4f} [{pred_mean-1.96*pred_se:.4f}, {pred_mean+1.96*pred_se:.4f}]  n={n_ko}")

pred_df = pd.DataFrame(pred_rows)

# ── Save ───────────────────────────────────────────────────────────────────────
summary_df = pd.DataFrame([{
    'model': 'intercept_only',
    'QM': None, 'QM_df': None, 'QMp': None,
    'tau2': round(tau2_0, 4), 'I2': round(I2_0, 1),
    'R2': None, 'n_KO': len(df), 'n_KO_unknown': (df['subcategory'].isna()).sum()
}, {
    'model': 'subcategory_moderator',
    'QM': round(QM, 3), 'QM_df': df_QM, 'QMp': round(p_QM, 4),
    'tau2': round(tau2_1, 4), 'I2': round(I2_1, 1),
    'R2': round(R2, 3), 'n_KO': len(df), 'n_KO_unknown': 121
}])
summary_df.to_csv(DATA / "subcategory_meta_analysis.csv", index=False)
pred_df.to_csv(DATA / "subcategory_predicted_lambda.csv", index=False)
print(f"\nSaved -> {DATA}/subcategory_meta_analysis.csv")
print(f"Saved -> {DATA}/subcategory_predicted_lambda.csv")

print(f"\n=== REPORT SUMMARY ===")
print(f"Overall mean lambda: {beta0[0]:.3f} [{beta0[0]-1.96*se0[0]:.3f}, {beta0[0]+1.96*se0[0]:.3f}]")
print(f"tau2={tau2_0:.4f}, I2={I2_0:.1f}%")
print(f"Subcategory moderator: QM({df_QM})={QM:.2f}, p={p_QM:.4f}")
print(f"R2={R2*100:.1f}%")
print(f"Original KW: H=8.71, p=0.1212 (unweighted, no sampling variances)")
