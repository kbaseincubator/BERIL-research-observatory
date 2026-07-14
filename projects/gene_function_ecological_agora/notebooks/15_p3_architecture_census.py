"""NB15 — Phase 3 architecture census on focused subsets.

For each of 4 Phase 3 focused subsets, compute Pfam multidomain architectures per KO
using interproscan_domains (audit-validated substrate per NB13):

  Subset A — PSII (K02703-K02727 PsbA-Z, ~25 KOs): for Cyanobacteria × PSII test
  Subset B — TCS HK (control_class = pos_tcs_hk in candidate set, 292 KOs): for Alm 2006 architectural back-test
  Subset C — Mycolic-acid curated specific KOs (11 from NB12): for Mycobacteriaceae architectural refinement
  Subset D — Top-50 mixed-category Innovator-Exchange (from candidate ranking): for NB11 novel observation follow-up

Strategy: filter at eggnog level FIRST (small KO lists), materialize the small
(gene_cluster_id, KO) joined frame, then filter IPS Pfam to those gene_clusters
(the join becomes broadcast-feasible). This avoids the 833M-row IPS scan that
hung NB14.

Outputs:
  data/p3_architecture_census_per_ko.tsv — per (subset, KO, architecture): n_gene_clusters
  data/p3_architecture_summary_per_ko.tsv — per KO: n_architectures, dominant_architecture, dominant_fraction
  data/p3_architecture_diagnostics.json
"""
import os, json, time
from pathlib import Path
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, ArrayType
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
print("=== NB15 — Phase 3 architecture census on focused subsets ===", flush=True)

# Define subsets
PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}  # K02703-K02727 PsbA-Z

candidates = pd.read_csv(DATA_DIR / "p3_candidate_set.tsv", sep="\t")
TCS_HK_KOS = set(candidates[candidates["control_class"] == "pos_tcs_hk"]["ko"])

MYCOLIC_SPECIFIC_KOS = {
    "K11212", "K11211", "K11778", "K11533", "K11534",
    "K00208", "K20274", "K11782", "K01205", "K00667", "K00507",
}

mixed_innov_top = candidates[candidates["category"] == "mixed"].nlargest(50, "n_innovator_exchange")
MIXED_TOP_KOS = set(mixed_innov_top["ko"])

all_subset_kos = PSII_KOS | TCS_HK_KOS | MYCOLIC_SPECIFIC_KOS | MIXED_TOP_KOS
print(f"Subset sizes: PSII {len(PSII_KOS)}, TCS HK {len(TCS_HK_KOS)}, Mycolic {len(MYCOLIC_SPECIFIC_KOS)}, Mixed-top-50 {len(MIXED_TOP_KOS)}", flush=True)
print(f"Total unique KOs to census: {len(all_subset_kos)}", flush=True)

# Subset assignment per KO (single primary subset for output classification)
def primary_subset(ko):
    if ko in PSII_KOS: return "psii"
    if ko in TCS_HK_KOS: return "tcs_hk"
    if ko in MYCOLIC_SPECIFIC_KOS: return "mycolic"
    if ko in MIXED_TOP_KOS: return "mixed_top50"
    return "other"

# Spark workflow
spark = get_spark_session()
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
spark.createDataFrame(species_df[["gtdb_species_clade_id"]]).createOrReplaceTempView("p1b_species")

# Stage 1: get gene_cluster → KO mapping for subset KOs only
print(f"\nStage 1: gene_cluster → KO mapping for {len(all_subset_kos)} subset KOs...", flush=True)
spark.createDataFrame(pd.DataFrame({"ko": list(all_subset_kos)})).createOrReplaceTempView("subset_kos")

# Quick path: pull eggnog only for these subset KOs by string-matching
ko_pattern = "|".join(sorted(all_subset_kos))
eggnog = spark.sql(f"""
    SELECT e.query_name AS gene_cluster_id, e.KEGG_ko
    FROM kbase_ke_pangenome.eggnog_mapper_annotations e
    JOIN kbase_ke_pangenome.gene_cluster gc ON e.query_name = gc.gene_cluster_id
    JOIN p1b_species sv ON gc.gtdb_species_clade_id = sv.gtdb_species_clade_id
    WHERE e.KEGG_ko RLIKE '({ko_pattern})'
""")

def parse_kos(ko_str):
    if ko_str in (None, "", "-"): return []
    toks = []
    for t in ko_str.replace(";", ",").split(","):
        t = t.replace("ko:", "").strip()
        if t and t.startswith("K") and len(t) == 6:
            toks.append(t)
    return list(set(toks))

parse_kos_udf = F.udf(parse_kos, ArrayType(StringType()))
gc_to_ko = (eggnog
    .withColumn("ko_list", parse_kos_udf(F.col("KEGG_ko")))
    .filter(F.size(F.col("ko_list")) > 0)
    .select("gene_cluster_id", F.explode("ko_list").alias("ko"))
    .join(F.broadcast(spark.table("subset_kos")), on="ko", how="inner")
)

t1 = time.time()
gc_to_ko_pdf = gc_to_ko.toPandas()
print(f"  collected (gc, KO) edges: {len(gc_to_ko_pdf):,} ({time.time()-t1:.1f}s)", flush=True)
unique_gcs = set(gc_to_ko_pdf["gene_cluster_id"])
print(f"  unique gene_clusters: {len(unique_gcs):,}", flush=True)

# Stage 2: get Pfam architecture per gene_cluster (via IPS, the audit-validated substrate)
print(f"\nStage 2: Pfam architecture per gene_cluster (IPS join, broadcast-filtered)...", flush=True)
spark.createDataFrame(pd.DataFrame({"gene_cluster_id": list(unique_gcs)})).createOrReplaceTempView("subset_gcs")

t1 = time.time()
gc_arch = spark.sql("""
    SELECT ips.gene_cluster_id,
           array_sort(collect_set(ips.signature_acc)) AS pfams
    FROM kbase_ke_pangenome.interproscan_domains ips
    JOIN subset_gcs sg ON ips.gene_cluster_id = sg.gene_cluster_id
    WHERE ips.analysis = 'Pfam'
    GROUP BY ips.gene_cluster_id
""")
gc_arch_pdf = gc_arch.toPandas()
gc_arch_pdf["architecture"] = gc_arch_pdf["pfams"].apply(lambda lst: "_".join(lst) if lst is not None else "")
print(f"  collected gc → architecture: {len(gc_arch_pdf):,} ({time.time()-t1:.1f}s)", flush=True)

# Stage 3: per (KO, architecture) count
merged = gc_to_ko_pdf.merge(gc_arch_pdf[["gene_cluster_id", "architecture"]], on="gene_cluster_id", how="left")
merged["architecture"] = merged["architecture"].fillna("__no_pfam__")
print(f"  merged (gc, ko, architecture) rows: {len(merged):,}", flush=True)

# Per (KO, architecture)
ko_arch_census = (merged
    .groupby(["ko", "architecture"])
    .size()
    .reset_index(name="n_gene_clusters")
    .sort_values(["ko", "n_gene_clusters"], ascending=[True, False])
)
ko_arch_census["subset"] = ko_arch_census["ko"].apply(primary_subset)
ko_arch_census = ko_arch_census[["subset", "ko", "architecture", "n_gene_clusters"]]
ko_arch_census.to_csv(DATA_DIR / "p3_architecture_census_per_ko.tsv", sep="\t", index=False)
print(f"\nWrote p3_architecture_census_per_ko.tsv: {len(ko_arch_census):,} (subset, KO, architecture) rows", flush=True)

# Per-KO summary
ko_summary = (ko_arch_census
    .groupby(["ko", "subset"])
    .agg(
        n_architectures=("architecture", "nunique"),
        n_gene_clusters_total=("n_gene_clusters", "sum"),
        dominant_architecture=("architecture", "first"),
        dominant_n_gc=("n_gene_clusters", "first"),
    )
    .reset_index()
)
ko_summary["dominant_fraction"] = ko_summary["dominant_n_gc"] / ko_summary["n_gene_clusters_total"]
ko_summary = ko_summary.sort_values(["subset", "n_gene_clusters_total"], ascending=[True, False])
ko_summary.to_csv(DATA_DIR / "p3_architecture_summary_per_ko.tsv", sep="\t", index=False)
print(f"Wrote p3_architecture_summary_per_ko.tsv: {len(ko_summary):,} per-KO summary rows", flush=True)

# Subset-level summary statistics
print(f"\n=== Per-subset architecture diversity ===", flush=True)
for subset in ["psii", "tcs_hk", "mycolic", "mixed_top50"]:
    sub = ko_summary[ko_summary["subset"] == subset]
    if len(sub) == 0:
        print(f"  {subset}: NO DATA", flush=True)
        continue
    print(f"  {subset}: {len(sub)} KOs, median {sub['n_architectures'].median():.0f} architectures/KO, "
          f"median dominant_fraction {sub['dominant_fraction'].median():.2f}", flush=True)

# Top architectures per subset
for subset in ["psii", "tcs_hk", "mycolic", "mixed_top50"]:
    print(f"\n=== Top-3 architectures × KOs for {subset} ===", flush=True)
    sub = ko_arch_census[ko_arch_census["subset"] == subset]
    if len(sub) == 0:
        print(f"  no data", flush=True)
        continue
    top3_per_ko = sub.groupby("ko").head(3)
    arch_overall = sub.groupby("architecture")["n_gene_clusters"].sum().sort_values(ascending=False).head(5)
    print(arch_overall.to_string(), flush=True)

diagnostics = {
    "phase": "3", "notebook": "NB15",
    "n_psii_kos": len(PSII_KOS),
    "n_tcs_hk_kos": len(TCS_HK_KOS),
    "n_mycolic_kos": len(MYCOLIC_SPECIFIC_KOS),
    "n_mixed_top50_kos": len(MIXED_TOP_KOS),
    "n_total_subset_kos": len(all_subset_kos),
    "n_gc_to_ko_edges": int(len(gc_to_ko_pdf)),
    "n_unique_gene_clusters": int(len(unique_gcs)),
    "n_gc_with_pfam": int(len(gc_arch_pdf)),
    "n_per_ko_arch_rows": int(len(ko_arch_census)),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p3_architecture_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"\nWrote p3_architecture_diagnostics.json ({time.time()-t0:.1f}s)", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
