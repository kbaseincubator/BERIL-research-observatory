"""NB26g — resume PSII pipeline from MinIO checkpoints, vectorized Stage 6+.

NB26f's Stage 6 (pandas iterrows neighborhood join over 27K × 2.2M) was too slow.
Resume from saved MinIO outputs and use vectorized merge instead.
"""
import json, time
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

tprint(f"=== NB26g — resume {HYP_ID} from checkpoints, vectorized Stage 6+ ===")
spark = get_spark_session()

# === Load saved stages from MinIO + local ===
tprint("Loading stage 1-5 outputs from MinIO + local")

focal_features_pd = pd.read_parquet(DATA_DIR / f"p4d2_neighborhood_{HYP_ID}_focal_features.parquet")
focal_features = pd.DataFrame({c: focal_features_pd[c].values for c in focal_features_pd.columns})
tprint(f"  focal_features (local): {len(focal_features):,}")

# Stage 5 contig features
cxf_on_contigs_spark = spark.read.parquet(f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage5a_cxf_contigs.parquet").toPandas()
cxf_on_contigs_pd = pd.DataFrame({c: cxf_on_contigs_spark[c].values for c in cxf_on_contigs_spark.columns})
tprint(f"  cxf_on_contigs: {len(cxf_on_contigs_pd):,}")

cf_spark = spark.read.parquet(f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage5b_cf.parquet").toPandas()
cf_pd = pd.DataFrame({c: cf_spark[c].values for c in cf_spark.columns})
tprint(f"  cf positions: {len(cf_pd):,}")

contig_features_pd = cxf_on_contigs_pd.merge(cf_pd, on="feature_id", how="inner")
tprint(f"  all CDS on focal contigs: {len(contig_features_pd):,}")

# === Stage 6 vectorized: merge by contig, filter by distance ===
tprint("Stage 6 (vectorized): merge focal × contig_features by contig_id, filter ±5kb")
tprint(f"  focal_features columns: {focal_features.columns.tolist()}")
focal_min = focal_features[["feature_id", "gene_id", "gene_cluster_id", "ko",
                             "gtdb_species_clade_id", "contig_id", "start_int"]].rename(columns={
    "feature_id": "focal_feature_id", "gene_id": "focal_gene_id",
    "gene_cluster_id": "focal_cluster_id", "ko": "focal_ko",
    "gtdb_species_clade_id": "focal_species", "start_int": "focal_start"})
tprint(f"  focal_min cols: {focal_min.columns.tolist()}")

merged = focal_min.merge(contig_features_pd, on="contig_id", how="inner")
tprint(f"  merged size: {len(merged):,}")
in_window = merged[
    (merged["nb_start"] >= merged["focal_start"] - NEIGHBOR_BP) &
    (merged["nb_end"] <= merged["focal_start"] + NEIGHBOR_BP) &
    (merged["feature_id"] != merged["focal_feature_id"])
].copy()
in_window["distance_bp"] = np.minimum(
    (in_window["nb_start"] - in_window["focal_start"]).abs(),
    (in_window["nb_end"] - in_window["focal_start"]).abs()).astype(int)
nbr_df = in_window[["focal_feature_id", "focal_gene_id", "focal_cluster_id", "focal_ko",
                     "focal_species", "feature_id", "distance_bp"]].rename(columns={"feature_id": "neighbor_feature_id"})
tprint(f"  total neighbor pairs: {len(nbr_df):,}")

# === Stage 7: cross-walk neighbor feature_id back to gene_cluster_id and bakta MGE ===
MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
mge_regex = "|".join(MGE_KEYWORDS)

tprint("Stage 7a: name table cross-walk for neighbor feature_ids")
nbr_fids = nbr_df["neighbor_feature_id"].unique().tolist()
tprint(f"  distinct neighbor feature_ids: {len(nbr_fids):,}")
nbr_fid_sdf = spark.createDataFrame(pd.DataFrame({"entity_id": nbr_fids}))
name_t = spark.table("kbase_genomes.name")
nbr_name = (name_t.join(F.broadcast(nbr_fid_sdf), "entity_id", "inner")
              .select("entity_id", F.col("name").alias("gene_id")))
stage7a_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage7a_nbrname.parquet"
nbr_name.coalesce(4).write.mode("overwrite").parquet(stage7a_path)
nbr_name_spark = spark.read.parquet(stage7a_path).toPandas()
nbr_name_pd = pd.DataFrame({c: nbr_name_spark[c].values for c in nbr_name_spark.columns})
tprint(f"  Stage 7a: {len(nbr_name_pd):,}")

tprint("Stage 7b: gene_id → gene_cluster_id")
nbr_genes = nbr_name_pd["gene_id"].unique().tolist()
nbr_genes_sdf = spark.createDataFrame(pd.DataFrame({"gene_id": nbr_genes}))
gj = spark.table("kbase_ke_pangenome.gene_genecluster_junction")
nbr_to_cluster = (gj.join(F.broadcast(nbr_genes_sdf), "gene_id", "inner")
                   .select("gene_id", "gene_cluster_id"))
stage7b_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage7b_nbrcluster.parquet"
nbr_to_cluster.coalesce(4).write.mode("overwrite").parquet(stage7b_path)
nbr_cluster_spark = spark.read.parquet(stage7b_path).toPandas()
nbr_cluster_pd = pd.DataFrame({c: nbr_cluster_spark[c].values for c in nbr_cluster_spark.columns})
tprint(f"  Stage 7b: {len(nbr_cluster_pd):,}")

tprint("Stage 7c: gene_cluster → bakta product → MGE flag")
nbr_cluster_ids = nbr_cluster_pd["gene_cluster_id"].unique().tolist()
nbr_cluster_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": nbr_cluster_ids}))
bakta_full = spark.table("kbase_ke_pangenome.bakta_annotations").select("gene_cluster_id", "product")
nbr_products = (bakta_full.join(F.broadcast(nbr_cluster_sdf), "gene_cluster_id", "inner")
                  .withColumn("is_mge",
                      F.when(F.col("product").isNotNull() & F.lower(F.col("product")).rlike(mge_regex), 1).otherwise(0))
                  .select("gene_cluster_id", "is_mge"))
stage7c_path = f"{MINIO_BASE}/p4d2_nbh_{HYP_ID}_stage7c_nbrmge.parquet"
nbr_products.coalesce(4).write.mode("overwrite").parquet(stage7c_path)
nbr_mge_spark = spark.read.parquet(stage7c_path).toPandas()
nbr_mge_pd = pd.DataFrame({c: nbr_mge_spark[c].values for c in nbr_mge_spark.columns})
nbr_mge_pd = nbr_mge_pd.drop_duplicates("gene_cluster_id")
tprint(f"  Stage 7c: {len(nbr_mge_pd):,}")

# === Stage 8: aggregate ===
tprint("Stage 8: aggregate")
nbr_full = (nbr_df
    .merge(nbr_name_pd.rename(columns={"entity_id": "neighbor_feature_id"}), on="neighbor_feature_id", how="left")
    .merge(nbr_cluster_pd.rename(columns={"gene_cluster_id": "neighbor_cluster_id"}), on="gene_id", how="left")
    .merge(nbr_mge_pd.rename(columns={"gene_cluster_id": "neighbor_cluster_id"}), on="neighbor_cluster_id", how="left"))
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

print(f"\nTop 15 (KO × species) by % with any MGE neighbor:", flush=True)
print(per_ko_sp.sort_values("pct_with_any_mge_neighbor", ascending=False).head(15).to_string(index=False), flush=True)

print(f"\nPer-KO summary:", flush=True)
ko_summary = (per_feature.groupby("focal_ko")
    .agg(n_features=("focal_feature_id", "count"),
         mean_mge_neighbor_fraction=("mge_neighbor_fraction", "mean"),
         pct_with_any_mge_neighbor=("any_mge_neighbor", lambda v: v.mean()*100))
    .reset_index())
print(ko_summary.sort_values("pct_with_any_mge_neighbor", ascending=False).to_string(index=False), flush=True)

diag = {
    "phase": "4", "deliverable": "P4-D2 neighborhood — PSII",
    "hypothesis": "Cyanobacteriia × PSII",
    "neighbor_window_bp": NEIGHBOR_BP,
    "n_focal_features": int(len(per_feature)),
    "n_neighbor_pairs": int(len(nbr_full)),
    "atlas_mge_neighbor_fraction": float(per_feature["mge_neighbor_fraction"].mean()),
    "pct_features_with_any_mge_neighbor": float(per_feature["any_mge_neighbor"].mean()*100),
    "per_ko_summary": ko_summary.to_dict(orient="records"),
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / f"p4d2_neighborhood_{HYP_ID}_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"=== DONE in {time.time()-t0:.1f}s ===")
