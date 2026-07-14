from _build import build_and_run

cells = [
    ("md", "# NB06 — Per-compound Phylogenetic Utilizer Map (Deliverable b)\n\n"
           "Place the predicted ENIGMA-isolate utilizers from NB03/NB04 onto a taxonomic "
           "backbone, with a **per-prediction certainty score**, so the wet lab can see "
           "*where in the tree* each compound's predicted catabolizers sit.\n\n"
           "**What backbone (honesty note).** genome_depot's `browser_taxon` is the **NCBI** "
           "taxonomy (ranks + `parent_id` chain), not GTDB with branch lengths. So this "
           "deliverable is an **NCBI-lineage placement** (domain→phylum→class→order→family→"
           "genus→species), not a true phylogeny. That is the resolution the in-lakehouse "
           "ENIGMA isolate metadata supports; a branch-length GTDB tree would require the "
           "pangenome assembly-accession bridge (deferred — adds no resolution for the "
           "wet-lab strain-selection use case, which is genus/family-level).\n\n"
           "**Certainty score.** Per (compound, strain): evidence **tier** (T2 degradation-"
           "map > T3 allowlist) combined with **sig_completeness** (fraction of the "
           "compound's catabolic signature reactions the genome carries). Derived label: "
           "`high` = T2 & completeness=1; `medium` = T2 or completeness=1; `low` otherwise."),

    ("code",
     "import pandas as pd, numpy as np, os\n"
     "import matplotlib\n"
     "matplotlib.use('Agg')\n"
     "import matplotlib.pyplot as plt\n"
     "from pathlib import Path\n"
     "from dotenv import load_dotenv\n"
     "\n"
     "DATA = Path('../data'); FIG = Path('../figures')\n"
     "pd.set_option('display.max_columns', 40); pd.set_option('display.width', 220)\n"
     "\n"
     "pred = pd.read_csv(DATA / 'compound_organism_predictions.tsv', sep='\\t')\n"
     "print('prediction rows:', len(pred), '| genomes:', pred['genome_id'].nunique(),\n"
     "      '| compounds:', pred['compound_id'].nunique())"),

    ("md", "## Build NCBI lineages from the genome_depot taxonomy backbone\n"
           "`browser_taxon.parent_id` points to the parent's `taxonomy_id` (NCBI taxid). "
           "Pull the whole table (small) and walk each predicted genome's taxid up to the "
           "root, collecting the standard ranks."),

    ("code",
     "load_dotenv('/home/aparkin/BERIL-research-observatory/.env')\n"
     "_tok = os.environ['KBASE_AUTH_TOKEN']\n"
     "from pyspark.sql import SparkSession\n"
     "_url = f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={_tok}'\n"
     "spark = SparkSession.builder.remote(_url).getOrCreate()\n"
     "DB = 'enigma_genome_depot_enigma'\n"
     "tax = spark.sql(f'SELECT taxonomy_id, parent_id, rank, name FROM {DB}.browser_taxon').toPandas()\n"
     "tax['taxonomy_id'] = tax['taxonomy_id'].astype(str)\n"
     "tax['parent_id'] = tax['parent_id'].astype(str)\n"
     "by_tid = tax.set_index('taxonomy_id')\n"
     "print('taxon rows:', len(tax))"),

    ("code",
     "RANKS = ['superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']\n"
     "# NCBI uses 'superkingdom'/'domain' inconsistently; accept either at the top\n"
     "def lineage(tid):\n"
     "    out = {r: None for r in RANKS}\n"
     "    tid = str(tid); seen = set()\n"
     "    for _ in range(40):\n"
     "        if tid not in by_tid.index or tid in seen:\n"
     "            break\n"
     "        seen.add(tid)\n"
     "        row = by_tid.loc[tid]\n"
     "        if isinstance(row, pd.DataFrame):\n"
     "            row = row.iloc[0]\n"
     "        rk = row['rank']\n"
     "        if rk == 'domain':\n"
     "            rk = 'superkingdom'\n"
     "        if rk in out and out[rk] is None:\n"
     "            out[rk] = row['name']\n"
     "        tid = str(row['parent_id'])\n"
     "    return out\n"
     "\n"
     "uniq = pred[['ncbi_taxid']].drop_duplicates()\n"
     "uniq['ncbi_taxid_s'] = uniq['ncbi_taxid'].astype('Int64').astype(str)\n"
     "lin = uniq['ncbi_taxid_s'].map(lambda t: lineage(t)).apply(pd.Series)\n"
     "lin['ncbi_taxid'] = uniq['ncbi_taxid'].values\n"
     "print('lineage coverage (non-null):')\n"
     "for r in RANKS:\n"
     "    print(f'  {r:14s} {lin[r].notna().sum():4d}/{len(lin)}')\n"
     "print('\\nsample:')\n"
     "print(lin[['ncbi_taxid','phylum','class','order','family','genus']].head(8).to_string(index=False))"),

    ("md", "## Strain-level utilizers with lineage + certainty"),

    ("code",
     "# collapse genomes -> strains (best-scoring genome per compound x strain), like NB04\n"
     "p = pred.sort_values('score', ascending=False)\n"
     "strain = (p.groupby(['compound_id', 'name', 'npc_pathway', 'tier', 'ncbi_taxid', 'taxon_name'],\n"
     "                    dropna=False)\n"
     "          .agg(score=('score', 'max'),\n"
     "               sig_completeness=('sig_completeness', 'max'),\n"
     "               n_sig_carried=('n_sig_carried', 'max'),\n"
     "               n_genomes=('genome_id', 'nunique')).reset_index())\n"
     "strain = strain.merge(lin, on='ncbi_taxid', how='left')\n"
     "\n"
     "def certainty(row):\n"
     "    t2 = row['tier'] == 'T2_pathway'\n"
     "    full = row['sig_completeness'] >= 1.0\n"
     "    if t2 and full: return 'high'\n"
     "    if t2 or full: return 'medium'\n"
     "    return 'low'\n"
     "strain['certainty'] = strain.apply(certainty, axis=1)\n"
     "print('strain-level rows:', len(strain), '| distinct strains:', strain['ncbi_taxid'].nunique())\n"
     "print('\\ncertainty x tier:')\n"
     "print(pd.crosstab(strain['certainty'], strain['tier']).to_string())"),

    ("md", "## Phylogenetic placement: compound x taxonomic order\n"
           "The core deliverable-(b) map — for each compound, how its predicted utilizer "
           "strains distribute across taxonomic **orders**, shaded by utilizer count. Orders "
           "(not genera) keep the map legible while showing clade structure."),

    ("code",
     "strain['order_lbl'] = strain['order'].fillna(strain['class']).fillna('(unresolved)')\n"
     "pc = (strain.groupby(['order_lbl', 'name'])['ncbi_taxid'].nunique()\n"
     "      .unstack(fill_value=0))\n"
     "comp_order = (strain.groupby('name')['ncbi_taxid'].nunique()\n"
     "              .sort_values(ascending=False).index.tolist())\n"
     "pc = pc[comp_order]\n"
     "pc = pc.loc[pc.sum(axis=1).sort_values(ascending=False).index]\n"
     "print('orders x compounds (utilizer strain counts):')\n"
     "print(pc.to_string())"),

    ("code",
     "fig, ax = plt.subplots(figsize=(9, max(4, 0.34*len(pc))))\n"
     "im = ax.imshow(pc.values, cmap='YlGnBu', aspect='auto')\n"
     "ax.set_xticks(range(len(pc.columns)))\n"
     "ax.set_xticklabels(pc.columns, rotation=45, ha='right', fontsize=8)\n"
     "ax.set_yticks(range(len(pc.index))); ax.set_yticklabels(pc.index, fontsize=8)\n"
     "for i in range(len(pc.index)):\n"
     "    for j in range(len(pc.columns)):\n"
     "        v = pc.values[i, j]\n"
     "        if v > 0:\n"
     "            ax.text(j, i, int(v), ha='center', va='center', fontsize=6,\n"
     "                    color='white' if v > pc.values.max()*0.5 else 'black')\n"
     "ax.set_title('Predicted utilizer strains by taxonomic order (deliverable b)')\n"
     "fig.colorbar(im, ax=ax, shrink=0.6, label='utilizer strains')\n"
     "fig.tight_layout(); fig.savefig(FIG / '06_phylo_order_map.png', dpi=150)\n"
     "print('saved 06_phylo_order_map.png'); plt.close(fig)"),

    ("md", "## Per-compound certainty composition\n"
           "For each compound, the certainty mix of its predicted utilizers — the wet-lab "
           "view of how trustworthy the call set is."),

    ("code",
     "cc = (strain.groupby(['name', 'certainty'])['ncbi_taxid'].nunique()\n"
     "      .unstack(fill_value=0).reindex(columns=['high', 'medium', 'low'], fill_value=0))\n"
     "cc = cc.loc[strain.groupby('name')['ncbi_taxid'].nunique().sort_values().index]\n"
     "print(cc.to_string())\n"
     "fig, ax = plt.subplots(figsize=(8, 4.5))\n"
     "cc.plot(kind='barh', stacked=True, ax=ax,\n"
     "        color={'high': '#1a9850', 'medium': '#fee08b', 'low': '#d73027'})\n"
     "ax.set_xlabel('predicted utilizer strains'); ax.set_ylabel('')\n"
     "ax.set_title('Per-compound predicted-utilizer certainty composition')\n"
     "ax.legend(title='certainty', loc='lower right')\n"
     "fig.tight_layout(); fig.savefig(FIG / '06_certainty_composition.png', dpi=150)\n"
     "print('saved 06_certainty_composition.png'); plt.close(fig)"),

    ("md", "## Write deliverable (b) table"),

    ("code",
     "out_cols = ['compound_id', 'name', 'npc_pathway', 'tier', 'certainty',\n"
     "            'ncbi_taxid', 'taxon_name', 'superkingdom', 'phylum', 'class',\n"
     "            'order', 'family', 'genus', 'species',\n"
     "            'n_genomes', 'n_sig_carried', 'sig_completeness', 'score']\n"
     "out = strain[out_cols].sort_values(['name', 'certainty', 'score'],\n"
     "                                   ascending=[True, True, False]).reset_index(drop=True)\n"
     "out.to_csv(DATA / 'phylo_utilizer_map.tsv', sep='\\t', index=False)\n"
     "print('wrote data/phylo_utilizer_map.tsv', out.shape)\n"
     "print('\\nsummary: strains per compound x phylum')\n"
     "print((strain.groupby(['name', 'phylum'])['ncbi_taxid'].nunique()\n"
     "       .unstack(fill_value=0)).to_string())\n"
     "print('\\n=== deliverable (b) headline ===')\n"
     "print(f'compounds mapped: {strain[\"name\"].nunique()} | utilizer strains placed: '\n"
     "      f'{strain[\"ncbi_taxid\"].nunique()} | high-certainty strain-calls: '\n"
     "      f'{int((strain[\"certainty\"]==\"high\").sum())}')"),
]

build_and_run("06_phylo_maps.ipynb", cells)
