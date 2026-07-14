from _build import build_and_run

cells = [
    ("md", "# NB07 — Environmental Occurrence Atlas (Deliverable c, environmental half)\n\n"
           "Deliverable (c) has two halves. NB05 did the **pathway co-occurrence** half (H2). "
           "This notebook does the **environmental** half: do the predicted ENIGMA-isolate "
           "utilizer genera (from NB04/NB06) actually occur in the **Oak Ridge SSO subsurface "
           "field communities**? We use the Zhou Lab 16S ASV surveys in `enigma_coral` — the SSO "
           "sediment and pump-test datasets — which sample the *same contaminated groundwater "
           "system* the SSO compounds were drawn from.\n\n"
           "**H3 honesty note — the planned source-tracking test is not supportable.** H3 asked "
           "whether a utilizer's environmental distribution tracks its compound's "
           "groundwater-vs-necromass source. Of the 8 callable compounds, only **2 are necromass** "
           "(terephthalic acid, phthalic acid) — and *both* are phthalate-class aromatics whose "
           "predicted utilizers are Actinomycetota-heavy. Source is therefore **confounded with "
           "chemical class**, and the necromass arm is n=2. We do **not** manufacture a "
           "source-contrast statistic from this. Instead we report the honest, well-powered "
           "question the field data *can* answer: **field presence/abundance of the predicted "
           "utilizer genera at the SSO site.**\n\n"
           "**What 'field-present' buys the wet lab.** A predicted utilizer genus that is also a "
           "real, abundant resident of the SSO subsurface is a stronger strain-selection bet than "
           "one predicted from genomes but absent in the field community."),

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
     "phylo = pd.read_csv(DATA / 'phylo_utilizer_map.tsv', sep='\\t')\n"
     "comp = pd.read_csv(DATA / 'compounds_selected.tsv', sep='\\t')\n"
     "src = dict(zip(comp['name'], comp['source_short']))\n"
     "# implicated genera per compound (drop nulls / unresolved)\n"
     "imp = (phylo[phylo['genus'].notna()][['name', 'npc_pathway', 'genus', 'certainty']]\n"
     "       .drop_duplicates())\n"
     "imp['source'] = imp['name'].map(src)\n"
     "print('compounds with >=1 genus-resolved utilizer:', imp['name'].nunique())\n"
     "print('distinct implicated genera:', imp['genus'].nunique())\n"
     "print(imp.groupby('source')['name'].nunique().to_string())"),

    ("md", "## SSO field survey: genus prevalence + relative abundance\n"
           "Two Zhou Lab 16S ASV surveys of the Oak Ridge SSO subsurface in `enigma_coral`:\n"
           "- **SSO sediment** — counts `ddt_brick0000459`, taxonomy `ddt_brick0000458`\n"
           "- **SSO pump-test** — counts `ddt_brick0000462`, taxonomy `ddt_brick0000461`\n\n"
           "For each survey: assign ASVs to genus, sum counts to genus per community, divide by "
           "the community total (all ASVs, incl. genus-unassigned) for relative abundance, then "
           "pool communities. Prevalence = fraction of SSO communities where the genus is detected."),

    ("code",
     "load_dotenv('/home/aparkin/BERIL-research-observatory/.env')\n"
     "_tok = os.environ['KBASE_AUTH_TOKEN']\n"
     "from pyspark.sql import SparkSession, functions as F\n"
     "_url = f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={_tok}'\n"
     "spark = SparkSession.builder.remote(_url).getOrCreate()\n"
     "DB = 'enigma_coral'\n"
     "\n"
     "def survey_genus_relab(counts_b, tax_b, survey):\n"
     "    counts = (spark.table(f'{DB}.{counts_b}')\n"
     "              .select('sdt_asv_name', 'sdt_community_name',\n"
     "                      F.col('count_count_unit').cast('double').alias('cnt'))\n"
     "              .filter('cnt > 0'))\n"
     "    tax = (spark.table(f'{DB}.{tax_b}')\n"
     "           .filter(\"taxonomic_level_sys_oterm_name = 'genus'\")\n"
     "           .select('sdt_asv_name', F.col('sdt_taxon_name').alias('genus')))\n"
     "    tot = counts.groupBy('sdt_community_name').agg(F.sum('cnt').alias('tot'))\n"
     "    gc = (counts.join(tax, 'sdt_asv_name')\n"
     "          .groupBy('sdt_community_name', 'genus').agg(F.sum('cnt').alias('gcnt'))\n"
     "          .join(tot, 'sdt_community_name'))\n"
     "    gc = gc.withColumn('relab', F.col('gcnt') / F.col('tot'))\n"
     "    pdf = gc.toPandas()\n"
     "    pdf['survey'] = survey\n"
     "    return pdf\n"
     "\n"
     "sed = survey_genus_relab('ddt_brick0000459', 'ddt_brick0000458', 'SSO_sediment')\n"
     "pmp = survey_genus_relab('ddt_brick0000462', 'ddt_brick0000461', 'SSO_pump_test')\n"
     "fld = pd.concat([sed, pmp], ignore_index=True)\n"
     "ncomm = fld.groupby('survey')['sdt_community_name'].nunique()\n"
     "print('communities per survey:'); print(ncomm.to_string())\n"
     "print('total SSO communities pooled:', fld['sdt_community_name'].nunique())\n"
     "print('genus x community rows:', len(fld), '| distinct field genera:', fld['genus'].nunique())"),

    ("md", "## Per-genus field statistics (pooled SSO)"),

    ("code",
     "N_TOT = fld['sdt_community_name'].nunique()\n"
     "gstat = (fld.groupby('genus')\n"
     "         .agg(n_comm_present=('sdt_community_name', 'nunique'),\n"
     "              mean_relab=('relab', 'mean'),\n"
     "              max_relab=('relab', 'max')).reset_index())\n"
     "gstat['prevalence'] = gstat['n_comm_present'] / N_TOT\n"
     "gstat = gstat.sort_values('prevalence', ascending=False)\n"
     "print('field genera with prevalence >= 0.5 (core SSO taxa):')\n"
     "print(gstat[gstat['prevalence'] >= 0.5].head(20).to_string(index=False))"),

    ("md", "## Match predicted utilizer genera to SSO field occurrence"),

    ("code",
     "m = imp.merge(gstat, on='genus', how='left')\n"
     "m['field_detected'] = m['n_comm_present'].notna()\n"
     "m['prevalence'] = m['prevalence'].fillna(0.0)\n"
     "m['mean_relab'] = m['mean_relab'].fillna(0.0)\n"
     "\n"
     "det = m['field_detected'].sum()\n"
     "print(f'implicated genus-calls: {len(m)} | field-detected at SSO: {det} '\n"
     "      f'({100*det/len(m):.0f}%)')\n"
     "print('distinct implicated genera detected in SSO field:',\n"
     "      m[m['field_detected']]['genus'].nunique(), '/', m['genus'].nunique())\n"
     "print('\\nfield-detected implicated genera by prevalence:')\n"
     "gg = (m[m['field_detected']].groupby('genus')\n"
     "      .agg(prevalence=('prevalence', 'first'), mean_relab=('mean_relab', 'first'),\n"
     "           n_compounds=('name', 'nunique')).reset_index()\n"
     "      .sort_values('prevalence', ascending=False))\n"
     "print(gg.head(25).to_string(index=False))"),

    ("md", "## Per-compound: how many predicted utilizer genera are real SSO residents\n"
           "The wet-lab view — for each compound, what fraction of its predicted utilizer genera "
           "are actually present in the SSO subsurface field community, and how abundant."),

    ("code",
     "pc = (m.groupby(['name', 'npc_pathway', 'source'])\n"
     "      .agg(n_genera=('genus', 'nunique'),\n"
     "           n_field=('genus', lambda s: m.loc[s.index][m.loc[s.index, 'field_detected']]['genus'].nunique()),\n"
     "           max_prev=('prevalence', 'max'),\n"
     "           best_genus=('genus', 'first')).reset_index())\n"
     "# recompute best field genus per compound cleanly\n"
     "best = (m[m['field_detected']].sort_values('prevalence', ascending=False)\n"
     "        .groupby('name').agg(top_field_genus=('genus', 'first'),\n"
     "                             top_field_prev=('prevalence', 'first')).reset_index())\n"
     "pc = pc.drop(columns=['best_genus']).merge(best, on='name', how='left')\n"
     "pc['frac_field'] = pc['n_field'] / pc['n_genera']\n"
     "pc = pc.sort_values('frac_field', ascending=False)\n"
     "print(pc[['name', 'source', 'n_genera', 'n_field', 'frac_field',\n"
     "          'top_field_genus', 'top_field_prev']].to_string(index=False))"),

    ("code",
     "fig, ax = plt.subplots(figsize=(8, 4.5))\n"
     "p = pc.sort_values('frac_field')\n"
     "colors = ['#2c7fb8' if s == 'groundwater' else '#d95f0e' for s in p['source']]\n"
     "ax.barh(p['name'], p['frac_field'], color=colors)\n"
     "for i, (_, r) in enumerate(p.iterrows()):\n"
     "    ax.text(r['frac_field'] + 0.01, i, f\"{int(r['n_field'])}/{int(r['n_genera'])}\",\n"
     "            va='center', fontsize=8)\n"
     "ax.set_xlabel('fraction of predicted utilizer genera detected in SSO field community')\n"
     "ax.set_xlim(0, 1.15)\n"
     "from matplotlib.patches import Patch\n"
     "ax.legend(handles=[Patch(color='#2c7fb8', label='groundwater'),\n"
     "                   Patch(color='#d95f0e', label='necromass')],\n"
     "          title='compound source', loc='lower right')\n"
     "ax.set_title('Predicted utilizers present in Oak Ridge SSO subsurface field community')\n"
     "fig.tight_layout(); fig.savefig(FIG / '07_field_occurrence.png', dpi=150)\n"
     "print('saved 07_field_occurrence.png'); plt.close(fig)"),

    ("md", "## Write deliverable (c) environmental table"),

    ("code",
     "out = m[['name', 'npc_pathway', 'source', 'genus', 'certainty',\n"
     "         'field_detected', 'n_comm_present', 'prevalence', 'mean_relab', 'max_relab']].copy()\n"
     "out = out.sort_values(['name', 'prevalence'], ascending=[True, False]).reset_index(drop=True)\n"
     "out.to_csv(DATA / 'environmental_atlas.tsv', sep='\\t', index=False)\n"
     "print('wrote data/environmental_atlas.tsv', out.shape)\n"
     "\n"
     "print('\\n=== deliverable (c) environmental headline ===')\n"
     "print(f'SSO communities surveyed: {N_TOT} | implicated genera: {m[\"genus\"].nunique()} | '\n"
     "      f'detected in SSO field: {m[m[\"field_detected\"]][\"genus\"].nunique()}')\n"
     "print(f'compounds with >=1 field-present utilizer genus: '\n"
     "      f'{pc[pc[\"n_field\"] > 0][\"name\"].nunique()} / {pc[\"name\"].nunique()}')\n"
     "\n"
     "print('\\n=== H3 verdict ===')\n"
     "print('UNTESTABLE / CONFOUNDED: of 8 callable compounds only 2 are necromass '\n"
     "      '(terephthalic + phthalic acid), both phthalate-class aromatics with '\n"
     "      'Actinomycetota-heavy utilizers. Source is confounded with chemical class and '\n"
     "      'the necromass arm is n=2; no source-contrast statistic is reported. '\n"
     "      'Reported instead: honest SSO field-occurrence of predicted utilizer genera.')"),
]

build_and_run("07_environmental_atlas.ipynb", cells)
