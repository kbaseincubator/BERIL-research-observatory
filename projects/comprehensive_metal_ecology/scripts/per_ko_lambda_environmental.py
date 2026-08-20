"""
Corrected per-KO lambda analysis: environmental metal concentration as response.
Tests all available metal representations:
  1. GeoROC bedrock metals (Cu, Zn, Ni, Cr, Co, Pb) — global, 9,800–9,900 genera
  2. AusMicrobiome NGSA soil metals (Cu, Zn, Pb, Ni, Co, As, Cr, Hg) — 933 genera

HGT hypothesis: resistance KOs should show low λ (≈0) when predicting environmental
metal concentrations, because HGT decouples gene presence from phylogeny.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import run_pgls

DATA = Path("data")
TREE = DATA / "gtdb_bac_genus_pruned.tree"
MICROBEATLAS_DATA = Path("../microbeatlas_metal_ecology/data")

print("Loading data...")
nb25 = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
nb25["genus_lower"] = nb25["genus_lower"].str.replace("g__", "", regex=False)

spark = pd.read_csv(DATA / "01_genus_ko_density_spark.csv")
curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")
env_global = pd.read_csv(DATA / "genus_lat_env_covariates.csv")
# AusMicrobiome NGSA per-genus soil metals
env_ngsa = pd.read_csv(MICROBEATLAS_DATA / "aus_genus_geo_niche.csv")

tier12 = curated[curated["evidence_tier"].isin(["Tier 1", "Tier 2"])].copy()

# KOs that were successfully fitted in the niche breadth analysis (from Task 1)
FITTED_KOS = [
    "K02007", "K02009", "K02012", "K02069", "K02190", "K02225", "K02230",
    "K03325", "K03446", "K03523", "K03635", "K03673", "K07644", "K07665",
    "K07785", "K07787", "K08225", "K09883", "K11601", "K11602", "K11604",
    "K11605", "K11606", "K11707", "K11708", "K11709", "K13638", "K15726",
    "K17686", "K18367", "K19594", "K19595", "K19976", "K25119", "K25287",
]

ko_meta = tier12.set_index("KO")[["gene_name", "primary_category"]].to_dict("index")

# Base density table (strip g__ prefix, already done above)
density_base = nb25[nb25["ko"].isin(FITTED_KOS)].copy()
density_base = density_base.merge(
    spark[["genus_lower", "n_genomes", "mean_genome_mb"]],
    on="genus_lower", how="inner"
)
density_base["density"] = (
    density_base["n_genomes_with_ko"] /
    (density_base["n_genomes"] * density_base["mean_genome_mb"])
)

print(f"KOs in density table: {density_base['ko'].nunique()}")
print(f"Genera in density table: {density_base['genus_lower'].nunique()}")

# Metal datasets
METAL_SOURCES = {
    "GeoROC (bedrock)": {
        "data": env_global,
        "metals": {
            "Cu": "georoc_Cu_log",
            "Zn": "georoc_Zn_log",
            "Ni": "georoc_Ni_log",
            "Cr": "georoc_Cr_log",
            "Co": "georoc_Co_log",
            "Pb": "georoc_Pb_log",
        },
        "log_transform": False,  # already log-transformed
    },
    "NGSA soil (AusMicrobiome)": {
        "data": env_ngsa,
        "metals": {
            "Cu": "Cu_mean",
            "Zn": "Zn_mean",
            "Pb": "Pb_mean",
            "Ni": "Ni_mean",
            "Co": "Co_mean",
            "As": "As_mean",
            "Cr": "Cr_mean",
            "Hg": "Hg_mean",
        },
        "log_transform": True,   # raw ppm values, apply log1p
    },
}


def zscore(x):
    return (x - x.mean()) / x.std(ddof=1)


def _extract_beta(res, key):
    if "betas" in res:
        return res["betas"][key], res["SEs"][key], res["p_values"][key]
    return res["beta"], res["SE"], res["p_value"]


# Store all results
all_results = []
unconditional_lambdas = {}

# ── For each metal source ──────────────────────────────────────────────────────
for source_name, source_cfg in METAL_SOURCES.items():
    print(f"\n{'='*60}")
    print(f"SOURCE: {source_name}")
    print(f"{'='*60}")
    metal_df = source_cfg["data"]
    do_log = source_cfg["log_transform"]

    for metal_name, metal_col in source_cfg["metals"].items():
        if metal_col not in metal_df.columns:
            print(f"  SKIP {metal_name}: column {metal_col} not found")
            continue

        metal_sub = metal_df[["genus_lower", metal_col]].dropna().copy()
        metal_sub = metal_sub[metal_sub[metal_col] > -90]  # exclude sentinels
        if do_log:
            metal_sub = metal_sub[metal_sub[metal_col] > 0]
            metal_sub["metal_val"] = np.log1p(metal_sub[metal_col])
        else:
            metal_sub["metal_val"] = metal_sub[metal_col]
        n_metal = len(metal_sub)
        print(f"\n--- {metal_name} ({source_name}, n_genera={n_metal}) ---")

        # Unconditional λ (metal concentration ~ intercept only)
        key_unc = f"{source_name}:{metal_name}"
        uncond_lam = None
        null_df = metal_sub[["genus_lower", "metal_val"]].copy()
        null_df["dummy_z"] = 0.0
        try:
            res_null = run_pgls(
                null_df, str(TREE), "metal_val", ["dummy_z"],
                taxon_col="genus_lower", label=f"null_{metal_name[:2]}"
            )
            uncond_lam = res_null["lambda_est"]
            unconditional_lambdas[key_unc] = uncond_lam
            print(f"  Unconditional λ: {uncond_lam:.3f} (n={res_null['n']})")
        except Exception as e:
            print(f"  Unconditional λ error: {e}")
            unconditional_lambdas[key_unc] = None

        # Per-KO λ
        metal_results = []
        for ko_id in FITTED_KOS:
            sub = density_base[density_base["ko"] == ko_id].copy()
            sub = sub[sub["density"] > 0]
            sub = sub.merge(metal_sub[["genus_lower", "metal_val"]],
                            on="genus_lower", how="inner")
            if len(sub) < 20:
                continue
            sub["density_z"] = zscore(sub["density"])
            try:
                res = run_pgls(
                    sub, str(TREE), "metal_val", ["density_z"],
                    taxon_col="genus_lower", label=f"{ko_id}_{metal_name[:2]}"
                )
                b, se, p = _extract_beta(res, "density_z")
                lam = res["lambda_est"]
                n = res["n"]
                meta = ko_meta.get(ko_id, {})
                row = {
                    "source": source_name,
                    "metal": metal_name,
                    "ko_id": ko_id,
                    "gene_name": meta.get("gene_name", ""),
                    "subcategory": meta.get("primary_category", "Unknown"),
                    "lambda": lam,
                    "beta": b,
                    "SE": se,
                    "p_value": p,
                    "n_genera": n,
                    "unconditional_lambda": uncond_lam,
                }
                metal_results.append(row)
                print(f"  {ko_id} ({meta.get('gene_name','')!s:<12} "
                      f"[{meta.get('primary_category','')!s:<25}]: "
                      f"λ={lam:.3f}, β={b:+.5f}, p={p:.3e}, n={n}")
            except Exception as e:
                print(f"  ERROR {ko_id}: {e}")

        print(f"\n  Fitted {len(metal_results)} KOs for {metal_name} ({source_name})")
        t_df = pd.DataFrame(metal_results)
        if len(t_df) == 0:
            continue

        # Per-subcategory summary
        for cat in t_df["subcategory"].unique():
            cdf = t_df[t_df["subcategory"] == cat]
            lams = cdf["lambda"].values
            print(f"    {cat} (n={len(lams)}): "
                  f"median λ={np.median(lams):.3f}, "
                  f"IQR={np.percentile(lams,25):.3f}–{np.percentile(lams,75):.3f}")

        res_lams = t_df[t_df["subcategory"] == "Resistance/Detoxification"]["lambda"].values
        other_lams = t_df[t_df["subcategory"] != "Resistance/Detoxification"]["lambda"].values
        if len(res_lams) >= 2 and len(other_lams) >= 2:
            stat, pval = mannwhitneyu(res_lams, other_lams, alternative="less")
            print(f"    Mann-Whitney U (resistance λ < others): W={stat:.1f}, p={pval:.3e}")
        else:
            print(f"    Insufficient KOs for Mann-Whitney")

        all_results.extend(metal_results)


# ── Save results ───────────────────────────────────────────────────────────────
all_df = pd.DataFrame(all_results)
all_df.to_csv(DATA / "per_ko_lambda_environmental.csv", index=False)
print(f"\n\nSaved {len(all_df)} rows to data/per_ko_lambda_environmental.csv")

# ── Violin plots: one per source × metal ──────────────────────────────────────
CAT_ORDER = [
    "Resistance/Detoxification", "Cofactor Biosynthesis",
    "Sensing/Regulation", "Transport/Homeostasis", "Unknown",
]
CAT_COLORS = {
    "Resistance/Detoxification": "#d62728",
    "Cofactor Biosynthesis":     "#2ca02c",
    "Sensing/Regulation":        "#ff7f0e",
    "Transport/Homeostasis":     "#1f77b4",
    "Unknown":                   "#9467bd",
}

# Aggregate violin: one panel per source, pooled across metals
for source_name in METAL_SOURCES:
    s_df = all_df[all_df["source"] == source_name]
    if len(s_df) < 5:
        continue

    # Average λ per KO × subcategory (across metals)
    agg = s_df.groupby(["ko_id", "subcategory"])["lambda"].median().reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axhline(0, color="grey", lw=0.7, ls=":", alpha=0.5)
    ax.axhline(1, color="grey", lw=0.7, ls=":", alpha=0.5)

    # Unconditional λ reference (mean across metals in this source)
    unc_vals = [v for k, v in unconditional_lambdas.items()
                if k.startswith(source_name) and v is not None]
    if unc_vals:
        mean_unc = np.mean(unc_vals)
        ax.axhline(mean_unc, color="black", lw=1.2, ls="--", alpha=0.8,
                   label=f"Mean unconditional λ = {mean_unc:.3f}")
        ax.legend(fontsize=8)

    positions = []
    labels = []
    rng = np.random.default_rng(42)
    for cat in CAT_ORDER:
        cat_data = agg[agg["subcategory"] == cat]["lambda"].values
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
            for part_key in ("cmedians", "cbars", "cmaxes", "cmins"):
                parts[part_key].set_color("black")
        jitter = rng.uniform(-0.12, 0.12, size=len(cat_data))
        ax.scatter(pos + jitter, cat_data, color=color, s=40, zorder=5, alpha=0.85)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Median Pagel's λ across metals (PGLS: soil metal ~ KO density)", fontsize=9)
    slug = source_name.split()[0].lower()
    ax.set_title(f"Per-KO λ by subcategory — {source_name}", fontsize=10)
    ax.set_ylim(-0.05, 1.15)
    plt.tight_layout()
    fname = DATA.parent / f"per_ko_lambda_environmental_{slug}.pdf"
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved violin plot: {fname}")

# ── Summary table ──────────────────────────────────────────────────────────────
print("\n\n" + "="*70)
print("MASTER SUMMARY: λ by subcategory and source")
print("="*70)
for source_name in METAL_SOURCES:
    s_df = all_df[all_df["source"] == source_name]
    if len(s_df) == 0:
        continue
    print(f"\n{source_name}:")
    unc_vals = [v for k, v in unconditional_lambdas.items()
                if k.startswith(source_name) and v is not None]
    print(f"  Unconditional λ (mean across metals): "
          f"{np.mean(unc_vals):.3f} (range {min(unc_vals):.3f}–{max(unc_vals):.3f})"
          if unc_vals else "  Unconditional λ: N/A")
    agg = s_df.groupby(["ko_id","subcategory"])["lambda"].median().reset_index()
    res_lams = agg[agg["subcategory"] == "Resistance/Detoxification"]["lambda"].values
    other_lams = agg[agg["subcategory"] != "Resistance/Detoxification"]["lambda"].values
    for cat in CAT_ORDER:
        cdf = agg[agg["subcategory"] == cat]
        if len(cdf) == 0:
            continue
        lams = cdf["lambda"].values
        print(f"    {cat:<30} n={len(lams)}, median λ={np.median(lams):.3f}, "
              f"IQR={np.percentile(lams,25):.3f}–{np.percentile(lams,75):.3f}")
    if len(res_lams) >= 2 and len(other_lams) >= 2:
        stat, pval = mannwhitneyu(res_lams, other_lams, alternative="less")
        print(f"    Mann-Whitney U (resistance λ < others): W={stat:.1f}, p={pval:.3e}")
    else:
        print(f"    Mann-Whitney: insufficient KOs")

print("\nDone.")
