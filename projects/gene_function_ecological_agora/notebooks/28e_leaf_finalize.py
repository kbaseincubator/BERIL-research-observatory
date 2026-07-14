"""NB28e finalize — vectorized merge of leaf_consistency to gain events.

Uses the saved p4_leaf_consistency_lookup.parquet (13.75M (rank × clade × ko) entries)
and merges per rank to gain events via the matching recipient_* column. Avoids
the 17M-row apply() that got killed.
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB28e finalize — vectorized leaf_consistency merge ===")

leaf = pd.read_parquet(DATA_DIR / "p4_leaf_consistency_lookup.parquet")
tprint(f"  lookup: {len(leaf):,} (rank × clade × ko)")

gains = pd.read_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet")
tprint(f"  gains: {len(gains):,}")

depth_to_rank = {"recent": "genus", "older_recent": "family", "mid": "order",
                 "older": "class", "ancient": "phylum"}
rank_col_map = {"genus": "recipient_genus", "family": "recipient_family",
                "order": "recipient_order", "class": "recipient_class",
                "phylum": "recipient_phylum"}

# Per-rank merge
gains["leaf_consistency"] = np.nan
for depth, rank in depth_to_rank.items():
    rec_col = rank_col_map[rank]
    sub_idx = gains[gains["depth_bin"] == depth].index
    if len(sub_idx) == 0: continue
    tprint(f"  {depth} (rank={rank}): {len(sub_idx):,} events")
    leaf_rank = leaf[leaf["rank"] == rank][["clade_id", "ko", "leaf_consistency"]].rename(
        columns={"clade_id": rec_col, "leaf_consistency": "lc_match"})
    sub = gains.loc[sub_idx, ["ko", rec_col]].merge(
        leaf_rank, on=["ko", rec_col], how="left")
    gains.loc[sub_idx, "leaf_consistency"] = sub["lc_match"].values
    tprint(f"    matched: {sub['lc_match'].notna().sum():,}")

n_filled = gains["leaf_consistency"].notna().sum()
tprint(f"\n  total leaf_consistency filled: {n_filled:,} of {len(gains):,} ({100*n_filled/len(gains):.1f}%)")
tprint(f"  per-event leaf_consistency stats: mean={gains['leaf_consistency'].mean():.3f}, "
       f"median={gains['leaf_consistency'].median():.3f}")

print("\n  Per-depth_bin leaf_consistency:")
print(gains.groupby("depth_bin")["leaf_consistency"].describe()[["count", "mean", "50%", "min", "max"]].to_string())

print("\n  Per-control_class_m21 leaf_consistency:")
print(gains.groupby("control_class_m21")["leaf_consistency"].describe()[["count", "mean", "50%"]].to_string())

# Save
gains.to_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet", index=False)
tprint(f"\n  saved p4_per_event_uncertainty.parquet ({len(gains):,} rows × {gains.shape[1]} cols)")

# Diagnostics
diag = {
    "phase": "4", "deliverable": "NB28e finalize — vectorized leaf_consistency merge",
    "n_lookup_entries": int(len(leaf)),
    "n_gains_with_leaf_consistency": int(n_filled),
    "leaf_consistency_mean": float(gains["leaf_consistency"].mean()),
    "leaf_consistency_median": float(gains["leaf_consistency"].median()),
    "per_depth_bin_mean": gains.groupby("depth_bin")["leaf_consistency"].mean().to_dict(),
    "per_control_class_mean": gains.groupby("control_class_m21")["leaf_consistency"].mean().to_dict(),
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4_leaf_consistency_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"=== DONE in {time.time()-t0:.1f}s ===")
