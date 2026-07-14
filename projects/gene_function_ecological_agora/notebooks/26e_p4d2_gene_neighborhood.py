"""NB26e / P4-D2 enhanced — gene-neighborhood MGE-cargo measurement.

Per-hypothesis pipeline (run one hypothesis at a time via HYP env var, or all):

  1. Identify focal gene_clusters (filter bakta_annotations: KO ∈ focal_ko_set)
     × gene_cluster (filter gtdb_species_clade_id ∈ focal_species).
  2. Get focal genes via gene_genecluster_junction × pangenome.gene
     (filter gene_cluster_id IN focal_cluster_set — small, broadcast-able).
  3. Cross-walk to kbase_genomes via name table → feature_id.
  4. Get positions via contig_x_feature × feature.
  5. For each focal feature, pull ±5kb neighbor features on same contig.
  6. Cross-walk neighbors back to gene_cluster_id → bakta product → MGE flag.
  7. Aggregate per focal-feature: fraction of neighbors that are MGE machinery.
  8. Aggregate per (KO × species).

Persist intermediates to MinIO at each stage so we can recover.

Outputs:
  data/p4d2_neighborhood_{hyp}_focal_features.parquet
  data/p4d2_neighborhood_{hyp}_neighbors_with_mge.parquet
  data/p4d2_neighborhood_{hyp}_diagnostics.json
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
print("=== NB26e — gene-neighborhood MGE-cargo pipeline ===", flush=True)

spark = get_spark_session()
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

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

PSII_KOS = sorted({f"K{n:05d}" for n in range(2703, 2728)})
PUL_KOS = sorted({"K21572", "K21573", "K00686", "K01187", "K01193", "K01205", "K01207", "K01218",
                  "K01776", "K17241", "K15922", "K15923"})

HYPOTHESES = [
    ("psii", "Cyanobacteriia × PSII", PSII_KOS,
        list(species[species["class"] == "c__Cyanobacteriia"]["gtdb_species_clade_id"])),
    ("pul", "Bacteroidota × PUL", PUL_KOS,
        list(species[species["phylum"] == "p__Bacteroidota"]["gtdb_species_clade_id"])),
    ("mycolic", "Mycobacteriaceae × mycolic", mycolic_kos,
        list(species[species["family"] == "f__Mycobacteriaceae"]["gtdb_species_clade_id"])),
]

# MGE keywords
MGE_KEYWORDS = ["phage", "transposase", "integrase", "plasmid", "transposon",
                "is element", "is-element", "prophage", "conjugation", "conjugative",
                "recombinase", "mobile element", "tn3", "is3", "is5", "is30", "is200",
                "is256", "is481", "is607", "is630", "is701", "is91", "tn5", "insertion sequence",
                "phage tail", "phage portal", "phage capsid", "phage holin", "phage lysin",
                "phage terminase", "tra protein"]
mge_regex = "|".join(MGE_KEYWORDS)

all_results = {}
for hyp_id, hyp_label, focal_kos, focal_species in HYPOTHESES:
    print(f"\n{'='*60}\nHYPOTHESIS: {hyp_label} ({hyp_id})", flush=True)
    print(f"  focal KOs: {len(focal_kos)}, focal species: {len(focal_species)}", flush=True)
    t_h = time.time()

    # Stage 1: focal gene_clusters
    print(f"\n  Stage 1: focal gene_clusters", flush=True)
    bakta = (spark.table("kbase_ke_pangenome.bakta_annotations")
        .filter(F.col("kegg_orthology_id").isNotNull() & (F.col("kegg_orthology_id") != ""))
        .withColumn("ko", F.split(F.col("kegg_orthology_id"), ",").getItem(0))
        .filter(F.col("ko").isin(focal_kos))
        .select("gene_cluster_id", "ko", "product"))
    gc = (spark.table("kbase_ke_pangenome.gene_cluster")
        .filter(F.col("gtdb_species_clade_id").isin(focal_species))
        .select("gene_cluster_id", "gtdb_species_clade_id"))
    focal_clusters = bakta.join(gc, "gene_cluster_id", "inner")
    fc_count = focal_clusters.count()
    print(f"    focal gene_clusters: {fc_count}", flush=True)
    if fc_count == 0:
        print(f"  no focal clusters; skipping {hyp_id}")
        continue
    focal_clusters_pd = focal_clusters.toPandas()
    focal_cluster_ids = focal_clusters_pd["gene_cluster_id"].unique().tolist()
    print(f"    distinct cluster IDs: {len(focal_cluster_ids)}", flush=True)

    # Stage 2: get constituent gene_ids — small set, broadcast filter
    print(f"\n  Stage 2: constituent genes (filter gene_genecluster_junction by cluster_id IN list)", flush=True)
    gj = spark.table("kbase_ke_pangenome.gene_genecluster_junction")
    cluster_id_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": focal_cluster_ids}))
    focal_genes = gj.join(F.broadcast(cluster_id_sdf), "gene_cluster_id", "inner")
    fg_count = focal_genes.count()
    print(f"    constituent genes: {fg_count:,}", flush=True)
    if fg_count == 0:
        print(f"  no constituent genes; skipping")
        continue
    # Get genome_id via pangenome.gene
    g = spark.table("kbase_ke_pangenome.gene")
    focal_genes_with_genome = focal_genes.join(g, "gene_id", "inner")
    print(f"    triggering pull...", flush=True)
    focal_genes_pd = focal_genes_with_genome.toPandas()
    print(f"    pulled {len(focal_genes_pd):,} (gene_id, gene_cluster_id, genome_id)", flush=True)

    # Stage 3: cross-walk to kbase_genomes via name table
    print(f"\n  Stage 3: name-table cross-walk (filter kbase_genomes.name by gene_id IN list)", flush=True)
    focal_gene_ids = focal_genes_pd["gene_id"].unique().tolist()
    print(f"    distinct gene_ids: {len(focal_gene_ids):,}", flush=True)
    name_t = spark.table("kbase_genomes.name")
    gene_id_sdf = spark.createDataFrame(pd.DataFrame({"name": focal_gene_ids}))
    name_join = name_t.join(F.broadcast(gene_id_sdf), "name", "inner").select("entity_id", "name")
    name_pd = name_join.toPandas()
    print(f"    name → entity_id (feature_id) rows: {len(name_pd):,}", flush=True)
    # name -> feature_id mapping
    focal_genes_pd = focal_genes_pd.merge(
        name_pd.rename(columns={"entity_id": "feature_id", "name": "gene_id"}),
        on="gene_id", how="left")

    # Stage 4: get positions via feature × contig_x_feature
    # IMPORTANT: filter contig_x_feature with the same broadcast list independently,
    # so the 1B-row cxf scan is pruned via broadcast filter rather than join-side filter.
    print(f"\n  Stage 4: feature positions", flush=True)
    feature_ids = focal_genes_pd["feature_id"].dropna().unique().tolist()
    print(f"    distinct feature_ids: {len(feature_ids):,}", flush=True)
    fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": feature_ids}))
    feat = spark.table("kbase_genomes.feature")
    cxf = spark.table("kbase_genomes.contig_x_feature")

    # Filter both with broadcast then join the filtered results
    feat_filt = (feat.join(F.broadcast(fid_sdf), "feature_id", "inner")
                  .filter(F.col("type") == "CDS")
                  .select("feature_id", F.col("start").cast("long").alias("start_int"),
                          F.col("end").cast("long").alias("end_int"), "strand"))
    cxf_filt = cxf.join(F.broadcast(fid_sdf), "feature_id", "inner").select("feature_id", "contig_id")
    feat_with_pos = feat_filt.join(F.broadcast(cxf_filt), "feature_id", "inner")
    pos_pd = feat_with_pos.toPandas()
    print(f"    feature positions: {len(pos_pd):,}", flush=True)
    focal_features = focal_genes_pd.merge(pos_pd, on="feature_id", how="inner")
    print(f"    focal features with positions: {len(focal_features):,}", flush=True)

    # Save focal feature table
    focal_features_path = DATA_DIR / f"p4d2_neighborhood_{hyp_id}_focal_features.parquet"
    pd.DataFrame({c: focal_features[c].values for c in focal_features.columns}).to_parquet(focal_features_path, index=False)
    print(f"    saved {focal_features_path}", flush=True)

    # Stage 5: pull ±5kb neighbors on same contigs
    # Same pattern as stage 4: filter cxf and feat independently with broadcast,
    # then join the filtered results.
    print(f"\n  Stage 5: pull ±{NEIGHBOR_BP}bp neighbors on focal contigs", flush=True)
    focal_contigs = focal_features["contig_id"].unique().tolist()
    print(f"    distinct contigs: {len(focal_contigs):,}", flush=True)
    contig_sdf = spark.createDataFrame(pd.DataFrame({"contig_id": focal_contigs}))

    # Step 5a: cxf filtered to focal contigs → (feature_id, contig_id) for those contigs
    cxf_on_contigs = cxf.join(F.broadcast(contig_sdf), "contig_id", "inner").select("feature_id", "contig_id")
    cxf_on_contigs_pd = cxf_on_contigs.toPandas()
    print(f"    cxf rows on focal contigs: {len(cxf_on_contigs_pd):,}", flush=True)

    # Step 5b: pull all features for those feature_ids (filter feat with broadcast)
    contig_feat_ids = cxf_on_contigs_pd["feature_id"].unique().tolist()
    cf_fid_sdf = spark.createDataFrame(pd.DataFrame({"feature_id": contig_feat_ids}))
    contig_feat_filt = (feat.join(F.broadcast(cf_fid_sdf), "feature_id", "inner")
                          .filter(F.col("type") == "CDS")
                          .select("feature_id", F.col("start").cast("long").alias("nb_start"),
                                  F.col("end").cast("long").alias("nb_end"), "strand"))
    contig_feat_pd = contig_feat_filt.toPandas()
    print(f"    CDS features pulled: {len(contig_feat_pd):,}", flush=True)
    contig_features_pd = cxf_on_contigs_pd.merge(contig_feat_pd, on="feature_id", how="inner")
    print(f"    all CDS features on focal contigs: {len(contig_features_pd):,}", flush=True)

    # Stage 6: in-pandas neighborhood join (small, fast)
    print(f"\n  Stage 6: neighborhood join in pandas", flush=True)
    # For each focal feature: find neighbors on same contig within ±NEIGHBOR_BP that are NOT itself
    nbr_rows = []
    focal_min_idx = focal_features.set_index("feature_id")
    cf_by_contig = contig_features_pd.groupby("contig_id")
    for _, row in focal_features.iterrows():
        contig_id = row["contig_id"]
        focal_start = row["start_int"]
        focal_fid = row["feature_id"]
        try:
            cf_sub = cf_by_contig.get_group(contig_id)
        except KeyError:
            continue
        in_window = cf_sub[
            (cf_sub["nb_start"] >= focal_start - NEIGHBOR_BP) &
            (cf_sub["nb_end"] <= focal_start + NEIGHBOR_BP) &
            (cf_sub["feature_id"] != focal_fid)
        ]
        for _, nbr in in_window.iterrows():
            nbr_rows.append({
                "focal_feature_id": focal_fid, "focal_gene_id": row["gene_id"],
                "focal_cluster_id": row["gene_cluster_id"], "focal_ko": row["ko"],
                "focal_species": row["gtdb_species_clade_id"],
                "neighbor_feature_id": nbr["feature_id"],
                "distance_bp": int(min(abs(nbr["nb_start"] - focal_start),
                                       abs(nbr["nb_end"] - focal_start))),
            })
    nbr_df = pd.DataFrame(nbr_rows)
    print(f"    total neighbor pairs: {len(nbr_df):,}", flush=True)

    if len(nbr_df) == 0:
        print(f"  no neighbors; skipping")
        continue

    # Stage 7: cross-walk neighbor feature_ids back to gene_cluster_id + MGE flag
    print(f"\n  Stage 7: neighbor feature_id → gene_cluster_id → bakta MGE flag", flush=True)
    nbr_fids = nbr_df["neighbor_feature_id"].unique().tolist()
    print(f"    distinct neighbor feature_ids: {len(nbr_fids):,}", flush=True)
    nbr_fid_sdf = spark.createDataFrame(pd.DataFrame({"entity_id": nbr_fids}))
    # name table maps entity_id (feature_id) ↔ name (gene_id)
    nbr_gene_id = (name_t.join(F.broadcast(nbr_fid_sdf), "entity_id", "inner")
        .select("entity_id", F.col("name").alias("gene_id")))
    nbr_to_cluster = (nbr_gene_id
        .join(gj, "gene_id", "inner")
        .select(F.col("entity_id").alias("neighbor_feature_id"),
                F.col("gene_cluster_id").alias("neighbor_cluster_id"),
                "gene_id"))
    nbr_to_cluster_pd = nbr_to_cluster.toPandas()
    print(f"    neighbor → cluster rows: {len(nbr_to_cluster_pd):,}", flush=True)

    # Get bakta product per neighbor cluster
    nbr_cluster_ids = nbr_to_cluster_pd["neighbor_cluster_id"].dropna().unique().tolist()
    print(f"    distinct neighbor clusters: {len(nbr_cluster_ids):,}", flush=True)
    nbr_cluster_sdf = spark.createDataFrame(pd.DataFrame({"gene_cluster_id": nbr_cluster_ids}))
    bakta_full = spark.table("kbase_ke_pangenome.bakta_annotations").select("gene_cluster_id", "product")
    nbr_products = (bakta_full
        .join(F.broadcast(nbr_cluster_sdf), "gene_cluster_id", "inner")
        .withColumn("is_mge",
            F.when(F.col("product").isNotNull() & F.lower(F.col("product")).rlike(mge_regex), 1).otherwise(0))
        .select(F.col("gene_cluster_id").alias("neighbor_cluster_id"), "product", "is_mge"))
    nbr_products_pd = nbr_products.toPandas()
    print(f"    neighbor cluster products: {len(nbr_products_pd):,}", flush=True)

    # Stage 8: aggregate
    nbr_full = nbr_df.merge(nbr_to_cluster_pd, on="neighbor_feature_id", how="left").merge(
        nbr_products_pd[["neighbor_cluster_id", "is_mge"]].drop_duplicates("neighbor_cluster_id"),
        on="neighbor_cluster_id", how="left")
    nbr_full["is_mge"] = nbr_full["is_mge"].fillna(0)
    print(f"\n  Stage 8: aggregate", flush=True)
    print(f"    total neighbor rows after MGE-tag: {len(nbr_full):,}", flush=True)
    print(f"    MGE-tagged neighbors: {int(nbr_full['is_mge'].sum()):,}", flush=True)

    # Per focal feature: fraction of neighbors that are MGE
    per_feature = (nbr_full.groupby(["focal_feature_id", "focal_cluster_id", "focal_ko", "focal_species"])
        .agg(n_neighbors=("neighbor_feature_id", "count"),
             n_mge_neighbors=("is_mge", "sum"))
        .reset_index())
    per_feature["mge_neighbor_fraction"] = per_feature["n_mge_neighbors"] / per_feature["n_neighbors"]
    per_feature["any_mge_neighbor"] = (per_feature["n_mge_neighbors"] > 0).astype(int)
    print(f"    per-focal-feature: {len(per_feature):,}, mean fraction = {per_feature['mge_neighbor_fraction'].mean():.4f}", flush=True)
    print(f"    fraction with ≥1 MGE neighbor: {per_feature['any_mge_neighbor'].mean()*100:.2f}%", flush=True)

    # Save
    out_path = DATA_DIR / f"p4d2_neighborhood_{hyp_id}_per_feature.parquet"
    pd.DataFrame({c: per_feature[c].values for c in per_feature.columns}).to_parquet(out_path, index=False)
    print(f"    saved {out_path}", flush=True)

    # Per (KO × species) summary
    per_ko_sp = (per_feature.groupby(["focal_ko", "focal_species"])
        .agg(n_features=("focal_feature_id", "count"),
             mean_mge_neighbor_fraction=("mge_neighbor_fraction", "mean"),
             pct_with_any_mge_neighbor=("any_mge_neighbor", "mean"))
        .reset_index())
    per_ko_sp["pct_with_any_mge_neighbor"] *= 100
    print(f"\n    per (KO × species): {len(per_ko_sp):,}, "
          f"mean fraction-with-MGE-neighbor = {per_ko_sp['pct_with_any_mge_neighbor'].mean():.2f}%", flush=True)
    print(f"    top 10 (KO × species) by % with any MGE neighbor:")
    print(per_ko_sp.sort_values("pct_with_any_mge_neighbor", ascending=False).head(10).to_string(index=False), flush=True)

    all_results[hyp_id] = {
        "hypothesis": hyp_label,
        "n_focal_clusters": int(fc_count),
        "n_focal_features": int(len(per_feature)),
        "n_neighbor_pairs": int(len(nbr_full)),
        "atlas_mge_neighbor_fraction": float(per_feature["mge_neighbor_fraction"].mean()),
        "pct_features_with_any_mge_neighbor": float(per_feature["any_mge_neighbor"].mean()*100),
        "elapsed_s": round(time.time()-t_h, 1),
    }
    print(f"\n  {hyp_id} done in {time.time()-t_h:.1f}s", flush=True)

# Save combined diagnostics
diag = {
    "phase": "4", "deliverable": "P4-D2 enhanced — gene-neighborhood MGE cargo",
    "neighbor_window_bp": NEIGHBOR_BP,
    "results_per_hypothesis": all_results,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d2_neighborhood_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
print(f"\n=== ALL DONE in {time.time()-t0:.1f}s ===", flush=True)
print(json.dumps(all_results, indent=2, default=str), flush=True)
