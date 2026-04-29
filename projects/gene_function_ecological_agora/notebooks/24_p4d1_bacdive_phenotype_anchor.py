"""NB24 / P4-D1 — BacDive phenotype anchoring.

For the 6,053 P1B species reps with BacDive matches (via GCF→GCA fallback in NB22d),
pull metabolite_utilization, physiology, and enzyme tables. Aggregate per focal clade
and test phenotype alignment with pre-registered biology:

  - NB12 Mycobacteriaceae × mycolic-acid: matched species should show
    acid-fast / aerobic / lipid-utilization phenotypes
  - NB16 Cyanobacteriia × PSII: matched species should show photosynthetic /
    autotrophic / aerobic phenotypes
  - Phase 1B Bacteroidota × PUL: matched species should show anaerobic /
    saccharolytic / polysaccharide-utilization phenotypes

Also: atlas-wide phenotype landscape per phylum (top-10 phyla).

Skipping isolation + culture_condition tables due to known data-quality CAST
errors (embedded quotes in numeric columns) flagged in NB22d; metabolite_utilization,
physiology, enzyme are clean.

Outputs:
  data/p4d1_bacdive_phenotype_per_species.parquet — per-species phenotype profile
  data/p4d1_bacdive_focal_clades.tsv — focal clade phenotype summary
  data/p4d1_bacdive_diagnostics.json
  figures/p4d1_bacdive_phenotype_panel.png
"""
import json, time
from pathlib import Path
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"

t0 = time.time()
print("=== NB24 / P4-D1 — BacDive phenotype anchor ===", flush=True)

species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
species["clean_no_version"] = species["representative_genome_id"].str.replace(r"^(GB_|RS_)", "", regex=True).str.replace(r"\.\d+$", "", regex=True)
species["clean_as_gca"] = species["clean_no_version"].str.replace(r"^GCF_", "GCA_", regex=True)

spark = get_spark_session()

# Stage 1: build clean species → bacdive_id mapping
print("\nStage 1: build species → bacdive_id mapping", flush=True)
bd_seq = spark.table("kescience_bacdive.sequence_info").filter(F.col("accession_type") == "genome").select("accession", "bacdive_id")
species_sdf = spark.createDataFrame(species[["clean_as_gca", "gtdb_species_clade_id", "GTDB_species", "genus", "family", "order", "class", "phylum"]])
mapping = species_sdf.join(F.broadcast(bd_seq), species_sdf["clean_as_gca"] == bd_seq["accession"]).drop("accession")
mapping_pd = mapping.toPandas()
print(f"  matched bacdive_ids: {len(mapping_pd):,} unique gtdb_species×bacdive_id pairs", flush=True)
matched_bd_ids = set(mapping_pd["bacdive_id"].dropna().astype(int))
print(f"  distinct bacdive_ids: {len(matched_bd_ids):,}", flush=True)

# Stage 2: pull each phenotype table for matched bacdive_ids
print("\nStage 2: pull phenotype tables", flush=True)
matched_bd_sdf = spark.createDataFrame(pd.DataFrame({"bacdive_id": list(matched_bd_ids)}))

phenotype_data = {}
for tab in ["metabolite_utilization", "physiology", "enzyme"]:
    print(f"\n  table: kescience_bacdive.{tab}")
    t = spark.table(f"kescience_bacdive.{tab}")
    print(f"    columns: {t.columns}")
    sub = t.join(F.broadcast(matched_bd_sdf), "bacdive_id")
    pd_sub = sub.toPandas()
    print(f"    rows for our species: {len(pd_sub):,}")
    phenotype_data[tab] = pd_sub

# Stage 3: aggregate phenotype per species
print("\nStage 3: aggregate phenotype per species", flush=True)
mut = phenotype_data["metabolite_utilization"]
phys = phenotype_data["physiology"]
enz = phenotype_data["enzyme"]

print(f"\n  metabolite_utilization columns: {mut.columns.tolist()}", flush=True)
print(f"  physiology columns: {phys.columns.tolist()}", flush=True)
print(f"  enzyme columns: {enz.columns.tolist()}", flush=True)

# Merge mapping (1:N if a species has multiple bacdive_id matches we'd see duplicates)
mut_x = mut.merge(mapping_pd[["bacdive_id", "gtdb_species_clade_id", "phylum", "family", "class", "genus"]], on="bacdive_id")
phys_x = phys.merge(mapping_pd[["bacdive_id", "gtdb_species_clade_id", "phylum", "family", "class", "genus"]], on="bacdive_id")
enz_x = enz.merge(mapping_pd[["bacdive_id", "gtdb_species_clade_id", "phylum", "family", "class", "genus"]], on="bacdive_id")

# Stage 4: focal clade phenotype summaries
print("\nStage 4: focal clade phenotype summaries", flush=True)

def top_phenotypes(df, focal_filter, value_col, top_n=15):
    """Return top phenotype values for a focal-clade filtered subset."""
    sub = df[focal_filter]
    if len(sub) == 0 or value_col not in sub.columns:
        return pd.Series(dtype=int)
    vc = sub[value_col].value_counts().head(top_n)
    return vc

focal_clades = {
    "Mycobacteriaceae": phys_x["family"] == "f__Mycobacteriaceae",
    "Cyanobacteriia": phys_x["class"] == "c__Cyanobacteriia",
    "Bacteroidota": phys_x["phylum"] == "p__Bacteroidota",
}

clade_summaries = {}
for clade_name, focal_filter in focal_clades.items():
    print(f"\n--- {clade_name} ---", flush=True)
    clade_summaries[clade_name] = {}
    for label, df, col_candidates in [
        ("physiology", phys_x, ["chebi_name", "value", "metabolite", "ability"]),
        ("metabolite_utilization", mut_x, ["chebi_name", "metabolite_name", "ability"]),
        ("enzyme", enz_x, ["ec_number", "enzyme_name"]),
    ]:
        sub_focal = focal_filter if df is phys_x else (
            (df["family"] == "f__Mycobacteriaceae") if clade_name == "Mycobacteriaceae"
            else (df["class"] == "c__Cyanobacteriia") if clade_name == "Cyanobacteriia"
            else (df["phylum"] == "p__Bacteroidota")
        )
        sub = df[sub_focal]
        n_species_with_data = sub["gtdb_species_clade_id"].nunique()
        # Find the actual column to use
        col = None
        for c in col_candidates:
            if c in sub.columns:
                col = c; break
        if col is None:
            print(f"  {label}: no usable column among {col_candidates}; available={sub.columns.tolist()}")
            continue
        vc = sub[col].value_counts().head(15)
        print(f"  {label} (col={col}, n_species={n_species_with_data}, n_rows={len(sub)}):")
        for v, n in vc.items():
            print(f"    {v}: {n}")
        clade_summaries[clade_name][label] = {"col": col, "top": vc.to_dict(), "n_species_with_data": int(n_species_with_data)}

# Save
for tab_name, df_x in [("metabolite_utilization", mut_x), ("physiology", phys_x), ("enzyme", enz_x)]:
    outpath = DATA_DIR / f"p4d1_bacdive_{tab_name}_per_species.parquet"
    df_x.to_parquet(outpath, index=False)
    print(f"\nSaved {outpath}", flush=True)

diagnostics = {
    "phase": "4", "deliverable": "P4-D1 NB24",
    "purpose": "BacDive phenotype anchoring for pre-registered atlas findings",
    "n_matched_bacdive_ids": int(len(matched_bd_ids)),
    "n_metabolite_utilization_rows": int(len(mut_x)),
    "n_physiology_rows": int(len(phys_x)),
    "n_enzyme_rows": int(len(enz_x)),
    "focal_clade_phenotype_summaries": clade_summaries,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d1_bacdive_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"\nWrote p4d1_bacdive_diagnostics.json", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
