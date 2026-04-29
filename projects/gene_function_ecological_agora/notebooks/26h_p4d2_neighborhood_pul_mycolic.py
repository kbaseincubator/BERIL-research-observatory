"""NB26h — gene-neighborhood pipeline for PUL + mycolic.

Same structure as NB26f/g but vectorized Stage 6 from start. Two hypotheses
in series with checkpoints to MinIO at each stage.
"""
import os, json, time, sys
from pathlib import Path
import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
MINIO_BASE = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data"
NEIGHBOR_BP = 5000

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB26h — PUL + mycolic neighborhood pipeline ===")
spark = get_spark_session()
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
mge_regex = "|".join(MGE_KEYWORDS)

# === Hypothesis definitions ===
MYCOLIC_PATHWAYS = {"ko00061", "ko00071", "ko01040", "ko00540"}
MYCOLIC_SPECIFIC_KOS = {"K11212", "K11211", "K11778", "K11533", "K11534",
                        "K00208", "K20274", "K11782", "K01205", "K00667", "K00507"}
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
def is_mycolic_ko(row):
    if row["ko"] in MYCOLIC_SPECIFIC_KOS: return True
    p = row.get("pathway_ids", "")
    if not isinstance(p, str): return False
    return bool(set(p.split(",")) & MYCOLIC_PATHWAYS)
ko_pwbr["is_mycolic"] = ko_pwbr.apply(is_mycolic_ko, axis=1)
mycolic_kos = sorted(set(ko_pwbr[ko_pwbr["is_mycolic"]]["ko"]))
PUL_KOS = sorted({"K21572", "K21573", "K00686", "K01187", "K01193", "K01205", "K01207", "K01218",
                  "K01776", "K17241", "K15922", "K15923"})

HYPOTHESES = [
    ("pul", "Bacteroidota × PUL", PUL_KOS,
        list(species[species["phylum"] == "p__Bacteroidota"]["gtdb_species_clade_id"])),
    ("mycolic", "Mycobacteriaceae × mycolic", mycolic_kos,
        list(species[species["family"] == "f__Mycobacteriaceae"]["gtdb_species_clade_id"])),
]

all_summaries = {}
for hyp_id, hyp_label, focal_kos, focal_species in HYPOTHESES:
    print(f"\n{'='*60}\nHYPOTHESIS: {hyp_label} ({hyp_id})", flush=True)
    print(f"  focal KOs: {len(focal_kos)}, focal species: {len(focal_species)}", flush=True)
    t_h = time.time()

    # Stage 1
    tprint(f"  [{hyp_id}] Stage 1: focal gene_clusters")
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
    s1_path = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage1_focal_clusters.parquet"
    focal_clusters.coalesce(2).write.mode("overwrite").parquet(s1_path)
    fc_pd = spark.read.parquet(s1_path).toPandas()
    fc_pd = pd.DataFrame({c: fc_pd[c].values for c in fc_pd.columns})
    tprint(f"    Stage 1: {len(fc_pd):,} (cluster, ko, species)")
    if len(fc_pd) == 0:
        print(f"    no focal clusters; skipping")
        continue
    focal_cluster_ids = fc_pd["gene_cluster_id"].unique().tolist()

    # Stage 2
    tprint(f"  [{hyp_id}] Stage 2: gene_genecluster_junction × pangenome.gene")
    cid_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": focal_cluster_ids}))
    gj = spark.table("kbase_ke_pangenome.gene_genecluster_junction")
    g = spark.table("kbase_ke_pangenome.gene")
    fg = gj.join(F.broadcast(cid_sdf), "gene_cluster_id", "inner").join(g, "gene_id", "inner")
    s2_path = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage2_genes.parquet"
    fg.coalesce(4).write.mode("overwrite").parquet(s2_path)
    fg_pd = spark.read.parquet(s2_path).toPandas()
    fg_pd = pd.DataFrame({c: fg_pd[c].values for c in fg_pd.columns})
    fg_pd = fg_pd.merge(fc_pd, on="gene_cluster_id", how="inner")
    tprint(f"    Stage 2: {len(fg_pd):,} genes")
    focal_gene_ids = fg_pd["gene_id"].unique().tolist()

    # Stage 3
    tprint(f"  [{hyp_id}] Stage 3: name table cross-walk")
    gid_sdf = spark.createDataFrame(pd.DataFrame({"name": focal_gene_ids}))
    name_t = spark.table("kbase_genomes.name")
    nm = name_t.join(F.broadcast(gid_sdf), "name", "inner").select("name", "entity_id")
    s3_path = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage3_name.parquet"
    nm.coalesce(4).write.mode("overwrite").parquet(s3_path)
    nm_pd = spark.read.parquet(s3_path).toPandas()
    nm_pd = pd.DataFrame({c: nm_pd[c].values for c in nm_pd.columns})
    fg_pd = fg_pd.merge(nm_pd.rename(columns={"name": "gene_id", "entity_id": "feature_id"}), on="gene_id", how="left")
    tprint(f"    Stage 3: {len(nm_pd):,} name→entity")

    # Stage 4
    tprint(f"  [{hyp_id}] Stage 4: feature positions")
    feat_ids = fg_pd["feature_id"].dropna().unique().tolist()
    fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": feat_ids}))
    feat = spark.table("kbase_genomes.feature")
    cxf = spark.table("kbase_genomes.contig_x_feature")
    feat_filt = (feat.join(F.broadcast(fid_sdf), "feature_id", "inner")
                  .filter(F.col("type") == "CDS")
                  .select("feature_id", F.col("start").cast("long").alias("start_int"),
                          F.col("end").cast("long").alias("end_int"), "strand"))
    s4a = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage4a_feat.parquet"
    feat_filt.coalesce(4).write.mode("overwrite").parquet(s4a)
    feat_pos = pd.DataFrame({c: spark.read.parquet(s4a).toPandas()[c].values for c in spark.read.parquet(s4a).toPandas().columns})
    cxf_filt = cxf.join(F.broadcast(fid_sdf), "feature_id", "inner").select("feature_id", "contig_id")
    s4b = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage4b_cxf.parquet"
    cxf_filt.coalesce(4).write.mode("overwrite").parquet(s4b)
    cxf_pos = pd.DataFrame({c: spark.read.parquet(s4b).toPandas()[c].values for c in spark.read.parquet(s4b).toPandas().columns})
    focal_features = fg_pd.merge(feat_pos, on="feature_id", how="inner").merge(cxf_pos, on="feature_id", how="inner")
    tprint(f"    Stage 4: {len(focal_features):,} focal features")
    focal_features.to_parquet(DATA_DIR / f"p4d2_neighborhood_{hyp_id}_focal_features.parquet", index=False)

    # Stage 5
    tprint(f"  [{hyp_id}] Stage 5: contig features")
    focal_contigs = focal_features["contig_id"].unique().tolist()
    tprint(f"    distinct focal contigs: {len(focal_contigs):,}")
    contig_sdf = spark.createDataFrame(pd.DataFrame({"contig_id": focal_contigs}))
    cxf_on = cxf.join(F.broadcast(contig_sdf), "contig_id", "inner").select("feature_id", "contig_id")
    s5a = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage5a_cxf_contigs.parquet"
    cxf_on.coalesce(4).write.mode("overwrite").parquet(s5a)
    cxf_on_pd = pd.DataFrame({c: spark.read.parquet(s5a).toPandas()[c].values for c in spark.read.parquet(s5a).toPandas().columns})
    cf_fids = cxf_on_pd["feature_id"].unique().tolist()
    cf_fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": cf_fids}))
    cf_filt = (feat.join(F.broadcast(cf_fid_sdf), "feature_id", "inner")
                .filter(F.col("type") == "CDS")
                .select("feature_id", F.col("start").cast("long").alias("nb_start"),
                        F.col("end").cast("long").alias("nb_end"), "strand"))
    s5b = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage5b_cf.parquet"
    cf_filt.coalesce(4).write.mode("overwrite").parquet(s5b)
    cf_pd = pd.DataFrame({c: spark.read.parquet(s5b).toPandas()[c].values for c in spark.read.parquet(s5b).toPandas().columns})
    contig_features_pd = cxf_on_pd.merge(cf_pd, on="feature_id", how="inner")
    tprint(f"    Stage 5: {len(contig_features_pd):,} CDS on focal contigs")

    # Stage 6 (vectorized)
    tprint(f"  [{hyp_id}] Stage 6: vectorized neighborhood join")
    focal_min = focal_features[["feature_id", "gene_id", "gene_cluster_id", "ko",
                                 "gtdb_species_clade_id", "contig_id", "start_int"]].rename(columns={
        "feature_id": "focal_feature_id", "gene_id": "focal_gene_id",
        "gene_cluster_id": "focal_cluster_id", "ko": "focal_ko",
        "gtdb_species_clade_id": "focal_species", "start_int": "focal_start"})
    merged = focal_min.merge(contig_features_pd, on="contig_id", how="inner")
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
    tprint(f"    neighbor pairs: {len(nbr_df):,}")

    # Stage 7
    tprint(f"  [{hyp_id}] Stage 7a: name cross-walk for neighbor feature_ids")
    nbr_fids = nbr_df["neighbor_feature_id"].unique().tolist()
    nbr_fid_sdf = spark.createDataFrame(pd.DataFrame({"entity_id": nbr_fids}))
    nbr_name = name_t.join(F.broadcast(nbr_fid_sdf), "entity_id", "inner").select("entity_id", F.col("name").alias("gene_id"))
    s7a = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage7a_nbrname.parquet"
    nbr_name.coalesce(4).write.mode("overwrite").parquet(s7a)
    nbr_name_pd = pd.DataFrame({c: spark.read.parquet(s7a).toPandas()[c].values for c in spark.read.parquet(s7a).toPandas().columns})
    tprint(f"    Stage 7a: {len(nbr_name_pd):,}")

    tprint(f"  [{hyp_id}] Stage 7b: gene_id → cluster_id")
    nbr_genes = nbr_name_pd["gene_id"].unique().tolist()
    nbr_genes_sdf = spark.createDataFrame(pd.DataFrame({"gene_id": nbr_genes}))
    nbr_clu = gj.join(F.broadcast(nbr_genes_sdf), "gene_id", "inner").select("gene_id", "gene_cluster_id")
    s7b = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage7b_nbrcluster.parquet"
    nbr_clu.coalesce(4).write.mode("overwrite").parquet(s7b)
    nbr_clu_pd = pd.DataFrame({c: spark.read.parquet(s7b).toPandas()[c].values for c in spark.read.parquet(s7b).toPandas().columns})
    tprint(f"    Stage 7b: {len(nbr_clu_pd):,}")

    tprint(f"  [{hyp_id}] Stage 7c: cluster → bakta product → MGE flag")
    nbr_cids = nbr_clu_pd["gene_cluster_id"].unique().tolist()
    nbr_cid_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": nbr_cids}))
    bakta_full = spark.table("kbase_ke_pangenome.bakta_annotations").select("gene_cluster_id", "product")
    nbr_p = (bakta_full.join(F.broadcast(nbr_cid_sdf), "gene_cluster_id", "inner")
                .withColumn("is_mge",
                    F.when(F.col("product").isNotNull() & F.lower(F.col("product")).rlike(mge_regex), 1).otherwise(0))
                .select("gene_cluster_id", "is_mge"))
    s7c = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage7c_nbrmge.parquet"
    nbr_p.coalesce(4).write.mode("overwrite").parquet(s7c)
    nbr_mge_pd = pd.DataFrame({c: spark.read.parquet(s7c).toPandas()[c].values for c in spark.read.parquet(s7c).toPandas().columns})
    nbr_mge_pd = nbr_mge_pd.drop_duplicates("gene_cluster_id")
    tprint(f"    Stage 7c: {len(nbr_mge_pd):,}")

    # Stage 8
    nbr_full = (nbr_df
        .merge(nbr_name_pd.rename(columns={"entity_id": "neighbor_feature_id"}), on="neighbor_feature_id", how="left")
        .merge(nbr_clu_pd.rename(columns={"gene_cluster_id": "neighbor_cluster_id"}), on="gene_id", how="left")
        .merge(nbr_mge_pd.rename(columns={"gene_cluster_id": "neighbor_cluster_id"}), on="neighbor_cluster_id", how="left"))
    nbr_full["is_mge"] = nbr_full["is_mge"].fillna(0)
    per_feature = (nbr_full.groupby(["focal_feature_id", "focal_cluster_id", "focal_ko", "focal_species"])
        .agg(n_neighbors=("neighbor_feature_id", "count"),
             n_mge_neighbors=("is_mge", "sum"))
        .reset_index())
    per_feature["mge_neighbor_fraction"] = per_feature["n_mge_neighbors"] / per_feature["n_neighbors"]
    per_feature["any_mge_neighbor"] = (per_feature["n_mge_neighbors"] > 0).astype(int)

    tprint(f"  [{hyp_id}] per-focal-feature: {len(per_feature):,}")
    tprint(f"  [{hyp_id}] mean fraction MGE neighbors: {per_feature['mge_neighbor_fraction'].mean():.4f}")
    tprint(f"  [{hyp_id}] fraction with ≥1 MGE neighbor: {per_feature['any_mge_neighbor'].mean()*100:.2f}%")

    out_path = DATA_DIR / f"p4d2_neighborhood_{hyp_id}_per_feature.parquet"
    pd.DataFrame({c: per_feature[c].values for c in per_feature.columns}).to_parquet(out_path, index=False)

    ko_summary = (per_feature.groupby("focal_ko")
        .agg(n_features=("focal_feature_id", "count"),
             mean_mge_neighbor_fraction=("mge_neighbor_fraction", "mean"),
             pct_with_any_mge_neighbor=("any_mge_neighbor", lambda v: v.mean()*100))
        .reset_index())
    print(f"\n  [{hyp_id}] Per-KO summary:", flush=True)
    print(ko_summary.sort_values("pct_with_any_mge_neighbor", ascending=False).head(20).to_string(index=False), flush=True)

    diag = {
        "phase": "4", "deliverable": f"P4-D2 neighborhood — {hyp_id}",
        "hypothesis": hyp_label,
        "neighbor_window_bp": NEIGHBOR_BP,
        "n_focal_features": int(len(per_feature)),
        "n_neighbor_pairs": int(len(nbr_full)),
        "atlas_mge_neighbor_fraction": float(per_feature["mge_neighbor_fraction"].mean()),
        "pct_features_with_any_mge_neighbor": float(per_feature["any_mge_neighbor"].mean()*100),
        "per_ko_summary": ko_summary.to_dict(orient="records"),
        "elapsed_s": round(time.time()-t_h, 1),
    }
    with open(DATA_DIR / f"p4d2_neighborhood_{hyp_id}_diagnostics.json", "w") as f:
        json.dump(diag, f, indent=2, default=str)
    all_summaries[hyp_id] = diag
    tprint(f"  [{hyp_id}] DONE in {time.time()-t_h:.1f}s")

print(f"\n=== ALL DONE in {time.time()-t0:.1f}s ===", flush=True)
print(json.dumps({k: {kk: v for kk, v in vv.items() if kk != 'per_ko_summary'} for k, vv in all_summaries.items()}, indent=2, default=str), flush=True)
