"""
Manuscript revision analyses:
  1. Genome-size-adjusted functional landscape PGLS (19 categories + P1 reference)
  2. Supplementary KO curation table for Tl, Al, S
  3. Resistance vs cofactor core/auxiliary comparison (Fisher's exact)
"""

import sys
import os
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore")

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data")
SCRIPTS = Path("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/scripts")
sys.path.insert(0, str(SCRIPTS))

from pgls_utils import run_pgls

TREE = DATA / "gtdb_bac_genus_pruned.tree"
MAIN_INPUT = DATA / "01_pgls_input_bacteria.csv"

# ─────────────────────────────────────────────────────────────────────────────
# 1. GENOME-SIZE-ADJUSTED FUNCTIONAL LANDSCAPE
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Task 1: Genome-size-adjusted landscape PGLS ===")

main = pd.read_csv(MAIN_INPUT)
# main has: genus_lower, ko_per_mb_primary, mean_genome_mb, mean_levins_B_std,
#           phylum, kingdom, predictor_z, genome_mb_z

# Load existing functional_landscape_results.csv for category metadata
existing = pd.read_csv(DATA / "functional_landscape_results.csv")
# Keep only the 19 non-reference rows
landscape_cats = existing[existing["group"] != "metal_reference"].copy()

# Mapping from category key → landscape density file stem
# The landscape files have genus_lower, ko_per_mb, n_mags
LANDSCAPE_FILES = {
    "aa_metab":          DATA / "landscape_aa_metab_density.csv",
    "abc_transporters":  DATA / "landscape_abc_transporters_density.csv",
    "amr":               DATA / "landscape_amr_density.csv",
    "carbohydrate_metab":DATA / "landscape_carbohydrate_metab_density.csv",
    "cell_growth_death": DATA / "landscape_cell_growth_death_density.csv",
    "cell_motility":     DATA / "landscape_cell_motility_density.csv",
    "cofactor_vitamin":  DATA / "landscape_cofactor_vitamin_density.csv",
    "energy_metab":      DATA / "landscape_energy_metab_density.csv",
    "glycan_biosyn":     DATA / "landscape_glycan_biosyn_density.csv",
    "lipid_metab":       DATA / "landscape_lipid_metab_density.csv",
    "nucleotide_metab":  DATA / "landscape_nucleotide_metab_density.csv",
    "protein_folding":   DATA / "landscape_protein_folding_density.csv",
    "quorum_sensing":    DATA / "landscape_quorum_sensing_density.csv",
    "replication_repair":DATA / "landscape_replication_repair_density.csv",
    "secondary_metab":   DATA / "landscape_secondary_metab_density.csv",
    "transcription":     DATA / "landscape_transcription_density.csv",
    "translation":       DATA / "landscape_translation_density.csv",
    "two_component":     DATA / "landscape_two_component_density.csv",
    "xenobiotics":       DATA / "landscape_xenobiotics_density.csv",
}

# Verify files exist
missing = {k: v for k, v in LANDSCAPE_FILES.items() if not v.exists()}
if missing:
    print(f"  WARNING: missing landscape files: {list(missing.keys())}")

results_adj = []

for cat_key, file_path in sorted(LANDSCAPE_FILES.items()):
    if not file_path.exists():
        print(f"  SKIP {cat_key}: file not found")
        continue

    dens = pd.read_csv(file_path)
    # Filter out rows with empty genus (first row artifact)
    dens = dens[dens["genus_lower"].notna() & (dens["genus_lower"] != "")]

    # Join with main to get mean_levins_B_std and genome_mb_z
    merged = dens.merge(
        main[["genus_lower", "mean_levins_B_std", "genome_mb_z", "phylum"]],
        on="genus_lower", how="inner"
    )

    # Z-score the density predictor
    mu = merged["ko_per_mb"].mean()
    sd = merged["ko_per_mb"].std()
    if sd == 0 or np.isnan(sd):
        print(f"  SKIP {cat_key}: zero SD in ko_per_mb")
        continue
    merged["density_z"] = (merged["ko_per_mb"] - mu) / sd

    # Get metadata from existing results
    row_meta = landscape_cats[landscape_cats["category"] == cat_key]
    if row_meta.empty:
        description = cat_key
        n_kos = "?"
    else:
        description = row_meta["description"].values[0]
        n_kos = row_meta["n_KOs"].values[0]

    # Run unadjusted (single predictor) — should match existing results
    try:
        res_unadj = run_pgls(
            merged, TREE,
            response="mean_levins_B_std",
            predictors=["density_z"],
            label=f"{cat_key}_unadj",
        )
        beta_unadj = res_unadj["beta"]
        p_unadj = res_unadj["p_value"]
        n_unadj = res_unadj["n"]
    except Exception as e:
        print(f"  ERROR unadj {cat_key}: {e}")
        beta_unadj = np.nan
        p_unadj = np.nan
        n_unadj = np.nan

    # Run genome-size-adjusted (two predictors)
    try:
        res_adj = run_pgls(
            merged, TREE,
            response="mean_levins_B_std",
            predictors=["density_z", "genome_mb_z"],
            label=f"{cat_key}_gsadj",
        )
        beta_adj = res_adj["betas"]["density_z"]
        p_adj = res_adj["p_values"]["density_z"]
        beta_gs = res_adj["betas"]["genome_mb_z"]
        p_gs = res_adj["p_values"]["genome_mb_z"]
        n_adj = res_adj["n"]
        lam_adj = res_adj["lambda_est"]
    except Exception as e:
        print(f"  ERROR adj {cat_key}: {e}")
        beta_adj = np.nan
        p_adj = np.nan
        beta_gs = np.nan
        p_gs = np.nan
        n_adj = np.nan
        lam_adj = np.nan

    results_adj.append({
        "category": cat_key,
        "description": description,
        "n_KOs": n_kos,
        "n_genera_unadj": n_unadj,
        "n_genera_adj": n_adj,
        "beta_unadj": round(float(beta_unadj), 4) if not np.isnan(beta_unadj) else np.nan,
        "p_unadj": p_unadj,
        "beta_adj": round(float(beta_adj), 4) if not np.isnan(beta_adj) else np.nan,
        "p_adj": p_adj,
        "beta_genome_size": round(float(beta_gs), 4) if not np.isnan(beta_gs) else np.nan,
        "p_genome_size": p_gs,
        "lambda_adj": lam_adj,
    })

    sig_str = "SIG" if (not np.isnan(p_adj) and p_adj < 0.05) else "ns"
    print(f"  {cat_key:25s}  β_unadj={beta_unadj:+.4f}  β_adj={beta_adj:+.4f}  "
          f"p_adj={p_adj:.2e}  n={n_adj}  [{sig_str}]")

# Also include P1 reference with adjustment
print("\n  Adding P1 reference (140-KO set)...")
p1_input = main[main["mean_levins_B_std"].notna() & main["predictor_z"].notna() & main["genome_mb_z"].notna()].copy()
try:
    res_p1_unadj = run_pgls(
        p1_input, TREE,
        response="mean_levins_B_std",
        predictors=["predictor_z"],
        label="metal_genes_p1_unadj",
    )
    res_p1_adj = run_pgls(
        p1_input, TREE,
        response="mean_levins_B_std",
        predictors=["predictor_z", "genome_mb_z"],
        label="metal_genes_p1_gsadj",
    )
    results_adj.append({
        "category": "metal_genes_p1",
        "description": "Metal genes Tier 1+2 (P1 reference)",
        "n_KOs": 140,
        "n_genera_unadj": res_p1_unadj["n"],
        "n_genera_adj": res_p1_adj["n"],
        "beta_unadj": round(float(res_p1_unadj["beta"]), 4),
        "p_unadj": res_p1_unadj["p_value"],
        "beta_adj": round(float(res_p1_adj["betas"]["predictor_z"]), 4),
        "p_adj": res_p1_adj["p_values"]["predictor_z"],
        "beta_genome_size": round(float(res_p1_adj["betas"]["genome_mb_z"]), 4),
        "p_genome_size": res_p1_adj["p_values"]["genome_mb_z"],
        "lambda_adj": res_p1_adj["lambda_est"],
    })
    print(f"  metal_genes_p1               β_unadj={res_p1_unadj['beta']:+.4f}  "
          f"β_adj={res_p1_adj['betas']['predictor_z']:+.4f}  "
          f"p_adj={res_p1_adj['p_values']['predictor_z']:.2e}  n={res_p1_adj['n']}")
except Exception as e:
    print(f"  ERROR P1: {e}")

df_adj = pd.DataFrame(results_adj)

# BH-FDR across the 19 landscape categories (not P1)
landscape_mask = df_adj["category"] != "metal_genes_p1"
p_vals = df_adj.loc[landscape_mask, "p_adj"].values
from statsmodels.stats.multitest import multipletests
if not np.all(np.isnan(p_vals)):
    reject, q_vals, _, _ = multipletests(
        np.where(np.isnan(p_vals), 1.0, p_vals),
        method="fdr_bh"
    )
    df_adj.loc[landscape_mask, "q_adj_bh"] = q_vals
else:
    df_adj["q_adj_bh"] = np.nan

df_adj.to_csv(DATA / "functional_landscape_gs_adjusted.csv", index=False)
print(f"\n  Saved to data/functional_landscape_gs_adjusted.csv ({len(df_adj)} rows)")

# Sort by beta_adj for ranking check
df_adj_sorted = df_adj[landscape_mask].sort_values("beta_adj")
metal_row = df_adj[df_adj["category"] == "metal_genes_p1"].iloc[0]
metal_beta_adj = metal_row["beta_adj"]

# Find P1 rank among adjusted betas
adj_betas_landscape = df_adj_sorted["beta_adj"].dropna().values
p1_rank = int(np.sum(adj_betas_landscape < metal_beta_adj)) + 1
n_sig_adj = int(np.sum(df_adj.loc[landscape_mask, "q_adj_bh"] < 0.05))
n_nonsig_adj = 19 - n_sig_adj

print(f"\n  P1 β_unadj = -0.021, β_adj = {metal_beta_adj:.4f}")
print(f"  P1 rank (by β_adj among 19 cats): {p1_rank}")
print(f"  Categories significant after adjustment (q<0.05): {n_sig_adj}/19")
print(f"  Categories losing significance after adjustment: {n_nonsig_adj} ... "
      f"but was {int((existing[existing['group']!='metal_reference']['q_bh']<0.05).sum())}/19 before")

# Show categories that were sig before but not after
merged_sig = df_adj.merge(
    existing[["category","q_bh"]].rename(columns={"q_bh":"q_unadj_bh"}),
    on="category", how="left"
)
changed = merged_sig[
    landscape_mask &
    (merged_sig["q_unadj_bh"] < 0.05) &
    (merged_sig["q_adj_bh"] >= 0.05)
]
if not changed.empty:
    print(f"\n  Categories losing significance after GS adjustment:")
    for _, r in changed.iterrows():
        print(f"    {r['category']}: q_before={r['q_unadj_bh']:.3e}, q_after={r['q_adj_bh']:.3e}")
else:
    print("\n  No categories lose significance after GS adjustment.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. SUPPLEMENTARY KO CURATION TABLE (Tl, Al, S)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Task 2: Supplementary KO curation table ===")

kos = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")

def biochem_rationale(row):
    """Generate brief biochemical rationale from category and definition."""
    cat = str(row["primary_category"]) if pd.notna(row["primary_category"]) else ""
    defn = str(row["definition"]) if pd.notna(row["definition"]) else ""
    metals = str(row["metals"]) if pd.notna(row["metals"]) else ""

    if "cofactor" in cat.lower() or "Cofactor" in cat:
        return f"Cofactor biosynthesis; metal cofactor dependency ({metals})"
    elif "resistance" in cat.lower() or "detox" in cat.lower():
        return f"Resistance/detoxification; fitness defect under {metals} stress"
    elif "transport" in cat.lower() or "homeostasis" in cat.lower():
        return f"Metal transport/homeostasis ({metals})"
    elif "sensing" in cat.lower() or "regulation" in cat.lower():
        return f"Sensing/regulatory response to {metals}"
    elif "metabolism" in cat.lower():
        return f"Metal-dependent metabolic enzyme ({metals})"
    else:
        return f"Fitness screen: defect under {metals} stress"

def build_evidence_source(row):
    """Concatenate non-null evidence source fields."""
    parts = []
    if pd.notna(row.get("source_kegg_module")) and str(row["source_kegg_module"]).strip():
        parts.append(f"KEGG:{row['source_kegg_module']}")
    if pd.notna(row.get("source_bacmet")) and str(row["source_bacmet"]).strip() not in ["", "nan", "False", "0"]:
        parts.append("BacMet2")
    if pd.notna(row.get("source_fitness")) and str(row["source_fitness"]).strip() not in ["", "nan", "False", "0"]:
        parts.append("FitnessBrowser")
    return "; ".join(parts) if parts else "KEGG BRITE"

rows_out = []
for metal in ["Tl", "Al", "S"]:
    # Use word-boundary matching to avoid matching "Al" in "Cal" etc.
    # Use exact match within comma-separated list
    mask = kos["metals"].apply(
        lambda x: metal in [m.strip() for m in str(x).split(",")] if pd.notna(x) else False
    )
    subset = kos[mask].copy()
    for _, row in subset.iterrows():
        rows_out.append({
            "KO": row["KO"],
            "gene_name": row.get("gene_name", ""),
            "definition": str(row.get("definition", ""))[:120],
            "metal": metal,
            "evidence_tier": row.get("evidence_tier", ""),
            "primary_category": row.get("primary_category", ""),
            "evidence_source": build_evidence_source(row),
            "biochemical_rationale": biochem_rationale(row),
        })

supp_df = pd.DataFrame(rows_out).drop_duplicates(subset=["KO", "metal"])
supp_df = supp_df.sort_values(["metal", "evidence_tier", "KO"]).reset_index(drop=True)

supp_df.to_csv(DATA / "supplementary_tl_al_s_kos.csv", index=False)
print(f"  Tl: {(supp_df['metal']=='Tl').sum()} KOs")
print(f"  Al: {(supp_df['metal']=='Al').sum()} KOs")
print(f"   S: {(supp_df['metal']=='S').sum()} KOs")
print(f"  Total rows: {len(supp_df)}")
print(f"  Saved to data/supplementary_tl_al_s_kos.csv")


# ─────────────────────────────────────────────────────────────────────────────
# 3. RESISTANCE vs COFACTOR CORE/AUXILIARY COMPARISON
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Task 3: Resistance vs cofactor core/auxiliary comparison ===")

coreness = pd.read_csv(DATA / "ko_coreness_pangenome.csv")
print(f"  ko_coreness_pangenome: {len(coreness)} KOs")
print(f"  Coreness range: {coreness['coreness'].min():.4f} – {coreness['coreness'].max():.4f}")
print(f"  Coreness percentiles: "
      f"5%={coreness['coreness'].quantile(0.05):.4f}, "
      f"25%={coreness['coreness'].quantile(0.25):.4f}, "
      f"50%={coreness['coreness'].quantile(0.50):.4f}, "
      f"95%={coreness['coreness'].quantile(0.95):.4f}")

# Extract subcategory membership from curated list (Tier 1+2 = 140 KOs)
kos_primary = kos[kos["tier_1_vs_2"].isin(["Tier 1", "Tier 2"])].copy()
print(f"\n  Primary KO set (Tier 1+2): {len(kos_primary)} KOs")

resistance_kos = kos_primary[kos_primary["primary_category"] == "Resistance/Detoxification"]["KO"].tolist()
cofactor_kos = kos_primary[kos_primary["primary_category"] == "Cofactor Biosynthesis"]["KO"].tolist()
print(f"  Resistance KOs: {len(resistance_kos)}")
print(f"  Cofactor KOs:   {len(cofactor_kos)}")

# Merge with coreness
resist_core = coreness[coreness["ko"].isin(resistance_kos)].copy()
cofact_core = coreness[coreness["ko"].isin(cofactor_kos)].copy()

print(f"\n  Resistance KOs with coreness data: {len(resist_core)}/{len(resistance_kos)}")
print(f"  Cofactor KOs with coreness data:   {len(cofact_core)}/{len(cofactor_kos)}")

if len(resist_core) > 0:
    print(f"\n  Resistance coreness: mean={resist_core['coreness'].mean():.4f}, "
          f"median={resist_core['coreness'].median():.4f}")
if len(cofact_core) > 0:
    print(f"  Cofactor coreness:   mean={cofact_core['coreness'].mean():.4f}, "
          f"median={cofact_core['coreness'].median():.4f}")

# Define thresholds.
# Given NB23 finding that no KO meets ≥95% core threshold, use:
# "core-like" = coreness ≥ 0.10 (present in ≥10% of pangenome MAG clusters)
# "auxiliary"  = coreness < 0.10
CORE_THRESHOLD = 0.10

if len(resist_core) > 0 and len(cofact_core) > 0:
    resist_core_n = int((resist_core["coreness"] >= CORE_THRESHOLD).sum())
    resist_aux_n  = int((resist_core["coreness"] < CORE_THRESHOLD).sum())
    cofact_core_n = int((cofact_core["coreness"] >= CORE_THRESHOLD).sum())
    cofact_aux_n  = int((cofact_core["coreness"] < CORE_THRESHOLD).sum())

    print(f"\n  Threshold: coreness ≥ {CORE_THRESHOLD} = 'core-like'")
    print(f"  Resistance: {resist_core_n} core-like, {resist_aux_n} auxiliary  "
          f"({100*resist_core_n/len(resist_core):.1f}% core-like)")
    print(f"  Cofactor:   {cofact_core_n} core-like, {cofact_aux_n} auxiliary  "
          f"({100*cofact_core_n/len(cofact_core):.1f}% core-like)")

    # Fisher's exact test: is resistance more likely to be auxiliary than cofactor?
    # Contingency table:
    #              core-like  auxiliary
    # Resistance   a          b
    # Cofactor     c          d
    contingency = np.array([
        [resist_core_n, resist_aux_n],
        [cofact_core_n, cofact_aux_n]
    ])
    odds_ratio, p_fisher = stats.fisher_exact(contingency, alternative="greater")
    # "greater": tests H1 that resistance is more likely to be aux (i.e., lower core fraction)
    # With alternative="greater", it tests that the odds ratio is > 1 for [0,0] vs [1,0]
    # Let me re-define: test whether cofactor has higher core fraction than resistance
    # Fisher exact with alternative="less" for the first row having lower odds
    odds_ratio2, p_fisher2 = stats.fisher_exact(contingency, alternative="two.sided")

    # More intuitive: test whether cofactor KOs are enriched in "core-like"
    # contingency2:
    #              core-like  auxiliary
    # Cofactor     c          d
    # Resistance   a          b
    contingency2 = np.array([
        [cofact_core_n, cofact_aux_n],
        [resist_core_n, resist_aux_n]
    ])
    or_cof_vs_res, p_cof_vs_res = stats.fisher_exact(contingency2, alternative="greater")

    print(f"\n  Fisher's exact (cofactor more core-like than resistance):")
    print(f"    OR = {or_cof_vs_res:.2f}, p = {p_cof_vs_res:.4f}")
    print(f"  Two-sided: OR = {odds_ratio2:.2f}, p = {p_fisher2:.4f}")

    resist_core_frac = resist_core_n / len(resist_core) if len(resist_core) > 0 else np.nan
    cofact_core_frac = cofact_core_n / len(cofact_core) if len(cofact_core) > 0 else np.nan

    # Save summary
    summary = {
        "threshold": CORE_THRESHOLD,
        "resistance_n_kos_with_data": len(resist_core),
        "resistance_n_core_like": resist_core_n,
        "resistance_n_auxiliary": resist_aux_n,
        "resistance_core_frac": resist_core_frac,
        "resistance_mean_coreness": resist_core["coreness"].mean(),
        "cofactor_n_kos_with_data": len(cofact_core),
        "cofactor_n_core_like": cofact_core_n,
        "cofactor_n_auxiliary": cofact_aux_n,
        "cofactor_core_frac": cofact_core_frac,
        "cofactor_mean_coreness": cofact_core["coreness"].mean(),
        "fisher_or": or_cof_vs_res,
        "fisher_p": p_cof_vs_res,
        "fisher_p_twosided": p_fisher2,
    }
    pd.DataFrame([summary]).to_csv(DATA / "resistance_cofactor_core_comparison.csv", index=False)
    print(f"\n  Saved to data/resistance_cofactor_core_comparison.csv")

print("\n=== All analyses complete ===")
