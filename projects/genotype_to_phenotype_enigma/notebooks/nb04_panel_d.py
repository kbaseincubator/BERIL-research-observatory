#!/usr/bin/env python3
"""Panel D — Genus co-occurrence + metabolic complementarity from 100WS ASVs.

Approach (SparCC proxy via CLR + Spearman, see Friedman & Alm 2012):
  1. Get ASV → genus from ddt_brick0000478 (taxonomy assignments).
  2. Get community × ASV counts from ddt_brick0000476, filter to environmental communities.
  3. Aggregate counts to community × genus matrix.
  4. CLR-transform counts (handles compositionality).
  5. Spearman correlations between genera (genus × genus matrix).
  6. Filter to ENIGMA-related genera; extract significant edges.
  7. For each co-occurring pair, test metabolic complementarity using NB03 guild assignments.

Produces:
  - data/asv_cooccurrence_edges.tsv: significant genus-pair edges (ρ, p-value)
  - data/complementarity_pairs.tsv: ENIGMA-genus pairs flagged complementary vs redundant
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={os.environ['KBASE_AUTH_TOKEN']}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"

# ── 1. ASV → genus ────────────────────────────────────────────────────────────
asv_genus = (
    spark.table("enigma_coral.ddt_brick0000478")
    .filter(F.col("taxonomic_level_sys_oterm_name") == "genus")
    .select(
        F.col("sdt_asv_name").alias("asv"),
        F.col("sdt_taxon_name").alias("genus"),
    )
    .filter(F.col("genus").isNotNull())
    .toPandas()
)
asv_genus = asv_genus.drop_duplicates(subset=["asv"])  # 1 genus per ASV
print(f"ASV → genus map: {len(asv_genus):,} ASVs, {asv_genus.genus.nunique()} genera")

# ── 2. Community × ASV counts → community × genus, restricted to environmental communities ──
env_communities = (
    spark.table("enigma_coral.sdt_community")
    .filter(F.col("community_type_sys_oterm_name") == "Environmental Community")
    .select(F.col("sdt_community_name").alias("community"))
)
print(f"Environmental communities: {env_communities.count():,}")

asv_genus_sdf = spark.createDataFrame(asv_genus)
counts = (
    spark.table("enigma_coral.ddt_brick0000476")
    .filter(F.col("count_count_unit") > 0)
    .select(
        F.col("sdt_asv_name").alias("asv"),
        F.col("sdt_community_name").alias("community"),
        F.col("count_count_unit").cast("long").alias("count"),
    )
    .join(F.broadcast(env_communities), "community", "inner")
    .join(F.broadcast(asv_genus_sdf), "asv", "inner")
)
# Aggregate: sum counts per (community, genus)
genus_counts_sdf = counts.groupBy("community", "genus").agg(F.sum("count").alias("count"))
print("Pulling community × genus counts...")
genus_counts = genus_counts_sdf.toPandas()
print(f"community×genus rows: {len(genus_counts):,}")

# Pivot to wide
mat = genus_counts.pivot_table(
    index="community", columns="genus", values="count", fill_value=0
).astype(float)
print(f"Community × genus matrix: {mat.shape}")

# Filter: keep genera present in ≥10% of communities, and communities with ≥100 reads
min_communities = max(int(0.1 * mat.shape[0]), 5)
prevalent = (mat > 0).sum(axis=0) >= min_communities
mat = mat.loc[:, prevalent]
mat = mat.loc[mat.sum(axis=1) >= 100]
print(f"Filtered matrix (genera in ≥{min_communities} communities, communities with ≥100 reads): {mat.shape}")

# ── 3. CLR transform ─────────────────────────────────────────────────────────
# Add pseudocount to avoid log(0)
mat_pseudo = mat + 1.0
geom_mean = np.exp(np.log(mat_pseudo).mean(axis=1))
clr = np.log(mat_pseudo.div(geom_mean, axis=0))
print(f"CLR-transformed matrix: {clr.shape}")

# ── 4. Spearman correlations (SparCC proxy) ──────────────────────────────────
from scipy.stats import spearmanr
print("Computing pairwise Spearman correlations...")
rho, pval = spearmanr(clr.values, axis=0)
genera_list = list(clr.columns)
print(f"Correlation matrix: {rho.shape}")

# Build edge list: only upper triangle, |rho| > 0.3, p < 0.01 (Bonferroni)
n_pairs = (len(genera_list) * (len(genera_list) - 1)) // 2
bonf = 0.01 / n_pairs
edges = []
for i in range(len(genera_list)):
    for j in range(i + 1, len(genera_list)):
        if abs(rho[i, j]) >= 0.3 and pval[i, j] < bonf:
            edges.append({
                "genus_a": genera_list[i],
                "genus_b": genera_list[j],
                "rho": float(rho[i, j]),
                "pval": float(pval[i, j]),
            })
edges_df = pd.DataFrame(edges)
print(f"Significant edges (|ρ|≥0.3, p<{bonf:.2e}): {len(edges_df):,}")
edges_df.to_csv(DATA / "asv_cooccurrence_edges.tsv", sep="\t", index=False)

# ── 5. Filter to ENIGMA-related genera ───────────────────────────────────────
strains = pd.read_csv(DATA / "strain_scalars.tsv", sep="\t")
strains["enigma_genus"] = strains.taxon_name.str.split().str[0]
mbg = pd.read_csv(DATA / "microbeatlas_genus_summary.tsv", sep="\t")
ENIGMA_GENERA = set(mbg["genus"].tolist()) | set(strains["enigma_genus"].dropna().unique())
ENIGMA_GENERA.discard("Environmental")
print(f"ENIGMA-related genera ({len(ENIGMA_GENERA)}): {sorted(ENIGMA_GENERA)}")

enigma_edges = edges_df[
    edges_df["genus_a"].isin(ENIGMA_GENERA) | edges_df["genus_b"].isin(ENIGMA_GENERA)
]
print(f"Edges involving ENIGMA-related genera: {len(enigma_edges):,}")
enigma_edges.to_csv(DATA / "asv_cooccurrence_edges_enigma.tsv", sep="\t", index=False)

# ── 6. Metabolic complementarity test using NB03 guilds ──────────────────────
# Map ENIGMA genus → set of guilds (some genera span multiple guilds)
strain_guild = strains.dropna(subset=["guild"])[["enigma_genus", "guild"]].drop_duplicates()
guild_per_genus = (
    strain_guild.groupby("enigma_genus")["guild"]
    .agg(lambda x: tuple(sorted(set(x))))
    .to_dict()
)

def complementarity_label(ga, gb):
    """Return 'complementary' if guilds disjoint, 'overlapping' if share a guild,
    or None if either genus has no guild assignment."""
    ga_g = guild_per_genus.get(ga)
    gb_g = guild_per_genus.get(gb)
    if ga_g is None or gb_g is None:
        return None
    if set(ga_g).isdisjoint(set(gb_g)):
        return "complementary"
    return "overlapping"

# Annotate edges where both genera are ENIGMA strain-derived (have guild info)
enigma_strain_genera = set(strain_guild["enigma_genus"].unique())
both_enigma = edges_df[
    edges_df["genus_a"].isin(enigma_strain_genera)
    & edges_df["genus_b"].isin(enigma_strain_genera)
].copy()
both_enigma["complementarity"] = both_enigma.apply(
    lambda r: complementarity_label(r["genus_a"], r["genus_b"]), axis=1
)
both_enigma["sign"] = both_enigma["rho"].apply(lambda r: "+" if r > 0 else "−")
both_enigma.to_csv(DATA / "complementarity_pairs.tsv", sep="\t", index=False)
print(f"Pairs with both genera in ENIGMA collection: {len(both_enigma)}")
if len(both_enigma):
    print("Cross-tab (sign × complementarity):")
    print(pd.crosstab(both_enigma["sign"], both_enigma["complementarity"]).to_string())

spark.stop()
