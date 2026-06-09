from _build import build_and_run

cells = [
    ("md", "# NB01 — Compound Identity Resolution (PubChem)\n\n"
           "Resolve each of the 83 compounds to a structural identifier (CID, InChIKey, "
           "SMILES, formula) plus KEGG/ChEBI cross-references — the bridge from the "
           "name-only source sheet to the structure- and pathway-keyed databases used "
           "downstream (NB02).\n\n"
           "**Two resolution channels:**\n"
           "- **21 compounds already carry an InChIKey as their `compound_id`** "
           "(e.g. `CECREIRZLPLYDM-...` = Manool) → resolve by structure (most reliable).\n"
           "- **62 carry `Cc1_xx` ids and only a name** → resolve `name → CID`, trying "
           "whitespace-stripped and slash-split alternates.\n\n"
           "All PubChem responses are disk-cached (`data/pubchem_cache.json`) so reruns "
           "are free and the notebook is reproducible offline once populated."),

    ("code",
     "import pandas as pd\n"
     "import requests\n"
     "import re, json, time\n"
     "from pathlib import Path\n"
     "\n"
     "DATA = Path('../data'); FIG = Path('../figures')\n"
     "pd.set_option('display.max_columns', 40); pd.set_option('display.width', 200)\n"
     "\n"
     "comp = pd.read_csv(DATA / 'compounds_selected.tsv', sep='\\t')\n"
     "print('compounds:', len(comp))\n"
     "INCHIKEY_RE = re.compile(r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$')\n"
     "comp['id_is_inchikey'] = comp['compound_id'].str.match(INCHIKEY_RE)\n"
     "print('ids that are already InChIKeys:', int(comp['id_is_inchikey'].sum()))\n"
     "print('ids that are Cc1_xx (name-only):', int((~comp['id_is_inchikey']).sum()))"),

    ("md", "## PubChem PUG-REST helpers (cached)\n"
           "Rate-limited to <5 req/s (PubChem policy). Every URL response is memoized to "
           "`data/pubchem_cache.json`."),

    ("code",
     "B = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'\n"
     "CACHE_PATH = DATA / 'pubchem_cache.json'\n"
     "_cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}\n"
     "_sess = requests.Session()\n"
     "\n"
     "def _get(url):\n"
     "    if url in _cache:\n"
     "        return _cache[url]\n"
     "    time.sleep(0.22)  # stay under 5 req/s\n"
     "    try:\n"
     "        r = _sess.get(url, timeout=30)\n"
     "        out = {'status': r.status_code,\n"
     "               'json': r.json() if r.status_code == 200 else None}\n"
     "    except Exception as e:\n"
     "        out = {'status': -1, 'json': None, 'error': str(e)}\n"
     "    _cache[url] = out\n"
     "    return out\n"
     "\n"
     "def _save_cache():\n"
     "    CACHE_PATH.write_text(json.dumps(_cache))\n"
     "\n"
     "PROPS = 'IUPACName,MolecularFormula,InChIKey,SMILES'\n"
     "\n"
     "def props_by_inchikey(ik):\n"
     "    r = _get(f'{B}/compound/inchikey/{ik}/property/{PROPS}/JSON')\n"
     "    if r['status'] == 200:\n"
     "        return r['json']['PropertyTable']['Properties'][0]\n"
     "    return None\n"
     "\n"
     "def cid_by_name(name):\n"
     "    from urllib.parse import quote\n"
     "    r = _get(f'{B}/compound/name/{quote(name)}/cids/JSON')\n"
     "    if r['status'] == 200:\n"
     "        cids = r['json'].get('IdentifierList', {}).get('CID', [])\n"
     "        return cids[0] if cids else None\n"
     "    return None\n"
     "\n"
     "def props_by_cid(cid):\n"
     "    r = _get(f'{B}/compound/cid/{cid}/property/{PROPS}/JSON')\n"
     "    if r['status'] == 200:\n"
     "        return r['json']['PropertyTable']['Properties'][0]\n"
     "    return None\n"
     "\n"
     "KEGG_RE = re.compile(r'^[CD]\\d{5}$')\n"
     "def xrefs_by_cid(cid):\n"
     "    '''Scrape KEGG (C/D-number) and ChEBI ids from the synonym list.'''\n"
     "    r = _get(f'{B}/compound/cid/{cid}/synonyms/JSON')\n"
     "    if r['status'] != 200:\n"
     "        return None, None\n"
     "    syn = r['json']['InformationList']['Information'][0].get('Synonym', [])\n"
     "    kegg = next((s for s in syn if KEGG_RE.match(s)), None)\n"
     "    chebi = next((s for s in syn if s.upper().startswith('CHEBI:')), None)\n"
     "    return kegg, chebi\n"
     "print('helpers ready; cache entries:', len(_cache))"),

    ("md", "## Build name candidates for the 62 name-only compounds\n"
           "Strip whitespace; split slash-delimited synonyms (`Mellein / Ochracin`, "
           "`Decanedioic acid/Sebacic acid`) into alternates tried in order. Underscore-"
           "mangled names (`1_prop_2_en_1_yl__...`) are tried as-is and flagged if they fail."),

    ("code",
     "STEREO_RE = re.compile(r'^(\\([^)]*\\)-?|[DL]-|rac-)+', re.IGNORECASE)\n"
     "def name_candidates(name):\n"
     "    name = str(name).strip()\n"
     "    cands = []\n"
     "    parts = [p.strip() for p in name.split('/') if p.strip()] if '/' in name else [name]\n"
     "    for p in parts:\n"
     "        if p not in cands:\n"
     "            cands.append(p)\n"
     "    # fallback: strip leading stereo/racemic descriptors, e.g. (±)-, (S)-(-)-, D-\n"
     "    for p in list(cands):\n"
     "        bare = STEREO_RE.sub('', p).strip()\n"
     "        if bare and bare not in cands:\n"
     "            cands.append(bare)\n"
     "    return cands\n"
     "\n"
     "# preview the messy ones\n"
     "for nm in ['Mellein / Ochracin', 'Decanedioic acid/Sebacic acid',\n"
     "           '1_prop_2_en_1_yl__1H_indole_3_carboxylic_acid', '2-Hydroxychalcone ']:\n"
     "    print(repr(nm), '->', name_candidates(nm))"),

    ("md", "## Resolve all 83 compounds"),

    ("code",
     "rows = []\n"
     "for _, r in comp.iterrows():\n"
     "    cid = ik = formula = smiles = iupac = kegg = chebi = None\n"
     "    via = 'failed'\n"
     "    if r['id_is_inchikey']:\n"
     "        ik0 = r['compound_id']\n"
     "        p = props_by_inchikey(ik0)\n"
     "        if p:\n"
     "            via = 'inchikey'\n"
     "            cid = p.get('CID'); ik = p.get('InChIKey', ik0)\n"
     "            formula = p.get('MolecularFormula'); smiles = p.get('SMILES')\n"
     "            iupac = p.get('IUPACName')\n"
     "        else:\n"
     "            ik = ik0  # keep the structural id even if PubChem lookup failed\n"
     "            via = 'inchikey_only'\n"
     "    else:\n"
     "        for cand in name_candidates(r['name']):\n"
     "            c = cid_by_name(cand)\n"
     "            if c:\n"
     "                p = props_by_cid(c)\n"
     "                if p:\n"
     "                    via = 'name'; cid = c\n"
     "                    ik = p.get('InChIKey'); formula = p.get('MolecularFormula')\n"
     "                    smiles = p.get('SMILES'); iupac = p.get('IUPACName')\n"
     "                    break\n"
     "    if cid is not None:\n"
     "        kegg, chebi = xrefs_by_cid(cid)\n"
     "    rows.append(dict(compound_id=r['compound_id'], name=r['name'],\n"
     "                     npc_pathway=r['npc_pathway'], resolved_via=via,\n"
     "                     cid=cid, inchikey=ik, molecular_formula=formula,\n"
     "                     smiles=smiles, iupac_name=iupac, kegg_id=kegg, chebi_id=chebi))\n"
     "_save_cache()\n"
     "res = pd.DataFrame(rows)\n"
     "print('cache entries after run:', len(_cache))\n"
     "print(res['resolved_via'].value_counts().to_string())"),

    ("md", "## Coverage report"),

    ("code",
     "res['has_structure'] = res['inchikey'].notna()\n"
     "res['has_kegg'] = res['kegg_id'].notna()\n"
     "res['has_chebi'] = res['chebi_id'].notna()\n"
     "n = len(res)\n"
     "print(f'structure (InChIKey): {res[\"has_structure\"].sum():2d}/{n}')\n"
     "print(f'SMILES              : {res[\"smiles\"].notna().sum():2d}/{n}')\n"
     "print(f'KEGG id             : {res[\"has_kegg\"].sum():2d}/{n}')\n"
     "print(f'ChEBI id            : {res[\"has_chebi\"].sum():2d}/{n}')\n"
     "print()\n"
     "cov = res.groupby('npc_pathway').agg(\n"
     "    n=('compound_id', 'size'),\n"
     "    structure=('has_structure', 'sum'),\n"
     "    kegg=('has_kegg', 'sum'),\n"
     "    chebi=('has_chebi', 'sum')).sort_values('n', ascending=False)\n"
     "print(cov.to_string())"),

    ("code",
     "# show any unresolved (no structure) compounds — these need manual curation\n"
     "missing = res[~res['has_structure']][['compound_id', 'name', 'npc_pathway', 'resolved_via']]\n"
     "print('UNRESOLVED (no structure):', len(missing))\n"
     "print(missing.to_string(index=False))"),

    ("md", "## Save resolved table for NB02"),

    ("code",
     "out_cols = ['compound_id', 'name', 'npc_pathway', 'resolved_via', 'cid',\n"
     "            'inchikey', 'molecular_formula', 'smiles', 'iupac_name',\n"
     "            'kegg_id', 'chebi_id']\n"
     "res[out_cols].to_csv(DATA / 'resolved_compounds.tsv', sep='\\t', index=False)\n"
     "print('wrote data/resolved_compounds.tsv', res.shape)\n"
     "res[out_cols].head(12)"),
]

build_and_run("01_identity_resolution.ipynb", cells)
