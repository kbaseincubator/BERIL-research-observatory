#!/usr/bin/env python3
"""NB01: Data Extraction — Genome × AMR Presence/Absence Matrices.

Runs the full extraction pipeline for all eligible species.
Outputs per-species TSV matrices and genome metadata.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from time import time
import traceback

# Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = PROJECT_DIR.parent / 'amr_pangenome_atlas'
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'
MATRIX_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = PROJECT_DIR / 'scripts' / 'nb01_extraction.log'

def log(msg):
    ts = pd.Timestamp.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

# Clear log
LOG_FILE.write_text('')
log("Starting NB01 extraction")

# Spark
sys.path.insert(0, str(PROJECT_DIR.parent.parent / 'scripts'))
from get_spark_session import get_spark_session
spark = get_spark_session()
spark.sql("SELECT 1 AS test").show()
log("Spark session ready")

# ── Utility ──
def chunked_query(spark, ids, query_template, chunk_size=5000):
    results = []
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i+chunk_size]
        id_list = "','".join(str(x) for x in chunk)
        query = query_template.format(id_list=f"'{id_list}'")
        results.append(spark.sql(query).toPandas())
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

# ── Species Selection ──
species_summary = pd.read_csv(ATLAS_DIR / 'data' / 'amr_species_summary.csv')
amr_census = pd.read_csv(ATLAS_DIR / 'data' / 'amr_census.csv')

eligible = species_summary[
    (species_summary['no_genomes'] >= 10) &
    (species_summary['n_amr'] >= 5) &
    ((species_summary['n_aux_amr'] + species_summary['n_sing_amr']) >= 1)
].copy()

eligible.to_csv(DATA_DIR / 'eligible_species.csv', index=False)
log(f"Eligible species: {len(eligible)}")

# AMR cluster lookup
species_amr_clusters = (
    amr_census
    .groupby('gtdb_species_clade_id')['gene_cluster_id']
    .apply(list)
    .to_dict()
)
eligible_ids = set(eligible['gtdb_species_clade_id'])
species_amr_clusters = {k: v for k, v in species_amr_clusters.items() if k in eligible_ids}
log(f"Species with AMR clusters: {len(species_amr_clusters)}")

# ── Extraction ──
def extract_species_matrix(spark, species_id, amr_cluster_ids, matrix_dir):
    outpath = matrix_dir / f"{species_id.replace('/', '_')}.tsv"
    if outpath.exists() and outpath.stat().st_size > 100:
        return outpath, 'cached'

    t0 = time()

    # Genome IDs
    genomes = chunked_query(spark, [species_id], """
        SELECT genome_id
        FROM kbase_ke_pangenome.genome
        WHERE gtdb_species_clade_id IN ({id_list})
    """)

    if len(genomes) == 0:
        return None, 'no_genomes'

    genome_ids = genomes['genome_id'].tolist()

    # Double-filtered join
    all_hits = []
    genome_chunk_size = 500
    amr_list = "','".join(str(x) for x in amr_cluster_ids)

    for gi in range(0, len(genome_ids), genome_chunk_size):
        g_chunk = genome_ids[gi:gi+genome_chunk_size]
        g_list = "','".join(str(x) for x in g_chunk)

        query = f"""
            SELECT DISTINCT g.genome_id, j.gene_cluster_id
            FROM kbase_ke_pangenome.gene g
            JOIN kbase_ke_pangenome.gene_genecluster_junction j
                ON g.gene_id = j.gene_id
            WHERE g.genome_id IN ('{g_list}')
              AND j.gene_cluster_id IN ('{amr_list}')
        """
        hits = spark.sql(query).toPandas()
        all_hits.append(hits)

    if not all_hits:
        return None, 'no_hits'

    hits_df = pd.concat(all_hits, ignore_index=True)

    if len(hits_df) == 0:
        return None, 'no_hits'

    # Pivot
    hits_df['present'] = 1
    matrix = hits_df.pivot_table(
        index='genome_id', columns='gene_cluster_id',
        values='present', fill_value=0, aggfunc='max'
    )

    for cid in amr_cluster_ids:
        if cid not in matrix.columns:
            matrix[cid] = 0

    for gid in genome_ids:
        if gid not in matrix.index:
            matrix.loc[gid] = 0

    matrix = matrix.astype(int)
    matrix.to_csv(outpath, sep='\t')

    elapsed = time() - t0
    return outpath, f'ok ({len(matrix)} genomes x {len(matrix.columns)} AMR, {elapsed:.0f}s)'


total = len(species_amr_clusters)
ok_count = 0
err_count = 0
cached_count = 0
t_start = time()

for idx, (species_id, amr_ids) in enumerate(sorted(species_amr_clusters.items())):
    short_name = species_id.split('--')[0].replace('s__', '')

    try:
        path, status = extract_species_matrix(spark, species_id, amr_ids, MATRIX_DIR)
        if 'cached' in status:
            cached_count += 1
        elif status.startswith('ok'):
            ok_count += 1
        log(f"[{idx+1}/{total}] {short_name}: {status}")
    except Exception as e:
        err_count += 1
        log(f"[{idx+1}/{total}] {short_name}: ERROR {e}")
        traceback.print_exc()

    # Periodic stats
    if (idx + 1) % 50 == 0:
        elapsed = time() - t_start
        rate = (idx + 1) / elapsed * 3600
        remaining = (total - idx - 1) / max(rate/3600, 0.001)
        log(f"  Progress: {idx+1}/{total}, {ok_count} ok, {cached_count} cached, {err_count} err, "
            f"rate={rate:.0f}/hr, ETA={remaining:.1f}h")

# ── Metadata ──
log("Extracting genome metadata...")
metadata_path = DATA_DIR / 'genome_metadata.csv'

if metadata_path.exists() and metadata_path.stat().st_size > 100:
    log(f"Metadata already cached: {metadata_path}")
else:
    all_genome_ids = set()
    for mf in MATRIX_DIR.glob('*.tsv'):
        idx_df = pd.read_csv(mf, sep='\t', usecols=[0])
        all_genome_ids.update(idx_df.iloc[:, 0].tolist())

    log(f"Extracting metadata for {len(all_genome_ids)} genomes...")
    genome_meta = chunked_query(spark, list(all_genome_ids), """
        SELECT genome_id, isolation_source, collection_date, geo_loc_name, host
        FROM kbase_ke_pangenome.ncbi_env
        WHERE genome_id IN ({id_list})
    """)
    genome_meta.to_csv(metadata_path, index=False)
    log(f"Metadata saved: {len(genome_meta)} genomes")

# ── Summary ──
elapsed_total = time() - t_start
matrix_files = list(MATRIX_DIR.glob('*.tsv'))
log(f"\nDONE. {len(matrix_files)} matrices in {elapsed_total/3600:.1f}h")
log(f"  ok={ok_count}, cached={cached_count}, errors={err_count}")

spark.stop()
log("Spark stopped. Extraction complete.")
