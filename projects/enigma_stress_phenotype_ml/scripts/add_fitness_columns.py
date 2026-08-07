"""Add continuous {stressor}_fit columns to labeled_pd.parquet.

Queries FitnessBrowser fitness scores and maps via KEGG to ENIGMA protein_ids,
then merges into the existing labeled_pd.parquet. Skips the expensive sequence
re-extraction step so this runs in ~5 min instead of the full NB01 ~45 min.

Run from the project root:
    python3 projects/enigma_stress_phenotype_ml/scripts/add_fitness_columns.py
"""

import sys, json, logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

# ── Spark setup (portable: works both in JupyterHub and standalone) ───────────
try:
    spark
except NameError:
    sys.path.append('/opt/conda/lib/python3.13/site-packages')
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()

from pyspark.sql import functions as F

PROJ_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJ_ROOT / 'data'

FITNESS_THRESHOLD = -2.0

STRESSOR_PATTERNS = {
    'Zn':    ['zinc', 'zncl2', 'znso4', 'zinc chloride', 'zinc sulfate'],
    'Cu':    ['copper', 'cuso4', 'cucl2', 'copper sulfate', 'copper chloride'],
    'Cd':    ['cadmium', 'cdcl2', 'cdso4', 'cadmium chloride'],
    'Co':    ['cobalt', 'cocl2', 'coso4', 'cobalt chloride'],
    'Ni':    ['nickel', 'nicl2', 'niso4', 'nickel chloride', 'nickel sulfate'],
    'Cr':    ['chromium', 'chromate', 'k2cro4', 'dichromate', 'potassium chromate'],
    'As':    ['arsenate', 'arsenite', 'sodium arsenite', 'sodium arsenate', 'nah2aso4'],
    'Hg':    ['mercury', 'hgcl2', 'mercury chloride', 'mercuric chloride'],
    'Pb':    ['lead', 'pbno3', 'lead nitrate', 'pbcl2'],
    'Mn':    ['manganese', 'mncl2', 'mnso4', 'manganese chloride'],
    'Fe':    ['iron', 'feso4', 'fecl3', 'iron limitation', 'iron depletion', 'dipyridyl', 'bipyridyl'],
    'Se':    ['selenium', 'selenite', 'selenate', 'sodium selenite'],
    'Ag':    ['silver', 'agno3', 'silver nitrate'],
    'Al':    ['aluminium', 'aluminum', 'alcl3', 'aluminum chloride'],
    'Ampicillin':    ['ampicillin'],
    'Kanamycin':     ['kanamycin'],
    'Gentamicin':    ['gentamicin'],
    'Rifampicin':    ['rifampicin', 'rifampin'],
    'Chloramphenicol': ['chloramphenicol'],
    'Tetracycline':  ['tetracycline'],
    'Phosphomycin':  ['phosphomycin', 'fosfomycin'],
    'Ceftazidime':   ['ceftazidime'],
    'Polymyxin':     ['polymyxin', 'colistin'],
    'Ramoplanin':    ['ramoplanin'],
    'Vancomycin':    ['vancomycin'],
    'Erythromycin':  ['erythromycin'],
    'Ciprofloxacin': ['ciprofloxacin', 'cipro'],
    'Spectinomycin': ['spectinomycin'],
    'Streptomycin':  ['streptomycin'],
    'Carbenicillin': ['carbenicillin'],
    'Penicillin':    ['penicillin'],
    'Trimethoprim':  ['trimethoprim'],
    'Bacitracin':    ['bacitracin'],
    'Linezolid':     ['linezolid'],
    'H2O2':          ['hydrogen peroxide', 'h2o2', 'peroxide'],
    'Paraquat':      ['paraquat', 'methyl viologen'],
    'Nitric oxide':  ['nitric oxide', 'no', 'spermine noate', 'deta no'],
    'Acid':          ['acid', 'acidic', 'low ph', 'ph 4', 'ph 4.5', 'ph 5', 'hcl'],
    'NaCl':          ['sodium chloride', 'nacl', 'salt', 'salinity'],
    'Sucrose':       ['sucrose', 'osmotic'],
    'Heat':          ['heat', 'high temperature', '42c', '45c', '37c'],
    'Cold':          ['cold', 'low temperature', '4c', '10c', '15c', '16c'],
    'EDTA':          ['edta', 'ethylenediaminetetraacetic acid'],
    'Ethanol':       ['ethanol', 'etoh'],
    'Bile salts':    ['bile', 'bile salts', 'cholate', 'deoxycholate'],
    'Nitrogen limitation': ['nitrogen limit', 'n limitation', 'low nitrogen', 'ammonium limit'],
    'Iron limitation':     ['iron limit', 'fe limitation', 'low iron', 'dipyridyl'],
    'UV':            ['uv', 'ultraviolet', 'uv irradiation'],
    'Anaerobic':     ['anaerobic', 'anoxic', 'low oxygen', 'nitrogen atmosphere'],
    'Biofilm':       ['biofilm'],
}

# Only extract for stressors that are in the existing labeled_pd
with open(DATA_DIR / 'active_stressors.json') as f:
    active_stressors = json.load(f)
STRESSOR_PATTERNS = {k: v for k, v in STRESSOR_PATTERNS.items() if k in active_stressors}
log.info(f"Extracting fitness columns for {len(STRESSOR_PATTERNS)} active stressors")

# ── Step 1: Extract fitness_min per locusId/orgId per stressor ────────────────
log.info("Querying FitnessBrowser fitness scores...")
exp = spark.table("kescience_fitnessbrowser.experiment")
gf  = spark.table("kescience_fitnessbrowser.genefitness")

fit_labels = None
for stressor, patterns in STRESSOR_PATTERNS.items():
    pattern = r'(?i)' + '|'.join(patterns)
    stressor_exps = exp.filter(F.col("expDesc").rlike(pattern)).select("expName")
    if stressor_exps.count() == 0:
        log.warning(f"  {stressor}: no experiments found, skipping")
        continue
    gene_fit = (gf.join(stressor_exps, "expName")
                  .withColumn("fit_num", F.col("fit").cast("float"))
                  .groupBy("locusId", "orgId")
                  .agg(F.min("fit_num").alias(f"{stressor}_fit")))
    if fit_labels is None:
        fit_labels = gene_fit
    else:
        fit_labels = fit_labels.join(gene_fit, ["locusId", "orgId"], "outer")
    log.info(f"  {stressor}: done")

if fit_labels is None:
    raise RuntimeError("No fitness data extracted.")

fit_cols = [c for c in fit_labels.columns if c not in ("locusId", "orgId")]
log.info(f"Extracted {len(fit_cols)} fitness columns for {fit_labels.count()} gene-organism pairs")

# ── Step 2: Construct composite protein_id key (orgId|locusId) ───────────────
# labeled_pd uses "{orgId}|{locusId}" as its protein_id index. FitnessBrowser
# uses exactly the same orgId and locusId values, so we join directly without
# going through the KEGG chain.
log.info("Constructing composite protein_id key from orgId|locusId...")
prot_fit = fit_labels.withColumn(
    "protein_id", F.concat(F.col("orgId"), F.lit("|"), F.col("locusId"))
).select("protein_id", *fit_cols)

log.info(f"Built {prot_fit.count()} protein-level fitness rows")

# ── Step 3: Collect and merge into existing labeled_pd.parquet ────────────────
log.info("Collecting to pandas and merging...")
fit_pd = prot_fit.toPandas().set_index("protein_id")

labeled_pd = pd.read_parquet(DATA_DIR / 'labeled_pd.parquet')

# Drop any existing _fit columns (idempotent re-run)
existing_fit = [c for c in labeled_pd.columns if c.endswith("_fit")]
if existing_fit:
    labeled_pd = labeled_pd.drop(columns=existing_fit)
    log.info(f"Dropped {len(existing_fit)} existing _fit columns for fresh merge")

# Left join: proteins in labeled_pd get fitness if mapped, NaN if not
labeled_pd = labeled_pd.join(fit_pd, how="left")

n_fit_cols = sum(1 for c in labeled_pd.columns if c.endswith("_fit"))
n_with_data = labeled_pd[[c for c in labeled_pd.columns if c.endswith("_fit")]].notna().any(axis=1).sum()
log.info(f"Merged: {n_fit_cols} fitness columns added; "
         f"{n_with_data}/{len(labeled_pd)} proteins have at least one fitness value")

labeled_pd.to_parquet(DATA_DIR / 'labeled_pd.parquet')
log.info(f"Saved labeled_pd.parquet: {labeled_pd.shape[0]} proteins × {labeled_pd.shape[1]} columns")

# Quick sanity check
for metal in ['Zn', 'Cu', 'Co']:
    fit_col = f"{metal}_fit"
    if fit_col in labeled_pd.columns:
        n_tested = labeled_pd[fit_col].notna().sum()
        n_pos = (labeled_pd[fit_col] < FITNESS_THRESHOLD).sum()
        log.info(f"  {metal}_fit: {n_tested} proteins tested, {n_pos} below threshold ({n_pos/n_tested:.2%})")
