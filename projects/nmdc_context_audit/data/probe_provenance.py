"""Characterize each real NMDC-labeled database: description, scale, currency.

Writes provenance_probe.md next to this script, regardless of the caller's
working directory. JVM stderr is noisy; run with 2>/dev/null.
"""
from pathlib import Path
from berdl_notebook_utils.setup_spark_session import get_spark_session

spark = get_spark_session()

# (db, [signature tables]) — dotted identifiers
TARGETS = {
    "nmdc.metadata": ["biosample_set", "study_set", "data_generation_set",
                       "workflow_execution_set", "functional_annotation_agg"],
    "nmdc.ncbi_biosamples": ["biosamples_flattened", "biosamples_attributes",
                             "bioprojects_flattened", "sra_biosamples_bioprojects"],
    "nmdc.ref_data": ["pfam_terms"],
    "nmdc.results": ["annotation_statistics", "gtdbtk_bacterial_summary",
                     "checkm_statistics", "annotation_kegg_orthology"],
    "kbase.nmdc_arkin": ["study_table", "taxonomy_dim", "embeddings_v1",
                         "sample_file_lookup", "metabolomics_gold", "omics_files_table"],
    "kbase.nmdc_mags": ["mag_catalog", "bin_catalog", "biosample_metadata", "study_sample"],
    "kbase.nmdc_neon": ["neon_mag_catalog", "sample_data", "study_sample"],
}

def q(sql):
    return spark.sql(sql).toPandas()

out = []
out.append("# NMDC Provenance Probe\n")

for db, tables in TARGETS.items():
    out.append(f"\n## `{db}`\n")
    # Database description / location / owner
    try:
        d = q(f"DESCRIBE DATABASE EXTENDED {db}")
        for _, row in d.iterrows():
            out.append(f"- **{row[0]}**: {row[1]}")
    except Exception as e:
        out.append(f"- (DESCRIBE DATABASE failed: {type(e).__name__}: {str(e)[:150]})")
    out.append("\n| table | rows | last_commit (Iceberg) |")
    out.append("|---|---:|---|")
    for t in tables:
        fq = f"{db}.{t}"
        # row count
        try:
            n = q(f"SELECT COUNT(*) c FROM {fq}").iloc[0]["c"]
            n = f"{int(n):,}"
        except Exception as e:
            n = f"ERR {str(e)[:40]}"
        # last commit via iceberg snapshots
        try:
            s = q(f"SELECT max(committed_at) m FROM {fq}.snapshots").iloc[0]["m"]
            s = str(s)
        except Exception:
            s = "n/a"
        out.append(f"| {t} | {n} | {s} |")

text = "\n".join(out)
out_path = Path(__file__).resolve().parent / "provenance_probe.md"
with open(out_path, "w") as f:
    f.write(text)
print(text)
