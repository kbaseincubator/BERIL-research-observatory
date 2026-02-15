#!/usr/bin/env python3
"""
Extract essential gene data and BBH ortholog pairs for all 48 FB organisms,
then build ortholog groups via connected components.

Usage: python3 src/extract_data.py
"""

import pandas as pd
import networkx as nx
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Connect to Spark
# ============================================================================
print("Connecting to Spark...")
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
print("Spark ready")

# Get all organisms
all_orgs = spark.sql("""
    SELECT orgId, genus, species, strain, taxonomyId
    FROM kescience_fitnessbrowser.organism
    ORDER BY orgId
""").toPandas()
org_ids = all_orgs['orgId'].tolist()
print(f"Total organisms: {len(org_ids)}")

# ============================================================================
# Step 1: Extract essential gene status for all organisms
# ============================================================================
essential_path = DATA_DIR / 'all_essential_genes.tsv'

if essential_path.exists() and essential_path.stat().st_size > 0:
    print(f"\nCACHED: {essential_path}")
    essential_df = pd.read_csv(essential_path, sep='\t')
    print(f"  {len(essential_df):,} genes, {essential_df['is_essential'].sum():,} essential")
else:
    print("\n=== EXTRACTING ESSENTIAL GENE STATUS ===")
    all_genes = []

    for i, orgId in enumerate(sorted(org_ids)):
        print(f"  [{i+1}/{len(org_ids)}] {orgId}...", end='', flush=True)

        # All type=1 (CDS) genes with coordinates
        genes = spark.sql(f"""
            SELECT orgId, locusId, scaffoldId,
                   CAST(begin AS INT) as gene_begin,
                   CAST(end AS INT) as gene_end,
                   gene, desc
            FROM kescience_fitnessbrowser.gene
            WHERE orgId = '{orgId}' AND type = '1'
        """).toPandas()

        # Genes with fitness data
        fitness_genes = spark.sql(f"""
            SELECT DISTINCT orgId, locusId
            FROM kescience_fitnessbrowser.genefitness
            WHERE orgId = '{orgId}'
        """).toPandas()

        genes['has_fitness'] = genes['locusId'].isin(fitness_genes['locusId'].values)
        genes['is_essential'] = ~genes['has_fitness']
        genes['gene_length'] = abs(genes['gene_end'] - genes['gene_begin']) + 1

        n_essential = genes['is_essential'].sum()
        n_total = len(genes)
        pct = n_essential / n_total * 100 if n_total > 0 else 0
        print(f" {n_total} genes, {n_essential} essential ({pct:.1f}%)")

        all_genes.append(genes)

    essential_df = pd.concat(all_genes, ignore_index=True)
    essential_df.to_csv(essential_path, sep='\t', index=False)
    print(f"\nSaved: {essential_path} ({len(essential_df):,} genes)")

# Summary
n_orgs = essential_df['orgId'].nunique()
n_essential = essential_df['is_essential'].sum()
n_total = len(essential_df)
print(f"\nEssential gene summary: {n_essential:,} / {n_total:,} genes "
      f"({n_essential/n_total*100:.1f}%) across {n_orgs} organisms")

# ============================================================================
# Step 2: Extract BBH ortholog pairs for all organisms
# ============================================================================
bbh_path = DATA_DIR / 'all_bbh_pairs.csv'

if bbh_path.exists() and bbh_path.stat().st_size > 0:
    print(f"\nCACHED: {bbh_path}")
    bbh = pd.read_csv(bbh_path)
    print(f"  {len(bbh):,} BBH pairs")
else:
    print("\n=== EXTRACTING BBH ORTHOLOG PAIRS ===")
    org_list = ", ".join([f"'{o}'" for o in org_ids])

    bbh = spark.sql(f"""
        SELECT orgId1, locusId1, orgId2, locusId2,
               CAST(ratio AS FLOAT) as ratio
        FROM kescience_fitnessbrowser.ortholog
        WHERE orgId1 IN ({org_list})
          AND orgId2 IN ({org_list})
    """).toPandas()

    bbh.to_csv(bbh_path, index=False)
    print(f"Saved: {bbh_path} ({len(bbh):,} BBH pairs)")

n_orgs_in_bbh = len(set(bbh['orgId1'].unique()) | set(bbh['orgId2'].unique()))
print(f"BBH pairs span {n_orgs_in_bbh} organisms")

# ============================================================================
# Step 3: Build ortholog groups via connected components
# ============================================================================
og_path = DATA_DIR / 'all_ortholog_groups.csv'

if og_path.exists() and og_path.stat().st_size > 0:
    print(f"\nCACHED: {og_path}")
    og_df = pd.read_csv(og_path)
    print(f"  {og_df['OG_id'].nunique():,} ortholog groups, {len(og_df):,} gene assignments")
else:
    print("\n=== BUILDING ORTHOLOG GROUPS ===")
    G = nx.Graph()
    for _, row in bbh.iterrows():
        n1 = f"{row['orgId1']}:{row['locusId1']}"
        n2 = f"{row['orgId2']}:{row['locusId2']}"
        G.add_edge(n1, n2, weight=row['ratio'])

    print(f"Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    components = list(nx.connected_components(G))
    print(f"Connected components: {len(components):,}")

    og_records = []
    for og_id, comp in enumerate(components):
        for node in comp:
            org, locus = node.split(':', 1)
            og_records.append({
                'OG_id': f'OG{og_id:05d}',
                'orgId': org,
                'locusId': locus
            })

    og_df = pd.DataFrame(og_records)
    og_df.to_csv(og_path, index=False)
    print(f"Saved: {og_path} ({len(og_df):,} assignments, "
          f"{og_df['OG_id'].nunique():,} OGs)")

# Summary
og_sizes = og_df.groupby('OG_id').size()
og_org_count = og_df.groupby('OG_id')['orgId'].nunique()
print(f"\nOrtholog group summary:")
print(f"  Total OGs: {og_df['OG_id'].nunique():,}")
print(f"  OG size: median={og_sizes.median():.0f}, max={og_sizes.max()}")
print(f"  OGs spanning 2+ organisms: {(og_org_count >= 2).sum():,}")
print(f"  OGs spanning 10+ organisms: {(og_org_count >= 10).sum():,}")
print(f"  OGs spanning all {n_orgs_in_bbh} organisms: "
      f"{(og_org_count >= n_orgs_in_bbh).sum()}")

# ============================================================================
# Step 4: Extract SEED annotations for new organisms
# ============================================================================
# Check which organisms already have annotations cached
existing_seed = Path(PROJECT_DIR.parent / 'conservation_vs_fitness' / 'data' / 'seed_annotations.tsv')
if existing_seed.exists():
    cached_seed = pd.read_csv(existing_seed, sep='\t')
    cached_orgs = set(cached_seed['orgId'].unique())
    new_orgs = [o for o in org_ids if o not in cached_orgs]
else:
    new_orgs = org_ids

seed_path = DATA_DIR / 'all_seed_annotations.tsv'
if seed_path.exists() and seed_path.stat().st_size > 0:
    print(f"\nCACHED: {seed_path}")
else:
    print(f"\n=== EXTRACTING SEED ANNOTATIONS ({len(new_orgs)} new organisms) ===")
    all_seed = []

    # Include existing cached annotations
    if existing_seed.exists():
        all_seed.append(cached_seed)
        print(f"  Loaded {len(cached_seed):,} cached annotations from conservation_vs_fitness")

    for i, orgId in enumerate(sorted(new_orgs)):
        print(f"  [{i+1}/{len(new_orgs)}] {orgId}...", end='', flush=True)
        seed = spark.sql(f"""
            SELECT orgId, locusId, seed_desc
            FROM kescience_fitnessbrowser.seedannotation
            WHERE orgId = '{orgId}'
        """).toPandas()
        all_seed.append(seed)
        print(f" {len(seed)} annotations")

    seed_df = pd.concat(all_seed, ignore_index=True)
    seed_df.to_csv(seed_path, sep='\t', index=False)
    print(f"Saved: {seed_path} ({len(seed_df):,} annotations)")

print("\n=== EXTRACTION COMPLETE ===")
