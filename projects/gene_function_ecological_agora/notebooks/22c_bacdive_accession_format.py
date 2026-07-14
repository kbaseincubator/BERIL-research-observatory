"""NB22c — diagnose BacDive accession format.

The previous audit returned 0 matches, which is suspicious given BacDive has 81,294
sequence_info rows (27,502 documented as GCA accessions per docs/schemas/bacdive.md
line 144). Likely a format-mismatch issue (version suffix, GCA vs GCF, etc.).
"""
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

spark = get_spark_session()
print("=== BacDive accession format diagnostic ===", flush=True)

bd = spark.table("kescience_bacdive.sequence_info")
print(f"bacdive sequence_info schema:")
bd.printSchema()
print(f"\ndistinct accession_types and counts:")
bd.groupBy("accession_type").count().show(20, truncate=False)
print(f"\nSample of accessions where accession_type is GCA-related:")
gca_like = bd.filter(F.col("accession").startswith("GCA")).select("accession", "accession_type", "database").limit(10)
gca_like.show(truncate=False)
print(f"\nSample of all accessions (mixed):")
bd.select("accession", "accession_type", "database").limit(20).show(truncate=False)

# Test with actual examples from our species
species = pd.read_csv("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data/p1b_full_species.tsv", sep="\t")
print(f"\nOur first 5 rep genome IDs:")
print(species["representative_genome_id"].head(10).tolist())

# Strip GB_/RS_ prefix
species["clean"] = species["representative_genome_id"].str.replace(r"^(GB_|RS_)", "", regex=True)
print(f"\nCleaned: {species['clean'].head(10).tolist()}")

# Check if version suffix matters
species["clean_no_version"] = species["clean"].str.replace(r"\.\d+$", "", regex=True)
print(f"\nNo-version: {species['clean_no_version'].head(10).tolist()}")

# Test one specific accession
test_acc = species["clean"].iloc[0]
test_acc_nv = species["clean_no_version"].iloc[0]
print(f"\nTest: bd accessions matching exact {test_acc}:")
bd.filter(F.col("accession") == test_acc).show(5, truncate=False)
print(f"\nTest: bd accessions LIKE {test_acc_nv}.%:")
bd.filter(F.col("accession").startswith(test_acc_nv)).show(5, truncate=False)
print(f"\nTest: bd accessions LIKE {test_acc_nv} (no version):")
bd.filter(F.col("accession") == test_acc_nv).show(5, truncate=False)
