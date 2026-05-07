"""Create Jupyter notebooks from analysis scripts with saved outputs."""
import json
import os
import subprocess
import sys

PROJ = os.path.join(os.path.dirname(__file__), '..')
NB_DIR = os.path.join(PROJ, 'notebooks')
os.makedirs(NB_DIR, exist_ok=True)

def make_notebook(cells):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0"
            }
        },
        "cells": cells
    }

def md_cell(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.split('\n'), "id": None}

def code_cell(source):
    return {"cell_type": "code", "metadata": {}, "source": source.split('\n'),
            "outputs": [], "execution_count": None, "id": None}


# --- NB01: Data Extraction (Spark-dependent, pre-executed) ---
nb01_cells = [
    md_cell("# NB01: Gene Family Extraction from kbase_ke_pangenome\n\n"
            "**Requires BERDL JupyterHub** — this notebook queries 132.5M gene clusters via Spark SQL.\n\n"
            "Outputs: `data/species_gene_families.csv`, `data/species_taxonomy.csv`, `data/phenazine_operon_species.csv`\n\n"
            "Run equivalent script: `python src/01_extract_gene_families.py`"),
    md_cell("## Gene Family Definitions\n\n"
            "23 gene families across 4 functional groups:\n"
            "- **P-acquisition (9):** phoA, phoD, pstA/B/C/S, phnC/D/E\n"
            "- **N-fixation (3):** nifH, nifD, nifH(Pfam)\n"
            "- **Metal-handling (4):** copA, corA, feoB, HMA\n"
            "- **Phenazine biosynthesis (7):** phzA/B/D/F/G/S/M"),
    code_cell("import pandas as pd\nimport os\nDATA_DIR = os.path.join('..', 'data')"),
    code_cell("# Load pre-extracted results (Spark query already executed)\n"
              "df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))\n"
              "print(f'Total species: {len(df)}')\n"
              "print(f'Columns: {len(df.columns)}')\n"
              "df.head()"),
    md_cell("## Summary Statistics"),
    code_cell("print(f\"P-acquisition: {df['has_P_acquisition'].sum()} ({df['has_P_acquisition'].mean()*100:.1f}%)\")\n"
              "print(f\"N-fixation: {df['has_N_fixation'].sum()} ({df['has_N_fixation'].mean()*100:.1f}%)\")\n"
              "print(f\"Metal-handling: {df['has_metal_handling'].sum()} ({df['has_metal_handling'].mean()*100:.1f}%)\")\n"
              "print(f\"Phenazine operon (>=3 phz genes): {df['has_phz_operon'].sum()} ({df['has_phz_operon'].mean()*100:.2f}%)\")\n"
              "print(f\"PhzF only (broad family): {df['has_phzF'].sum()}\")\n"
              "print()\n"
              "print(f\"P + Metal: {((df['has_P_acquisition']==1) & (df['has_metal_handling']==1)).sum()}\")\n"
              "print(f\"N + Metal: {((df['has_N_fixation']==1) & (df['has_metal_handling']==1)).sum()}\")\n"
              "print(f\"Phz operon + Metal: {((df['has_phz_operon']==1) & (df['has_metal_handling']==1)).sum()}\")\n"
              "print(f\"All four: {((df['has_P_acquisition']==1) & (df['has_N_fixation']==1) & (df['has_metal_handling']==1) & (df['has_phz_operon']==1)).sum()}\")"),
]

# --- NB02: Co-occurrence Analysis ---
nb02_cells = [
    md_cell("# NB02: Co-occurrence Matrix and Statistical Testing\n\n"
            "Computes Jaccard index, phi coefficient, Fisher's exact test, and permutation null\n"
            "for pairwise associations between gene family groups.\n\n"
            "Run equivalent script: `python src/02_cooccurrence_stats.py`"),
    code_cell("import pandas as pd\nimport numpy as np\nfrom scipy import stats\nfrom itertools import combinations\nimport os\nDATA_DIR = os.path.join('..', 'data')"),
    code_cell("df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))\nprint(f'Loaded {len(df)} species')"),
    md_cell("## Group-Level Co-occurrence"),
    code_cell("cooc = pd.read_csv(os.path.join(DATA_DIR, 'cooccurrence_matrix.csv'))\ncooc[['group_A', 'group_B', 'n_both', 'jaccard', 'phi', 'odds_ratio', 'fisher_p']]"),
    md_cell("## Permutation Test Results\n\n"
            "1,000 permutations shuffling group membership vectors."),
    code_cell(
        "groups = {\n"
        "    'P_acquisition': ['phoA', 'phoD_pfam', 'pstA', 'pstB', 'pstC', 'pstS', 'phnC', 'phnD', 'phnE'],\n"
        "    'N_fixation': ['nifH', 'nifD', 'nifH_pfam'],\n"
        "    'Metal_handling': ['copA', 'corA', 'feoB_pfam', 'HMA_pfam'],\n"
        "    'Phenazine_operon': None,\n"
        "}\n\n"
        "group_has = {}\n"
        "for gname, genes in groups.items():\n"
        "    if genes is None:\n"
        "        group_has[gname] = df['has_phz_operon'].values\n"
        "    else:\n"
        "        cols = [f'has_{g}' for g in genes if f'has_{g}' in df.columns]\n"
        "        group_has[gname] = (df[cols].sum(axis=1) >= 1).astype(int).values\n\n"
        "def phi_coefficient(a, b):\n"
        "    n11 = np.sum((a==1)&(b==1)); n10 = np.sum((a==1)&(b==0))\n"
        "    n01 = np.sum((a==0)&(b==1)); n00 = np.sum((a==0)&(b==0))\n"
        "    denom = np.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))\n"
        "    return (n11*n00 - n10*n01) / denom if denom > 0 else 0.0\n\n"
        "np.random.seed(42)\n"
        "N_PERM = 1000\n"
        "key_pairs = [('P_acquisition','Metal_handling'),('N_fixation','Metal_handling'),\n"
        "             ('Phenazine_operon','Metal_handling'),('P_acquisition','N_fixation')]\n\n"
        "for g1, g2 in key_pairs:\n"
        "    a, b = group_has[g1], group_has[g2]\n"
        "    obs_phi = phi_coefficient(a, b)\n"
        "    null_phis = np.array([phi_coefficient(a, np.random.permutation(b)) for _ in range(N_PERM)])\n"
        "    z = (obs_phi - np.mean(null_phis)) / np.std(null_phis) if np.std(null_phis) > 0 else float('inf')\n"
        "    perm_p = (np.sum(np.abs(null_phis) >= np.abs(obs_phi)) + 1) / (N_PERM + 1)\n"
        "    print(f'{g1} vs {g2}: phi={obs_phi:.4f}, Z={z:.1f}, perm_p={perm_p:.4f}')"),
    md_cell("## Per-Gene-Family Pairwise Detail"),
    code_cell("detail = pd.read_csv(os.path.join(DATA_DIR, 'pairwise_detail.csv'))\n"
              "print('Top 10 enrichments (nutrient x metal):')\n"
              "detail.sort_values('enrichment', ascending=False).head(10)[['nutrient_gene','metal_gene','enrichment','phi','n_both','fisher_p']]"),
    code_cell("print('Bottom 5 (depleted co-occurrence):')\n"
              "detail[detail['phi']<0].sort_values('phi').head(5)[['nutrient_gene','metal_gene','enrichment','phi','n_both','fisher_p']]"),
]

# --- NB03: Core/Accessory + Phylogenetic ---
nb03_cells = [
    md_cell("# NB03: Core vs. Accessory Enrichment and Phylogenetic Stratification\n\n"
            "Tests whether co-occurring nutrient and metal genes concentrate in the core genome,\n"
            "and stratifies co-occurrence by GTDB taxonomy.\n\n"
            "Run equivalent scripts: `python src/03_core_accessory_enrichment.py` and `python src/04_phylogenetic_stratification.py`"),
    code_cell("import pandas as pd\nimport numpy as np\nimport os\nDATA_DIR = os.path.join('..', 'data')"),
    md_cell("## Core vs. Accessory Enrichment"),
    code_cell("summary = pd.read_csv(os.path.join(DATA_DIR, 'core_enrichment_summary.csv'))\nsummary"),
    code_cell("df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))\n"
              "all_genes = ['phoA','phoD_pfam','pstA','pstC','pstS','phnC','phnE',\n"
              "             'nifH','nifD','nifH_pfam','phzF','phzG','phzS',\n"
              "             'copA','corA','feoB_pfam','HMA_pfam']\n"
              "print('Gene family core fractions:')\n"
              "for g in all_genes:\n"
              "    total = int(df[f'n_{g}'].sum())\n"
              "    core = int(df[f'n_{g}_core'].sum())\n"
              "    frac = core/total if total > 0 else 0\n"
              "    print(f'  {g:>12s}: {frac:.3f} ({core}/{total})')"),
    md_cell("## Phylum-Level Stratification"),
    code_cell("phy = pd.read_csv(os.path.join(DATA_DIR, 'phylum_cooccurrence.csv'))\n"
              "top = phy[phy['n_species']>=50].sort_values('phi_PM', ascending=False).head(12)\n"
              "top[['phylum','n_species','frac_P','frac_M','phi_PM','PM_enrichment','n_Phz_operon']]"),
    md_cell("## Phenazine Operon Taxonomy"),
    code_cell("phz = pd.read_csv(os.path.join(DATA_DIR, 'phenazine_operon_taxonomy.csv'))\n"
              "print(f'{len(phz)} phenazine operon species')\n"
              "print()\n"
              "print('By family:')\n"
              "for fam, grp in phz.groupby('family'):\n"
              "    genera = grp['genus'].unique()\n"
              "    print(f'  {fam}: {len(grp)} species ({', '.join(genera[:4])})')"),
    md_cell("## Plant-Associated Lineages"),
    code_cell("tax = pd.read_csv(os.path.join(DATA_DIR, 'species_taxonomy.csv'))\n"
              "merged = df.merge(tax[['gtdb_species_clade_id','family']], on='gtdb_species_clade_id', how='left')\n\n"
              "plant_fams = ['f__Pseudomonadaceae','f__Rhizobiaceae','f__Burkholderiaceae',\n"
              "              'f__Streptomycetaceae','f__Xanthomonadaceae','f__Enterobacteriaceae']\n"
              "for fam in plant_fams:\n"
              "    s = merged[merged['family']==fam]\n"
              "    if len(s)==0: continue\n"
              "    n=len(s); np_=int(s['has_P_acquisition'].sum()); nm=int(s['has_metal_handling'].sum())\n"
              "    nphz=int(s['has_phz_operon'].sum())\n"
              "    print(f'{fam}: n={n} P={np_/n:.2f} M={nm/n:.2f} Phz_operon={nphz}')"),
]

# --- NB04: Figure ---
nb04_cells = [
    md_cell("# NB04: Multi-Panel Figure\n\n"
            "Generates Figure 1 for the report.\n\n"
            "Run equivalent script: `python src/05_figure.py`"),
    code_cell("import pandas as pd\nimport numpy as np\nimport matplotlib\nmatplotlib.use('Agg')\n"
              "import matplotlib.pyplot as plt\nimport matplotlib.gridspec as gridspec\n"
              "from matplotlib.colors import TwoSlopeNorm\nfrom matplotlib.patches import Patch\n"
              "import os\n\nFIG_DIR = os.path.join('..', 'figures')\nDATA_DIR = os.path.join('..', 'data')"),
    code_cell("# Load all data\n"
              "detail = pd.read_csv(os.path.join(DATA_DIR, 'pairwise_detail.csv'))\n"
              "df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))\n"
              "phy = pd.read_csv(os.path.join(DATA_DIR, 'phylum_cooccurrence.csv'))\n"
              "phz_tax = pd.read_csv(os.path.join(DATA_DIR, 'phenazine_operon_taxonomy.csv'))\n"
              "print('Data loaded')"),
    code_cell("# Execute the figure script\nexec(open(os.path.join('..', 'src', '05_figure.py')).read())\n"
              "print('Figure saved to figures/')"),
    code_cell("from IPython.display import Image\nImage(os.path.join(FIG_DIR, 'figure1_cooccurrence.png'), width=900)"),
]

notebooks = {
    'NB01_gene_family_extraction.ipynb': nb01_cells,
    'NB02_cooccurrence_analysis.ipynb': nb02_cells,
    'NB03_core_accessory_phylogenetic.ipynb': nb03_cells,
    'NB04_figure.ipynb': nb04_cells,
}

for name, cells in notebooks.items():
    for i, c in enumerate(cells):
        if c.get('id') is None:
            c['id'] = f'cell_{i}'
        if isinstance(c.get('source'), list):
            c['source'] = [line + '\n' for line in c['source'][:-1]] + [c['source'][-1]]

    nb = make_notebook(cells)
    path = os.path.join(NB_DIR, name)
    with open(path, 'w') as f:
        json.dump(nb, f, indent=1)
    print(f"Created {path}")

print("\nNow execute notebooks to capture outputs...")
for name in notebooks:
    path = os.path.join(NB_DIR, name)
    if 'NB01' in name:
        print(f"Skipping {name} execution (Spark-dependent, outputs captured from pre-run data)")
    print(f"Executing {name}...")
    result = subprocess.run(
        ['jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--inplace',
         '--ExecutePreprocessor.timeout=300', path],
        capture_output=True, text=True, cwd=NB_DIR
    )
    if result.returncode == 0:
        print(f"  OK: {name}")
    else:
        print(f"  FAILED: {name}")
        print(f"  stderr: {result.stderr[:500]}")
