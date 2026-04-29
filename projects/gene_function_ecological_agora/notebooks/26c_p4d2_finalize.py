"""NB26c — finalize P4-D2 from MinIO output. Re-reads ko_genus_mge MinIO parquet
and runs all the tests + figure that NB26b couldn't finish due to a pyarrow
metadata serialization quirk on Spark-Connect-derived pandas frames.
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
print("=== NB26c — P4-D2 finalize ===", flush=True)

spark = get_spark_session()
ko_genus_mge_spark = spark.read.parquet(MINIO_PATH)
ko_genus_mge_pd = ko_genus_mge_spark.toPandas()
# Strip metadata via explicit reconstruction
ko_genus_mge = pd.DataFrame({c: ko_genus_mge_pd[c].values for c in ko_genus_mge_pd.columns})
print(f"(ko × genus) MGE rows: {len(ko_genus_mge):,}", flush=True)

total_clusters = int(ko_genus_mge["n_clusters"].sum())
total_mge = int(ko_genus_mge["n_mge_clusters"].sum())
print(f"atlas-wide: {total_clusters:,} KO-bearing clusters, {total_mge:,} MGE ({100*total_mge/total_clusters:.3f}%)", flush=True)

ko_genus_mge.to_parquet(DATA_DIR / "p4d2_ko_genus_mge.parquet", index=False)

species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

# Tag M22 recent gains
print("\nTag M22 recent gains", flush=True)
gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
recent = gains[gains["depth_bin"] == "recent"].dropna(subset=["recipient_genus"])
recent_tagged = recent.merge(
    ko_genus_mge.rename(columns={"genus": "recipient_genus"}),
    on=["ko", "recipient_genus"], how="left")

# Add taxonomy
species_tax = species[["genus", "family", "order", "class", "phylum"]].drop_duplicates(subset="genus")
recent_tagged = recent_tagged.merge(species_tax, left_on="recipient_genus", right_on="genus", how="left")
print(f"  recent gains tagged: {recent_tagged['mge_fraction'].notna().sum():,} of {len(recent_tagged):,}", flush=True)
recent_tagged.to_parquet(DATA_DIR / "p4d2_recent_gain_mge_attributed.parquet", index=False)

# T1 KO category
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

print("\n--- T1 per-KO-category MGE rate ---", flush=True)
t1_results = []
for cat in ["regulatory", "metabolic", "mixed", "other", "unannotated"]:
    sub = recent_tagged[(recent_tagged["category"] == cat) & recent_tagged["mge_fraction"].notna()]
    n = len(sub)
    if n == 0: continue
    print(f"  {cat}: n={n:,}, mean MGE={sub['mge_fraction'].mean():.4f}, "
          f"median={sub['mge_fraction'].median():.4f}, %≥5%={(sub['mge_fraction']>=0.05).mean()*100:.1f}%", flush=True)
    t1_results.append({"category": cat, "n_gains": n, "mean_mge_fraction": float(sub['mge_fraction'].mean()),
                       "median_mge_fraction": float(sub['mge_fraction'].median()),
                       "pct_with_mge_ge_5pct": float((sub['mge_fraction']>=0.05).mean()*100)})

# T2 hypotheses
print("\n--- T2 pre-registered hypotheses ---", flush=True)
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
    print(f"  {label}: n={len(sub):,}, mean MGE={sub['mge_fraction'].mean():.4f}, "
          f"median={sub['mge_fraction'].median():.4f}, %≥5%={(sub['mge_fraction']>=0.05).mean()*100:.1f}%", flush=True)
    t2_results.append({"hypothesis": label, "n_gains": int(len(sub)),
                       "mean_mge": float(sub['mge_fraction'].mean()),
                       "median_mge": float(sub['mge_fraction'].median()),
                       "pct_high": float((sub['mge_fraction']>=0.05).mean()*100)})

# T3 biome
print("\n--- T3 biome-stratified MGE rate ---", flush=True)
env_pd = pd.read_parquet(DATA_DIR / "p4d1_env_per_species.parquet")
env = pd.DataFrame({c: env_pd[c].values for c in env_pd.columns})

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

recent_with_biome = recent_tagged.merge(genus_biome, left_on="recipient_genus", right_on="genus", how="left", suffixes=("", "_b"))
recent_with_biome["genus_biome"] = "other"
recent_with_biome.loc[recent_with_biome["pct_marine"] >= 0.3, "genus_biome"] = "marine"
recent_with_biome.loc[recent_with_biome["pct_soil"] >= 0.3, "genus_biome"] = "soil"
recent_with_biome.loc[recent_with_biome["pct_hostpath"] >= 0.3, "genus_biome"] = "hostpath"
recent_with_biome.loc[recent_with_biome["pct_gut"] >= 0.3, "genus_biome"] = "gut"

t3_results = []
for biome in ["marine", "soil", "hostpath", "gut", "other"]:
    sub = recent_with_biome[(recent_with_biome["genus_biome"] == biome) & recent_with_biome["mge_fraction"].notna()]
    if len(sub) == 0: continue
    print(f"  {biome}: n={len(sub):,}, mean MGE={sub['mge_fraction'].mean():.4f}, "
          f"median={sub['mge_fraction'].median():.4f}, %≥5%={(sub['mge_fraction']>=0.05).mean()*100:.1f}%", flush=True)
    t3_results.append({"biome": biome, "n_gains": int(len(sub)),
                       "mean_mge": float(sub['mge_fraction'].mean()),
                       "median_mge": float(sub['mge_fraction'].median()),
                       "pct_high": float((sub['mge_fraction']>=0.05).mean()*100)})

# Diagnostics + figure
diag = {
    "phase": "4", "deliverable": "P4-D2",
    "purpose": "MGE context per recent gain event",
    "n_total_clusters": total_clusters, "n_mge_clusters": total_mge,
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
