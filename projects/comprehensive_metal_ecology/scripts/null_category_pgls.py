"""
null_category_pgls.py
=====================
Q1 (Exploratory): PGLS of per-Mb KO density vs niche breadth for five null
KEGG functional categories that a priori should NOT be associated with metal
niche breadth (ABC transporters, AMR, glycan biosynthesis, cell motility,
two-component systems).

Uses the same kescience_mgnify Spark query as NB18 Block 2.
Outputs data/null_category_pgls_results.csv.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

from pgls_utils import run_pgls
from berdl_notebook_utils import get_spark_session

TREE = DATA / "gtdb_bac_genus_pruned.tree"
PGLS_INPUT = DATA / "01_pgls_input_bacteria.csv"
NULL_KEYS = ["abc_transporters", "amr", "glycan_biosyn", "cell_motility", "two_component"]
MIN_GENERA = 100

# ---------------------------------------------------------------------------
# Load authoritative KO lists from NB18
# ---------------------------------------------------------------------------

NB18 = ROOT / "notebooks" / "18_functional_landscape.ipynb"
print(f"Loading KEGG_CATEGORIES from {NB18.name}...")
with open(NB18) as f:
    nb = json.load(f)

KEGG_CATS = {}
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if "KEGG_CATEGORIES" in src and "def " not in src and "import" not in src[:50]:
        ns = {}
        try:
            exec(src, ns)
            if "KEGG_CATEGORIES" in ns:
                KEGG_CATS = ns["KEGG_CATEGORIES"]
                break
        except Exception:
            continue

if not KEGG_CATS:
    raise RuntimeError("Could not load KEGG_CATEGORIES from NB18")

NULL_CATEGORIES = {k: KEGG_CATS[k] for k in NULL_KEYS if k in KEGG_CATS}
print(f"Null categories: { {k: len(v) for k, v in NULL_CATEGORIES.items()} }")

# ---------------------------------------------------------------------------
# Spark session
# ---------------------------------------------------------------------------
print("Connecting to Spark...")
spark = get_spark_session()

def compute_ko_density(ko_ids_list):
    """Per-genus KO density (KOs per Mb) from kescience_mgnify.genome + gene_eggnog."""
    ko_prefixed = [f"ko:{k}" for k in ko_ids_list]
    quoted = ", ".join(f"'{k}'" for k in ko_prefixed)
    sql = f"""
        SELECT gm.genome_id,
               regexp_extract(gm.lineage, 'g__([^;]+)', 1) AS genus,
               COUNT(DISTINCT koid.ko)                      AS n_ko,
               gm.length                                    AS genome_length_bp
        FROM kescience_mgnify.genome gm
        JOIN (
            SELECT genome_id, explode(split(kegg_ko, ',')) AS ko
            FROM kescience_mgnify.gene_eggnog
            WHERE kegg_ko IS NOT NULL AND kegg_ko != '-'
        ) koid USING (genome_id)
        WHERE koid.ko IN ({quoted})
        GROUP BY gm.genome_id, gm.lineage, gm.length
    """
    pm = spark.sql(sql).toPandas()
    pm["genus_lower"] = pm["genus"].str.lower().str.strip()
    pm["ko_per_mb"]   = pm["n_ko"] / (pm["genome_length_bp"] / 1e6)
    gk = (pm.groupby("genus_lower", as_index=False)
            .agg(ko_per_mb=("ko_per_mb", "mean"), n_mags=("genome_id", "count")))
    return gk

# ---------------------------------------------------------------------------
# Load PGLS base data
# ---------------------------------------------------------------------------
pgls_input = pd.read_csv(PGLS_INPUT)
print(f"PGLS input: {len(pgls_input)} genera")

# ---------------------------------------------------------------------------
# Per-category density + PGLS
# ---------------------------------------------------------------------------
results = []

for cat_key, ko_list in NULL_CATEGORIES.items():
    print(f"\n--- {cat_key} ({len(ko_list)} KOs) ---")

    density_csv = DATA / f"landscape_{cat_key}_density.csv"
    if density_csv.exists():
        print(f"  Using cached density: {density_csv.name}")
        density_df = pd.read_csv(density_csv)
    else:
        print("  Querying Spark (this may take a few minutes)...")
        density_df = compute_ko_density(ko_list)
        density_df.to_csv(density_csv, index=False)
        print(f"  Saved: {density_csv.name} ({len(density_df)} genera)")

    merged = pgls_input.merge(density_df[["genus_lower", "ko_per_mb"]],
                              on="genus_lower", how="inner")
    print(f"  Genera with density: {len(merged)}")

    if len(merged) < MIN_GENERA:
        status = f"SKIP: {len(merged)} genera < {MIN_GENERA} minimum"
        results.append({
            "category": cat_key, "n_kos": len(ko_list), "n_genera": len(merged),
            "beta": np.nan, "SE": np.nan, "p_value": np.nan,
            "lambda_est": np.nan, "n_pgls": np.nan, "status": status,
        })
        print(f"  {status}")
        continue

    merged = merged.copy()
    mu, sd = merged["ko_per_mb"].mean(), merged["ko_per_mb"].std()
    merged["pred_z"] = (merged["ko_per_mb"] - mu) / sd

    print("  Running PGLS...")
    try:
        res = run_pgls(
            merged,
            tree_path=TREE,
            response="mean_levins_B_std",
            predictors=["pred_z"],
            taxon_col="genus_lower",
            label=f"null_{cat_key}",
            min_n=30,
        )
        beta  = float(res["beta"])
        se    = float(res["SE"])
        pval  = float(res["p_value"])
        lam   = float(res["lambda_est"])
        n_fit = int(res["n"])
        status = "OK"
        print(f"  beta={beta:.4f}  SE={se:.4f}  p={pval:.4e}  lambda={lam:.3f}  n={n_fit}")
    except Exception as exc:
        beta = se = pval = lam = np.nan
        n_fit = 0
        status = f"ERROR: {exc}"
        print(f"  PGLS error: {exc}")

    results.append({
        "category": cat_key, "n_kos": len(ko_list), "n_genera": len(merged),
        "beta": beta, "SE": se, "p_value": pval,
        "lambda_est": lam, "n_pgls": n_fit, "status": status,
    })

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out = pd.DataFrame(results)
out_path = DATA / "null_category_pgls_results.csv"
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(out[["category", "n_kos", "n_pgls", "beta", "SE", "p_value", "status"]].to_string(index=False))
