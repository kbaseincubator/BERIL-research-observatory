"""NB28e — leaf_consistency per gain event (true full atlas, from MinIO).

Plan:
  1. Read s3a://.../p2_ko_assignments.parquet (28M species-level KO presence) via Spark
  2. Join with p1b_full_species (taxonomy) — small broadcast
  3. Per (rank, clade, ko) compute n_species_with_ko + n_species_in_clade → leaf_consistency
  4. Write per-(rank, clade, ko) → leaf_consistency lookup to MinIO
  5. Read back locally; join to p4_per_event_uncertainty.parquet
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
ASSIGN_PATH = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data/p2_ko_assignments.parquet"
LEAF_OUT = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data/p4_leaf_consistency_lookup.parquet"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB28e — leaf_consistency from full assignments ===")
spark = get_spark_session()

# Load taxonomy locally, push to Spark
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
tax_cols = ["gtdb_species_clade_id", "genus", "family", "order", "class", "phylum"]
tax_sdf = spark.createDataFrame(species[tax_cols])
tprint(f"  taxonomy: {len(species):,} species")

# Per-rank clade size (n_species_in_clade)
rank_sizes = {}
for rank in ["genus", "family", "order", "class", "phylum"]:
    sub = species.dropna(subset=[rank])
    rank_sizes[rank] = sub.groupby(rank).size().to_dict()
    tprint(f"  {rank}: {len(rank_sizes[rank]):,} clades")

# Read assignments (filter is_present)
tprint("  reading assignments from MinIO...")
assignments = (spark.read.parquet(ASSIGN_PATH)
    .filter(F.col("is_present"))
    .select("ko", "gtdb_species_clade_id"))

# Join with taxonomy
joined = assignments.join(F.broadcast(tax_sdf), "gtdb_species_clade_id", "inner")

# Per-rank aggregation: count species with KO per (rank, clade, ko)
rank_dfs = {}
for rank in ["genus", "family", "order", "class", "phylum"]:
    tprint(f"  aggregating {rank} rank...")
    agg = (joined.filter(F.col(rank).isNotNull())
        .groupBy(F.col(rank).alias("clade_id"), "ko")
        .agg(F.countDistinct("gtdb_species_clade_id").alias("n_species_with_ko"))
        .withColumn("rank", F.lit(rank)))
    rank_dfs[rank] = agg

# Union all ranks
all_ranks = rank_dfs["genus"]
for rank in ["family", "order", "class", "phylum"]:
    all_ranks = all_ranks.unionByName(rank_dfs[rank])

# Write to MinIO (single coalesce so we get a small file)
tprint("  writing per-(rank × clade × ko) species count to MinIO...")
all_ranks.coalesce(8).write.mode("overwrite").parquet(LEAF_OUT)
tprint(f"  wrote {LEAF_OUT}")

# Read back
tprint("  reading back from MinIO...")
leaf_df_spark = spark.read.parquet(LEAF_OUT).toPandas()
leaf_df = pd.DataFrame({c: leaf_df_spark[c].values for c in leaf_df_spark.columns})
tprint(f"  leaf lookup: {len(leaf_df):,} rows")

# Map clade size
def get_clade_size(row):
    return rank_sizes.get(row["rank"], {}).get(row["clade_id"], 1)
leaf_df["n_species_in_clade"] = leaf_df.apply(get_clade_size, axis=1)
leaf_df["leaf_consistency"] = leaf_df["n_species_with_ko"] / leaf_df["n_species_in_clade"].clip(lower=1)
tprint(f"  leaf_consistency stats: mean={leaf_df['leaf_consistency'].mean():.3f}, "
       f"median={leaf_df['leaf_consistency'].median():.3f}, "
       f"max={leaf_df['leaf_consistency'].max():.3f}")
leaf_df.to_parquet(DATA_DIR / "p4_leaf_consistency_lookup.parquet", index=False)
tprint(f"  saved p4_leaf_consistency_lookup.parquet ({len(leaf_df):,} rows)")

# Join to gain events
tprint("\n  joining leaf_consistency to gain events")
gains = pd.read_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet")
tprint(f"  gains: {len(gains):,}")

depth_to_rank = {"recent": "genus", "older_recent": "family", "mid": "order",
                 "older": "class", "ancient": "phylum"}
rank_col_map = {"genus": "recipient_genus", "family": "recipient_family",
                "order": "recipient_order", "class": "recipient_class",
                "phylum": "recipient_phylum"}

# Build lookup dict for fast join
leaf_lookup = dict(zip(zip(leaf_df["rank"], leaf_df["clade_id"], leaf_df["ko"]),
                       leaf_df["leaf_consistency"]))
tprint(f"  built lookup: {len(leaf_lookup):,} entries")

def get_lc(row):
    rank = depth_to_rank.get(row["depth_bin"])
    if rank is None: return np.nan
    clade = row.get(rank_col_map[rank])
    if pd.isna(clade): return np.nan
    return leaf_lookup.get((rank, clade, row["ko"]), np.nan)

tprint("  applying lookup to gains...")
gains["leaf_consistency"] = gains.apply(get_lc, axis=1)
n_filled = gains["leaf_consistency"].notna().sum()
tprint(f"  leaf_consistency filled: {n_filled:,} of {len(gains):,} ({100*n_filled/len(gains):.1f}%)")
tprint(f"  per-event leaf_consistency stats: mean={gains['leaf_consistency'].mean():.3f}, "
       f"median={gains['leaf_consistency'].median():.3f}")

# Distribution by depth_bin
print("\n  Per-depth_bin leaf_consistency:")
print(gains.groupby("depth_bin")["leaf_consistency"].describe()[["count", "mean", "50%"]].to_string())

gains.to_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet", index=False)
tprint(f"\n  updated p4_per_event_uncertainty.parquet")

# Diagnostics
diag = {
    "phase": "4", "deliverable": "NB28e — leaf_consistency from full atlas",
    "n_leaf_lookup_rows": int(len(leaf_df)),
    "n_gains_with_leaf_consistency": int(n_filled),
    "leaf_consistency_mean": float(gains["leaf_consistency"].mean()),
    "leaf_consistency_median": float(gains["leaf_consistency"].median()),
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4_leaf_consistency_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"\n=== DONE in {time.time()-t0:.1f}s ===")
