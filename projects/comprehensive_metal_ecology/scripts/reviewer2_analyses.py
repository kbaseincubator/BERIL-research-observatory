"""
Reviewer 2 analyses:
  1. Expanded cofactor PGLS (KEGG cofactors+vitamins as broader test, + genome-size control)
  2. Comparator PGLS: metal-gene β when controlling for 6 major KEGG category densities
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import run_pgls

DATA = Path("data")
TREE = DATA / "gtdb_bac_genus_pruned.tree"

primary = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")

# ─── helpers ─────────────────────────────────────────────────────────────────

def zscore(x):
    return (x - x.mean()) / x.std(ddof=1)


def _extract_beta(res, key):
    if "betas" in res:
        return res["betas"][key], res["SEs"][key], res["p_values"][key]
    return res["beta"], res["SE"], res["p_value"]


# ─── TASK 1: expanded cofactor identification ─────────────────────────────────

print("=== TASK 1: Expanded cofactor gene set ===")

df_ko = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")
cof_modules = ["M00175", "M00176", "M00842", "M00193", "M00194", "M00121", "M00122"]
mask_cat = df_ko["primary_category"] == "Cofactor Biosynthesis"
mask_is_cof = df_ko["is_cofactor"] == True
mask_mod = df_ko["source_kegg_module"].fillna("").apply(
    lambda x: any(m in x for m in cof_modules)
)
expanded_cof_kos = df_ko[mask_cat | mask_is_cof | mask_mod]["KO"].tolist()
n_expanded = len(expanded_cof_kos)
print(f"  Expanded cofactor set: {n_expanded} KOs")
print(f"    - is_cofactor=True: {mask_is_cof.sum()}")
print(f"    - primary_category=='Cofactor Biosynthesis': {mask_cat.sum()}")
print(f"    - module match: {mask_mod.sum()}")

# Subset available in parquet (for jackknife reference)
pq = pd.read_parquet(DATA / "nb26_category_ko_counts.parquet")
in_parquet = set(expanded_cof_kos) & set(pq["ko"].unique())
print(f"  KOs with pangenome density data: {len(in_parquet)} / {n_expanded}")
print(f"  KOs in parquet: {sorted(in_parquet)}")

# ─── TASK 1: PGLS with KEGG cofactor/vitamin density (382-KO expanded proxy) ─

print("\n=== TASK 1b: PGLS with KEGG cofactor/vitamin density + genome size ===")

cof_vit = pd.read_csv(DATA / "landscape_cofactor_vitamin_density.csv")
cof_vit = cof_vit.rename(columns={"ko_per_mb": "cofvit_per_mb"})
cof_vit = cof_vit.dropna(subset=["genus_lower"])

merged = primary.merge(cof_vit[["genus_lower", "cofvit_per_mb"]], on="genus_lower", how="inner")
merged = merged.dropna(subset=["mean_levins_B_std", "cofvit_per_mb", "mean_genome_mb"])
merged["cofvit_z"] = zscore(merged["cofvit_per_mb"])
merged["genome_mb_z"] = zscore(merged["mean_genome_mb"])
print(f"  Merged n (cofactor/vitamin + primary): {len(merged)}")

# single-predictor PGLS (cofvit only)
res_1pred = run_pgls(
    merged, str(TREE), "mean_levins_B_std", ["cofvit_z"],
    taxon_col="genus_lower", label="cofvit_1pred"
)
beta_1, se_1, p_1 = _extract_beta(res_1pred, "cofvit_z")
lam_1 = res_1pred["lambda_est"]
print(f"\n  1-predictor (cofvit only): β={beta_1:.4f}, SE={se_1:.4f}, p={p_1:.2e}, λ={lam_1:.3f}")

# 2-predictor PGLS (cofvit + genome size)
res_2pred = run_pgls(
    merged, str(TREE), "mean_levins_B_std", ["cofvit_z", "genome_mb_z"],
    taxon_col="genus_lower", label="cofvit_2pred"
)
beta_cof_adj, se_cof_adj, p_cof_adj = _extract_beta(res_2pred, "cofvit_z")
beta_gs_adj, se_gs_adj, p_gs_adj = _extract_beta(res_2pred, "genome_mb_z")
lam_2 = res_2pred["lambda_est"]
n_2 = res_2pred["n"]
print(f"\n  2-predictor (cofvit + genome size, n={n_2}):")
print(f"    cofvit: β={beta_cof_adj:.4f}, SE={se_cof_adj:.4f}, p={p_cof_adj:.2e}")
print(f"    genome_size: β={beta_gs_adj:.4f}, SE={se_gs_adj:.4f}, p={p_gs_adj:.2e}")
print(f"    λ={lam_2:.3f}")

# ─── TASK 1c: resistance PGLS for comparison ─────────────────────────────────

print("\n=== TASK 1c: Resistance β for reference ===")
# Load resistance density from category results (already computed: β = +0.003, p = 0.656)
cat_res = pd.read_csv(DATA / "03_category_pgls_results.csv")
resist_row = cat_res[cat_res["label"] == "F1.1_resistance"].iloc[0]
print(f"  Resistance: β={resist_row['beta']:.4f}, p={resist_row['p_value']:.3e}")
delta_beta = abs(beta_1 - resist_row["beta"])
print(f"  Δβ (cofvit − resistance, 1-pred): {delta_beta:.4f}")
delta_beta_adj = abs(beta_cof_adj - resist_row["beta"])
print(f"  Δβ (cofvit − resistance, 2-pred): {delta_beta_adj:.4f}")

# ─── TASK 2: comparator PGLS ──────────────────────────────────────────────────

print("\n\n=== TASK 2: Comparator PGLS (metal-gene β when controlling for other categories) ===")

comparators = {
    "carbohydrate_metabolism": DATA / "landscape_carbohydrate_metab_density.csv",
    "amino_acid_metabolism":    DATA / "landscape_aa_metab_density.csv",
    "energy_metabolism":        DATA / "landscape_energy_metab_density.csv",
    "membrane_transport_ABC":   DATA / "landscape_abc_transporters_density.csv",
    "translation":              DATA / "landscape_translation_density.csv",
    "transcription":            DATA / "landscape_transcription_density.csv",
}

results = []
for comp_name, comp_path in comparators.items():
    try:
        comp_df = pd.read_csv(comp_path)
        comp_df = comp_df.dropna(subset=["genus_lower"])
        comp_df = comp_df.rename(columns={"ko_per_mb": "comp_per_mb"})
        merged_c = primary.merge(
            comp_df[["genus_lower", "comp_per_mb"]],
            on="genus_lower", how="inner"
        )
        merged_c = merged_c.dropna(subset=["mean_levins_B_std", "ko_per_mb_primary",
                                            "mean_genome_mb", "comp_per_mb"])
        merged_c["metal_z"]  = zscore(merged_c["ko_per_mb_primary"])
        merged_c["comp_z"]   = zscore(merged_c["comp_per_mb"])
        merged_c["genome_z"] = zscore(merged_c["mean_genome_mb"])
        n_c = len(merged_c)

        res = run_pgls(
            merged_c, str(TREE), "mean_levins_B_std",
            ["metal_z", "comp_z", "genome_z"],
            taxon_col="genus_lower", label=f"comp_{comp_name}"
        )
        b_metal, se_metal, p_metal = _extract_beta(res, "metal_z")
        b_comp,  se_comp,  p_comp  = _extract_beta(res, "comp_z")
        lam = res["lambda_est"]
        print(f"\n  {comp_name} (n={n_c}):")
        print(f"    metal β={b_metal:.4f}, SE={se_metal:.4f}, p={p_metal:.2e}")
        print(f"    comp  β={b_comp:.4f},  SE={se_comp:.4f},  p={p_comp:.2e}")
        print(f"    λ={lam:.3f}")
        results.append({
            "comparator": comp_name,
            "n": n_c,
            "metal_beta": b_metal,
            "metal_SE":   se_metal,
            "metal_p":    p_metal,
            "comp_beta":  b_comp,
            "comp_SE":    se_comp,
            "comp_p":     p_comp,
            "lambda_est": lam,
        })
    except Exception as e:
        print(f"  {comp_name}: ERROR {e}")
        import traceback; traceback.print_exc()

results_df = pd.DataFrame(results)
results_df.to_csv(DATA / "comparator_pgls_results.csv", index=False)
print("\n\nComparator results saved to data/comparator_pgls_results.csv")
print(results_df[["comparator", "n", "metal_beta", "metal_p"]].to_string(index=False))

# ─── Summary ─────────────────────────────────────────────────────────────────

print("\n\n=== SUMMARY ===")
print(f"Expanded cofactor set: {n_expanded} KOs ({len(in_parquet)} with pangenome density)")
print(f"KEGG cofactor/vitamin proxy (382 KOs, n={n_2}):")
print(f"  β (unadjusted) = {beta_1:.4f}, p = {p_1:.2e}")
print(f"  β (+ genome size) = {beta_cof_adj:.4f}, p = {p_cof_adj:.2e}")
print(f"Resistance β = {resist_row['beta']:.4f}")
print(f"Δβ (cofvit vs resistance, genome-adjusted) = {delta_beta_adj:.4f}")

if len(results) > 0:
    sig_models = [r for r in results if r["metal_p"] < 0.05]
    print(f"\nComparator models: {len(results)} total, {len(sig_models)} with metal p < 0.05")
    metal_betas = [r["metal_beta"] for r in results]
    print(f"Metal β range across comparators: {min(metal_betas):.4f} to {max(metal_betas):.4f}")
    print(f"Max metal p-value: {max(r['metal_p'] for r in results):.2e}")

# Save summary
summary = {
    "expanded_cofactor_n_kos": n_expanded,
    "expanded_cofactor_n_with_data": len(in_parquet),
    "kegg_cofvit_n": n_2,
    "kegg_cofvit_beta_unadj": float(beta_1),
    "kegg_cofvit_p_unadj": float(p_1),
    "kegg_cofvit_beta_gs_adj": float(beta_cof_adj),
    "kegg_cofvit_p_gs_adj": float(p_cof_adj),
    "kegg_cofvit_lambda": float(lam_2),
    "resistance_beta": float(resist_row["beta"]),
    "delta_beta_cofvit_vs_resistance_gs_adj": float(delta_beta_adj),
    "comparator_results": results,
}
with open(DATA / "reviewer2_analyses_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSummary saved to data/reviewer2_analyses_summary.json")
