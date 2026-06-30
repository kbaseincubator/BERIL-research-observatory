import pandas as pd
from pathlib import Path
import json
import logging

log = logging.getLogger(__name__)

def load_labeled_pd(data_dir: Path) -> pd.DataFrame:
    """Load labeled_pd.parquet with consistent index name 'protein_id'."""
    df = pd.read_parquet(data_dir / 'labeled_pd.parquet')
    if df.index.name != 'protein_id':
        if 'protein_id' in df.columns:
            df = df.set_index('protein_id')
        elif 'id' in df.columns:
            df = df.set_index('id')
            df.index.name = 'protein_id'
        else:
            df.index.name = 'protein_id'
    # Drop leftover 'id' column if present
    if 'id' in df.columns:
        del df['id']
    return df

def load_active_stressors(data_dir: Path) -> list:
    with open(data_dir / 'active_stressors.json', 'r') as f:
        return json.load(f)

def load_best_combination(data_dir: Path) -> list:
    with open(data_dir / 'best_feature_combination.json', 'r') as f:
        return json.load(f)['combination'].split('+')

def load_features(feature_names, data_dir, drop_organism=True):
    """
    Load one or more feature sets from cached parquet files,
    concatenate them, and return a single DataFrame.
    """
    dfs = []
    for name in feature_names:
        path = data_dir / f"features_{name}.parquet"
        df = pd.read_parquet(path)
        if drop_organism:
            df = df.drop(columns=['organism'], errors='ignore')
        dfs.append(df)
    return pd.concat(dfs, axis=1)