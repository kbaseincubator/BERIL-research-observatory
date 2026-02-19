#!/usr/bin/env python3
"""
BERDL Pangenome Analysis Script
Run this directly on BERDL compute node to avoid API timeouts.

Usage:
    python3 berdl_analysis.py
"""

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

# Configuration
BASE_URL = "https://hub.berdl.kbase.us/apis/mcp"
DATABASE = "kbase_ke_pangenome"

# Load auth token from .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.startswith('KBASE_AUTH_TOKEN'):
                AUTH_TOKEN = line.split('"')[1]
                break
else:
    print("ERROR: .env file not found. Please provide KBASE_AUTH_TOKEN")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def query_berdl(sql, limit=10000):
    """Query BERDL API."""
    url = f"{BASE_URL}/delta/tables/query"
    payload = {"query": sql, "limit": limit}

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            return pd.DataFrame(data['results'])
        return pd.DataFrame()
    except Exception as e:
        print(f"Query failed: {e}")
        return None

def main():
    print("=" * 60)
    print("BERDL Pangenome Analysis")
    print("=" * 60)

    # 1. Query pangenome statistics
    print("\n1. Querying pangenome statistics...")
    sql = f"""
    SELECT
        gtdb_species_clade_id,
        no_genomes,
        no_core,
        no_aux_genome as no_accessory,
        no_singleton_gene_clusters as no_singletons,
        no_gene_clusters
    FROM {DATABASE}.pangenome
    ORDER BY no_genomes DESC
    LIMIT 5000
    """

    df_pangenome = query_berdl(sql, limit=5000)

    if df_pangenome is None or len(df_pangenome) == 0:
        print("❌ Failed to retrieve pangenome data")
        return

    print(f"✅ Loaded {len(df_pangenome):,} species")

    # Calculate percentages
    df_pangenome['pct_core'] = (df_pangenome['no_core'] / df_pangenome['no_gene_clusters'] * 100).round(2)
    df_pangenome['pct_accessory'] = (df_pangenome['no_accessory'] / df_pangenome['no_gene_clusters'] * 100).round(2)
    df_pangenome['pct_singletons'] = (df_pangenome['no_singletons'] / df_pangenome['no_gene_clusters'] * 100).round(2)

    # 2. Save to CSV
    print("\n2. Saving data to CSV...")
    df_pangenome.to_csv('pangenome_stats.csv', index=False)
    print("✅ Saved to pangenome_stats.csv")

    # 3. Basic statistics
    print("\n3. Basic Statistics:")
    print(df_pangenome[['no_genomes', 'no_core', 'no_accessory', 'no_singletons']].describe())

    # 4. Get species names for top 20
    print("\n4. Fetching species names for top 20...")
    top_ids = df_pangenome.head(20)['gtdb_species_clade_id'].tolist()
    ids_str = "','".join(top_ids)

    sql_species = f"""
    SELECT
        gtdb_species_clade_id,
        GTDB_species,
        GTDB_taxonomy,
        mean_intra_species_ANI,
        ANI_circumscription_radius
    FROM {DATABASE}.gtdb_species_clade
    WHERE gtdb_species_clade_id IN ('{ids_str}')
    """

    df_species = query_berdl(sql_species, limit=50)

    if df_species is not None and len(df_species) > 0:
        df_top = df_pangenome.head(20).merge(df_species, on='gtdb_species_clade_id', how='left')
        print(f"✅ Got {len(df_species)} species names")

        print("\nTop 20 Species by Genome Count:")
        print(df_top[['GTDB_species', 'no_genomes', 'no_core', 'no_accessory', 'pct_core']].to_string())

        # Save top species
        df_top.to_csv('top_species.csv', index=False)
        print("\n✅ Saved to top_species.csv")

    # 5. Generate plots
    print("\n5. Generating plots...")

    # Distribution of genomes
    fig1 = px.histogram(
        df_pangenome,
        x='no_genomes',
        title=f'Distribution of Genomes per Species (n={len(df_pangenome)})',
        labels={'no_genomes': 'Genomes per Species'},
        nbins=50
    )
    fig1.write_html('plot_genome_distribution.html')
    print("✅ Saved plot_genome_distribution.html")

    # Core vs Accessory
    fig2 = px.scatter(
        df_pangenome.head(500),
        x='no_core',
        y='no_accessory',
        size='no_genomes',
        hover_data=['gtdb_species_clade_id'],
        title='Core vs Accessory Genes (Top 500 Species)',
        labels={'no_core': 'Core Genes', 'no_accessory': 'Accessory Genes'},
        log_x=True,
        log_y=True
    )
    fig2.write_html('plot_core_vs_accessory.html')
    print("✅ Saved plot_core_vs_accessory.html")

    # Pangenome composition
    fig3 = go.Figure()
    fig3.add_trace(go.Box(y=df_pangenome['pct_core'], name='Core %'))
    fig3.add_trace(go.Box(y=df_pangenome['pct_accessory'], name='Accessory %'))
    fig3.add_trace(go.Box(y=df_pangenome['pct_singletons'], name='Singletons %'))
    fig3.update_layout(
        title='Pangenome Composition Distribution',
        yaxis_title='Percentage'
    )
    fig3.write_html('plot_composition.html')
    print("✅ Saved plot_composition.html")

    # 6. Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - pangenome_stats.csv (all species data)")
    print("  - top_species.csv (top 20 with names)")
    print("  - plot_genome_distribution.html")
    print("  - plot_core_vs_accessory.html")
    print("  - plot_composition.html")
    print("\nOpen HTML files in a browser to view interactive plots.")

if __name__ == "__main__":
    main()
