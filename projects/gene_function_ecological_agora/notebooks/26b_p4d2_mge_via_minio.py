"""NB26b — P4-D2 retry: aggregate to (ko × genus) in Spark, write to MinIO,
then read locally for tests.

NB26 blew driver.maxResultSize when toPandas-ing (KO × species) MGE counts.
This version:
  1. Joins bakta_annotations + gene_cluster + species (genus) IN Spark
  2. Aggregates to (ko, genus) directly
  3. Writes to MinIO parquet
  4. Reads locally for tests

That keeps the driver-side dataframe at ~few million rows × 4 cols.
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"
MINIO_PATH = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data/p4d2_ko_genus_mge.parquet"

t0 = time.time()
print("=== NB26b / P4-D2 — MGE context (MinIO staged) ===", flush=True)

spark = get_spark_session()

# Stage 1: compute (ko × genus) MGE fraction in Spark, write to MinIO
print("\nStage 1: compute (ko × genus) MGE fraction in Spark", flush=True)
MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
mge_regex = "|".join(MGE_KEYWORDS)

# Push species → genus mapping to Spark
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
species_sdf = spark.createDataFrame(species[["gtdb_species_clade_id", "genus"]])

bakta = (spark.table("kbase_ke_pangenome.bakta_annotations")
    .filter(F.col("kegg_orthology_id").isNotNull() & (F.col("kegg_orthology_id") != ""))
    .withColumn("is_mge",
        F.when(F.col("product").isNotNull() & F.lower(F.col("product")).rlike(mge_regex), 1).otherwise(0))
    .withColumn("ko", F.split(F.col("kegg_orthology_id"), ",").getItem(0))
    .select("gene_cluster_id", "ko", "is_mge"))

gc = spark.table("kbase_ke_pangenome.gene_cluster").select("gene_cluster_id", "gtdb_species_clade_id")

ko_genus_agg = (bakta
    .join(gc, "gene_cluster_id", "inner")
    .join(F.broadcast(species_sdf), "gtdb_species_clade_id", "inner")
    .filter(F.col("genus").isNotNull())
    .groupBy("ko", "genus")
    .agg(F.count("*").alias("n_clusters"),
         F.sum("is_mge").alias("n_mge_clusters"),
         F.countDistinct("gtdb_species_clade_id").alias("n_species"))
    .withColumn("mge_fraction", F.col("n_mge_clusters") / F.col("n_clusters")))

# Write coalesced to MinIO
print("  writing to MinIO...", flush=True)
ko_genus_agg.coalesce(8).write.mode("overwrite").parquet(MINIO_PATH)
print(f"  wrote {MINIO_PATH}", flush=True)

# Stage 2: read locally
print("\nStage 2: read MinIO output via Spark, then collect", flush=True)
ko_genus_mge = spark.read.parquet(MINIO_PATH).toPandas()
print(f"  (ko × genus) MGE rows: {len(ko_genus_mge):,}", flush=True)

# Atlas-wide MGE rate
total_clusters = ko_genus_mge["n_clusters"].sum()
total_mge = ko_genus_mge["n_mge_clusters"].sum()
print(f"  total KO-bearing clusters: {total_clusters:,}", flush=True)
print(f"  total MGE-flagged: {total_mge:,} ({100*total_mge/total_clusters:.3f}%)", flush=True)

# Save local
ko_genus_mge.to_parquet(DATA_DIR / "p4d2_ko_genus_mge.parquet", index=False)
print(f"  saved local p4d2_ko_genus_mge.parquet", flush=True)

# Stage 3: tag M22 recent gains
print("\nStage 3: tag M22 recent gains with MGE fraction", flush=True)
gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
recent = gains[gains["depth_bin"] == "recent"].dropna(subset=["recipient_genus"])
print(f"  M22 recent gains with genus: {len(recent):,}", flush=True)

recent_tagged = recent.merge(
    ko_genus_mge.rename(columns={"genus": "recipient_genus"}),
    on=["ko", "recipient_genus"], how="left")
print(f"  with non-null MGE fraction: {recent_tagged['mge_fraction'].notna().sum():,}", flush=True)

# Add taxonomy back
species_tax = species[["gtdb_species_clade_id", "genus", "family", "order", "class", "phylum"]].drop_duplicates(subset="genus")
recent_tagged = recent_tagged.merge(species_tax[["genus", "family", "order", "class", "phylum"]],
                                      left_on="recipient_genus", right_on="genus", how="left")

recent_tagged.to_parquet(DATA_DIR / "p4d2_recent_gain_mge_attributed.parquet", index=False)

# Stage 4: tests
print("\n--- T1: per-KO-category MGE rate ---", flush=True)
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
REG_PATHWAY_PREFIXES = {f"ko03{n:03d}" for n in range(0, 100)}
REG_PATHWAY_RANGES = {f"ko0{n:04d}" for n in [2010, 2020, 2024, 2025, 2026, 2030, 2040, 2060, 2065]}
REG_PATHWAYS = REG_PATHWAY_PREFIXES | REG_PATHWAY_RANGES
def is_metabolic(p):
    if not p.startswith("ko"): return False
    try: return int(p[2:]) < 2000
    except ValueError: return False
def classify(s):
    if not isinstance(s, str) or s == "": return "unannotated"
    pwys = set(s.split(","))
    n_reg = sum(1 for p in pwys if p in REG_PATHWAYS)
    n_met = sum(1 for p in pwys if is_metabolic(p))
    if n_reg > 0 and n_met == 0: return "regulatory"
    if n_met > 0 and n_reg == 0: return "metabolic"
    if n_reg > 0 and n_met > 0: return "mixed"
    return "other"
ko_pwbr["category"] = ko_pwbr["pathway_ids"].apply(classify)
ko_to_cat = dict(zip(ko_pwbr["ko"], ko_pwbr["category"]))
recent_tagged["category"] = recent_tagged["ko"].map(ko_to_cat).fillna("unannotated")

t1_results = []
for cat in ["regulatory", "metabolic", "mixed", "other", "unannotated"]:
    sub = recent_tagged[(recent_tagged["category"] == cat) & recent_tagged["mge_fraction"].notna()]
    n = len(sub)
    if n == 0: continue
    mean_mge = sub["mge_fraction"].mean()
    median_mge = sub["mge_fraction"].median()
    pct_high = 100 * (sub["mge_fraction"] >= 0.05).mean()
    print(f"  {cat}: n_gains = {n:,}, mean MGE-fraction = {mean_mge:.4f}, "
          f"median = {median_mge:.4f}, % MGE ≥ 5% = {pct_high:.1f}%", flush=True)
    t1_results.append({"category": cat, "n_gains": n, "mean_mge_fraction": float(mean_mge),
                       "median_mge_fraction": float(median_mge), "pct_with_mge_ge_5pct": float(pct_high)})

# T2 hypothesis-targeted
print("\n--- T2: pre-registered hypotheses ---", flush=True)
MYCOLIC_PATHWAYS = {"ko00061", "ko00071", "ko01040", "ko00540"}
MYCOLIC_SPECIFIC_KOS = {"K11212", "K11211", "K11778", "K11533", "K11534",
                        "K00208", "K20274", "K11782", "K01205", "K00667", "K00507"}
def is_mycolic_ko(row):
    if row["ko"] in MYCOLIC_SPECIFIC_KOS: return True
    p = row.get("pathway_ids", "")
    if not isinstance(p, str): return False
    return bool(set(p.split(",")) & MYCOLIC_PATHWAYS)
ko_pwbr["is_mycolic"] = ko_pwbr.apply(is_mycolic_ko, axis=1)
mycolic_kos = set(ko_pwbr[ko_pwbr["is_mycolic"]]["ko"])

PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}
PUL_KOS = {"K21572", "K21573", "K00686", "K01187", "K01193", "K01205", "K01207", "K01218",
           "K01776", "K17241", "K15922", "K15923"}

t2_results = []
for label, focal_filter, ko_set in [
    ("Mycobacteriaceae × mycolic", recent_tagged["family"] == "f__Mycobacteriaceae", mycolic_kos),
    ("Cyanobacteriia × PSII (class)", recent_tagged["class"] == "c__Cyanobacteriia", PSII_KOS),
    ("Bacteroidota × PUL", recent_tagged["phylum"] == "p__Bacteroidota", PUL_KOS),
]:
    sub = recent_tagged[focal_filter & recent_tagged["ko"].isin(ko_set) & recent_tagged["mge_fraction"].notna()]
    if len(sub) == 0:
        print(f"  {label}: no recent gains")
        continue
    mean_mge = sub["mge_fraction"].mean()
    median_mge = sub["mge_fraction"].median()
    pct_high = 100 * (sub["mge_fraction"] >= 0.05).mean()
    print(f"  {label}: n_gains = {len(sub):,}, mean MGE-fraction = {mean_mge:.4f}, "
          f"median = {median_mge:.4f}, % MGE ≥ 5% = {pct_high:.1f}%", flush=True)
    t2_results.append({"hypothesis": label, "n_gains": len(sub), "mean_mge": float(mean_mge),
                       "median_mge": float(median_mge), "pct_high": float(pct_high)})

# T3 biome-stratified
print("\n--- T3: biome-stratified MGE rate ---", flush=True)
env = pd.read_parquet(DATA_DIR / "p4d1_env_per_species.parquet")
def text_blob(row):
    cols = ["mgnify_biomes", "env_broad_scale", "env_local_scale", "env_medium",
            "isolation_source", "host", "sample_type", "host_disease"]
    return " ".join(str(row.get(c, "")).lower() for c in cols if pd.notna(row.get(c)))
env["blob"] = env.apply(text_blob, axis=1)
def has_pat(blob, patterns):
    return any(p in blob for p in patterns)
env["is_marine"] = env["blob"].apply(lambda b: has_pat(b, ["marine", "ocean", "sea", "saline"]))
env["is_soil"] = env["blob"].apply(lambda b: has_pat(b, ["soil", "rhizosphere", "sediment"]))
env["is_hostpath"] = env["blob"].apply(lambda b: has_pat(b, ["lung", "sputum", "tuberc", "leprosy", "human-skin"]))
env["is_gut"] = env["blob"].apply(lambda b: has_pat(b, ["gut", "rumen", "feces", "fecal", "intestin"]))

genus_biome = env.groupby("genus").agg(
    n_species=("gtdb_species_clade_id", "count"),
    pct_marine=("is_marine", "mean"),
    pct_soil=("is_soil", "mean"),
    pct_hostpath=("is_hostpath", "mean"),
    pct_gut=("is_gut", "mean"),
).reset_index()

recent_with_biome = recent_tagged.merge(genus_biome, left_on="recipient_genus", right_on="genus", how="left", suffixes=("", "_biome"))
recent_with_biome["genus_biome"] = "other"
recent_with_biome.loc[recent_with_biome["pct_marine"] >= 0.3, "genus_biome"] = "marine"
recent_with_biome.loc[recent_with_biome["pct_soil"] >= 0.3, "genus_biome"] = "soil"
recent_with_biome.loc[recent_with_biome["pct_hostpath"] >= 0.3, "genus_biome"] = "hostpath"
recent_with_biome.loc[recent_with_biome["pct_gut"] >= 0.3, "genus_biome"] = "gut"

t3_results = []
for biome in ["marine", "soil", "hostpath", "gut", "other"]:
    sub = recent_with_biome[(recent_with_biome["genus_biome"] == biome) & recent_with_biome["mge_fraction"].notna()]
    if len(sub) == 0: continue
    mean_mge = sub["mge_fraction"].mean()
    median_mge = sub["mge_fraction"].median()
    pct_high = 100 * (sub["mge_fraction"] >= 0.05).mean()
    print(f"  {biome}: n_gains = {len(sub):,}, mean MGE = {mean_mge:.4f}, "
          f"median = {median_mge:.4f}, % MGE ≥ 5% = {pct_high:.1f}%", flush=True)
    t3_results.append({"biome": biome, "n_gains": len(sub), "mean_mge": float(mean_mge),
                       "median_mge": float(median_mge), "pct_high": float(pct_high)})

# Diagnostics + figure
diag = {
    "phase": "4", "deliverable": "P4-D2",
    "purpose": "MGE context per recent gain event",
    "n_total_clusters": int(total_clusters), "n_mge_clusters": int(total_mge),
    "atlas_mge_pct": round(100*total_mge/total_clusters, 3),
    "n_ko_genus_pairs": int(len(ko_genus_mge)),
    "n_recent_gains_tagged": int(recent_tagged["mge_fraction"].notna().sum()),
    "t1_per_category": t1_results,
    "t2_per_hypothesis": t2_results,
    "t3_per_biome": t3_results,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d2_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
print(f"\nWrote p4d2_diagnostics.json", flush=True)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
ax = axes[0]
cats = [r["category"] for r in t1_results]
vals = [r["mean_mge_fraction"] for r in t1_results]
ax.bar(cats, vals, color=["#d62728", "#2ca02c", "#9467bd", "lightgray", "lightgray"][:len(cats)])
for i, r in enumerate(t1_results):
    ax.text(i, vals[i] + 0.0005, f"n={r['n_gains']:,}", ha="center", fontsize=8)
ax.set_ylabel("Mean MGE fraction"); ax.set_title("T1 KO category"); ax.grid(axis="y", alpha=0.3)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")

ax = axes[1]
labels = [r["hypothesis"][:25] for r in t2_results]
vals = [r["mean_mge"] for r in t2_results]
ax.bar(labels, vals, color="#1f77b4")
for i, r in enumerate(t2_results):
    ax.text(i, vals[i] + 0.0005, f"n={r['n_gains']:,}", ha="center", fontsize=8)
ax.set_ylabel("Mean MGE fraction"); ax.set_title("T2 pre-registered")
plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
ax.grid(axis="y", alpha=0.3)

ax = axes[2]
biomes = [r["biome"] for r in t3_results]
vals = [r["mean_mge"] for r in t3_results]
ax.bar(biomes, vals, color=["#1f77b4", "#8c564b", "#e377c2", "#7f7f7f", "lightgray"][:len(biomes)])
for i, r in enumerate(t3_results):
    ax.text(i, vals[i] + 0.0005, f"n={r['n_gains']:,}", ha="center", fontsize=8)
ax.set_ylabel("Mean MGE fraction"); ax.set_title("T3 genus dominant biome")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d2_mge_context_panel.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
