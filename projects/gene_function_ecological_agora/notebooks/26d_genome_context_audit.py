"""NB26d — audit gene-neighborhood path before scaling.

Verify the cross-walk: pangenome gene_id → kbase_genomes feature → start/end/contig.
Then check whether we can pull a gene's ±N-gene neighborhood from the same contig.

If this works, NB26e will run a focused MGE-cargo analysis on the pre-registered
hypotheses (Mycobacteriaceae × mycolic, Cyanobacteriia × PSII, Bacteroidota × PUL).
"""
import time
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

t0 = time.time()
print("=== NB26d — gene neighborhood path audit ===", flush=True)

spark = get_spark_session()

# --- Stage 1: pick a test species + KO with known content ---
print("\nStage 1: schema check on key tables", flush=True)
gc = spark.table("kbase_ke_pangenome.gene_cluster")
print(f"  gene_cluster: {gc.columns}")
gj = spark.table("kbase_ke_pangenome.gene_genecluster_junction")
print(f"  gene_genecluster_junction: {gj.columns}")
g = spark.table("kbase_ke_pangenome.gene")
print(f"  pangenome.gene: {g.columns}")
n = spark.table("kbase_genomes.name")
print(f"  kbase_genomes.name: {n.columns}")
f_ = spark.table("kbase_genomes.feature")
print(f"  kbase_genomes.feature: {f_.columns}")
cxf = spark.table("kbase_genomes.contig_x_feature")
print(f"  contig_x_feature: {cxf.columns}")

# --- Stage 2: pull a few example genes via the cross-walk ---
print("\nStage 2: test cross-walk for 100 randomly-chosen mycolic-acid gene_clusters", flush=True)
# Find some Mycobacteriaceae gene_clusters carrying mycolic-acid KO K11212 (Pks13)
# K11212 = Pks13 polyketide synthase 13 — central mycolic-acid biosynthesis enzyme
bakta = spark.table("kbase_ke_pangenome.bakta_annotations").select(
    "gene_cluster_id", "kegg_orthology_id", "product")

# Find clusters with K11212 in any KO field
test_clusters = (bakta
    .filter(F.col("kegg_orthology_id").contains("K11212"))
    .join(gc.select("gene_cluster_id", "gtdb_species_clade_id"), "gene_cluster_id"))
print(f"  K11212-bearing gene_clusters: {test_clusters.count()}")
test_clusters_sample = test_clusters.limit(5).toPandas()
print(f"  sample:\n{test_clusters_sample}")

# Get a single gene_cluster's constituent genes
print("\n  pulling gene members of first test cluster...", flush=True)
test_cluster_id = test_clusters_sample.iloc[0]["gene_cluster_id"]
print(f"  test_cluster_id = {test_cluster_id}")

cluster_genes = (gj
    .filter(F.col("gene_cluster_id") == test_cluster_id)
    .join(g, "gene_id"))
n_genes = cluster_genes.count()
print(f"  cluster has {n_genes} constituent genes")
sample_genes = cluster_genes.limit(3).toPandas()
print(f"  sample genes:\n{sample_genes}")

# --- Stage 3: resolve gene_id → kbase_genomes feature ---
test_gene_id = sample_genes.iloc[0]["gene_id"]
test_genome_id = sample_genes.iloc[0]["genome_id"]
print(f"\nStage 3: resolve gene_id={test_gene_id} → kbase_genomes feature", flush=True)

name_match = n.filter(F.col("name") == test_gene_id).limit(5).toPandas()
print(f"  name matches: {name_match}")

# --- Stage 4: get position via contig_x_feature + feature ---
if len(name_match) > 0:
    feature_id = name_match.iloc[0]["entity_id"]
    print(f"\nStage 4: pull position for feature_id={feature_id}")
    feature_pos = (cxf.filter(F.col("feature_id") == feature_id)
        .join(f_, "feature_id")
        .toPandas())
    print(f"  position:\n{feature_pos}")

    # Now find the contig and pull neighbors
    if len(feature_pos) > 0:
        contig_id = feature_pos.iloc[0]["contig_id"]
        feat_start = int(feature_pos.iloc[0]["start"])
        print(f"\nStage 5: pull ±5kb neighbors on contig {contig_id} (feat_start={feat_start})")
        # Note: start is stored as STRING per pitfalls
        neighbors = (cxf.filter(F.col("contig_id") == contig_id)
            .join(f_, "feature_id")
            .filter(F.col("type") == "CDS")
            .withColumn("start_int", F.col("start").cast("long"))
            .withColumn("end_int", F.col("end").cast("long"))
            .filter((F.col("start_int") >= feat_start - 5000) & (F.col("end_int") <= feat_start + 5000))
            .select("feature_id", "start_int", "end_int", "strand", "type")
            .toPandas())
        print(f"  ±5kb neighbors: {len(neighbors)} CDS features")
        print(neighbors.head(15).to_string())

print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
