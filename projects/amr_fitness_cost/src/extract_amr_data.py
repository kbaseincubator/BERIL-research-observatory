#!/usr/bin/env python3
"""
Extract bakta_amr data for gene clusters linked to Fitness Browser genes.

Queries BERDL via Spark Connect to get:
  1. bakta_amr annotations for FB-linked gene clusters (Tier 1)
  2. bakta_annotations with AMR-related products for FB-linked clusters (Tier 2)

Usage:
  python src/extract_amr_data.py
"""

import os
import sys

import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(os.path.dirname(PROJECT_DIR))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

FB_LINK_PATH = os.path.join(
    REPO_DIR, "projects", "conservation_vs_fitness", "data", "fb_pangenome_link.tsv"
)


def main():
    from berdl_notebook_utils.setup_spark_session import get_spark_session

    spark = get_spark_session()
    os.makedirs(DATA_DIR, exist_ok=True)

    # Load FB-pangenome link table
    fb_link = pd.read_csv(FB_LINK_PATH, sep="\t")
    print(f"FB-pangenome link: {len(fb_link):,} links, "
          f"{fb_link['gene_cluster_id'].nunique():,} unique clusters, "
          f"{fb_link['orgId'].nunique()} organisms")

    # Register FB cluster IDs as temp view for Spark joins
    cluster_ids = fb_link["gene_cluster_id"].unique().tolist()

    # --- Tier 1: bakta_amr hits ---
    print("\n--- Tier 1: bakta_amr for FB-linked clusters ---")

    # Query in batches (Spark IN clause has limits)
    batch_size = 5000
    amr_rows = []
    for i in range(0, len(cluster_ids), batch_size):
        batch = cluster_ids[i : i + batch_size]
        id_list = ",".join(f"'{cid}'" for cid in batch)
        query = f"""
            SELECT gene_cluster_id, amr_gene, amr_product, method,
                   identity, query_cov, subject_cov, accession
            FROM kbase_ke_pangenome.bakta_amr
            WHERE gene_cluster_id IN ({id_list})
        """
        df = spark.sql(query).toPandas()
        amr_rows.append(df)
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Batch {i // batch_size + 1}/{(len(cluster_ids) + batch_size - 1) // batch_size}")

    amr_df = pd.concat(amr_rows, ignore_index=True) if amr_rows else pd.DataFrame()
    print(f"  Found {len(amr_df)} bakta_amr hits across "
          f"{amr_df['gene_cluster_id'].nunique()} clusters")

    amr_path = os.path.join(DATA_DIR, "bakta_amr_fb_clusters.csv")
    amr_df.to_csv(amr_path, index=False)
    print(f"  Saved to {amr_path}")

    # --- Tier 2: bakta_annotations with AMR-related products ---
    print("\n--- Tier 2: bakta_annotations AMR keywords for FB-linked clusters ---")

    # AMR-related product keywords (specific enough to avoid metabolic enzymes)
    amr_keywords_query = """
        SELECT gene_cluster_id, gene, product, ec, go, cog_id, cog_category,
               kegg_orthology_id, uniref100, uniref90, uniref50
        FROM kbase_ke_pangenome.bakta_annotations
        WHERE gene_cluster_id IN ({id_list})
        AND (
            LOWER(product) LIKE '%beta-lactamase%'
            OR LOWER(product) LIKE '%aminoglycoside%'
            OR LOWER(product) LIKE '%chloramphenicol acetyltransferase%'
            OR LOWER(product) LIKE '%chloramphenicol efflux%'
            OR LOWER(product) LIKE '%tetracycline efflux%'
            OR LOWER(product) LIKE '%tetracycline resistance%'
            OR LOWER(product) LIKE '%macrolide efflux%'
            OR LOWER(product) LIKE '%erythromycin esterase%'
            OR LOWER(product) LIKE '%vancomycin resistance%'
            OR LOWER(product) LIKE '%rifampin%'
            OR LOWER(product) LIKE '%multidrug efflux%'
            OR LOWER(product) LIKE '%multidrug resistance%'
            OR LOWER(product) LIKE '%antibiotic efflux%'
            OR LOWER(product) LIKE '%antibiotic resistance%'
            OR LOWER(product) LIKE '%drug resistance%'
            OR (LOWER(product) LIKE '%efflux pump%'
                AND (LOWER(product) LIKE '%rnd%'
                     OR LOWER(product) LIKE '%multidrug%'
                     OR LOWER(product) LIKE '%antibiotic%'
                     OR LOWER(product) LIKE '%resistance%'))
            OR LOWER(product) LIKE '%fosfomycin%resistance%'
            OR LOWER(product) LIKE '%streptogramin%'
            OR LOWER(product) LIKE '%sulfonamide%resistance%'
            OR LOWER(product) LIKE '%trimethoprim%resistance%'
            OR LOWER(product) LIKE '%mercury resistance%'
            OR LOWER(product) LIKE '%mercury reductase%'
            OR LOWER(product) LIKE '%arsenic resistance%'
            OR LOWER(product) LIKE '%arsenate reductase%'
            OR LOWER(product) LIKE '%copper resistance%'
            OR LOWER(product) LIKE '%chromate resistance%'
            OR LOWER(product) LIKE '%silver resistance%'
            OR LOWER(product) LIKE '%tellurite resistance%'
        )
    """

    annot_rows = []
    for i in range(0, len(cluster_ids), batch_size):
        batch = cluster_ids[i : i + batch_size]
        id_list = ",".join(f"'{cid}'" for cid in batch)
        query = amr_keywords_query.format(id_list=id_list)
        df = spark.sql(query).toPandas()
        annot_rows.append(df)

    annot_df = pd.concat(annot_rows, ignore_index=True) if annot_rows else pd.DataFrame()
    print(f"  Found {len(annot_df)} AMR-keyword annotation hits across "
          f"{annot_df['gene_cluster_id'].nunique()} clusters")

    annot_path = os.path.join(DATA_DIR, "bakta_annotations_amr_keywords.csv")
    annot_df.to_csv(annot_path, index=False)
    print(f"  Saved to {annot_path}")

    print("\nDone. Next: run notebooks/01_data_assembly.ipynb")


if __name__ == "__main__":
    main()
