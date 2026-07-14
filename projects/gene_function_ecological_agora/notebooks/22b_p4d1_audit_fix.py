"""NB22b — fix the BacDive + NMDC audits from NB22.

NB22 succeeded for GTDB metadata (99.96% isolation_source coverage) and FB (0.18%, 35
species). BacDive failed on a column-name reference (`species_name` not in
sequence_info — that's in the `strain` table). NMDC `taxonomy_features` was discovered
to be a wide matrix where columns are NCBI taxids; the audit needs to bridge
GTDB → NCBI taxid first, then check column overlap.
"""
import json, time
from pathlib import Path
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
print("=== NB22b — BacDive + NMDC audit fix ===", flush=True)

species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
our_species_clade_ids = set(species["gtdb_species_clade_id"].unique())
print(f"P1B species reps: {len(species):,}", flush=True)

spark = get_spark_session()

# Stage 3 fixed: BacDive — count distinct accessions matching our reps
print("\n--- Stage 3 (fixed): BacDive sequence_info GCA coverage ---", flush=True)
bacdive_seq = spark.table("kescience_bacdive.sequence_info").select("accession", "bacdive_id")
total_bd = bacdive_seq.count()
print(f"  bacdive sequence_info total rows: {total_bd:,}", flush=True)

# Strip GB_/RS_ prefix from our genome IDs
species_for_bd = species[["representative_genome_id", "gtdb_species_clade_id"]].copy()
species_for_bd["clean_acc"] = species_for_bd["representative_genome_id"].str.replace(r"^(GB_|RS_)", "", regex=True)

species_clean_sdf = spark.createDataFrame(species_for_bd[["clean_acc", "gtdb_species_clade_id"]])
bd_join = species_clean_sdf.join(F.broadcast(bacdive_seq), species_clean_sdf["clean_acc"] == bacdive_seq["accession"], "left")
bd_stats = bd_join.agg(
    F.countDistinct(F.when(F.col("bacdive_id").isNotNull(), F.col("gtdb_species_clade_id"))).alias("species_with_bacdive_match"),
    F.countDistinct(F.when(F.col("bacdive_id").isNotNull(), F.col("clean_acc"))).alias("genomes_matched"),
).collect()[0].asDict()
print(f"  BacDive coverage: {bd_stats}", flush=True)
bd_pct = 100 * bd_stats["species_with_bacdive_match"] / len(our_species_clade_ids)
print(f"  → {bd_pct:.1f}% of P1B species have a BacDive sequence_info match", flush=True)

# Now also try a join through strain → taxonomy for actual phenotype-data coverage
print("\n  Checking BacDive strain → physiology / metabolite_utilization tables for phenotype coverage...", flush=True)
try:
    bd_strain = spark.table("kescience_bacdive.strain").select("bacdive_id", "ncbi_taxid")
    print(f"    strain rows: {bd_strain.count():,}", flush=True)
    # Count BacDive ids with matched our genomes that have phenotype rows
    matched_bd_ids = (bd_join.filter(F.col("bacdive_id").isNotNull())
                            .select("bacdive_id").distinct())
    n_matched_bd = matched_bd_ids.count()
    print(f"    distinct matched bacdive_ids: {n_matched_bd:,}", flush=True)

    for phen_table in ["metabolite_utilization", "physiology", "isolation", "enzyme", "culture_condition"]:
        try:
            t = spark.table(f"kescience_bacdive.{phen_table}").select("bacdive_id").distinct()
            covered = t.join(F.broadcast(matched_bd_ids), "bacdive_id").count()
            print(f"    {phen_table}: {covered:,} of our matched BacDive strains have rows", flush=True)
        except Exception as e:
            print(f"    {phen_table}: failed ({type(e).__name__})", flush=True)
except Exception as e:
    print(f"  strain join failed: {e}", flush=True)

# Stage 4 fixed: NMDC via NCBI taxid bridge
print("\n--- Stage 4 (fixed): NMDC taxonomy_features via NCBI taxid bridge ---", flush=True)

# Get our species' NCBI taxids from gtdb_metadata
print("  pulling NCBI taxids for our 18,989 species reps from gtdb_metadata...", flush=True)
gtdb_meta = spark.table("kbase_ke_pangenome.gtdb_metadata")
print(f"  gtdb_metadata schema sample: ncbi_taxid candidate columns:", flush=True)
sample_cols = [c for c in gtdb_meta.columns if 'taxid' in c.lower() or 'taxon' in c.lower()]
print(f"    {sample_cols}", flush=True)

species_sdf = spark.createDataFrame(species[["representative_genome_id", "gtdb_species_clade_id"]])
joined_taxid = species_sdf.join(F.broadcast(gtdb_meta.select("accession", "ncbi_taxid", "ncbi_species_taxid")),
                                  species_sdf["representative_genome_id"] == gtdb_meta["accession"],
                                  "left")
taxid_df = joined_taxid.select("gtdb_species_clade_id", "ncbi_taxid", "ncbi_species_taxid").toPandas()
print(f"  taxid coverage: ncbi_taxid non-null = {taxid_df['ncbi_taxid'].notna().sum():,}; "
      f"ncbi_species_taxid non-null = {taxid_df['ncbi_species_taxid'].notna().sum():,}", flush=True)

our_taxids = set(taxid_df["ncbi_taxid"].dropna().astype(str).astype(str).str.replace(r"\.0$", "", regex=True))
our_species_taxids = set(taxid_df["ncbi_species_taxid"].dropna().astype(str).str.replace(r"\.0$", "", regex=True))
print(f"  distinct ncbi_taxids (genome-level): {len(our_taxids):,}", flush=True)
print(f"  distinct ncbi_species_taxids: {len(our_species_taxids):,}", flush=True)

# Get NMDC taxonomy_features columns (NCBI taxids)
nmdc_tax = spark.table("nmdc_arkin.taxonomy_features")
nmdc_taxids = set(c for c in nmdc_tax.columns if c.isdigit())
print(f"  NMDC taxonomy_features taxid columns: {len(nmdc_taxids):,}", flush=True)
overlap_genome = our_taxids & nmdc_taxids
overlap_species = our_species_taxids & nmdc_taxids
print(f"  overlap (genome-level taxids): {len(overlap_genome):,}", flush=True)
print(f"  overlap (species-level taxids): {len(overlap_species):,}", flush=True)
nmdc_pct = 100 * len(overlap_species) / len(our_species_clade_ids)
print(f"  → {nmdc_pct:.1f}% of our P1B species have NCBI species-taxid overlap with NMDC samples", flush=True)

# Read existing audit, merge in fixes
audit_path = DATA_DIR / "p4d1_feasibility_audit.json"
with open(audit_path) as f:
    audit = json.load(f)

audit["bacdive_coverage"] = {
    "species_with_match": int(bd_stats["species_with_bacdive_match"]),
    "genomes_matched": int(bd_stats["genomes_matched"]),
    "total_bacdive_seq_rows": int(total_bd),
}
audit["bacdive_species_pct"] = round(bd_pct, 2)
audit["nmdc_taxid_bridge"] = {
    "n_our_taxids_genome": len(our_taxids),
    "n_our_taxids_species": len(our_species_taxids),
    "n_nmdc_taxid_columns": len(nmdc_taxids),
    "overlap_species_taxids": len(overlap_species),
    "overlap_genome_taxids": len(overlap_genome),
    "species_pct_in_nmdc": round(nmdc_pct, 2),
}

# Decision
gtdb_iso_pct = audit["gtdb_isolation_source_pct"]
print(f"\n--- DECISION ---", flush=True)
print(f"GTDB isolation_source: {gtdb_iso_pct:.1f}% (workhorse)", flush=True)
print(f"BacDive accession-level: {bd_pct:.1f}%", flush=True)
print(f"NMDC species-taxid overlap: {nmdc_pct:.1f}%", flush=True)
print(f"Fitness Browser: 0.18% (point validation only)", flush=True)

# Compute "non-trivial isolation source" coverage (drop the 'none' entries)
sources_minus_none = sum(s["count"] for s in audit["top_isolation_sources"] if s["ncbi_isolation_source"] != "none")
total_iso = audit["gtdb_metadata_coverage"]["with_isolation_source"]
audit["gtdb_isolation_source_meaningful_pct_estimate"] = round(100 * (total_iso - 4824) / 18989, 2)
print(f"GTDB isolation_source (excl. 'none'): ~{audit['gtdb_isolation_source_meaningful_pct_estimate']:.1f}%", flush=True)

decision = {
    "go_no_go": "GO with scoped scope: GTDB isolation_source as primary environment substrate (~74% meaningful coverage); BacDive secondary phenotype anchor for type-strain species; NMDC for sample-level enrichment in well-covered species; Fitness Browser as 30-organism point-validation only",
    "primary_substrate": "kbase_ke_pangenome.gtdb_metadata.ncbi_isolation_source",
    "scope_down_from_v2_9": "do not attempt MGnify (no audit done; deferred); reduce Fitness Browser scope from atlas-wide to 30-organism point-validation",
}
audit["decision"] = decision

with open(audit_path, "w") as f:
    json.dump(audit, f, indent=2, default=str)
print(f"\nUpdated p4d1_feasibility_audit.json", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
