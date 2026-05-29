"""
NB01: AMR and Prophage Marker Census
=====================================
Requires BERDL JupyterHub (Spark access).

Build the complete inventory of AMR genes and prophage markers across
the BERDL pangenome (293K genomes, 27K species). Identify prophage markers
via bakta_annotations product keywords + bakta_pfam_domains, since
genomad_mobile_elements is not ingested in BERDL.

Outputs:
  data/amr_clusters.csv           — all AMR gene clusters with species + core/acc
  data/prophage_marker_clusters.csv — all prophage marker clusters
  data/amr_prophage_species_summary.csv — per-species counts
  data/census_summary.json        — top-level statistics
  figures/nb01_amr_prophage_phylum_distribution.png
  figures/nb01_census_overview.png
"""

import json
import os
import sys
import warnings

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
    spark = get_spark_session()                       # JupyterHub notebook kernel
except NameError:
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()                   # JupyterHub CLI
    except ImportError:
        from get_spark_session import get_spark_session
        spark = get_spark_session()                   # local w/ proxy

print("Spark session ready.")

_script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
PROJECT = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "notebooks" else _script_dir
# Fallback: if running from repo root, use explicit path
if not os.path.isdir(os.path.join(PROJECT, "data")) and not os.path.isdir(os.path.join(PROJECT, "figures")):
    PROJECT = os.path.join(os.getcwd(), "projects", "prophage_amr_comobilization")
DATA    = os.path.join(PROJECT, "data")
FIG     = os.path.join(PROJECT, "figures")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

# ===================================================================
# 1. AMR gene census  (bakta_amr — 83K rows, safe to full-scan)
# ===================================================================
print("\n=== 1. AMR Gene Census ===")

amr_df = spark.sql("""
    SELECT
        a.gene_cluster_id,
        a.amr_gene,
        a.amr_product,
        a.method,
        a.identity,
        a.query_cov,
        a.subject_cov,
        a.accession AS amr_accession
    FROM kbase_ke_pangenome.bakta_amr a
""")

amr_count = amr_df.count()
print(f"Total AMR gene cluster entries: {amr_count:,}")

# Map to species + core/accessory via gene_cluster
amr_with_species = spark.sql("""
    SELECT
        a.gene_cluster_id,
        a.amr_gene,
        a.amr_product,
        a.method,
        a.identity,
        gc.gtdb_species_clade_id AS species_id,
        gc.is_core,
        gc.is_auxiliary,
        gc.is_singleton
    FROM kbase_ke_pangenome.bakta_amr a
    JOIN kbase_ke_pangenome.gene_cluster gc
        ON a.gene_cluster_id = gc.gene_cluster_id
""")

amr_pd = amr_with_species.toPandas()
print(f"AMR clusters mapped to species: {len(amr_pd):,}")
print(f"Unique AMR gene names: {amr_pd['amr_gene'].nunique():,}")
print(f"Species with AMR genes: {amr_pd['species_id'].nunique():,}")

# Conservation breakdown
for label, col in [("Core", "is_core"), ("Accessory", "is_auxiliary"), ("Singleton", "is_singleton")]:
    n = int((amr_pd[col] == True).sum())
    pct = 100.0 * n / len(amr_pd) if len(amr_pd) > 0 else 0
    print(f"  {label}: {n:,} ({pct:.1f}%)")

amr_pd.to_csv(os.path.join(DATA, "amr_clusters.csv"), index=False)
print(f"Saved data/amr_clusters.csv")

# ===================================================================
# 2. Prophage marker census — keyword approach
# ===================================================================
print("\n=== 2. Prophage Marker Census (keyword) ===")

# Keywords validated in gene_function_ecological_agora NB26
PROPHAGE_KEYWORDS = [
    "phage", "prophage", "terminase", "integrase", "holin",
    "endolysin", "phage_portal", "phage_tail", "phage_capsid",
    "excisionase", "baseplate", "tail_fiber", "tail_spike",
    "head_morphogenesis", "phage_lysin", "lysozyme",
    "recombinase", "transposase",
]

# Build RLIKE pattern
keyword_pattern = "|".join(PROPHAGE_KEYWORDS)

prophage_kw_df = spark.sql(f"""
    SELECT
        ba.gene_cluster_id,
        ba.product,
        ba.gene AS gene_name
    FROM kbase_ke_pangenome.bakta_annotations ba
    WHERE LOWER(ba.product) RLIKE '{keyword_pattern}'
""")

prophage_kw_count = prophage_kw_df.count()
print(f"Prophage-keyword gene clusters (bakta_annotations): {prophage_kw_count:,}")

# Deduplicate to unique gene_cluster_ids with a label
prophage_kw_ids = prophage_kw_df.select("gene_cluster_id").distinct()
prophage_kw_id_count = prophage_kw_ids.count()
print(f"Unique prophage-keyword gene cluster IDs: {prophage_kw_id_count:,}")

# ===================================================================
# 3. Prophage marker census — Pfam domain approach
# ===================================================================
print("\n=== 3. Prophage Marker Census (Pfam domains) ===")

PHAGE_PFAMS = [
    "Terminase_1", "Terminase_GpA", "Terminase_3", "Terminase_6",
    "Phage_portal", "HK97", "Phage_cap_E",
    "Phage_tail_S", "Phage_sheath", "Phage_fiber",
    "Phage_holin", "Phage_lysozyme",
    "Phage_integrase", "Phage_int_SAM_5",
    "Phage_CI_repr",
]

pfam_pattern = "|".join(PHAGE_PFAMS)

prophage_pfam_df = spark.sql(f"""
    SELECT DISTINCT gene_cluster_id
    FROM kbase_ke_pangenome.bakta_pfam_domains
    WHERE pfam_name RLIKE '{pfam_pattern}'
""")

prophage_pfam_count = prophage_pfam_df.count()
print(f"Unique prophage-Pfam gene cluster IDs: {prophage_pfam_count:,}")

# ===================================================================
# 4. Merge prophage markers (union, deduplicate)
# ===================================================================
print("\n=== 4. Merge Prophage Markers ===")

# Union both sources
all_prophage_ids = prophage_kw_ids.union(prophage_pfam_df).distinct()
total_prophage = all_prophage_ids.count()
print(f"Total unique prophage marker gene clusters (keyword + Pfam): {total_prophage:,}")

# Overlap
overlap_df = prophage_kw_ids.intersect(prophage_pfam_df)
overlap_count = overlap_df.count()
print(f"Overlap (both keyword + Pfam): {overlap_count:,}")
print(f"Keyword-only: {prophage_kw_id_count - overlap_count:,}")
print(f"Pfam-only: {prophage_pfam_count - overlap_count:,}")

# Map to species + core/accessory
all_prophage_ids.createOrReplaceTempView("prophage_ids")

prophage_with_species = spark.sql("""
    SELECT
        p.gene_cluster_id,
        gc.gtdb_species_clade_id AS species_id,
        gc.is_core,
        gc.is_auxiliary,
        gc.is_singleton
    FROM prophage_ids p
    JOIN kbase_ke_pangenome.gene_cluster gc
        ON p.gene_cluster_id = gc.gene_cluster_id
""")

prophage_pd = prophage_with_species.toPandas()
print(f"\nProphage markers mapped to species: {len(prophage_pd):,}")
print(f"Species with prophage markers: {prophage_pd['species_id'].nunique():,}")

for label, col in [("Core", "is_core"), ("Accessory", "is_auxiliary"), ("Singleton", "is_singleton")]:
    n = prophage_pd[col].sum()
    pct = 100.0 * n / len(prophage_pd) if len(prophage_pd) > 0 else 0
    print(f"  {label}: {n:,} ({pct:.1f}%)")

prophage_pd.to_csv(os.path.join(DATA, "prophage_marker_clusters.csv"), index=False)
print(f"Saved data/prophage_marker_clusters.csv")

# ===================================================================
# 5. Species-level summary
# ===================================================================
print("\n=== 5. Species-Level Summary ===")

# AMR counts per species
amr_species = amr_pd.groupby("species_id").agg(
    n_amr_clusters=("gene_cluster_id", "nunique"),
    n_amr_core=("is_core", lambda x: (x == True).sum()),
    n_amr_accessory=("is_auxiliary", lambda x: (x == True).sum()),
    n_amr_singleton=("is_singleton", lambda x: (x == True).sum()),
    unique_amr_genes=("amr_gene", "nunique"),
).reset_index()

# Prophage counts per species
prophage_species = prophage_pd.groupby("species_id").agg(
    n_prophage_clusters=("gene_cluster_id", "nunique"),
    n_prophage_core=("is_core", lambda x: (x == True).sum()),
    n_prophage_accessory=("is_auxiliary", lambda x: (x == True).sum()),
    n_prophage_singleton=("is_singleton", lambda x: (x == True).sum()),
).reset_index()

# Get pangenome stats (genome counts, total clusters)
pangenome_pd = spark.sql("""
    SELECT
        gtdb_species_clade_id AS species_id,
        no_genomes,
        no_gene_clusters,
        no_core,
        no_aux_genome,
        no_singleton_gene_clusters
    FROM kbase_ke_pangenome.pangenome
""").toPandas()

# Get taxonomy
taxonomy_pd = spark.sql("""
    SELECT DISTINCT
        g.gtdb_species_clade_id AS species_id,
        t.phylum, t.class, t.order, t.family, t.genus
    FROM kbase_ke_pangenome.genome g
    JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t
        ON g.genome_id = t.genome_id
""").toPandas()

# Merge everything
species_summary = pangenome_pd.merge(taxonomy_pd, on="species_id", how="left")
species_summary = species_summary.merge(amr_species, on="species_id", how="left")
species_summary = species_summary.merge(prophage_species, on="species_id", how="left")

# Fill NaN with 0 for species lacking AMR or prophage
fill_cols = [c for c in species_summary.columns if c.startswith("n_amr") or c.startswith("n_prophage") or c == "unique_amr_genes"]
species_summary[fill_cols] = species_summary[fill_cols].fillna(0).astype(int)

# Compute densities (per genome)
species_summary["amr_per_genome"] = species_summary["n_amr_clusters"] / species_summary["no_genomes"].clip(lower=1)
species_summary["prophage_per_genome"] = species_summary["n_prophage_clusters"] / species_summary["no_genomes"].clip(lower=1)

# Co-occurrence: species with BOTH AMR and prophage markers
both = species_summary[(species_summary["n_amr_clusters"] > 0) & (species_summary["n_prophage_clusters"] > 0)]
amr_only = species_summary[(species_summary["n_amr_clusters"] > 0) & (species_summary["n_prophage_clusters"] == 0)]
prophage_only = species_summary[(species_summary["n_amr_clusters"] == 0) & (species_summary["n_prophage_clusters"] > 0)]
neither = species_summary[(species_summary["n_amr_clusters"] == 0) & (species_summary["n_prophage_clusters"] == 0)]

print(f"Total species: {len(species_summary):,}")
print(f"Species with AMR genes: {len(amr_only) + len(both):,}")
print(f"Species with prophage markers: {len(prophage_only) + len(both):,}")
print(f"Species with BOTH: {len(both):,}")
print(f"Species with AMR only: {len(amr_only):,}")
print(f"Species with prophage only: {len(prophage_only):,}")
print(f"Species with neither: {len(neither):,}")

species_summary.to_csv(os.path.join(DATA, "amr_prophage_species_summary.csv"), index=False)
print(f"Saved data/amr_prophage_species_summary.csv")

# ===================================================================
# 6. Census summary JSON
# ===================================================================
def pct_true(series):
    """Percentage of True values, handling bool or numeric."""
    return float(100 * (series == True).sum() / len(series)) if len(series) > 0 else 0.0

census = {
    "amr": {
        "total_clusters": int(amr_count),
        "mapped_to_species": len(amr_pd),
        "unique_amr_genes": int(amr_pd["amr_gene"].nunique()),
        "species_count": int(amr_pd["species_id"].nunique()),
        "pct_core": pct_true(amr_pd["is_core"]),
        "pct_accessory": pct_true(amr_pd["is_auxiliary"]),
        "pct_singleton": pct_true(amr_pd["is_singleton"]),
    },
    "prophage": {
        "keyword_clusters": int(prophage_kw_id_count),
        "pfam_clusters": int(prophage_pfam_count),
        "overlap": int(overlap_count),
        "total_unique": int(total_prophage),
        "mapped_to_species": len(prophage_pd),
        "species_count": int(prophage_pd["species_id"].nunique()),
        "pct_core": pct_true(prophage_pd["is_core"]),
        "pct_accessory": pct_true(prophage_pd["is_auxiliary"]),
        "pct_singleton": pct_true(prophage_pd["is_singleton"]),
    },
    "co_occurrence": {
        "species_both": len(both),
        "species_amr_only": len(amr_only),
        "species_prophage_only": len(prophage_only),
        "species_neither": len(neither),
    },
}

with open(os.path.join(DATA, "census_summary.json"), "w") as f:
    json.dump(census, f, indent=2)
print(f"\nSaved data/census_summary.json")

# ===================================================================
# 7. Figures
# ===================================================================
print("\n=== 7. Generating Figures ===")

# --- Figure 1: Phylum distribution ---
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Clean phylum names
species_summary["phylum_clean"] = species_summary["phylum"].fillna("Unknown").str.replace("p__", "", regex=False)

# AMR by phylum (top 15)
amr_by_phylum = (
    species_summary[species_summary["n_amr_clusters"] > 0]
    .groupby("phylum_clean")["n_amr_clusters"]
    .sum()
    .sort_values(ascending=False)
    .head(15)
)
amr_by_phylum.plot(kind="barh", ax=axes[0], color="steelblue")
axes[0].set_xlabel("Total AMR gene clusters")
axes[0].set_title("AMR Gene Clusters by Phylum (top 15)")
axes[0].invert_yaxis()

# Prophage by phylum (top 15)
pro_by_phylum = (
    species_summary[species_summary["n_prophage_clusters"] > 0]
    .groupby("phylum_clean")["n_prophage_clusters"]
    .sum()
    .sort_values(ascending=False)
    .head(15)
)
pro_by_phylum.plot(kind="barh", ax=axes[1], color="coral")
axes[1].set_xlabel("Total prophage marker clusters")
axes[1].set_title("Prophage Marker Clusters by Phylum (top 15)")
axes[1].invert_yaxis()

plt.tight_layout()
fig.savefig(os.path.join(FIG, "nb01_amr_prophage_phylum_distribution.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved figures/nb01_amr_prophage_phylum_distribution.png")

# --- Figure 2: Census overview (4-panel) ---
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# Panel A: Core/Accessory/Singleton breakdown
categories = ["Core", "Accessory", "Singleton"]
amr_vals = [census["amr"]["pct_core"], census["amr"]["pct_accessory"], census["amr"]["pct_singleton"]]
pro_vals = [census["prophage"]["pct_core"], census["prophage"]["pct_accessory"], census["prophage"]["pct_singleton"]]

x = np.arange(len(categories))
w = 0.35
axes[0, 0].bar(x - w/2, amr_vals, w, label="AMR genes", color="steelblue")
axes[0, 0].bar(x + w/2, pro_vals, w, label="Prophage markers", color="coral")
axes[0, 0].set_xticks(x)
axes[0, 0].set_xticklabels(categories)
axes[0, 0].set_ylabel("Percentage (%)")
axes[0, 0].set_title("A. Core/Accessory/Singleton Status")
axes[0, 0].legend()

# Panel B: Species co-occurrence
co_labels = ["Both", "AMR only", "Prophage only", "Neither"]
co_vals = [
    census["co_occurrence"]["species_both"],
    census["co_occurrence"]["species_amr_only"],
    census["co_occurrence"]["species_prophage_only"],
    census["co_occurrence"]["species_neither"],
]
colors = ["mediumpurple", "steelblue", "coral", "lightgray"]
axes[0, 1].bar(co_labels, co_vals, color=colors)
axes[0, 1].set_ylabel("Number of species")
axes[0, 1].set_title("B. Species-Level Co-occurrence")
for i, v in enumerate(co_vals):
    axes[0, 1].text(i, v + max(co_vals)*0.01, f"{v:,}", ha="center", fontsize=9)

# Panel C: AMR density vs prophage density scatter
mask = (species_summary["n_amr_clusters"] > 0) | (species_summary["n_prophage_clusters"] > 0)
scatter_df = species_summary[mask].copy()
axes[1, 0].scatter(
    scatter_df["prophage_per_genome"],
    scatter_df["amr_per_genome"],
    alpha=0.15, s=8, c="black"
)
axes[1, 0].set_xlabel("Prophage markers per genome")
axes[1, 0].set_ylabel("AMR clusters per genome")
axes[1, 0].set_title("C. Prophage vs AMR Density (per species)")

# Panel D: Prophage detection method overlap
kw_only = prophage_kw_id_count - overlap_count
pfam_only = prophage_pfam_count - overlap_count
method_labels = ["Keyword only", "Pfam only", "Both"]
method_vals = [kw_only, pfam_only, overlap_count]
method_colors = ["lightsalmon", "lightblue", "mediumpurple"]
axes[1, 1].bar(method_labels, method_vals, color=method_colors)
axes[1, 1].set_ylabel("Gene clusters")
axes[1, 1].set_title("D. Prophage Detection Method Overlap")
for i, v in enumerate(method_vals):
    axes[1, 1].text(i, v + max(method_vals)*0.01, f"{v:,}", ha="center", fontsize=9)

plt.suptitle("NB01: AMR and Prophage Marker Census", fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
fig.savefig(os.path.join(FIG, "nb01_census_overview.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved figures/nb01_census_overview.png")

# ===================================================================
# 8. Print final summary
# ===================================================================
print("\n" + "=" * 60)
print("NB01 CENSUS SUMMARY")
print("=" * 60)
print(f"AMR gene clusters:       {census['amr']['mapped_to_species']:>10,}")
print(f"  Unique AMR gene names: {census['amr']['unique_amr_genes']:>10,}")
print(f"  Species with AMR:      {census['amr']['species_count']:>10,}")
print(f"  Core:                  {census['amr']['pct_core']:>9.1f}%")
print(f"  Accessory:             {census['amr']['pct_accessory']:>9.1f}%")
print(f"  Singleton:             {census['amr']['pct_singleton']:>9.1f}%")
print()
print(f"Prophage marker clusters:{census['prophage']['total_unique']:>10,}")
print(f"  Keyword method:        {census['prophage']['keyword_clusters']:>10,}")
print(f"  Pfam method:           {census['prophage']['pfam_clusters']:>10,}")
print(f"  Overlap:               {census['prophage']['overlap']:>10,}")
print(f"  Species with prophage: {census['prophage']['species_count']:>10,}")
print(f"  Core:                  {census['prophage']['pct_core']:>9.1f}%")
print(f"  Accessory:             {census['prophage']['pct_accessory']:>9.1f}%")
print(f"  Singleton:             {census['prophage']['pct_singleton']:>9.1f}%")
print()
print(f"Species with BOTH:       {census['co_occurrence']['species_both']:>10,}")
print(f"Species with AMR only:   {census['co_occurrence']['species_amr_only']:>10,}")
print(f"Species with prophage:   {census['co_occurrence']['species_prophage_only']:>10,}")
print(f"Species with neither:    {census['co_occurrence']['species_neither']:>10,}")
print("=" * 60)
print("\nNB01 complete. Proceed to NB02 for gene neighborhood co-localization.")
