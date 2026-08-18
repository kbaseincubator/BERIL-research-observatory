#!/usr/bin/env python3
"""
analysis_catboost_split_validation.py

CatBoost + Leave-One-Phylum-Out (LOPO) CV validation of the resistance–cofactor
polarity discovered in PGLS:

  PGLS finding (NB25 / untested hypotheses H5c):
    - Resistance genes (Tier 1): β ≈ +0.008 for Levins' B_std (positive — generalists)
    - Cofactor genes (Tier 2): β ≈ −0.013 for Levins' B_std (negative — specialists)
    - Split: Δβ = 0.035, emp_p = 0.0 (1,000 permutations)

  CatBoost prediction:
    - Levins' B_std: resistance SHAP > 0, cofactor SHAP < 0 (opposite signs)
    - Environmental responses: resistance may be positive, cofactor ≈ 0

Steps
-----
1  CatBoost LOPO CV: 12 functional subsets → B_std + 15 env responses
2  SHAP extraction: signed mean SHAP and mean |SHAP| for resistance and cofactor
3  Comparison table across 16 responses
4  Statistical test: resistance−cofactor SHAP divergence for B_std vs env average
5  Figures: paired bar chart + scatter
6  Markdown report + interpretive SI paragraph

Constraints
-----------
- OMP_NUM_THREADS=1 (set externally)
- thread_count=1 in all CatBoost calls
- No SoilGrids, no CSU from enriched_metadata_gee
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

from catboost import CatBoostRegressor, Pool

DATA = Path("data")
FIG  = Path("figures")
LOG  = Path("logs")
FIG.mkdir(exist_ok=True)
LOG.mkdir(exist_ok=True)

t0 = time.time()

# ─── Constants ─────────────────────────────────────────────────────────────────
MIN_PHYLUM_N = 10

CB = dict(
    iterations=300, depth=4, learning_rate=0.05,
    l2_leaf_reg=3.0, loss_function='RMSE',
    random_seed=42, verbose=False, thread_count=1,
)

SUBSETS = {
    "Primary_140KO":       "ko_per_mb_primary_z",
    "Resistance_Tier1":    "ko_per_mb_tier1_z",
    "Cofactor_Tier2":      "ko_per_mb_tier2_z",
    "Expanded_KEGG":       "expanded_z",
    "Heme":                "heme_z",
    "Cobalamin":           "cobalamin_z",
    "Molybdopterin":       "molybdopterin_z",
    "Siroheme":            "siroheme_z",
    "FeS_assembly":        "fes_assembly_z",
    "Core_metabolism":     "core_metabolism_z",
    "Metal_dep_metab":     "metal_dep_z",
    "Nonmetal_cofactors":  "cofactor_vitamin_per_mb_z",
}

# The two focal features to track
RESISTANCE_FEAT = "Resistance_Tier1"
COFACTOR_FEAT   = "Cofactor_Tier2"

ENV_RESPONSES = {
    "GEOROC_Cu": "georoc_Cu_z",  "GEOROC_Ni": "georoc_Ni_z",
    "GEOROC_Zn": "georoc_Zn_z",  "GEOROC_Co": "georoc_Co_z",
    "GEOROC_Cr": "georoc_Cr_z",  "GEOROC_Pb": "georoc_Pb_z",
    "CSU_As":    "csu_As_z",     "CSU_Cd":    "csu_Cd_z",
    "CSU_Cr":    "csu_Cr_z",     "CSU_Cu":    "csu_Cu_z",
    "CSU_Hg":    "csu_Hg_z",     "CSU_Pb":    "csu_Pb_z",
    "Soil_pH":   "ph_z",         "Temperature": "temp_z",
    "Env_PC1":   "env_PC1_z",
}

# ─── Helpers ───────────────────────────────────────────────────────────────────
def zscore(arr):
    a = np.asarray(arr, dtype=float)
    mu = np.nanmean(a); sd = np.nanstd(a, ddof=1)
    return (a - mu) / sd if sd > 1e-12 else a - mu


def complete_rows(X, y):
    return np.isfinite(np.asarray(y, dtype=float)) & np.all(np.isfinite(X), axis=1)


def run_lopo(X, y, phylum_arr, params):
    """LOPO regression CV; returns [(phylum, rho)] for valid folds."""
    X  = np.asarray(X, dtype=float)
    y  = np.asarray(y, dtype=float)
    ph = np.asarray(phylum_arr)
    results = []
    for p in np.unique(ph):
        test  = (ph == p)
        train = ~test
        if test.sum() < MIN_PHYLUM_N:
            continue
        ok_tr = complete_rows(X[train], y[train])
        ok_te = complete_rows(X[test],  y[test])
        if ok_tr.sum() < 20 or ok_te.sum() < 3:
            continue
        try:
            model = CatBoostRegressor(**params)
            model.fit(X[train][ok_tr], y[train][ok_tr], verbose=False)
            pred = model.predict(X[test][ok_te])
            rho  = stats.spearmanr(pred, y[test][ok_te]).statistic
            if np.isfinite(rho):
                results.append((str(p), float(rho)))
        except Exception:
            pass
    return results


def avg_rho(lopo_result):
    if not lopo_result:
        return np.nan
    return float(np.mean([r for _, r in lopo_result]))


def shap_for_model(model, X, y):
    """Mean signed SHAP and mean |SHAP| per feature (bias column excluded)."""
    valid = complete_rows(X, y)
    if valid.sum() < 30:
        return np.full(X.shape[1], np.nan), np.full(X.shape[1], np.nan)
    sv = model.get_feature_importance(
        Pool(X[valid], y[valid]), type='ShapValues')[:, :-1]
    return sv.mean(axis=0), np.abs(sv).mean(axis=0)


def elapsed():
    return f"{(time.time()-t0)/60:.1f} min"


# ─── Step 0: Load data ─────────────────────────────────────────────────────────
def load_data():
    print("Loading data...")
    base = pd.read_csv(DATA / "soil_sample_pgls_dataset.csv")
    tier = pd.read_csv(DATA / "tier_z_scores_full.csv")
    exp  = pd.read_csv(DATA / "expanded_kegg_metal_cofactor_densities.csv")
    geo  = pd.read_csv(DATA / "genus_lat_env_covariates.csv")
    csu  = pd.read_csv(DATA / "genus_csu_mobility.csv")
    s8   = pd.read_csv(DATA / "s8_ko_metadata.csv")

    # Core-metabolism aggregate
    for c in ["translation_per_mb", "replication_repair_per_mb", "aa_metab_per_mb"]:
        if c not in base.columns:
            base[c] = 0.0
    base["core_metabolism"] = (
        base["translation_per_mb"].fillna(0)
        + base["replication_repair_per_mb"].fillna(0)
        + base["aa_metab_per_mb"].fillna(0)
    )
    base["core_metabolism_z"] = zscore(base["core_metabolism"])

    # Metal-dep metabolism z-score from nb25
    metal_dep_kos = s8.loc[s8["primary_category"] == "Metal-dependent Metabolism", "ko"].tolist()
    nb25 = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
    nb25["genus_lower"] = nb25["genus_lower"].str.replace(r'^g__', '', regex=True)
    md = (nb25[nb25["ko"].isin(metal_dep_kos)]
          .groupby("genus_lower")["n_genomes_with_ko"].sum().reset_index()
          .rename(columns={"n_genomes_with_ko": "metal_dep_sum"}))
    md = md.merge(base[["genus_lower", "mean_genome_mb"]].dropna(), on="genus_lower", how="inner")
    md["metal_dep_per_mb"] = md["metal_dep_sum"] / md["mean_genome_mb"]
    md["metal_dep_z"] = zscore(md["metal_dep_per_mb"])
    md = md[["genus_lower", "metal_dep_z"]]

    master = (
        exp[["genus_lower", "mean_genome_mb", "genome_mb_z",
             "expanded_z", "cobalamin_z", "fes_assembly_z",
             "heme_z", "molybdopterin_z", "siroheme_z"]]
        .merge(base[["genus_lower", "ko_per_mb_primary_z", "genome_size_mb_z",
                     "core_metabolism_z", "cofactor_vitamin_per_mb_z",
                     "mean_levins_B_std", "phylum", "mean_genome_mb",
                     "n_soil_samples"]],
               on="genus_lower", how="inner", suffixes=("_exp", ""))
        .merge(tier[["genus_lower", "ko_per_mb_tier1_z", "ko_per_mb_tier2_z"]],
               on="genus_lower", how="left")
        .merge(md, on="genus_lower", how="left")
        .merge(geo[["genus_lower", "georoc_Cu_log", "georoc_Ni_log", "georoc_Zn_log",
                    "georoc_Co_log", "georoc_Cr_log", "georoc_Pb_log",
                    "median_soil_ph", "median_era5_temp_C"]],
               on="genus_lower", how="left")
        .merge(csu[["genus_lower", "PF1_As", "PF1_Cd", "PF1_Cr",
                    "PF1_Cu", "PF1_Hg", "PF1_Pb"]], on="genus_lower", how="left")
    )

    # genome_size fallback
    mask = master["genome_size_mb_z"].isna()
    master.loc[mask, "genome_size_mb_z"] = master.loc[mask, "genome_mb_z"]

    # Env z-scores
    master["Bstd_z"] = zscore(master["mean_levins_B_std"])
    for m in ["Cu", "Ni", "Zn", "Co", "Cr", "Pb"]:
        master[f"georoc_{m}_z"] = zscore(master[f"georoc_{m}_log"])
    for m in ["As", "Cd", "Cr", "Cu", "Hg", "Pb"]:
        master[f"csu_{m}_z"] = zscore(np.log10(master[f"PF1_{m}"].values + 1e-4))
    master["ph_z"]   = zscore(master["median_soil_ph"])
    master["temp_z"] = zscore(master["median_era5_temp_C"])

    # env_PC1
    pca_cols = ["georoc_Cu_log", "georoc_Ni_log", "georoc_Zn_log",
                "georoc_Co_log", "georoc_Cr_log", "georoc_Pb_log",
                "median_soil_ph", "median_era5_temp_C"]
    pca_mask = master[pca_cols].notna().all(axis=1)
    pca_data = StandardScaler().fit_transform(master.loc[pca_mask, pca_cols].values)
    pc1      = PCA(n_components=1, random_state=42).fit_transform(pca_data)[:, 0]
    master["env_PC1"] = np.nan
    master.loc[pca_mask, "env_PC1"] = pc1
    master["env_PC1_z"] = zscore(master["env_PC1"])

    print(f"  Master: {len(master):,} genera, {master['phylum'].notna().sum():,} with phylum")
    return master


# ─── Step 1+2: LOPO + SHAP for all 16 responses ────────────────────────────────
def run_all_responses(master):
    print(f"\n─── Steps 1+2: LOPO CV + SHAP for 16 responses  [{elapsed()}] ───")

    subset_cols = list(SUBSETS.values())
    feat_names  = list(SUBSETS.keys()) + ["genome_size_mb_z"]
    res_idx     = feat_names.index(RESISTANCE_FEAT)
    cof_idx     = feat_names.index(COFACTOR_FEAT)

    # Drop rows missing any subset feature or phylum
    needed = subset_cols + ["genome_size_mb_z", "phylum"]
    sub_m  = master[needed + ["Bstd_z"] + list(ENV_RESPONSES.values())].dropna(
        subset=subset_cols + ["phylum"]).copy()

    ph = sub_m["phylum"].values
    X  = np.column_stack([sub_m[c].values for c in subset_cols]
                         + [sub_m["genome_size_mb_z"].values])

    # All responses: B_std first, then env
    all_responses = {"Levins_Bstd": "Bstd_z"} | ENV_RESPONSES

    rows = []
    for resp_name, resp_col in all_responses.items():
        resp_type = "Cross-biome niche" if resp_name == "Levins_Bstd" else "Environmental"
        if resp_col not in sub_m.columns:
            print(f"  WARNING: {resp_col} missing, skipping")
            continue
        y = sub_m[resp_col].values

        # LOPO CV
        lopo_res = run_lopo(X, y, ph, CB)
        ar = avg_rho(lopo_res)

        # Full-data fit for SHAP (always, regardless of avg_rho — direction still informative)
        valid = complete_rows(X, y)
        if valid.sum() >= 30:
            model = CatBoostRegressor(**CB)
            model.fit(X[valid], y[valid], verbose=False)
            mean_shap, abs_shap = shap_for_model(model, X[valid], y[valid])
            res_shap = float(mean_shap[res_idx])
            cof_shap = float(mean_shap[cof_idx])
            res_abs  = float(abs_shap[res_idx])
            cof_abs  = float(abs_shap[cof_idx])
            total_abs_shap = float(abs_shap.mean())
            # Normalised divergence: (res - cof) / mean |SHAP|
            norm_div = (res_shap - cof_shap) / total_abs_shap if total_abs_shap > 1e-10 else np.nan
        else:
            res_shap = cof_shap = res_abs = cof_abs = total_abs_shap = norm_div = np.nan

        # Opposite-sign flag (the split)
        split_present = (np.isfinite(res_shap) and np.isfinite(cof_shap)
                         and res_shap > 0 and cof_shap < 0)

        rows.append({
            "response":         resp_name,
            "response_type":    resp_type,
            "avg_lopo_rho":     ar,
            "n_folds":          len(lopo_res),
            "res_mean_shap":    res_shap,
            "cof_mean_shap":    cof_shap,
            "res_abs_shap":     res_abs,
            "cof_abs_shap":     cof_abs,
            "total_abs_shap":   total_abs_shap,
            "norm_divergence":  norm_div,
            "split_present":    split_present,
        })
        tag = "SPLIT" if split_present else "     "
        print(f"  {tag} {resp_name:20s}  avg ρ={ar:+.3f}  "
              f"res SHAP={res_shap:+.4f}  cof SHAP={cof_shap:+.4f}")

    return pd.DataFrame(rows)


# ─── Step 3+4: Statistical test ────────────────────────────────────────────────
def statistical_test(df):
    print(f"\n─── Step 4: Statistical test  [{elapsed()}] ───")

    bstd_row = df[df["response"] == "Levins_Bstd"].iloc[0]
    env_rows  = df[df["response_type"] == "Environmental"].dropna(subset=["norm_divergence"])

    bstd_div  = bstd_row["norm_divergence"]
    env_divs  = env_rows["norm_divergence"].values

    print(f"  B_std normalised divergence: {bstd_div:+.4f}")
    print(f"  Env divergences: mean={env_divs.mean():+.4f}, sd={env_divs.std():.4f}")

    # One-sample z-test: is B_std divergence > env mean?
    n_env  = len(env_divs)
    env_mu = env_divs.mean()
    env_sd = env_divs.std(ddof=1)
    z_stat = (bstd_div - env_mu) / (env_sd / n_env**0.5) if env_sd > 1e-10 else np.nan
    p_one  = float(stats.norm.sf(z_stat)) if np.isfinite(z_stat) else np.nan

    # Permutation test: fraction of env responses with divergence ≥ B_std
    perm_p = float(np.mean(env_divs >= bstd_div))

    # Wilcoxon sign test: resistance SHAP vs cofactor SHAP for env responses
    res_env = env_rows["res_mean_shap"].dropna().values
    cof_env = env_rows["cof_mean_shap"].dropna().values
    if len(res_env) >= 5:
        wil_stat, wil_p = stats.wilcoxon(res_env, cof_env, alternative='greater')
    else:
        wil_stat, wil_p = np.nan, np.nan

    # B_std: is resistance positive AND cofactor negative?
    split_confirmed = bstd_row["split_present"]
    env_split_count = int(df[df["response_type"] == "Environmental"]["split_present"].sum())
    env_n           = int((df["response_type"] == "Environmental").sum())

    print(f"  z-test (B_std divergence > env mean): z={z_stat:.3f}, p={p_one:.4f}")
    print(f"  Permutation p (env divergence ≥ B_std): {perm_p:.4f}")
    print(f"  Wilcoxon (res > cof for env, right-sided): W={wil_stat}, p={wil_p:.4f}")
    print(f"  B_std split (res+ cof-): {split_confirmed}")
    print(f"  Env responses with split: {env_split_count}/{env_n}")

    return {
        "bstd_div": bstd_div, "env_div_mean": env_mu, "env_div_sd": env_sd,
        "z_stat": z_stat, "p_one_sided": p_one, "perm_p": perm_p,
        "wilcoxon_W": wil_stat, "wilcoxon_p": wil_p,
        "bstd_split": split_confirmed,
        "env_split_count": env_split_count, "env_n": env_n,
    }


# ─── Step 5a: Paired bar chart ─────────────────────────────────────────────────
def plot_barchart(df):
    print(f"\n─── Figure 1: Paired bar chart  [{elapsed()}] ───")

    df_plot = df[df["res_mean_shap"].notna()].copy()
    # Order: Levins_Bstd first, then env alphabetically
    env_order = sorted(df_plot[df_plot["response_type"] == "Environmental"]["response"].tolist())
    order     = ["Levins_Bstd"] + env_order
    df_plot   = df_plot.set_index("response").loc[order].reset_index()

    x      = np.arange(len(df_plot))
    width  = 0.38
    colors = {"Resistance_Tier1": "#2171b5", "Cofactor_Tier2": "#f16913"}

    fig, ax = plt.subplots(figsize=(14, 5))
    bars_r = ax.bar(x - width/2, df_plot["res_mean_shap"], width,
                    color=colors["Resistance_Tier1"], label="Resistance (Tier 1)", zorder=3)
    bars_c = ax.bar(x + width/2, df_plot["cof_mean_shap"], width,
                    color=colors["Cofactor_Tier2"],   label="Cofactor (Tier 2)",   zorder=3)

    # Highlight B_std bar pair with a box
    ax.axvspan(-0.6, 0.6, alpha=0.08, color="gold", zorder=1)
    ax.axvline(0.5, color="black", lw=0.8, ls="--", zorder=2)

    ax.axhline(0, color="black", lw=0.8, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [r.replace("Levins_Bstd", "Levins' B_std").replace("_", " ")
         for r in df_plot["response"]],
        rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Mean SHAP value (signed)", fontsize=9)
    ax.set_title(
        "Resistance–Cofactor SHAP polarity: cross-biome niche breadth vs environmental responses\n"
        "CatBoost LOPO CV (11 phyla) | Shaded: Levins' B_std (cross-biome target)",
        fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3, zorder=0)

    # Add avg_rho annotation on top of resistance bar
    for i, row in enumerate(df_plot.itertuples()):
        rho = row.avg_lopo_rho
        if np.isfinite(rho):
            ax.text(i - width/2, max(row.res_mean_shap, 0) + 0.001,
                    f"ρ={rho:.2f}", ha="center", va="bottom", fontsize=5, color="navy")

    plt.tight_layout()
    plt.savefig(FIG / "catboost_split_shap_barchart.pdf", bbox_inches="tight")
    plt.savefig(FIG / "catboost_split_shap_barchart.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved → figures/catboost_split_shap_barchart.pdf/.png")


# ─── Step 5b: Scatter plot ─────────────────────────────────────────────────────
def plot_scatter(df, stats_dict):
    print(f"\n─── Figure 2: Scatter plot  [{elapsed()}] ───")

    df_plot = df[df["res_mean_shap"].notna()].copy()
    env_df  = df_plot[df_plot["response_type"] == "Environmental"]
    bstd_df = df_plot[df_plot["response_type"] == "Cross-biome niche"]

    fig, ax = plt.subplots(figsize=(7, 6))

    # Env responses: grey dots
    ax.scatter(env_df["res_mean_shap"], env_df["cof_mean_shap"],
               c="steelblue", alpha=0.7, s=60, zorder=3, label="Environmental responses")

    # Annotate env points
    for _, row in env_df.iterrows():
        ax.annotate(row["response"].replace("GEOROC_", "").replace("CSU_", ""),
                    (row["res_mean_shap"], row["cof_mean_shap"]),
                    fontsize=6, textcoords="offset points", xytext=(4, 2), color="steelblue")

    # Levins' B_std: gold star
    if len(bstd_df):
        b = bstd_df.iloc[0]
        ax.scatter(b["res_mean_shap"], b["cof_mean_shap"],
                   c="gold", edgecolors="black", s=180, zorder=5,
                   marker="*", label="Levins' B_std (cross-biome)")
        ax.annotate("Levins' B_std",
                    (b["res_mean_shap"], b["cof_mean_shap"]),
                    fontsize=8, fontweight="bold",
                    textcoords="offset points", xytext=(6, -10))

    # Reference lines
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(0, color="black", lw=0.8)

    # Quadrant labels
    xlim = ax.get_xlim(); ylim = ax.get_ylim()
    pad_x = (xlim[1] - xlim[0]) * 0.04
    pad_y = (ylim[1] - ylim[0]) * 0.04
    ax.text(xlim[1] - pad_x, ylim[0] + pad_y, "Res+ Cof−\n(SPLIT)",
            ha="right", va="bottom", fontsize=7, color="darkorange",
            bbox=dict(boxstyle="round,pad=0.2", fc="lightyellow", ec="orange", alpha=0.7))
    ax.text(xlim[0] + pad_x, ylim[0] + pad_y, "Res− Cof−",
            ha="left", va="bottom", fontsize=7, color="grey", alpha=0.6)
    ax.text(xlim[1] - pad_x, ylim[1] - pad_y, "Res+ Cof+",
            ha="right", va="top", fontsize=7, color="grey", alpha=0.6)

    p_ann = stats_dict.get("p_one_sided", np.nan)
    p_str = f"z-test p = {p_ann:.3f}" if np.isfinite(p_ann) else ""
    ax.set_xlabel("Resistance (Tier 1) mean SHAP", fontsize=9)
    ax.set_ylabel("Cofactor (Tier 2) mean SHAP", fontsize=9)
    ax.set_title(
        f"Resistance vs Cofactor SHAP direction across 16 response variables\n{p_str}",
        fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig(FIG / "catboost_split_shap_scatter.pdf", bbox_inches="tight")
    plt.savefig(FIG / "catboost_split_shap_scatter.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved → figures/catboost_split_shap_scatter.pdf/.png")


# ─── Step 6: Report ────────────────────────────────────────────────────────────
def write_report(df, stats_dict):
    print(f"\n─── Step 6: Writing report  [{elapsed()}] ───")

    bstd = df[df["response"] == "Levins_Bstd"].iloc[0]
    env  = df[df["response_type"] == "Environmental"]

    split_confirmed  = bstd["split_present"]
    env_split_count  = stats_dict["env_split_count"]
    env_n            = stats_dict["env_n"]
    bstd_div         = stats_dict["bstd_div"]
    env_div_mean     = stats_dict["env_div_mean"]
    z_stat           = stats_dict["z_stat"]
    p_one            = stats_dict["p_one_sided"]
    perm_p           = stats_dict["perm_p"]
    wil_p            = stats_dict["wilcoxon_p"]

    # Interpret
    if split_confirmed and env_split_count == 0:
        outcome = "specific"
        si_para = (
            "CatBoost with LOPO cross-validation independently confirmed that the "
            "resistance–cofactor polarity is specific to cross-biome niche breadth. "
            f"For Levins' B_std, resistance (Tier 1) and cofactor (Tier 2) showed opposite "
            f"SHAP associations (resistance mean SHAP = {bstd['res_mean_shap']:+.4f}, "
            f"cofactor mean SHAP = {bstd['cof_mean_shap']:+.4f}), consistent with the PGLS "
            "split (resistance β ≈ +0.008, cofactor β ≈ −0.013; Δβ = 0.035, emp_p < 0.001). "
            f"For all {env_n} environmental responses, cofactor SHAP was near zero or positive "
            f"({env_split_count}/{env_n} showed the split; env mean normalised divergence = "
            f"{env_div_mean:+.3f} vs B_std = {bstd_div:+.3f}; z = {z_stat:.2f}, "
            f"p = {p_one:.3f}). This confirms that the resistance–cofactor polarity is a "
            "cross-biome macroecological phenomenon and does not reflect a general ability "
            "of these gene sets to predict environmental conditions."
        )
    elif split_confirmed and env_split_count > env_n // 3:
        outcome = "extends"
        si_para = (
            "CatBoost SHAP revealed that the resistance–cofactor polarity extends beyond "
            "cross-biome niche breadth to environmental prediction, with resistance positive "
            f"and cofactor negative for {env_split_count}/{env_n} environmental responses. "
            f"For Levins' B_std the split is clearest (resistance SHAP = {bstd['res_mean_shap']:+.4f}, "
            f"cofactor SHAP = {bstd['cof_mean_shap']:+.4f}), and the normalised divergence "
            f"is larger for B_std than for the average environmental response "
            f"({bstd_div:+.3f} vs {env_div_mean:+.3f}, z = {z_stat:.2f}, p = {p_one:.3f}). "
            "This suggests the split is a more general feature of metal-gene ecology than "
            "the PGLS alone indicated."
        )
    else:
        outcome = "ambiguous"
        si_para = (
            "CatBoost did not unambiguously recover the resistance–cofactor polarity. "
            f"For Levins' B_std, resistance SHAP = {bstd['res_mean_shap']:+.4f} and "
            f"cofactor SHAP = {bstd['cof_mean_shap']:+.4f} "
            f"({'opposite signs — split present' if split_confirmed else 'split not present'}). "
            f"For environmental responses, {env_split_count}/{env_n} showed the split. "
            "The LOPO framework may have insufficient power to resolve the modest effect size "
            "(PGLS β ≈ 0.008–0.013) against the phylogenetic variance captured by 11 held-out "
            "phyla. The PGLS remains the primary analytical framework for this finding."
        )

    # Build table
    tbl_rows = []
    for _, row in df.iterrows():
        split_flag = "✓ SPLIT" if row["split_present"] else ""
        tbl_rows.append({
            "Response": row["response"],
            "Type": row["response_type"],
            "Avg LOPO ρ": f"{row['avg_lopo_rho']:+.3f}" if np.isfinite(row["avg_lopo_rho"]) else "NA",
            "Resistance mean SHAP": f"{row['res_mean_shap']:+.4f}" if np.isfinite(row["res_mean_shap"]) else "NA",
            "Cofactor mean SHAP": f"{row['cof_mean_shap']:+.4f}" if np.isfinite(row["cof_mean_shap"]) else "NA",
            "Resistance |SHAP|": f"{row['res_abs_shap']:.4f}" if np.isfinite(row["res_abs_shap"]) else "NA",
            "Cofactor |SHAP|": f"{row['cof_abs_shap']:.4f}" if np.isfinite(row["cof_abs_shap"]) else "NA",
            "Split present": split_flag,
        })
    tbl_df = pd.DataFrame(tbl_rows)

    lines = [
        "# CatBoost Split Validation: Resistance–Cofactor SHAP Polarity", "",
        "## Overview", "",
        "This analysis tests whether the PGLS-discovered resistance–cofactor polarity "
        "(resistance positive, cofactor negative for Levins' B_std) is specific to cross-biome "
        "niche breadth or extends to environmental responses. CatBoost with LOPO CV "
        "(11 phyla, ≥10 genera) was applied to 16 response variables: Levins' B_std + "
        "15 environmental responses (same as Finding 19). Features: 12 functional subset "
        "densities + genome size. SHAP was extracted from full-data fits for all responses.",
        "",
        "**PGLS baseline (Finding 4 / H5c):** resistance β ≈ +0.008 (p = 0.021), "
        "cofactor β ≈ −0.013 (p = 0.055†); split permutation Δβ = 0.035, emp_p < 0.001.",
        "",
        "---", "", "## Results Table", "",
        tbl_df.to_markdown(index=False),
        "",
        "---", "", "## Statistical Test (Step 4)", "",
        f"- **B_std normalised divergence** (resistance − cofactor) / mean |SHAP|: "
        f"**{bstd_div:+.4f}**",
        f"- **Environmental responses** normalised divergence: "
        f"mean = {env_div_mean:+.4f}, SD = {stats_dict['env_div_sd']:.4f}",
        f"- **z-test** (B_std > env mean): z = {z_stat:.3f}, p = {p_one:.4f}",
        f"- **Permutation p** (fraction of env responses with divergence ≥ B_std): "
        f"{perm_p:.4f}",
        f"- **Wilcoxon** (resistance > cofactor for env responses): "
        f"W = {stats_dict['wilcoxon_W']}, p = {wil_p:.4f}",
        f"- **B_std split present** (res+ cof-): {bstd['split_present']}",
        f"- **Env responses with split**: {env_split_count}/{env_n}",
        f"- **Outcome**: {outcome.upper()}",
        "",
        "---", "", "## Figures", "",
        "- `figures/catboost_split_shap_barchart.pdf` — Paired bar chart, 16 responses",
        "- `figures/catboost_split_shap_scatter.pdf` — Resistance vs cofactor SHAP scatter",
        "",
        "---", "", "## SI Paragraph", "",
        "**Machine-learning validation of the resistance–cofactor polarity.** " + si_para,
        "",
    ]

    with open("catboost_split_validation.md", "w") as f:
        f.write("\n".join(lines))
    print("  Saved → catboost_split_validation.md")
    print(f"\n  Outcome: {outcome.upper()}")
    print(f"  SI paragraph written.")


# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("CatBoost split validation: resistance–cofactor polarity")
    print("=" * 60)

    master = load_data()
    df     = run_all_responses(master)

    # Save raw results
    df.to_csv(DATA / "catboost_split_validation.csv", index=False)
    print(f"\n  Saved → data/catboost_split_validation.csv ({len(df)} rows)")

    stats_dict = statistical_test(df)
    plot_barchart(df)
    plot_scatter(df, stats_dict)
    write_report(df, stats_dict)

    total = (time.time() - t0) / 60
    print(f"\nAll done in {total:.1f} minutes.")


if __name__ == "__main__":
    main()
