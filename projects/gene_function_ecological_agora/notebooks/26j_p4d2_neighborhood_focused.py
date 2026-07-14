"""NB26j — focused gene-neighborhood for canonical PUL + mycolic markers.

NB26h's PUL run blew driver.maxResultSize because the 12 PUL KOs include
generic glycoside hydrolases (K01205, K01218 etc.) used in 2,581 Bacteroidota
species → 119K focal clusters → 746K focal genes → 218K contigs. Too big.

Pivot: restrict to canonical markers only:
  - PUL: K21572 (SusC outer membrane), K21573 (SusD lipoprotein) — the actual
    PUL signature; everything else is generic CAZyme not PUL-specific.
  - Mycolic: 11 mycolic-specific KOs (MYCOLIC_SPECIFIC_KOS — Pks13, FAS-II
    components, MmaA1/2, etc.) — biology-driven, not pathway-id-based.

This keeps each hypothesis at <30K focal features (PSII-scale, proven feasible).
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

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB26j — PUL (canonical) + mycolic (specific) gene-neighborhood ===")
spark = get_spark_session()
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
mge_regex = "|".join(MGE_KEYWORDS)

# Canonical-marker KO sets
PUL_CANONICAL = ["K21572", "K21573"]  # SusC + SusD outer-membrane PUL signature
MYCOLIC_SPECIFIC = ["K11212", "K11211", "K11778", "K11533", "K11534",
                     "K00208", "K20274", "K11782", "K01205", "K00667", "K00507"]

HYPOTHESES = [
    ("pul_canonical", "Bacteroidota × PUL (SusC/SusD canonical)", PUL_CANONICAL,
        list(species[species["phylum"] == "p__Bacteroidota"]["gtdb_species_clade_id"])),
    ("mycolic_specific", "Mycobacteriaceae × mycolic-specific (11 KO panel)", MYCOLIC_SPECIFIC,
        list(species[species["family"] == "f__Mycobacteriaceae"]["gtdb_species_clade_id"])),
]

all_summaries = {}
for hyp_id, hyp_label, focal_kos, focal_species in HYPOTHESES:
    print(f"\n{'='*60}\nHYPOTHESIS: {hyp_label} ({hyp_id})", flush=True)
    print(f"  focal KOs: {len(focal_kos)}, focal species: {len(focal_species)}", flush=True)
    t_h = time.time()

    # Stage 1
    tprint(f"  [{hyp_id}] Stage 1: focal gene_clusters")
    fkos_sdf = spark.createDataFrame(pd.DataFrame({"focal_ko": focal_kos}))
    fsp_sdf = spark.createDataFrame(pd.DataFrame({"gtdb_species_clade_id": focal_species}))
    bakta = (spark.table("kbase_ke_pangenome.bakta_annotations")
        .filter(F.col("kegg_orthology_id").isNotNull() & (F.col("kegg_orthology_id") != ""))
        .withColumn("ko", F.split(F.col("kegg_orthology_id"), ",").getItem(0))
        .select("gene_cluster_id", "ko"))
    bakta_focal = bakta.join(F.broadcast(fkos_sdf), bakta["ko"] == fkos_sdf["focal_ko"], "inner").drop("focal_ko")
    gc = spark.table("kbase_ke_pangenome.gene_cluster").select("gene_cluster_id", "gtdb_species_clade_id")
    gc_focal = gc.join(F.broadcast(fsp_sdf), "gtdb_species_clade_id", "inner")
    focal_clusters = bakta_focal.join(gc_focal, "gene_cluster_id", "inner")
    s1 = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage1_focal_clusters.parquet"
    focal_clusters.coalesce(2).write.mode("overwrite").parquet(s1)
    fc_pd = spark.read.parquet(s1).toPandas()
    fc_pd = pd.DataFrame({c: fc_pd[c].values for c in fc_pd.columns})
    tprint(f"    Stage 1: {len(fc_pd):,}")
    if len(fc_pd) == 0:
        print(f"    no focal clusters; skipping"); continue
    fc_ids = fc_pd["gene_cluster_id"].unique().tolist()

    # Stage 2
    tprint(f"  [{hyp_id}] Stage 2: gene_genecluster_junction × pangenome.gene")
    cid_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": fc_ids}))
    gj = spark.table("kbase_ke_pangenome.gene_genecluster_junction")
    g = spark.table("kbase_ke_pangenome.gene")
    fg = gj.join(F.broadcast(cid_sdf), "gene_cluster_id", "inner").join(g, "gene_id", "inner")
    s2 = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage2_genes.parquet"
    fg.coalesce(4).write.mode("overwrite").parquet(s2)
    fg_pd = spark.read.parquet(s2).toPandas()
    fg_pd = pd.DataFrame({c: fg_pd[c].values for c in fg_pd.columns})
    fg_pd = fg_pd.merge(fc_pd, on="gene_cluster_id", how="inner")
    tprint(f"    Stage 2: {len(fg_pd):,}")
    fg_ids = fg_pd["gene_id"].unique().tolist()

    # Stage 3
    tprint(f"  [{hyp_id}] Stage 3: name table cross-walk")
    gid_sdf = spark.createDataFrame(pd.DataFrame({"name": fg_ids}))
    name_t = spark.table("kbase_genomes.name")
    nm = name_t.join(F.broadcast(gid_sdf), "name", "inner").select("name", "entity_id")
    s3 = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage3_name.parquet"
    nm.coalesce(4).write.mode("overwrite").parquet(s3)
    nm_pd = spark.read.parquet(s3).toPandas()
    nm_pd = pd.DataFrame({c: nm_pd[c].values for c in nm_pd.columns})
    fg_pd = fg_pd.merge(nm_pd.rename(columns={"name": "gene_id", "entity_id": "feature_id"}),
                          on="gene_id", how="left")
    tprint(f"    Stage 3: {len(nm_pd):,}")

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
    feat_pos_df = spark.read.parquet(s4a).toPandas()
    feat_pos = pd.DataFrame({c: feat_pos_df[c].values for c in feat_pos_df.columns})
    cxf_filt = cxf.join(F.broadcast(fid_sdf), "feature_id", "inner").select("feature_id", "contig_id")
    s4b = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage4b_cxf.parquet"
    cxf_filt.coalesce(4).write.mode("overwrite").parquet(s4b)
    cxf_pos_df = spark.read.parquet(s4b).toPandas()
    cxf_pos = pd.DataFrame({c: cxf_pos_df[c].values for c in cxf_pos_df.columns})
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
    cxf_on_df = spark.read.parquet(s5a).toPandas()
    cxf_on_pd = pd.DataFrame({c: cxf_on_df[c].values for c in cxf_on_df.columns})
    cf_fids = cxf_on_pd["feature_id"].unique().tolist()
    tprint(f"    distinct CDS feature_ids on focal contigs: {len(cf_fids):,}")
    cf_fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": cf_fids}))
    cf_filt = (feat.join(F.broadcast(cf_fid_sdf), "feature_id", "inner")
                .filter(F.col("type") == "CDS")
                .select("feature_id", F.col("start").cast("long").alias("nb_start"),
                        F.col("end").cast("long").alias("nb_end"), "strand"))
    s5b = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage5b_cf.parquet"
    cf_filt.coalesce(4).write.mode("overwrite").parquet(s5b)
    cf_df = spark.read.parquet(s5b).toPandas()
    cf_pd = pd.DataFrame({c: cf_df[c].values for c in cf_df.columns})
    contig_features_pd = cxf_on_pd.merge(cf_pd, on="feature_id", how="inner")
    tprint(f"    Stage 5: {len(contig_features_pd):,} CDS on focal contigs")

    # Stage 6 vectorized
    tprint(f"  [{hyp_id}] Stage 6: vectorized neighborhood")
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
    nbr_name_df = spark.read.parquet(s7a).toPandas()
    nbr_name_pd = pd.DataFrame({c: nbr_name_df[c].values for c in nbr_name_df.columns})

    tprint(f"  [{hyp_id}] Stage 7b: gene_id → cluster_id")
    nbr_genes = nbr_name_pd["gene_id"].unique().tolist()
    nbr_genes_sdf = spark.createDataFrame(pd.DataFrame({"gene_id": nbr_genes}))
    nbr_clu = gj.join(F.broadcast(nbr_genes_sdf), "gene_id", "inner").select("gene_id", "gene_cluster_id")
    s7b = f"{MINIO_BASE}/p4d2_nbh_{hyp_id}_stage7b_nbrcluster.parquet"
    nbr_clu.coalesce(4).write.mode("overwrite").parquet(s7b)
    nbr_clu_df = spark.read.parquet(s7b).toPandas()
    nbr_clu_pd = pd.DataFrame({c: nbr_clu_df[c].values for c in nbr_clu_df.columns})

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
    nbr_mge_df = spark.read.parquet(s7c).toPandas()
    nbr_mge_pd = pd.DataFrame({c: nbr_mge_df[c].values for c in nbr_mge_df.columns}).drop_duplicates("gene_cluster_id")

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
    print(ko_summary.sort_values("pct_with_any_mge_neighbor", ascending=False).to_string(index=False), flush=True)

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
