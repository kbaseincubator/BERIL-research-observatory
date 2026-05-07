"""
Extract species-level gene family presence/absence matrix from kbase_ke_pangenome.

Outputs:
  data/species_gene_families.csv — one row per species, columns for each gene family (0/1 + cluster counts)
  data/species_gene_families_detail.csv — one row per (species, gene_family), with core/aux/singleton breakdown
  data/species_taxonomy.csv — GTDB taxonomy per species
  data/phenazine_operon_species.csv — species with ≥3 distinct phz genes (true operon carriers)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from berdl_notebook_utils.setup_spark_session import get_spark_session

spark = get_spark_session()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

GENE_FAMILIES = {
    'phoA': "ba.kegg_orthology_id = 'K01077'",
    'phoD_pfam': "EXISTS (SELECT 1 FROM kbase_ke_pangenome.bakta_pfam_domains bpd WHERE bpd.gene_cluster_id = ba.gene_cluster_id AND bpd.pfam_id LIKE 'PF09423.%')",
    'pstA': "ba.gene = 'pstA'",
    'pstB': "ba.gene = 'pstB'",
    'pstC': "ba.gene = 'pstC'",
    'pstS': "ba.gene = 'pstS'",
    'phnC': "ba.gene = 'phnC'",
    'phnD': "ba.gene = 'phnD' OR ba.kegg_orthology_id = 'K02044'",
    'phnE': "ba.gene = 'phnE' OR ba.kegg_orthology_id = 'K02042'",
    'nifH': "ba.kegg_orthology_id = 'K02588'",
    'nifD': "ba.kegg_orthology_id = 'K02586'",
    'nifH_pfam': "EXISTS (SELECT 1 FROM kbase_ke_pangenome.bakta_pfam_domains bpd WHERE bpd.gene_cluster_id = ba.gene_cluster_id AND bpd.pfam_id LIKE 'PF00142.%')",
    'copA': "ba.kegg_orthology_id = 'K17686'",
    'corA': "ba.gene = 'corA'",
    'feoB_pfam': "EXISTS (SELECT 1 FROM kbase_ke_pangenome.bakta_pfam_domains bpd WHERE bpd.gene_cluster_id = ba.gene_cluster_id AND bpd.pfam_id LIKE 'PF02421.%')",
    'HMA_pfam': "EXISTS (SELECT 1 FROM kbase_ke_pangenome.bakta_pfam_domains bpd WHERE bpd.gene_cluster_id = ba.gene_cluster_id AND bpd.pfam_id LIKE 'PF00403.%')",
    'phzF': "ba.kegg_orthology_id = 'K06998'",
    'phzA': "ba.gene = 'phzA'",
    'phzB': "ba.gene = 'phzB'",
    'phzD': "ba.gene = 'phzD'",
    'phzG': "ba.gene = 'phzG'",
    'phzS': "ba.kegg_orthology_id = 'K20940' OR ba.gene = 'phzS'",
    'phzM': "ba.gene = 'phzM'",
}

print("Extracting gene family presence per species (simplified approach)...")

cases = []
for name, condition in GENE_FAMILIES.items():
    if 'EXISTS' in condition:
        continue
    cases.append(f"MAX(CASE WHEN {condition} THEN 1 ELSE 0 END) AS has_{name}")
    cases.append(f"SUM(CASE WHEN {condition} THEN 1 ELSE 0 END) AS n_{name}")
    cases.append(f"SUM(CASE WHEN ({condition}) AND gc.is_core THEN 1 ELSE 0 END) AS n_{name}_core")
    cases.append(f"SUM(CASE WHEN ({condition}) AND gc.is_auxiliary AND NOT gc.is_singleton THEN 1 ELSE 0 END) AS n_{name}_aux")
    cases.append(f"SUM(CASE WHEN ({condition}) AND gc.is_singleton THEN 1 ELSE 0 END) AS n_{name}_singleton")

case_sql = ",\n    ".join(cases)

query = f"""
SELECT gc.gtdb_species_clade_id,
    {case_sql}
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.bakta_annotations ba ON gc.gene_cluster_id = ba.gene_cluster_id
GROUP BY gc.gtdb_species_clade_id
"""

print("Running main query (this may take several minutes)...")
df = spark.sql(query)
pdf = df.toPandas()
print(f"Got {len(pdf)} species rows")

pfam_families = {
    'phoD_pfam': 'PF09423',
    'nifH_pfam': 'PF00142',
    'feoB_pfam': 'PF02421',
    'HMA_pfam': 'PF00403',
}

for name, pfam_prefix in pfam_families.items():
    print(f"Extracting PFAM {name} ({pfam_prefix})...")
    pfam_query = f"""
    SELECT gc.gtdb_species_clade_id,
        MAX(1) AS has_{name},
        COUNT(*) AS n_{name},
        SUM(CASE WHEN gc.is_core THEN 1 ELSE 0 END) AS n_{name}_core,
        SUM(CASE WHEN gc.is_auxiliary AND NOT gc.is_singleton THEN 1 ELSE 0 END) AS n_{name}_aux,
        SUM(CASE WHEN gc.is_singleton THEN 1 ELSE 0 END) AS n_{name}_singleton
    FROM kbase_ke_pangenome.gene_cluster gc
    JOIN kbase_ke_pangenome.bakta_pfam_domains bpd ON gc.gene_cluster_id = bpd.gene_cluster_id
    WHERE bpd.pfam_id LIKE '{pfam_prefix}.%'
    GROUP BY gc.gtdb_species_clade_id
    """
    pfam_df = spark.sql(pfam_query).toPandas()
    pfam_df = pfam_df.set_index('gtdb_species_clade_id')
    for col in pfam_df.columns:
        pdf = pdf.set_index('gtdb_species_clade_id') if 'gtdb_species_clade_id' in pdf.columns else pdf
        if col not in pdf.columns:
            pdf[col] = 0
        pdf.loc[pfam_df.index, col] = pfam_df[col]
    pdf = pdf.reset_index()

pdf = pdf.fillna(0)

for col in pdf.columns:
    if col.startswith('has_') or col.startswith('n_'):
        pdf[col] = pdf[col].astype(int)

has_cols = [c for c in pdf.columns if c.startswith('has_')]
gene_names = [c.replace('has_', '') for c in has_cols]

phz_genes = ['phzA', 'phzB', 'phzD', 'phzF', 'phzG', 'phzS', 'phzM']
phz_has_cols = [f'has_{g}' for g in phz_genes if f'has_{g}' in pdf.columns]
pdf['n_phz_genes'] = pdf[phz_has_cols].sum(axis=1)
pdf['has_phz_operon'] = (pdf['n_phz_genes'] >= 3).astype(int)

p_genes = ['phoA', 'phoD_pfam', 'pstA', 'pstB', 'pstC', 'pstS', 'phnC', 'phnD', 'phnE']
p_has_cols = [f'has_{g}' for g in p_genes if f'has_{g}' in pdf.columns]
pdf['has_P_acquisition'] = (pdf[p_has_cols].sum(axis=1) >= 1).astype(int)
pdf['n_P_genes'] = pdf[p_has_cols].sum(axis=1)

nif_genes = ['nifH', 'nifD', 'nifH_pfam']
nif_has_cols = [f'has_{g}' for g in nif_genes if f'has_{g}' in pdf.columns]
pdf['has_N_fixation'] = (pdf[nif_has_cols].sum(axis=1) >= 1).astype(int)

metal_genes = ['copA', 'corA', 'feoB_pfam', 'HMA_pfam']
metal_has_cols = [f'has_{g}' for g in metal_genes if f'has_{g}' in pdf.columns]
pdf['has_metal_handling'] = (pdf[metal_has_cols].sum(axis=1) >= 1).astype(int)
pdf['n_metal_genes'] = pdf[metal_has_cols].sum(axis=1)

out_path = os.path.join(DATA_DIR, 'species_gene_families.csv')
pdf.to_csv(out_path, index=False)
print(f"Saved {out_path} ({len(pdf)} rows, {len(pdf.columns)} columns)")

print("\nExtracting taxonomy...")
tax_query = """
SELECT gsc.gtdb_species_clade_id, gsc.GTDB_species, gsc.GTDB_taxonomy,
       gsc.no_clustered_genomes_filtered AS n_genomes,
       p.no_gene_clusters, p.no_core, p.no_aux_genome, p.no_singleton_gene_clusters
FROM kbase_ke_pangenome.gtdb_species_clade gsc
LEFT JOIN kbase_ke_pangenome.pangenome p ON gsc.gtdb_species_clade_id = p.gtdb_species_clade_id
"""
tax_pdf = spark.sql(tax_query).toPandas()

def parse_taxonomy(tax_str):
    if not tax_str:
        return {}
    parts = tax_str.split(';')
    ranks = ['domain', 'phylum', 'class', 'order', 'family', 'genus', 'species']
    return {ranks[i]: parts[i].strip() if i < len(parts) else '' for i in range(len(ranks))}

tax_parsed = tax_pdf['GTDB_taxonomy'].apply(lambda x: parse_taxonomy(x) if x else {})
for rank in ['domain', 'phylum', 'class', 'order', 'family', 'genus']:
    tax_pdf[rank] = tax_parsed.apply(lambda x: x.get(rank, ''))

tax_out = os.path.join(DATA_DIR, 'species_taxonomy.csv')
tax_pdf.to_csv(tax_out, index=False)
print(f"Saved {tax_out} ({len(tax_pdf)} rows)")

phz_species = pdf[pdf['has_phz_operon'] == 1][['gtdb_species_clade_id', 'n_phz_genes'] + phz_has_cols].copy()
phz_out = os.path.join(DATA_DIR, 'phenazine_operon_species.csv')
phz_species.to_csv(phz_out, index=False)
print(f"Saved {phz_out} ({len(phz_species)} phenazine operon species)")

print("\n=== Summary ===")
print(f"Total species: {len(pdf)}")
print(f"P-acquisition: {pdf['has_P_acquisition'].sum()}")
print(f"N-fixation: {pdf['has_N_fixation'].sum()}")
print(f"Metal-handling: {pdf['has_metal_handling'].sum()}")
print(f"Phenazine operon (≥3 phz genes): {pdf['has_phz_operon'].sum()}")
print(f"PhzF only (broad family): {pdf['has_phzF'].sum()}")
print(f"P + Metal: {((pdf['has_P_acquisition']==1) & (pdf['has_metal_handling']==1)).sum()}")
print(f"N + Metal: {((pdf['has_N_fixation']==1) & (pdf['has_metal_handling']==1)).sum()}")
print(f"Phz operon + Metal: {((pdf['has_phz_operon']==1) & (pdf['has_metal_handling']==1)).sum()}")
print(f"P + N + Metal: {((pdf['has_P_acquisition']==1) & (pdf['has_N_fixation']==1) & (pdf['has_metal_handling']==1)).sum()}")
print(f"All four: {((pdf['has_P_acquisition']==1) & (pdf['has_N_fixation']==1) & (pdf['has_metal_handling']==1) & (pdf['has_phz_operon']==1)).sum()}")
