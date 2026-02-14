#!/usr/bin/env python3
"""
Extract per-gene fitness summary statistics from the Fitness Browser via Spark Connect.

For each organism, computes:
- Overall fitness stats: min/max/mean fitness, counts of sick/beneficial experiments
- Per-condition-type stats: same metrics broken down by experiment group (stress, carbon source, etc.)
- Specific phenotype counts per gene

Usage: python3 src/extract_fitness_stats.py
"""

import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# The 33 high-coverage organisms from conservation_vs_fitness (excluding Dyella79)
CONSERVATION_PROJECT = PROJECT_DIR.parent / 'conservation_vs_fitness'

print("Connecting to Spark...")
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
print("Spark ready")

# Load organism list from conservation_vs_fitness link table
link = pd.read_csv(CONSERVATION_PROJECT / 'data' / 'fb_pangenome_link.tsv', sep='\t')
link = link[link['orgId'] != 'Dyella79']
organisms = sorted(link['orgId'].unique())
print(f"Organisms to process: {len(organisms)}")

# ============================================================================
# Extract overall fitness stats per gene
# ============================================================================
print("\n=== EXTRACTING OVERALL FITNESS STATS ===")

fitness_stats_path = DATA_DIR / 'fitness_stats.tsv'

if fitness_stats_path.exists() and fitness_stats_path.stat().st_size > 0:
    print(f"Already cached: {fitness_stats_path}")
else:
    all_stats = []
    for i, orgId in enumerate(organisms):
        print(f"  [{i+1}/{len(organisms)}] {orgId}...", end='', flush=True)
        stats = spark.sql(f"""
            SELECT orgId, locusId,
                   COUNT(*) as n_experiments,
                   MIN(CAST(fit AS FLOAT)) as min_fit,
                   MAX(CAST(fit AS FLOAT)) as max_fit,
                   AVG(CAST(fit AS FLOAT)) as mean_fit,
                   SUM(CASE WHEN CAST(fit AS FLOAT) < -1 THEN 1 ELSE 0 END) as n_sick,
                   SUM(CASE WHEN CAST(fit AS FLOAT) < -2 THEN 1 ELSE 0 END) as n_very_sick,
                   SUM(CASE WHEN CAST(fit AS FLOAT) > 1 THEN 1 ELSE 0 END) as n_beneficial,
                   SUM(CASE WHEN CAST(fit AS FLOAT) > 2 THEN 1 ELSE 0 END) as n_very_beneficial,
                   SUM(CASE WHEN ABS(CAST(fit AS FLOAT)) > 1 THEN 1 ELSE 0 END) as n_significant
            FROM kescience_fitnessbrowser.genefitness
            WHERE orgId = '{orgId}'
            GROUP BY orgId, locusId
        """).toPandas()
        all_stats.append(stats)
        print(f" {len(stats)} genes")

    fitness_stats = pd.concat(all_stats, ignore_index=True)
    fitness_stats.to_csv(fitness_stats_path, sep='\t', index=False)
    print(f"Saved: {fitness_stats_path} ({len(fitness_stats):,} rows)")

# ============================================================================
# Extract fitness stats by condition type
# ============================================================================
print("\n=== EXTRACTING FITNESS STATS BY CONDITION TYPE ===")

by_condition_path = DATA_DIR / 'fitness_stats_by_condition.tsv'

if by_condition_path.exists() and by_condition_path.stat().st_size > 0:
    print(f"Already cached: {by_condition_path}")
else:
    all_cond = []
    for i, orgId in enumerate(organisms):
        print(f"  [{i+1}/{len(organisms)}] {orgId}...", end='', flush=True)
        cond = spark.sql(f"""
            SELECT gf.orgId, gf.locusId, e.expGroup,
                   COUNT(*) as n_exps,
                   MIN(CAST(gf.fit AS FLOAT)) as min_fit,
                   MAX(CAST(gf.fit AS FLOAT)) as max_fit,
                   AVG(CAST(gf.fit AS FLOAT)) as mean_fit,
                   SUM(CASE WHEN CAST(gf.fit AS FLOAT) < -1 THEN 1 ELSE 0 END) as n_sick,
                   SUM(CASE WHEN CAST(gf.fit AS FLOAT) > 1 THEN 1 ELSE 0 END) as n_beneficial
            FROM kescience_fitnessbrowser.genefitness gf
            JOIN kescience_fitnessbrowser.experiment e
                ON gf.orgId = e.orgId AND gf.expName = e.expName
            WHERE gf.orgId = '{orgId}'
            GROUP BY gf.orgId, gf.locusId, e.expGroup
        """).toPandas()
        all_cond.append(cond)
        print(f" {len(cond)} rows")

    by_condition = pd.concat(all_cond, ignore_index=True)
    by_condition.to_csv(by_condition_path, sep='\t', index=False)
    print(f"Saved: {by_condition_path} ({len(by_condition):,} rows)")

# ============================================================================
# Extract specific phenotype counts per gene
# ============================================================================
print("\n=== EXTRACTING SPECIFIC PHENOTYPE COUNTS ===")

specpheno_path = DATA_DIR / 'specific_phenotypes.tsv'

if specpheno_path.exists() and specpheno_path.stat().st_size > 0:
    print(f"Already cached: {specpheno_path}")
else:
    all_sp = []
    for i, orgId in enumerate(organisms):
        print(f"  [{i+1}/{len(organisms)}] {orgId}...", end='', flush=True)
        sp = spark.sql(f"""
            SELECT orgId, locusId, COUNT(*) as n_specific_phenotypes
            FROM kescience_fitnessbrowser.specificphenotype
            WHERE orgId = '{orgId}'
            GROUP BY orgId, locusId
        """).toPandas()
        all_sp.append(sp)
        print(f" {len(sp)} genes")

    specpheno = pd.concat(all_sp, ignore_index=True)
    specpheno.to_csv(specpheno_path, sep='\t', index=False)
    print(f"Saved: {specpheno_path} ({len(specpheno):,} rows)")

print("\n=== EXTRACTION COMPLETE ===")
print(f"Overall fitness stats: {fitness_stats_path}")
print(f"By condition type: {by_condition_path}")
print(f"Specific phenotypes: {specpheno_path}")
