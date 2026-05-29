"""
Build data/candidate_otu_list.csv

Columns:
  OTU_id, genus, mean_levins_B_std, n_metal_types,
  top10pct_both (flag), nitrifier_role, seq_100bp

Sources:
  data/otu_pangenome_link.csv   – OTU ↔ genus mapping + nitrifier_role
  data/otu_niche_breadth.csv    – per-OTU levins_B_std
  data/genus_trait_table.csv    – genus-level mean_n_metal_types

Note: otus.97.allinfo is not present in this project; seq_100bp is set to NA.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data")

# ── 1. Load OTU ↔ genus link ─────────────────────────────────────────────────
link = pd.read_csv(DATA / "otu_pangenome_link.csv", low_memory=False)
link = link[["otu_id", "genus_clean", "nitrifier_role"]].rename(
    columns={"genus_clean": "genus"}
)

# ── 2. Load per-OTU niche breadth ───────────────────────────────────────────
nb = pd.read_csv(DATA / "otu_niche_breadth.csv", low_memory=False)
nb = nb[["otu_id", "levins_B_std"]].rename(
    columns={"levins_B_std": "otu_levins_B_std"}
)

# ── 3. Load genus-level traits ───────────────────────────────────────────────
gt = pd.read_csv(DATA / "genus_trait_table.csv", low_memory=False)
gt = gt[["otu_genus", "mean_levins_B_std", "mean_n_metal_types", "is_nitrifier"]].rename(
    columns={"otu_genus": "genus", "mean_n_metal_types": "n_metal_types"}
)

# ── 4. Merge OTUs with niche breadth ─────────────────────────────────────────
df = link.merge(nb, on="otu_id", how="left")

# Prefer per-OTU levins_B_std; fall back to genus mean after joining genus traits
df = df.merge(gt, on="genus", how="left")

# Use per-OTU value where available, otherwise genus mean
df["mean_levins_B_std"] = df["otu_levins_B_std"].combine_first(df["mean_levins_B_std"])
df.drop(columns=["otu_levins_B_std"], inplace=True)

# ── 5. Identify nitrifier OTUs ───────────────────────────────────────────────
# nitrifier_role is non-empty in otu_pangenome_link for known nitrifier OTUs;
# is_nitrifier=1 covers genus-level nitrifiers (e.g. Nitrosopumilus without role set)
df["is_nitrifier_flag"] = (
    df["nitrifier_role"].notna() & (df["nitrifier_role"] != "")
) | (df["is_nitrifier"] == 1)
df.drop(columns=["is_nitrifier"], inplace=True)

# ── 6. Compute top-10% flag ──────────────────────────────────────────────────
# Apply only to rows that have both numeric values
has_both = df["mean_levins_B_std"].notna() & df["n_metal_types"].notna()

q90_B   = df.loc[has_both, "mean_levins_B_std"].quantile(0.90)
q90_met = df.loc[has_both, "n_metal_types"].quantile(0.90)

df["top10pct_both"] = (
    has_both
    & (df["mean_levins_B_std"] >= q90_B)
    & (df["n_metal_types"] >= q90_met)
).astype(int)

print(f"90th-pct thresholds:  levins_B_std >= {q90_B:.3f},  n_metal_types >= {q90_met:.1f}")
print(f"OTUs in top-10% by both metrics: {df['top10pct_both'].sum()}")
print(f"Nitrifier OTUs included:         {df['is_nitrifier_flag'].sum()}")

# ── 7. Candidate set: top-10% union nitrifiers ───────────────────────────────
candidates = df[df["top10pct_both"].astype(bool) | df["is_nitrifier_flag"]].copy()
print(f"Total candidate OTUs:            {len(candidates)}")

# ── 8. seq_100bp – not available (otus.97.allinfo absent) ────────────────────
candidates["seq_100bp"] = "NA"

# ── 9. Tidy and save ─────────────────────────────────────────────────────────
out_cols = [
    "otu_id", "genus", "mean_levins_B_std", "n_metal_types",
    "top10pct_both", "is_nitrifier_flag", "nitrifier_role", "seq_100bp",
]
candidates = candidates[out_cols].rename(columns={"otu_id": "OTU_id"})
candidates = candidates.sort_values(
    ["top10pct_both", "is_nitrifier_flag", "mean_levins_B_std"],
    ascending=[False, False, False],
)

out_path = DATA / "candidate_otu_list.csv"
candidates.to_csv(out_path, index=False)
print(f"\nSaved → {out_path}  ({len(candidates)} rows)")
print(candidates.head(10).to_string(index=False))
