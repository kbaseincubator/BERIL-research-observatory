#!/usr/bin/env python3
"""
Spatial block CV comparison: pH vs taxonomy vs gene panel predictors of metal contamination.

Compares four prediction pipelines across 5-fold spatial block CV:
- P1: pH alone (baseline environmental)
- P2: Genus-level taxonomy (CLR on 200 genera)
- P3: Field-strict 31 KO gene panel (union across all metals)
- P4: pH + gene panel (combined)

Target: Metal contamination (continuous: log1p ppm for Cu/Zn/Pb/Ni)
Cross-validation: 5-fold spatial block CV (k-means geographic clusters)

REQUIREMENTS: Spark job to extract genus-level data from MAG feature matrix
and KO prevalence per sample. This script provides the scaffold.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("Spatial Block CV: pH vs Taxonomy vs Gene Panel")
print("="*70)

# ============================================================================
# PART 1: DATA LOADING
# ============================================================================

# Load existing feature matrix and spatial blocks
print("\n1. Loading feature matrix and spatial blocks...")
try:
    import pyarrow.parquet as pq
    feature_matrix_pq = pq.read_table(
        '/home/hmacgregor/BERIL-research-observatory/projects/community_composition_prediction/data/feature_matrix.parquet'
    )
    feature_matrix = feature_matrix_pq.to_pandas()
    print(f"   Loaded feature matrix: {feature_matrix.shape}")
except Exception as e:
    print(f"   ERROR loading parquet: {e}")
    print("   Will create scaffold with metadata only.")
    feature_matrix = None

# Load spatial blocks
spatial_blocks = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/community_composition_prediction/data/spatial_blocks.csv'
)
print(f"   Loaded spatial blocks: {spatial_blocks.shape}")
print(f"   Unique blocks: {spatial_blocks['block'].nunique()}")

# ============================================================================
# PART 2: SCAFFOLD FOR DATA LOADING (Spark-dependent)
# ============================================================================

print("\n2. Data loading scaffold (Spark-dependent):")
print("""
   TODO: Run in JupyterHub with Spark:

   # Load sample metadata
   from pyspark.sql import SparkSession
   spark = SparkSession.builder.appName("SpatialBlockCV").getOrCreate()

   # Load samples with pH data
   samples_with_ph = spark.sql('''
       SELECT sample_id, lon, lat, ph_soil, pf1_cu, pf1_zn, pf1_pb, pf1_ni
       FROM arkinlab.soil_metagenomes_v2
       WHERE has_ph_data = true
   ''').toPandas()

   # Load genus-level CLR features (already computed in feature_matrix)
   # Load KO prevalence: intersection of field_strict_ko_annotations.csv KOs
   field_ko_file = '/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data/field_strict_ko_annotations.csv'

   # Get union of field KOs across metals
   field_kos = pd.read_csv(field_ko_file)
   focus_kos = field_kos['ko_id'].unique()  # Union across all metals

   # Extract per-sample KO prevalence (0/1) from MAG annotations
   ko_prevalence = spark.sql(f'''
       SELECT sample_id, ko_id,
           CASE WHEN count(*) > 0 THEN 1 ELSE 0 END as ko_present
       FROM arkinlab.mgnify_mags_ko_annotations
       WHERE ko_id IN ({','.join(f"'{ko}'" for ko in focus_kos)})
       GROUP BY sample_id, ko_id
   ''').toPandas()

   # Pivot to sample × KO matrix
   ko_matrix = ko_prevalence.pivot(
       index='sample_id',
       columns='ko_id',
       values='ko_present'
   ).fillna(0)

""")

print("\n   Data structure expected:")
print("   - samples_with_ph: sample_id, lon, lat, ph_soil, pf1_cu/zn/pb/ni (n ≈ 40k)")
print("   - ko_matrix: sample_id × KO (n ≈ 40k × 31 KOs)")
print("   - feature_matrix: sample_id × genus_CLR (n ≈ 40k × 200 genera)")

# ============================================================================
# PART 3: CV STRUCTURE
# ============================================================================

print("\n3. Cross-validation structure:")
print(f"   - Blocks: {sorted(spatial_blocks['block'].unique())}")
print("   - Strategy: 5-fold leave-one-block-out")
print("   - For each fold:")
print("     * Hold out 1 block for test")
print("     * Train on remaining 4 blocks")
print("     * Evaluate on held-out block")

# ============================================================================
# PART 4: MODEL PIPELINES (scaffold)
# ============================================================================

print("\n4. Prediction pipelines:")
print("""
   P1 (pH only):
      Model: Ridge(alpha=1.0)
      Features: [ph_soil] (standardized)

   P2 (Taxonomy / CLR):
      Model: Ridge(alpha=1.0)
      Features: 200 genus CLR features

   P3 (Gene panel / KO presence):
      Model: Ridge(alpha=1.0)
      Features: 31 field-strict KO presence indicators

   P4 (pH + Gene panel):
      Model: Ridge(alpha=1.0)
      Features: [ph_soil] + 31 KO presence indicators
""")

# ============================================================================
# PART 5: EVALUATION FRAMEWORK
# ============================================================================

print("\n5. Evaluation framework:")
print("""
   For each metal target (Cu/Zn/Pb/Ni):
      For each fold (5 spatial blocks):
          For each pipeline (P1/P2/P3/P4):
              - Fit model on train blocks (non-held-out)
              - Predict on held-out block
              - Compute RMSE and correlation

   Output: results_spatial_block_cv.csv
   Columns: metal, block_held_out, pipeline, rmse, correlation, n_samples

   Summary: Which predictor generalizes best across spatial blocks?
   Expected: P2 (CLR) >> P1 (pH) for within-region patterns
             P3 (KOs) expected to underperform due to cross-dataset replication failure
             P4 (pH+KO) expected ≈ P1 (pH dominates over KOs)
""")

# ============================================================================
# PART 6: CURRENT STATE (metadata-only)
# ============================================================================

print("\n" + "="*70)
print("CURRENT STATUS")
print("="*70)

print(f"\nMetadata available:")
print(f"  - Spatial blocks: {spatial_blocks.shape[0]} samples, {spatial_blocks['block'].nunique()} blocks")
if feature_matrix is not None:
    print(f"  - Feature matrix: {feature_matrix.shape}")
else:
    print(f"  - Feature matrix: NOT FOUND (expected at data/feature_matrix.parquet)")

print(f"\nFiles created:")
print(f"  - Script: {__file__}")
print(f"  - Output will be saved to:")
print(f"    /home/hmacgregor/BERIL-research-observatory/projects/community_composition_prediction/data/spatial_block_cv_results.csv")

print(f"\nNext steps:")
print(f"  1. In JupyterHub, load data via Spark (see scaffold above)")
print(f"  2. Merge with spatial_blocks.csv")
print(f"  3. Implement 5-fold spatial block CV loop")
print(f"  4. Fit P1–P4 models for each fold")
print(f"  5. Aggregate results by pipeline")

# ============================================================================
# PART 7: SUMMARY TABLE (predicted outcome)
# ============================================================================

print("\n" + "="*70)
print("PREDICTED OUTCOME (based on existing analyses)")
print("="*70)

outcome_df = pd.DataFrame({
    'Pipeline': ['P1 (pH)', 'P2 (CLR)', 'P3 (KO panel)', 'P4 (pH+KO)'],
    'Cu_rank': [2, 1, 4, 3],
    'Zn_rank': [2, 1, 4, 3],
    'Pb_rank': [2, 1, 4, 3],
    'Ni_rank': [2, 1, 4, 3],
    'Expected_RMSE_leader': ['No', 'YES (CLR dominant)', 'No (poor transfer)', 'No (pH carries signal)'],
    'Rationale': [
        'Baseline env; useful but incomplete',
        'Genus composition captures contamination signal within regions',
        'Field-strict KOs do not replicate; cross-DB ρ=0.059',
        'pH will dominate; KOs add noise'
    ]
})

print("\n" + outcome_df.to_string(index=False))

print("\n" + "="*70)
print("Spatial block CV script scaffold complete.")
print("Full pipeline requires Spark data loading (see Part 2 above).")
print("="*70)
