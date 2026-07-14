"""NB26f — PSII-only gene-neighborhood, leaner Spark pipeline.

Restructure of NB26e to combat Spark Connect contention:
  - Stage 1 written explicitly with .persist() + checkpoint via MinIO write
  - Each stage prints time elapsed
  - Smaller scope (PSII only) — 25 KOs × 309 species
  - Uses earlier ko_genus_mge to confirm focal_kos×focal_species exist before query

If this completes successfully, NB26g/h will run PUL and mycolic in series.
"""
import os, json, time
from pathlib import Path
import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
MINIO_BASE = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data"
NEIGHBOR_BP = 5000
HYP_ID = "psii"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint(f"=== NB26f — {HYP_ID} gene-neighborhood pipeline ===")

spark = get_spark_session()

# Sanity check — quick query before doing heavy work
tprint("Sanity: spark.range(10).count()")
n = spark.range(10).count()
tprint(f"  result: {n}")

species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

PSII_KOS = sorted({f"K{n:05d}" for n in range(2703, 2728)})
focal_kos = PSII_KOS
focal_species = list(species[species["class"] == "c__Cyanobacteriia"]["gtdb_species_clade_id"])
tprint(f"focal KOs: {len(focal_kos)}, focal species: {len(focal_species)}")

MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
mge_regex = "|".join(MGE_KEYWORDS)

# === Stage 1: focal gene_clusters (write to MinIO so we can checkpoint) ===
tprint("Stage 1: focal gene_clusters (filter+join, write to MinIO)")
focal_kos_sdf = spark.createDataFrame(pd.DataFrame({"focal_ko": focal_kos}))
focal_species_sdf = spark.createDataFrame(pd.DataFrame({"gtdb_species_clade_id": focal_species}))

bakta = (spark.table("kbase_ke_pangenome.bakta_annotations")
    .filter(F.col("kegg_orthology_id").isNotNull() & (F.col("kegg_orthology_id") != ""))
    .withColumn("ko", F.split(F.col("kegg_orthology_id"), ",").getItem(0))
    .select("gene_cluster_id", "ko"))
bakta_focal = bakta.join(F.broadcast(focal_kos_sdf), bakta["ko"] == focal_kos_sdf["focal_ko"], "inner").drop("focal_ko")
gc = spark.table("kbase_ke_pangenome.gene_cluster").select("gene_cluster_id", "gtdb_species_clade_id")
gc_focal = gc.join(F.broadcast(focal_species_sdf), "gtdb_species_clade_id", "inner")
focal_clusters = bakta_focal.join(gc_focal, "gene_cluster_id", "inner")

stage1_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage1_focal_clusters.parquet"
focal_clusters.coalesce(2).write.mode("overwrite").parquet(stage1_path)
tprint(f"  Stage 1 wrote to {stage1_path}")
focal_clusters_pd = spark.read.parquet(stage1_path).toPandas()
focal_clusters_pd = pd.DataFrame({c: focal_clusters_pd[c].values for c in focal_clusters_pd.columns})
tprint(f"  Stage 1 read back: {len(focal_clusters_pd):,} (gene_cluster_id, ko, species) rows")
focal_cluster_ids = focal_clusters_pd["gene_cluster_id"].unique().tolist()
tprint(f"  distinct cluster_ids: {len(focal_cluster_ids):,}")

# === Stage 2: constituent genes ===
tprint("Stage 2: constituent genes (gene_genecluster_junction × pangenome.gene)")
cluster_id_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": focal_cluster_ids}))
gj = spark.table("kbase_ke_pangenome.gene_genecluster_junction")
g = spark.table("kbase_ke_pangenome.gene")
focal_genes = (gj.join(F.broadcast(cluster_id_sdf), "gene_cluster_id", "inner")
                .join(g, "gene_id", "inner"))

stage2_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage2_genes.parquet"
focal_genes.coalesce(4).write.mode("overwrite").parquet(stage2_path)
tprint(f"  Stage 2 wrote to {stage2_path}")
focal_genes_pd = spark.read.parquet(stage2_path).toPandas()
focal_genes_pd = pd.DataFrame({c: focal_genes_pd[c].values for c in focal_genes_pd.columns})
tprint(f"  Stage 2 read back: {len(focal_genes_pd):,} (gene_id, gene_cluster_id, genome_id) rows")
focal_gene_ids = focal_genes_pd["gene_id"].unique().tolist()
tprint(f"  distinct gene_ids: {len(focal_gene_ids):,}")

# Add KO + species back via merge
focal_genes_pd = focal_genes_pd.merge(focal_clusters_pd, on="gene_cluster_id", how="inner")

# === Stage 3: cross-walk to feature_id ===
tprint("Stage 3: name-table cross-walk")
gene_id_sdf = spark.createDataFrame(pd.DataFrame({"name": focal_gene_ids}))
name_t = spark.table("kbase_genomes.name")
name_match = (name_t.join(F.broadcast(gene_id_sdf), "name", "inner")
              .select("name", "entity_id"))
stage3_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage3_name.parquet"
name_match.coalesce(4).write.mode("overwrite").parquet(stage3_path)
tprint(f"  Stage 3 wrote to {stage3_path}")
name_pd = spark.read.parquet(stage3_path).toPandas()
name_pd = pd.DataFrame({c: name_pd[c].values for c in name_pd.columns})
tprint(f"  Stage 3 read back: {len(name_pd):,} (name → entity_id)")
focal_genes_pd = focal_genes_pd.merge(
    name_pd.rename(columns={"name": "gene_id", "entity_id": "feature_id"}),
    on="gene_id", how="left")

# === Stage 4: feature positions ===
tprint("Stage 4: feature positions")
feat_ids = focal_genes_pd["feature_id"].dropna().unique().tolist()
tprint(f"  distinct feature_ids: {len(feat_ids):,}")
fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": feat_ids}))
feat = spark.table("kbase_genomes.feature")
cxf = spark.table("kbase_genomes.contig_x_feature")

# Two-step: filter feat and cxf independently with broadcast, write each to MinIO
feat_filt = (feat.join(F.broadcast(fid_sdf), "feature_id", "inner")
              .filter(F.col("type") == "CDS")
              .select("feature_id", F.col("start").cast("long").alias("start_int"),
                      F.col("end").cast("long").alias("end_int"), "strand"))
stage4a_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage4a_feat.parquet"
feat_filt.coalesce(4).write.mode("overwrite").parquet(stage4a_path)
tprint(f"  Stage 4a wrote feat positions to {stage4a_path}")
feat_pos_pd = spark.read.parquet(stage4a_path).toPandas()
feat_pos_pd = pd.DataFrame({c: feat_pos_pd[c].values for c in feat_pos_pd.columns})
tprint(f"  Stage 4a read back: {len(feat_pos_pd):,}")

cxf_filt = cxf.join(F.broadcast(fid_sdf), "feature_id", "inner").select("feature_id", "contig_id")
stage4b_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage4b_cxf.parquet"
cxf_filt.coalesce(4).write.mode("overwrite").parquet(stage4b_path)
tprint(f"  Stage 4b wrote cxf to {stage4b_path}")
cxf_pd = spark.read.parquet(stage4b_path).toPandas()
cxf_pd = pd.DataFrame({c: cxf_pd[c].values for c in cxf_pd.columns})
tprint(f"  Stage 4b read back: {len(cxf_pd):,}")

focal_features = focal_genes_pd.merge(feat_pos_pd, on="feature_id", how="inner").merge(cxf_pd, on="feature_id", how="inner")
tprint(f"  focal features assembled: {len(focal_features):,}")
focal_features_path = DATA_DIR / f"p4d2_neighborhood_{HYP_ID}_focal_features.parquet"
pd.DataFrame({c: focal_features[c].values for c in focal_features.columns}).to_parquet(focal_features_path, index=False)

# === Stage 5: pull all CDS features on focal contigs ===
tprint(f"Stage 5: ±{NEIGHBOR_BP}bp neighbor features on focal contigs")
focal_contigs = focal_features["contig_id"].unique().tolist()
tprint(f"  distinct focal contigs: {len(focal_contigs):,}")
contig_sdf = spark.createDataFrame(pd.DataFrame({"contig_id": focal_contigs}))

cxf_on_contigs = cxf.join(F.broadcast(contig_sdf), "contig_id", "inner").select("feature_id", "contig_id")
stage5a_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage5a_cxf_contigs.parquet"
cxf_on_contigs.coalesce(4).write.mode("overwrite").parquet(stage5a_path)
tprint(f"  Stage 5a wrote to {stage5a_path}")
cxf_on_contigs_pd = spark.read.parquet(stage5a_path).toPandas()
cxf_on_contigs_pd = pd.DataFrame({c: cxf_on_contigs_pd[c].values for c in cxf_on_contigs_pd.columns})
tprint(f"  Stage 5a read back: {len(cxf_on_contigs_pd):,} (feature_id, contig_id) on focal contigs")

cf_fids = cxf_on_contigs_pd["feature_id"].unique().tolist()
cf_fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": cf_fids}))
cf_filt = (feat.join(F.broadcast(cf_fid_sdf), "feature_id", "inner")
            .filter(F.col("type") == "CDS")
            .select("feature_id", F.col("start").cast("long").alias("nb_start"),
                    F.col("end").cast("long").alias("nb_end"), "strand"))
stage5b_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage5b_cf.parquet"
cf_filt.coalesce(4).write.mode("overwrite").parquet(stage5b_path)
tprint(f"  Stage 5b wrote to {stage5b_path}")
cf_pd = spark.read.parquet(stage5b_path).toPandas()
cf_pd = pd.DataFrame({c: cf_pd[c].values for c in cf_pd.columns})
tprint(f"  Stage 5b read back: {len(cf_pd):,}")

contig_features_pd = cxf_on_contigs_pd.merge(cf_pd, on="feature_id", how="inner")
tprint(f"  all CDS on focal contigs: {len(contig_features_pd):,}")

# === Stage 6: neighborhood join in pandas ===
tprint(f"Stage 6: neighborhood join in pandas")
nbr_rows = []
cf_by_contig = contig_features_pd.groupby("contig_id")
for _, row in focal_features.iterrows():
    contig_id = row["contig_id"]; focal_start = row["start_int"]; focal_fid = row["feature_id"]
    try: cf_sub = cf_by_contig.get_group(contig_id)
    except KeyError: continue
    in_window = cf_sub[
        (cf_sub["nb_start"] >= focal_start - NEIGHBOR_BP) &
        (cf_sub["nb_end"] <= focal_start + NEIGHBOR_BP) &
        (cf_sub["feature_id"] != focal_fid)]
    for _, nbr in in_window.iterrows():
        nbr_rows.append({
            "focal_feature_id": focal_fid, "focal_gene_id": row["gene_id"],
            "focal_cluster_id": row["gene_cluster_id"], "focal_ko": row["ko"],
            "focal_species": row["gtdb_species_clade_id"],
            "neighbor_feature_id": nbr["feature_id"],
            "distance_bp": int(min(abs(nbr["nb_start"] - focal_start), abs(nbr["nb_end"] - focal_start)))})
nbr_df = pd.DataFrame(nbr_rows)
tprint(f"  total neighbor pairs: {len(nbr_df):,}")

# === Stage 7: neighbor → cluster → bakta MGE flag ===
tprint("Stage 7: neighbor feature → gene_cluster → bakta MGE")
nbr_fids = nbr_df["neighbor_feature_id"].unique().tolist()
nbr_fid_sdf = spark.createDataFrame(pd.DataFrame({"entity_id": nbr_fids}))
nbr_name = (name_t.join(F.broadcast(nbr_fid_sdf), "entity_id", "inner")
              .select("entity_id", F.col("name").alias("gene_id")))
stage7a_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage7a_nbrname.parquet"
nbr_name.coalesce(4).write.mode("overwrite").parquet(stage7a_path)
tprint(f"  Stage 7a wrote to {stage7a_path}")
nbr_name_pd = spark.read.parquet(stage7a_path).toPandas()
nbr_name_pd = pd.DataFrame({c: nbr_name_pd[c].values for c in nbr_name_pd.columns})
tprint(f"  Stage 7a read back: {len(nbr_name_pd):,}")

nbr_genes = nbr_name_pd["gene_id"].unique().tolist()
nbr_genes_sdf = spark.createDataFrame(pd.DataFrame({"gene_id": nbr_genes}))
nbr_to_cluster = (gj.join(F.broadcast(nbr_genes_sdf), "gene_id", "inner")
                   .select("gene_id", "gene_cluster_id"))
stage7b_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage7b_nbrcluster.parquet"
nbr_to_cluster.coalesce(4).write.mode("overwrite").parquet(stage7b_path)
tprint(f"  Stage 7b wrote to {stage7b_path}")
nbr_cluster_pd = spark.read.parquet(stage7b_path).toPandas()
nbr_cluster_pd = pd.DataFrame({c: nbr_cluster_pd[c].values for c in nbr_cluster_pd.columns})
tprint(f"  Stage 7b read back: {len(nbr_cluster_pd):,}")

nbr_cluster_ids = nbr_cluster_pd["gene_cluster_id"].unique().tolist()
nbr_cluster_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": nbr_cluster_ids}))
bakta_full = spark.table("kbase_ke_pangenome.bakta_annotations").select("gene_cluster_id", "product")
nbr_products = (bakta_full.join(F.broadcast(nbr_cluster_sdf), "gene_cluster_id", "inner")
                  .withColumn("is_mge",
                      F.when(F.col("product").isNotNull() & F.lower(F.col("product")).rlike(mge_regex), 1).otherwise(0))
                  .select("gene_cluster_id", "is_mge"))
stage7c_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage7c_nbrmge.parquet"
nbr_products.coalesce(4).write.mode("overwrite").parquet(stage7c_path)
tprint(f"  Stage 7c wrote to {stage7c_path}")
nbr_mge_pd = spark.read.parquet(stage7c_path).toPandas()
nbr_mge_pd = pd.DataFrame({c: nbr_mge_pd[c].values for c in nbr_mge_pd.columns})
tprint(f"  Stage 7c read back: {len(nbr_mge_pd):,}")

# === Stage 8: aggregate ===
tprint("Stage 8: aggregate")
nbr_full = (nbr_df
    .merge(nbr_name_pd.rename(columns={"entity_id": "neighbor_feature_id"}), on="neighbor_feature_id", how="left")
    .merge(nbr_cluster_pd.rename(columns={"gene_cluster_id": "neighbor_cluster_id"}), on="gene_id", how="left")
    .merge(nbr_mge_pd.rename(columns={"gene_cluster_id": "neighbor_cluster_id"}).drop_duplicates("neighbor_cluster_id"),
           on="neighbor_cluster_id", how="left"))
nbr_full["is_mge"] = nbr_full["is_mge"].fillna(0)
tprint(f"  total tagged: {len(nbr_full):,}, MGE neighbors: {int(nbr_full['is_mge'].sum()):,}")

per_feature = (nbr_full.groupby(["focal_feature_id", "focal_cluster_id", "focal_ko", "focal_species"])
    .agg(n_neighbors=("neighbor_feature_id", "count"),
         n_mge_neighbors=("is_mge", "sum"))
    .reset_index())
per_feature["mge_neighbor_fraction"] = per_feature["n_mge_neighbors"] / per_feature["n_neighbors"]
per_feature["any_mge_neighbor"] = (per_feature["n_mge_neighbors"] > 0).astype(int)
tprint(f"  per-focal-feature: {len(per_feature):,}")
tprint(f"  mean fraction MGE neighbors: {per_feature['mge_neighbor_fraction'].mean():.4f}")
tprint(f"  fraction with ≥1 MGE neighbor: {per_feature['any_mge_neighbor'].mean()*100:.2f}%")

out_path = DATA_DIR / f"p4d2_neighborhood_{HYP_ID}_per_feature.parquet"
pd.DataFrame({c: per_feature[c].values for c in per_feature.columns}).to_parquet(out_path, index=False)
tprint(f"  saved {out_path}")

per_ko_sp = (per_feature.groupby(["focal_ko", "focal_species"])
    .agg(n_features=("focal_feature_id", "count"),
         mean_mge_neighbor_fraction=("mge_neighbor_fraction", "mean"),
         pct_with_any_mge_neighbor=("any_mge_neighbor", "mean"))
    .reset_index())
per_ko_sp["pct_with_any_mge_neighbor"] *= 100

print(f"\nTop 10 (KO × species) by % with any MGE neighbor:", flush=True)
print(per_ko_sp.sort_values("pct_with_any_mge_neighbor", ascending=False).head(10).to_string(index=False), flush=True)

diag = {
    "phase": "4", "deliverable": "P4-D2 neighborhood — PSII",
    "hypothesis": "Cyanobacteriia × PSII",
    "neighbor_window_bp": NEIGHBOR_BP,
    "n_focal_clusters": int(len(focal_cluster_ids)),
    "n_focal_features": int(len(per_feature)),
    "n_neighbor_pairs": int(len(nbr_full)),
    "atlas_mge_neighbor_fraction": float(per_feature["mge_neighbor_fraction"].mean()),
    "pct_features_with_any_mge_neighbor": float(per_feature["any_mge_neighbor"].mean()*100),
    "top_ko_species": per_ko_sp.sort_values("pct_with_any_mge_neighbor", ascending=False).head(20).to_dict(orient="records"),
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / f"p4d2_neighborhood_{HYP_ID}_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"=== DONE ===")
