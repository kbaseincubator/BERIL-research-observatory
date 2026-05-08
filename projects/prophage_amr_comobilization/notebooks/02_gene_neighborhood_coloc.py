"""
NB02: Gene Neighborhood Co-localization
========================================
Requires BERDL JupyterHub (Spark access).

For each AMR gene instance, measure the distance to the nearest prophage
marker on the same contig. Gene ordering is parsed from gene_id format:
  gene_id = "{contig_id}_{gene_number}"   e.g. "NZ_UTEP01000078.1_260"

Uses a strict prophage-core definition (terminase, phage structural,
holin/lysin) to avoid inflating the signal with generic mobile elements.

Strategy:
  - Top-100 species by AMR cluster count (with >=5 genomes)
  - Sample up to 20 genomes per species to keep queries tractable
  - Batch species into groups of 10 for efficient Spark queries
  - Parse contig + gene rank from gene_id
  - For each AMR gene instance, find nearest strict-prophage marker

Outputs:
  data/amr_prophage_distances.csv
  data/coloc_summary.json
  figures/nb02_distance_distribution.png
  figures/nb02_proximal_fraction.png
"""

import json
import os
import sys
import warnings
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Spark session
# ---------------------------------------------------------------------------
try:
    spark = get_spark_session()
except NameError:
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
        from get_spark_session import get_spark_session
        spark = get_spark_session()

print("Spark session ready.")

_script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
PROJECT = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "notebooks" else _script_dir
if not os.path.isdir(os.path.join(PROJECT, "data")):
    PROJECT = os.path.join(os.getcwd(), "projects", "prophage_amr_comobilization")
DATA = os.path.join(PROJECT, "data")
FIG  = os.path.join(PROJECT, "figures")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def parse_gene_id(gene_id):
    """Parse contig_id and gene_number from gene_id.

    Format: "{contig}_{number}" where contig may itself contain underscores.
    The gene number is always the final integer after the last underscore.
    """
    last_underscore = gene_id.rfind("_")
    if last_underscore == -1:
        return gene_id, 0
    contig = gene_id[:last_underscore]
    try:
        num = int(gene_id[last_underscore + 1:])
    except ValueError:
        return gene_id, 0
    return contig, num


# ===================================================================
# 1. Define strict prophage markers (cluster IDs, pulled to Python)
# ===================================================================
print("\n=== 1. Strict Prophage Marker Definition ===")

STRICT_PHAGE_KEYWORDS = [
    "terminase", "phage_portal", "phage_tail", "phage_capsid",
    "phage_baseplate", "tail_fiber", "tail_spike", "holin",
    "endolysin", "phage_lysin", "head_morphogenesis",
    "phage_sheath",
]
strict_kw_pattern = "|".join(STRICT_PHAGE_KEYWORDS)

strict_ids_pd = spark.sql(f"""
    SELECT DISTINCT gene_cluster_id
    FROM kbase_ke_pangenome.bakta_annotations
    WHERE (LOWER(product) RLIKE '{strict_kw_pattern}')
       OR (LOWER(product) LIKE '%phage%'
           AND LOWER(product) NOT LIKE '%transposase%'
           AND LOWER(product) NOT LIKE '%integrase%'
           AND LOWER(product) NOT LIKE '%recombinase%')
""").toPandas()

PHAGE_PFAMS = [
    "Terminase_1", "Terminase_GpA", "Terminase_3", "Terminase_6",
    "Phage_portal", "HK97", "Phage_cap_E",
    "Phage_tail_S", "Phage_sheath", "Phage_fiber",
    "Phage_holin", "Phage_lysozyme",
]
pfam_pattern = "|".join(PHAGE_PFAMS)

pfam_ids_pd = spark.sql(f"""
    SELECT DISTINCT gene_cluster_id
    FROM kbase_ke_pangenome.bakta_pfam_domains
    WHERE pfam_name RLIKE '{pfam_pattern}'
""").toPandas()

prophage_cluster_set = set(strict_ids_pd["gene_cluster_id"]) | set(pfam_ids_pd["gene_cluster_id"])
print(f"Total strict prophage clusters: {len(prophage_cluster_set):,}")

# ===================================================================
# 2. Select target species + load AMR cluster set
# ===================================================================
print("\n=== 2. Select Target Species ===")

species_summary = pd.read_csv(os.path.join(DATA, "amr_prophage_species_summary.csv"))
both_mask = (species_summary["n_amr_clusters"] > 0) & (species_summary["n_prophage_clusters"] > 0)
both_species = species_summary[both_mask & (species_summary["no_genomes"] >= 5)].copy()
target_species = both_species.nlargest(100, "n_amr_clusters")["species_id"].tolist()
print(f"Target species: {len(target_species)}")

amr_clusters = pd.read_csv(os.path.join(DATA, "amr_clusters.csv"))
amr_cluster_set = set(amr_clusters["gene_cluster_id"].unique())
print(f"AMR cluster IDs: {len(amr_cluster_set):,}")

# ===================================================================
# 3. Gene neighborhood analysis — batched bulk queries
# ===================================================================
print("\n=== 3. Gene Neighborhood Co-localization ===")

# Strategy:
# - Batch species into groups of 5
# - For each batch, sample up to 20 genomes per species
# - Pull all genes (gene_id + gene_cluster_id) for sampled genomes
# - Filter locally for AMR/prophage using Python sets
# - Calculate distances in Python/numpy
#
# This minimizes Spark round-trips (20 queries instead of 200)
# while keeping result sizes manageable (~500K rows per batch).

GENOMES_PER_SPECIES = 20
BATCH_SIZE = 5  # species per batch

all_distances = []
t0 = time.time()

for batch_start in range(0, len(target_species), BATCH_SIZE):
    batch_species = target_species[batch_start:batch_start + BATCH_SIZE]
    batch_num = batch_start // BATCH_SIZE + 1
    total_batches = (len(target_species) + BATCH_SIZE - 1) // BATCH_SIZE

    species_in_clause = ", ".join(f"'{sp}'" for sp in batch_species)

    t_batch = time.time()

    # Query: sample genomes, get all gene+junction data
    query = f"""
        SELECT g.gene_id, g.genome_id, j.gene_cluster_id, ge.gtdb_species_clade_id
        FROM kbase_ke_pangenome.gene g
        JOIN kbase_ke_pangenome.genome ge ON g.genome_id = ge.genome_id
        JOIN kbase_ke_pangenome.gene_genecluster_junction j ON g.gene_id = j.gene_id
        WHERE ge.gtdb_species_clade_id IN ({species_in_clause})
        AND g.genome_id IN (
            SELECT genome_id FROM (
                SELECT genome_id, gtdb_species_clade_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY gtdb_species_clade_id
                           ORDER BY genome_id
                       ) AS rn
                FROM kbase_ke_pangenome.genome
                WHERE gtdb_species_clade_id IN ({species_in_clause})
            ) sub
            WHERE rn <= {GENOMES_PER_SPECIES}
        )
    """
    batch_pd = spark.sql(query).toPandas()
    t_query = time.time() - t_batch

    if len(batch_pd) == 0:
        elapsed = time.time() - t0
        print(f"  Batch {batch_num}/{total_batches}: 0 genes (query {t_query:.0f}s, total {elapsed:.0f}s)")
        continue

    # Label AMR and prophage genes locally
    batch_pd["is_amr"] = batch_pd["gene_cluster_id"].isin(amr_cluster_set)
    batch_pd["is_prophage"] = batch_pd["gene_cluster_id"].isin(prophage_cluster_set)

    # For each species in this batch, compute distances
    for species_id in batch_species:
        sp_data = batch_pd[batch_pd["gtdb_species_clade_id"] == species_id]
        amr_genes = sp_data[sp_data["is_amr"]].copy()
        pro_genes = sp_data[sp_data["is_prophage"]].copy()

        if len(amr_genes) == 0:
            continue

        if len(pro_genes) == 0:
            # No prophage in sampled genomes
            for _, row in amr_genes.iterrows():
                contig, gnum = parse_gene_id(row["gene_id"])
                all_distances.append({
                    "species_id": species_id,
                    "genome_id": row["genome_id"],
                    "contig_id": contig,
                    "amr_gene_cluster_id": row["gene_cluster_id"],
                    "gene_num": gnum,
                    "nearest_prophage_distance": np.nan,
                    "contig_has_prophage": False,
                })
            continue

        # Parse prophage positions
        pro_parsed = pro_genes["gene_id"].apply(parse_gene_id)
        pro_genes = pro_genes.copy()
        pro_genes["contig_id"] = [p[0] for p in pro_parsed]
        pro_genes["gene_num"] = [p[1] for p in pro_parsed]

        # Build lookup: (genome_id, contig_id) -> numpy array of prophage gene_nums
        pro_by_contig = {}
        for _, row in pro_genes.iterrows():
            key = (row["genome_id"], row["contig_id"])
            pro_by_contig.setdefault(key, []).append(row["gene_num"])
        for key in pro_by_contig:
            pro_by_contig[key] = np.array(pro_by_contig[key])

        # For each AMR gene, find nearest prophage on same contig
        for _, row in amr_genes.iterrows():
            contig, gnum = parse_gene_id(row["gene_id"])
            key = (row["genome_id"], contig)
            if key in pro_by_contig:
                min_dist = int(np.abs(pro_by_contig[key] - gnum).min())
                all_distances.append({
                    "species_id": species_id,
                    "genome_id": row["genome_id"],
                    "contig_id": contig,
                    "amr_gene_cluster_id": row["gene_cluster_id"],
                    "gene_num": gnum,
                    "nearest_prophage_distance": min_dist,
                    "contig_has_prophage": True,
                })
            else:
                all_distances.append({
                    "species_id": species_id,
                    "genome_id": row["genome_id"],
                    "contig_id": contig,
                    "amr_gene_cluster_id": row["gene_cluster_id"],
                    "gene_num": gnum,
                    "nearest_prophage_distance": np.nan,
                    "contig_has_prophage": False,
                })

    elapsed = time.time() - t0
    done = min(batch_start + BATCH_SIZE, len(target_species))
    rate = elapsed / done * len(target_species) if done > 0 else 0
    print(f"  Batch {batch_num}/{total_batches}: "
          f"{len(batch_pd):,} genes, "
          f"{batch_pd['is_amr'].sum():,} AMR, "
          f"{batch_pd['is_prophage'].sum():,} prophage "
          f"(query {t_query:.0f}s, total {elapsed:.0f}s, "
          f"~{rate - elapsed:.0f}s left)")

# ===================================================================
# 4. Save and summarize
# ===================================================================
print("\n=== 4. Summary ===")

dist_df = pd.DataFrame(all_distances)
dist_df.to_csv(os.path.join(DATA, "amr_prophage_distances.csv"), index=False)
print(f"Total AMR gene instances analyzed: {len(dist_df):,}")
print(f"Unique species: {dist_df['species_id'].nunique():,}")
print(f"Unique genomes: {dist_df['genome_id'].nunique():,}")

has_pro = dist_df[dist_df["contig_has_prophage"] == True].copy()
no_pro = dist_df[dist_df["contig_has_prophage"] == False]
print(f"AMR on contigs WITH prophage: {len(has_pro):,} ({100*len(has_pro)/max(len(dist_df),1):.1f}%)")
print(f"AMR on contigs WITHOUT prophage: {len(no_pro):,} ({100*len(no_pro)/max(len(dist_df),1):.1f}%)")

for threshold in [5, 10, 20, 50]:
    n_prox = (has_pro["nearest_prophage_distance"] <= threshold).sum()
    pct = 100 * n_prox / max(len(dist_df), 1)
    print(f"  Within {threshold:>2d} genes of prophage: {n_prox:,} ({pct:.1f}% of all AMR)")

med_dist = has_pro["nearest_prophage_distance"].median() if len(has_pro) > 0 else float("nan")
mean_dist = has_pro["nearest_prophage_distance"].mean() if len(has_pro) > 0 else float("nan")
print(f"\nMedian distance (on prophage contigs): {med_dist:.0f} genes")
print(f"Mean distance: {mean_dist:.1f} genes")

summary = {
    "total_amr_instances": len(dist_df),
    "unique_species": int(dist_df["species_id"].nunique()),
    "unique_genomes": int(dist_df["genome_id"].nunique()),
    "genomes_sampled_per_species": GENOMES_PER_SPECIES,
    "on_prophage_contig": len(has_pro),
    "on_prophage_contig_pct": round(100 * len(has_pro) / max(len(dist_df), 1), 1),
    "no_prophage_contig": len(no_pro),
    "median_distance_genes": float(med_dist) if not np.isnan(med_dist) else None,
    "mean_distance_genes": round(float(mean_dist), 1) if not np.isnan(mean_dist) else None,
    "proximal_5": int((has_pro["nearest_prophage_distance"] <= 5).sum()),
    "proximal_10": int((has_pro["nearest_prophage_distance"] <= 10).sum()),
    "proximal_20": int((has_pro["nearest_prophage_distance"] <= 20).sum()),
    "proximal_50": int((has_pro["nearest_prophage_distance"] <= 50).sum()),
    "strict_prophage_clusters_used": len(prophage_cluster_set),
}
with open(os.path.join(DATA, "coloc_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSaved data/coloc_summary.json")

# ===================================================================
# 5. Figures
# ===================================================================
print("\n=== 5. Generating Figures ===")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

vals = has_pro["nearest_prophage_distance"].dropna()
if len(vals) > 0:
    axes[0].hist(vals.clip(upper=200), bins=100, color="steelblue", edgecolor="white", linewidth=0.3)
    axes[0].axvline(10, color="red", linestyle="--", label="10-gene threshold")
    axes[0].axvline(20, color="orange", linestyle="--", label="20-gene threshold")
    axes[0].set_xlabel("Distance to nearest prophage marker (genes)")
    axes[0].set_ylabel("Count of AMR gene instances")
    axes[0].set_title("A. Distance Distribution (capped at 200)")
    axes[0].legend()

    sorted_vals = np.sort(vals.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    mask = sorted_vals <= 200
    axes[1].plot(sorted_vals[mask], cdf[mask], color="steelblue", linewidth=2)
    axes[1].axhline(0.5, color="gray", linestyle=":", alpha=0.5)
    for t, c in [(5, "green"), (10, "red"), (20, "orange")]:
        frac = (vals <= t).mean()
        axes[1].axvline(t, color=c, linestyle="--", alpha=0.7, label=f"<={t}: {frac:.1%}")
    axes[1].set_xlabel("Distance to nearest prophage marker (genes)")
    axes[1].set_ylabel("Cumulative fraction")
    axes[1].set_title("B. Cumulative Distribution")
    axes[1].legend(fontsize=9)

plt.suptitle("NB02: AMR-Prophage Gene Neighborhood Distances", fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(FIG, "nb02_distance_distribution.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved figures/nb02_distance_distribution.png")

# Per-species proximal fraction
fig, ax = plt.subplots(figsize=(10, 6))
species_prox = []
for sp, grp in dist_df.groupby("species_id"):
    n_total = len(grp)
    has = grp[grp["contig_has_prophage"] == True]
    n_prox_10 = (has["nearest_prophage_distance"] <= 10).sum()
    species_prox.append({
        "species_id": sp,
        "n_amr_total": n_total,
        "n_proximal_10": n_prox_10,
        "pct_proximal_10": 100 * n_prox_10 / max(n_total, 1),
    })

sp_df = pd.DataFrame(species_prox).sort_values("pct_proximal_10", ascending=False)
ax.bar(range(len(sp_df)), sp_df["pct_proximal_10"], color="steelblue", width=1.0)
ax.set_xlabel("Species (ranked)")
ax.set_ylabel("% AMR genes within 10 genes of prophage")
ax.set_title("Fraction of AMR Genes Proximal to Prophage (<=10 genes), by Species")
median_pct = sp_df["pct_proximal_10"].median()
ax.axhline(median_pct, color="red", linestyle="--", label=f"Median: {median_pct:.1f}%")
ax.legend()
plt.tight_layout()
fig.savefig(os.path.join(FIG, "nb02_proximal_fraction.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved figures/nb02_proximal_fraction.png")

print("\nNB02 complete. Proceed to NB03 for conservation test (H1).")
