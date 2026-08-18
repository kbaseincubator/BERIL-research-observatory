"""
silva_genus_niche_breadth.py
---
Compute Levins' B_std per genus using the SILVA taxonomy from
~/projects/microbeatlas/otus.silva.csv and compare coverage to the existing
mean_levins_B_std in data/soil_sample_pgls_dataset.csv.

If coverage is comparable or better, reruns the primary PGLS
(mean_levins_B_std ~ ko_per_mb_primary_z + genome_size_mb_z) and the
cofactor/resistance split using the new B_std as the response.

Outputs
-------
data/silva_genus_niche_breadth.csv   (per-genus: new B_std + existing PGLS cols)
data/silva_genus_pgls_results.csv    (PGLS results vs P1 reference)
"""

import os, sys, re
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT  = Path(__file__).resolve().parent.parent
DATA     = PROJECT / 'data'
SILVA_CSV = Path('/home/hmacgregor/projects/microbeatlas/otus.silva.csv')
PGLS_CSV  = DATA / 'soil_sample_pgls_dataset.csv'
TREE_PATH = (PROJECT.parent
             / 'microbeatlas_metal_ecology'
             / 'data'
             / 'gtdb_bac_genus_pruned.tree')

OUT_NICHE = DATA / 'silva_genus_niche_breadth.csv'
OUT_PGLS  = DATA / 'silva_genus_pgls_results.csv'

MIN_SAMPLES_PER_GENUS = 10   # same threshold as main analysis

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Parse otus.silva.csv → {otu_97 → silva_genus_lower}
# ─────────────────────────────────────────────────────────────────────────────
print("Step 1: Parsing otus.silva.csv …")

EXCLUDE = re.compile(
    r'uncultured|unidentified|metagenome|unclassified|unknown|'
    r'incertae\s*sedis|sp\.',
    re.IGNORECASE
)

otu_genus: dict[str, str] = {}

with open(SILVA_CSV) as fh:
    fh.readline()  # skip header
    for line in fh:
        line = line.rstrip('\n')
        if not line:
            continue
        try:
            otu_field, tax_field = line.split(',', 1)
        except ValueError:
            continue

        # Only Bacteria (the PGLS tree is bacteria-only)
        if not tax_field.startswith('Bacteria'):
            continue

        # Extract 97_XXXXX from semicolon-delimited multi-level OTU ID
        otu97 = None
        for part in otu_field.split(';'):
            if part.startswith('97_'):
                otu97 = part
                break
        if otu97 is None or otu97 in otu_genus:
            continue  # already seen this OTU → take first occurrence

        # Genus is the 6th field (0-indexed: index 5)
        tax_parts = tax_field.split(';')
        if len(tax_parts) < 6:
            continue
        genus_raw = tax_parts[5].strip()

        if not genus_raw:
            continue
        if EXCLUDE.search(genus_raw):
            continue

        # Strip "Candidatus " prefix (PGLS dataset uses bare name)
        genus_clean = re.sub(r'^Candidatus\s+', '', genus_raw, flags=re.IGNORECASE)
        # Keep only single-word genera (multi-word = informal clade name)
        if ' ' in genus_clean or '[' in genus_clean:
            continue

        otu_genus[otu97] = genus_clean.lower()

otu_df = pd.DataFrame(
    {'otu_id': list(otu_genus.keys()), 'genus_lower': list(otu_genus.values())}
)

print(f"  OTUs with valid SILVA genus: {len(otu_df):,}")
print(f"  Distinct genera:             {otu_df['genus_lower'].nunique():,}")

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Spark: aggregate OTU counts to genus × sample
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 2: Querying Spark …")

try:
    from berdl_notebook_utils import get_spark_session
    spark = get_spark_session()
except Exception:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()

otu_spark = spark.createDataFrame(otu_df)
otu_spark.createOrReplaceTempView('silva_otus')

# Compute Levins' B_std inside Spark to avoid pulling genus×sample rows to driver.
# Formula: B = 1/Σ(p²); p = genus_count/genus_total; B_std = (B−1)/(n_samples−1)
niche_spark = spark.sql(f"""
    WITH gs AS (
        SELECT s.genus_lower,
               c.sample_id,
               SUM(c.count) AS gs_count
        FROM   arkinlab.microbeatlas.otu_counts_long c
        JOIN   silva_otus s ON c.otu_id = s.otu_id
        WHERE  c.count > 0
        GROUP BY s.genus_lower, c.sample_id
    ),
    totals AS (
        SELECT genus_lower,
               SUM(gs_count)  AS genus_total,
               COUNT(*)        AS n_samples
        FROM   gs
        GROUP BY genus_lower
    )
    SELECT
        g.genus_lower,
        t.n_samples,
        1.0 / SUM(POWER(g.gs_count / CAST(t.genus_total AS DOUBLE), 2)) AS levins_B,
        (1.0 / SUM(POWER(g.gs_count / CAST(t.genus_total AS DOUBLE), 2)) - 1.0)
            / GREATEST(CAST(t.n_samples AS DOUBLE) - 1.0, 1.0)            AS silva_levins_B_std
    FROM   gs g
    JOIN   totals t ON g.genus_lower = t.genus_lower
    GROUP  BY g.genus_lower, t.n_samples
    HAVING t.n_samples >= {MIN_SAMPLES_PER_GENUS}
""").toPandas()

# OTU counts per genus (local)
n_otus_per_genus = otu_df['genus_lower'].value_counts().rename('n_otus_silva')
niche_spark = niche_spark.join(n_otus_per_genus, on='genus_lower', how='left')

spark.stop()

print(f"  Distinct genera (Spark): {niche_spark['genus_lower'].nunique():,}")
print(f"  Distinct samples (approx): from Spark query")

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Summarise
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 3: B_std summary …")

niche_df = niche_spark.copy()

print(f"  Genera after ≥{MIN_SAMPLES_PER_GENUS} samples: {len(niche_df):,}")
print(f"  B_std  mean={niche_df['silva_levins_B_std'].mean():.3f}  "
      f"sd={niche_df['silva_levins_B_std'].std():.3f}  "
      f"range=[{niche_df['silva_levins_B_std'].min():.3f}, "
      f"{niche_df['silva_levins_B_std'].max():.3f}]")

# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Compare coverage to existing PGLS dataset
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 4: Coverage comparison …")

pgls_input = pd.read_csv(PGLS_CSV)
main_n = len(pgls_input)
main_with_bstd = pgls_input['mean_levins_B_std'].notna().sum()

merged = niche_df.merge(pgls_input, on='genus_lower', how='inner')

n_matched = len(merged)
n_with_existing = merged['mean_levins_B_std'].notna().sum()
rho = (merged[['silva_levins_B_std', 'mean_levins_B_std']]
       .dropna()
       .corr()
       .iloc[0, 1])

print(f"  Main PGLS dataset genera:          {main_n:,}")
print(f"  … with existing mean_levins_B_std: {main_with_bstd:,}")
print(f"  SILVA B_std coverage (≥10 samples): {len(niche_df):,} genera total")
print(f"  Matched to PGLS dataset:           {n_matched:,} genera")
print(f"  … of which existing B_std present: {n_with_existing:,}")
print(f"  Spearman ρ (SILVA vs existing B_std): {rho:.3f}")

# Save merged file
merged.to_csv(OUT_NICHE, index=False)
print(f"  Saved → {OUT_NICHE}")

# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Run PGLS with SILVA B_std
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 5: Running PGLS with SILVA B_std …")

sys.path.insert(0, str(PROJECT))
from scripts.pgls_utils import run_pgls

pgls_in = merged.dropna(
    subset=['silva_levins_B_std', 'ko_per_mb_primary_z', 'genome_size_mb_z']
).copy()

def _b(res, key):
    return res.get('betas', {}).get(key, res.get('beta', float('nan')))

def _p(res, key):
    return res.get('p_values', {}).get(key, res.get('p_value', float('nan')))

# M1: primary replication of P1
res1 = run_pgls(
    pgls_in,
    tree_path=str(TREE_PATH),
    response='silva_levins_B_std',
    predictors=['ko_per_mb_primary_z', 'genome_size_mb_z'],
    label='M1_primary_silva',
)
print(f"\n  M1 (SILVA B_std ~ total KO + genome_size):")
print(f"    β_ko  = {_b(res1,'ko_per_mb_primary_z'):+.5f}")
print(f"    SE    = {res1['SEs']['ko_per_mb_primary_z']:.5f}")
print(f"    λ     = {res1['lambda_est']:.3f}")
print(f"    p     = {_p(res1,'ko_per_mb_primary_z'):.3e}")
print(f"    n     = {res1['n']}")
print(f"\n  P1 reference: β=−0.021, λ=0.757, p=2.1×10⁻⁸, n=1,574")

# M2: cofactor vs resistance split
pgls_split = merged.dropna(
    subset=['silva_levins_B_std', 'cofactor_per_mb_z',
            'resistance_per_mb_z', 'genome_size_mb_z']
).copy()

res2 = run_pgls(
    pgls_split,
    tree_path=str(TREE_PATH),
    response='silva_levins_B_std',
    predictors=['cofactor_per_mb_z', 'resistance_per_mb_z', 'genome_size_mb_z'],
    label='M2_split_silva',
)
print(f"\n  M2 (SILVA B_std ~ cofactor + resistance + genome_size):")
print(f"    β_cofactor  = {_b(res2,'cofactor_per_mb_z'):+.5f}  "
      f"p={_p(res2,'cofactor_per_mb_z'):.3e}")
print(f"    β_resistance= {_b(res2,'resistance_per_mb_z'):+.5f}  "
      f"p={_p(res2,'resistance_per_mb_z'):.3e}")
print(f"    λ           = {res2['lambda_est']:.3f}")
print(f"    n           = {res2['n']}")

# Save results
pd.DataFrame([res1, res2]).to_csv(OUT_PGLS, index=False)
print(f"\n  Saved → {OUT_PGLS}")
print("\nDone.")
