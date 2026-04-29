"""NB22d — BacDive match using version-stripped GCA accessions.

NB22c diagnosed that BacDive accessions are stored without version suffix
(e.g., GCA_002951815) while our representative_genome_id values have versions
(e.g., GB_GCA_000433415.1). The match needs to strip the .N version too.

Also try GCF→GCA fallback: BacDive INSDC accessions are GCA-only; some of our
species are RS_GCF_*. Test whether INSDC has the matching GCA equivalent
(equivalent_assembly is NCBI standard so usually GCA assembly = GCF assembly).
"""
import json
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

spark = get_spark_session()
species = pd.read_csv("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data/p1b_full_species.tsv", sep="\t")
print(f"P1B species reps: {len(species):,}", flush=True)

# Strip prefix and version
species["clean_no_version"] = species["representative_genome_id"].str.replace(r"^(GB_|RS_)", "", regex=True).str.replace(r"\.\d+$", "", regex=True)
# Also create a GCA-form version (some are RS_GCF — convert GCF → GCA)
species["clean_as_gca"] = species["clean_no_version"].str.replace(r"^GCF_", "GCA_", regex=True)
n_gca = species["clean_no_version"].str.startswith("GCA").sum()
n_gcf = species["clean_no_version"].str.startswith("GCF").sum()
print(f"  GCA-form (no version): {n_gca}, GCF-form (no version): {n_gcf}", flush=True)

bd = spark.table("kescience_bacdive.sequence_info").filter(F.col("accession_type") == "genome").select("accession", "bacdive_id")

species_sdf = spark.createDataFrame(species[["clean_no_version", "clean_as_gca", "gtdb_species_clade_id"]])

# Match 1: clean_no_version (direct, GCA-only matches)
m1 = species_sdf.join(F.broadcast(bd), species_sdf["clean_no_version"] == bd["accession"], "left")
m1_count = m1.filter(F.col("bacdive_id").isNotNull()).select("gtdb_species_clade_id").distinct().count()
print(f"Match 1 (direct, no version): {m1_count} of 18,989 species ({100*m1_count/18989:.2f}%)", flush=True)

# Match 2: GCF→GCA fallback
m2 = species_sdf.join(F.broadcast(bd), species_sdf["clean_as_gca"] == bd["accession"], "left")
m2_count = m2.filter(F.col("bacdive_id").isNotNull()).select("gtdb_species_clade_id").distinct().count()
print(f"Match 2 (GCF→GCA fallback): {m2_count} of 18,989 species ({100*m2_count/18989:.2f}%)", flush=True)

# Now check phenotype-table coverage among matched strains
print("\nMatched-strain phenotype coverage:", flush=True)
matched_bd_ids = m2.filter(F.col("bacdive_id").isNotNull()).select("bacdive_id").distinct()
n_matched = matched_bd_ids.count()
print(f"  distinct matched bacdive_ids: {n_matched:,}", flush=True)

phenotype_coverage = {}
for tab in ["metabolite_utilization", "physiology", "isolation", "enzyme", "culture_condition"]:
    try:
        t = spark.table(f"kescience_bacdive.{tab}").select("bacdive_id").distinct()
        cov = t.join(F.broadcast(matched_bd_ids), "bacdive_id").count()
        print(f"  {tab}: {cov:,} of matched ({100*cov/n_matched if n_matched else 0:.1f}%)", flush=True)
        phenotype_coverage[tab] = cov
    except Exception as e:
        print(f"  {tab}: failed ({type(e).__name__})", flush=True)
        phenotype_coverage[tab] = -1

# Update audit JSON
audit_path = "/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data/p4d1_feasibility_audit.json"
with open(audit_path) as f:
    audit = json.load(f)
audit["bacdive_coverage"] = {
    "match_direct_no_version": int(m1_count),
    "match_gcf_to_gca_fallback": int(m2_count),
    "match_combined_pct": round(100 * m2_count / 18989, 2),
    "matched_distinct_bacdive_ids": int(n_matched),
    "phenotype_table_coverage": phenotype_coverage,
}
audit["bacdive_species_pct"] = round(100 * m2_count / 18989, 2)
with open(audit_path, "w") as f:
    json.dump(audit, f, indent=2, default=str)
print(f"\nUpdated audit JSON. Final BacDive coverage: {audit['bacdive_species_pct']}%", flush=True)
