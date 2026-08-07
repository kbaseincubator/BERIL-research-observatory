"""
Rank KEGG functional categories by PGLS β (niche breadth ~ density + genome_size).
Also includes the expanded cofactor/vitamin set and the metal-gene primary set.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import run_pgls

DATA = Path("data")
TREE = DATA / "gtdb_bac_genus_pruned.tree"

primary = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")


def zscore(x):
    return (x - x.mean()) / x.std(ddof=1)


def _extract_beta(res, key):
    if "betas" in res:
        return res["betas"][key], res["SEs"][key], res["p_values"][key]
    return res["beta"], res["SE"], res["p_value"]


landscape_files = {
    "Amino acid metabolism":       "landscape_aa_metab_density.csv",
    "ABC transporters":            "landscape_abc_transporters_density.csv",
    "AMR genes":                   "landscape_amr_density.csv",
    "Carbohydrate metabolism":     "landscape_carbohydrate_metab_density.csv",
    "Cell growth & death":         "landscape_cell_growth_death_density.csv",
    "Cell motility":               "landscape_cell_motility_density.csv",
    "Cofactor & vitamin biosyn.":  "landscape_cofactor_vitamin_density.csv",
    "Energy metabolism":           "landscape_energy_metab_density.csv",
    "Glycan biosynthesis":         "landscape_glycan_biosyn_density.csv",
    "Lipid metabolism":            "landscape_lipid_metab_density.csv",
    "Nucleotide metabolism":       "landscape_nucleotide_metab_density.csv",
    "Protein folding":             "landscape_protein_folding_density.csv",
    "Quorum sensing":              "landscape_quorum_sensing_density.csv",
    "Replication & repair":        "landscape_replication_repair_density.csv",
    "Secondary metabolism":        "landscape_secondary_metab_density.csv",
    "Sporulation":                 "landscape_sporulation_density.csv",
    "Terpenoid/polyketide":        "landscape_terpenoid_polyket_density.csv",
    "Transcription":               "landscape_transcription_density.csv",
    "Translation":                 "landscape_translation_density.csv",
    "Two-component systems":       "landscape_two_component_density.csv",
    "Xenobiotics metabolism":      "landscape_xenobiotics_density.csv",
}

results = []

for cat_name, fname in landscape_files.items():
    fpath = DATA / fname
    if not fpath.exists():
        print(f"  MISSING: {fname}")
        continue
    try:
        cat_df = pd.read_csv(fpath).dropna(subset=["genus_lower"])
        cat_df = cat_df.rename(columns={"ko_per_mb": "cat_density"})
        merged = primary.merge(cat_df[["genus_lower", "cat_density"]], on="genus_lower", how="inner")
        merged = merged.dropna(subset=["mean_levins_B_std", "cat_density", "mean_genome_mb"])
        merged = merged[merged["cat_density"] > 0]
        if len(merged) < 50:
            print(f"  SKIP {cat_name}: n={len(merged)} too small")
            continue
        merged["density_z"] = zscore(merged["cat_density"])
        merged["genome_z"] = zscore(merged["mean_genome_mb"])
        res = run_pgls(
            merged, str(TREE), "mean_levins_B_std", ["density_z", "genome_z"],
            taxon_col="genus_lower", label=f"cat_{cat_name[:20]}"
        )
        b, se, p = _extract_beta(res, "density_z")
        lam = res["lambda_est"]
        n = res["n"]
        results.append({
            "category": cat_name,
            "n": n,
            "beta": b,
            "SE": se,
            "p_value": p,
            "lambda": lam,
        })
        print(f"  {cat_name}: β={b:+.4f}, p={p:.3e}, λ={lam:.3f}, n={n}")
    except Exception as e:
        print(f"  ERROR {cat_name}: {e}")
        import traceback; traceback.print_exc()

# Add metal-gene primary set (ko_per_mb_primary) for reference
try:
    merged_metal = primary.dropna(subset=["mean_levins_B_std", "ko_per_mb_primary", "mean_genome_mb"])
    merged_metal = merged_metal[merged_metal["ko_per_mb_primary"] > 0]
    merged_metal = merged_metal.copy()
    merged_metal["density_z"] = zscore(merged_metal["ko_per_mb_primary"])
    merged_metal["genome_z"] = zscore(merged_metal["mean_genome_mb"])
    res_metal = run_pgls(
        merged_metal, str(TREE), "mean_levins_B_std", ["density_z", "genome_z"],
        taxon_col="genus_lower", label="metal_primary"
    )
    b, se, p = _extract_beta(res_metal, "density_z")
    lam = res_metal["lambda_est"]
    n = res_metal["n"]
    results.append({
        "category": "Metal genes (primary set, 140 KO)",
        "n": n, "beta": b, "SE": se, "p_value": p, "lambda": lam,
    })
    print(f"  Metal genes primary: β={b:+.4f}, p={p:.3e}, λ={lam:.3f}, n={n}")
except Exception as e:
    print(f"  ERROR metal primary: {e}")

df = pd.DataFrame(results).sort_values("beta")
df["rank"] = range(1, len(df) + 1)

print("\n\n=== RANKED TABLE (most negative β first) ===")
print(f"{'Rank':<5} {'Category':<35} {'β':>8} {'SE':>8} {'p':>10} {'λ':>7} {'n':>6}")
print("-" * 85)
for _, row in df.iterrows():
    marker = " ◀" if "Cofactor" in row["category"] else (" ★" if "Metal" in row["category"] else "")
    print(f"{int(row['rank']):<5} {row['category']:<35} {row['beta']:>+8.4f} {row['SE']:>8.4f} {row['p_value']:>10.3e} {row['lambda']:>7.3f} {int(row['n']):>6}{marker}")

# Cofactor rank
cof_row = df[df["category"].str.contains("Cofactor")]
if len(cof_row) > 0:
    cof_rank = cof_row.iloc[0]["rank"]
    cof_beta = cof_row.iloc[0]["beta"]
    total = len(df)
    pct_rank = (1 - (cof_rank - 1) / total) * 100
    print(f"\n=== COFACTOR SUMMARY ===")
    print(f"  Rank: {int(cof_rank)} of {total}")
    print(f"  β = {cof_beta:+.4f}")
    print(f"  Stronger than {pct_rank:.0f}% of all categories")
    pct_stronger_neg = (df["beta"] < cof_beta).sum() / total * 100
    print(f"  Categories with more negative β: {(df['beta'] < cof_beta).sum()}")

df.to_csv(DATA / "kegg_category_pgls_ranking.csv", index=False)
print(f"\nSaved to data/kegg_category_pgls_ranking.csv")
