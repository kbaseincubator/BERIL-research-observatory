"""Supplement labeled_pd.parquet with fitness data from downloaded FitnessBrowser files.

For organisms missing from the BERDL Spark tables, the refocus project downloaded
raw FitnessBrowser data to data/fitness_browser/{org}/. This script reads those
wide-format fitness.txt files, identifies metal experiments, computes fitness_min
per gene per stressor, and merges into labeled_pd.parquet.

Run from the enigma_stress_phenotype_ml project directory:
    python3 scripts/add_fitness_from_files.py
"""

import logging, re
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

PROJ_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJ_ROOT / 'data'
FB_DIR = PROJ_ROOT.parent / 'refocus' / 'data' / 'fitness_browser'

STRESSOR_PATTERNS = {
    'Zn':  ['zinc', 'zncl2', 'znso4', 'zinc chloride', 'zinc sulfate', 'zinc pyrithione'],
    'Cu':  ['copper', 'cuso4', 'cucl2', 'copper sulfate', 'copper chloride', 'copper nitrate'],
    'Cd':  ['cadmium', 'cdcl2', 'cdso4', 'cadmium chloride', 'cadmium nitrate'],
    'Co':  ['cobalt', 'cocl2', 'coso4', 'cobalt chloride'],
    'Ni':  ['nickel', 'nicl2', 'niso4', 'nickel chloride', 'nickel sulfate'],
    'Cr':  ['chromium', 'chromate', 'k2cro4', 'dichromate', 'potassium chromate', 'chromic'],
    'As':  ['arsenate', 'arsenite', 'sodium arsenite', 'sodium arsenate', 'nah2aso4', 'arsenic'],
    'Hg':  ['mercury', 'hgcl2', 'mercury chloride', 'mercuric chloride'],
    'Pb':  ['lead', 'pbno3', 'lead nitrate', 'pbcl2', 'lead chloride'],
    'Mn':  ['manganese', 'mncl2', 'mnso4', 'manganese chloride', 'manganese sulfate'],
    'Fe':  ['iron', 'feso4', 'fecl3', 'iron limitation', 'iron depletion', 'dipyridyl', 'bipyridyl', 'iron sulfate'],
    'Se':  ['selenium', 'selenite', 'selenate', 'sodium selenite', 'sodium selenate'],
    'Ag':  ['silver', 'agno3', 'silver nitrate', 'silver chloride'],
    'Al':  ['aluminium', 'aluminum', 'alcl3', 'aluminum chloride', 'aluminium chloride'],
}


def classify_exp(desc):
    """Return stressor name for an experiment description, or None."""
    desc_lower = str(desc).lower()
    for stressor, patterns in STRESSOR_PATTERNS.items():
        if any(p in desc_lower for p in patterns):
            return stressor
    return None


def load_org_fitness(org):
    """Load and pivot fitness data for one organism from downloaded files.

    Returns DataFrame with locusId index and {stressor}_fit columns,
    or None if no metal experiments found.
    """
    fit_file = FB_DIR / org / f'{org}_fitness.txt'
    exp_file = FB_DIR / org / f'{org}_experiments.txt'

    if not fit_file.exists() or not exp_file.exists():
        log.debug(f"{org}: missing fitness or experiment file")
        return None

    exp_df = pd.read_csv(exp_file, sep='\t')
    # Classify each experiment by metal stressor
    exp_df['stressor'] = exp_df['expDesc'].apply(classify_exp)
    metal_exps = exp_df[exp_df['stressor'].notna()][['expName', 'stressor']]
    if len(metal_exps) == 0:
        return None

    # Read fitness file (wide format: rows=genes, cols=experiments)
    fit_df = pd.read_csv(fit_file, sep='\t')
    gene_cols = ['orgId', 'locusId', 'sysName', 'geneName', 'desc']
    exp_cols = [c for c in fit_df.columns if c not in gene_cols]

    # Build name→stressor mapping from column headers
    # Column headers in fitness.txt are "{expName} {expDesc}" concatenated
    col_stressor = {}
    for col in exp_cols:
        for _, row in metal_exps.iterrows():
            if row['expName'] in col:
                col_stressor[col] = row['stressor']
                break

    if not col_stressor:
        return None

    result = {'locusId': fit_df['locusId']}
    for stressor in STRESSOR_PATTERNS:
        s_cols = [c for c, s in col_stressor.items() if s == stressor]
        if not s_cols:
            continue
        fit_col = f"{stressor}_fit"
        # Min across all experiments for that stressor (most negative = most essential)
        result[fit_col] = fit_df[s_cols].min(axis=1).values

    result_df = pd.DataFrame(result).set_index('locusId')
    # Drop columns that are all NaN
    result_df = result_df.dropna(how='all', axis=1)
    return result_df


# Organisms to supplement (missing from Spark but have downloaded files)
SUPPLEMENT_ORGS = [
    'Bifido', 'Brev2', 'Burkholderia_OAS925', 'Bvulgatus_CL09T03C04', 'CL21',
    'Lysobacter_OAE881', 'Mucilaginibacter_YX36', 'MycoTube', 'RPal_CGA009',
    'Variovorax_OAS795', 'Xantho', 'rhodanobacter_10B01', 'rhodanobacter_R12', 'rhodanobacter_T8'
]

labeled_pd = pd.read_parquet(DATA_DIR / 'labeled_pd.parquet')
fit_cols = [c for c in labeled_pd.columns if c.endswith('_fit')]

rows_updated = 0
for org in SUPPLEMENT_ORGS:
    org_fit = load_org_fitness(org)
    if org_fit is None or len(org_fit.columns) == 0:
        log.info(f"{org}: no metal fitness data in downloaded files")
        continue

    log.info(f"{org}: {len(org_fit.columns)} metal fitness columns from {len(org_fit)} genes")

    # Build composite protein_id keys for this organism
    # labeled_pd index is "{organism}|{locusId}"
    for col in org_fit.columns:
        if col not in labeled_pd.columns:
            labeled_pd[col] = np.nan

    for locusId, row in org_fit.iterrows():
        protein_id = f"{org}|{locusId}"
        if protein_id not in labeled_pd.index:
            continue
        for col, val in row.items():
            if not pd.isna(val):
                labeled_pd.at[protein_id, col] = val
                rows_updated += 1

log.info(f"Updated {rows_updated} protein×stressor values from downloaded files")

# Sanity check
log.info("Sanity check after supplementation:")
for metal in ['Zn', 'Cu', 'Co', 'Ni', 'Al', 'As', 'Pb', 'Ag']:
    fit_col = f"{metal}_fit"
    if fit_col in labeled_pd.columns:
        n = labeled_pd[fit_col].notna().sum()
        n_pos = (labeled_pd[fit_col] < -2).sum()
        log.info(f"  {metal}_fit: {n} proteins with data, {n_pos} below -2")

labeled_pd.to_parquet(DATA_DIR / 'labeled_pd.parquet')
log.info(f"Saved updated labeled_pd.parquet: {labeled_pd.shape}")
