#!/usr/bin/env python
"""
Map FB organism names to pangenome genome IDs.

Strategy: Query fitnessbrowser organism table and GapMind genomes,
then match by species/strain names.
"""

import pandas as pd
from get_spark_session import get_spark_session

# Known mappings for common FB organisms (from literature/databases)
KNOWN_MAPPINGS = {
    'Keio': 'GCF_000005845.2',  # E. coli K-12 substr. MG1655
    'DvH': 'GCF_000195755.1',   # Desulfovibrio vulgaris str. Hildenborough
    'MR1': 'GCF_000146165.2',   # Shewanella oneidensis MR-1
    'Putida': 'GCF_000007565.2', # Pseudomonas putida KT2440
    'PS': 'GCF_000006765.1',     # Pseudomonas aeruginosa PAO1
}

def main():
    spark = get_spark_session()

    # Get FB organism metadata
    print("Querying Fitness Browser organisms...")
    fb_orgs = spark.sql("""
        SELECT orgId, genus, species, strain, taxonomyId
        FROM kescience_fitnessbrowser.organism
        ORDER BY orgId
    """).toPandas()

    print(f"✅ Retrieved {len(fb_orgs)} FB organisms")

    # Get sample of genomes from GapMind to understand IDs
    print("\nQuerying GapMind for genome sample...")
    gm_genomes = spark.sql("""
        SELECT DISTINCT genome_id
        FROM kbase_ke_pangenome.gapmind_pathways
        LIMIT 1000
    """).toPandas()

    # Get genome metadata for matched ones
    genome_ids = "','".join(gm_genomes['genome_id'].tolist())
    genome_metadata = spark.sql(f"""
        SELECT genome_id, gtdb_species_clade_id, gtdb_taxonomy_id
        FROM kbase_ke_pangenome.genome
        WHERE genome_id IN ('{genome_ids}')
    """).toPandas()

    print(f"✅ Retrieved {len(genome_metadata)} genome metadata records")
    print("\nSample genomes:")
    print(genome_metadata.head(10))

    # Create mapping using known mappings as seed
    fb_genome_map = []
    for _, org in fb_orgs.iterrows():
        org_id = org['orgId']

        if org_id in KNOWN_MAPPINGS:
            genome_id = KNOWN_MAPPINGS[org_id]
            match_method = 'known_mapping'
        else:
            genome_id = None
            match_method = 'no_match'

        fb_genome_map.append({
            'orgId': org_id,
            'genome_id': genome_id,
            'genus': org['genus'],
            'species': org['species'],
            'strain': org['strain'],
            'taxonomyId': org['taxonomyId'],
            'match_method': match_method
        })

    mapping_df = pd.DataFrame(fb_genome_map)

    # Save
    output_file = "../data/fb_genome_mapping.tsv"
    mapping_df.to_csv(output_file, sep='\t', index=False)

    print(f"\n✅ Saved mapping to {output_file}")
    print(f"   Matched: {mapping_df['genome_id'].notna().sum()}")
    print(f"   Unmatched: {mapping_df['genome_id'].isna().sum()}")

    spark.stop()

if __name__ == '__main__':
    main()
