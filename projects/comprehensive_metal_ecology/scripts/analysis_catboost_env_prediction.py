#!/usr/bin/env python3
"""
analysis_catboost_env_prediction.py

CatBoost + Leave-One-Phylum-Out (LOPO) cross-validation to rank individual KOs
and functional subsets by their ability to predict environmental conditions at
genus level. Phylogenetic control: hold out all genera from one phylum at a time,
train on the rest, measure Spearman ρ on held-out phylum.

Steps
-----
1a  All-KO CatBoost: ~110 KO features → 15 env responses (LOPO avg Spearman ρ)
1b  SHAP feature importance: top 10 KOs per response (responses with avg ρ > 0)
1c  Single-KO CatBoost: one KO + genome_size vs each env response (LOPO avg ρ)
1d  Within-subset SHAP: Resistance / Transport / Cofactor / Metal-dep subsets
2a  Subset CatBoost: 12 functional subset features → 15 env responses (LOPO + SHAP)
2b  Heatmap: subset SHAP matrix
3   Weighted subset CatBoost: abundance-weighted comparison
4   Reverse classifier: env features → KO binary presence/absence (LOPO AUC)
5   Synthesis + report

Constraints
-----------
- OMP_NUM_THREADS=1  (set in shell before launch)
- thread_count=1 in all CatBoost calls  (128-CPU machine)
- No SoilGrids, no CSU from enriched_metadata_gee
- CSU: genus_csu_mobility.csv (PF1 mobile fractions only)
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from catboost import CatBoostRegressor, CatBoostClassifier, Pool

DATA = Path("data")
FIG  = Path("figures")
LOG  = Path("logs")
FIG.mkdir(exist_ok=True)
LOG.mkdir(exist_ok=True)

t0_global = time.time()

# ─── Constants ─────────────────────────────────────────────────────────────────
MIN_KO_GENERA = 20
MIN_PHYLUM_N  = 10

CB = dict(
    iterations=200, depth=4, learning_rate=0.05,
    l2_leaf_reg=3.0, loss_function='RMSE',
    random_seed=42, verbose=False, thread_count=1,
)
CB_FAST = {**CB, 'iterations': 100}       # 2-feature single-KO models
CB_CLS  = {**CB, 'loss_function': 'Logloss', 'eval_metric': 'AUC'}

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
    """Boolean mask: rows with finite y AND all finite X."""
    y_ok = np.isfinite(np.asarray(y, dtype=float))
    X_ok = np.all(np.isfinite(np.asarray(X, dtype=float)), axis=1)
    return y_ok & X_ok


def run_lopo_reg(X, y, phylum_arr, params, sample_weight=None):
    """LOPO regression CV; returns list of (phylum_name, spearman_rho)."""
    X  = np.asarray(X, dtype=float)
    y  = np.asarray(y, dtype=float)
    ph = np.asarray(phylum_arr)
    results = []
    for p in np.unique(ph):
        test_mask  = (ph == p)
        train_mask = ~test_mask
        if test_mask.sum() < MIN_PHYLUM_N:
            continue
        ok_tr = complete_rows(X[train_mask], y[train_mask])
        ok_te = complete_rows(X[test_mask],  y[test_mask])
        if ok_tr.sum() < 20 or ok_te.sum() < 3:
            continue
        X_tr, y_tr = X[train_mask][ok_tr], y[train_mask][ok_tr]
        X_te, y_te = X[test_mask][ok_te],  y[test_mask][ok_te]
        sw = None
        if sample_weight is not None:
            sw = np.asarray(sample_weight)[train_mask][ok_tr]
        try:
            model = CatBoostRegressor(**params)
            model.fit(X_tr, y_tr, sample_weight=sw, verbose=False)
            pred = model.predict(X_te)
            rho  = spearmanr(pred, y_te).statistic
            if np.isfinite(rho):
                results.append((str(p), float(rho)))
        except Exception:
            pass
    return results


def run_lopo_cls(X, y, phylum_arr, params):
    """LOPO binary classifier CV; returns list of (phylum_name, auc)."""
    X  = np.asarray(X, dtype=float)
    y  = np.asarray(y, dtype=int)
    ph = np.asarray(phylum_arr)
    results = []
    for p in np.unique(ph):
        test_mask  = (ph == p)
        train_mask = ~test_mask
        if test_mask.sum() < MIN_PHYLUM_N:
            continue
        ok_tr = np.all(np.isfinite(X[train_mask]), axis=1)
        ok_te = np.all(np.isfinite(X[test_mask]),  axis=1)
        if ok_tr.sum() < 20 or ok_te.sum() < 3:
            continue
        X_tr, y_tr = X[train_mask][ok_tr], y[train_mask][ok_tr]
        X_te, y_te = X[test_mask][ok_te],  y[test_mask][ok_te]
        # Need both classes in training set
        if len(np.unique(y_tr)) < 2 or len(np.unique(y_te)) < 2:
            continue
        try:
            model = CatBoostClassifier(**params)
            model.fit(X_tr, y_tr, verbose=False)
            prob  = model.predict_proba(X_te)[:, 1]
            auc   = roc_auc_score(y_te, prob)
            results.append((str(p), float(auc)))
        except Exception:
            pass
    return results


def avg_stat(lopo_result):
    if not lopo_result:
        return np.nan
    return float(np.mean([v for _, v in lopo_result]))


def shap_from_model(model, X_valid, y_valid):
    """Mean absolute SHAP values (per feature), excluding bias column."""
    shap_matrix = model.get_feature_importance(
        Pool(X_valid, y_valid), type='ShapValues')
    return np.abs(shap_matrix[:, :-1]).mean(axis=0)


def elapsed():
    return f"{(time.time()-t0_global)/60:.1f} min"


# ─── Step 0: load_data ─────────────────────────────────────────────────────────
def load_data():
    print("Loading source files...")

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
        base["translation_per_mb"].fillna(0) +
        base["replication_repair_per_mb"].fillna(0) +
        base["aa_metab_per_mb"].fillna(0)
    )
    base["core_metabolism_z"] = zscore(base["core_metabolism"])

    # Metal-dep metabolism z-score from nb25 (Metal-dependent Metabolism KOs)
    print("  Computing metal-dep z-score from nb25...")
    metal_dep_kos = s8.loc[s8["primary_category"] == "Metal-dependent Metabolism", "ko"].tolist()
    nb25_raw = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
    nb25_raw["genus_lower"] = nb25_raw["genus_lower"].str.replace(r'^g__', '', regex=True)
    md_agg = (nb25_raw[nb25_raw["ko"].isin(metal_dep_kos)]
              .groupby("genus_lower")["n_genomes_with_ko"]
              .sum().reset_index()
              .rename(columns={"n_genomes_with_ko": "metal_dep_sum"}))
    md_agg = md_agg.merge(base[["genus_lower", "mean_genome_mb"]].dropna(),
                           on="genus_lower", how="inner")
    md_agg["metal_dep_per_mb"] = md_agg["metal_dep_sum"] / md_agg["mean_genome_mb"]
    md_agg["metal_dep_z"] = zscore(md_agg["metal_dep_per_mb"])
    md_agg = md_agg[["genus_lower", "metal_dep_z"]]

    # Merge all sources
    master = (
        exp[["genus_lower", "mean_genome_mb", "genome_mb_z",
             "expanded_z", "cobalamin_z", "fes_assembly_z",
             "heme_z", "molybdopterin_z", "siroheme_z"]]
        .merge(base[["genus_lower", "ko_per_mb_primary_z", "genome_size_mb_z",
                     "core_metabolism_z", "cofactor_vitamin_per_mb_z",
                     "phylum", "mean_genome_mb", "n_soil_samples"]],
               on="genus_lower", how="inner", suffixes=("_exp", ""))
        .merge(tier[["genus_lower", "ko_per_mb_tier1_z", "ko_per_mb_tier2_z"]],
               on="genus_lower", how="left")
        .merge(md_agg, on="genus_lower", how="left")
        .merge(geo[["genus_lower", "georoc_Cu_log", "georoc_Ni_log", "georoc_Zn_log",
                    "georoc_Co_log", "georoc_Cr_log", "georoc_Pb_log",
                    "median_soil_ph", "median_era5_temp_C", "n_samples"]],
               on="genus_lower", how="left")
        .merge(csu[["genus_lower", "PF1_As", "PF1_Cd", "PF1_Cr",
                    "PF1_Cu", "PF1_Hg", "PF1_Pb"]],
               on="genus_lower", how="left")
    )

    # genome_size_mb_z: prefer base; fall back to exp
    mask = master["genome_size_mb_z"].isna()
    master.loc[mask, "genome_size_mb_z"] = master.loc[mask, "genome_mb_z"]

    # mean_genome_mb: prefer exp; fall back to base
    gm_mask = master["mean_genome_mb"].isna()
    master.loc[gm_mask, "mean_genome_mb"] = master.loc[gm_mask, "mean_genome_mb_exp"]

    # Env response z-scores
    for metal in ["Cu", "Ni", "Zn", "Co", "Cr", "Pb"]:
        master[f"georoc_{metal}_z"] = zscore(master[f"georoc_{metal}_log"])
    for metal in ["As", "Cd", "Cr", "Cu", "Hg", "Pb"]:
        master[f"csu_{metal}_z"] = zscore(np.log10(master[f"PF1_{metal}"].values + 1e-4))
    master["ph_z"]   = zscore(master["median_soil_ph"])
    master["temp_z"] = zscore(master["median_era5_temp_C"])

    # env_PC1
    pca_cols = ["georoc_Cu_log", "georoc_Ni_log", "georoc_Zn_log",
                "georoc_Co_log", "georoc_Cr_log", "georoc_Pb_log",
                "median_soil_ph", "median_era5_temp_C"]
    pca_mask = master[pca_cols].notna().all(axis=1)
    pca_data = StandardScaler().fit_transform(master.loc[pca_mask, pca_cols].values)
    pc1 = PCA(n_components=1, random_state=42).fit_transform(pca_data)[:, 0]
    master["env_PC1"] = np.nan
    master.loc[pca_mask, "env_PC1"] = pc1
    master["env_PC1_z"] = zscore(master["env_PC1"])

    # Sample weights: log10(n_samples + 1) normalized to mean=1
    w = np.log10(master["n_samples"].fillna(1) + 1)
    master["weight_norm"] = w / w.mean()

    print(f"  Master: {len(master):,} genera, "
          f"{master['phylum'].notna().sum():,} with phylum")

    # ─── Per-KO feature matrix ────────────────────────────────────────────────
    print("  Building per-KO density matrix from nb25...")
    tier1_2_kos = s8["ko"].tolist()   # all 118 Tier 1+2 KOs

    nb25_filt = nb25_raw[nb25_raw["ko"].isin(tier1_2_kos)].copy()
    ko_genera_cnt = nb25_filt.groupby("ko")["genus_lower"].count()
    valid_kos = ko_genera_cnt[ko_genera_cnt >= MIN_KO_GENERA].index.tolist()
    print(f"  Tier 1+2 KOs with ≥{MIN_KO_GENERA} genera: {len(valid_kos)}")

    nb25_valid = nb25_filt[nb25_filt["ko"].isin(valid_kos)]
    ko_wide = nb25_valid.pivot_table(
        index="genus_lower", columns="ko",
        values="n_genomes_with_ko", fill_value=0)

    # Per-Mb density
    genome_mb = master.set_index("genus_lower")["mean_genome_mb"].dropna()
    ko_wide = ko_wide.loc[ko_wide.index.isin(genome_mb.index)]
    ko_wide = ko_wide.div(genome_mb.reindex(ko_wide.index), axis=0)

    # Binary presence (before z-scoring, used in Step 4)
    ko_binary = (ko_wide > 0).astype(int)

    # Z-score each KO column
    ko_z = ko_wide.apply(zscore, axis=0)

    print(f"  Per-KO matrix: {ko_z.shape} (genera × KOs)")
    return master, ko_z, ko_binary, s8, valid_kos


# ─── Step 1a: all-KO CatBoost ──────────────────────────────────────────────────
def step1a_all_ko(master, ko_z, s8):
    print(f"\n─── Step 1a: All-KO CatBoost LOPO CV  [{elapsed()}] ───")

    # Align master and ko_z on genus_lower
    common = master.set_index("genus_lower").index.intersection(ko_z.index)
    m  = master.set_index("genus_lower").loc[common].reset_index()
    k  = ko_z.loc[common]
    ph = m["phylum"].values

    phyla_counts = pd.Series(ph).value_counts()
    lopo_phyla   = phyla_counts[phyla_counts >= MIN_PHYLUM_N].index.tolist()
    print(f"  LOPO phyla ({len(lopo_phyla)}): {lopo_phyla}")
    print(f"  n genera: {len(m)}, n KO features: {k.shape[1]}")

    gsize = m["genome_size_mb_z"].values
    X = np.column_stack([k.values, gsize])
    feature_names = k.columns.tolist() + ["genome_size_mb_z"]

    lopo_rows = []
    shap_store = {}   # resp_name → {feature: mean_abs_shap}

    for i, (resp_name, resp_col) in enumerate(ENV_RESPONSES.items()):
        y = m[resp_col].values if resp_col in m.columns else np.full(len(m), np.nan)
        lopo_res = run_lopo_reg(X, y, ph, CB)
        ar = avg_stat(lopo_res)
        lopo_rows.append({
            "env_response": resp_name, "model": "all_KO",
            "avg_rho": ar, "n_folds": len(lopo_res),
        })
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(ENV_RESPONSES)} responses")

        # Full-data SHAP for positive-ρ responses
        if np.isfinite(ar) and ar > 0:
            valid = complete_rows(X, y)
            if valid.sum() > 50:
                model = CatBoostRegressor(**CB)
                model.fit(X[valid], y[valid], verbose=False)
                mean_shap = shap_from_model(model, X[valid], y[valid])
                shap_store[resp_name] = dict(zip(feature_names, mean_shap))

    print(f"  Responses with avg ρ > 0: {sum(1 for r in lopo_rows if r['avg_rho'] is not np.nan and (r['avg_rho'] or 0) > 0)}")
    return pd.DataFrame(lopo_rows), shap_store, feature_names, X, ph, m, k


# ─── Step 1b: SHAP summary ─────────────────────────────────────────────────────
def step1b_shap_summary(shap_store, s8, pgls_ko_df):
    print(f"\n─── Step 1b: SHAP importance summary  [{elapsed()}] ───")

    pgls_top10 = {}
    if pgls_ko_df is not None and "ko" in pgls_ko_df.columns:
        for resp in ENV_RESPONSES:
            sub = pgls_ko_df[pgls_ko_df["env_response"] == resp].sort_values("p")
            pgls_top10[resp] = set(sub["ko"].head(10).tolist())

    rows = []
    for resp_name, shap_dict in shap_store.items():
        # Exclude genome_size from ranking
        ko_shap = {k: v for k, v in shap_dict.items() if k != "genome_size_mb_z"}
        sorted_kos = sorted(ko_shap.items(), key=lambda x: -x[1])
        print(f"  {resp_name}: top5 = {[k for k,_ in sorted_kos[:5]]}")
        for rank, (ko, sv) in enumerate(sorted_kos[:10], 1):
            cat = s8.loc[s8["ko"] == ko, "primary_category"].values
            rows.append({
                "env_response": resp_name, "rank": rank,
                "ko": ko, "mean_abs_shap": sv,
                "primary_category": cat[0] if len(cat) else "Unknown",
                "in_pgls_top10": ko in pgls_top10.get(resp_name, set()),
            })
    return pd.DataFrame(rows)


# ─── Step 1c: single-KO CatBoost ───────────────────────────────────────────────
def step1c_single_ko(master, ko_z, s8, ph_for_1c):
    print(f"\n─── Step 1c: Single-KO CatBoost LOPO CV  [{elapsed()}] ───")

    common = master.set_index("genus_lower").index.intersection(ko_z.index)
    m  = master.set_index("genus_lower").loc[common].reset_index()
    k  = ko_z.loc[common]
    ph = ph_for_1c   # already aligned to common genera

    gsize = m["genome_size_mb_z"].values
    rows  = []
    total = len(k.columns) * len(ENV_RESPONSES)
    done  = 0

    for ko in k.columns:
        ko_vals = k[ko].values
        X_ko    = np.column_stack([ko_vals, gsize])
        cat     = s8.loc[s8["ko"] == ko, "primary_category"].values
        cat     = cat[0] if len(cat) else "Unknown"

        for resp_name, resp_col in ENV_RESPONSES.items():
            y = m[resp_col].values if resp_col in m.columns else np.full(len(m), np.nan)
            lopo_res = run_lopo_reg(X_ko, y, ph, CB_FAST)
            ar = avg_stat(lopo_res)
            rows.append({
                "ko": ko, "primary_category": cat,
                "env_response": resp_name,
                "avg_rho": ar, "n_folds": len(lopo_res),
            })
            done += 1
            if done % 500 == 0:
                print(f"  {done}/{total} single-KO models")

    print(f"  Done: {done}/{total}")
    return pd.DataFrame(rows)


# ─── Step 1d: within-subset SHAP ───────────────────────────────────────────────
def step1d_within_subset(master, ko_z, s8, ph_for_1d):
    print(f"\n─── Step 1d: Within-subset CatBoost LOPO + SHAP  [{elapsed()}] ───")

    common = master.set_index("genus_lower").index.intersection(ko_z.index)
    m   = master.set_index("genus_lower").loc[common].reset_index()
    k   = ko_z.loc[common]
    ph  = ph_for_1d
    gsize = m["genome_size_mb_z"].values

    # Define subsets by primary_category in s8_ko_metadata
    subset_defs = {
        "Resistance":  s8.loc[s8["primary_category"] == "Resistance/Detoxification", "ko"].tolist(),
        "Transport":   s8.loc[s8["primary_category"] == "Transport/Homeostasis",     "ko"].tolist(),
        "Cofactor":    s8.loc[s8["primary_category"] == "Cofactor Biosynthesis",     "ko"].tolist(),
        "Metal_dep":   s8.loc[s8["primary_category"] == "Metal-dependent Metabolism","ko"].tolist(),
    }

    rows = []
    for subset_name, subset_kos in subset_defs.items():
        avail = [ko for ko in subset_kos if ko in k.columns]
        print(f"  {subset_name}: {len(avail)}/{len(subset_kos)} KOs in matrix")
        if len(avail) < 2:
            continue

        X_sub      = np.column_stack([k[avail].values, gsize])
        feat_names = avail + ["genome_size_mb_z"]

        for resp_name, resp_col in ENV_RESPONSES.items():
            y = m[resp_col].values if resp_col in m.columns else np.full(len(m), np.nan)
            lopo_res = run_lopo_reg(X_sub, y, ph, CB)
            ar       = avg_stat(lopo_res)

            valid = complete_rows(X_sub, y)
            if valid.sum() < 30:
                continue
            model = CatBoostRegressor(**CB)
            model.fit(X_sub[valid], y[valid], verbose=False)
            mean_shap = shap_from_model(model, X_sub[valid], y[valid])

            for ko, sv in zip(feat_names, mean_shap):
                cat = s8.loc[s8["ko"] == ko, "primary_category"].values
                rows.append({
                    "subset": subset_name, "ko": ko,
                    "primary_category": cat[0] if len(cat) else "genome_size",
                    "env_response": resp_name,
                    "mean_abs_shap": sv, "avg_rho": ar,
                })
    return pd.DataFrame(rows)


# ─── Step 2: Functional-subset CatBoost ────────────────────────────────────────
def step2_subset_catboost(master):
    print(f"\n─── Step 2: Functional-subset CatBoost LOPO + SHAP  [{elapsed()}] ───")

    subset_cols = list(SUBSETS.values())
    feat_names  = list(SUBSETS.keys()) + ["genome_size_mb_z"]

    # Complete-case master for subset features
    needed = subset_cols + ["genome_size_mb_z", "phylum", "weight_norm"] + list(ENV_RESPONSES.values())
    needed = [c for c in needed if c in master.columns]
    sub_m  = master[needed].dropna(subset=subset_cols + ["phylum"]).copy()

    ph = sub_m["phylum"].values
    X  = np.column_stack(
        [sub_m[c].values for c in subset_cols] + [sub_m["genome_size_mb_z"].values]
    )
    w  = sub_m["weight_norm"].values if "weight_norm" in sub_m.columns else None

    lopo_rows = []
    shap_rows = []

    for i, (resp_name, resp_col) in enumerate(ENV_RESPONSES.items()):
        if resp_col not in sub_m.columns:
            continue
        y = sub_m[resp_col].values

        # Unweighted LOPO
        lopo_res = run_lopo_reg(X, y, ph, CB)
        ar = avg_stat(lopo_res)
        lopo_rows.append({"env_response": resp_name, "model": "subset",
                          "avg_rho": ar, "n_folds": len(lopo_res)})

        # SHAP on full data
        valid = complete_rows(X, y)
        if valid.sum() > 30:
            model = CatBoostRegressor(**CB)
            model.fit(X[valid], y[valid], verbose=False)
            mean_shap = shap_from_model(model, X[valid], y[valid])
            for fn, sv in zip(feat_names, mean_shap):
                shap_rows.append({"subset": fn, "env_response": resp_name,
                                   "mean_abs_shap": sv, "avg_rho": ar})

        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(ENV_RESPONSES)} responses (avg ρ={ar:.3f})")

    lopo_df = pd.DataFrame(lopo_rows)
    shap_df = pd.DataFrame(shap_rows)

    # ─── Weighted LOPO (Step 3) ───────────────────────────────────────────────
    print(f"\n─── Step 3: Weighted subset CatBoost  [{elapsed()}] ───")
    weighted_rows = []
    for resp_name, resp_col in ENV_RESPONSES.items():
        if resp_col not in sub_m.columns:
            continue
        y = sub_m[resp_col].values

        lopo_w = run_lopo_reg(X, y, ph, CB, sample_weight=w)
        ar_w   = avg_stat(lopo_w)

        valid = complete_rows(X, y)
        if valid.sum() > 30:
            model_w = CatBoostRegressor(**CB)
            model_w.fit(X[valid], y[valid], sample_weight=w[valid], verbose=False)
            shap_w = shap_from_model(model_w, X[valid], y[valid])
        else:
            shap_w = np.full(len(feat_names), np.nan)

        # Find unweighted SHAP for same response
        shap_u_map = {r["subset"]: r["mean_abs_shap"]
                      for r in shap_rows if r["env_response"] == resp_name}
        for fn, sv_w in zip(feat_names, shap_w):
            weighted_rows.append({
                "subset": fn, "env_response": resp_name,
                "shap_unweighted": shap_u_map.get(fn, np.nan),
                "shap_weighted":   float(sv_w),
            })
        if (len(weighted_rows) // len(feat_names)) % 5 == 0:
            print(f"  {len(weighted_rows)//len(feat_names)}/{len(ENV_RESPONSES)} (weighted avg ρ={ar_w:.3f})")

    weighted_df = pd.DataFrame(weighted_rows)

    # Compute Spearman ρ between weighted and unweighted SHAP per response
    wr_corr = []
    for resp in ENV_RESPONSES:
        df_r = weighted_df[weighted_df["env_response"] == resp].dropna()
        if len(df_r) >= 5:
            rho, _ = spearmanr(df_r["shap_unweighted"], df_r["shap_weighted"])
            wr_corr.append({"env_response": resp, "shap_rank_rho": rho})
    wr_corr_df = pd.DataFrame(wr_corr)
    if len(wr_corr_df):
        print(f"  Weighted vs unweighted SHAP rank ρ — mean: "
              f"{wr_corr_df['shap_rank_rho'].mean():.3f}, "
              f"min: {wr_corr_df['shap_rank_rho'].min():.3f}")

    return lopo_df, shap_df, weighted_df, wr_corr_df


# ─── Step 4: reverse classifier ────────────────────────────────────────────────
def step4_reverse_classifier(master, ko_z, ko_binary, s8, shap_store, single_ko_df):
    print(f"\n─── Step 4: Reverse classifier (env → KO presence)  [{elapsed()}] ───")

    # Top-10 KOs = union of top-5 by mean |SHAP| and top-5 by single-KO avg ρ
    top_by_shap = []
    for shap_dict in shap_store.values():
        ko_shap = {k: v for k, v in shap_dict.items() if k != "genome_size_mb_z"}
        top_by_shap.extend([k for k, _ in sorted(ko_shap.items(), key=lambda x: -x[1])[:5]])

    top_by_rho = []
    if single_ko_df is not None and len(single_ko_df):
        mean_rho = (single_ko_df.groupby("ko")["avg_rho"]
                    .mean().sort_values(ascending=False))
        top_by_rho = mean_rho.head(5).index.tolist()

    top10 = list(dict.fromkeys(top_by_shap[:5] + top_by_rho[:5]))[:10]
    if not top10:
        top10 = ko_z.columns.tolist()[:10]
    print(f"  Top-10 KOs for reverse classifier: {top10}")

    # Feature matrix: all 15 env z-scores + genome_size_mb_z
    env_cols  = [c for c in ENV_RESPONSES.values() if c in master.columns]
    feat_list = env_cols + ["genome_size_mb_z"]

    common = master.set_index("genus_lower").index.intersection(ko_binary.index)
    m_sub  = master.set_index("genus_lower").loc[common].reset_index()
    kb_sub = ko_binary.loc[common]
    ph     = m_sub["phylum"].values

    X = np.column_stack([m_sub[c].values if c in m_sub.columns
                          else np.full(len(m_sub), np.nan) for c in feat_list])

    rows = []
    for ko in top10:
        if ko not in kb_sub.columns:
            continue
        y_bin = kb_sub[ko].values
        cat   = s8.loc[s8["ko"] == ko, "primary_category"].values
        cat   = cat[0] if len(cat) else "Unknown"

        lopo_res = run_lopo_cls(X, y_bin, ph, CB_CLS)
        avg_auc  = avg_stat(lopo_res)
        std_auc  = float(np.std([v for _, v in lopo_res])) if lopo_res else np.nan
        print(f"  {ko} ({cat}): avg AUC = {avg_auc:.3f} (n_folds={len(lopo_res)})")
        rows.append({
            "ko": ko, "primary_category": cat,
            "avg_auc": avg_auc, "std_auc": std_auc,
            "n_folds": len(lopo_res),
        })
    return pd.DataFrame(rows)


# ─── Step 5: Heatmap ───────────────────────────────────────────────────────────
def draw_heatmap(shap_df):
    print(f"\n─── Drawing heatmap  [{elapsed()}] ───")

    pivot = shap_df.pivot_table(
        index="subset", columns="env_response",
        values="mean_abs_shap", aggfunc="mean")

    # Annotate with avg_rho
    rho_pivot = shap_df.pivot_table(
        index="subset", columns="env_response",
        values="avg_rho", aggfunc="mean")

    subset_order = list(SUBSETS.keys()) + ["genome_size_mb_z"]
    env_order    = list(ENV_RESPONSES.keys())
    pivot = pivot.reindex(index=[s for s in subset_order if s in pivot.index],
                          columns=[e for e in env_order if e in pivot.columns])
    rho_pivot = rho_pivot.reindex(index=pivot.index, columns=pivot.columns)

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(pivot, cmap="YlOrRd", ax=ax,
                linewidths=0.3, linecolor="white",
                cbar_kws={"label": "Mean |SHAP|"})

    # Annotate cells with avg ρ (show only if |ρ| ≥ 0.05)
    for i, row_name in enumerate(pivot.index):
        for j, col_name in enumerate(pivot.columns):
            rho_val = rho_pivot.at[row_name, col_name] if (
                row_name in rho_pivot.index and col_name in rho_pivot.columns) else np.nan
            if np.isfinite(rho_val) and abs(rho_val) >= 0.05:
                ax.text(j + 0.5, i + 0.5, f"{rho_val:.2f}",
                        ha="center", va="center", fontsize=6, color="black")

    ax.set_title("Functional subset mean |SHAP| (CatBoost LOPO CV)\n"
                 "Cell annotations: avg LOPO Spearman ρ (|ρ| ≥ 0.05)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "catboost_shap_heatmap.pdf", bbox_inches="tight")
    plt.savefig(FIG / "catboost_shap_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved → figures/catboost_shap_heatmap.pdf/.png")


# ─── Step 5: write report ──────────────────────────────────────────────────────
def write_report(lopo1a, shap1b, single_ko_df, within_df, lopo2, shap2,
                  weighted_df, wr_corr_df, reverse_df, pgls_r2=0.011):
    print(f"\n─── Writing report  [{elapsed()}] ───")

    lines = ["# CatBoost Environmental Prediction Analysis", "",
             "## Overview", "",
             "CatBoost regressors with Leave-One-Phylum-Out (LOPO) cross-validation "
             "test whether metal-gene functional subset densities and individual KO "
             "densities at genus level predict environmental conditions. Each fold trains "
             "on all phyla except one and evaluates on the held-out phylum (Spearman ρ). "
             "11 phyla qualify (≥10 genera each). This complements the Pagel's λ PGLS "
             "framework (Finding 18) by allowing nonlinear relationships and providing "
             "model-agnostic SHAP feature importance.", ""]

    # Step 1a: LOPO results table
    lines += ["---", "", "## Step 1a: All-KO CatBoost LOPO CV", ""]
    if len(lopo1a):
        tbl = lopo1a[["env_response", "avg_rho", "n_folds"]].to_markdown(index=False)
        lines.append(tbl)
    lines.append("")

    # Step 1b: SHAP top-10
    lines += ["---", "", "## Step 1b: SHAP Feature Importance (top-10 KOs)", ""]
    if len(shap1b):
        for resp in lopo1a.loc[lopo1a["avg_rho"].fillna(0) > 0, "env_response"]:
            sub = shap1b[shap1b["env_response"] == resp].sort_values("rank").head(10)
            if len(sub):
                lines.append(f"**{resp}:**")
                lines.append(sub[["rank","ko","primary_category","mean_abs_shap","in_pgls_top10"]].to_markdown(index=False))
                lines.append("")

    # Step 1c: top-10 by single-KO avg ρ (pooled over all responses)
    lines += ["---", "", "## Step 1c: Single-KO CatBoost — Top KOs by Mean Avg ρ", ""]
    if single_ko_df is not None and len(single_ko_df):
        top = (single_ko_df.groupby(["ko","primary_category"])["avg_rho"]
               .mean().reset_index()
               .sort_values("avg_rho", ascending=False).head(20))
        lines.append(top.to_markdown(index=False))
    lines.append("")

    # Step 1d: within-subset highlights
    lines += ["---", "", "## Step 1d: Within-Subset SHAP Decomposition", ""]
    if len(within_df):
        best = (within_df.groupby(["subset","ko","primary_category"])["mean_abs_shap"]
                .mean().reset_index()
                .sort_values(["subset","mean_abs_shap"], ascending=[True, False]))
        for subset_name in within_df["subset"].unique():
            top_kos = best[best["subset"] == subset_name].head(5)
            lines.append(f"**{subset_name}** — top KOs by mean |SHAP|:")
            lines.append(top_kos[["ko","primary_category","mean_abs_shap"]].to_markdown(index=False))
            lines.append("")

    # Step 2: subset results
    lines += ["---", "", "## Step 2: Functional Subset CatBoost LOPO + SHAP", ""]
    if len(lopo2):
        lines.append(lopo2[["env_response","avg_rho","n_folds"]].to_markdown(index=False))
    lines.append("")
    lines.append("Heatmap: `figures/catboost_shap_heatmap.pdf`")
    lines.append("")

    # Step 3: weighted comparison
    lines += ["---", "", "## Step 3: Abundance-Weighted vs Unweighted SHAP Rankings", ""]
    if len(wr_corr_df):
        lines.append(wr_corr_df.to_markdown(index=False))
        mean_rho_w = wr_corr_df["shap_rank_rho"].mean()
        lines.append(f"\nMean Spearman ρ (weighted vs unweighted SHAP rankings): **{mean_rho_w:.3f}**")
    lines.append("")

    # Step 4: reverse AUC
    lines += ["---", "", "## Step 4: Reverse Classifier (Env → KO Presence/Absence)", ""]
    if len(reverse_df):
        lines.append(reverse_df.to_markdown(index=False))
    lines.append("")

    # Step 5: synthesis
    lines += ["---", "", "## Synthesis", ""]
    if len(lopo1a):
        n_pos_1a = (lopo1a["avg_rho"].fillna(0) > 0).sum()
        lines.append(f"- **Step 1a (all-KO model)**: {n_pos_1a}/{len(lopo1a)} responses have avg ρ > 0 across LOPO folds.")
    if len(lopo2):
        n_pos_2 = (lopo2["avg_rho"].fillna(0) > 0).sum()
        best_resp = lopo2.loc[lopo2["avg_rho"].idxmax(), "env_response"] if len(lopo2) else "N/A"
        lines.append(f"- **Step 2 (subset model)**: {n_pos_2}/{len(lopo2)} responses have avg ρ > 0. Best: {best_resp}.")
    if len(wr_corr_df):
        lines.append(f"- **Step 3 (weighted)**: Mean Spearman ρ between weighted and unweighted SHAP rankings = {wr_corr_df['shap_rank_rho'].mean():.3f}.")
    if len(reverse_df):
        best_auc = reverse_df["avg_auc"].max() if len(reverse_df) else np.nan
        lines.append(f"- **Step 4 (reverse)**: Best avg AUC across KOs = {best_auc:.3f}.")

    # PGLS comparison
    lines += ["", "### CatBoost vs PGLS comparison", "",
              f"PGLS multivariate (all 12 subsets → env_PC1): R² = {pgls_r2:.3f}. "
              "CatBoost avg ρ² provides an analogous nonlinear variance-explained "
              "estimate. If CatBoost ρ² ≈ PGLS R², the relationship is largely linear; "
              "if substantially higher, nonlinear associations exist.", ""]

    # SI paragraph
    lines += ["---", "", "## SI Paragraph", "",
              "**Machine-learning validation of functional subset environmental associations.** "
              "To test whether the PGLS results reflect nonlinear or phylogenetically "
              "confounded patterns, we applied CatBoost gradient-boosted trees with "
              "Leave-One-Phylum-Out (LOPO) cross-validation (11 phyla, ≥10 genera each) "
              "to predict the same 15 environmental variables from genus-level metal-gene "
              "functional subset densities and individual Tier 1+2 KO densities. SHAP "
              "feature importance was extracted for all models with positive held-out "
              "Spearman ρ. Abundance-weighted models (weights = log₁₀(n_MicrobeAtlas_samples + 1)) "
              "were compared with unweighted models. For top-ranked KOs by SHAP importance "
              "and single-KO ρ, we additionally trained binary classifiers predicting KO "
              "presence/absence from environmental variables (LOPO AUC). Results are "
              "reported in Supplementary Data File S_catboost_env.", ""]

    report = "\n".join(lines)
    with open("catboost_environmental_prediction.md", "w") as f:
        f.write(report)
    print("  Saved → catboost_environmental_prediction.md")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("CatBoost environmental prediction analysis")
    print("=" * 60)

    # Step 0: load data
    master, ko_z, ko_binary, s8, valid_kos = load_data()

    # Load per-KO PGLS results for cross-reference
    pgls_ko_path = DATA / "per_ko_env_prediction.csv"
    pgls_ko_df   = pd.read_csv(pgls_ko_path) if pgls_ko_path.exists() else None

    # ─── Step 1a: all-KO LOPO ────────────────────────────────────────────────
    lopo1a_df, shap_store, feat_names, X_all, ph_allko, m_allko, k_allko = (
        step1a_all_ko(master, ko_z, s8))

    # ─── Step 1b: SHAP summary ───────────────────────────────────────────────
    shap1b_df = step1b_shap_summary(shap_store, s8, pgls_ko_df)

    # ─── Step 1c: single-KO ──────────────────────────────────────────────────
    single_ko_df = step1c_single_ko(master, ko_z, s8, ph_allko)

    # ─── Step 1d: within-subset ──────────────────────────────────────────────
    within_df = step1d_within_subset(master, ko_z, s8, ph_allko)

    # ─── Steps 2 + 3: subset CatBoost (weighted inside) ─────────────────────
    lopo2_df, shap2_df, weighted_df, wr_corr_df = step2_subset_catboost(master)

    # ─── Combine lopo rows for output ────────────────────────────────────────
    lopo_combined = pd.concat([lopo1a_df, lopo2_df], ignore_index=True)

    # ─── Step 4: reverse classifier ──────────────────────────────────────────
    reverse_df = step4_reverse_classifier(
        master, ko_z, ko_binary, s8, shap_store, single_ko_df)

    # ─── Save outputs ─────────────────────────────────────────────────────────
    print(f"\n─── Saving outputs  [{elapsed()}] ───")

    lopo_combined.to_csv(DATA / "catboost_lopo_results.csv", index=False)
    print(f"  Saved → data/catboost_lopo_results.csv ({len(lopo_combined)} rows)")

    single_ko_df.to_csv(DATA / "catboost_single_ko_ranking.csv", index=False)
    print(f"  Saved → data/catboost_single_ko_ranking.csv ({len(single_ko_df)} rows)")

    within_df.to_csv(DATA / "catboost_within_subset_shap.csv", index=False)
    print(f"  Saved → data/catboost_within_subset_shap.csv ({len(within_df)} rows)")

    shap2_df.to_csv(DATA / "catboost_shap_heatmap.csv", index=False)
    print(f"  Saved → data/catboost_shap_heatmap.csv ({len(shap2_df)} rows)")

    weighted_df.to_csv(DATA / "catboost_weighted_comparison.csv", index=False)
    print(f"  Saved → data/catboost_weighted_comparison.csv ({len(weighted_df)} rows)")

    reverse_df.to_csv(DATA / "catboost_reverse_auc.csv", index=False)
    print(f"  Saved → data/catboost_reverse_auc.csv ({len(reverse_df)} rows)")

    # ─── Heatmap ─────────────────────────────────────────────────────────────
    if len(shap2_df):
        draw_heatmap(shap2_df)

    # ─── Report ───────────────────────────────────────────────────────────────
    write_report(lopo1a_df, shap1b_df, single_ko_df, within_df,
                  lopo2_df, shap2_df, weighted_df, wr_corr_df, reverse_df)

    total_min = (time.time() - t0_global) / 60
    print(f"\nAll done in {total_min:.1f} minutes.")


if __name__ == "__main__":
    main()
