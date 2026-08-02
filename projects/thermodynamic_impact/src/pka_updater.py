"""Convert OPAM2 pKa predictions to ModelSEED TSV format and apply updates."""

import glob
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.MolStandardize import rdMolStandardize


def opam2_to_modelseed_format(acid_entries, base_entries):
    """Convert OPAM2 predictions to ModelSEED pKa/pkb string format.

    OPAM2 acid predictions return H atom indices; we map to the heavy-atom
    neighbor. Base predictions return heavy-atom indices directly.
    Both are converted to 1-based indexing and formatted as 'fragment:atom:value;...'.

    Args:
        acid_entries: list of (heavy_atom_0based, pka_value)
        base_entries: list of (heavy_atom_0based, pka_value)

    Returns:
        (pka_str, pkb_str) in ModelSEED format
    """
    pka_parts = [f"1:{idx + 1}:{val:.2f}" for idx, val in acid_entries]
    pkb_parts = [f"1:{idx + 1}:{val:.2f}" for idx, val in base_entries]
    return ";".join(pka_parts), ";".join(pkb_parts)


def update_compound_tsvs(predictions, msdb_dir):
    """Write OPAM2 predictions into ModelSEEDDatabase compound TSV files.

    Args:
        predictions: dict[cpd_id] -> {'pka': str, 'pkb': str}
        msdb_dir: path to ModelSEEDDatabase root

    Returns:
        dict with counts: updated, new, unchanged
    """
    msdb_path = Path(msdb_dir)
    cpd_files = sorted(glob.glob(str(msdb_path / "Biochemistry" / "compound_*.tsv")))
    cpd_files = [f for f in cpd_files if "provenance" not in f]

    counts = {"updated": 0, "new": 0, "unchanged": 0}

    for cpd_file in cpd_files:
        df = pd.read_csv(cpd_file, sep="\t")
        file_changed = False

        for idx, row in df.iterrows():
            cpd_id = row["id"]
            if cpd_id not in predictions:
                counts["unchanged"] += 1
                continue

            pred = predictions[cpd_id]
            old_pka = str(row.get("pka", "")) if pd.notna(row.get("pka", "")) else ""
            old_pkb = str(row.get("pkb", "")) if pd.notna(row.get("pkb", "")) else ""
            had_existing = bool(old_pka or old_pkb)

            if pred["pka"]:
                df.at[idx, "pka"] = pred["pka"]
            if pred["pkb"]:
                df.at[idx, "pkb"] = pred["pkb"]

            if had_existing:
                counts["updated"] += 1
            else:
                counts["new"] += 1
            file_changed = True

        if file_changed:
            df.to_csv(cpd_file, sep="\t", index=False)

    return counts
