from _build import build_and_run

cells = [
    ("md", "# NB03 — Organism Mapping (ENIGMA isolates, reaction bridge)\n\n"
           "Map each compound to the **ENIGMA isolate genomes** (`enigma_genome_depot_enigma`, "
           "3,109 genomes) that carry the enzymes for its catabolic reactions. This is the "
           "substrate for deliverable (a) — the per-compound isolate utilizer table (NB04).\n\n"
           "**Why a reaction-level bridge (not pathway-maps).** During design we found KEGG "
           "*pathway-map* membership is **non-discriminative**: broad degradation maps "
           "(`Degradation of aromatic compounds`, `Fatty acid degradation`, `Benzoate degradation`) "
           "are annotated in ~98% of all 3,109 genomes, so map presence predicts nothing. "
           "KEGG **reaction** (R-number) membership discriminates far better — signature "
           "reactions hit 1-130 genomes (<5%) while generic reactions hit ~3,000.\n\n"
           "**Method.** For each compound we take its KEGG reaction set, measure each reaction's "
           "*genome prevalence* across genome_depot, and split reactions into **signature** "
           "(prevalence < 10%, specific catabolic steps) vs **generic** (ubiquitous, uninformative). "
           "A genome is called a candidate utilizer **only if it carries ≥1 signature reaction** — "
           "this is what keeps the call discriminative. Each prediction carries a tier and a "
           "signature-completeness fraction.\n\n"
           "**Tiers (per RESEARCH_PLAN evidence ladder).**\n"
           "- **T2_pathway** — signature reaction carried *and* the compound sits in a KEGG "
           "degradation map (catabolic context confirmed; the strongest call short of measured fitness).\n"
           "- **T3_signature** — signature reaction carried, no degradation-map context "
           "(key-enzyme by annotation).\n\n"
           "**Honest coverage ceiling.** Only **67 of 207** distinct reactions across the 54 "
           "KEGG-mapped compounds are annotated in *any* ENIGMA genome, and only **15 compounds** "
           "have a signature reaction. The remaining 68 compounds get **no enzyme-level organism "
           "call** — the knowledge gap widens at the organism step, which is itself a headline result."),

    ("code",
     "import pandas as pd, numpy as np, json, os, math\n"
     "import matplotlib\n"
     "matplotlib.use('Agg')\n"
     "import matplotlib.pyplot as plt\n"
     "from pathlib import Path\n"
     "from dotenv import load_dotenv\n"
     "\n"
     "DATA = Path('../data'); FIG = Path('../figures')\n"
     "pd.set_option('display.max_columns', 40); pd.set_option('display.width', 220)\n"
     "\n"
     "# on-cluster Spark Connect (token from .env; never printed)\n"
     "load_dotenv('/home/aparkin/BERIL-research-observatory/.env')\n"
     "_tok = os.environ['KBASE_AUTH_TOKEN']\n"
     "from pyspark.sql import SparkSession\n"
     "_url = f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={_tok}'\n"
     "spark = SparkSession.builder.remote(_url).getOrCreate()\n"
     "DB = 'enigma_genome_depot_enigma'\n"
     "print('spark connected:', spark.version)"),

    ("md", "## Load deepened linkage + KEGG reaction sets (from NB02b cache)"),

    ("code",
     "link = pd.read_csv(DATA / 'compound_linkage_deepened.tsv', sep='\\t')\n"
     "cache = json.loads((DATA / 'deepen_cache.json').read_text())\n"
     "\n"
     "def rxns_for(cnum):\n"
     "    e = cache.get(f'https://rest.kegg.jp/link/reaction/{cnum}')\n"
     "    if not e: return []\n"
     "    body = e.get('body') if isinstance(e, dict) else e\n"
     "    if not body: return []\n"
     "    out = []\n"
     "    for p in body.strip().split('\\n'):\n"
     "        f = p.split('\\t')\n"
     "        if len(f) == 2 and f[1].startswith('rn:'):\n"
     "            out.append(f[1][3:])\n"
     "    return out\n"
     "\n"
     "kid = link[link['kegg_id'].notna()].copy()\n"
     "kid['rxn_set'] = kid['kegg_id'].map(rxns_for)\n"
     "kid['has_degmap'] = kid['kegg_deg_maps'].apply(lambda x: isinstance(x, str) and len(str(x)) > 3)\n"
     "all_rxn = sorted({r for s in kid['rxn_set'] for r in s})\n"
     "print('KEGG-mapped compounds:', len(kid))\n"
     "print('with >=1 reaction   :', int((kid['rxn_set'].map(len) > 0).sum()))\n"
     "print('distinct reactions  :', len(all_rxn))"),

    ("md", "## Reaction lookup + genome prevalence\n"
           "Map each R-number to its genome_depot FK id, then count distinct genomes carrying "
           "each reaction. Prevalence is the fraction of the 3,109 genomes."),

    ("code",
     "kr = spark.sql(f'SELECT id, kegg_id FROM {DB}.browser_kegg_reaction').toPandas()\n"
     "r2fk = dict(zip(kr['kegg_id'], kr['id']))\n"
     "fk2r = {v: k for k, v in r2fk.items()}\n"
     "fks = [r2fk[r] for r in all_rxn if r in r2fk]\n"
     "NGEN = spark.sql(f'SELECT COUNT(DISTINCT genome_id) n FROM {DB}.browser_gene').toPandas()['n'][0]\n"
     "print(f'reactions in genome_depot lookup: {len(fks)}/{len(all_rxn)}   total genomes: {NGEN}')\n"
     "\n"
     "fkstr = ','.join(map(str, fks))\n"
     "# (reaction_fk, genome_id) carriage for ALL in-genome reactions\n"
     "carr = spark.sql(f'''\n"
     "  SELECT rr.kegg_reaction_id fk, g.genome_id\n"
     "  FROM {DB}.browser_protein_kegg_reactions rr\n"
     "  JOIN {DB}.browser_gene g ON g.protein_id = rr.protein_id\n"
     "  WHERE rr.kegg_reaction_id IN ({fkstr})\n"
     "  GROUP BY rr.kegg_reaction_id, g.genome_id\n"
     "''').toPandas()\n"
     "carr['rxn'] = carr['fk'].map(fk2r)\n"
     "prev = carr.groupby('rxn')['genome_id'].nunique().rename('n_gen').reset_index()\n"
     "prev['prev_frac'] = prev['n_gen'] / NGEN\n"
     "prev_map = dict(zip(prev['rxn'], prev['prev_frac']))\n"
     "print('carriage rows:', len(carr))\n"
     "print(prev['prev_frac'].describe().to_string())"),

    ("md", "## Classify reactions: signature (<10% of genomes) vs generic\n"
           "Signature reactions are specific enough to predict catabolic capability; generic "
           "reactions (present in most genomes) are dropped from organism calls."),

    ("code",
     "SIG = 0.10\n"
     "prev['kind'] = np.where(prev['prev_frac'] < SIG, 'signature', 'generic')\n"
     "print(prev['kind'].value_counts().to_string())\n"
     "print()\n"
     "print('signature reactions (most specific first):')\n"
     "print(prev[prev.kind == 'signature'].sort_values('prev_frac')[['rxn', 'n_gen', 'prev_frac']]\n"
     "      .head(20).to_string(index=False))\n"
     "sig_rxns = set(prev[prev.kind == 'signature']['rxn'])"),

    ("md", "## Per-compound reaction coverage\n"
           "How many compounds even reach the organism step — the honest funnel."),

    ("code",
     "rows = []\n"
     "for _, r in kid.iterrows():\n"
     "    rs = r['rxn_set']\n"
     "    in_gd = [x for x in rs if x in prev_map]\n"
     "    sig = [x for x in in_gd if x in sig_rxns]\n"
     "    rows.append(dict(compound_id=r['compound_id'], name=r['name'],\n"
     "                     npc_pathway=r['npc_pathway'], kegg_id=r['kegg_id'],\n"
     "                     has_degmap=bool(r['has_degmap']),\n"
     "                     n_rxn=len(rs), n_in_gd=len(in_gd), n_sig=len(sig),\n"
     "                     sig_rxns=';'.join(sig)))\n"
     "cov = pd.DataFrame(rows)\n"
     "N = len(link)\n"
     "print(f'compounds total                         : {N}')\n"
     "print(f'  with KEGG id                          : {len(kid)}')\n"
     "print(f'  with >=1 reaction in genome_depot     : {int((cov.n_in_gd > 0).sum())}')\n"
     "print(f'  with >=1 SIGNATURE reaction (callable) : {int((cov.n_sig > 0).sum())}')\n"
     "print(f'    of which degradation-context (T2)   : {int(((cov.n_sig > 0) & cov.has_degmap).sum())}')\n"
     "print()\n"
     "print(cov[cov.n_sig > 0][['name', 'kegg_id', 'n_rxn', 'n_in_gd', 'n_sig', 'has_degmap']]\n"
     "      .sort_values('n_sig', ascending=False).to_string(index=False))"),

    ("md", "## Genome → strain → taxon resolution\n"
           "Load the small entity tables so each predicted genome carries an isolate name and "
           "NCBI taxon (used directly by NB04 deliverable a)."),

    ("code",
     "gen = spark.sql(f'SELECT id genome_id, name genome_name, strain_id, taxon_id FROM {DB}.browser_genome').toPandas()\n"
     "strn = spark.sql(f'SELECT id strain_pk, strain_id strain_code, full_name strain_full FROM {DB}.browser_strain').toPandas()\n"
     "tax = spark.sql(f'SELECT id taxon_pk, taxonomy_id ncbi_taxid, rank, name taxon_name FROM {DB}.browser_taxon').toPandas()\n"
     "gmap = gen.merge(strn, left_on='strain_id', right_on='strain_pk', how='left') \\\n"
     "          .merge(tax, left_on='taxon_id', right_on='taxon_pk', how='left')\n"
     "gmap = gmap[['genome_id', 'genome_name', 'strain_full', 'ncbi_taxid', 'rank', 'taxon_name']]\n"
     "print('genome metadata rows:', len(gmap))\n"
     "print(gmap.head(5).to_string(index=False))"),

    ("md", "## Build per-(compound, genome) predictions\n"
           "Emit a row **only** when the genome carries ≥1 signature reaction of the compound. "
           "Score = sum of -log10(prevalence) over carried signature reactions (rarity-weighted). "
           "`sig_completeness` = carried signatures / total signatures for that compound."),

    ("code",
     "# reaction -> compounds (a reaction may serve several compounds)\n"
     "rxn2comp = {}\n"
     "for _, r in kid.iterrows():\n"
     "    for x in r['rxn_set']:\n"
     "        if x in sig_rxns:\n"
     "            rxn2comp.setdefault(x, []).append(r['compound_id'])\n"
     "\n"
     "# carriage restricted to signature reactions\n"
     "csig = carr[carr['rxn'].isin(sig_rxns)].copy()\n"
     "comp_meta = kid.set_index('compound_id')\n"
     "sig_tot = {cid: sum(1 for x in comp_meta.loc[cid, 'rxn_set'] if x in sig_rxns)\n"
     "           for cid in comp_meta.index}\n"
     "w = {x: -math.log10(prev_map[x]) for x in sig_rxns}\n"
     "\n"
     "from collections import defaultdict\n"
     "acc = defaultdict(lambda: {'rxns': [], 'score': 0.0})\n"
     "for _, row in csig.iterrows():\n"
     "    rx, gid = row['rxn'], row['genome_id']\n"
     "    for cid in rxn2comp.get(rx, []):\n"
     "        a = acc[(cid, gid)]\n"
     "        a['rxns'].append(rx); a['score'] += w[rx]\n"
     "\n"
     "pred = []\n"
     "for (cid, gid), a in acc.items():\n"
     "    m = comp_meta.loc[cid]\n"
     "    nsig = len(set(a['rxns']))\n"
     "    tier = 'T2_pathway' if m['has_degmap'] else 'T3_signature'\n"
     "    pred.append(dict(compound_id=cid, name=m['name'], npc_pathway=m['npc_pathway'],\n"
     "                     kegg_id=m['kegg_id'], genome_id=gid,\n"
     "                     tier=tier, n_sig_carried=nsig,\n"
     "                     sig_completeness=round(nsig / max(sig_tot[cid], 1), 3),\n"
     "                     score=round(a['score'], 3),\n"
     "                     sig_rxns_carried=';'.join(sorted(set(a['rxns'])))))\n"
     "pred = pd.DataFrame(pred).merge(gmap, on='genome_id', how='left')\n"
     "pred = pred.sort_values(['compound_id', 'score'], ascending=[True, False]).reset_index(drop=True)\n"
     "print('prediction rows (compound x genome):', len(pred))\n"
     "print('distinct compounds with calls :', pred['compound_id'].nunique())\n"
     "print('distinct genomes called       :', pred['genome_id'].nunique())\n"
     "print(pred['tier'].value_counts().to_string())"),

    ("code",
     "# per-compound summary: how many genomes, tier, top isolate\n"
     "summ = (pred.groupby(['compound_id', 'name', 'npc_pathway', 'tier'])\n"
     "        .agg(n_genomes=('genome_id', 'nunique'),\n"
     "             max_score=('score', 'max'),\n"
     "             max_completeness=('sig_completeness', 'max'))\n"
     "        .reset_index().sort_values('n_genomes', ascending=False))\n"
     "print(summ.to_string(index=False))"),

    ("md", "## Figure: candidate-utilizer breadth per compound"),

    ("code",
     "fig, ax = plt.subplots(figsize=(8, 5))\n"
     "s = summ.sort_values('n_genomes')\n"
     "colors = {'T2_pathway': '#2c7fb8', 'T3_signature': '#7fcdbb'}\n"
     "ax.barh(s['name'], s['n_genomes'], color=[colors[t] for t in s['tier']])\n"
     "ax.set_xlabel('ENIGMA isolate genomes carrying a signature reaction')\n"
     "ax.set_title('Reaction-bridge organism calls (n=%d compounds of 83)' % summ['compound_id'].nunique())\n"
     "from matplotlib.patches import Patch\n"
     "ax.legend(handles=[Patch(color=colors['T2_pathway'], label='T2 (degradation-context)'),\n"
     "                   Patch(color=colors['T3_signature'], label='T3 (signature enzyme)')],\n"
     "          loc='lower right')\n"
     "fig.tight_layout(); fig.savefig(FIG / '03_organism_calls.png', dpi=150)\n"
     "print('saved 03_organism_calls.png'); plt.close(fig)"),

    ("md", "## Save predictions + organism-dark gap list"),

    ("code",
     "pred_cols = ['compound_id', 'name', 'npc_pathway', 'kegg_id', 'tier',\n"
     "             'genome_id', 'genome_name', 'strain_full', 'ncbi_taxid', 'rank', 'taxon_name',\n"
     "             'n_sig_carried', 'sig_completeness', 'score', 'sig_rxns_carried']\n"
     "pred[pred_cols].to_csv(DATA / 'compound_organism_predictions.tsv', sep='\\t', index=False)\n"
     "print('wrote data/compound_organism_predictions.tsv', pred.shape)\n"
     "\n"
     "# compounds with NO enzyme-level organism call — the gap that widens at the organism step\n"
     "called = set(pred['compound_id'])\n"
     "dark = link[~link['compound_id'].isin(called)][['compound_id', 'name', 'npc_pathway', 'kegg_id', 'best_tier']].copy()\n"
     "def why(r):\n"
     "    if pd.isna(r['kegg_id']): return 'no_kegg'\n"
     "    sub = cov[cov.compound_id == r['compound_id']]\n"
     "    if len(sub) == 0: return 'no_kegg'\n"
     "    if sub.iloc[0]['n_in_gd'] == 0: return 'kegg_no_rxn_in_genomes'\n"
     "    return 'only_generic_rxns'\n"
     "dark['organism_dark_reason'] = dark.apply(why, axis=1)\n"
     "dark.to_csv(DATA / 'compound_organism_dark.tsv', sep='\\t', index=False)\n"
     "print('organism-dark compounds:', len(dark), '/', len(link))\n"
     "print(dark['organism_dark_reason'].value_counts().to_string())\n"
     "print()\n"
     "print(dark[['name', 'npc_pathway', 'organism_dark_reason']].to_string(index=False))"),
]

build_and_run("03_organism_mapping.ipynb", cells)
