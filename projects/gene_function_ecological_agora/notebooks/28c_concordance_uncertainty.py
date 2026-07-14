"""NB28 Stage 3 — concordance-weighted atlas + conflict analysis + per-event uncertainty.

Three deliverables:
  1. data/p4_concordance_weighted_atlas.parquet — extends p4_deep_rank_pp_atlas.parquet
     with tree_proxy_quadrant column (joined from Stage 2 output) and concordance flag
     where deep-rank P×P category and genus-rank tree-proxy quadrant either agree or conflict.
  2. data/p4_conflict_analysis.tsv — per-tuple disagreements with hypothesis classification.
  3. data/p4_per_event_uncertainty.parquet — extends p2_m22_gains_attributed.parquet with
     leaf_consistency column (fraction of species under recipient_clade carrying the KO).
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

tprint("=== NB28 Stage 3 — concordance + conflict + per-event uncertainty ===")

# === Load data ===
atlas_pp = pd.read_parquet(DATA_DIR / "p4_deep_rank_pp_atlas.parquet")
tprint(f"  deep-rank atlas: {len(atlas_pp):,} (rank × clade × KO)")

quadrants = pd.read_csv(DATA_DIR / "p4_genus_rank_quadrants_tree_proxy.tsv", sep="\t")
tprint(f"  genus-rank quadrants: {len(quadrants):,} (genus × KO)")

# === Stage 3a: concordance-weighted atlas ===
tprint("\nStage 3a: concordance-weighted atlas")

# Subset atlas to genus rank only for direct join with quadrants
atlas_genus = atlas_pp[atlas_pp["rank"] == "genus"].copy()
tprint(f"  atlas at genus rank: {len(atlas_genus):,}")

# Join: deep-rank P×P (atlas_genus) × genus-rank tree-proxy quadrant
merged = atlas_genus.merge(
    quadrants[["genus", "ko", "n_recipient_gains", "n_donor_candidate_events",
                "donor_recipient_ratio", "quadrant_proxy", "confidence"]],
    left_on=["clade_id", "ko"], right_on=["genus", "ko"], how="left"
).drop(columns=["genus"])
merged["quadrant_proxy"] = merged["quadrant_proxy"].fillna("Insufficient-Data")
merged["confidence"] = merged["confidence"].fillna("insufficient")
tprint(f"  merged: {len(merged):,}")

# Concordance flag: deep-rank P×P category and tree-proxy quadrant agreement
def concordance(row):
    pp = row["pp_category"]
    quad = row["quadrant_proxy"]
    if pp == "Insufficient-Data" or quad == "Insufficient-Data":
        return "insufficient_data"
    # Define agreement mapping:
    # - Innovator-Isolated (deep) ↔ Open-Innovator OR Closed-Stable (genus tree proxy):
    #   producer-high in both, but genus-rank donor proxy may show donating to family OR isolated
    # - Innovator-Exchange (deep) ↔ Broker OR Open-Innovator (genus): exchange is bidirectional but tree
    #   proxy may resolve as donor-dominated (Open) or balanced (Broker)
    # - Sink-Broker-Exchange (deep) ↔ Sink OR Broker (genus): consumer-high in both
    # - Stable (deep) ↔ Closed-Stable OR Insufficient (genus): no transitions
    agreement = {
        "Innovator-Isolated": {"Open-Innovator", "Closed-Stable"},
        "Innovator-Exchange": {"Open-Innovator", "Broker"},
        "Sink-Broker-Exchange": {"Sink", "Broker"},
        "Stable": {"Closed-Stable"},
    }
    if pp in agreement:
        return "agree" if quad in agreement[pp] else "conflict"
    return "n/a"

merged["concordance"] = merged.apply(concordance, axis=1)
tprint(f"  concordance distribution:")
for c, n in merged["concordance"].value_counts().items():
    tprint(f"    {c}: {n:,}")

# Save concordance-weighted atlas (genus rank only, since tree-proxy is genus-rank)
out_cols = ["rank", "clade_id", "ko", "producer_z", "consumer_z", "n_clades_with",
             "control_class", "pp_category",
             "n_recipient_gains", "n_donor_candidate_events", "donor_recipient_ratio",
             "quadrant_proxy", "confidence", "concordance"]
merged[out_cols].to_parquet(DATA_DIR / "p4_concordance_weighted_atlas.parquet", index=False)
tprint(f"  wrote p4_concordance_weighted_atlas.parquet ({len(merged):,} rows)")

# === Stage 3b: conflict analysis ===
tprint("\nStage 3b: conflict analysis")
conflicts = merged[merged["concordance"] == "conflict"].copy()
tprint(f"  conflicting tuples: {len(conflicts):,}")

# Hypothesis classification for conflicts
def hypothesize_conflict(row):
    pp = row["pp_category"]
    quad = row["quadrant_proxy"]
    n_events = (row.get("n_recipient_gains", 0) or 0) + (row.get("n_donor_candidate_events", 0) or 0)
    conf = row.get("confidence", "insufficient")
    if conf in ("low", "medium"):
        return "low-confidence-tree-proxy"
    if pp == "Innovator-Isolated" and quad == "Sink":
        return "deep-producer-but-genus-recipient (rank-dependence?)"
    if pp == "Innovator-Exchange" and quad == "Sink":
        return "deep-exchange-but-genus-recipient (broader donor pattern at deeper rank)"
    if pp == "Sink-Broker-Exchange" and quad == "Open-Innovator":
        return "deep-consumer-but-genus-donor (rank-dependence: receives at deep rank, donates at genus)"
    if pp == "Stable" and quad in ("Open-Innovator", "Broker", "Sink"):
        return "deep-stable-but-genus-active (recent activity below deep-rank threshold)"
    return "other-conflict"

conflicts["hypothesis"] = conflicts.apply(hypothesize_conflict, axis=1)
tprint(f"  conflict hypothesis breakdown:")
for h, n in conflicts["hypothesis"].value_counts().items():
    tprint(f"    {h}: {n:,}")

conflicts[["clade_id", "ko", "pp_category", "quadrant_proxy",
            "donor_recipient_ratio", "confidence", "hypothesis"]].to_csv(
    DATA_DIR / "p4_conflict_analysis.tsv", sep="\t", index=False)
tprint(f"  wrote p4_conflict_analysis.tsv ({len(conflicts):,} rows)")

# === Stage 3c: per-event uncertainty ===
tprint("\nStage 3c: per-event uncertainty (leaf_consistency)")

gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
tprint(f"  M22 gains: {len(gains):,}")
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

# For each (rank × clade × ko), compute fraction of species in clade carrying ko
# We have atlas_pp with `n_clades_with` (atlas-wide n of clades at same rank with the KO),
# but for leaf_consistency we want PER-CLADE prevalence (fraction of species in this clade with KO)

# Need: per (rank × clade × ko), how many species in clade have ko present?
# Phase 1B species data has per-species KO presence; but full atlas has per-(rank × clade × KO) only
# Recompute prevalence from p1b_full_extract_local.parquet would be heavy; use a proxy:
#   atlas already has paralog_count (1 if any species has KO, higher if multiple); n_clades_with at rank below
# Cleanest tractable proxy: per-rank, count species in clade with ko via the species df + ko atlas

# Simpler: load p2_ko_atlas_intermediate (has presence at species level joined to clade)
# If too big, fallback to atlas-derived proxy

intermediate_path = DATA_DIR / "p2_ko_atlas_intermediate.parquet"
if intermediate_path.exists():
    inter = pd.read_parquet(intermediate_path)
    tprint(f"  intermediate (species-level KO): columns = {inter.columns.tolist()}")
    if "gtdb_species_clade_id" in inter.columns and "ko" in inter.columns:
        # per-species presence
        # join species → genus, family, etc.
        species_tax = species[["gtdb_species_clade_id", "genus", "family", "order", "class", "phylum"]]
        species_with_ko = inter.merge(species_tax, on="gtdb_species_clade_id", how="inner")
        tprint(f"  species_with_ko: {len(species_with_ko):,}")
    else:
        tprint("  intermediate format not recognized; skipping leaf_consistency")
        species_with_ko = None
else:
    tprint("  no intermediate; using atlas-only proxy")
    species_with_ko = None

if species_with_ko is not None:
    # Per (rank × clade × ko), count species with ko
    per_clade_counts = {}
    species_per_clade = {}
    for rank in ["genus", "family", "order", "class", "phylum"]:
        # n_species_in_clade
        sp_per_clade = species.groupby(rank).size().to_dict() if rank in species.columns else {}
        species_per_clade[rank] = sp_per_clade
        # n_species_with_ko per (clade × ko)
        if rank in species_with_ko.columns:
            grp = species_with_ko.groupby([rank, "ko"]).size().reset_index(name="n_species_with_ko")
            grp["rank"] = rank
            grp = grp.rename(columns={rank: "clade_id"})
            per_clade_counts[rank] = grp
            tprint(f"  rank={rank}: {len(grp):,} (clade × ko) entries")
    per_clade_df = pd.concat(per_clade_counts.values(), ignore_index=True) if per_clade_counts else None
    tprint(f"  per_clade_df: {len(per_clade_df) if per_clade_df is not None else 0:,}")

    # leaf_consistency = n_species_with_ko / n_species_in_clade
    if per_clade_df is not None:
        per_clade_df["n_species_in_clade"] = per_clade_df.apply(
            lambda r: species_per_clade[r["rank"]].get(r["clade_id"], 1), axis=1)
        per_clade_df["leaf_consistency"] = per_clade_df["n_species_with_ko"] / per_clade_df["n_species_in_clade"].clip(lower=1)
        tprint(f"  leaf_consistency stats: mean={per_clade_df['leaf_consistency'].mean():.3f}, "
               f"median={per_clade_df['leaf_consistency'].median():.3f}")

        # Map onto gains: gain at rank R, recipient_clade C, ko K → leaf_consistency
        # Build join keys: gain has recipient_genus/family/order/class/phylum
        # acquisition_depth tells us which rank
        rank_col_map = {"genus": "recipient_genus", "family": "recipient_family",
                        "order": "recipient_order", "class": "recipient_class",
                        "phylum": "recipient_phylum"}
        # For each gain, its recipient_rank is wherever the deepest non-null recipient column is
        # Use acquisition_depth to map
        depth_to_rank = {"recent": "genus", "older_recent": "family", "mid": "order",
                         "older": "class", "ancient": "phylum"}

        # join lookup: build a single (rank, clade_id, ko) → leaf_consistency map
        leaf_map = dict(zip(zip(per_clade_df["rank"], per_clade_df["clade_id"], per_clade_df["ko"]),
                            per_clade_df["leaf_consistency"]))
        tprint(f"  built leaf_consistency lookup: {len(leaf_map):,} entries")

        def get_leaf_consistency(row):
            rank = depth_to_rank.get(row["depth_bin"])
            if rank is None: return np.nan
            clade = row.get(rank_col_map[rank])
            if pd.isna(clade): return np.nan
            return leaf_map.get((rank, clade, row["ko"]), np.nan)

        # Apply
        tprint(f"  computing leaf_consistency for {len(gains):,} gains...")
        gains["leaf_consistency"] = gains.apply(get_leaf_consistency, axis=1)
        tprint(f"  leaf_consistency: non-null = {gains['leaf_consistency'].notna().sum():,} of {len(gains):,}")
        tprint(f"  leaf_consistency stats: mean={gains['leaf_consistency'].mean():.3f}, "
               f"median={gains['leaf_consistency'].median():.3f}")

        # Save
        gains.to_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet", index=False)
        tprint(f"  wrote p4_per_event_uncertainty.parquet ({len(gains):,} rows)")
    else:
        tprint("  could not build per_clade_df; saving gains as-is with n_leaves_under only")
        gains.to_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet", index=False)
else:
    # Fallback: just save gains with n_leaves_under (already there)
    tprint("  fallback: saving gains with n_leaves_under only (no leaf_consistency)")
    gains.to_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet", index=False)

# Diagnostics
diag = {
    "phase": "4", "deliverable": "NB28 Stage 3",
    "n_concordance_atlas_rows": int(len(merged)),
    "concordance_distribution": merged["concordance"].value_counts().to_dict(),
    "n_conflict_tuples": int(len(conflicts)),
    "conflict_hypotheses": conflicts["hypothesis"].value_counts().to_dict(),
    "n_gains_with_leaf_consistency": int(gains["leaf_consistency"].notna().sum() if "leaf_consistency" in gains.columns else 0),
    "leaf_consistency_mean": float(gains["leaf_consistency"].mean()) if "leaf_consistency" in gains.columns else None,
    "leaf_consistency_median": float(gains["leaf_consistency"].median()) if "leaf_consistency" in gains.columns else None,
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4_concordance_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"\n=== Stage 3 DONE in {time.time()-t0:.1f}s ===")
