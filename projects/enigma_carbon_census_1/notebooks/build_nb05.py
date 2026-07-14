from _build import build_and_run

cells = [
    ("md", "# NB05 — Catabolic Co-occurrence & Modularity (H2)\n\n"
           "Test **H2 — modularity / co-occurrence**: catabolic capacities co-occur "
           "non-randomly within genomes and cluster phylogenetically. *H0:* pathway "
           "presence is independent across genomes.\n\n"
           "**Honesty-of-scope caveat (stated, not hidden).** After the reaction-level "
           "catabolic filter (NB03), only **8 compounds** carry catabolically-coherent "
           "isolate calls. Co-occurrence is therefore computed over an 8-wide capacity "
           "vector, not the full 83. Furthermore, **5 of the 8** are aromatic acids/"
           "aldehydes (salicylate, 3-hydroxybenzoate, 4-hydroxybenzaldehyde, phthalate, "
           "terephthalate) that funnel into the shared **protocatechuate/catechol → "
           "β-ketoadipate** lower pathway. Their mutual co-occurrence is partly "
           "*mechanistic* (one shared lower module), not independent acquisition of "
           "distinct modules. The more informative test of H2 is whether the aromatic "
           "block co-occurs with the **non-aromatic** capacities (phenylethylamine "
           "deamination, xanthine oxidation, abscisate hydroxylation), which share no "
           "lower pathway. We report both, and we report effect size (φ) alongside "
           "Fisher p so significance is not driven by rarity alone."),

    ("code",
     "import pandas as pd, numpy as np, os\n"
     "import matplotlib\n"
     "matplotlib.use('Agg')\n"
     "import matplotlib.pyplot as plt\n"
     "from itertools import combinations\n"
     "from scipy.stats import fisher_exact\n"
     "from pathlib import Path\n"
     "from dotenv import load_dotenv\n"
     "\n"
     "DATA = Path('../data'); FIG = Path('../figures')\n"
     "pd.set_option('display.max_columns', 40); pd.set_option('display.width', 220)\n"
     "\n"
     "pred = pd.read_csv(DATA / 'compound_organism_predictions.tsv', sep='\\t')\n"
     "print('prediction rows:', len(pred),\n"
     "      '| genomes with >=1 call:', pred['genome_id'].nunique(),\n"
     "      '| callable compounds:', pred['compound_id'].nunique())\n"
     "\n"
     "# aromatic-funnel block (shared protocatechuate/catechol lower pathway)\n"
     "AROMATIC = {'salicylic acid', '3-hydroxybenzoic acid', '4-hydroxybenzaldehyde',\n"
     "            'phthalic acid', 'TEREPHTHALIC ACID'}\n"
     "pred['block'] = pred['name'].map(lambda n: 'aromatic-funnel' if n in AROMATIC else 'other')\n"
     "print('\\ncompounds by block:')\n"
     "print(pred.groupby('block')['name'].apply(lambda s: sorted(set(s))).to_string())"),

    ("md", "## Genome x compound capacity matrix\n"
           "Binary presence: does a genome carry >=1 catabolic signature reaction for the "
           "compound. Rows = the 800 genomes with any call; the full-DB genome count is the "
           "null denominator for the across-genome test."),

    ("code",
     "load_dotenv('/home/aparkin/BERIL-research-observatory/.env')\n"
     "_tok = os.environ['KBASE_AUTH_TOKEN']\n"
     "from pyspark.sql import SparkSession\n"
     "_url = f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={_tok}'\n"
     "spark = SparkSession.builder.remote(_url).getOrCreate()\n"
     "DB = 'enigma_genome_depot_enigma'\n"
     "NGEN = spark.sql(f'SELECT COUNT(DISTINCT genome_id) n FROM {DB}.browser_gene').toPandas()['n'][0]\n"
     "print('total genomes in DB (null denominator):', NGEN)"),

    ("code",
     "# binary genome x compound matrix over the callable set\n"
     "order = (pred.groupby('name')['genome_id'].nunique()\n"
     "         .sort_values(ascending=False).index.tolist())\n"
     "mat = (pred.assign(v=1).pivot_table(index='genome_id', columns='name', values='v',\n"
     "                                    aggfunc='max', fill_value=0)[order].astype(int))\n"
     "print('matrix:', mat.shape, '(genomes x compounds)')\n"
     "print('\\nprevalence (fraction of all', NGEN, 'genomes):')\n"
     "for c in order:\n"
     "    print(f'  {c:24s} {mat[c].sum():4d}  {mat[c].sum()/NGEN*100:5.2f}%')"),

    ("md", "## Within-genome versatility\n"
           "How many of the 8 capacities each genome carries. A right-skewed distribution "
           "(most genomes carry 1, a few carry many) is the within-genome signature of "
           "modular versatility."),

    ("code",
     "vers = mat.sum(axis=1)\n"
     "dist = vers.value_counts().sort_index()\n"
     "print('versatility (capacities per genome, among the 800 with >=1):')\n"
     "for k, v in dist.items():\n"
     "    print(f'  {k} capacit{\"y\" if k==1 else \"ies\"}: {v:4d} genomes')\n"
     "print(f'\\nmean {vers.mean():.2f} | median {int(vers.median())} | max {int(vers.max())}')\n"
     "# how many genomes carry BOTH an aromatic and a non-aromatic capacity\n"
     "arom_cols = [c for c in order if c in AROMATIC]\n"
     "other_cols = [c for c in order if c not in AROMATIC]\n"
     "has_arom = mat[arom_cols].sum(axis=1) > 0\n"
     "has_other = mat[other_cols].sum(axis=1) > 0\n"
     "print(f'\\ngenomes with an aromatic capacity      : {int(has_arom.sum())}')\n"
     "print(f'genomes with a non-aromatic capacity   : {int(has_other.sum())}')\n"
     "print(f'genomes with BOTH (cross-block overlap): {int((has_arom & has_other).sum())}')"),

    ("code",
     "fig, ax = plt.subplots(figsize=(7, 4))\n"
     "ax.bar(dist.index, dist.values, color='#41b6c4', edgecolor='k', linewidth=0.4)\n"
     "ax.set_xlabel('catabolic capacities carried (of 8)')\n"
     "ax.set_ylabel('genomes')\n"
     "ax.set_title('Within-genome catabolic versatility (n=%d genomes with >=1 call)' % len(mat))\n"
     "fig.tight_layout(); fig.savefig(FIG / '05_versatility.png', dpi=150)\n"
     "print('saved 05_versatility.png'); plt.close(fig)"),

    ("md", "## Pairwise co-occurrence across genomes\n"
           "For each compound pair, build a 2x2 table over **all %d genomes** and compute "
           "the phi coefficient (effect size) and a Fisher exact p, BH-corrected across the "
           "28 pairs. phi>0 = co-occur more than independence predicts. The aromatic-vs-"
           "aromatic pairs are expected positive (shared funnel); watch the cross-block "
           "pairs."),

    ("code",
     "rows = []\n"
     "g_all = NGEN\n"
     "present = {c: set(mat.index[mat[c] == 1]) for c in order}\n"
     "for a, b in combinations(order, 2):\n"
     "    A, B = present[a], present[b]\n"
     "    n11 = len(A & B)\n"
     "    n10 = len(A - B)\n"
     "    n01 = len(B - A)\n"
     "    n00 = g_all - n11 - n10 - n01\n"
     "    # phi coefficient\n"
     "    num = n11 * n00 - n10 * n01\n"
     "    den = np.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))\n"
     "    phi = num / den if den > 0 else np.nan\n"
     "    _, p = fisher_exact([[n11, n10], [n01, n00]], alternative='greater')\n"
     "    blk = 'within-aromatic' if (a in AROMATIC and b in AROMATIC) else (\n"
     "          'within-other' if (a not in AROMATIC and b not in AROMATIC) else 'cross-block')\n"
     "    rows.append(dict(a=a, b=b, block=blk, n11=n11, n10=n10, n01=n01,\n"
     "                     phi=phi, p=p))\n"
     "co = pd.DataFrame(rows)\n"
     "# Benjamini-Hochberg\n"
     "m = len(co); co = co.sort_values('p').reset_index(drop=True)\n"
     "co['q'] = (co['p'] * m / (co.index + 1)).iloc[::-1].cummin().iloc[::-1].clip(upper=1)\n"
     "co = co.sort_values('phi', ascending=False).reset_index(drop=True)\n"
     "print(co[['a','b','block','n11','phi','p','q']].to_string(index=False))"),

    ("code",
     "print('co-occurrence summary by pair class (mean phi, n significant at q<0.05):')\n"
     "for blk, grp in co.groupby('block'):\n"
     "    print(f'  {blk:16s} pairs={len(grp):2d}  mean_phi={grp[\"phi\"].mean():+.3f}  '\n"
     "          f'q<0.05: {int((grp[\"q\"]<0.05).sum())}/{len(grp)}')\n"
     "cross = co[co['block'] == 'cross-block']\n"
     "print('\\ncross-block pairs (the real H2 test — distinct lower pathways):')\n"
     "print(cross[['a','b','n11','phi','p','q']].to_string(index=False))"),

    ("code",
     "# heatmap of phi\n"
     "M = pd.DataFrame(np.eye(len(order)), index=order, columns=order)\n"
     "for _, r in co.iterrows():\n"
     "    M.loc[r['a'], r['b']] = r['phi']; M.loc[r['b'], r['a']] = r['phi']\n"
     "fig, ax = plt.subplots(figsize=(7.5, 6.5))\n"
     "im = ax.imshow(M.values, cmap='RdBu_r', vmin=-1, vmax=1)\n"
     "ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=45, ha='right', fontsize=8)\n"
     "ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=8)\n"
     "for i in range(len(order)):\n"
     "    for j in range(len(order)):\n"
     "        if i != j:\n"
     "            ax.text(j, i, f'{M.values[i,j]:.2f}', ha='center', va='center',\n"
     "                    fontsize=6, color='k')\n"
     "ax.set_title('Catabolic co-occurrence (phi) across %d genomes' % g_all)\n"
     "fig.colorbar(im, ax=ax, shrink=0.7, label='phi coefficient')\n"
     "fig.tight_layout(); fig.savefig(FIG / '05_cooccurrence.png', dpi=150)\n"
     "print('saved 05_cooccurrence.png'); plt.close(fig)"),

    ("md", "## Phylogenetic concentration\n"
           "Is catabolic versatility clustered by clade? Map each genome to its genus and "
           "ask whether versatility (and the multi-capacity genomes specifically) "
           "concentrate in a few genera rather than spreading uniformly."),

    ("code",
     "tax = pred[['genome_id', 'taxon_name']].drop_duplicates('genome_id').set_index('genome_id')\n"
     "gv = mat.join(tax)\n"
     "gv['genus'] = gv['taxon_name'].astype(str).str.split().str[0]\n"
     "gv['versatility'] = vers\n"
     "by_genus = (gv.groupby('genus')\n"
     "            .agg(n_genomes=('versatility', 'size'),\n"
     "                 mean_vers=('versatility', 'mean'),\n"
     "                 max_vers=('versatility', 'max'))\n"
     "            .sort_values('mean_vers', ascending=False))\n"
     "print('top genera by mean catabolic versatility (>=3 genomes):')\n"
     "print(by_genus[by_genus['n_genomes'] >= 3].head(15).to_string())\n"
     "\n"
     "multi = gv[gv['versatility'] >= 3]\n"
     "print(f'\\nhigh-versatility genomes (>=3 capacities): {len(multi)}')\n"
     "print('their genus concentration:')\n"
     "gc = multi['genus'].value_counts()\n"
     "print(gc.head(10).to_string())\n"
     "print(f'top-3 genera hold {gc.head(3).sum()}/{len(multi)} '\n"
     "      f'({gc.head(3).sum()/len(multi)*100:.0f}%) of high-versatility genomes')"),

    ("code",
     "topg = by_genus[by_genus['n_genomes'] >= 3].head(15).iloc[::-1]\n"
     "fig, ax = plt.subplots(figsize=(8, 6))\n"
     "ax.barh(topg.index, topg['mean_vers'], color='#fc8d59', edgecolor='k', linewidth=0.4)\n"
     "ax.set_xlabel('mean capacities per genome (of 8)')\n"
     "ax.set_title('Catabolic versatility by genus (genera with >=3 genomes)')\n"
     "fig.tight_layout(); fig.savefig(FIG / '05_genus_versatility.png', dpi=150)\n"
     "print('saved 05_genus_versatility.png'); plt.close(fig)"),

    ("md", "## H2 verdict\n"
           "Deccompose the verdict so the aromatic-funnel artifact is not mistaken for "
           "broad modularity."),

    ("code",
     "co.to_csv(DATA / 'cooccurrence_matrix.tsv', sep='\\t', index=False)\n"
     "print('wrote data/cooccurrence_matrix.tsv', co.shape)\n"
     "\n"
     "wa = co[co['block'] == 'within-aromatic']\n"
     "xb = co[co['block'] == 'cross-block']\n"
     "wo = co[co['block'] == 'within-other']\n"
     "both = int((has_arom & has_other).sum())\n"
     "print('\\n=== H2 VERDICT ===')\n"
     "print(f'Scope: 8 catabolically-coherent compounds over {len(mat)} genomes '\n"
     "      f'(of {NGEN} total).')\n"
     "print(f'\\nWithin-genome: versatility right-skewed, mean {vers.mean():.2f}, max {int(vers.max())}.')\n"
     "print(f'\\nWithin-aromatic pairs: mean phi {wa[\"phi\"].mean():+.3f}, '\n"
     "      f'{int((wa[\"q\"]<0.05).sum())}/{len(wa)} significant (q<0.05).')\n"
     "print('  -> EXPECTED: shared protocatechuate/catechol lower pathway, not independent modules.')\n"
     "print(f'\\nCross-block pairs (distinct lower pathways = real H2 test):')\n"
     "print(f'  mean phi {xb[\"phi\"].mean():+.3f}, {int((xb[\"q\"]<0.05).sum())}/{len(xb)} significant.')\n"
     "print(f'  genomes carrying BOTH an aromatic and a non-aromatic capacity: {both}')\n"
     "if (xb['q'] < 0.05).any():\n"
     "    sig = xb[xb['q'] < 0.05].sort_values('phi', ascending=False)\n"
     "    print('  significant cross-block co-occurrences:')\n"
     "    for _, r in sig.iterrows():\n"
     "        print(f'    {r[\"a\"]} + {r[\"b\"]}: phi={r[\"phi\"]:+.3f} (n11={r[\"n11\"]}, q={r[\"q\"]:.1e})')\n"
     "else:\n"
     "    print('  -> NO significant cross-block co-occurrence.')\n"
     "print('\\nInterpretation: H2 support among aromatics is largely mechanistic (one shared')\n"
     "print('lower module). Genuine cross-module modularity is judged on the cross-block result')\n"
     "print('above. Phylogenetic clustering: see 05_genus_versatility.png.')"),
]

build_and_run("05_cooccurrence.ipynb", cells)
