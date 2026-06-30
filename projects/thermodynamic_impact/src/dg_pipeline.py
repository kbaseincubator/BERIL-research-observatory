"""Batch deltaG prediction pipeline using dGPredictor with custom compound caches."""

import json
import gzip
from pathlib import Path


def rebuild_compound_cache(compounds_df, cpd_inchi_map, output_path, build_fn):
    """Rebuild dGPredictor compound cache from updated pKa values.

    Args:
        compounds_df: pandas DataFrame with columns id, pka, pkb, formula, charge, smiles
        cpd_inchi_map: dict[cpd_id -> inchi_string]
        output_path: path for the output .json.gz file
        build_fn: the build_compound_cache function from retrain_modelseed.py

    Returns:
        dict of Compound objects
    """
    compound_dict = build_fn(compounds_df, cpd_inchi_map)

    cache_list = [comp.to_json_dict() for comp in compound_dict.values()]
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(cache_list, f)

    return compound_dict


def compare_dg_results(old_results, new_results):
    """Compare two sets of dG predictions and return a list of dicts.

    Args:
        old_results: dict[rxn_id -> {dG_mean, dG_std, ...}]
        new_results: dict[rxn_id -> {dG_mean, dG_std, ...}]

    Returns:
        list of dicts with columns: rxn_id, old_dg, new_dg, diff, abs_diff, ...
    """
    common = set(old_results.keys()) & set(new_results.keys())
    rows = []
    for rxn_id in sorted(common):
        old = old_results[rxn_id]
        new = new_results[rxn_id]
        rows.append({
            "rxn_id": rxn_id,
            "old_dg": old["dG_mean"],
            "new_dg": new["dG_mean"],
            "diff": new["dG_mean"] - old["dG_mean"],
            "abs_diff": abs(new["dG_mean"] - old["dG_mean"]),
            "old_model_only": old.get("dG_model_only", None),
            "new_model_only": new.get("dG_model_only", None),
            "old_pH_correction": old.get("ddG0_pH_correction", None),
            "new_pH_correction": new.get("ddG0_pH_correction", None),
        })
    return rows
