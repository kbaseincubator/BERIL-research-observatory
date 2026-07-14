"""NB26 / P4-D2 — MGE context per gain event.

Tag each M22 recent gain event with MGE-context fraction via keyword matching on
bakta_annotations.product. genomad_mobile_elements is NOT ingested in BERDL (verified
via catalog scan), so bakta product field is the only path.

Method:
  1. Flag gene_clusters with MGE-context products (keywords: phage, transposase,
     integrase, plasmid, mobile, IS element, conjugation, recombinase, prophage)
  2. For each (KO × gtdb_species_clade_id), compute MGE-fraction = MGE-flagged
     clusters / total clusters carrying that KO in that species
  3. For each M22 recent gain event (ko × recipient_genus), aggregate species-level
     MGE fractions across constituent species
  4. Tests:
     - T1 atlas-wide MGE rate per KO category (regulatory / metabolic / mixed)
     - T2 pre-registered hypotheses: Mycobacteriaceae × mycolic / Cyanobacteriia ×
       PSII / Bacteroidota × PUL
     - T3 biome-stratified MGE rate (using P4-D1 substrate)

Outputs:
  data/p4d2_ko_species_mge_fraction.parquet — per (KO × species) MGE fraction
  data/p4d2_recent_gain_mge_attributed.parquet — per gain event MGE-context
  data/p4d2_diagnostics.json
  figures/p4d2_mge_context_panel.png
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

t0 = time.time()
print("=== NB26 / P4-D2 — MGE context per gain event ===", flush=True)

spark = get_spark_session()

# Stage 1: build MGE-flag and KO assignment per gene_cluster
# Filter bakta_annotations to clusters with non-null KO, capture product + KO
print("\nStage 1: pull per-gene_cluster KO + MGE-flag from bakta_annotations", flush=True)

# MGE keywords (case-insensitive)
MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
# Combine into a single regex (case-insensitive) for Spark
mge_regex = "|".join(MGE_KEYWORDS)
print(f"  MGE keyword regex: {len(MGE_KEYWORDS)} terms", flush=True)

bakta = spark.table("kbase_ke_pangenome.bakta_annotations").select("gene_cluster_id", "product", "kegg_orthology_id")
print(f"  bakta_annotations total rows: 132,538,155 (per schema)", flush=True)

# Filter to clusters with KO, flag MGE in product
bakta_with_ko = (bakta
    .filter(F.col("kegg_orthology_id").isNotNull() & (F.col("kegg_orthology_id") != ""))
    .withColumn("is_mge",
        F.when(F.col("product").isNotNull() & F.lower(F.col("product")).rlike(mge_regex), 1).otherwise(0))
    .select("gene_cluster_id", "kegg_orthology_id", "is_mge"))

# Split kegg_orthology_id (can have multiple KO IDs comma-separated). Just take the first.
bakta_clean = bakta_with_ko.withColumn("ko", F.split(F.col("kegg_orthology_id"), ",").getItem(0))

print(f"  filtering + flagging done; counting...", flush=True)
n_ko_clusters = bakta_clean.count()
print(f"  gene_clusters with KO: {n_ko_clusters:,}", flush=True)
n_mge = bakta_clean.filter(F.col("is_mge") == 1).count()
print(f"  KO clusters flagged MGE: {n_mge:,} ({100*n_mge/n_ko_clusters:.2f}%)", flush=True)

# Stage 2: join with gene_cluster to get gtdb_species_clade_id, compute (KO × species) MGE fraction
print("\nStage 2: join with gene_cluster, compute (KO × species) MGE fraction", flush=True)
gc = spark.table("kbase_ke_pangenome.gene_cluster").select("gene_cluster_id", "gtdb_species_clade_id")
joined = bakta_clean.join(gc, "gene_cluster_id", "inner")
ko_species_mge = (joined
    .groupBy("ko", "gtdb_species_clade_id")
    .agg(F.count("*").alias("n_clusters"),
         F.sum("is_mge").alias("n_mge_clusters"))
    .withColumn("mge_fraction", F.col("n_mge_clusters") / F.col("n_clusters")))
print(f"  triggering compute via toPandas...", flush=True)
ko_species_mge_pd = ko_species_mge.toPandas()
print(f"  (KO × species) rows: {len(ko_species_mge_pd):,}", flush=True)
print(f"  MGE-fraction summary: min={ko_species_mge_pd['mge_fraction'].min():.3f}, "
      f"mean={ko_species_mge_pd['mge_fraction'].mean():.3f}, "
      f"median={ko_species_mge_pd['mge_fraction'].median():.3f}, "
      f"max={ko_species_mge_pd['mge_fraction'].max():.3f}", flush=True)
ko_species_mge_pd.to_parquet(DATA_DIR / "p4d2_ko_species_mge_fraction.parquet", index=False)
print(f"  saved p4d2_ko_species_mge_fraction.parquet", flush=True)

# Stage 3: build species → genus mapping for joining recent gains
print("\nStage 3: per recent-gain (KO × recipient_genus) MGE fraction", flush=True)
species_meta = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")[
    ["gtdb_species_clade_id", "genus", "family", "order", "class", "phylum"]]
ko_species_with_genus = ko_species_mge_pd.merge(species_meta, on="gtdb_species_clade_id", how="inner")
print(f"  (KO × species × genus): {len(ko_species_with_genus):,}", flush=True)

# Aggregate to (ko × genus) level
ko_genus_mge = (ko_species_with_genus
    .groupby(["ko", "genus"])
    .agg(n_species=("gtdb_species_clade_id", "count"),
         total_clusters=("n_clusters", "sum"),
         total_mge_clusters=("n_mge_clusters", "sum"))
    .reset_index())
ko_genus_mge["mge_fraction_genus"] = ko_genus_mge["total_mge_clusters"] / ko_genus_mge["total_clusters"]
print(f"  (KO × genus) rows: {len(ko_genus_mge):,}", flush=True)

# Stage 4: tag M22 recent gains
gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
recent = gains[gains["depth_bin"] == "recent"].dropna(subset=["recipient_genus"])
print(f"\n  M22 recent gains with genus: {len(recent):,}", flush=True)

recent_tagged = recent.merge(ko_genus_mge[["ko", "genus", "mge_fraction_genus", "n_species", "total_clusters", "total_mge_clusters"]],
                              left_on=["ko", "recipient_genus"], right_on=["ko", "genus"], how="left")
print(f"  recent gains joined to MGE: {len(recent_tagged):,}", flush=True)
print(f"  with non-null MGE fraction: {recent_tagged['mge_fraction_genus'].notna().sum():,}", flush=True)
recent_tagged.to_parquet(DATA_DIR / "p4d2_recent_gain_mge_attributed.parquet", index=False)

# Stage 5: tests
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
    sub = recent_tagged[(recent_tagged["category"] == cat) & recent_tagged["mge_fraction_genus"].notna()]
    n = len(sub)
    if n == 0: continue
    mean_mge = sub["mge_fraction_genus"].mean()
    median_mge = sub["mge_fraction_genus"].median()
    pct_high = 100 * (sub["mge_fraction_genus"] >= 0.05).mean()  # ≥5% MGE-context
    print(f"  {cat}: n_gains = {n:,}, mean MGE-fraction = {mean_mge:.4f}, median = {median_mge:.4f}, "
          f"% with MGE ≥ 5% = {pct_high:.1f}%", flush=True)
    t1_results.append({"category": cat, "n_gains": n, "mean_mge_fraction": float(mean_mge),
                       "median_mge_fraction": float(median_mge), "pct_with_mge_ge_5pct": float(pct_high)})

print("\n--- T2: pre-registered hypothesis MGE rates ---", flush=True)

# Mycolic
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

# PSII
PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}

# PUL — use the bacteroidota_pul KO list from Phase 1B if available
# Otherwise, fall back to: SusC/SusD homologs and BRITE 02000 (Transporters)
# A simpler proxy: K21572 (susC) and K21573 (susD) — outer membrane PUL transporters
PUL_KOS = {"K21572", "K21573", "K00686", "K01187", "K01193", "K01205", "K01207", "K01218",
           "K01776", "K17241", "K15922", "K15923"}

t2_results = []
for label, focal_filter, ko_set in [
    ("Mycobacteriaceae × mycolic", recent_tagged["family"] == "f__Mycobacteriaceae", mycolic_kos),
    ("Cyanobacteriia × PSII (class)", recent_tagged["class"] == "c__Cyanobacteriia", PSII_KOS),
    ("Bacteroidota × PUL", recent_tagged["phylum"] == "p__Bacteroidota", PUL_KOS),
]:
    sub = recent_tagged[focal_filter & recent_tagged["ko"].isin(ko_set) & recent_tagged["mge_fraction_genus"].notna()]
    if len(sub) == 0:
        print(f"  {label}: no recent gains")
        continue
    mean_mge = sub["mge_fraction_genus"].mean()
    median_mge = sub["mge_fraction_genus"].median()
    pct_high = 100 * (sub["mge_fraction_genus"] >= 0.05).mean()
    print(f"  {label}: n_gains = {len(sub):,}, mean MGE-fraction = {mean_mge:.4f}, "
          f"median = {median_mge:.4f}, % with MGE ≥ 5% = {pct_high:.1f}%", flush=True)
    t2_results.append({"hypothesis": label, "n_gains": len(sub), "mean_mge": float(mean_mge),
                       "median_mge": float(median_mge), "pct_high": float(pct_high)})

# Stage 6: T3 biome-stratified
print("\n--- T3: biome-stratified MGE rate ---", flush=True)
env = pd.read_parquet(DATA_DIR / "p4d1_env_per_species.parquet")
# Merge per-species biome flags onto recent_tagged (via genus → species → biome)
species_biomes = env[["gtdb_species_clade_id", "genus"]].copy()
# Build per-genus biome fractions (atlas-side)
def text_blob(row, env_cols=["mgnify_biomes", "env_broad_scale", "env_local_scale", "env_medium",
                              "isolation_source", "host", "sample_type", "host_disease"]):
    return " ".join(str(row.get(c, "")).lower() for c in env_cols if pd.notna(row.get(c)))
env["blob"] = env.apply(text_blob, axis=1)
def has_pat(blob, patterns):
    return any(p in blob for p in patterns)
env["is_marine"] = env["blob"].apply(lambda b: has_pat(b, ["marine", "ocean", "sea", "saline"]))
env["is_soil"] = env["blob"].apply(lambda b: has_pat(b, ["soil", "rhizosphere", "sediment"]))
env["is_hostpath"] = env["blob"].apply(lambda b: has_pat(b, ["lung", "sputum", "tuberc", "leprosy", "host_disease", "human-skin"]))
env["is_gut"] = env["blob"].apply(lambda b: has_pat(b, ["gut", "rumen", "feces", "fecal", "intestin"]))

# Per-genus biome flags (any species in genus tagged with biome)
genus_biome = env.groupby("genus").agg(
    n_species=("gtdb_species_clade_id", "count"),
    pct_marine=("is_marine", "mean"),
    pct_soil=("is_soil", "mean"),
    pct_hostpath=("is_hostpath", "mean"),
    pct_gut=("is_gut", "mean"),
).reset_index()
recent_with_biome = recent_tagged.merge(genus_biome, left_on="recipient_genus", right_on="genus", how="left")

# Categorize each recent gain by genus dominant biome (>30% threshold)
recent_with_biome["genus_biome"] = "other"
recent_with_biome.loc[recent_with_biome["pct_marine"] >= 0.3, "genus_biome"] = "marine"
recent_with_biome.loc[recent_with_biome["pct_soil"] >= 0.3, "genus_biome"] = "soil"
recent_with_biome.loc[recent_with_biome["pct_hostpath"] >= 0.3, "genus_biome"] = "hostpath"
recent_with_biome.loc[recent_with_biome["pct_gut"] >= 0.3, "genus_biome"] = "gut"

t3_results = []
for biome in ["marine", "soil", "hostpath", "gut", "other"]:
    sub = recent_with_biome[(recent_with_biome["genus_biome"] == biome) & recent_with_biome["mge_fraction_genus"].notna()]
    if len(sub) == 0: continue
    mean_mge = sub["mge_fraction_genus"].mean()
    median_mge = sub["mge_fraction_genus"].median()
    pct_high = 100 * (sub["mge_fraction_genus"] >= 0.05).mean()
    print(f"  {biome}: n_gains = {len(sub):,}, mean MGE = {mean_mge:.4f}, "
          f"median = {median_mge:.4f}, % MGE ≥ 5% = {pct_high:.1f}%", flush=True)
    t3_results.append({"biome": biome, "n_gains": len(sub), "mean_mge": float(mean_mge),
                       "median_mge": float(median_mge), "pct_high": float(pct_high)})

# Save diagnostics
diag = {
    "phase": "4", "deliverable": "P4-D2",
    "purpose": "MGE context per recent gain event",
    "n_ko_clusters_total": int(n_ko_clusters),
    "n_mge_flagged_clusters": int(n_mge),
    "atlas_mge_pct": round(100*n_mge/n_ko_clusters, 3),
    "n_ko_species_pairs": int(len(ko_species_mge_pd)),
    "n_recent_gains_tagged": int(recent_tagged["mge_fraction_genus"].notna().sum()),
    "t1_per_category": t1_results,
    "t2_per_hypothesis": t2_results,
    "t3_per_biome": t3_results,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d2_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)

# Figure
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: T1 KO category
ax = axes[0]
cats = [r["category"] for r in t1_results]
mge_vals = [r["mean_mge_fraction"] for r in t1_results]
ax.bar(cats, mge_vals, color=["#d62728", "#2ca02c", "#9467bd", "lightgray", "lightgray"][:len(cats)])
ax.set_ylabel("Mean MGE fraction"); ax.set_title("T1 KO category")
for i, r in enumerate(t1_results):
    ax.text(i, mge_vals[i] + 0.0005, f"n={r['n_gains']:,}", ha="center", fontsize=8)
ax.grid(axis="y", alpha=0.3)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")

# Panel B: T2 hypothesis
ax = axes[1]
labels = [r["hypothesis"][:30] for r in t2_results]
mge_vals = [r["mean_mge"] for r in t2_results]
ax.bar(labels, mge_vals, color="#1f77b4")
ax.set_ylabel("Mean MGE fraction"); ax.set_title("T2 pre-registered hypotheses")
for i, r in enumerate(t2_results):
    ax.text(i, mge_vals[i] + 0.0005, f"n={r['n_gains']:,}", ha="center", fontsize=8)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
ax.grid(axis="y", alpha=0.3)

# Panel C: T3 biome
ax = axes[2]
biomes = [r["biome"] for r in t3_results]
mge_vals = [r["mean_mge"] for r in t3_results]
ax.bar(biomes, mge_vals, color=["#1f77b4", "#8c564b", "#e377c2", "#7f7f7f", "lightgray"][:len(biomes)])
ax.set_ylabel("Mean MGE fraction"); ax.set_title("T3 genus dominant biome")
for i, r in enumerate(t3_results):
    ax.text(i, mge_vals[i] + 0.0005, f"n={r['n_gains']:,}", ha="center", fontsize=8)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d2_mge_context_panel.png", dpi=120, bbox_inches="tight")
print(f"\nWrote figure", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
