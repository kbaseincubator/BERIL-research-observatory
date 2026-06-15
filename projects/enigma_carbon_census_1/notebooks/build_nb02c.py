from _build import build_and_run

cells = [
    ("md", "# NB02c — Tier-1 robustness: FB carbon-source match by InChIKey (review I1)\n\n"
           "ADVERSARIAL_REVIEW_1 (I1) flagged that NB02's Tier-1 channel matched compounds to "
           "Fitness Browser carbon-source experiments by **normalized name strings** "
           "(`condition_1` ↔ compound name). Name matching is fragile across acid/conjugate-base, "
           "salt/hydrate, and synonym variants — a measured RB-TnSeq carbon-source experiment "
           "could be missed, which would wrongly push a compound into the *organism-dark* set.\n\n"
           "This notebook re-does the Tier-1 match **structurally**: resolve every distinct FB "
           "carbon-source `condition_1` name to a PubChem InChIKey, then match on the 14-character "
           "InChIKey connectivity block against our 83 resolved compounds. This is stereo- and "
           "salt-insensitive and independent of naming.\n\n"
           "**Result (preview):** of 154 distinct FB carbon-source conditions, 134 resolve to a "
           "single-compound InChIKey (the other 20 are polymers/mixtures — arabinogalactan, "
           "casamino acids, herring-sperm DNA, etc. — which cannot match a single compound). The "
           "structural match recovers **exactly one** of our 83 compounds: **lauric acid**. This "
           "*confirms* the name-based match was not silently dropping aromatics or fatty acids — "
           "the FB carbon-source panel is overwhelmingly common metabolites with near-zero overlap "
           "with these NP secondary metabolites. The actionable consequence is downstream (NB08): "
           "lauric acid carries Tier-1 *measured* fitness yet was flagged `callable=False`; that "
           "is corrected there."),

    ("code",
     "import os, re, json, time\n"
     "import pandas as pd, requests\n"
     "from pathlib import Path\n"
     "DATA = Path('../data')\n"
     "pd.set_option('display.max_columns', 40); pd.set_option('display.width', 200)\n"
     "res = pd.read_csv(DATA / 'resolved_compounds.tsv', sep='\\t')\n"
     "res['ik14'] = res['inchikey'].str.slice(0, 14)\n"
     "ours14 = dict(zip(res['ik14'], res['name']))\n"
     "print('resolved compounds:', len(res))"),

    ("md", "## Pull distinct FB carbon-source conditions (Spark)\n"
           "Same source as NB02 channel T1: `kescience_fitnessbrowser.experiment`, "
           "`expGroup='carbon source'`. Cached to `data/fb_carbon_conditions.tsv`."),

    ("code",
     "from pyspark.sql import SparkSession, functions as F\n"
     "_tok = os.environ['KBASE_AUTH_TOKEN']\n"
     "spark = SparkSession.builder.remote(\n"
     "    f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={_tok}'\n"
     ").getOrCreate()\n"
     "fb = (spark.table('kescience_fitnessbrowser.experiment')\n"
     "      .filter(F.lower('expGroup') == 'carbon source')\n"
     "      .filter(F.col('condition_1').isNotNull())\n"
     "      .groupBy('condition_1').agg(\n"
     "          F.countDistinct('orgId').alias('n_orgs'),\n"
     "          F.concat_ws(',', F.collect_set('orgId')).alias('orgs'))\n"
     "      .toPandas())\n"
     "fb.to_csv(DATA / 'fb_carbon_conditions.tsv', sep='\\t', index=False)\n"
     "print('distinct FB carbon-source conditions:', len(fb))"),

    ("md", "## Resolve FB names → InChIKey (PubChem, cached)\n"
           "Light cleaning of salt/hydrate/stereo descriptors, then PubChem name→InChIKey with the "
           "raw name as fallback. Cached to `data/fb_pubchem_cache.json` so re-execution is offline."),

    ("code",
     "cache_path = DATA / 'fb_pubchem_cache.json'\n"
     "cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}\n"
     "SALT = ['disodium salt','monopotassium salt','dihydrochloride','hydrochloride','monohydrate',\n"
     "        'dihydrate','hexahydrate','pentahydrate','sodium salt','lithium salt','potassium salt',\n"
     "        'sodium','potassium','lithium',' salt',' hydrate',' dibasic',' basic']\n"
     "def clean(s):\n"
     "    s = re.sub(r'\\([^)]*\\)', '', str(s)); low = s.lower()\n"
     "    for w in SALT: low = low.replace(w, '')\n"
     "    return low.strip(' ,;-')\n"
     "def pubchem_ik(name):\n"
     "    if name in cache: return cache[name]\n"
     "    ik = None\n"
     "    for q in [name, clean(name)]:\n"
     "        if not q: continue\n"
     "        try:\n"
     "            u = ('https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'\n"
     "                 f'{requests.utils.quote(q)}/property/InChIKey/JSON')\n"
     "            r = requests.get(u, timeout=20)\n"
     "            if r.status_code == 200:\n"
     "                ik = r.json()['PropertyTable']['Properties'][0]['InChIKey']; break\n"
     "        except Exception: pass\n"
     "        time.sleep(0.2)\n"
     "    cache[name] = ik; return ik\n"
     "fb['ik'] = [pubchem_ik(n) for n in fb['condition_1']]\n"
     "cache_path.write_text(json.dumps(cache))\n"
     "fb['ik14'] = fb['ik'].str.slice(0, 14)\n"
     "print('FB names resolved to InChIKey: %d/%d' % (fb['ik'].notna().sum(), len(fb)))\n"
     "print('unresolved (polymers/mixtures):')\n"
     "print('  ' + ', '.join(sorted(fb[fb['ik'].isna()]['condition_1'])[:25]))"),

    ("md", "## Structural match: FB InChIKey-14 ↔ our 83 compounds"),

    ("code",
     "fb['match'] = fb['ik14'].map(lambda k: ours14.get(k) if pd.notna(k) else None)\n"
     "hits = fb[fb['match'].notna()].copy()\n"
     "hits.to_csv(DATA / 'fb_inchikey_matches.tsv', sep='\\t', index=False)\n"
     "print('Tier-1 compounds by structural (InChIKey) match:', hits['match'].nunique())\n"
     "print(hits[['condition_1', 'n_orgs', 'match']].to_string(index=False))\n"
     "\n"
     "# compare to the name-based Tier-1 set from NB02\n"
     "link = pd.read_csv(DATA / 'compound_linkage.tsv', sep='\\t')\n"
     "name_t1 = set(link[link['fb_carbon']]['name'])\n"
     "ik_t1 = set(hits['match'])\n"
     "print('\\nname-based Tier-1 set :', sorted(name_t1))\n"
     "print('InChIKey Tier-1 set    :', sorted(ik_t1))\n"
     "print('recovered ONLY by InChIKey (name-match missed):', sorted(ik_t1 - name_t1))\n"
     "print('in name set but not InChIKey:', sorted(name_t1 - ik_t1))"),

    ("md", "## Conclusion (I1)\n"
           "The structural match recovers the same single Tier-1 compound (**lauric acid**) as the "
           "name match — confirming no measured carbon-source experiments were lost to naming. The "
           "FB carbon-source panel (sugars, amino acids, organic acids, a handful of common fatty "
           "and aromatic acids) simply has minimal overlap with these natural-product secondary "
           "metabolites. The one real correction this exposes is semantic, not a missed match: "
           "lauric acid has Tier-1 *measured* growth-on-carbon yet was scored `callable=False` "
           "because the organism-mapping path (NB03/04) found only biosynthetic-direction "
           "signatures. NB08 is updated to treat **any Tier-1 measured carbon source as callable** "
           "(`callable_basis='measured_fitness'`), keeping the ENIGMA-isolate prediction column "
           "honest (the FB organism for lauric acid is a reference bacterium, not an ENIGMA "
           "isolate, so deliverable (a) is unchanged)."),
]

build_and_run("02c_fb_inchikey_rematch.ipynb", cells, timeout=1200)
