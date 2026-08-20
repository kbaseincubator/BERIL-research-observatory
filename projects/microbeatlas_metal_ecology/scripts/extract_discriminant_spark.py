#!/usr/bin/env python3
"""
extract_discriminant_spark.py — JupyterHub Spark extraction for discriminant PGLS control

Run on JupyterHub (requires kbase_ke_pangenome access):
    # In a JupyterHub notebook cell:
    exec(open('scripts/extract_discriminant_spark.py').read())

Extracts genus-level counts for 19 discriminant metal-dependent / metal-sensing KOs.
These genes were excluded from the 94-KO list because they are metal-SENSING or
metal-DEPENDENT (require metals as cofactors) rather than metal-resistance genes.

Outputs:
    data/discriminant_gene_detail.csv   — per gene-cluster hits (analogous to metal_gene_detail.csv)
    data/species_discriminant_metal.csv — per-species aggregated counts
    data/genus_discriminant_metal.csv   — per-genus aggregated counts for PGLS
"""

from pathlib import Path
import pandas as pd

DATA = Path('data')

# ─── 1. Load discriminant KO list ────────────────────────────────────────────
disc_df = pd.read_csv(DATA / 'discriminant_metabolism_kos.csv')
DISC_KOS = disc_df['ko_id'].tolist()

# Build KO → metals_needed lookup
ko_to_metals = {}
for _, row in disc_df.iterrows():
    metals = [m.strip() for m in str(row['metals_needed']).split(';')]
    ko_to_metals[row['ko_id']] = metals

ko_in_list = ', '.join(f"'{ko}'" for ko in DISC_KOS)
print(f"Discriminant KOs to query: {len(DISC_KOS)}")
print(f"  seed_homeostasis: {(disc_df['category']=='seed_homeostasis').sum()}")
print(f"  metal_dependent_enzyme: {(disc_df['category']=='metal_dependent_enzyme').sum()}")

# ─── 2. Spark query: discriminant KO × gene_cluster ─────────────────────────
disc_detail_path = DATA / 'discriminant_gene_detail.csv'

if disc_detail_path.exists():
    disc_detail = pd.read_csv(disc_detail_path)
    print(f"\nLoaded {len(disc_detail):,} gene clusters from cache.")
else:
    print(f"\nQuerying Spark for {len(DISC_KOS)} discriminant KOs...")
    disc_spark = spark.sql(f'''
        SELECT
            ba.gene_cluster_id,
            ba.kegg_orthology_id,
            ba.gene       AS gene_name,
            ba.product    AS gene_product,
            gc.gtdb_species_clade_id,
            gc.is_core,
            gc.is_auxiliary
        FROM kbase_ke_pangenome.bakta_annotations ba
        JOIN kbase_ke_pangenome.gene_cluster gc
          ON ba.gene_cluster_id = gc.gene_cluster_id
        WHERE ba.kegg_orthology_id IN ({ko_in_list})
    ''')
    disc_detail = disc_spark.toPandas()

    # Annotate with category and metals
    disc_detail = disc_detail.merge(
        disc_df[['ko_id', 'category', 'metals_needed']],
        left_on='kegg_orthology_id', right_on='ko_id', how='left'
    ).drop(columns=['ko_id'])

    disc_detail.to_csv(disc_detail_path, index=False)
    n_found = disc_detail['kegg_orthology_id'].nunique()
    print(f"Found {len(disc_detail):,} gene clusters; {n_found}/{len(DISC_KOS)} KOs present.")
    print(disc_detail['kegg_orthology_id'].value_counts().head(10).to_string())

# ─── 3. Load GTDB taxonomy bridge ────────────────────────────────────────────
gtdb_tax = pd.read_csv(DATA / 'gtdb_genus_taxonomy.csv')
# gtdb_genus_taxonomy.csv has: gtdb_species_clade_id, GTDB_species, gtdb_genus, gtdb_phylum, clade_genome_count

disc_ann = disc_detail.merge(gtdb_tax, on='gtdb_species_clade_id', how='left')
disc_ann = disc_ann.dropna(subset=['gtdb_genus'])

print(f"\nAnnotated: {len(disc_ann):,} entries × {disc_ann['gtdb_species_clade_id'].nunique():,} species clades")

# ─── 4. One-per-species subsampling ─────────────────────────────────────────
# Aggregate to species clade first (same method as NB01)
def ko_to_metal_set(ko):
    return set(ko_to_metals.get(ko, ['unknown']))

# Per species: count distinct KO-metal combinations (= n_discriminant_types)
# and distinct KOs (= n_discriminant_clusters)
species_agg = (
    disc_ann
    .groupby(['gtdb_species_clade_id', 'GTDB_species', 'gtdb_genus'], as_index=False)
    .agg(
        n_discriminant_clusters=('kegg_orthology_id', 'nunique'),
        n_discriminant_types=('metals_needed', lambda x: len(set(
            m.strip() for metals in x for m in str(metals).split(';')
        ))),
        has_sod=('kegg_orthology_id', lambda x: int(any(k in {'K04564','K04565'} for k in x))),
        has_catalase=('kegg_orthology_id', lambda x: int('K03781' in set(x))),
        has_cox=('kegg_orthology_id', lambda x: int(any(k in {'K02274','K02275','K00404'} for k in x))),
        has_fur=('kegg_orthology_id', lambda x: int('K06189' in set(x))),
        has_znuABC=('kegg_orthology_id', lambda x: int(any(k in {'K09815','K09816','K09817'} for k in x))),
        has_ferredoxin=('kegg_orthology_id', lambda x: int('K05524' in set(x))),
    )
)

species_agg.to_csv(DATA / 'species_discriminant_metal.csv', index=False)
print(f"\nSpecies-level: {len(species_agg):,} species clades with discriminant genes")
print(f"  Median discriminant metal types per species: {species_agg['n_discriminant_types'].median():.1f}")
print(f"  Median discriminant gene clusters: {species_agg['n_discriminant_clusters'].median():.1f}")

# ─── 5. Aggregate to genus (one-per-species mean) ───────────────────────────
genus_agg = (
    species_agg
    .groupby('gtdb_genus', as_index=False)
    .agg(
        n_species_with_discriminant=('gtdb_species_clade_id', 'count'),
        mean_n_discriminant_clusters=('n_discriminant_clusters', 'mean'),
        mean_n_discriminant_types=('n_discriminant_types', 'mean'),
        mean_has_sod=('has_sod', 'mean'),
        mean_has_catalase=('has_catalase', 'mean'),
        mean_has_cox=('has_cox', 'mean'),
        mean_has_fur=('has_fur', 'mean'),
        mean_has_znuABC=('has_znuABC', 'mean'),
        mean_has_ferredoxin=('has_ferredoxin', 'mean'),
    )
)

# Normalise genus name for tree matching
genus_agg['genus_lower'] = genus_agg['gtdb_genus'].str.lower()

genus_agg.to_csv(DATA / 'genus_discriminant_metal.csv', index=False)
print(f"\nGenus-level: {len(genus_agg):,} genera with discriminant gene data")
print(f"  Mean discriminant types: {genus_agg['mean_n_discriminant_types'].mean():.2f}")
print(f"  SD: {genus_agg['mean_n_discriminant_types'].std():.2f}")
print(f"\nSaved: data/species_discriminant_metal.csv")
print(f"Saved: data/genus_discriminant_metal.csv")
print(f"\nNext step: run Rscript scripts/discriminant_pgls.R data/")
