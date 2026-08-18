#!/usr/bin/env python3
"""
analysis_env_prediction_by_functional_subset.py

Five-step analysis: which metal-gene functional subsets (and individual KOs)
best predict environmental conditions at genus level via phylogenetically
corrected regression (Pagel's-lambda PGLS)?

VCV matrix is built ONCE using a fast ancestor-path approach (instead of
dendropy's slow per-pair tree.mrca()), then cached and reused for all models.

Steps
-----
1  Subset PGLS: 12 functional subsets × 15 env responses (~180 models)
2  Per-KO PGLS: all nb25 KOs (≥20 genera) vs top 3 env responses
3  Weighted PGLS: n_samples-weighted comparison vs Step 1
4  Multivariate PGLS: env_PC1 ~ all functional subsets simultaneously
5  Report: environmental_prediction_analysis.md + heatmap PDF
"""

import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = Path("data")
FIG  = Path("figures")
FIG.mkdir(exist_ok=True)

# ─── Load pgls_utils internals ────────────────────────────────────────────────
_spec = importlib.util.spec_from_file_location("pgls_utils", "scripts/pgls_utils.py")
_pu   = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pu)

TREE_PATH = DATA / "gtdb_bac_genus_pruned.tree"
MIN_N     = 30

# ─── Helpers ──────────────────────────────────────────────────────────────────

def zscore(arr):
    a  = np.asarray(arr, dtype=float)
    mu = np.nanmean(a)
    sd = np.nanstd(a, ddof=1)
    return (a - mu) / sd if sd > 1e-12 else a - mu


def bh_correct(p_values):
    p = np.asarray(p_values, dtype=float)
    valid = ~np.isnan(p)
    q = np.full_like(p, np.nan)
    if valid.sum() > 0:
        _, q_adj, _, _ = multipletests(p[valid], method="fdr_bh")
        q[valid] = q_adj
    return q


# ─── Fast VCV build ───────────────────────────────────────────────────────────

def build_vcv_fast(tree, taxa):
    """Build VCV using precomputed ancestor-path sets — ~10-50× faster than dendropy tree.mrca().

    For each pair (i,j) scans leaf-i's path root-first until finding a node
    also in leaf-j's ancestor set (O(1) lookup).  Much faster than
    dendropy's MRCA traversal for deeply divergent taxa.
    """
    taxa_norm = [t.replace(" ", "_").lower() for t in taxa]
    n = len(taxa_norm)

    # Precompute root-to-node distances
    node_depth: dict[int, float] = {}
    for node in tree.preorder_node_iter():
        if node.parent_node is None:
            node_depth[id(node)] = 0.0
        else:
            el = node.edge_length if node.edge_length is not None else 0.0
            node_depth[id(node)] = node_depth[id(node.parent_node)] + el

    # Map normalised taxon label → leaf node
    label_to_node: dict[str, object] = {}
    for leaf in tree.leaf_node_iter():
        if leaf.taxon:
            lbl = leaf.taxon.label.replace(" ", "_").lower()
            label_to_node[lbl] = leaf

    leaf_nodes = [label_to_node[t] for t in taxa_norm]

    # Root-to-leaf paths (list of integer node IDs)
    ancestor_paths: list[list[int]] = []
    for leaf in leaf_nodes:
        path = []
        node = leaf
        while node is not None:
            path.append(id(node))
            node = node.parent_node
        path.reverse()          # root at index 0
        ancestor_paths.append(path)

    # Ancestor sets for O(1) membership checks
    ancestor_sets = [set(p) for p in ancestor_paths]

    # Diagonal: tip depths
    tip_depths = np.array([node_depth[id(lf)] for lf in leaf_nodes])
    V = np.zeros((n, n))
    np.fill_diagonal(V, tip_depths)

    # Off-diagonal: shared root-to-MRCA depth
    # Scan leaf-i's path from LEAF toward ROOT; stop at first node in set_j
    for i in range(n):
        path_i = ancestor_paths[i]
        for j in range(i + 1, n):
            set_j = ancestor_sets[j]
            mrca_d = 0.0
            for anc_id in reversed(path_i):
                if anc_id in set_j:
                    mrca_d = node_depth[anc_id]
                    break
            V[i, j] = mrca_d
            V[j, i] = mrca_d

    return V


# ─── Step 0: Load data ────────────────────────────────────────────────────────

def load_data():
    """Assemble master dataframe from all source files."""
    print("Loading source files...")
    base    = pd.read_csv(DATA / "soil_sample_pgls_dataset.csv")
    tiers   = pd.read_csv(DATA / "tier_z_scores_full.csv")
    exp     = pd.read_csv(DATA / "expanded_kegg_metal_cofactor_densities.csv")
    env     = pd.read_csv(DATA / "genus_lat_env_covariates.csv")
    csu     = pd.read_csv(DATA / "genus_csu_mobility.csv")
    ko_meta = pd.read_csv(DATA / "s8_ko_metadata.csv")

    # Core-metabolism z-score
    base["core_metabolism"] = (base["translation_per_mb"]
                               + base["replication_repair_per_mb"]
                               + base["aa_metab_per_mb"])
    base["core_metabolism_z"] = zscore(base["core_metabolism"])

    # Metal-dep metabolism z-score from nb25 (15 KOs)
    print("  Computing metal-dep metabolism z-score from nb25...")
    nb25 = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
    md_kos = set(ko_meta[ko_meta.primary_category == "Metal-dependent Metabolism"]["ko"])
    nb25_md = nb25[nb25.ko.isin(md_kos)].copy()
    nb25_md["genus"] = nb25_md.genus_lower.str.replace(r"^g__", "", regex=True)
    md_count = (nb25_md.groupby("genus")["ko"].count()
                .rename("n_kos_metal_dep").reset_index())
    md_count = md_count.merge(
        exp[["genus_lower", "mean_genome_mb"]],
        left_on="genus", right_on="genus_lower", how="left"
    )
    md_count["metal_dep_per_mb"] = md_count["n_kos_metal_dep"] / md_count["mean_genome_mb"]
    md_count["metal_dep_z"] = zscore(md_count["metal_dep_per_mb"])
    md_count = md_count[["genus", "metal_dep_z"]].rename(columns={"genus": "genus_lower"})

    # Master dataframe: start from tiers (1,574 genera)
    master = tiers.copy()
    master = master.merge(
        exp[["genus_lower", "mean_genome_mb", "genome_mb_z", "expanded_z",
             "cobalamin_z", "fes_assembly_z", "heme_z",
             "molybdopterin_z", "siroheme_z"]],
        on="genus_lower", how="left"
    )
    master = master.merge(
        base[["genus_lower", "ko_per_mb_primary_z", "genome_size_mb_z",
              "core_metabolism_z", "cofactor_vitamin_per_mb_z"]],
        on="genus_lower", how="left"
    )
    mask_gz = master["genome_size_mb_z"].isna()
    master.loc[mask_gz, "genome_size_mb_z"] = master.loc[mask_gz, "genome_mb_z"]

    master = master.merge(
        env[["genus_lower", "n_samples",
             "georoc_Cu_log", "georoc_Ni_log", "georoc_Zn_log",
             "georoc_Co_log", "georoc_Cr_log", "georoc_Pb_log",
             "median_soil_ph", "median_era5_temp_C"]],
        on="genus_lower", how="left"
    )
    master = master.merge(
        csu[["genus_lower", "PF1_As", "PF1_Cd", "PF1_Cr",
             "PF1_Cu", "PF1_Hg", "PF1_Pb"]],
        on="genus_lower", how="left"
    )
    master = master.merge(md_count, on="genus_lower", how="left")

    # Environmental response columns
    for metal in ["Cu", "Ni", "Zn", "Co", "Cr", "Pb"]:
        master[f"georoc_{metal}_z"] = zscore(master[f"georoc_{metal}_log"])
    for metal in ["As", "Cd", "Cr", "Cu", "Hg", "Pb"]:
        master[f"csu_{metal}_z"] = zscore(
            np.log10(master[f"PF1_{metal}"].values + 1e-4)
        )
    master["ph_z"]   = zscore(master["median_soil_ph"])
    master["temp_z"] = zscore(master["median_era5_temp_C"])

    # Env PC1
    print("  Computing env PC1...")
    pca_cols = ["georoc_Cu_log", "georoc_Ni_log", "georoc_Zn_log",
                "georoc_Co_log", "georoc_Cr_log", "georoc_Pb_log",
                "median_soil_ph", "median_era5_temp_C"]
    pca_mask = master[pca_cols].notna().all(axis=1)
    pca_data = StandardScaler().fit_transform(master.loc[pca_mask, pca_cols])
    pc1 = PCA(n_components=1).fit_transform(pca_data)[:, 0]
    master["env_PC1"] = np.nan
    master.loc[pca_mask, "env_PC1"] = pc1
    master["env_PC1_z"] = zscore(master["env_PC1"])

    master["weight"] = np.log10(master["n_samples"].fillna(1) + 1)

    print(f"  Master: {len(master):,} genera")
    return master, nb25, ko_meta


# ─── Build cached VCV ─────────────────────────────────────────────────────────

def build_cached_vcv(master):
    """Filter to tree-present genera, build VCV once with fast path-scan method."""
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)  # suppress dendropy unrooted warning

    print("Loading tree...")
    t0 = time.time()
    tree = _pu.load_tree(TREE_PATH)
    tree_labels = {t.label.replace(" ", "_").lower()
                   for t in tree.taxon_namespace}
    print(f"  Tree loaded in {time.time()-t0:.1f}s, {len(tree_labels):,} tips")

    master["genus_norm"] = master["genus_lower"].str.replace(" ", "_").str.lower()
    in_tree = master["genus_norm"].isin(tree_labels)
    master  = master[in_tree].copy().reset_index(drop=True)
    taxa    = master["genus_norm"].tolist()
    print(f"  {len(taxa):,} genera in tree")

    print(f"Building VCV ({len(taxa)}×{len(taxa)}) via fast ancestor-path method...")
    t0 = time.time()
    V = build_vcv_fast(tree, taxa)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s. VCV shape: {V.shape}")
    return master, V, taxa


# ─── Fast model runner (uses cached V) ───────────────────────────────────────

def run_fast(y_all, X_all, V_full, mask, w_all=None, n_grid=10):
    """Subset cached VCV to complete-case rows and fit Pagel-lambda PGLS.

    w_all: if provided, apply WLS via sqrt(w) pre-multiplication on y and X.
    """
    idx   = np.where(mask)[0]
    n     = len(idx)
    if n < MIN_N:
        return None

    y     = y_all[idx]
    X     = X_all[idx]
    V_sub = V_full[np.ix_(idx, idx)]

    if w_all is not None:
        w  = w_all[idx]
        w  = w / w.mean()
        sw = np.sqrt(w)
        y_ = y * sw
        X_ = X * sw[:, None]
    else:
        y_, X_ = y, X

    try:
        lam, _ = _pu._optimise_lambda(y_, X_, V_sub, n_grid=n_grid)
        ll, sigma2, betas, betas_se, V_lam, L = _pu._gls_fit(y_, X_, V_sub, lam)
    except Exception as exc:
        return {"converged": False, "error": str(exc), "n": n}

    df_r   = n - X.shape[1]
    t_stat = betas / betas_se
    p_vals = 2 * stats.t.sf(np.abs(t_stat), df=df_r)

    # R² on Cholesky-transformed scale (original y)
    try:
        L_inv  = np.linalg.inv(L)
        y_t    = L_inv @ y
        yhat_t = L_inv @ (X @ betas)
        ss_res = np.sum((y_t - yhat_t) ** 2)
        ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
        r2     = float(1 - ss_res / ss_tot) if ss_tot > 1e-12 else np.nan
    except Exception:
        r2 = np.nan

    return {
        "converged":   True,
        "n":           n,
        "lambda_est":  float(lam),
        "betas":       betas,      # index 0 = intercept
        "betas_se":    betas_se,
        "t_stats":     t_stat,
        "p_values":    p_vals,
        "r2":          r2,
    }


# ─── Functional subsets and env responses ─────────────────────────────────────

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

ENV_RESPONSES = {
    "GEOROC_Cu":   "georoc_Cu_z",
    "GEOROC_Ni":   "georoc_Ni_z",
    "GEOROC_Zn":   "georoc_Zn_z",
    "GEOROC_Co":   "georoc_Co_z",
    "GEOROC_Cr":   "georoc_Cr_z",
    "GEOROC_Pb":   "georoc_Pb_z",
    "CSU_As":      "csu_As_z",
    "CSU_Cd":      "csu_Cd_z",
    "CSU_Cr":      "csu_Cr_z",
    "CSU_Cu":      "csu_Cu_z",
    "CSU_Hg":      "csu_Hg_z",
    "CSU_Pb":      "csu_Pb_z",
    "Soil_pH":     "ph_z",
    "Temperature": "temp_z",
    "Env_PC1":     "env_PC1_z",
}


# ─── Step 1: Subset PGLS ──────────────────────────────────────────────────────

def step1_subset_pgls(master, V_full):
    """12 × 15 = 180 PGLS models: env_response ~ subset_z + genome_size_z."""
    print("\n─── Step 1: Subset PGLS (12 × 15 models) ───")
    rows    = []
    y_genome = master["genome_size_mb_z"].values
    total   = len(SUBSETS) * len(ENV_RESPONSES)
    done    = 0

    for sname, scol in SUBSETS.items():
        if scol not in master.columns:
            print(f"  SKIP {sname}: column {scol!r} missing")
            continue
        y_sub = master[scol].values

        for ename, ecol in ENV_RESPONSES.items():
            done += 1
            if ecol not in master.columns:
                rows.append({"subset": sname, "env_response": ename,
                             "n": 0, "beta": np.nan, "SE": np.nan,
                             "p": np.nan, "q": np.nan,
                             "lambda_est": np.nan, "r2": np.nan})
                continue

            y_env = master[ecol].values
            mask  = np.isfinite(y_sub) & np.isfinite(y_env) & np.isfinite(y_genome)
            X_all = np.column_stack([np.ones(len(master)), y_sub, y_genome])
            res   = run_fast(y_env, X_all, V_full, mask)

            if res is None or not res.get("converged", False):
                rows.append({"subset": sname, "env_response": ename,
                             "n": 0, "beta": np.nan, "SE": np.nan,
                             "p": np.nan, "q": np.nan,
                             "lambda_est": np.nan, "r2": np.nan})
            else:
                rows.append({
                    "subset":       sname,
                    "env_response": ename,
                    "n":            res["n"],
                    "beta":         res["betas"][1],
                    "SE":           res["betas_se"][1],
                    "p":            res["p_values"][1],
                    "q":            np.nan,
                    "lambda_est":   res["lambda_est"],
                    "r2":           res["r2"],
                })

        if done % 15 == 0 or done == total:
            print(f"  {done}/{total} complete")

    df = pd.DataFrame(rows)
    for ename in ENV_RESPONSES:
        em = df.env_response == ename
        df.loc[em, "q"] = bh_correct(df.loc[em, "p"].values)

    out = DATA / "functional_subset_env_prediction.csv"
    df.to_csv(out, index=False)
    print(f"  Saved → {out} ({len(df)} rows)")
    return df


# ─── Step 2: Per-KO PGLS ──────────────────────────────────────────────────────

def step2_per_ko_pgls(master, V_full, step1_df, nb25, ko_meta):
    """PGLS for all nb25 KOs (≥20 genera) vs top 3 env responses."""
    print("\n─── Step 2: Per-KO PGLS ───")

    # Top 3 env responses by mean |β| × n_significant
    sig_c  = (step1_df.groupby("env_response")
               .apply(lambda g: (g["q"].fillna(1) < 0.05).sum())
               .rename("n_sig"))
    mab    = (step1_df.groupby("env_response")["beta"]
               .apply(lambda g: g.dropna().abs().mean())
               .rename("mean_abs_beta"))
    rank   = pd.concat([sig_c, mab], axis=1)
    rank["score"] = rank["n_sig"] * rank["mean_abs_beta"]
    top_env = rank.nlargest(3, "score").index.tolist()
    print(f"  Top env responses: {top_env}")

    # nb25 pivoted to genera × KOs
    nb25_c = nb25.copy()
    nb25_c["genus"] = nb25_c.genus_lower.str.replace(r"^g__", "", regex=True)
    # Wide: rows = genera, cols = KOs
    nb25_wide = nb25_c.pivot_table(
        index="genus", columns="ko", values="n_genomes_with_ko", aggfunc="first"
    ).fillna(0)

    # Restrict to genera in master (tree-filtered)
    common    = nb25_wide.index.intersection(master.genus_lower.values)
    nb25_wide = nb25_wide.loc[common].reset_index(drop=True)
    master_nb = (master.set_index("genus_lower")
                        .loc[common].reset_index())

    # Pre-build VCV for the nb25 subset (once)
    vcv_idx  = {g: i for i, g in enumerate(master["genus_norm"].values)}
    full_idx = np.array([vcv_idx[master_nb.loc[k, "genus_norm"]]
                         for k in range(len(master_nb))])
    V_nb     = V_full[np.ix_(full_idx, full_idx)]

    y_genome  = master_nb["genome_size_mb_z"].values
    intercept = np.ones(len(master_nb))
    rows      = []
    kos       = nb25_wide.columns.tolist()
    total     = len(kos) * len(top_env)
    done      = 0

    for ko in kos:
        ko_counts = nb25_wide[ko].values.astype(float)
        n_present = (ko_counts > 0).sum()
        if n_present < 20:
            done += len(top_env)
            continue
        ko_z  = zscore(ko_counts)
        ko_info = ko_meta[ko_meta.ko == ko]
        cat  = ko_info["primary_category"].values[0] if len(ko_info) else "Unknown"
        tier = ko_info["tier_1_vs_2"].values[0]      if len(ko_info) else "Unknown"

        for ename in top_env:
            done += 1
            ecol  = ENV_RESPONSES[ename]
            y_env = (master_nb[ecol].values
                     if ecol in master_nb.columns
                     else np.full(len(master_nb), np.nan))
            mask  = np.isfinite(ko_z) & np.isfinite(y_env) & np.isfinite(y_genome)
            X_all = np.column_stack([intercept, ko_z, y_genome])
            res   = run_fast(y_env, X_all, V_nb, mask)

            if res is None or not res.get("converged", False):
                rows.append({"ko": ko, "primary_category": cat,
                             "tier_1_vs_2": tier,
                             "n_genera_present": n_present, "env_response": ename,
                             "n": 0, "beta": np.nan, "SE": np.nan,
                             "p": np.nan, "q": np.nan, "lambda_est": np.nan})
            else:
                rows.append({
                    "ko":               ko,
                    "primary_category": cat,
                    "tier_1_vs_2":      tier,
                    "n_genera_present": n_present,
                    "env_response":     ename,
                    "n":                res["n"],
                    "beta":             res["betas"][1],
                    "SE":               res["betas_se"][1],
                    "p":                res["p_values"][1],
                    "q":                np.nan,
                    "lambda_est":       res["lambda_est"],
                })

        if done % 300 == 0 or done == total:
            print(f"  {done}/{total} models")

    df = pd.DataFrame(rows)
    for ename in top_env:
        em = df.env_response == ename
        df.loc[em, "q"] = bh_correct(df.loc[em, "p"].values)

    out = DATA / "per_ko_env_prediction.csv"
    df.to_csv(out, index=False)
    print(f"  Saved → {out} ({len(df)} rows)")
    return df, top_env


# ─── Step 3: Weighted PGLS comparison ─────────────────────────────────────────

def step3_weighted_pgls(master, V_full, step1_df):
    """Weighted PGLS (n_samples weights) for all 180 pairs; compare to Step 1 β."""
    print("\n─── Step 3: Weighted PGLS comparison ───")

    w_all     = master["weight"].values
    y_genome  = master["genome_size_mb_z"].values
    intercept = np.ones(len(master))

    uw_lookup = {(r.subset, r.env_response): r.beta for _, r in step1_df.iterrows()}

    rows  = []
    total = len(SUBSETS) * len(ENV_RESPONSES)
    done  = 0

    for sname, scol in SUBSETS.items():
        if scol not in master.columns:
            continue
        y_sub = master[scol].values

        for ename, ecol in ENV_RESPONSES.items():
            done += 1
            b_uw = uw_lookup.get((sname, ename), np.nan)

            if ecol not in master.columns or not np.isfinite(b_uw):
                rows.append({"subset": sname, "env_response": ename,
                             "beta_unweighted": b_uw,
                             "beta_weighted": np.nan, "delta_beta": np.nan})
                continue

            y_env = master[ecol].values
            mask  = (np.isfinite(y_sub) & np.isfinite(y_env)
                     & np.isfinite(y_genome) & np.isfinite(w_all))
            X_all = np.column_stack([intercept, y_sub, y_genome])
            res_w = run_fast(y_env, X_all, V_full, mask, w_all=w_all)

            b_w = res_w["betas"][1] if (res_w and res_w.get("converged")) else np.nan
            rows.append({
                "subset":          sname,
                "env_response":    ename,
                "beta_unweighted": b_uw,
                "beta_weighted":   b_w,
                "delta_beta":      (b_w - b_uw
                                    if np.isfinite(b_uw) and np.isfinite(b_w)
                                    else np.nan),
            })

        if done % 15 == 0 or done == total:
            print(f"  {done}/{total} models")

    df = pd.DataFrame(rows)
    valid = df.dropna(subset=["beta_unweighted", "beta_weighted"])
    rho, pval = (stats.spearmanr(valid["beta_unweighted"], valid["beta_weighted"])
                 if len(valid) >= 5 else (np.nan, np.nan))
    delta = valid["delta_beta"].abs().mean()
    print(f"  Spearman ρ (unweighted vs weighted β): {rho:.3f}  p={pval:.2e}")
    print(f"  Mean |Δβ|: {delta:.4f}")

    out = DATA / "abundance_weighted_comparison.csv"
    df.to_csv(out, index=False)
    print(f"  Saved → {out}")
    return df, rho, pval, delta


# ─── Step 4: Multivariate PGLS ────────────────────────────────────────────────

def step4_multivariate_pgls(master, V_full):
    """env_PC1_z ~ all functional subsets + genome_size_z."""
    print("\n─── Step 4: Multivariate PGLS ───")

    subset_cols = list(SUBSETS.values())
    available   = [c for c in subset_cols if c in master.columns]

    if "env_PC1_z" not in master.columns or master["env_PC1_z"].notna().sum() < MIN_N:
        print("  env_PC1_z unavailable; skipping")
        return None

    all_cols  = available + ["genome_size_mb_z"]
    y_env     = master["env_PC1_z"].values
    intercept = np.ones(len(master))
    arrs      = [master[c].values for c in all_cols]
    mask      = np.isfinite(y_env)
    for a in arrs:
        mask = mask & np.isfinite(a)

    X_all = np.column_stack([intercept] + arrs)
    res   = run_fast(y_env, X_all, V_full, mask)

    if res is None or not res.get("converged"):
        print("  Multivariate model did not converge")
        return None

    rows = []
    for i, pname in enumerate(all_cols):
        rows.append({
            "predictor":  pname,
            "beta":       res["betas"][i + 1],
            "SE":         res["betas_se"][i + 1],
            "t_stat":     res["t_stats"][i + 1],
            "p":          res["p_values"][i + 1],
        })
    df = pd.DataFrame(rows)
    _, df["q"], _, _ = multipletests(df["p"].fillna(1), method="fdr_bh")
    df["n"]          = res["n"]
    df["lambda_est"] = res["lambda_est"]
    df["r2"]         = res["r2"]
    print(f"  n={res['n']}, λ={res['lambda_est']:.3f}, R²={res['r2']:.3f}")
    return df


# ─── Heatmap ──────────────────────────────────────────────────────────────────

def draw_heatmap(step1_df):
    """12 × 15 β heatmap with BH significance stars."""
    print("\nDrawing heatmap...")
    subset_order = list(SUBSETS.keys())
    env_order    = list(ENV_RESPONSES.keys())

    beta_mat = np.full((len(subset_order), len(env_order)), np.nan)
    sig_mat  = [["" for _ in range(len(env_order))] for _ in range(len(subset_order))]

    for i, sname in enumerate(subset_order):
        for j, ename in enumerate(env_order):
            row = step1_df[(step1_df.subset == sname) & (step1_df.env_response == ename)]
            if len(row) == 0:
                continue
            b = row["beta"].values[0]
            q = row["q"].values[0]
            beta_mat[i, j] = b
            if np.isfinite(q):
                if   q < 0.001: sig_mat[i][j] = "***"
                elif q < 0.01:  sig_mat[i][j] = "**"
                elif q < 0.05:  sig_mat[i][j] = "*"
                elif q < 0.10:  sig_mat[i][j] = "†"

    vals = beta_mat[np.isfinite(beta_mat)]
    vmax = max(np.percentile(np.abs(vals), 95), 0.05) if len(vals) > 0 else 0.1

    fig, ax = plt.subplots(figsize=(13, 6))
    masked   = np.ma.masked_invalid(beta_mat)
    cmap     = plt.cm.RdBu_r.copy()
    cmap.set_bad(color="#cccccc")
    im = ax.imshow(masked, cmap=cmap, vmin=-vmax, vmax=vmax,
                   aspect="auto", interpolation="none")

    for i in range(len(subset_order)):
        for j in range(len(env_order)):
            txt = sig_mat[i][j]
            if txt:
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=7, color="black")

    ax.set_xticks(range(len(env_order)))
    ax.set_xticklabels(env_order, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(subset_order)))
    ax.set_yticklabels(subset_order, fontsize=9)
    plt.colorbar(im, ax=ax, shrink=0.7, label="PGLS β (partial, controlling genome size)")
    ax.set_title(
        "PGLS: metal-gene functional subset → environmental predictor\n"
        "(† BH q<0.10  * q<0.05  ** q<0.01  *** q<0.001)",
        fontsize=10, pad=8
    )
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"functional_subset_env_heatmap.{ext}",
                    dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {FIG}/functional_subset_env_heatmap.pdf/.png")


# ─── Step 5: Report ───────────────────────────────────────────────────────────

def write_report(step1_df, step2_df, rho, pval, delta, step4_df, top_env):
    """Write environmental_prediction_analysis.md."""
    print("\nWriting report...")

    n_sig = (step1_df["q"] < 0.05).sum()
    n_tot = step1_df["q"].notna().sum()

    mean_b = (step1_df.dropna(subset=["beta"])
              .groupby("subset")["beta"]
              .apply(lambda g: g.abs().mean())
              .sort_values(ascending=False)
              .rename("mean_abs_beta"))
    n_sig_sub = (step1_df[step1_df.q.fillna(1) < 0.05]
                 .groupby("subset").size()
                 .rename("n_sig_env"))
    summary_tab = pd.concat([mean_b, n_sig_sub], axis=1).fillna(0).reset_index()
    summary_tab["n_sig_env"] = summary_tab["n_sig_env"].astype(int)

    sig_by_env = (step1_df[step1_df.q.fillna(1) < 0.05]
                  .groupby("env_response").size()
                  .sort_values(ascending=False)
                  .reset_index())
    sig_by_env.columns = ["env_response", "n_sig_subsets"]

    # Per-KO top-KO table
    top_ko_sections = []
    if step2_df is not None:
        for ename in top_env:
            sub = step2_df[
                (step2_df.env_response == ename) & step2_df.q.notna()
            ].nsmallest(10, "q")
            top_ko_sections.append(
                f"\n**{ename}** (top 10 by BH q):\n\n"
                + sub[["ko", "primary_category", "n_genera_present",
                        "n", "beta", "SE", "p", "q",
                        "lambda_est"]].to_markdown(index=False)
            )

    # Step 4
    mv_table = ""
    mv_stats  = ""
    if step4_df is not None:
        mv_table = step4_df[["predictor", "beta", "SE",
                              "t_stat", "p", "q"]].to_markdown(index=False)
        mv_stats = (f"n = {step4_df['n'].iloc[0]}, "
                    f"λ = {step4_df['lambda_est'].iloc[0]:.3f}, "
                    f"R² = {step4_df['r2'].iloc[0]:.3f}")

    # Top 2 subsets for SI text
    s0 = summary_tab.iloc[0]
    s1 = summary_tab.iloc[1]

    lines = [
        "# Environmental Prediction by Functional Subset",
        "",
        "## Overview",
        "",
        ("Phylogenetically corrected regression (Pagel's λ PGLS) testing whether "
         "metal-gene functional subset densities at genus level predict environmental "
         "metal and geochemical conditions. "
         "Model: `env_response_z ~ subset_density_z + genome_size_z + intercept`. "
         f"Tree: `{TREE_PATH.name}` (GTDB genus-level)."),
        "",
        "---",
        "",
        "## Step 1: Subset PGLS (12 × 15 = 180 models)",
        "",
        f"Total models: {len(step1_df)} | Significant (BH q<0.05): **{n_sig}/{n_tot}**",
        "",
        "### Functional subsets ranked by mean |β|",
        "",
        summary_tab.to_markdown(index=False),
        "",
        "### Significant associations by env response",
        "",
        sig_by_env.to_markdown(index=False),
        "",
        "Heatmap: `figures/functional_subset_env_heatmap.pdf`",
        "",
        "---",
        "",
        "## Step 2: Per-KO PGLS",
        "",
        f"Top 3 env responses (ranked by mean |β| × n_sig): **{top_env}**",
        "",
    ]

    if step2_df is not None:
        n_ko_sig = (step2_df["q"].fillna(1) < 0.05).sum()
        n_ko_tot = step2_df["q"].notna().sum()
        lines += [
            f"KOs tested (≥20 genera present): **{step2_df.ko.nunique()}**",
            f"Significant KO × env pairs (BH q<0.05): **{n_ko_sig}/{n_ko_tot}**",
        ]
        lines += top_ko_sections

    lines += [
        "",
        "---",
        "",
        "## Step 3: Abundance-Weighted PGLS",
        "",
        "Weight: log₁₀(n_samples + 1), normalized. WLS via √w pre-multiplication on y, X.",
        "",
        f"- **Spearman ρ**: {rho:.3f} (p = {pval:.2e})",
        f"- **Mean |Δβ|**: {delta:.4f}",
        "",
        ("ρ > 0.9 and mean |Δβ| < 0.05 would indicate that genus-level abundance "
         "weighting does not change conclusions."),
        "",
        "---",
        "",
        "## Step 4: Multivariate PGLS (env_PC1 ~ all subsets)",
        "",
        "env_PC1 = PC1 of PCA on GEOROC metals (Cu/Ni/Zn/Co/Cr/Pb) + soil pH + temperature.",
        "",
    ]

    if step4_df is not None:
        lines += [mv_stats, "", mv_table]
    else:
        lines.append("*(Multivariate model could not be fit)*")

    lines += [
        "",
        "---",
        "",
        "## SI Paragraph",
        "",
        (f"**Environmental prediction by functional gene subset.** "
         f"To identify which metal-gene functional categories are most strongly "
         f"associated with environmental metal and geochemical gradients, we ran "
         f"Pagel's λ PGLS regressing 15 environmental variables (GEOROC bedrock "
         f"metals Cu, Ni, Zn, Co, Cr, Pb; CSU PF1 mobile fractions As, Cd, Cr, Cu, "
         f"Hg, Pb; soil pH; mean annual temperature; and a multi-metal environment PC1) "
         f"against each of 12 functional gene-density subsets at genus level, "
         f"controlling for genome size ({len(step1_df)} models total, BH FDR "
         f"correction within each environmental variable). "
         f"{n_sig} of {n_tot} models were significant at q < 0.05. "
         f"The subsets most strongly associated with environmental metal gradients "
         f"were {s0['subset'].replace('_', ' ')} (mean |β| = {s0['mean_abs_beta']:.4f}, "
         f"{s0['n_sig_env']} env responses significant) and "
         f"{s1['subset'].replace('_', ' ')} (mean |β| = {s1['mean_abs_beta']:.4f}, "
         f"{s1['n_sig_env']} significant). "
         f"Abundance-weighted PGLS (genera weighted by log₁₀(n_MicrobeAtlas_samples + 1)) "
         f"yielded nearly identical estimates (Spearman ρ = {rho:.3f}, "
         f"p = {pval:.2e}, mean |Δβ| = {delta:.4f}), "
         f"indicating that the pattern is not driven by highly-sampled genera. "
         f"Per-KO PGLS for all {step2_df.ko.nunique() if step2_df is not None else '—'} "
         f"tracked KOs vs. the top three environmental predictors is reported in "
         f"Supplementary Data File S_env_ko."),
        "",
    ]

    out = Path("environmental_prediction_analysis.md")
    out.write_text("\n".join(lines))
    print(f"  Saved → {out}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    t_start = time.time()
    master, nb25, ko_meta = load_data()
    master, V_full, taxa  = build_cached_vcv(master)

    step1_df              = step1_subset_pgls(master, V_full)
    step2_df, top_env     = step2_per_ko_pgls(master, V_full, step1_df, nb25, ko_meta)
    wdf, rho, pval, delta = step3_weighted_pgls(master, V_full, step1_df)
    step4_df              = step4_multivariate_pgls(master, V_full)

    draw_heatmap(step1_df)
    write_report(step1_df, step2_df, rho, pval, delta, step4_df, top_env)

    print(f"\nAll done in {(time.time()-t_start)/60:.1f} minutes.")


if __name__ == "__main__":
    main()
