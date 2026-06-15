from _build import build_and_run

cells = [
    ("md", "# NB04 — ENIGMA Isolate Utilizer Table (Deliverable a)\n\n"
           "Turn the (compound × genome) reaction-bridge calls from NB03 into the **wet-lab-facing "
           "deliverable**: for each compound, which **ENIGMA isolate strains** are predicted to "
           "catabolize it, with a confidence tier, the specific enzyme step, and a specificity flag "
           "to guide strain selection.\n\n"
           "**What this notebook adds over NB03:**\n"
           "1. **Strain-level rollup** — collapse multiple genome assemblies of the same strain to one "
           "row (best-scoring genome), since the wet lab tests strains, not assemblies.\n"
           "2. **Enzyme annotation** — attach the KEGG reaction *description* (e.g. *salicylate "
           "hydroxylase*) so each call names the enzyme to assay.\n"
           "3. **Specificity flag** — `narrow` (≤10 strains), `focused` (≤50), `broad` (>50). Narrow "
           "calls are the most actionable for picking a discriminating test strain; broad calls "
           "(central aromatic intermediates) say *most isolates can do this*.\n"
           "4. **Explicit Tier-0 rows** — the 68 organism-dark compounds are written into the same "
           "table as no-call rows, so the deliverable is complete and the gap is visible, not hidden."),

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
     "dark = pd.read_csv(DATA / 'compound_organism_dark.tsv', sep='\\t')\n"
     "link = pd.read_csv(DATA / 'compound_linkage_deepened.tsv', sep='\\t')\n"
     "print('prediction rows:', len(pred), '| dark compounds:', len(dark))"),

    ("md", "## Enzyme descriptions for the signature reactions\n"
           "Pull the human-readable reaction name for each signature R-number so the deliverable "
           "names the enzyme step, not just an R-number."),

    ("code",
     "load_dotenv('/home/aparkin/BERIL-research-observatory/.env')\n"
     "_tok = os.environ['KBASE_AUTH_TOKEN']\n"
     "from pyspark.sql import SparkSession\n"
     "_url = f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={_tok}'\n"
     "spark = SparkSession.builder.remote(_url).getOrCreate()\n"
     "DB = 'enigma_genome_depot_enigma'\n"
     "\n"
     "sig_set = sorted({r for s in pred['sig_rxns_carried'].dropna() for r in str(s).split(';') if r})\n"
     "rstr = ','.join(f\"'{r}'\" for r in sig_set)\n"
     "rdesc = spark.sql(f\"SELECT kegg_id rxn, description FROM {DB}.browser_kegg_reaction \"\n"
     "                  f\"WHERE kegg_id IN ({rstr})\").toPandas()\n"
     "rdesc_map = dict(zip(rdesc['rxn'], rdesc['description']))\n"
     "print('signature reactions annotated:', len(rdesc_map), '/', len(sig_set))\n"
     "for r in sig_set[:12]:\n"
     "    print(f'  {r}: {rdesc_map.get(r, \"(no desc)\")[:80]}')"),

    ("md", "## Strain-level rollup\n"
           "Group genomes by strain (NCBI taxon + full name); keep the best-scoring genome per strain."),

    ("code",
     "pred['enzymes'] = pred['sig_rxns_carried'].apply(\n"
     "    lambda s: '; '.join(f'{r} ({rdesc_map.get(r, \"?\")})' for r in str(s).split(';') if r))\n"
     "# best genome per (compound, strain)\n"
     "pred = pred.sort_values('score', ascending=False)\n"
     "strain = (pred.groupby(['compound_id', 'name', 'npc_pathway', 'kegg_id', 'tier',\n"
     "                        'ncbi_taxid', 'taxon_name'], dropna=False)\n"
     "          .agg(best_genome=('genome_name', 'first'),\n"
     "               strain_full=('strain_full', 'first'),\n"
     "               n_genomes=('genome_id', 'nunique'),\n"
     "               score=('score', 'max'),\n"
     "               sig_completeness=('sig_completeness', 'max'),\n"
     "               enzymes=('enzymes', 'first'))\n"
     "          .reset_index())\n"
     "print('strain-level prediction rows:', len(strain))\n"
     "print('distinct strains predicted    :', strain['ncbi_taxid'].nunique())"),

    ("md", "## Per-compound specificity + breadth"),

    ("code",
     "br = (strain.groupby(['compound_id', 'name', 'npc_pathway', 'tier'])\n"
     "      .agg(n_strains=('ncbi_taxid', 'nunique'), max_score=('score', 'max'),\n"
     "           max_completeness=('sig_completeness', 'max')).reset_index())\n"
     "def spec(n):\n"
     "    return 'narrow' if n <= 10 else ('focused' if n <= 50 else 'broad')\n"
     "br['specificity'] = br['n_strains'].map(spec)\n"
     "br = br.sort_values('n_strains')\n"
     "print(br[['name', 'npc_pathway', 'tier', 'n_strains', 'specificity',\n"
     "          'max_score', 'max_completeness']].to_string(index=False))"),

    ("md", "## Genus distribution among predicted utilizers\n"
           "Which genera show up most often as candidate utilizers — useful for choosing test strains "
           "already in hand."),

    ("code",
     "strain['genus'] = strain['taxon_name'].astype(str).str.split().str[0]\n"
     "gtop = (strain.groupby('genus')['compound_id'].nunique().rename('n_compounds')\n"
     "        .reset_index().sort_values('n_compounds', ascending=False).head(20))\n"
     "gcount = strain['genus'].value_counts().rename('n_calls')\n"
     "gtop = gtop.merge(gcount, left_on='genus', right_index=True)\n"
     "print(gtop.to_string(index=False))"),

    ("code",
     "fig, ax = plt.subplots(figsize=(8, 6))\n"
     "g = gtop.sort_values('n_calls')\n"
     "ax.barh(g['genus'], g['n_calls'], color='#41b6c4')\n"
     "ax.set_xlabel('candidate-utilizer calls (compound x strain)')\n"
     "ax.set_title('Top genera among predicted ENIGMA isolate utilizers')\n"
     "fig.tight_layout(); fig.savefig(FIG / '04_utilizer_genera.png', dpi=150)\n"
     "print('saved 04_utilizer_genera.png'); plt.close(fig)"),

    ("md", "## Assemble the complete deliverable (a) table\n"
           "Predicted calls + explicit Tier-0 rows for the 68 organism-dark compounds."),

    ("code",
     "call_cols = ['compound_id', 'name', 'npc_pathway', 'kegg_id', 'tier',\n"
     "             'ncbi_taxid', 'taxon_name', 'strain_full', 'best_genome',\n"
     "             'n_genomes', 'score', 'sig_completeness', 'enzymes']\n"
     "calls = strain[call_cols].copy()\n"
     "calls = calls.merge(br[['compound_id', 'specificity']].drop_duplicates(), on='compound_id', how='left')\n"
     "\n"
     "dark_rows = dark.rename(columns={'best_tier': 'linkage_tier'}).copy()\n"
     "dark_rows['tier'] = 'T0_organism_dark'\n"
     "for c in ['ncbi_taxid', 'taxon_name', 'strain_full', 'best_genome', 'n_genomes',\n"
     "          'score', 'sig_completeness', 'enzymes', 'specificity']:\n"
     "    dark_rows[c] = np.nan\n"
     "dark_rows['enzymes'] = dark_rows['organism_dark_reason']\n"
     "dark_rows = dark_rows[call_cols + ['specificity']]\n"
     "\n"
     "deliverable = pd.concat([calls, dark_rows], ignore_index=True)\n"
     "deliverable = deliverable.sort_values(['tier', 'compound_id', 'score'],\n"
     "                                      ascending=[True, True, False]).reset_index(drop=True)\n"
     "deliverable.to_csv(DATA / 'enigma_utilizer_predictions.tsv', sep='\\t', index=False)\n"
     "print('wrote data/enigma_utilizer_predictions.tsv', deliverable.shape)\n"
     "print()\n"
     "print('tier breakdown (rows):')\n"
     "print(deliverable['tier'].value_counts().to_string())\n"
     "print()\n"
     "print('compounds with >=1 isolate call:', calls['compound_id'].nunique(),\n"
     "      '| organism-dark compounds:', dark_rows['compound_id'].nunique())"),

    ("md", "## Spot-check: the actionable narrow calls\n"
           "The compounds where a single strain choice would be discriminating in the wet lab."),

    ("code",
     "narrow_ids = br[br['specificity'] == 'narrow']['compound_id']\n"
     "nz = calls[calls['compound_id'].isin(narrow_ids)].sort_values(['name', 'score'], ascending=[True, False])\n"
     "for nm, grp in nz.groupby('name'):\n"
     "    e = grp.iloc[0]['enzymes']\n"
     "    print(f'\\n=== {nm}  [{grp.iloc[0][\"tier\"]}]  enzyme: {e[:70]} ===')\n"
     "    print(grp[['taxon_name', 'strain_full', 'score', 'sig_completeness']].head(10).to_string(index=False))"),
]

build_and_run("04_enigma_utilizers.ipynb", cells)
