#!/usr/bin/env python3
"""
Retrieve AlphaFold structures from the EBI AlphaFold Protein Structure Database.

Downloads PDB, mmCIF, and PAE (Predicted Aligned Error) files for given UniProt
accession(s). Validates downloaded files and outputs metadata as TSV rows
suitable for the `alphafold_structures` Delta Lake table.

Usage:
  python retrieve_alphafold.py --accession P0A6Y8
  python retrieve_alphafold.py --accession P0A6Y8 Q9Y6K9 --output-dir ./structures
  python retrieve_alphafold.py --accession-file accessions.txt --output-dir ./structures
  python retrieve_alphafold.py --accession P0A6Y8 --upload  # upload to MinIO

Output:
  For each accession, creates a directory with:
    {accession}/model.pdb
    {accession}/model.cif
    {accession}/pae.json
    {accession}/metadata.tsv   (one-row TSV for alphafold_structures table)
"""

import argparse
import json
import os
import sys
from datetime import date

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)

EBI_BASE_URL = "https://alphafold.ebi.ac.uk"
EBI_API_URL = f"{EBI_BASE_URL}/api"
MINIO_BASE = "s3a://cdm-lake/tenant-general-warehouse/kescience/structural-biology/alphafold-structures"

METADATA_HEADER = [
    "uniprot_accession",
    "pdb_path",
    "cif_path",
    "pae_path",
    "n_residues",
    "n_domains",
    "mean_plddt",
    "retrieval_date",
]


def fetch_alphafold_entry(accession, session=None):
    """Fetch AlphaFold entry metadata from the EBI API."""
    s = session or requests.Session()
    url = f"{EBI_API_URL}/prediction/{accession}"
    resp = s.get(url, timeout=30)
    if resp.status_code == 404:
        print(f"  WARNING: No AlphaFold entry found for {accession}")
        return None
    resp.raise_for_status()
    return resp.json()


def download_file(url, output_path, session=None):
    """Download a file from URL to output_path."""
    s = session or requests.Session()
    resp = s.get(url, timeout=120, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size = os.path.getsize(output_path)
    print(f"  Downloaded {output_path} ({size:,} bytes)")
    return size


def validate_pdb(pdb_path):
    """Validate PDB file: check for ATOM records and count residues."""
    residues = set()
    atom_count = 0
    plddt_sum = 0.0
    plddt_count = 0

    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM"):
                atom_count += 1
                chain = line[21]
                resnum = line[22:26].strip()
                residues.add((chain, resnum))
                # B-factor column contains pLDDT in AlphaFold models
                try:
                    plddt = float(line[60:66].strip())
                    plddt_sum += plddt
                    plddt_count += 1
                except (ValueError, IndexError):
                    pass

    n_residues = len(residues)
    mean_plddt = round(plddt_sum / plddt_count, 2) if plddt_count > 0 else 0.0

    if atom_count == 0:
        print(f"  WARNING: No ATOM records found in {pdb_path}")
        return 0, 0.0

    print(f"  PDB validation: {atom_count} atoms, {n_residues} residues, mean pLDDT={mean_plddt}")
    return n_residues, mean_plddt


def validate_cif(cif_path):
    """Basic validation: check file is non-empty and contains _atom_site."""
    size = os.path.getsize(cif_path)
    if size == 0:
        print(f"  WARNING: Empty mmCIF file: {cif_path}")
        return False
    has_atoms = False
    with open(cif_path) as f:
        for line in f:
            if "_atom_site." in line:
                has_atoms = True
                break
    if not has_atoms:
        print(f"  WARNING: No _atom_site records in {cif_path}")
    return has_atoms


def validate_pae(pae_path):
    """Validate PAE JSON: check it parses and has expected structure."""
    with open(pae_path) as f:
        data = json.load(f)
    # PAE JSON can be a list of dicts or a dict with predicted_aligned_error
    if isinstance(data, list) and len(data) > 0:
        entry = data[0]
        if "predicted_aligned_error" in entry:
            pae = entry["predicted_aligned_error"]
            n = len(pae)
            print(f"  PAE validation: {n}x{n} matrix")
            return True
    elif isinstance(data, dict) and "predicted_aligned_error" in data:
        pae = data["predicted_aligned_error"]
        n = len(pae)
        print(f"  PAE validation: {n}x{n} matrix")
        return True
    # Newer format with pae_interaction
    print(f"  PAE validation: parsed successfully (non-standard format)")
    return True


def retrieve_structure(accession, output_dir, session=None):
    """Retrieve all files for a single accession. Returns metadata dict or None."""
    print(f"Retrieving AlphaFold structure for {accession}...")
    s = session or requests.Session()

    # Fetch entry metadata from API
    entry = fetch_alphafold_entry(accession, session=s)
    if entry is None:
        return None

    # Handle API response (can be a list)
    if isinstance(entry, list):
        if len(entry) == 0:
            print(f"  WARNING: Empty response for {accession}")
            return None
        entry = entry[0]

    # Create output directory
    acc_dir = os.path.join(output_dir, accession)
    os.makedirs(acc_dir, exist_ok=True)

    # Extract download URLs from API response
    pdb_url = entry.get("pdbUrl")
    cif_url = entry.get("cifUrl")
    pae_url = entry.get("paeDocUrl") or entry.get("paeImageUrl")

    # Fallback to constructed URLs if API doesn't provide them
    if not pdb_url:
        pdb_url = f"{EBI_BASE_URL}/files/AF-{accession}-F1-model_v4.pdb"
    if not cif_url:
        cif_url = f"{EBI_BASE_URL}/files/AF-{accession}-F1-model_v4.cif"
    if not pae_url:
        pae_url = f"{EBI_BASE_URL}/files/AF-{accession}-F1-predicted_aligned_error_v4.json"

    pdb_path = os.path.join(acc_dir, "model.pdb")
    cif_path = os.path.join(acc_dir, "model.cif")
    pae_path = os.path.join(acc_dir, "pae.json")

    # Download files
    try:
        download_file(pdb_url, pdb_path, session=s)
    except Exception as e:
        print(f"  ERROR downloading PDB: {e}")
        return None

    try:
        download_file(cif_url, cif_path, session=s)
    except Exception as e:
        print(f"  WARNING: Could not download mmCIF: {e}")

    try:
        download_file(pae_url, pae_path, session=s)
    except Exception as e:
        print(f"  WARNING: Could not download PAE: {e}")

    # Validate
    n_residues, mean_plddt = validate_pdb(pdb_path)
    if os.path.exists(cif_path):
        validate_cif(cif_path)
    if os.path.exists(pae_path):
        try:
            validate_pae(pae_path)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARNING: PAE validation failed: {e}")

    # Build metadata row
    today = date.today().isoformat()
    metadata = {
        "uniprot_accession": accession,
        "pdb_path": f"{MINIO_BASE}/{accession}/model.pdb",
        "cif_path": f"{MINIO_BASE}/{accession}/model.cif",
        "pae_path": f"{MINIO_BASE}/{accession}/pae.json",
        "n_residues": n_residues,
        "n_domains": 0,  # Set after phenix.process_predicted_model
        "mean_plddt": mean_plddt,
        "retrieval_date": today,
    }

    # Write per-accession metadata TSV
    meta_path = os.path.join(acc_dir, "metadata.tsv")
    with open(meta_path, "w") as f:
        f.write("\t".join(METADATA_HEADER) + "\n")
        f.write("\t".join(str(metadata[h]) for h in METADATA_HEADER) + "\n")
    print(f"  Metadata written to {meta_path}")

    return metadata


def upload_to_minio(accession, local_dir):
    """Upload retrieved files to MinIO using mc CLI."""
    import subprocess

    minio_path = f"cdm-lake/tenant-general-warehouse/kescience/structural-biology/alphafold-structures/{accession}/"
    acc_dir = os.path.join(local_dir, accession)

    for filename in ["model.pdb", "model.cif", "pae.json"]:
        local_file = os.path.join(acc_dir, filename)
        if os.path.exists(local_file):
            cmd = ["mc", "cp", local_file, f"berdl/{minio_path}{filename}"]
            print(f"  Uploading {filename} to MinIO...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  WARNING: mc cp failed: {result.stderr.strip()}")
            else:
                print(f"  Uploaded {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve AlphaFold structures from EBI"
    )
    parser.add_argument(
        "--accession",
        nargs="+",
        help="UniProt accession(s) to retrieve",
    )
    parser.add_argument(
        "--accession-file",
        help="File with one UniProt accession per line",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Base output directory (default: current directory)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload retrieved files to MinIO after download",
    )
    parser.add_argument(
        "--metadata-tsv",
        help="Append all metadata rows to this combined TSV file",
    )
    args = parser.parse_args()

    # Collect accessions
    accessions = []
    if args.accession:
        accessions.extend(args.accession)
    if args.accession_file:
        with open(args.accession_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    accessions.append(line)
    if not accessions:
        parser.error("Provide --accession or --accession-file")

    os.makedirs(args.output_dir, exist_ok=True)

    # Process each accession
    session = requests.Session()
    results = []
    failed = []

    for acc in accessions:
        metadata = retrieve_structure(acc, args.output_dir, session=session)
        if metadata:
            results.append(metadata)
            if args.upload:
                upload_to_minio(acc, args.output_dir)
        else:
            failed.append(acc)
        print()

    # Write combined metadata TSV
    if args.metadata_tsv and results:
        write_header = not os.path.exists(args.metadata_tsv)
        with open(args.metadata_tsv, "a") as f:
            if write_header:
                f.write("\t".join(METADATA_HEADER) + "\n")
            for m in results:
                f.write("\t".join(str(m[h]) for h in METADATA_HEADER) + "\n")
        print(f"Metadata appended to {args.metadata_tsv}")

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Retrieved: {len(results)}/{len(accessions)}")
    if failed:
        print(f"  Failed:    {', '.join(failed)}")
    print(f"  Output:    {args.output_dir}")


if __name__ == "__main__":
    main()
