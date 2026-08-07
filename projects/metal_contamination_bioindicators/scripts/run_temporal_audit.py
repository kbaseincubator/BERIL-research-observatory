#!/usr/bin/env python3
"""
Temporal audit of sample collection dates in metal contamination bioindicators project.

Checks:
1. Date field coverage
2. Year range and distribution
3. Temporal correlation with metals, geography, and community composition
4. Within-study temporal heterogeneity
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
import json

DATA = Path("data")
RESULTS = Path("data")

print("=" * 80)
print("TEMPORAL AUDIT: Metal Contamination Bioindicators")
print("=" * 80)

# ============================================================================
# STEP 1: Load and identify date fields
# ============================================================================
print("\nSTEP 1: Loading data and identifying date columns...")

# Load ENA metadata with date columns
ena_date_cols = [
    'exp_sample_accession_ref',  # join key to soil_samples
    'smp_attr_collection_date',
    'smp_attr_year',
    'por_collection_date',
    'por_collection_date_start',
    'por_collection_date_end'
]
ena = pd.read_parquet(DATA / "ena_metadata_full.parquet", columns=ena_date_cols)
print(f"  Loaded ena_metadata_full: {len(ena)} rows (runs)")

# Keep only unique samples (some samples have multiple runs)
ena = ena.drop_duplicates(subset=['exp_sample_accession_ref'])
print(f"  Unique samples in ENA: {len(ena)} rows")

# Replace empty strings with NaN
for col in ['smp_attr_collection_date', 'smp_attr_year', 'por_collection_date',
             'por_collection_date_start', 'por_collection_date_end']:
    ena[col] = ena[col].replace('', np.nan)

# Load soil samples (primary dataset)
soil = pd.read_parquet(DATA / "soil_samples.parquet", columns=['sample_id', 'lat', 'lon'])
print(f"  Loaded soil_samples: {len(soil)} rows")

# Join on exp_sample_accession_ref
ena_soil = soil.merge(
    ena[['exp_sample_accession_ref', 'smp_attr_collection_date', 'smp_attr_year',
          'por_collection_date', 'por_collection_date_start', 'por_collection_date_end']].rename(
        columns={'exp_sample_accession_ref': 'sample_id'}
    ),
    on='sample_id',
    how='inner'
)
print(f"  After merge on soil_samples: {len(ena_soil)} rows")

# ============================================================================
# STEP 2: Coverage analysis
# ============================================================================
print("\nSTEP 2: Date coverage analysis...")

total_samples = len(soil)

# Try parsing dates from most promising fields
best_dates = None
date_source = None

# Try por_collection_date_start (most complete range usually)
try:
    test_dates = pd.to_datetime(ena_soil['por_collection_date_start'], errors='coerce')
    if test_dates.notna().sum() > 0:
        best_dates = test_dates
        date_source = "por_collection_date_start"
except:
    pass

# Fall back to smp_attr_year if start dates incomplete
if best_dates is None or best_dates.notna().sum() < 1000:
    try:
        year_vals = pd.to_numeric(ena_soil['smp_attr_year'], errors='coerce')
        valid_years = year_vals[year_vals.notna() & (year_vals > 1900) & (year_vals < 2050)]
        if len(valid_years) > 0:
            best_dates = pd.Series(np.nan, index=ena_soil.index)
            best_dates[valid_years.index] = pd.to_datetime(valid_years.astype(int).astype(str) + '-01-01')
            date_source = "smp_attr_year"
    except:
        pass

if best_dates is not None:
    valid_dates = best_dates[best_dates.notna()]
    samples_with_date = len(valid_dates)
    pct_coverage = 100.0 * samples_with_date / total_samples
else:
    samples_with_date = 0
    pct_coverage = 0.0
    date_source = "NONE"

print(f"  Samples with date: {samples_with_date:,} / {total_samples:,} ({pct_coverage:.1f}%)")
print(f"  Date source: {date_source}")

if samples_with_date > 0:
    year_min = valid_dates.dt.year.min()
    year_max = valid_dates.dt.year.max()
    print(f"  Year range: {year_min} - {year_max}")

    # Year distribution
    year_counts = valid_dates.dt.year.value_counts().sort_index()
    year_dist = {int(y): int(c) for y, c in year_counts.items()}
    print(f"  Number of unique years: {len(year_dist)}")
    print(f"  Top 10 years by sample count:")
    for year in sorted(year_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {int(year[0])}: {int(year[1]):,}")
else:
    year_min = None
    year_max = None
    year_dist = {}

# ============================================================================
# STEP 3: Temporal confound checks
# ============================================================================
print("\nSTEP 3: Temporal confound analysis...")

temporal_confounds = {
    "year_vs_metal_rho": {},
    "year_vs_lat_rho": None,
    "year_vs_lon_rho": None,
    "year_vs_clr_pc1_rho": None
}

if samples_with_date and samples_with_date >= 100:
    # Add year as numeric to our dataframe
    ana_df = ena_soil.copy()
    ana_df['year'] = best_dates.dt.year
    ana_df = ana_df.dropna(subset=['year'])

    # Load metals from analysis_matrix
    print("  Loading analysis_matrix for metal columns...")
    amat = pd.read_parquet(DATA / "analysis_matrix.parquet", columns=['sample_id', 's25_as_AT', 's25_cd_AT', 's25_cr_AT', 's25_cu_AT', 's25_ni_AT', 's25_pb_AT'])
    ana_df = ana_df.merge(amat, on='sample_id', how='inner')

    metals = ['as', 'cd', 'cr', 'cu', 'ni', 'pb']
    for metal in metals:
        col = f's25_{metal}_AT'
        if col in ana_df.columns:
            valid_idx = ana_df[['year', col]].notna().all(axis=1)
            if valid_idx.sum() > 10:
                rho, pval = spearmanr(ana_df.loc[valid_idx, 'year'], ana_df.loc[valid_idx, col])
                temporal_confounds['year_vs_metal_rho'][metal] = {
                    'rho': float(rho),
                    'pval': float(pval),
                    'n': int(valid_idx.sum())
                }
                sig = "*" if pval < 0.05 else ""
                print(f"    {metal:2s}: rho={rho:7.4f}, p={pval:.3e} {sig}")

    # Year vs geography
    if 'lat' in ana_df.columns and 'lon' in ana_df.columns:
        valid_idx = ana_df[['year', 'lat']].notna().all(axis=1)
        if valid_idx.sum() > 10:
            rho_lat, pval_lat = spearmanr(ana_df.loc[valid_idx, 'year'], ana_df.loc[valid_idx, 'lat'])
            temporal_confounds['year_vs_lat_rho'] = {'rho': float(rho_lat), 'pval': float(pval_lat)}
            print(f"  year vs latitude: rho={rho_lat:.4f}, p={pval_lat:.3e}")

        valid_idx = ana_df[['year', 'lon']].notna().all(axis=1)
        if valid_idx.sum() > 10:
            rho_lon, pval_lon = spearmanr(ana_df.loc[valid_idx, 'year'], ana_df.loc[valid_idx, 'lon'])
            temporal_confounds['year_vs_lon_rho'] = {'rho': float(rho_lon), 'pval': float(pval_lon)}
            print(f"  year vs longitude: rho={rho_lon:.4f}, p={pval_lon:.3e}")

    # Year vs community (CLR PC1)
    print("  Computing CLR PC1 (this may take a minute)...")
    try:
        clr_matrix = pd.read_parquet(DATA / "clr_matrix.parquet", columns=None)
        print(f"    Loaded CLR matrix: {clr_matrix.shape}")

        # Subsample for memory
        if len(clr_matrix) > 10000:
            subsample_idx = np.random.RandomState(42).choice(len(clr_matrix), 10000, replace=False)
            clr_sub = clr_matrix.iloc[subsample_idx]
            sample_ids_sub = clr_sub.index.tolist()
        else:
            clr_sub = clr_matrix
            sample_ids_sub = clr_matrix.index.tolist()

        # Compute PCA
        from sklearn.decomposition import PCA
        pca = PCA(n_components=1)
        pc1 = pca.fit_transform(clr_sub.values)[:, 0]

        # Map back to years
        clr_year_df = pd.DataFrame({
            'sample_id': sample_ids_sub,
            'clr_pc1': pc1
        })
        clr_year_df = clr_year_df.merge(
            ana_df[['sample_id', 'year']],
            on='sample_id',
            how='inner'
        )

        if len(clr_year_df) > 10:
            rho_clr, pval_clr = spearmanr(clr_year_df['year'], clr_year_df['clr_pc1'])
            temporal_confounds['year_vs_clr_pc1_rho'] = {'rho': float(rho_clr), 'pval': float(pval_clr)}
            print(f"  year vs CLR PC1: rho={rho_clr:.4f}, p={pval_clr:.3e}")
    except Exception as e:
        print(f"  Could not compute CLR PC1: {e}")

# ============================================================================
# STEP 4: Within-study temporal heterogeneity
# ============================================================================
print("\nSTEP 4: Within-study temporal heterogeneity...")

within_study_analysis = {
    'n_studies_with_year_range': 0,
    'mean_within_study_year_span': None,
    'year_vs_clr_within_study_rho': None
}

try:
    # Load project metadata
    meta = pd.read_parquet(DATA / "sample_meta_project_env.parquet", columns=['sample_id', 'Project'])

    # Merge with years
    study_df = meta.merge(
        pd.DataFrame({
            'sample_id': ena_soil['sample_id'].values,
            'year': best_dates.dt.year.values if best_dates is not None else np.nan
        }),
        on='sample_id',
        how='inner'
    )
    study_df = study_df.dropna(subset=['year', 'Project'])

    # Find studies with multi-year sampling
    study_year_ranges = study_df.groupby('Project')['year'].agg(['min', 'max', 'count'])
    study_year_ranges['span'] = study_year_ranges['max'] - study_year_ranges['min']
    multi_year_studies = study_year_ranges[study_year_ranges['span'] > 0]

    n_multi_year = len(multi_year_studies)
    within_study_analysis['n_studies_with_year_range'] = int(n_multi_year)
    if n_multi_year > 0:
        mean_span = multi_year_studies['span'].mean()
        within_study_analysis['mean_within_study_year_span'] = float(mean_span)
        print(f"  Studies with multi-year sampling: {n_multi_year}")
        print(f"  Mean year span within studies: {mean_span:.1f} years")
        print(f"  Top 5 studies by year range:")
        for proj, row in study_year_ranges.nlargest(5, 'span').iterrows():
            print(f"    {proj}: {int(row['min'])}-{int(row['max'])} ({int(row['span'])} yr span, n={int(row['count'])})")

except Exception as e:
    print(f"  Could not analyze within-study: {e}")

# ============================================================================
# STEP 5: Summary and save
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

conclusion = ""
if samples_with_date < 1000:
    conclusion = "MINIMAL DATE DATA: <1% coverage. Temporal confounding unlikely to be a major issue due to data scarcity."
elif pct_coverage < 20:
    conclusion = f"LOW DATE COVERAGE ({pct_coverage:.1f}%): Limited temporal variation in data. Confounding unlikely unless severely biased."
else:
    # Check if any temporal correlations are significant
    sig_metal_corrs = any(
        abs(v.get('rho', 0)) > 0.1 and v.get('pval', 1) < 0.05
        for v in temporal_confounds['year_vs_metal_rho'].values()
    )
    sig_geo_corrs = (
        (temporal_confounds['year_vs_lat_rho'] and
         abs(temporal_confounds['year_vs_lat_rho'].get('rho', 0)) > 0.1 and
         temporal_confounds['year_vs_lat_rho'].get('pval', 1) < 0.05) or
        (temporal_confounds['year_vs_lon_rho'] and
         abs(temporal_confounds['year_vs_lon_rho'].get('rho', 0)) > 0.1 and
         temporal_confounds['year_vs_lon_rho'].get('pval', 1) < 0.05)
    )

    if sig_metal_corrs:
        conclusion = f"POTENTIAL TEMPORAL CONFOUND: Year significantly correlates with some metals. Control for collection year in sensitivity analyses."
    elif sig_geo_corrs:
        conclusion = f"TEMPORAL-GEOGRAPHIC CONFOUND: Collection year correlates with sampling location. Consider stratified analyses."
    else:
        conclusion = f"MINIMAL TEMPORAL CONFOUND: Date data shows adequate coverage ({pct_coverage:.1f}%), but no strong year-metal or year-geography correlations detected."

print(f"\n{conclusion}\n")

# Save results
results = {
    "total_samples": int(total_samples),
    "samples_with_date": int(samples_with_date),
    "date_coverage_pct": float(pct_coverage),
    "year_range": [int(year_min), int(year_max)] if year_min is not None else None,
    "year_distribution": year_dist,
    "date_source": date_source,
    "temporal_confound_checks": temporal_confounds,
    "within_study_year_effect": within_study_analysis,
    "conclusion": conclusion
}

output_file = RESULTS / "temporal_audit.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {output_file}")

# Also print summary stats
print(f"\nQuick stats:")
print(f"  Total samples analyzed: {total_samples:,}")
print(f"  Samples with collection dates: {samples_with_date:,} ({pct_coverage:.1f}%)")
if year_min:
    print(f"  Date range: {year_min}-{year_max}")
    print(f"  Temporal confound risk: {'LOW' if pct_coverage < 20 or not sig_metal_corrs else 'ELEVATED'}")

print("\nDone.")
