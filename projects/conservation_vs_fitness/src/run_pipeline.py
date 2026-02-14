#!/usr/bin/env python3
"""
Run NB01 + NB02 pipeline: organism mapping + FASTA extraction.

Uses BERDL Spark Connect session to query the data lakehouse.
Downloads FB protein sequences from the Fitness Browser website.

Usage: python3 src/run_pipeline.py
"""

import pandas as pd
import urllib.request
import sys
import os
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
FB_FASTA_DIR = DATA_DIR / 'fb_fastas'
SPECIES_FASTA_DIR = DATA_DIR / 'species_fastas'

FB_FASTA_DIR.mkdir(parents=True, exist_ok=True)
SPECIES_FASTA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'diamond_hits').mkdir(parents=True, exist_ok=True)

# ============================================================================
# Connect to Spark
# ============================================================================
print("=" * 60)
print("CONNECTING TO SPARK")
print("=" * 60)

from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
print("Spark session ready")

# Quick check
orgs_check = spark.sql("SELECT COUNT(*) as cnt FROM kescience_fitnessbrowser.organism").toPandas()
print(f"Fitness browser organisms: {orgs_check['cnt'][0]}")

# ============================================================================
# PHASE 1: Download FB protein sequences
# ============================================================================
print("\n" + "=" * 60)
print("PHASE 1: DOWNLOAD FB PROTEIN SEQUENCES")
print("=" * 60)

AASEQS_URL = 'https://fit.genomics.lbl.gov/cgi_data/aaseqs'
aaseqs_path = DATA_DIR / 'fb_aaseqs_all.fasta'

if not aaseqs_path.exists():
    print(f"Downloading from {AASEQS_URL}...")
    urllib.request.urlretrieve(AASEQS_URL, aaseqs_path)
    print(f"Downloaded to {aaseqs_path}")
else:
    print(f"Already downloaded: {aaseqs_path}")

# Count and split into per-organism FASTAs
print("Splitting into per-organism FASTAs...")
org_files = {}
org_counts = {}

with open(aaseqs_path) as f:
    current_org = None
    for line in f:
        if line.startswith('>'):
            header = line[1:].strip()
            orgId = header.split(':')[0]
            current_org = orgId
            if orgId not in org_files:
                fasta_path = FB_FASTA_DIR / f"{orgId}.fasta"
                org_files[orgId] = open(fasta_path, 'w')
                org_counts[orgId] = 0
            org_files[orgId].write(line)
            org_counts[orgId] += 1
        else:
            if current_org and current_org in org_files:
                org_files[current_org].write(line)

for fh in org_files.values():
    fh.close()

total_seqs = sum(org_counts.values())
print(f"Split {total_seqs:,} sequences into {len(org_counts)} organism FASTAs")

# ============================================================================
# PHASE 2: Load FB organisms and scaffolds
# ============================================================================
print("\n" + "=" * 60)
print("PHASE 2: ORGANISM MAPPING (NB01)")
print("=" * 60)

fb_orgs = spark.sql("""
    SELECT orgId, genus, species, strain, taxonomyId
    FROM kescience_fitnessbrowser.organism
    ORDER BY genus, species
""").toPandas()
print(f"Total FB organisms: {len(fb_orgs)}")

fb_scaffolds = spark.sql("""
    SELECT DISTINCT orgId, scaffoldId
    FROM kescience_fitnessbrowser.gene
""").toPandas()
print(f"Scaffold entries: {len(fb_scaffolds)}")

# ============================================================================
# Strategy 1: NCBI taxid matching
# ============================================================================
print("\n--- Strategy 1: NCBI taxid matching ---")

tax_ids = fb_orgs['taxonomyId'].dropna().unique().tolist()
tax_id_str = ','.join([str(int(float(t))) for t in tax_ids])

taxid_matches = spark.sql(f"""
    SELECT DISTINCT
        m.ncbi_taxid,
        m.ncbi_species_taxid,
        m.accession,
        g.gtdb_species_clade_id
    FROM kbase_ke_pangenome.gtdb_metadata m
    JOIN kbase_ke_pangenome.genome g ON m.accession = g.genome_id
    WHERE CAST(m.ncbi_species_taxid AS INT) IN ({tax_id_str})
       OR CAST(m.ncbi_taxid AS INT) IN ({tax_id_str})
""").toPandas()

print(f"Taxid matches: {len(taxid_matches)} genome-clade pairs")

taxid_mapping = []
for _, org in fb_orgs.iterrows():
    tid = org['taxonomyId']
    if pd.isna(tid):
        continue
    tid = int(float(tid))
    hits = taxid_matches[
        (taxid_matches['ncbi_species_taxid'].astype(str).str.strip() == str(tid)) |
        (taxid_matches['ncbi_taxid'].astype(str).str.strip() == str(tid))
    ]
    for clade in hits['gtdb_species_clade_id'].unique():
        pg_genomes = hits[hits['gtdb_species_clade_id'] == clade]['accession'].tolist()
        taxid_mapping.append({
            'orgId': org['orgId'], 'genus': org['genus'],
            'species': org['species'], 'strain': org['strain'],
            'taxonomyId': tid, 'gtdb_species_clade_id': clade,
            'pg_genome_id': pg_genomes[0], 'match_method': 'taxid'
        })

taxid_df = pd.DataFrame(taxid_mapping)
taxid_orgs = taxid_df['orgId'].nunique() if len(taxid_df) > 0 else 0
print(f"FB organisms matched by taxid: {taxid_orgs}/48")

# ============================================================================
# Strategy 2: NCBI organism name matching
# ============================================================================
print("\n--- Strategy 2: NCBI organism name matching ---")

name_mapping = []
for _, org in fb_orgs.iterrows():
    orgId = org['orgId']
    genus = org['genus']
    species = org['species']
    strain = org['strain']

    if pd.isna(genus) or pd.isna(species):
        continue

    # Escape single quotes in names
    genus_safe = str(genus).replace("'", "''")
    species_safe = str(species).replace("'", "''")

    query = f"""
        SELECT DISTINCT m.accession, g.gtdb_species_clade_id, m.ncbi_organism_name
        FROM kbase_ke_pangenome.gtdb_metadata m
        JOIN kbase_ke_pangenome.genome g ON m.accession = g.genome_id
        WHERE m.ncbi_organism_name LIKE '%{genus_safe}%{species_safe}%'
        LIMIT 100
    """
    try:
        hits = spark.sql(query).toPandas()
    except Exception as e:
        print(f"  WARNING: query failed for {orgId} ({genus} {species}): {e}")
        continue

    # Try strain-specific match
    if not pd.isna(strain) and str(strain).strip() and len(hits) > 0:
        strain_safe = str(strain).replace("'", "''")
        try:
            strain_hits = spark.sql(f"""
                SELECT DISTINCT m.accession, g.gtdb_species_clade_id, m.ncbi_organism_name
                FROM kbase_ke_pangenome.gtdb_metadata m
                JOIN kbase_ke_pangenome.genome g ON m.accession = g.genome_id
                WHERE m.ncbi_organism_name LIKE '%{genus_safe}%{species_safe}%{strain_safe}%'
                LIMIT 100
            """).toPandas()
            if len(strain_hits) > 0:
                hits = strain_hits
        except Exception:
            pass

    for clade in hits['gtdb_species_clade_id'].unique():
        clade_hits = hits[hits['gtdb_species_clade_id'] == clade]
        name_mapping.append({
            'orgId': orgId, 'genus': genus, 'species': species,
            'strain': strain, 'taxonomyId': org['taxonomyId'],
            'gtdb_species_clade_id': clade,
            'pg_genome_id': clade_hits['accession'].iloc[0],
            'match_method': 'ncbi_name'
        })

name_df = pd.DataFrame(name_mapping)
name_orgs = name_df['orgId'].nunique() if len(name_df) > 0 else 0
print(f"FB organisms matched by NCBI name: {name_orgs}/48")

if len(taxid_df) > 0 and len(name_df) > 0:
    new_by_name = set(name_df['orgId']) - set(taxid_df['orgId'])
    print(f"New organisms found only by NCBI name: {len(new_by_name)}")
    for oid in sorted(new_by_name):
        row = name_df[name_df['orgId'] == oid].iloc[0]
        print(f"  {oid}: {row['genus']} {row['species']}")

# ============================================================================
# Strategy 3: Scaffold accession matching (only for unmatched organisms)
# ============================================================================
print("\n--- Strategy 3: Scaffold accession matching ---")

already_matched = set()
if len(taxid_df) > 0:
    already_matched |= set(taxid_df['orgId'])
if len(name_df) > 0:
    already_matched |= set(name_df['orgId'])

unmatched_orgs = fb_orgs[~fb_orgs['orgId'].isin(already_matched)]
print(f"Unmatched after strategies 1+2: {len(unmatched_orgs)} organisms")

scaffold_mapping = []
refseq_prefixes = ('NC_', 'NZ_', 'CP', 'AE', 'AP', 'BA', 'BX', 'CR', 'FN', 'FP', 'HE', 'AL', 'AM')

# Only try scaffold matching for unmatched organisms (avoids slow gene table scans)
for _, org in unmatched_orgs.iterrows():
    orgId = org['orgId']
    org_scaffolds = fb_scaffolds[fb_scaffolds['orgId'] == orgId]['scaffoldId'].tolist()
    refseq_scaffolds = [s for s in org_scaffolds if any(s.startswith(p) for p in refseq_prefixes)]

    if not refseq_scaffolds:
        print(f"  {orgId}: no RefSeq scaffolds ({org_scaffolds})")
        continue

    scaffold = refseq_scaffolds[0]
    print(f"  {orgId}: trying scaffold {scaffold}...", end='', flush=True)
    try:
        # Use gene_cluster table instead of gene table — much smaller
        # gene_cluster_id is derived from contig accession
        hits = spark.sql(f"""
            SELECT DISTINCT gc.gtdb_species_clade_id
            FROM kbase_ke_pangenome.gene_cluster gc
            WHERE gc.gene_cluster_id LIKE '{scaffold}%'
            LIMIT 10
        """).toPandas()
    except Exception as e:
        print(f" FAILED: {e}")
        continue

    if len(hits) == 0:
        # Try without version suffix (e.g., NC_003155 instead of NC_003155.5)
        scaffold_base = scaffold.split('.')[0] if '.' in scaffold else scaffold
        if scaffold_base != scaffold:
            try:
                hits = spark.sql(f"""
                    SELECT DISTINCT gc.gtdb_species_clade_id
                    FROM kbase_ke_pangenome.gene_cluster gc
                    WHERE gc.gene_cluster_id LIKE '{scaffold_base}%'
                    LIMIT 10
                """).toPandas()
            except Exception:
                pass

    if len(hits) > 0:
        for clade in hits['gtdb_species_clade_id'].unique():
            scaffold_mapping.append({
                'orgId': orgId, 'genus': org['genus'], 'species': org['species'],
                'strain': org['strain'], 'taxonomyId': org['taxonomyId'],
                'gtdb_species_clade_id': clade,
                'pg_genome_id': '',  # not available from gene_cluster lookup
                'match_method': 'scaffold'
            })
        print(f" matched -> {hits['gtdb_species_clade_id'].tolist()}")
    else:
        print(f" no match")

scaffold_df = pd.DataFrame(scaffold_mapping)
scaffold_orgs = scaffold_df['orgId'].nunique() if len(scaffold_df) > 0 else 0
print(f"FB organisms matched by scaffold: {scaffold_orgs}")

if len(scaffold_df) > 0:
    new_by_scaffold = set(scaffold_df['orgId']) - already_matched
    print(f"New organisms found only by scaffold: {len(new_by_scaffold)}")
    for oid in sorted(new_by_scaffold):
        row = scaffold_df[scaffold_df['orgId'] == oid].iloc[0]
        print(f"  {oid}: {row['genus']} {row['species']}")

# ============================================================================
# Combine all strategies
# ============================================================================
print("\n--- Combining all strategies ---")

all_mappings = pd.concat([taxid_df, name_df, scaffold_df], ignore_index=True)

method_priority = {'taxid': 0, 'scaffold': 1, 'ncbi_name': 2}
all_mappings['priority'] = all_mappings['match_method'].map(method_priority)
all_mappings = all_mappings.sort_values('priority').drop_duplicates(
    subset=['orgId', 'gtdb_species_clade_id'], keep='first'
).drop(columns='priority').sort_values(['orgId', 'gtdb_species_clade_id'])

print(f"Combined: {len(all_mappings)} orgId x clade pairs")
print(f"Unique FB organisms matched: {all_mappings['orgId'].nunique()}/48")
print(f"Unique pangenome clades: {all_mappings['gtdb_species_clade_id'].nunique()}")
print(f"Match method breakdown:")
print(all_mappings['match_method'].value_counts().to_string())

# QC: unmatched
matched_orgs = set(all_mappings['orgId'])
unmatched = fb_orgs[~fb_orgs['orgId'].isin(matched_orgs)]
print(f"\nUnmatched organisms ({len(unmatched)}):")
for _, row in unmatched.iterrows():
    print(f"  {row['orgId']:25s} {row['genus']} {row['species']} "
          f"(strain={row['strain']}, taxid={row['taxonomyId']})")

# Multi-clade
clades_per_org = all_mappings.groupby('orgId')['gtdb_species_clade_id'].nunique()
multi_clade = clades_per_org[clades_per_org > 1]
print(f"\nMulti-clade organisms: {len(multi_clade)}")
for orgId, n in multi_clade.items():
    clades = all_mappings[all_mappings['orgId'] == orgId]['gtdb_species_clade_id'].tolist()
    print(f"  {orgId}: {n} clades — {clades}")

# Save
output_path = DATA_DIR / 'organism_mapping.tsv'
all_mappings.to_csv(output_path, sep='\t', index=False)
print(f"\nSaved: {output_path}")

mapped_orgs_list = sorted(all_mappings['orgId'].unique())
mapped_clades = sorted(all_mappings['gtdb_species_clade_id'].unique())

# ============================================================================
# PHASE 3: Extract cluster rep FASTAs (NB02)
# ============================================================================
print("\n" + "=" * 60)
print("PHASE 3: EXTRACT CLUSTER REP FASTAs (NB02)")
print("=" * 60)

# Check FB FASTAs exist for mapped organisms
missing_fb = [org for org in mapped_orgs_list if org not in org_counts]
if missing_fb:
    print(f"WARNING: {len(missing_fb)} mapped organisms missing from aaseqs:")
    for org in missing_fb:
        print(f"  {org}")
else:
    print(f"All {len(mapped_orgs_list)} mapped organisms have FB protein FASTAs")

# Get expected cluster counts
clade_str = "','".join(mapped_clades)
expected_counts = spark.sql(f"""
    SELECT gtdb_species_clade_id, no_gene_clusters, no_genomes
    FROM kbase_ke_pangenome.pangenome
    WHERE gtdb_species_clade_id IN ('{clade_str}')
""").toPandas()
print(f"\nExpected cluster counts for {len(expected_counts)} clades")

# Extract cluster rep FASTAs per species
extraction_stats = []

for i, clade_id in enumerate(mapped_clades):
    fasta_path = SPECIES_FASTA_DIR / f"{clade_id}.fasta"

    # Skip if already extracted
    if fasta_path.exists() and fasta_path.stat().st_size > 0:
        n_existing = sum(1 for line in open(fasta_path) if line.startswith('>'))
        extraction_stats.append({
            'clade_id': clade_id, 'n_clusters': n_existing, 'status': 'cached'
        })
        print(f"  [{i+1}/{len(mapped_clades)}] {clade_id}: {n_existing:,} clusters (cached)")
        continue

    # Extract from Spark — single query per clade (partitioned column = fast)
    print(f"  [{i+1}/{len(mapped_clades)}] {clade_id}: extracting...", end='', flush=True)

    cluster_reps = spark.sql(f"""
        SELECT gene_cluster_id, faa_sequence
        FROM kbase_ke_pangenome.gene_cluster
        WHERE gtdb_species_clade_id = '{clade_id}'
          AND faa_sequence IS NOT NULL AND faa_sequence != ''
    """).toPandas()

    if len(cluster_reps) == 0:
        print(f" WARNING - no clusters with sequences!")
        extraction_stats.append({
            'clade_id': clade_id, 'n_clusters': 0, 'status': 'empty'
        })
        continue

    # Write FASTA
    with open(fasta_path, 'w') as f:
        for _, row in cluster_reps.iterrows():
            f.write(f">{row['gene_cluster_id']}\n")
            seq = row['faa_sequence']
            for j in range(0, len(seq), 70):
                f.write(seq[j:j+70] + '\n')

    extraction_stats.append({
        'clade_id': clade_id, 'n_clusters': len(cluster_reps), 'status': 'extracted'
    })
    print(f" {len(cluster_reps):,} clusters")

stats_df = pd.DataFrame(extraction_stats)
print(f"\nExtracted {stats_df['n_clusters'].sum():,} total cluster rep sequences")

# QC: compare to expected
qc = stats_df.merge(expected_counts, left_on='clade_id', right_on='gtdb_species_clade_id', how='left')
if 'no_gene_clusters' in qc.columns:
    qc['pct_extracted'] = (qc['n_clusters'] / qc['no_gene_clusters'] * 100).round(1)
    low_pct = qc[qc['pct_extracted'] < 95]
    if len(low_pct) > 0:
        print(f"\nWARNING: {len(low_pct)} clades with <95% extraction:")
        for _, row in low_pct.iterrows():
            print(f"  {row['clade_id']}: {row['n_clusters']}/{row['no_gene_clusters']} ({row['pct_extracted']}%)")

# ============================================================================
# PHASE 4: Extract cluster metadata for core/aux/singleton classification
# ============================================================================
print("\n" + "=" * 60)
print("PHASE 4: EXTRACT CLUSTER METADATA")
print("=" * 60)

cluster_meta_path = DATA_DIR / 'cluster_metadata.tsv'

if cluster_meta_path.exists() and cluster_meta_path.stat().st_size > 0:
    print(f"Already cached: {cluster_meta_path}")
else:
    # gene_cluster already has is_core, is_auxiliary, is_singleton columns directly
    print("Extracting cluster metadata (is_core/aux/singleton) per clade...")
    all_meta = []
    for i, clade_id in enumerate(mapped_clades):
        print(f"  [{i+1}/{len(mapped_clades)}] {clade_id}...", end='', flush=True)
        meta = spark.sql(f"""
            SELECT gc.gene_cluster_id, gc.gtdb_species_clade_id,
                   gc.is_core, gc.is_auxiliary, gc.is_singleton,
                   p.no_genomes as species_total_genomes
            FROM kbase_ke_pangenome.gene_cluster gc
            JOIN kbase_ke_pangenome.pangenome p
                ON gc.gtdb_species_clade_id = p.gtdb_species_clade_id
            WHERE gc.gtdb_species_clade_id = '{clade_id}'
        """).toPandas()
        if len(meta) > 0:
            all_meta.append(meta)
            print(f" {len(meta):,} clusters")
        else:
            print(" 0 clusters")

    if all_meta:
        cluster_meta = pd.concat(all_meta, ignore_index=True)
        cluster_meta.to_csv(cluster_meta_path, sep='\t', index=False)
        print(f"\nSaved cluster metadata: {len(cluster_meta):,} clusters to {cluster_meta_path}")
    else:
        print("WARNING: No cluster metadata extracted")

print("\n" + "=" * 60)
print("PIPELINE PHASES 1-4 COMPLETE")
print("=" * 60)
print(f"Organism mapping: {output_path}")
print(f"FB FASTAs: {FB_FASTA_DIR}/")
print(f"Species FASTAs: {SPECIES_FASTA_DIR}/")
print(f"Cluster metadata: {cluster_meta_path}")
print(f"\nNext: run src/run_diamond.sh")
