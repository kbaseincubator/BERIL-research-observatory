from _build import build_and_run

cells = [
    ("md", "# NB00 — Compound Profile (ENIGMA Carbon Census 1)\n\n"
           "Load the source spreadsheet, isolate the **83 selected** compounds, and profile "
           "their chemical-class composition, source (groundwater vs necromass), and "
           "physicochemical properties (MW, LogP). Outputs a clean compounds table for "
           "downstream identity resolution (NB01) and figures for the report."),

    ("code",
     "import pandas as pd\n"
     "import numpy as np\n"
     "import matplotlib\n"
     "matplotlib.use('Agg')\n"
     "import matplotlib.pyplot as plt\n"
     "from pathlib import Path\n"
     "\n"
     "DATA = Path('../data'); FIG = Path('../figures')\n"
     "DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)\n"
     "pd.set_option('display.max_columns', 30)\n"
     "pd.set_option('display.width', 160)"),

    ("code",
     "raw = pd.read_excel('../user_data/Carbon_Census_Compound_Selections.xlsx')\n"
     "print('raw shape:', raw.shape)\n"
     "print('columns:', list(raw.columns))"),

    ("md", "## Select the 83 compounds\n"
           "`Include?` ∈ {Yes, Yes expensive}. The 9 NaN rows are excluded candidates."),

    ("code",
     "SEL = {'Yes', 'Yes, expensive'}\n"
     "df = raw[raw['Include?'].isin(SEL)].copy().reset_index(drop=True)\n"
     "assert len(df) == 83, f'expected 83 selected, got {len(df)}'\n"
     "df['expensive'] = df['Include?'].eq('Yes, expensive')\n"
     "df['source_short'] = df['Source'].map({\n"
     "    'Carbon Census SSO Groundwater': 'groundwater',\n"
     "    'Necromass': 'necromass'})\n"
     "print('selected:', len(df))\n"
     "print(df['source_short'].value_counts())\n"
     "print('expensive:', int(df['expensive'].sum()))"),

    ("md", "## Chemical-class composition (NP Classifier ontology)"),

    ("code",
     "for col in ['NPC Pathway', 'NPC Superclass', 'NPC Class']:\n"
     "    print(f'\\n=== {col} ===')\n"
     "    print(df[col].value_counts(dropna=False).to_string())"),

    ("code",
     "# class x source crosstab (NPC Pathway)\n"
     "ct = pd.crosstab(df['NPC Pathway'].fillna('(none)'), df['source_short'])\n"
     "ct['total'] = ct.sum(axis=1)\n"
     "ct = ct.sort_values('total', ascending=False)\n"
     "print(ct.to_string())"),

    ("md", "## Physicochemical properties"),

    ("code",
     "for col in ['MW (g/mol)', 'LogP', 'H2O Sol. (mM)']:\n"
     "    s = pd.to_numeric(df[col], errors='coerce')\n"
     "    print(f'{col:16s} n={s.notna().sum():3d}  min={s.min():.2f}  '\n"
     "          f'med={s.median():.2f}  max={s.max():.2f}')"),

    ("md", "## Figures"),

    ("code",
     "# Fig 1: NPC Pathway composition, stacked by source\n"
     "ctp = pd.crosstab(df['NPC Pathway'].fillna('(none)'), df['source_short'])\n"
     "ctp = ctp.loc[ctp.sum(axis=1).sort_values(ascending=False).index]\n"
     "fig, ax = plt.subplots(figsize=(8, 4.5))\n"
     "ctp.plot(kind='barh', stacked=True, ax=ax,\n"
     "         color={'groundwater': '#3b7dd8', 'necromass': '#d98c3b'})\n"
     "ax.set_xlabel('compounds'); ax.set_ylabel('NPC Pathway')\n"
     "ax.set_title('Carbon Census: chemical-class composition by source (n=83)')\n"
     "ax.invert_yaxis(); ax.legend(title='source')\n"
     "fig.tight_layout(); fig.savefig(FIG / '00_class_composition.png', dpi=150)\n"
     "print('saved 00_class_composition.png'); plt.close(fig)"),

    ("code",
     "# Fig 2: MW vs LogP, colored by source, sized by class\n"
     "mw = pd.to_numeric(df['MW (g/mol)'], errors='coerce')\n"
     "logp = pd.to_numeric(df['LogP'], errors='coerce')\n"
     "fig, ax = plt.subplots(figsize=(7, 5))\n"
     "for src, c in [('groundwater', '#3b7dd8'), ('necromass', '#d98c3b')]:\n"
     "    m = df['source_short'].eq(src)\n"
     "    ax.scatter(mw[m], logp[m], c=c, label=src, alpha=0.75, edgecolor='k', linewidth=0.3)\n"
     "ax.set_xlabel('MW (g/mol)'); ax.set_ylabel('LogP')\n"
     "ax.set_title('Physicochemical space of the 83 compounds')\n"
     "ax.axhline(0, color='grey', lw=0.5, ls='--'); ax.legend()\n"
     "fig.tight_layout(); fig.savefig(FIG / '00_mw_logp.png', dpi=150)\n"
     "print('saved 00_mw_logp.png'); plt.close(fig)"),

    ("md", "## Save clean compounds table for NB01"),

    ("code",
     "keep = ['Unique ID', 'Name', 'source_short', 'expensive',\n"
     "        'NPC Pathway', 'NPC Superclass', 'NPC Class', 'Orig. Class',\n"
     "        'MW (g/mol)', 'LogP', 'H2O Sol. (mM)']\n"
     "clean = df[keep].rename(columns={\n"
     "    'Unique ID': 'compound_id', 'Name': 'name',\n"
     "    'NPC Pathway': 'npc_pathway', 'NPC Superclass': 'npc_superclass',\n"
     "    'NPC Class': 'npc_class', 'Orig. Class': 'orig_class',\n"
     "    'MW (g/mol)': 'mw', 'H2O Sol. (mM)': 'h2o_sol_mM'})\n"
     "clean.to_csv(DATA / 'compounds_selected.tsv', sep='\\t', index=False)\n"
     "print('wrote data/compounds_selected.tsv', clean.shape)\n"
     "clean.head(10)"),
]

build_and_run("00_compound_profile.ipynb", cells)
