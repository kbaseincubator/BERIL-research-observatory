#!/usr/bin/env python3
"""
Extract all 132.5M gene cluster representative protein sequences from BERDL
and write them as FASTA files chunked for parallel Bakta annotation.

Outputs:
  - FASTA chunks: data/bakta_reannotation/fasta_chunks/chunk_NNN.fasta
  - Metadata:     data/bakta_reannotation/extraction_manifest.json

Strategy:
  - Query species list with cluster counts
  - Group species into batches, extract each batch via Spark
  - Accumulate into FASTA files of ~2M sequences each
  - Upload chunks to MinIO for CTS processing

Requires: BERDL JupyterHub (berdl_notebook_utils)
"""

import json
import os
import sys
import time
from pathlib import Path

# --- Config ---
CHUNK_SIZE = 2_000_000  # sequences per FASTA chunk
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "fasta_chunks"
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "extraction_manifest.json"
SPECIES_BATCH_SIZE = 50  # query this many species per Spark call

# --- Setup ---
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()

# --- Step 1: Get species list with cluster counts ---
print("Getting species list with cluster counts...")
t0 = time.time()
species_df = spark.sql("""
    SELECT gtdb_species_clade_id, COUNT(*) as n_clusters
    FROM kbase_ke_pangenome.gene_cluster
    WHERE faa_sequence IS NOT NULL AND faa_sequence != ''
    GROUP BY gtdb_species_clade_id
    ORDER BY gtdb_species_clade_id
""").collect()

species_list = [(r['gtdb_species_clade_id'], r['n_clusters']) for r in species_df]
total_seqs = sum(n for _, n in species_list)
n_species = len(species_list)
print(f"  {n_species:,} species, {total_seqs:,} total sequences")
print(f"  Species query took {time.time()-t0:.0f}s")

# --- Step 2: Extract sequences species-by-species, write FASTA chunks ---
print(f"\nExtracting sequences into chunks of {CHUNK_SIZE:,}...")

chunk_idx = 0
chunk_path = OUTPUT_DIR / f"chunk_{chunk_idx:03d}.fasta"
chunk_fh = open(chunk_path, 'w')
chunk_count = 0
total_written = 0
species_processed = 0
manifest_chunks = []
chunk_species = []  # species in current chunk

t_start = time.time()
t_last_report = t_start

# Process species in batches for efficient Spark queries
for batch_start in range(0, n_species, SPECIES_BATCH_SIZE):
    batch = species_list[batch_start:batch_start + SPECIES_BATCH_SIZE]
    batch_ids = [sid for sid, _ in batch]
    batch_expected = sum(n for _, n in batch)

    # Build SQL with escaped species IDs
    id_list = "','".join(sid.replace("'", "''") for sid in batch_ids)
    query = f"""
        SELECT gene_cluster_id, faa_sequence, gtdb_species_clade_id
        FROM kbase_ke_pangenome.gene_cluster
        WHERE gtdb_species_clade_id IN ('{id_list}')
          AND faa_sequence IS NOT NULL AND faa_sequence != ''
    """

    try:
        rows = spark.sql(query).collect()
    except Exception as e:
        print(f"  ERROR querying batch starting at {batch_start}: {e}")
        print(f"  Species: {batch_ids[:3]}...")
        # Try one by one as fallback
        rows = []
        for sid, _ in batch:
            try:
                sid_escaped = sid.replace("'", "''")
                q = f"""
                    SELECT gene_cluster_id, faa_sequence, gtdb_species_clade_id
                    FROM kbase_ke_pangenome.gene_cluster
                    WHERE gtdb_species_clade_id = '{sid_escaped}'
                      AND faa_sequence IS NOT NULL AND faa_sequence != ''
                """
                rows.extend(spark.sql(q).collect())
            except Exception as e2:
                print(f"    SKIP species {sid}: {e2}")

    # Write sequences to FASTA
    for r in rows:
        if chunk_count >= CHUNK_SIZE:
            # Close current chunk
            chunk_fh.close()
            manifest_chunks.append({
                'chunk': f"chunk_{chunk_idx:03d}.fasta",
                'n_sequences': chunk_count,
                'species': chunk_species,
            })
            print(f"  Wrote chunk_{chunk_idx:03d}.fasta ({chunk_count:,} seqs)")

            # Open next chunk
            chunk_idx += 1
            chunk_path = OUTPUT_DIR / f"chunk_{chunk_idx:03d}.fasta"
            chunk_fh = open(chunk_path, 'w')
            chunk_count = 0
            chunk_species = []

        # Write FASTA entry
        chunk_fh.write(f">{r['gene_cluster_id']}\n")
        seq = r['faa_sequence']
        for i in range(0, len(seq), 70):
            chunk_fh.write(seq[i:i+70] + '\n')
        chunk_count += 1
        total_written += 1

        if r['gtdb_species_clade_id'] not in chunk_species:
            chunk_species.append(r['gtdb_species_clade_id'])

    species_processed += len(batch)

    # Progress report every 60 seconds
    now = time.time()
    if now - t_last_report > 60:
        elapsed = now - t_start
        rate = total_written / elapsed
        eta = (total_seqs - total_written) / rate if rate > 0 else 0
        pct = total_written / total_seqs * 100
        print(f"  Progress: {total_written:>12,} / {total_seqs:,} ({pct:.1f}%) "
              f"| {species_processed:,}/{n_species:,} species "
              f"| {rate:.0f} seq/s | ETA {eta/60:.0f} min")
        t_last_report = now

# Close final chunk
chunk_fh.close()
if chunk_count > 0:
    manifest_chunks.append({
        'chunk': f"chunk_{chunk_idx:03d}.fasta",
        'n_sequences': chunk_count,
        'species': chunk_species,
    })
    print(f"  Wrote chunk_{chunk_idx:03d}.fasta ({chunk_count:,} seqs)")

elapsed = time.time() - t_start

# --- Step 3: Write manifest ---
manifest = {
    'total_sequences': total_written,
    'total_species': n_species,
    'chunk_size_target': CHUNK_SIZE,
    'n_chunks': chunk_idx + 1,
    'output_dir': str(OUTPUT_DIR),
    'extraction_time_sec': round(elapsed),
    'chunks': manifest_chunks,
}

with open(MANIFEST_PATH, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"\n{'='*60}")
print(f"EXTRACTION COMPLETE")
print(f"{'='*60}")
print(f"  Total sequences: {total_written:,}")
print(f"  Total species:   {n_species:,}")
print(f"  Chunks:          {chunk_idx + 1}")
print(f"  Time:            {elapsed/60:.1f} min")
print(f"  Manifest:        {MANIFEST_PATH}")
print(f"  FASTA dir:       {OUTPUT_DIR}")
print(f"{'='*60}")
