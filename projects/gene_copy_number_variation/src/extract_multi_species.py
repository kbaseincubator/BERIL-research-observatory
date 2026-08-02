"""Extract per-COG copy number stats for a batch of species.

Saves incrementally — if the process dies, we don't lose progress.
Skips species already processed.

Usage:
    python extract_multi_species.py <manifest.csv> <output_dir>
"""

import sys
import time
from pathlib import Path

import pandas as pd
from berdl_notebook_utils.setup_spark_session import get_spark_session


def extract_one(spark, species_prefix, phylum, no_genomes):
    q = f"""
        WITH copies AS (
            SELECT gc.gene_cluster_id, gc.is_core, g.genome_id, COUNT(*) as copy_count
            FROM kbase_ke_pangenome.gene g
            JOIN kbase_ke_pangenome.gene_genecluster_junction j ON g.gene_id = j.gene_id
            JOIN kbase_ke_pangenome.gene_cluster gc ON j.gene_cluster_id = gc.gene_cluster_id
            JOIN kbase_ke_pangenome.genome gm ON g.genome_id = gm.genome_id
            WHERE gm.gtdb_species_clade_id LIKE '{species_prefix}%'
            AND gc.gtdb_species_clade_id LIKE '{species_prefix}%'
            GROUP BY gc.gene_cluster_id, gc.is_core, g.genome_id
        ),
        cluster_stats AS (
            SELECT c.gene_cluster_id, c.is_core, ann.COG_category,
                   COUNT(DISTINCT c.genome_id) as n_carriers,
                   SUM(c.copy_count) as total_copies,
                   SUM(CASE WHEN c.copy_count > 1 THEN 1 ELSE 0 END) as n_multicopy_genomes
            FROM copies c
            LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann ON c.gene_cluster_id = ann.query_name
            GROUP BY c.gene_cluster_id, c.is_core, ann.COG_category
        )
        SELECT COALESCE(COG_category, '_missing') as COG_category, is_core,
               COUNT(*) as n_clusters, SUM(n_carriers) as total_carrier_genomes,
               SUM(total_copies) as total_copies, SUM(n_multicopy_genomes) as total_multicopy_genomes
        FROM cluster_stats GROUP BY COG_category, is_core
    """
    df = spark.sql(q).toPandas()
    df['species_prefix'] = species_prefix
    df['phylum'] = phylum
    df['no_genomes'] = no_genomes
    return df


def main():
    manifest_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(manifest_path)
    print(f'Loaded manifest: {len(manifest)} species', flush=True)

    spark = get_spark_session()
    print('Spark session ready', flush=True)

    n = spark.sql("SHOW TABLES IN kbase_ke_pangenome").count()
    if n == 0:
        raise SystemExit(
            "Namespace sanity check failed: kbase_ke_pangenome has no tables. "
            "The collection may have migrated to the dotted Iceberg form "
            "(kbase.ke_pangenome) — see docs/pitfalls.md 'Namespace Convention "
            "Changed from Underscores to Dots'. Update the SQL to the dotted "
            "form and re-run."
        )
    print(f'Namespace check OK: kbase_ke_pangenome has {n} tables', flush=True)

    t_start = time.time()
    for i, row in manifest.iterrows():
        out_path = output_dir / f'{row.species_prefix}.csv'
        if out_path.exists():
            print(f'[{i+1:2d}/{len(manifest)}] {row.species_prefix:55s} SKIP (already done)', flush=True)
            continue

        t0 = time.time()
        try:
            df = extract_one(spark, row.species_prefix, row.phylum, row.no_genomes)
            df.to_csv(out_path, index=False)
            elapsed = time.time() - t0
            total = time.time() - t_start
            avg = total / (i + 1)
            remaining_min = avg * (len(manifest) - i - 1) / 60
            print(f'[{i+1:2d}/{len(manifest)}] {row.species_prefix:55s} '
                  f'{len(df):3d} rows in {elapsed:6.1f}s '
                  f'(avg {avg:.1f}s, est remaining {remaining_min:.1f} min)', flush=True)
        except Exception as e:
            print(f'[{i+1:2d}/{len(manifest)}] {row.species_prefix:55s} FAILED: {e}', flush=True)

    print(f'\nAll done. Total: {(time.time() - t_start)/60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
