"""
pfam_cross_validation.py
========================
Exploratory Pfam-based cross-validation of the KEGG category PGLS results.

For each of the five functional categories, computes per-genus Pfam-domain
density (unique metal-relevant Pfam domains per Mb) from KOs that have both
(a) a Pfam annotation in curated_mrg_ko_ids_v2_pfam.csv and (b) a presence
record in nb25_ko_presence_matrix.parquet. Runs PGLS against mean_levins_B_std
and writes data/pfam_category_pgls_results.csv.

Rules:
  - Labeled exploratory throughout.
  - KOs with no Pfam annotation contribute zero to genus Pfam density.
  - Failures (too few non-zero genera) are recorded, not silently dropped.
  - Does not alter existing statistics in other output files.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pgls_utils import run_pgls

TREE = DATA / "gtdb_bac_genus_pruned.tree"
MIN_NONZERO = 100  # minimum genera with non-zero Pfam density to attempt PGLS

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

print("Loading data...")
pfam_df = pd.read_csv(DATA / "curated_mrg_ko_ids_v2_pfam.csv", low_memory=False)
pgls_input = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
nb25 = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")

print(f"  pfam_df: {len(pfam_df)} KOs")
print(f"  pgls_input: {len(pgls_input)} genera")
print(f"  nb25: {len(nb25)} rows, {nb25['ko'].nunique()} unique KOs, "
      f"{nb25['genus_lower'].nunique()} unique genera")

# Strip g__ prefix from nb25 genus labels to match pgls_input genus_lower
nb25 = nb25.copy()
nb25["genus_lower"] = nb25["genus_lower"].str.replace(r"^g__", "", regex=True).str.lower()

pgls_genera = set(pgls_input["genus_lower"].str.lower())
nb25_genera_in_pgls = set(nb25["genus_lower"]) & pgls_genera
print(f"  nb25 genera overlapping with PGLS input: {len(nb25_genera_in_pgls)}")

# Build KO → set of Pfam IDs mapping (from curated file; semicolon-delimited)
ko_pfam_map: dict[str, set] = {}
for _, row in pfam_df.iterrows():
    ko = str(row["KO"])
    pfam_str = str(row.get("pfam_ids", "") or "")
    pfams = {p.strip() for p in pfam_str.split(";") if p.strip() and p.strip() != "nan"}
    ko_pfam_map[ko] = pfams

# Build fast lookup: genus → {ko: n_genomes_with_ko} for genera in PGLS
print("Building genus-KO presence lookup...")
nb25_pgls = nb25[nb25["genus_lower"].isin(pgls_genera)].copy()
# Pivot: genus × ko → n_genomes (0 means absent)
presence_pivot = nb25_pgls.pivot_table(
    index="genus_lower", columns="ko", values="n_genomes_with_ko", fill_value=0
)
presence_binary = (presence_pivot > 0)  # True/False
print(f"  Presence matrix: {presence_binary.shape[0]} genera × {presence_binary.shape[1]} KOs")

# Category definitions (full 730-KO list primary_category values, matching Table 4)
CATEGORIES = {
    "F1.1_resistance":  "Resistance/Detoxification",
    "F1.2_transport":   "Transport/Homeostasis",
    "F1.3_sensing":     "Sensing/Regulation",
    "F1.4_cofactor":    "Cofactor Biosynthesis",
    "F1.5_metabolism":  "Metal-dependent Metabolism",
}

# KEGG-based β from Table 4 (03_category_pgls_results.csv) for comparison
kegg_results = pd.read_csv(DATA / "03_category_pgls_results.csv")
kegg_beta = dict(zip(kegg_results["label"], kegg_results["beta"]))
kegg_p    = dict(zip(kegg_results["label"], kegg_results["p_value"]))

# ---------------------------------------------------------------------------
# Per-category analysis
# ---------------------------------------------------------------------------

results = []

for label, cat_name in CATEGORIES.items():
    print(f"\n--- {label}: {cat_name} ---")

    # KOs in this category
    cat_kos = set(pfam_df[pfam_df["primary_category"] == cat_name]["KO"].astype(str))
    print(f"  KOs in category (full list): {len(cat_kos)}")

    # KOs present in nb25 matrix
    kos_in_matrix = cat_kos & set(presence_binary.columns)
    print(f"  KOs in nb25 matrix: {len(kos_in_matrix)}")

    # KOs with at least one Pfam annotation
    kos_with_pfam = {ko for ko in kos_in_matrix if ko_pfam_map.get(ko)}
    print(f"  KOs with Pfam annotation in matrix: {len(kos_with_pfam)}")

    if not kos_with_pfam:
        print("  FAIL: no Pfam-annotated KOs present in local data.")
        results.append({
            "label": label,
            "category": cat_name,
            "n_kos_total": len(cat_kos),
            "n_kos_in_matrix": len(kos_in_matrix),
            "n_kos_with_pfam": 0,
            "n_unique_pfams_possible": 0,
            "n_genera_nonzero": 0,
            "status": "FAIL: no Pfam-annotated KOs in nb25 data",
            "beta_pfam": np.nan,
            "SE_pfam": np.nan,
            "p_pfam": np.nan,
            "lambda_pfam": np.nan,
            "n_pgls": np.nan,
            "beta_kegg": kegg_beta.get(label, np.nan),
            "p_kegg": kegg_p.get(label, np.nan),
        })
        continue

    # Collect all unique Pfam domains across the Pfam-annotated KOs
    all_pfams = set()
    for ko in kos_with_pfam:
        all_pfams |= ko_pfam_map[ko]
    print(f"  Unique Pfam domains possible per genus: {len(all_pfams)}")

    # Build per-genus Pfam density
    genus_pfam_density: dict[str, float] = {}
    pfam_cols = [ko for ko in kos_with_pfam if ko in presence_binary.columns]

    for genus, row_genome in pgls_input[["genus_lower", "mean_genome_mb"]].iterrows():
        g = str(row_genome["genus_lower"]).lower()
        genome_mb = float(row_genome["mean_genome_mb"])

        if g in presence_binary.index:
            pres_row = presence_binary.loc[g]
            present_kos = {ko for ko in pfam_cols if pres_row.get(ko, False)}
        else:
            present_kos = set()

        # Union of Pfam domains from present KOs
        pfam_union: set = set()
        for ko in present_kos:
            pfam_union |= ko_pfam_map[ko]

        pfam_per_mb = len(pfam_union) / genome_mb if genome_mb > 0 else 0.0
        genus_pfam_density[g] = pfam_per_mb

    # Assemble predictor dataframe
    pred_df = pgls_input.copy()
    pred_df["pfam_per_mb"] = pred_df["genus_lower"].str.lower().map(genus_pfam_density)

    n_nonzero = int((pred_df["pfam_per_mb"] > 0).sum())
    print(f"  Genera with non-zero Pfam density: {n_nonzero}")

    if n_nonzero < MIN_NONZERO:
        print(f"  FAIL: only {n_nonzero} genera with non-zero density (min={MIN_NONZERO}).")
        results.append({
            "label": label,
            "category": cat_name,
            "n_kos_total": len(cat_kos),
            "n_kos_in_matrix": len(kos_in_matrix),
            "n_kos_with_pfam": len(kos_with_pfam),
            "n_unique_pfams_possible": len(all_pfams),
            "n_genera_nonzero": n_nonzero,
            "status": f"FAIL: only {n_nonzero} genera with non-zero density (min={MIN_NONZERO})",
            "beta_pfam": np.nan,
            "SE_pfam": np.nan,
            "p_pfam": np.nan,
            "lambda_pfam": np.nan,
            "n_pgls": np.nan,
            "beta_kegg": kegg_beta.get(label, np.nan),
            "p_kegg": kegg_p.get(label, np.nan),
        })
        continue

    # Z-score the predictor
    mean_dens = pred_df["pfam_per_mb"].mean()
    std_dens  = pred_df["pfam_per_mb"].std()
    pred_df["pfam_per_mb_z"] = (pred_df["pfam_per_mb"] - mean_dens) / std_dens

    # Run PGLS
    print("  Running PGLS...")
    try:
        res = run_pgls(
            pred_df,
            tree_path=TREE,
            response="mean_levins_B_std",
            predictors=["pfam_per_mb_z"],
            taxon_col="genus_lower",
            label=f"pfam_{label}",
            min_n=30,
        )
        beta  = float(res["beta"])
        se    = float(res["SE"])
        p_val = float(res["p_value"])
        lam   = float(res["lambda_est"])
        n_fit = int(res["n"])
        status = "OK"
        print(f"  beta={beta:.4f}, SE={se:.4f}, p={p_val:.4e}, lambda={lam:.3f}, n={n_fit}")
    except Exception as exc:
        print(f"  PGLS error: {exc}")
        beta = se = p_val = lam = np.nan
        n_fit = 0
        status = f"PGLS error: {exc}"

    results.append({
        "label": label,
        "category": cat_name,
        "n_kos_total": len(cat_kos),
        "n_kos_in_matrix": len(kos_in_matrix),
        "n_kos_with_pfam": len(kos_with_pfam),
        "n_unique_pfams_possible": len(all_pfams),
        "n_genera_nonzero": n_nonzero,
        "status": status,
        "beta_pfam": beta,
        "SE_pfam": se,
        "p_pfam": p_val,
        "lambda_pfam": lam,
        "n_pgls": n_fit,
        "beta_kegg": kegg_beta.get(label, np.nan),
        "p_kegg": kegg_p.get(label, np.nan),
    })

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------

out_df = pd.DataFrame(results)
out_path = DATA / "pfam_category_pgls_results.csv"
out_df.to_csv(out_path, index=False)
print(f"\nResults saved to {out_path}")
print(out_df[["label", "n_kos_with_pfam", "n_genera_nonzero", "beta_pfam", "p_pfam", "beta_kegg", "p_kegg", "status"]].to_string(index=False))
