"""
Species-level niche breadth sensitivity analysis.

Reads vsearch SINTAX output, queries Spark for OTU counts, computes
Levins' B_std per GTDB species, merges genus-level KO density, and runs
a within-genus linear mixed model.

Outputs
-------
data/otu_to_species_classification.csv   (OTU → species mapping)
data/species_level_niche_breadth.csv     (species B_std + metadata)
data/species_level_pgls_results.csv      (mixed-model results)
"""

import os, sys
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA    = PROJECT / 'data'

SINTAX_TSV  = DATA / 'otu_to_species_classification.tsv'
PGLS_INPUT  = DATA / 'soil_sample_pgls_dataset.csv'
OUT_MAP     = DATA / 'otu_to_species_classification.csv'
OUT_NICHE   = DATA / 'species_level_niche_breadth.csv'
OUT_PGLS    = DATA / 'species_level_pgls_results.csv'

MIN_OTUS_PER_SPECIES   = 5
MIN_SAMPLES_PER_SPECIES = 5

# ---------------------------------------------------------------------------
# Step 1: Parse SINTAX output → OTU → GTDB species + genus
# ---------------------------------------------------------------------------
print("Step 1: Parsing SINTAX output …")

records = []
with open(SINTAX_TSV) as f:
    for line in f:
        parts = line.rstrip('\n').split('\t')
        otu_id  = parts[0]
        tax_str = parts[3] if len(parts) > 3 else ''  # cutoff-filtered taxonomy

        if not tax_str or 's:' not in tax_str:
            continue  # no species-level hit at ≥0.8 confidence

        # Parse "d:Bacteria,p:X,...,g:Genus,s:Species"
        taxa = {}
        for token in tax_str.split(','):
            if ':' in token:
                rank, name = token.split(':', 1)
                taxa[rank.strip()] = name.strip().replace(' ', '_')

        species = taxa.get('s', '')
        genus   = taxa.get('g', '')
        if not species or not genus:
            continue

        records.append({'otu_id': otu_id, 'gtdb_species': species, 'gtdb_genus': genus})

otu_map = pd.DataFrame(records)
print(f"  OTUs with species classification: {len(otu_map):,}")
print(f"  Distinct species: {otu_map['gtdb_species'].nunique():,}")
print(f"  Distinct genera:  {otu_map['gtdb_genus'].nunique():,}")

# Filter to species with ≥ MIN_OTUS_PER_SPECIES OTUs
species_otu_counts = otu_map['gtdb_species'].value_counts()
valid_species = species_otu_counts[species_otu_counts >= MIN_OTUS_PER_SPECIES].index
otu_map_filtered = otu_map[otu_map['gtdb_species'].isin(valid_species)].copy()
print(f"  Species with ≥{MIN_OTUS_PER_SPECIES} OTUs: {len(valid_species):,}  "
      f"({len(otu_map_filtered):,} OTUs)")

otu_map_filtered.to_csv(OUT_MAP, index=False)
print(f"  Saved → {OUT_MAP}")

# ---------------------------------------------------------------------------
# Step 2: Spark — get OTU counts for classified OTUs
# ---------------------------------------------------------------------------
print("\nStep 2: Querying Spark for OTU sample counts …")

try:
    from berdl_notebook_utils import get_spark_session
    spark = get_spark_session()
except Exception:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()

# Verify otu_id format in otu_counts_long
sample_otus = spark.sql(
    "SELECT DISTINCT otu_id FROM arkinlab.microbeatlas.otu_counts_long LIMIT 5"
).toPandas()
print(f"  Sample otu_ids from Spark: {sample_otus['otu_id'].tolist()}")

# Upload OTU→species map as temp view
otu_spark = spark.createDataFrame(otu_map_filtered[['otu_id', 'gtdb_species', 'gtdb_genus']])
otu_spark.createOrReplaceTempView('species_otus')

# Join counts with species map; aggregate to species × sample
counts_df = spark.sql("""
    SELECT
        s.gtdb_species,
        s.gtdb_genus,
        c.sample_id,
        SUM(c.count)     AS species_count
    FROM arkinlab.microbeatlas.otu_counts_long c
    JOIN species_otus s ON c.otu_id = s.otu_id
    WHERE c.count > 0
    GROUP BY s.gtdb_species, s.gtdb_genus, c.sample_id
""").toPandas()

spark.stop()
print(f"  Species × sample rows: {len(counts_df):,}")
print(f"  Distinct species in counts: {counts_df['gtdb_species'].nunique():,}")

# ---------------------------------------------------------------------------
# Step 3: Compute Levins' B_std per species
# ---------------------------------------------------------------------------
print("\nStep 3: Computing Levins' B_std per species …")

def levins_b_std(counts: pd.Series) -> tuple:
    """Return (B_raw, B_std, n_samples) for a species count vector."""
    counts = counts[counts > 0]
    n = len(counts)
    if n < 1:
        return np.nan, np.nan, 0
    p = counts / counts.sum()  # relative abundance across samples (row-normalise)
    B = 1.0 / (p ** 2).sum()
    B_std = (B - 1.0) / (n - 1.0) if n > 1 else 0.0
    return B, B_std, n

results = []
for species, grp in counts_df.groupby('gtdb_species'):
    B, B_std, n_samples = levins_b_std(grp['species_count'])
    gtdb_genus = grp['gtdb_genus'].iloc[0]
    n_otus = int(otu_map_filtered.loc[
        otu_map_filtered['gtdb_species'] == species, 'otu_id'
    ].nunique())
    results.append({
        'gtdb_species': species,
        'gtdb_genus': gtdb_genus,
        'gtdb_genus_lower': gtdb_genus.lower(),
        'n_otus': n_otus,
        'n_samples': n_samples,
        'levins_B': B,
        'levins_B_std': B_std,
    })

niche_df = pd.DataFrame(results)

# Apply sample filter
niche_df = niche_df[niche_df['n_samples'] >= MIN_SAMPLES_PER_SPECIES].copy()
print(f"  Species after ≥{MIN_SAMPLES_PER_SPECIES} samples filter: {len(niche_df):,}")
print(f"  B_std mean={niche_df['levins_B_std'].mean():.3f}  "
      f"sd={niche_df['levins_B_std'].std():.3f}  "
      f"range=[{niche_df['levins_B_std'].min():.3f}, {niche_df['levins_B_std'].max():.3f}]")

# ---------------------------------------------------------------------------
# Step 4: Merge genus-level KO density
# ---------------------------------------------------------------------------
print("\nStep 4: Merging genus-level KO density …")

import re

pgls_input = pd.read_csv(PGLS_INPUT)
pgls_set = set(pgls_input['genus_lower'].str.lower().str.strip())

def resolve_genus(gtdb_genus: str) -> str:
    """Map GTDB genus name to MicrobeAtlas genus name.

    GTDB renames many genera by appending a suffix (_A, _B, _M, _1, etc.)
    to disambiguate. Try: exact match → strip trailing _[A-Z0-9]+ suffix.
    """
    base = gtdb_genus.lower().strip()
    if base in pgls_set:
        return base
    stripped = re.sub(r'_[A-Z0-9]+$', '', gtdb_genus, flags=re.IGNORECASE).lower().strip()
    if stripped in pgls_set:
        return stripped
    return base  # no match; keep original for merge (will not join)

niche_df['genus_lower_key'] = niche_df['gtdb_genus'].apply(resolve_genus)
pgls_input['genus_lower_key'] = pgls_input['genus_lower'].str.lower().str.strip()

merged = niche_df.merge(
    pgls_input[['genus_lower_key', 'ko_per_mb_primary', 'ko_per_mb_primary_z',
                'cofactor_per_mb_z', 'resistance_per_mb_z',
                'genome_size_mb_z', 'mean_genome_mb', 'phylum', 'kingdom']],
    on='genus_lower_key', how='inner'
)
print(f"  Species with genus KO density match: {len(merged):,} "
      f"({merged['gtdb_genus'].nunique():,} genera)")

# Z-score species-level B_std for comparability
merged['B_std_z'] = (merged['levins_B_std'] - merged['levins_B_std'].mean()) / \
                     merged['levins_B_std'].std(ddof=1)

merged.to_csv(OUT_NICHE, index=False)
print(f"  Saved → {OUT_NICHE}")

# ---------------------------------------------------------------------------
# Step 5: Within-genus linear mixed model
# ---------------------------------------------------------------------------
print("\nStep 5: Running within-genus linear mixed model …")

import statsmodels.formula.api as smf
from scipy import stats

model_results = []

def run_lme(df, response, predictor, label):
    sub = df[['gtdb_genus', response, predictor]].dropna()
    # Require ≥2 species per genus for within-genus variance
    genus_counts = sub['gtdb_genus'].value_counts()
    sub = sub[sub['gtdb_genus'].isin(genus_counts[genus_counts >= 2].index)].copy()
    n = len(sub)
    n_genera = sub['gtdb_genus'].nunique()
    if n < 20:
        return {'label': label, 'n': n, 'n_genera': n_genera,
                'error': f'n={n} too small', 'converged': False}
    # z-score predictor within the regression
    sub[f'{predictor}_z'] = (sub[predictor] - sub[predictor].mean()) / sub[predictor].std(ddof=1)
    try:
        model = smf.mixedlm(f"{response} ~ {predictor}_z",
                             sub, groups=sub['gtdb_genus']).fit(reml=True)
        beta = model.fe_params[f'{predictor}_z']
        se   = model.bse[f'{predictor}_z']
        t    = model.tvalues[f'{predictor}_z']
        p    = model.pvalues[f'{predictor}_z']
        return {
            'label': label, 'n_species': n, 'n_genera': n_genera,
            'beta': round(beta, 5), 'SE': round(se, 5),
            't': round(t, 3), 'p_value': p,
            'converged': model.converged,
        }
    except Exception as e:
        return {'label': label, 'n': n, 'n_genera': n_genera,
                'error': str(e), 'converged': False}

# Model 1: total KO density
r1 = run_lme(merged, 'levins_B_std', 'ko_per_mb_primary', 'M1_total_KO')
print(f"  M1 (total KO):     β={r1.get('beta','?'):+.4f}  "
      f"p={r1.get('p_value','?'):.3e}  n={r1.get('n_species','?')}  "
      f"genera={r1.get('n_genera','?')}")
model_results.append(r1)

# Model 2: cofactor vs resistance split
def fmt(r, key, fmt_spec):
    v = r.get(key)
    return f"{v:{fmt_spec}}" if v is not None and not isinstance(v, str) else str(v)

r2a = run_lme(merged, 'levins_B_std', 'cofactor_per_mb_z', 'M2a_cofactor')
r2b = run_lme(merged, 'levins_B_std', 'resistance_per_mb_z', 'M2b_resistance')
print(f"  M2a (cofactor):    β={fmt(r2a,'beta','+.4f')}  p={fmt(r2a,'p_value','.3e')}")
print(f"  M2b (resistance):  β={fmt(r2b,'beta','+.4f')}  p={fmt(r2b,'p_value','.3e')}")
model_results.extend([r2a, r2b])

# Model 3: cofactor + resistance jointly (split test)
sub3 = merged[['gtdb_genus', 'levins_B_std', 'cofactor_per_mb_z', 'resistance_per_mb_z']].dropna()
genus_counts3 = sub3['gtdb_genus'].value_counts()
sub3 = sub3[sub3['gtdb_genus'].isin(genus_counts3[genus_counts3 >= 2].index)].copy()
try:
    m3 = smf.mixedlm(
        "levins_B_std ~ cofactor_per_mb_z + resistance_per_mb_z",
        sub3, groups=sub3['gtdb_genus']
    ).fit(reml=True)
    r3 = {
        'label': 'M3_joint',
        'n_species': len(sub3), 'n_genera': sub3['gtdb_genus'].nunique(),
        'beta_cofactor':    round(m3.fe_params['cofactor_per_mb_z'], 5),
        'p_cofactor':       m3.pvalues['cofactor_per_mb_z'],
        'beta_resistance':  round(m3.fe_params['resistance_per_mb_z'], 5),
        'p_resistance':     m3.pvalues['resistance_per_mb_z'],
        'converged':        m3.converged,
    }
    print(f"  M3 joint:  β_cofactor={r3['beta_cofactor']:+.4f}  p={r3['p_cofactor']:.3e}  "
          f"β_resist={r3['beta_resistance']:+.4f}  p={r3['p_resistance']:.3e}")
except Exception as e:
    r3 = {'label': 'M3_joint', 'error': str(e), 'converged': False}
    print(f"  M3 joint failed: {e}")
model_results.append(r3)

pd.DataFrame(model_results).to_csv(OUT_PGLS, index=False)
print(f"\n  Saved → {OUT_PGLS}")
print("\nDone.")
