"""NB25 / P4-D1 — AlphaEarth env-cluster × function-class recent acquisition.

For the 5,157 species with AlphaEarth 64-dim env embeddings, cluster into k=10 env
clusters (k-means). For each env-cluster × function-class, compute mean recent-gain
rate per genus represented in that cluster.

This is the project's *quantitative* env-aware test: is M22 recent-acquisition rate
biome-stratified at finer resolution than discrete biome labels?

Tests:
  T1: Per env-cluster, dominant biome label (sanity check that clusters recover
      ecological structure).
  T2: Per (env-cluster × function-class), mean recent-rank gain count per genus
      represented. Heatmap.
  T3: Per pre-registered hypothesis, do focal-clade species cluster preferentially in
      specific env-clusters?

Outputs:
  data/p4d1_alphaearth_clusters.tsv — per-species env-cluster assignment
  data/p4d1_alphaearth_diagnostics.json
  figures/p4d1_alphaearth_env_cluster_panel.png
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"

t0 = time.time()
print("=== NB25 / P4-D1 — AlphaEarth env-cluster x function-class ===", flush=True)

env = pd.read_parquet(DATA_DIR / "p4d1_env_per_species.parquet")
ae_cols = [f"A{n:02d}" for n in range(64)]
has_ae = env[ae_cols[0]].notna()
print(f"P1B species with AlphaEarth: {has_ae.sum():,} of {len(env):,}", flush=True)

ae_df = env[has_ae].copy().reset_index(drop=True)

# Stage 1: K-means clustering
print("\nStage 1: K-means clustering (k=10)", flush=True)
X = ae_df[ae_cols].values
km = KMeans(n_clusters=10, random_state=42, n_init=10)
ae_df["env_cluster"] = km.fit_predict(X)
print(f"  cluster sizes: {ae_df['env_cluster'].value_counts().sort_index().to_dict()}", flush=True)

# Stage 2: dominant biome per cluster (sanity check)
print("\nStage 2: dominant biome per cluster", flush=True)
cluster_biome = []
for c in range(10):
    sub = ae_df[ae_df["env_cluster"] == c]
    n = len(sub)
    # Use mgnify_biomes if available, else env_broad_scale, else isolation_source
    biome_counts = {}
    for biome_str in sub["mgnify_biomes"].dropna():
        for b in str(biome_str).split(";"):
            biome_counts[b] = biome_counts.get(b, 0) + 1
    top_mg = sorted(biome_counts.items(), key=lambda x: -x[1])[:3]
    iso_counts = sub["isolation_source"].value_counts().head(3).to_dict()
    print(f"  cluster {c} (n={n}): top MGnify biomes = {top_mg}; top isolation = {iso_counts}", flush=True)
    cluster_biome.append({"cluster": int(c), "n": int(n),
                          "top_mgnify_biomes": top_mg,
                          "top_isolation_sources": iso_counts})

# Stage 3: per (env-cluster × function-class) recent-gain rate
print("\nStage 3: per (env-cluster × function-class) recent-gain rate", flush=True)
gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
recent_gains = gains[gains["depth_bin"] == "recent"].dropna(subset=["recipient_genus"])
print(f"  recent gains with genus attribution: {len(recent_gains):,}", flush=True)

# KO category map (regulatory/metabolic/mixed)
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
REG_PATHWAY_PREFIXES = {f"ko03{n:03d}" for n in range(0, 100)}
REG_PATHWAY_RANGES = {f"ko0{n:04d}" for n in [2010, 2020, 2024, 2025, 2026, 2030, 2040, 2060, 2065]}
REG_PATHWAYS = REG_PATHWAY_PREFIXES | REG_PATHWAY_RANGES
def is_metabolic(p):
    if not p.startswith("ko"): return False
    try: n = int(p[2:])
    except ValueError: return False
    return n < 2000
def classify(pwy_str):
    if not isinstance(pwy_str, str) or pwy_str == "": return "unannotated"
    pwys = set(pwy_str.split(","))
    n_reg = sum(1 for p in pwys if p in REG_PATHWAYS)
    n_met = sum(1 for p in pwys if is_metabolic(p))
    if n_reg > 0 and n_met == 0: return "regulatory"
    if n_met > 0 and n_reg == 0: return "metabolic"
    if n_reg > 0 and n_met > 0: return "mixed"
    return "other"
ko_pwbr["category"] = ko_pwbr["pathway_ids"].apply(classify)
ko_to_cat = dict(zip(ko_pwbr["ko"], ko_pwbr["category"]))

# Per-genus recent-gain count by category
recent_gains["category"] = recent_gains["ko"].map(ko_to_cat).fillna("unannotated")
gain_per_genus = recent_gains.groupby(["recipient_genus", "category"]).size().unstack(fill_value=0).reset_index()
gain_per_genus.columns.name = None
print(f"  per-genus recent-gain matrix: {gain_per_genus.shape}", flush=True)

# Aggregate cluster: for each species, attribute its genus's gain count, then average per cluster
cluster_gain = ae_df[["env_cluster", "genus", "phylum", "family"]].merge(
    gain_per_genus, left_on="genus", right_on="recipient_genus", how="left"
).fillna(0)

# Per cluster, mean per-species recent-gain count by category
cluster_summary = cluster_gain.groupby("env_cluster")[["regulatory", "metabolic", "mixed", "unannotated", "other"]].mean()
print(f"\n  per-cluster mean recent-gain count per species (by category):")
print(cluster_summary.round(1).to_string(), flush=True)

# Stage 4: focal clade × env-cluster distribution
print("\nStage 4: focal clade env-cluster distribution", flush=True)
focal_dist = {}
for clade_name, filter_col, filter_val in [
    ("Cyanobacteriia", "class", "c__Cyanobacteriia"),
    ("Mycobacteriaceae", "family", "f__Mycobacteriaceae"),
    ("Bacteroidota", "phylum", "p__Bacteroidota"),
]:
    sub = ae_df[ae_df[filter_col] == filter_val]
    n = len(sub)
    if n == 0:
        print(f"  {clade_name}: no AE-covered species")
        focal_dist[clade_name] = {"n": 0, "cluster_counts": {}}
        continue
    cc = sub["env_cluster"].value_counts().sort_index().to_dict()
    cc_pct = {int(k): round(100*v/n, 1) for k, v in cc.items()}
    print(f"  {clade_name} (n_AE={n}): cluster_pct = {cc_pct}", flush=True)
    focal_dist[clade_name] = {"n": int(n), "cluster_pct": cc_pct}

# Save
ae_df[["gtdb_species_clade_id", "GTDB_species", "phylum", "class", "family", "genus",
       "cleaned_lat", "cleaned_lon", "cleaned_year", "env_cluster",
       "isolation_source", "env_broad_scale", "mgnify_biomes"]].to_csv(
    DATA_DIR / "p4d1_alphaearth_clusters.tsv", sep="\t", index=False)
print(f"\nWrote p4d1_alphaearth_clusters.tsv", flush=True)

diagnostics = {
    "phase": "4", "deliverable": "P4-D1 NB25",
    "purpose": "AlphaEarth env-cluster × function-class quantitative test",
    "n_species_with_alphaearth": int(len(ae_df)),
    "k_clusters": 10,
    "cluster_biome_summary": cluster_biome,
    "cluster_recent_gain_per_species": cluster_summary.round(2).to_dict(),
    "focal_clade_cluster_distribution": focal_dist,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d1_alphaearth_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)

# Figure
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Panel A: cluster-by-category mean gain heatmap
ax = axes[0]
mat = cluster_summary[["regulatory", "metabolic", "mixed", "other", "unannotated"]].values
im = ax.imshow(mat, aspect="auto", cmap="viridis")
ax.set_xticks(range(5)); ax.set_xticklabels(["reg", "met", "mixed", "other", "unann"])
ax.set_yticks(range(10)); ax.set_yticklabels([f"C{c}" for c in range(10)])
ax.set_xlabel("KO category"); ax.set_ylabel("Env cluster")
ax.set_title("Mean per-species recent-gain count\nby env-cluster × KO category")
plt.colorbar(im, ax=ax)

# Panel B: focal clade env-cluster distribution
ax = axes[1]
clades = list(focal_dist.keys())
clusters = list(range(10))
mat = np.zeros((len(clades), 10))
for i, cl in enumerate(clades):
    cd = focal_dist[cl].get("cluster_pct", {})
    for c in clusters:
        mat[i, c] = cd.get(c, 0)
im = ax.imshow(mat, aspect="auto", cmap="Blues")
ax.set_xticks(clusters); ax.set_xticklabels([f"C{c}" for c in clusters])
ax.set_yticks(range(len(clades))); ax.set_yticklabels(clades)
ax.set_xlabel("Env cluster"); ax.set_title("Focal clade env-cluster distribution (%)")
for i in range(len(clades)):
    for c in clusters:
        if mat[i, c] > 0:
            ax.text(c, i, f"{mat[i, c]:.0f}", ha="center", va="center",
                    fontsize=8, color="white" if mat[i, c] > 30 else "black")
plt.colorbar(im, ax=ax)

# Panel C: AE 2D PCA scatter of species, colored by cluster
ax = axes[2]
from sklearn.decomposition import PCA
pc = PCA(n_components=2).fit_transform(X)
for c in range(10):
    mask = ae_df["env_cluster"] == c
    ax.scatter(pc[mask, 0], pc[mask, 1], s=4, alpha=0.4, label=f"C{c}")
ax.set_xlabel("AE PC1"); ax.set_ylabel("AE PC2")
ax.set_title(f"AlphaEarth 2D PCA, n={len(ae_df):,}")
ax.legend(loc="upper right", fontsize=7, ncol=2)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d1_alphaearth_env_cluster_panel.png", dpi=120, bbox_inches="tight")
print(f"\nWrote figure", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
