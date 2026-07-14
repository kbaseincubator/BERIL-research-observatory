"""
Ecotype clustering and COG profiling — standalone script.

Runs the same analysis as NB02 but outside nbconvert to avoid process kills.
Saves results incrementally to data/ directory.

Usage (on BERDL JupyterHub):
    python src/run_clustering.py
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

try:
    from hdbscan import HDBSCAN
    print("HDBSCAN available")
    USE_HDBSCAN = True
except ImportError:
    print("HDBSCAN not available, using KMeans")
    from sklearn.cluster import KMeans
    USE_HDBSCAN = False

from berdl_notebook_utils.setup_spark_session import get_spark_session

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MAX_GENOMES = 300
N_PER_BIN = 5  # 5 per bin = 15 total (feasible at current Spark load)


def cluster_one_species(sp_presence, min_cluster_size=10, n_pcs=50):
    """Cluster genomes within one species by auxiliary gene content."""
    if len(sp_presence) < 100:
        return None, 0, None

    genomes = sorted(sp_presence['genome_id'].unique())
    clusters = sorted(sp_presence['gene_cluster_id'].unique())

    if len(genomes) < 20 or len(clusters) < 10:
        return None, 0, None

    genome_idx = {g: i for i, g in enumerate(genomes)}
    cluster_idx = {c: i for i, c in enumerate(clusters)}

    rows = sp_presence['genome_id'].map(genome_idx).values
    cols = sp_presence['gene_cluster_id'].map(cluster_idx).values
    data = np.ones(len(rows), dtype=np.float32)
    matrix = csr_matrix((data, (rows, cols)), shape=(len(genomes), len(clusters)))

    n_components = min(n_pcs, len(genomes) - 1, len(clusters) - 1)
    if n_components < 2:
        return None, 0, None

    X_pca = PCA(n_components=n_components, random_state=42).fit_transform(matrix.toarray())

    if USE_HDBSCAN:
        labels = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=5).fit_predict(X_pca)
    else:
        best_score, best_labels = -1, np.zeros(len(genomes), dtype=int)
        for k in range(2, min(7, len(genomes) // min_cluster_size + 1)):
            labs = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_pca)
            if len(set(labs)) > 1:
                score = silhouette_score(X_pca, labs)
                if score > best_score:
                    best_score, best_labels = score, labs
        labels = best_labels

    valid_labels = [l for l in set(labels) if l != -1
                    and np.sum(labels == l) >= min_cluster_size]
    if len(valid_labels) < 2:
        return None, 0, None

    valid_mask = np.isin(labels, valid_labels)
    if np.sum(valid_mask) < 20:
        return None, 0, None

    sil = silhouette_score(X_pca[valid_mask], labels[valid_mask])
    ecotype_df = pd.DataFrame({'genome_id': genomes, 'ecotype': labels})
    ecotype_df = ecotype_df[ecotype_df['ecotype'].isin(valid_labels)]
    return ecotype_df, len(valid_labels), sil


def main():
    print("=" * 60)
    print("Ecotype Clustering & COG Profiling")
    print("=" * 60)

    # --- Step 1: Setup ---
    spark = get_spark_session()
    targets = pd.read_csv(os.path.join(DATA_DIR, 'target_species.csv'))

    eligible = targets[(targets['no_genomes'] >= 50) & (targets['no_genomes'] <= MAX_GENOMES)].copy()
    print(f"Total target species: {len(targets)}")
    print(f"Species with 50-{MAX_GENOMES} genomes: {len(eligible)}")

    np.random.seed(42)
    bins = [
        ('50-100',  eligible[(eligible.no_genomes >= 50)  & (eligible.no_genomes < 100)]),
        ('100-200', eligible[(eligible.no_genomes >= 100) & (eligible.no_genomes < 200)]),
        ('200-300', eligible[(eligible.no_genomes >= 200) & (eligible.no_genomes <= 300)]),
    ]
    sample_dfs = []
    for label, df in bins:
        n = min(N_PER_BIN, len(df))
        sample_dfs.append(df.sample(n=n, random_state=42))
        print(f"  {label}: {len(df)} available, sampled {n}")

    eligible = pd.concat(sample_dfs, ignore_index=True)
    species_list = eligible['gtdb_species_clade_id'].tolist()
    species_in = "', '".join(species_list)
    print(f"\nSampled {len(eligible)} species for analysis")

    # --- Step 2: Genome → species mapping ---
    print("\nQuerying genome → species mapping...")
    t0 = time.time()
    genome_species = spark.sql(f"""
        SELECT genome_id, gtdb_species_clade_id AS species
        FROM kbase_ke_pangenome.genome
        WHERE gtdb_species_clade_id IN ('{species_in}')
    """).toPandas()
    print(f"Got {len(genome_species)} genomes across {genome_species['species'].nunique()} species "
          f"in {time.time()-t0:.1f}s")

    # --- Step 3: Auxiliary gene cluster IDs ---
    print("Querying auxiliary gene cluster IDs...")
    t0 = time.time()
    aux_clusters = spark.sql(f"""
        SELECT gtdb_species_clade_id AS species, gene_cluster_id
        FROM kbase_ke_pangenome.gene_cluster
        WHERE gtdb_species_clade_id IN ('{species_in}')
          AND is_auxiliary = true
    """).toPandas()
    print(f"Got {len(aux_clusters):,} auxiliary gene clusters across "
          f"{aux_clusters['species'].nunique()} species in {time.time()-t0:.1f}s")

    aux_cluster_sets = aux_clusters.groupby('species')['gene_cluster_id'].apply(set).to_dict()
    print(f"Mean aux clusters/species: {np.mean([len(v) for v in aux_cluster_sets.values()]):.0f}")

    # --- Step 4: Clustering loop ---
    print("\n--- Clustering Loop ---")
    all_ecotypes = []
    clustering_stats = []
    # Store auxiliary gene clusters per species for COG profiling (only for successful species)
    presence_store = {}
    t_start = time.time()

    for idx, sp in enumerate(species_list):
        short = sp.split('--')[0].replace('s__', '')
        sp_genomes = genome_species[genome_species['species'] == sp]['genome_id'].tolist()
        n_genomes = len(sp_genomes)

        if n_genomes < 20 or sp not in aux_cluster_sets or len(aux_cluster_sets[sp]) < 10:
            continue

        t0 = time.time()
        try:
            # 2-table join filtered by genome_id, chunked
            all_dfs = []
            for i in range(0, len(sp_genomes), 200):
                chunk = sp_genomes[i:i + 200]
                genome_in = "', '".join(chunk)
                df = spark.sql(f"""
                    SELECT g.genome_id, j.gene_cluster_id
                    FROM kbase_ke_pangenome.gene g
                    JOIN kbase_ke_pangenome.gene_genecluster_junction j
                        ON g.gene_id = j.gene_id
                    WHERE g.genome_id IN ('{genome_in}')
                """).toPandas()
                all_dfs.append(df)
            raw_presence = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame(columns=['genome_id', 'gene_cluster_id'])

            # Post-filter to auxiliary gene clusters
            aux_set = aux_cluster_sets[sp]
            aux_presence = raw_presence[raw_presence['gene_cluster_id'].isin(aux_set)].copy()
            aux_presence = aux_presence.drop_duplicates(subset=['genome_id', 'gene_cluster_id'])
            t_query = time.time() - t0

            # Cluster
            ecotype_df, n_clusters, sil = cluster_one_species(aux_presence)

            if ecotype_df is not None:
                ecotype_df = ecotype_df.copy()
                ecotype_df['species'] = sp
                all_ecotypes.append(ecotype_df)
                presence_store[sp] = aux_presence
                cluster_sizes = ecotype_df['ecotype'].value_counts().to_dict()
                clustering_stats.append({
                    'species': sp, 'short_name': short,
                    'n_genomes': n_genomes, 'n_clusters': n_clusters,
                    'silhouette': sil, 'cluster_sizes': str(cluster_sizes),
                    'n_assigned': len(ecotype_df)
                })
                status = f"clusters={n_clusters} sil={sil:.3f}"
            else:
                status = "no valid clusters"

            elapsed = time.time() - t_start
            print(f"  [{idx+1:3d}/{len(species_list)}] {short:35s} n={n_genomes:4d} "
                  f"q={t_query:.0f}s {status} "
                  f"(ecotypes: {len(clustering_stats)}, {elapsed:.0f}s)",
                  flush=True)

            # Incremental save after each species
            if all_ecotypes:
                pd.concat(all_ecotypes, ignore_index=True).to_csv(
                    os.path.join(DATA_DIR, 'ecotype_assignments.csv'), index=False)
                pd.DataFrame(clustering_stats).to_csv(
                    os.path.join(DATA_DIR, 'clustering_stats.csv'), index=False)

        except Exception as e:
            elapsed = time.time() - t_start
            print(f"  [{idx+1:3d}/{len(species_list)}] {short:35s} ERROR: {str(e)[:80]} ({elapsed:.0f}s)",
                  flush=True)

    total_time = time.time() - t_start
    print(f"\n=== Clustering Summary ===")
    print(f"Species processed: {len(species_list)}")
    print(f"Species with valid ecotypes: {len(clustering_stats)}")
    print(f"Total time: {total_time:.0f}s ({total_time/60:.1f} min)")

    if not clustering_stats:
        print("No valid ecotypes found — exiting")
        return

    stats_df = pd.DataFrame(clustering_stats)
    print(f"Mean silhouette: {stats_df['silhouette'].mean():.3f}")
    print(f"Median silhouette: {stats_df['silhouette'].median():.3f}")
    print(f"Mean clusters/species: {stats_df['n_clusters'].mean():.1f}")
    print(f"Total genomes assigned: {stats_df['n_assigned'].sum()}")

    # --- Step 5: Save clustering results ---
    ecotypes_combined = pd.concat(all_ecotypes, ignore_index=True)
    ecotypes_combined.to_csv(os.path.join(DATA_DIR, 'ecotype_assignments.csv'), index=False)
    stats_df.to_csv(os.path.join(DATA_DIR, 'clustering_stats.csv'), index=False)
    print(f"\nSaved {len(ecotypes_combined)} ecotype assignments and stats for {len(stats_df)} species")

    # --- Step 6: COG profiling ---
    print("\n--- COG Profiling ---")
    species_with_ecotypes = list(ecotypes_combined['species'].unique())
    all_cog_profiles = []
    COG_BATCH = 10

    for bi in range(0, len(species_with_ecotypes), COG_BATCH):
        batch = species_with_ecotypes[bi:bi + COG_BATCH]
        bn = bi // COG_BATCH + 1
        total_batches = (len(species_with_ecotypes) + COG_BATCH - 1) // COG_BATCH
        sp_in = "', '".join(batch)

        t0 = time.time()
        try:
            cog_df = spark.sql(f"""
                SELECT gc.gtdb_species_clade_id AS species,
                       gc.gene_cluster_id, ann.COG_category
                FROM kbase_ke_pangenome.gene_cluster gc
                JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
                    ON gc.gene_cluster_id = ann.query_name
                WHERE gc.gtdb_species_clade_id IN ('{sp_in}')
                  AND gc.is_auxiliary = true
                  AND ann.COG_category IS NOT NULL
                  AND ann.COG_category != '-'
            """).toPandas()
        except Exception as e:
            print(f"  COG batch {bn}/{total_batches}: ERROR: {str(e)[:80]}", flush=True)
            continue

        t_q = time.time() - t0
        batch_profiles = 0

        for sp in batch:
            sp_cog = cog_df[cog_df['species'] == sp]
            if len(sp_cog) == 0 or sp not in presence_store:
                continue

            sp_ecotypes = ecotypes_combined[ecotypes_combined['species'] == sp]
            genome_ecotype = dict(zip(sp_ecotypes['genome_id'], sp_ecotypes['ecotype']))

            sp_presence = presence_store[sp]
            assigned_genomes = set(genome_ecotype.keys())
            sp_pf = sp_presence[sp_presence['genome_id'].isin(assigned_genomes)].copy()

            cog_map = dict(zip(sp_cog['gene_cluster_id'], sp_cog['COG_category']))
            sp_pf['COG_category'] = sp_pf['gene_cluster_id'].map(cog_map)
            sp_pf = sp_pf.dropna(subset=['COG_category'])

            if len(sp_pf) == 0:
                continue

            sp_pf['ecotype'] = sp_pf['genome_id'].map(genome_ecotype).astype(int)

            rows = []
            for _, r in sp_pf.iterrows():
                for cat in r['COG_category']:
                    rows.append({'species': sp, 'ecotype': r['ecotype'], 'COG_category': cat})

            if not rows:
                continue

            expanded = pd.DataFrame(rows)
            profile = expanded.groupby(['species', 'ecotype', 'COG_category']).size().reset_index(name='count')
            totals = profile.groupby(['species', 'ecotype'])['count'].sum().reset_index(name='total')
            profile = profile.merge(totals, on=['species', 'ecotype'])
            profile['fraction'] = profile['count'] / profile['total']

            all_cog_profiles.append(profile)
            batch_profiles += 1

        print(f"  COG batch {bn}/{total_batches}: "
              f"{batch_profiles}/{len(batch)} profiled ({t_q:.1f}s)", flush=True)

    if all_cog_profiles:
        cog_profiles = pd.concat(all_cog_profiles, ignore_index=True)
        cog_profiles.to_csv(os.path.join(DATA_DIR, 'ecotype_cog_profiles.csv'), index=False)
        print(f"\nSaved {len(cog_profiles)} COG profile entries "
              f"for {cog_profiles['species'].nunique()} species")
    else:
        print("No COG profiles generated")

    print("\n=== Done ===")


if __name__ == '__main__':
    main()
