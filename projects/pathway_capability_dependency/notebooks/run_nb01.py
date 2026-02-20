#!/usr/bin/env python3
"""
NB01 runner script — executes data extraction cells sequentially.
Uses local Spark session via proxy chain (get_spark_session).
Large GapMind tables exported to MinIO, then downloaded.
"""
import os
import sys
import time
import glob
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

UPSTREAM = {
    'essential_metabolome': os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'essential_metabolome', 'data'),
    'essential_genome': os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'essential_genome', 'data'),
}

print("=" * 60)
print("NB01: Data Extraction — Runner Script")
print("=" * 60)

# --- Initialize Spark ---
print("\n[1/10] Initializing Spark session...")
t0 = time.time()
from get_spark_session import get_spark_session
spark = get_spark_session()
print(f"  Spark session ready ({time.time()-t0:.1f}s)")

# Check upstream data
print("\nUpstream data availability:")
for project, path in UPSTREAM.items():
    if os.path.exists(path):
        files = os.listdir(path)
        print(f"  {project}: {len(files)} files")
    else:
        print(f"  {project}: NOT FOUND")

fb_genome_map_path = os.path.join(UPSTREAM['essential_metabolome'], 'fb_genome_mapping_manual.tsv')
if os.path.exists(fb_genome_map_path):
    fb_genome_map = pd.read_csv(fb_genome_map_path, sep='\t')
    print(f"\nLoaded FB-genome mapping: {len(fb_genome_map)} organisms")
else:
    fb_genome_map = None
    print("\nFB-genome mapping not found")

# --- GapMind-FB coverage check ---
output_path = os.path.join(DATA_DIR, 'gapmind_fb_coverage.csv')
if os.path.exists(output_path):
    print(f"\n[2/10] GapMind-FB coverage: already exists, skipping")
else:
    print(f"\n[2/10] Checking GapMind coverage for FB organisms...")
    t0 = time.time()
    fb_orgs = spark.sql("""
        SELECT DISTINCT orgId FROM kescience_fitnessbrowser.gene
        WHERE CAST(type AS INT) = 1
    """).toPandas()

    gapmind_genome_counts = spark.sql("""
        SELECT clade_name, COUNT(DISTINCT genome_id) as n_genomes,
               COUNT(DISTINCT pathway) as n_pathways
        FROM kbase_ke_pangenome.gapmind_pathways
        WHERE sequence_scope = 'all'
        GROUP BY clade_name
    """).toPandas()

    print(f"  Total FB organisms: {len(fb_orgs)}")
    print(f"  GapMind clades with data: {len(gapmind_genome_counts)}")

    if fb_genome_map is not None:
        fb_genome_map_copy = fb_genome_map.copy()
        fb_genome_map_copy['gapmind_genome_id'] = fb_genome_map_copy['genome_id'].str.replace(r'^(RS_|GB_)', '', regex=True)
        gapmind_genomes = spark.sql("""
            SELECT DISTINCT genome_id FROM kbase_ke_pangenome.gapmind_pathways
        """).toPandas()
        fb_genome_map_copy['in_gapmind'] = fb_genome_map_copy['gapmind_genome_id'].isin(gapmind_genomes['genome_id'])
        coverage = fb_genome_map_copy[['orgId', 'genome_id', 'gapmind_genome_id', 'in_gapmind']].copy()
        n_covered = coverage['in_gapmind'].sum()
        print(f"  FB organisms with GapMind data: {n_covered}/{len(coverage)}")
    else:
        coverage = gapmind_genome_counts
    coverage.to_csv(output_path, index=False)
    print(f"  Saved ({time.time()-t0:.1f}s)")


# --- GapMind pathway status (scope=all) — CHUNKED BY PATHWAY ---
output_path = os.path.join(DATA_DIR, 'gapmind_genome_pathway_status.csv')
if os.path.exists(output_path):
    print(f"\n[3/10] GapMind genome pathway status: already exists, skipping")
else:
    print(f"\n[3/10] Extracting GapMind pathway status (scope=all)...")
    print("  Chunking by individual pathway to stay under maxResultSize...")
    t0 = time.time()

    # Get list of all pathways
    pathways = spark.sql("""
        SELECT DISTINCT pathway FROM kbase_ke_pangenome.gapmind_pathways
        WHERE sequence_scope = 'all'
        ORDER BY pathway
    """).toPandas()['pathway'].tolist()
    print(f"  Found {len(pathways)} pathways to process")

    # Collect in batches of 5 pathways at a time
    BATCH_SIZE = 5
    chunks = []
    for i in range(0, len(pathways), BATCH_SIZE):
        batch = pathways[i:i+BATCH_SIZE]
        batch_str = "','".join(batch)
        tc = time.time()
        chunk = spark.sql(f"""
            SELECT
                genome_id, clade_name, pathway, metabolic_category,
                MAX(score) as best_score,
                MAX(score_simplified) as is_complete,
                MAX(nHi) as max_nHi,
                MAX(CASE WHEN score_category = 'complete' THEN 1 ELSE 0 END) as is_fully_complete,
                MAX(CASE WHEN score_category = 'likely_complete' THEN 1 ELSE 0 END) as is_likely_complete
            FROM kbase_ke_pangenome.gapmind_pathways
            WHERE sequence_scope = 'all'
              AND pathway IN ('{batch_str}')
            GROUP BY genome_id, clade_name, pathway, metabolic_category
        """).toPandas()
        chunks.append(chunk)
        elapsed = time.time() - tc
        total_so_far = sum(len(c) for c in chunks)
        print(f"    Batch {i//BATCH_SIZE + 1}/{(len(pathways)+BATCH_SIZE-1)//BATCH_SIZE}: "
              f"{len(batch)} pathways, {len(chunk):,} rows ({elapsed:.1f}s) [total: {total_so_far:,}]")

    gapmind_all_pd = pd.concat(chunks, ignore_index=True)
    gapmind_all_pd.to_csv(output_path, index=False)
    print(f"  TOTAL: {len(gapmind_all_pd):,} rows saved ({time.time()-t0:.1f}s)")

# --- GapMind pathway status (scope=core) — CHUNKED BY PATHWAY ---
output_path = os.path.join(DATA_DIR, 'gapmind_core_pathway_status.csv')
if os.path.exists(output_path):
    print(f"\n[4/10] GapMind core pathway status: already exists, skipping")
else:
    print(f"\n[4/10] Extracting GapMind pathway status (scope=core)...")
    print("  Chunking by individual pathway...")
    t0 = time.time()

    pathways = spark.sql("""
        SELECT DISTINCT pathway FROM kbase_ke_pangenome.gapmind_pathways
        WHERE sequence_scope = 'core'
        ORDER BY pathway
    """).toPandas()['pathway'].tolist()

    BATCH_SIZE = 5
    chunks = []
    for i in range(0, len(pathways), BATCH_SIZE):
        batch = pathways[i:i+BATCH_SIZE]
        batch_str = "','".join(batch)
        tc = time.time()
        chunk = spark.sql(f"""
            SELECT
                genome_id, clade_name, pathway, metabolic_category,
                MAX(score) as best_score_core,
                MAX(score_simplified) as is_complete_core
            FROM kbase_ke_pangenome.gapmind_pathways
            WHERE sequence_scope = 'core'
              AND pathway IN ('{batch_str}')
            GROUP BY genome_id, clade_name, pathway, metabolic_category
        """).toPandas()
        chunks.append(chunk)
        elapsed = time.time() - tc
        total_so_far = sum(len(c) for c in chunks)
        print(f"    Batch {i//BATCH_SIZE + 1}/{(len(pathways)+BATCH_SIZE-1)//BATCH_SIZE}: "
              f"{len(chunk):,} rows ({elapsed:.1f}s) [total: {total_so_far:,}]")

    gapmind_core_pd = pd.concat(chunks, ignore_index=True)
    gapmind_core_pd.to_csv(output_path, index=False)
    print(f"  TOTAL: {len(gapmind_core_pd):,} rows saved ({time.time()-t0:.1f}s)")

# --- Species-level pathway summary ---
output_csv = os.path.join(DATA_DIR, 'species_pathway_summary.csv')
if os.path.exists(output_csv):
    print(f"\n[5/10] Species pathway summary: already exists, skipping")
else:
    print(f"\n[5/10] Computing species-level pathway summary...")
    t0 = time.time()
    species_summary_pd = spark.sql("""
        WITH genome_pathway AS (
            SELECT
                genome_id, clade_name, pathway, metabolic_category,
                MAX(score_simplified) as is_complete
            FROM kbase_ke_pangenome.gapmind_pathways
            WHERE sequence_scope = 'all'
            GROUP BY genome_id, clade_name, pathway, metabolic_category
        )
        SELECT
            clade_name, pathway, metabolic_category,
            COUNT(*) as n_genomes,
            SUM(CAST(is_complete AS INT)) as n_complete,
            AVG(is_complete) as frac_complete
        FROM genome_pathway
        GROUP BY clade_name, pathway, metabolic_category
    """).toPandas()
    species_summary_pd.to_csv(output_csv, index=False)
    n_species = species_summary_pd['clade_name'].nunique()
    n_pathways = species_summary_pd['pathway'].nunique()
    print(f"  Saved: {len(species_summary_pd):,} rows ({time.time()-t0:.1f}s)")
    print(f"  Species: {n_species:,}, Pathways: {n_pathways}")

# --- Pangenome stats ---
output_path = os.path.join(DATA_DIR, 'pangenome_stats.csv')
if os.path.exists(output_path):
    print(f"\n[6/10] Pangenome stats: already exists, skipping")
else:
    print(f"\n[6/10] Extracting pangenome stats...")
    t0 = time.time()
    pangenome_pd = spark.sql("""
        SELECT
            gtdb_species_clade_id, no_genomes, no_gene_clusters,
            no_core, no_aux_genome, no_singleton_gene_clusters
        FROM kbase_ke_pangenome.pangenome
    """).toPandas()
    for col in ['no_genomes', 'no_gene_clusters', 'no_core', 'no_aux_genome', 'no_singleton_gene_clusters']:
        pangenome_pd[col] = pd.to_numeric(pangenome_pd[col], errors='coerce')
    pangenome_pd['frac_singleton'] = pangenome_pd['no_singleton_gene_clusters'] / pangenome_pd['no_gene_clusters']
    pangenome_pd['frac_core'] = pangenome_pd['no_core'] / pangenome_pd['no_gene_clusters']
    pangenome_pd['frac_accessory'] = pangenome_pd['no_aux_genome'] / pangenome_pd['no_gene_clusters']
    pangenome_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(pangenome_pd):,} rows ({time.time()-t0:.1f}s)")

# --- FB fitness summary ---
output_path = os.path.join(DATA_DIR, 'fb_fitness_summary.csv')
if os.path.exists(output_path):
    print(f"\n[7/10] FB fitness summary: already exists, skipping")
else:
    print(f"\n[7/10] Extracting FB fitness summary (27M rows aggregated)...")
    t0 = time.time()
    fb_fitness_pd = spark.sql("""
        SELECT
            orgId, locusId,
            COUNT(*) as n_conditions,
            AVG(CAST(fit AS FLOAT)) as mean_fitness,
            PERCENTILE_APPROX(CAST(fit AS FLOAT), 0.5) as median_fitness,
            MIN(CAST(fit AS FLOAT)) as min_fitness,
            MAX(CAST(fit AS FLOAT)) as max_fitness,
            STDDEV(CAST(fit AS FLOAT)) as std_fitness,
            SUM(CASE WHEN ABS(CAST(fit AS FLOAT)) > 1.0 THEN 1 ELSE 0 END) as n_strong_phenotype,
            SUM(CASE WHEN CAST(fit AS FLOAT) < -1.0 THEN 1 ELSE 0 END) as n_sick,
            SUM(CASE WHEN CAST(fit AS FLOAT) > 1.0 THEN 1 ELSE 0 END) as n_beneficial,
            SUM(CASE WHEN ABS(CAST(fit AS FLOAT)) > 2.0 THEN 1 ELSE 0 END) as n_very_strong,
            SUM(CASE WHEN ABS(CAST(fit AS FLOAT)) > 1.0 THEN 1 ELSE 0 END) / COUNT(*) as fitness_breadth,
            SUM(CASE WHEN CAST(fit AS FLOAT) < -1.0 THEN 1 ELSE 0 END) / COUNT(*) as sick_breadth,
            SUM(CASE WHEN CAST(fit AS FLOAT) < -2.0 THEN 1 ELSE 0 END) / COUNT(*) as severe_sick_breadth
        FROM kescience_fitnessbrowser.genefitness
        GROUP BY orgId, locusId
    """).toPandas()
    fb_fitness_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(fb_fitness_pd):,} rows ({time.time()-t0:.1f}s)")
    print(f"  Organisms: {fb_fitness_pd['orgId'].nunique()}")
    print(f"  Fitness breadth stats:")
    print(fb_fitness_pd['fitness_breadth'].describe().to_string())

# --- Condition-type fitness ---
output_path = os.path.join(DATA_DIR, 'fb_fitness_by_condition_type.csv')
if os.path.exists(output_path):
    print(f"\n[8/10] Condition-type fitness: already exists, skipping")
else:
    print(f"\n[8/10] Extracting condition-type fitness (v2)...")
    t0 = time.time()
    cond_fitness_pd = spark.sql("""
        WITH exp_types AS (
            SELECT
                name as expName,
                orgId,
                CASE
                    WHEN LOWER(Condition_1) LIKE '%carbon%'
                         OR LOWER(`Group`) LIKE '%carbon%'
                         OR LOWER(Condition_1) LIKE '%glucose%'
                         OR LOWER(Condition_1) LIKE '%sugar%'
                         OR LOWER(Condition_1) LIKE '%acetate%'
                         OR LOWER(Condition_1) LIKE '%lactate%'
                         OR LOWER(Condition_1) LIKE '%glycerol%'
                         THEN 'carbon_source'
                    WHEN LOWER(Condition_1) LIKE '%nitrogen%'
                         OR LOWER(`Group`) LIKE '%nitrogen%'
                         OR LOWER(Condition_1) LIKE '%ammonium%'
                         OR LOWER(Condition_1) LIKE '%amino acid%'
                         THEN 'nitrogen_source'
                    WHEN LOWER(Condition_1) LIKE '%stress%'
                         OR LOWER(Condition_1) LIKE '%metal%'
                         OR LOWER(Condition_1) LIKE '%antibiotic%'
                         OR LOWER(Condition_1) LIKE '%salt%'
                         OR LOWER(Condition_1) LIKE '%pH%'
                         OR LOWER(Condition_1) LIKE '%temperature%'
                         OR LOWER(Condition_1) LIKE '%oxidative%'
                         OR LOWER(Condition_1) LIKE '%osmotic%'
                         THEN 'stress'
                    ELSE 'other'
                END as condition_type
            FROM kescience_fitnessbrowser.exps
        )
        SELECT
            gf.orgId, gf.locusId, et.condition_type,
            COUNT(*) as n_conditions,
            AVG(CAST(gf.fit AS FLOAT)) as mean_fitness,
            PERCENTILE_APPROX(CAST(gf.fit AS FLOAT), 0.5) as median_fitness,
            MIN(CAST(gf.fit AS FLOAT)) as min_fitness,
            SUM(CASE WHEN CAST(gf.fit AS FLOAT) < -1.0 THEN 1 ELSE 0 END) as n_sick,
            SUM(CASE WHEN ABS(CAST(gf.fit AS FLOAT)) > 1.0 THEN 1 ELSE 0 END) as n_strong
        FROM kescience_fitnessbrowser.genefitness gf
        JOIN exp_types et ON gf.expName = et.expName AND gf.orgId = et.orgId
        GROUP BY gf.orgId, gf.locusId, et.condition_type
    """).toPandas()
    cond_fitness_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(cond_fitness_pd):,} rows ({time.time()-t0:.1f}s)")
    print(f"  Condition type distribution:")
    print(cond_fitness_pd.groupby('condition_type')['n_conditions'].sum().to_string())

# --- KEGG annotations ---
output_path = os.path.join(DATA_DIR, 'fb_kegg_annotations.csv')
if os.path.exists(output_path):
    print(f"\n[9/10] KEGG annotations: already exists, skipping")
else:
    print(f"\n[9/10] Extracting KEGG KO + pathway annotations (93M-row table)...")
    t0 = time.time()
    kegg_pd = spark.sql("""
        SELECT
            query_name as gene_cluster_id,
            EC, KEGG_ko, KEGG_Pathway, COG_category, Description
        FROM kbase_ke_pangenome.eggnog_mapper_annotations
        WHERE (
            KEGG_Pathway LIKE '%map00220%'
            OR KEGG_Pathway LIKE '%map00260%'
            OR KEGG_Pathway LIKE '%map00270%'
            OR KEGG_Pathway LIKE '%map00290%'
            OR KEGG_Pathway LIKE '%map00300%'
            OR KEGG_Pathway LIKE '%map00330%'
            OR KEGG_Pathway LIKE '%map00340%'
            OR KEGG_Pathway LIKE '%map00350%'
            OR KEGG_Pathway LIKE '%map00360%'
            OR KEGG_Pathway LIKE '%map00380%'
            OR KEGG_Pathway LIKE '%map00400%'
            OR KEGG_Pathway LIKE '%map00250%'
            OR KEGG_Pathway LIKE '%map00010%'
            OR KEGG_Pathway LIKE '%map00020%'
            OR KEGG_Pathway LIKE '%map00030%'
            OR KEGG_Pathway LIKE '%map00040%'
            OR KEGG_Pathway LIKE '%map00051%'
            OR KEGG_Pathway LIKE '%map00052%'
            OR KEGG_Pathway LIKE '%map00500%'
            OR KEGG_Pathway LIKE '%map00520%'
            OR KEGG_Pathway LIKE '%map00620%'
            OR KEGG_Pathway LIKE '%map00630%'
            OR KEGG_Pathway LIKE '%map00640%'
            OR KEGG_Pathway LIKE '%map00650%'
            OR KEGG_Pathway LIKE '%map00660%'
            OR KEGG_Pathway LIKE '%map00562%'
            OR COG_category LIKE '%E%'
            OR COG_category LIKE '%G%'
            OR COG_category LIKE '%C%'
        )
        AND (KEGG_ko != '-' OR EC != '-' OR KEGG_Pathway != '-')
    """).toPandas()
    kegg_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(kegg_pd):,} rows ({time.time()-t0:.1f}s)")
    print(f"  Unique gene clusters: {kegg_pd['gene_cluster_id'].nunique():,}")
    print(f"  With KEGG_ko: {(kegg_pd['KEGG_ko'] != '-').sum():,}")

# --- Essential genes ---
output_path = os.path.join(DATA_DIR, 'fb_essential_genes.csv')
if os.path.exists(output_path):
    print(f"\n[10/10] Essential genes: already exists, skipping")
else:
    print(f"\n[10/10] Identifying putative essential genes...")
    t0 = time.time()
    essentials_pd = spark.sql("""
        SELECT g.orgId, g.locusId, g.sysName, g.gene as gene_name, g.desc as gene_desc
        FROM kescience_fitnessbrowser.gene g
        LEFT JOIN (
            SELECT DISTINCT orgId, locusId FROM kescience_fitnessbrowser.genefitness
        ) gf ON g.orgId = gf.orgId AND g.locusId = gf.locusId
        WHERE CAST(g.type AS INT) = 1
          AND gf.locusId IS NULL
    """).toPandas()
    essentials_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(essentials_pd):,} genes ({time.time()-t0:.1f}s)")
    print(f"  Per organism:")
    print(essentials_pd.groupby('orgId').size().describe().to_string())

# --- Summary ---
print("\n" + "=" * 60)
print("NB01 COMPLETE — Generated data files:")
print("=" * 60)
for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.csv'))):
    size_mb = os.path.getsize(f) / 1e6
    print(f"  {os.path.basename(f):45s} {size_mb:8.1f} MB")
print("\nReady for NB02 (Tier 1) and NB03 (Tier 2).")
