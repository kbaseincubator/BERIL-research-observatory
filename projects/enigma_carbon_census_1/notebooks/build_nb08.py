from _build import build_and_run

cells = [
    ("md", "# NB08 — Synthesis: Three Deliverables + the Honest Gap Map\n\n"
           "Assemble the ENIGMA Carbon Census knowledge product from NB01–NB07 into one place:\n\n"
           "- **(a) ENIGMA-isolate utilizer table** — NB04 `enigma_utilizer_predictions.tsv`\n"
           "- **(b) Phylogenetic utilizer map + certainty** — NB06 `phylo_utilizer_map.tsv`\n"
           "- **(c) Co-occurrence (H2) + environmental atlas** — NB05 `cooccurrence_matrix.tsv`, "
           "NB07 `environmental_atlas.tsv`\n\n"
           "**The governing principle of this census is honesty over coverage.** The headline is "
           "not 'we predicted utilizers for everything' — it is the opposite: of 83 compounds, "
           "only a small minority are knowledge-supported enough to make an organism call. The "
           "rest are **organism-dark**, and that gap is the most actionable result for prioritizing "
           "wet-lab discovery — those are the compounds where genetic determinants are genuinely "
           "unknown and worth the experiment."),

    ("code",
     "import pandas as pd, numpy as np\n"
     "import matplotlib\n"
     "matplotlib.use('Agg')\n"
     "import matplotlib.pyplot as plt\n"
     "from pathlib import Path\n"
     "\n"
     "DATA = Path('../data'); FIG = Path('../figures')\n"
     "pd.set_option('display.max_columns', 50); pd.set_option('display.width', 240)\n"
     "\n"
     "comp = pd.read_csv(DATA / 'compounds_selected.tsv', sep='\\t')\n"
     "link = pd.read_csv(DATA / 'compound_linkage_deepened.tsv', sep='\\t')\n"
     "dark = pd.read_csv(DATA / 'compound_organism_dark.tsv', sep='\\t')\n"
     "deliv_a = pd.read_csv(DATA / 'enigma_utilizer_predictions.tsv', sep='\\t')\n"
     "phylo = pd.read_csv(DATA / 'phylo_utilizer_map.tsv', sep='\\t')\n"
     "env = pd.read_csv(DATA / 'environmental_atlas.tsv', sep='\\t')\n"
     "print('compounds:', len(comp), '| linkage rows:', len(link), '| organism-dark:', len(dark))\n"
     "print('deliverable (a) rows:', len(deliv_a), '| (b) strain placements:', len(phylo),\n"
     "      '| (c) genus field-calls:', len(env))"),

    ("md", "## The discovery funnel (83 → callable)\n"
           "Every narrowing step, with the count that survives it. This is the spine of the census."),

    ("code",
     "n_total = len(comp)\n"
     "n_struct = link['inchikey'].notna().sum()\n"
     "n_kegg = link['kegg_id'].notna().sum()\n"
     "callable_ids = set(deliv_a[deliv_a['tier'] != 'T0_organism_dark']['compound_id'])\n"
     "n_callable = len(callable_ids)\n"
     "n_dark = comp['compound_id'].nunique() - n_callable\n"
     "n_placed = phylo['ncbi_taxid'].nunique()\n"
     "n_high = (phylo['certainty'] == 'high').sum()\n"
     "n_field_genera = env[env['field_detected']]['genus'].nunique()\n"
     "\n"
     "funnel = pd.DataFrame([\n"
     "    ('compounds in census', n_total),\n"
     "    ('structure resolved (InChIKey)', int(n_struct)),\n"
     "    ('KEGG-linked', int(n_kegg)),\n"
     "    ('callable (>=1 isolate utilizer)', n_callable),\n"
     "    ('organism-dark (no call)', n_dark),\n"
     "], columns=['step', 'n'])\n"
     "print(funnel.to_string(index=False))\n"
     "print(f'\\nutilizer strains placed (b): {n_placed} | high-certainty strain-calls: {n_high}')\n"
     "print(f'utilizer genera present in SSO field (c): {n_field_genera}')"),

    ("code",
     "fig, ax = plt.subplots(figsize=(8, 4))\n"
     "vals = funnel[funnel['step'] != 'organism-dark (no call)']\n"
     "ax.barh(range(len(vals)), vals['n'], color='#2b8cbe')\n"
     "ax.set_yticks(range(len(vals))); ax.set_yticklabels(vals['step'])\n"
     "ax.invert_yaxis()\n"
     "for i, v in enumerate(vals['n']):\n"
     "    ax.text(v + 0.5, i, str(int(v)), va='center', fontsize=9)\n"
     "ax.set_xlabel('compounds')\n"
     "ax.set_title('ENIGMA Carbon Census discovery funnel (83 compounds)')\n"
     "fig.tight_layout(); fig.savefig(FIG / '08_funnel.png', dpi=150)\n"
     "print('saved 08_funnel.png'); plt.close(fig)"),

    ("md", "## Per-compound master summary\n"
           "One row per compound: source, pathway, linkage tier, callable status, utilizer breadth "
           "(b), and field occurrence (c). The single table a wet-lab planner reads."),

    ("code",
     "# (b) breadth + certainty per compound\n"
     "b = (phylo.groupby('name')\n"
     "     .agg(n_strains=('ncbi_taxid', 'nunique'),\n"
     "          n_high=('certainty', lambda s: (s == 'high').sum()),\n"
     "          n_genera=('genus', 'nunique')).reset_index())\n"
     "# (c) field occurrence per compound\n"
     "c = (env.groupby('name')\n"
     "     .agg(n_genera_c=('genus', 'nunique'),\n"
     "          n_field=('field_detected', 'sum'),\n"
     "          top_field_prev=('prevalence', 'max')).reset_index())\n"
     "\n"
     "master = comp[['compound_id', 'name', 'source_short', 'npc_pathway']].copy()\n"
     "master = master.merge(link[['compound_id', 'best_tier', 'deep_tier', 'rescued']],\n"
     "                      on='compound_id', how='left')\n"
     "master['callable'] = master['compound_id'].isin(callable_ids)\n"
     "master = master.merge(b, on='name', how='left').merge(c, on='name', how='left')\n"
     "for col in ['n_strains', 'n_high', 'n_genera', 'n_genera_c', 'n_field']:\n"
     "    master[col] = master[col].fillna(0).astype(int)\n"
     "master = master.sort_values(['callable', 'n_strains'], ascending=[False, False])\n"
     "print('=== CALLABLE COMPOUNDS ===')\n"
     "print(master[master['callable']][['name', 'source_short', 'npc_pathway', 'best_tier',\n"
     "      'n_strains', 'n_high', 'n_genera', 'n_field', 'top_field_prev']].to_string(index=False))"),

    ("md", "## The organism-dark gap list (the headline result)\n"
           "Compounds with no isolate utilizer call — where genetic determinants of carbon use are "
           "genuinely unknown. These are the prioritized targets for wet-lab discovery."),

    ("code",
     "dk = master[~master['callable']].copy()\n"
     "dk = dk.merge(dark[['compound_id', 'organism_dark_reason']], on='compound_id', how='left')\n"
     "print(f'organism-dark compounds: {len(dk)} / {len(master)} '\n"
     "      f'({100*len(dk)/len(master):.0f}%)')\n"
     "print('\\nby compound source:')\n"
     "print(dk.groupby('source_short')['compound_id'].nunique().to_string())\n"
     "print('\\nby NPC pathway (top dark classes):')\n"
     "print(dk.groupby('npc_pathway')['compound_id'].nunique().sort_values(ascending=False).to_string())\n"
     "print('\\nby dark reason:')\n"
     "print(dk['organism_dark_reason'].value_counts().to_string())"),

    ("md", "## Write the master census table"),

    ("code",
     "out = master[['compound_id', 'name', 'source_short', 'npc_pathway',\n"
     "              'best_tier', 'deep_tier', 'rescued', 'callable',\n"
     "              'n_strains', 'n_high', 'n_genera', 'n_field', 'top_field_prev']].copy()\n"
     "out = out.merge(dark[['compound_id', 'organism_dark_reason']], on='compound_id', how='left')\n"
     "out = out.sort_values(['callable', 'n_strains'], ascending=[False, False]).reset_index(drop=True)\n"
     "out.to_csv(DATA / 'census_master_summary.tsv', sep='\\t', index=False)\n"
     "print('wrote data/census_master_summary.tsv', out.shape)\n"
     "\n"
     "print('\\n' + '=' * 60)\n"
     "print('ENIGMA CARBON CENSUS — HEADLINE')\n"
     "print('=' * 60)\n"
     "print(f'compounds in census              : {n_total}')\n"
     "print(f'structure-resolved               : {int(n_struct)}')\n"
     "print(f'KEGG-linked                      : {int(n_kegg)}')\n"
     "print(f'CALLABLE (>=1 isolate utilizer)  : {n_callable}')\n"
     "print(f'ORGANISM-DARK (discovery targets): {n_dark}  <- the actionable gap')\n"
     "print(f'utilizer strains placed (b)      : {n_placed}  ({n_high} high-certainty)')\n"
     "print(f'utilizer genera in SSO field (c) : {n_field_genera}')\n"
     "print('H2 (modularity): co-occurrence not supported beyond the shared aromatic funnel; '\n"
     "      'phylogenetic concentration in Burkholderiales IS supported.')\n"
     "print('H3 (source-tracking): UNTESTABLE/CONFOUNDED (2/8 necromass, both phthalate-class).')"),
]

build_and_run("08_synthesis.ipynb", cells)
