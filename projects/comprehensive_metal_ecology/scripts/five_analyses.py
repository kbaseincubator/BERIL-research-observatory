"""
Five-analysis script:
  Task 1: Per-KO Pagel's λ (HGT fingerprint)
  Task 3: Per-metal resistance PGLS
  Task 4: Fitness burden PGLS
  Task 5: Expanded essential biosynthetic set PGLS
"""
import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import mannwhitneyu, chi2_contingency

warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import run_pgls

DATA = Path("data")
TREE = DATA / "gtdb_bac_genus_pruned.tree"

# ──────────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────────
print("Loading data...")
nb25 = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
nb25["genus_lower"] = nb25["genus_lower"].str.replace("g__", "", regex=False)

spark = pd.read_csv(DATA / "01_genus_ko_density_spark.csv")
primary = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")

tier12 = curated[curated["evidence_tier"].isin(["Tier 1", "Tier 2"])].copy()
tier12_kos = set(tier12["KO"])

# nb25 KOs in Tier1+2
nb25_kos = set(nb25["ko"].unique())
available_kos = sorted(tier12_kos & nb25_kos)
print(f"Tier1+2 KOs available in nb25: {len(available_kos)} / {len(tier12_kos)}")

# Build per-genus per-KO density for available KOs
ko_df = nb25[nb25["ko"].isin(available_kos)].copy()
ko_df = ko_df.merge(spark[["genus_lower", "n_genomes", "mean_genome_mb"]], on="genus_lower", how="inner")
ko_df["density"] = ko_df["n_genomes_with_ko"] / (ko_df["n_genomes"] * ko_df["mean_genome_mb"])
ko_df = ko_df.merge(primary[["genus_lower", "mean_levins_B_std", "mean_genome_mb"]],
                    on="genus_lower", how="inner", suffixes=("", "_primary"))
ko_df = ko_df.dropna(subset=["mean_levins_B_std"])
print(f"Genera with density data and niche breadth: {ko_df['genus_lower'].nunique()}")

# KO metadata
ko_meta = tier12.set_index("KO")[["gene_name", "primary_category", "source_fitness", "metals"]].to_dict("index")


def zscore(x):
    return (x - x.mean()) / x.std(ddof=1)


def _extract_beta(res, key):
    if "betas" in res:
        return res["betas"][key], res["SEs"][key], res["p_values"][key]
    return res["beta"], res["SE"], res["p_value"]


# ──────────────────────────────────────────────────────────────────
# TASK 1: Per-KO Pagel's λ
# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TASK 1: Per-KO Pagel's λ analysis")
print("=" * 60)

task1_results = []
for ko_id in available_kos:
    sub = ko_df[ko_df["ko"] == ko_id].copy()
    sub = sub[sub["density"] > 0]
    if len(sub) < 20:
        print(f"  SKIP {ko_id}: n={len(sub)}")
        continue
    sub["density_z"] = zscore(sub["density"])
    try:
        res = run_pgls(
            sub, str(TREE), "mean_levins_B_std", ["density_z"],
            taxon_col="genus_lower", label=f"ko_{ko_id}"
        )
        b, se, p = _extract_beta(res, "density_z")
        lam = res["lambda_est"]
        n = res["n"]
        meta = ko_meta.get(ko_id, {})
        task1_results.append({
            "ko_id": ko_id,
            "gene_name": meta.get("gene_name", ""),
            "subcategory": meta.get("primary_category", "Unknown"),
            "lambda": lam,
            "beta": b,
            "SE": se,
            "p_value": p,
            "n_genera": n,
        })
        print(f"  {ko_id} ({meta.get('gene_name','')}) [{meta.get('primary_category','')}]: "
              f"λ={lam:.3f}, β={b:+.4f}, p={p:.3e}, n={n}")
    except Exception as e:
        print(f"  ERROR {ko_id}: {e}")

t1_df = pd.DataFrame(task1_results)
t1_df.to_csv(DATA / "task1_per_ko_lambda.csv", index=False)

if len(t1_df) > 0:
    print(f"\n  Fitted {len(t1_df)} KOs")

    res_kos = t1_df[t1_df["subcategory"] == "Resistance/Detoxification"]["lambda"].values
    cof_kos = t1_df[t1_df["subcategory"] == "Cofactor Biosynthesis"]["lambda"].values
    tra_kos = t1_df[t1_df["subcategory"] == "Transport/Homeostasis"]["lambda"].values

    print(f"\n  Resistance/Detoxification (n={len(res_kos)}): median λ={np.median(res_kos):.3f}, "
          f"IQR={np.percentile(res_kos, 25):.3f}–{np.percentile(res_kos, 75):.3f}")
    print(f"  Cofactor Biosynthesis (n={len(cof_kos)}): median λ={np.median(cof_kos):.3f} "
          + (f"IQR={np.percentile(cof_kos, 25):.3f}–{np.percentile(cof_kos, 75):.3f}" if len(cof_kos) > 1 else "(only 1 KO)"))
    print(f"  Transport/Homeostasis (n={len(tra_kos)}): median λ={np.median(tra_kos):.3f}, "
          f"IQR={np.percentile(tra_kos, 25):.3f}–{np.percentile(tra_kos, 75):.3f}")

    # Proportion λ < 0.2
    if len(res_kos) > 0:
        pct_res_low = (res_kos < 0.2).mean() * 100
        print(f"  Resistance KOs with λ < 0.2: {pct_res_low:.0f}%")
    if len(cof_kos) > 0:
        pct_cof_low = (cof_kos < 0.2).mean() * 100
        print(f"  Cofactor KOs with λ < 0.2: {pct_cof_low:.0f}%")

    # Mann-Whitney U (only if ≥2 groups)
    if len(res_kos) >= 2 and len(cof_kos) >= 2:
        stat, pval = mannwhitneyu(res_kos, cof_kos, alternative="less")
        print(f"\n  Mann-Whitney U (resistance < cofactor): W={stat:.1f}, p={pval:.3e}")
    elif len(res_kos) >= 1 and len(cof_kos) == 1:
        print(f"\n  Note: only 1 cofactor KO passed filter — Mann-Whitney not applicable")
        print(f"  Cofactor λ = {cof_kos[0]:.3f}; resistance median λ = {np.median(res_kos):.3f}")

    # ── Violin plot ──────────────────────────────────────────────
    CAT_ORDER = [
        "Resistance/Detoxification",
        "Cofactor Biosynthesis",
        "Sensing/Regulation",
        "Transport/Homeostasis",
        "Unknown",
    ]
    CAT_COLORS = {
        "Resistance/Detoxification": "#d62728",
        "Cofactor Biosynthesis":     "#2ca02c",
        "Sensing/Regulation":        "#ff7f0e",
        "Transport/Homeostasis":     "#1f77b4",
        "Unknown":                   "#9467bd",
    }

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhline(0, color="grey", lw=0.8, ls="--", alpha=0.6)
    ax.axhline(1, color="grey", lw=0.8, ls="--", alpha=0.6)

    positions = []
    labels = []
    for i, cat in enumerate(CAT_ORDER):
        cat_data = t1_df[t1_df["subcategory"] == cat]["lambda"].values
        if len(cat_data) == 0:
            continue
        pos = len(positions) + 1
        positions.append(pos)
        labels.append(f"{cat}\n(n={len(cat_data)})")
        color = CAT_COLORS.get(cat, "#7f7f7f")
        if len(cat_data) >= 3:
            parts = ax.violinplot(cat_data, positions=[pos], widths=0.6,
                                  showmedians=True, showextrema=True)
            for pc in parts["bodies"]:
                pc.set_facecolor(color)
                pc.set_alpha(0.7)
            parts["cmedians"].set_color("black")
            parts["cbars"].set_color("black")
            parts["cmaxes"].set_color("black")
            parts["cmins"].set_color("black")
        ax.scatter(
            [pos + np.random.uniform(-0.1, 0.1) for _ in cat_data],
            cat_data, color=color, s=40, zorder=5, alpha=0.85
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Pagel's λ (per-KO PGLS)", fontsize=11)
    ax.set_title("Phylogenetic signal (λ) per Tier 1+2 KO by functional subcategory", fontsize=10)
    ax.set_ylim(-0.05, 1.15)
    plt.tight_layout()
    fig.savefig(DATA.parent / "per_ko_lambda_violin.pdf", dpi=150)
    print(f"  Saved per_ko_lambda_violin.pdf")
    plt.close()

# ──────────────────────────────────────────────────────────────────
# TASK 3: Per-metal resistance PGLS
# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TASK 3: Per-metal resistance PGLS")
print("=" * 60)

METALS = ["As", "Cu", "Ni", "Co", "Cd", "Zn", "Hg", "Fe", "Mn"]
task3_results = []

res_kos_meta = tier12[tier12["primary_category"] == "Resistance/Detoxification"].copy()
res_kos_meta = res_kos_meta[res_kos_meta["KO"].isin(nb25_kos)]

for metal in METALS:
    metal_kos = res_kos_meta[res_kos_meta["metals"].fillna("").str.contains(metal)]
    if len(metal_kos) == 0:
        print(f"  {metal}: no resistance KOs with data")
        continue

    metal_ko_ids = metal_kos["KO"].tolist()
    sub = ko_df[ko_df["ko"].isin(metal_ko_ids)].copy()
    sub = sub[sub["density"] > 0]

    # Sum densities per genus across metal's resistance KOs
    per_genus = sub.groupby("genus_lower").agg(
        metal_resistance_density=("density", "sum"),
        mean_levins_B_std=("mean_levins_B_std", "first"),
        mean_genome_mb=("mean_genome_mb", "first"),
    ).reset_index()
    per_genus = per_genus.dropna(subset=["mean_levins_B_std", "metal_resistance_density"])

    if len(per_genus) < 30:
        print(f"  {metal}: n={len(per_genus)} too small (KOs: {metal_ko_ids})")
        continue

    per_genus["density_z"] = zscore(per_genus["metal_resistance_density"])
    per_genus["genome_z"] = zscore(per_genus["mean_genome_mb"])

    try:
        res = run_pgls(
            per_genus, str(TREE), "mean_levins_B_std", ["density_z", "genome_z"],
            taxon_col="genus_lower", label=f"res_{metal}"
        )
        b, se, p = _extract_beta(res, "density_z")
        lam = res["lambda_est"]
        n = res["n"]
        task3_results.append({
            "metal": metal,
            "n_kos": len(metal_ko_ids),
            "ko_ids": "; ".join(metal_ko_ids),
            "n_genera": n,
            "beta": b,
            "SE": se,
            "p_value": p,
            "lambda": lam,
        })
        print(f"  {metal} ({len(metal_ko_ids)} KOs, n={n}): β={b:+.4f}, SE={se:.4f}, p={p:.3e}, λ={lam:.3f}")
    except Exception as e:
        print(f"  ERROR {metal}: {e}")

t3_df = pd.DataFrame(task3_results)
t3_df.to_csv(DATA / "task3_per_metal_resistance_pgls.csv", index=False)

if len(t3_df) > 0:
    print(f"\n  Summary:")
    print(f"  {'Metal':<6} {'KOs':<4} {'n':<6} {'β':>8} {'p':>10}")
    for _, r in t3_df.iterrows():
        sig = "*" if r["p_value"] < 0.05 else ""
        print(f"  {r['metal']:<6} {int(r['n_kos']):<4} {int(r['n_genera']):<6} {r['beta']:>+8.4f} {r['p_value']:>10.3e} {sig}")

    sig_metals = t3_df[t3_df["p_value"] < 0.05]
    print(f"  Metals with p < 0.05: {', '.join(sig_metals['metal'].tolist()) or 'none'}")

# ──────────────────────────────────────────────────────────────────
# TASK 4: Fitness burden PGLS
# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TASK 4: Fitness burden PGLS")
print("=" * 60)

# KOs with fitness evidence by primary category (Tier 1+2)
fit_kos = tier12[tier12["source_fitness"].notna()].copy()
print(f"  Tier1+2 KOs with FitnessBrowser evidence: {len(fit_kos)}")
print(f"  By category:\n{fit_kos['primary_category'].value_counts().to_string()}")

fit_res_kos = fit_kos[fit_kos["primary_category"] == "Resistance/Detoxification"]["KO"].tolist()
fit_tra_kos = fit_kos[fit_kos["primary_category"] == "Transport/Homeostasis"]["KO"].tolist()
fit_res_in_nb25 = [k for k in fit_res_kos if k in nb25_kos]
fit_tra_in_nb25 = [k for k in fit_tra_kos if k in nb25_kos]
print(f"\n  Fitness-supported resistance KOs in nb25: {len(fit_res_in_nb25)} / {len(fit_res_kos)}")
print(f"  Fitness-supported transport KOs in nb25: {len(fit_tra_in_nb25)} / {len(fit_tra_kos)}")

# Compute per-genus fitness density for resistance
res_fit_sub = ko_df[ko_df["ko"].isin(fit_res_in_nb25) & (ko_df["density"] > 0)]
res_fit_pg = res_fit_sub.groupby("genus_lower").agg(
    fit_res_density=("density", "sum"),
    mean_levins_B_std=("mean_levins_B_std", "first"),
    mean_genome_mb=("mean_genome_mb", "first"),
).reset_index()

# Compute per-genus fitness density for transport
tra_fit_sub = ko_df[ko_df["ko"].isin(fit_tra_in_nb25) & (ko_df["density"] > 0)]
tra_fit_pg = tra_fit_sub.groupby("genus_lower").agg(
    fit_tra_density=("density", "sum"),
).reset_index()

# Merge
fit_merged = res_fit_pg.merge(tra_fit_pg, on="genus_lower", how="inner")
fit_merged = fit_merged.dropna(subset=["mean_levins_B_std", "fit_res_density", "fit_tra_density"])
print(f"\n  Merged genera with both fitness density types: {len(fit_merged)}")

if len(fit_merged) >= 30:
    fit_merged["res_fit_z"] = zscore(fit_merged["fit_res_density"])
    fit_merged["tra_fit_z"] = zscore(fit_merged["fit_tra_density"])
    fit_merged["genome_z"] = zscore(fit_merged["mean_genome_mb"])

    try:
        res_fit = run_pgls(
            fit_merged, str(TREE), "mean_levins_B_std",
            ["res_fit_z", "tra_fit_z", "genome_z"],
            taxon_col="genus_lower", label="fit_burden"
        )
        b_res, se_res, p_res = _extract_beta(res_fit, "res_fit_z")
        b_tra, se_tra, p_tra = _extract_beta(res_fit, "tra_fit_z")
        b_gs, se_gs, p_gs = _extract_beta(res_fit, "genome_z")
        lam = res_fit["lambda_est"]
        n = res_fit["n"]
        print(f"\n  Fitness burden PGLS (n={n}, λ={lam:.3f}):")
        print(f"    Fitness-resistance density: β={b_res:+.4f}, SE={se_res:.4f}, p={p_res:.3e}")
        print(f"    Fitness-transport density:  β={b_tra:+.4f}, SE={se_tra:.4f}, p={p_tra:.3e}")
        print(f"    Genome size:                β={b_gs:+.4f}, SE={se_gs:.4f}, p={p_gs:.3e}")
        task4_summary = {
            "n": n, "lambda": lam,
            "fit_resistance_beta": b_res, "fit_resistance_SE": se_res, "fit_resistance_p": p_res,
            "fit_transport_beta": b_tra, "fit_transport_SE": se_tra, "fit_transport_p": p_tra,
        }
        with open(DATA / "task4_fitness_burden.json", "w") as f:
            json.dump(task4_summary, f, indent=2)
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()
        task4_summary = None
else:
    print("  Insufficient data for PGLS")
    task4_summary = None

# ──────────────────────────────────────────────────────────────────
# TASK 5: Expanded essential biosynthetic set
# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TASK 5: Expanded essential biosynthetic set PGLS")
print("=" * 60)

essential_files = {
    "aa":         "landscape_aa_metab_density.csv",
    "cofactor":   "landscape_cofactor_vitamin_density.csv",
    "lipid":      "landscape_lipid_metab_density.csv",
    "nucleotide": "landscape_nucleotide_metab_density.csv",
}

essential_dfs = {}
for key, fname in essential_files.items():
    df = pd.read_csv(DATA / fname).dropna(subset=["genus_lower"])
    df = df.rename(columns={"ko_per_mb": f"{key}_density"})
    essential_dfs[key] = df[["genus_lower", f"{key}_density"]]

# Merge all essential categories
from functools import reduce
ess_merged = reduce(lambda l, r: l.merge(r, on="genus_lower", how="inner"), essential_dfs.values())
print(f"  Genera with all four essential category densities: {len(ess_merged)}")

# Sum to get total essential biosynthetic density
ess_merged["essential_density"] = (
    ess_merged["aa_density"] + ess_merged["cofactor_density"] +
    ess_merged["lipid_density"] + ess_merged["nucleotide_density"]
)

# Merge with primary PGLS data
ess_pg = ess_merged.merge(primary[["genus_lower", "mean_levins_B_std", "mean_genome_mb"]],
                           on="genus_lower", how="inner")
ess_pg = ess_pg.dropna(subset=["mean_levins_B_std", "essential_density"])
print(f"  After merging with primary PGLS data: {len(ess_pg)}")

if len(ess_pg) >= 50:
    ess_pg["ess_z"] = zscore(ess_pg["essential_density"])
    ess_pg["genome_z"] = zscore(ess_pg["mean_genome_mb"])

    try:
        res_ess = run_pgls(
            ess_pg, str(TREE), "mean_levins_B_std", ["ess_z", "genome_z"],
            taxon_col="genus_lower", label="essential_biosyn"
        )
        b_ess, se_ess, p_ess = _extract_beta(res_ess, "ess_z")
        lam_ess = res_ess["lambda_est"]
        n_ess = res_ess["n"]
        print(f"\n  Expanded essential biosynthetic PGLS (n={n_ess}):")
        print(f"    β={b_ess:+.4f}, SE={se_ess:.4f}, p={p_ess:.3e}, λ={lam_ess:.3f}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()
        b_ess, se_ess, p_ess, lam_ess, n_ess = None, None, None, None, None

    # Also run resistance-only PGLS for comparison
    amr_df = pd.read_csv(DATA / "landscape_amr_density.csv").dropna(subset=["genus_lower"])
    amr_df = amr_df.rename(columns={"ko_per_mb": "amr_density"})
    amr_pg = amr_df.merge(primary[["genus_lower", "mean_levins_B_std", "mean_genome_mb"]],
                           on="genus_lower", how="inner").dropna(subset=["mean_levins_B_std"])
    print(f"\n  AMR comparison PGLS (n={len(amr_pg)}):")
    if len(amr_pg) >= 30:
        amr_pg["amr_z"] = zscore(amr_pg["amr_density"])
        amr_pg["genome_z"] = zscore(amr_pg["mean_genome_mb"])
        try:
            res_amr = run_pgls(
                amr_pg, str(TREE), "mean_levins_B_std", ["amr_z", "genome_z"],
                taxon_col="genus_lower", label="amr_compare"
            )
            b_amr, se_amr, p_amr = _extract_beta(res_amr, "amr_z")
            lam_amr = res_amr["lambda_est"]
            n_amr = res_amr["n"]
            print(f"    β={b_amr:+.4f}, SE={se_amr:.4f}, p={p_amr:.3e}, λ={lam_amr:.3f}")
        except Exception as e:
            print(f"  AMR ERROR: {e}")
            b_amr, p_amr = None, None

    # Split-magnitude permutation test (β essential vs β resistance)
    # Permute: randomly assign landscape densities to 'essential' or 'resistance' label
    # and compute the difference in β — then compare to observed difference
    if b_ess is not None and "b_amr" in dir() and b_amr is not None:
        obs_diff = b_ess - b_amr  # expected: negative (essential more negative)
        print(f"\n  Observed β difference (essential − resistance): {obs_diff:+.4f}")

        # Permutation (simplified: bootstrap from the ranked table)
        # Use ranking approach: from KEGG ranking, pick essential vs accessory categories
        kegg_df = pd.read_csv(DATA / "kegg_category_pgls_ranking.csv")
        essential_cats = ["Cofactor & vitamin biosyn.", "Amino acid metabolism",
                          "Nucleotide metabolism", "Lipid metabolism", "Translation",
                          "Replication & repair", "Protein folding"]
        accessory_cats = ["AMR genes", "ABC transporters", "Two-component systems",
                          "Cell motility", "Quorum sensing", "Xenobiotics metabolism",
                          "Terpenoid/polyketide", "Transcription", "Carbohydrate metabolism"]
        ess_betas = kegg_df[kegg_df["category"].isin(essential_cats)]["beta"].values
        acc_betas = kegg_df[kegg_df["category"].isin(accessory_cats)]["beta"].values

        n_perm = 5000
        rng = np.random.default_rng(42)
        all_betas = np.concatenate([ess_betas, acc_betas])
        null_diffs = []
        for _ in range(n_perm):
            perm = rng.permutation(all_betas)
            null_diff = perm[:len(ess_betas)].mean() - perm[len(ess_betas):].mean()
            null_diffs.append(null_diff)
        null_diffs = np.array(null_diffs)
        obs_cat_diff = ess_betas.mean() - acc_betas.mean()
        perm_p = (null_diffs <= obs_cat_diff).mean()
        print(f"  Category-level split: essential mean β={ess_betas.mean():+.4f}, accessory mean β={acc_betas.mean():+.4f}")
        print(f"  Observed difference: {obs_cat_diff:+.4f}")
        print(f"  Permutation p (essential < accessory): {perm_p:.4f}")

    # Save task5 summary
    task5_summary = {
        "essential_set_n_categories": 4,
        "essential_categories": list(essential_files.keys()),
        "n_genera": n_ess,
        "beta": float(b_ess) if b_ess is not None else None,
        "SE": float(se_ess) if se_ess is not None else None,
        "p_value": float(p_ess) if p_ess is not None else None,
        "lambda": float(lam_ess) if lam_ess is not None else None,
    }
    with open(DATA / "task5_essential_biosyn.json", "w") as f:
        json.dump(task5_summary, f, indent=2)

# ──────────────────────────────────────────────────────────────────
# Summary report
# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
if len(t1_df) > 0:
    print(f"\nTask 1 — Per-KO λ ({len(t1_df)} KOs fitted):")
    for cat in t1_df["subcategory"].unique():
        sub = t1_df[t1_df["subcategory"] == cat]["lambda"].values
        print(f"  {cat} (n={len(sub)}): median λ={np.median(sub):.3f}")
    print(f"  Violin plot saved: per_ko_lambda_violin.pdf")

print(f"\nTask 3 — Per-metal resistance PGLS:")
if len(t3_df) > 0:
    for _, r in t3_df.iterrows():
        print(f"  {r['metal']}: β={r['beta']:+.4f}, p={r['p_value']:.3e}")
else:
    print("  No metals had sufficient data")

print(f"\nTask 4 — Fitness burden PGLS: see task4_fitness_burden.json")
print(f"Task 5 — Expanded essential PGLS: see task5_essential_biosyn.json")
