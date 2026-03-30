#!/usr/bin/env python3
"""
Batch validation of AlphaFold structures or local PDB files.

Validates multiple structures in one run, producing per-structure reports
and a combined summary TSV. No Phenix required for AlphaFold models (pLDDT
is extracted from B-factor column).

Usage:
  python batch_validate.py --accessions P0A6Y8 Q9Y6K9 --output-dir results/
  python batch_validate.py --accession-file accessions.txt --output-dir results/
  python batch_validate.py --pdb-dir models/ --output-dir results/
  python batch_validate.py --pdb-dir models/ --output-dir results/ --export-tsv
"""

import argparse
import csv
import glob
import json
import os
import sys
from datetime import date

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from retrieve_alphafold import validate_pdb, METADATA_HEADER


def validate_pdb_file(pdb_path):
    """Validate a single PDB file and return a report dict.

    For AlphaFold models, pLDDT is in the B-factor column.
    No Phenix required.
    """
    n_residues, mean_plddt = validate_pdb(pdb_path)

    # Compute pLDDT distribution from B-factor column
    plddt_bins = {"very_high": 0, "high": 0, "low": 0, "very_low": 0}
    atom_count = 0

    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                atom_count += 1
                try:
                    plddt = float(line[60:66].strip())
                    if plddt >= 90:
                        plddt_bins["very_high"] += 1
                    elif plddt >= 70:
                        plddt_bins["high"] += 1
                    elif plddt >= 50:
                        plddt_bins["low"] += 1
                    else:
                        plddt_bins["very_low"] += 1
                except (ValueError, IndexError):
                    pass

    # Convert to percentages
    if atom_count > 0:
        for key in plddt_bins:
            plddt_bins[key] = round(100.0 * plddt_bins[key] / atom_count, 1)

    report = {
        "model": pdb_path,
        "name": os.path.splitext(os.path.basename(pdb_path))[0],
        "n_residues": n_residues,
        "mean_plddt": mean_plddt,
        "plddt_distribution": plddt_bins,
        "validation_date": date.today().isoformat(),
    }

    # Quality assessment
    if mean_plddt >= 90:
        report["quality"] = "very_high"
    elif mean_plddt >= 70:
        report["quality"] = "high"
    elif mean_plddt >= 50:
        report["quality"] = "low"
    else:
        report["quality"] = "very_low"

    return report


def batch_validate_pdbs(pdb_paths, output_dir):
    """Validate a list of PDB files and produce reports.

    Returns list of report dicts.
    """
    os.makedirs(output_dir, exist_ok=True)
    reports = []

    for i, pdb_path in enumerate(pdb_paths, 1):
        name = os.path.splitext(os.path.basename(pdb_path))[0]
        print(f"[{i}/{len(pdb_paths)}] Validating {name}...")

        try:
            report = validate_pdb_file(pdb_path)
            reports.append(report)

            # Write per-structure JSON report
            report_path = os.path.join(output_dir, f"{name}_report.json")
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            print(f"  ERROR: {e}")
            reports.append({
                "model": pdb_path,
                "name": name,
                "error": str(e),
            })

    return reports


def batch_validate_accessions(accessions, output_dir):
    """Retrieve AlphaFold structures and validate them.

    Returns list of report dicts.
    """
    try:
        import requests
    except ImportError:
        print("ERROR: 'requests' package required for accession retrieval")
        sys.exit(1)

    from retrieve_alphafold import retrieve_structure

    os.makedirs(output_dir, exist_ok=True)
    download_dir = os.path.join(output_dir, "structures")
    os.makedirs(download_dir, exist_ok=True)

    session = requests.Session()
    pdb_paths = []
    metadata_list = []

    for i, acc in enumerate(accessions, 1):
        print(f"[{i}/{len(accessions)}] Retrieving {acc}...")
        metadata = retrieve_structure(acc, download_dir, session=session)
        if metadata:
            pdb_path = os.path.join(download_dir, acc, "model.pdb")
            if os.path.exists(pdb_path):
                pdb_paths.append(pdb_path)
                metadata_list.append(metadata)
        print()

    reports = batch_validate_pdbs(pdb_paths, output_dir)

    # Enrich reports with accession info
    for report, metadata in zip(reports, metadata_list):
        report["uniprot_accession"] = metadata.get("uniprot_accession")

    return reports


def write_summary_tsv(reports, output_path):
    """Write a combined summary TSV from batch reports."""
    columns = [
        "name", "n_residues", "mean_plddt", "quality",
        "plddt_very_high", "plddt_high", "plddt_low", "plddt_very_low",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        for r in reports:
            if "error" in r:
                continue
            dist = r.get("plddt_distribution", {})
            writer.writerow([
                r.get("name", ""),
                r.get("n_residues", 0),
                r.get("mean_plddt", 0),
                r.get("quality", ""),
                dist.get("very_high", 0),
                dist.get("high", 0),
                dist.get("low", 0),
                dist.get("very_low", 0),
            ])

    print(f"Summary written to {output_path}")


def write_batch_stats(reports, output_dir):
    """Write batch statistics JSON."""
    valid = [r for r in reports if "error" not in r]
    if not valid:
        return

    plddt_values = [r["mean_plddt"] for r in valid if r.get("mean_plddt")]
    n_residues = [r["n_residues"] for r in valid if r.get("n_residues")]

    quality_counts = {}
    for r in valid:
        q = r.get("quality", "unknown")
        quality_counts[q] = quality_counts.get(q, 0) + 1

    stats = {
        "total_structures": len(reports),
        "successful": len(valid),
        "failed": len(reports) - len(valid),
        "quality_distribution": quality_counts,
    }

    if plddt_values:
        stats["plddt_mean"] = round(sum(plddt_values) / len(plddt_values), 2)
        stats["plddt_min"] = round(min(plddt_values), 2)
        stats["plddt_max"] = round(max(plddt_values), 2)

    if n_residues:
        stats["residues_mean"] = round(sum(n_residues) / len(n_residues), 1)
        stats["residues_total"] = sum(n_residues)

    stats_path = os.path.join(output_dir, "batch_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Batch stats written to {stats_path}")
    return stats


def print_summary(reports):
    """Print a human-readable batch summary."""
    valid = [r for r in reports if "error" not in r]
    failed = [r for r in reports if "error" in r]

    print()
    print("=" * 70)
    print("BATCH VALIDATION SUMMARY")
    print("=" * 70)
    print(f"  Total:     {len(reports)}")
    print(f"  Valid:     {len(valid)}")
    print(f"  Failed:    {len(failed)}")

    if valid:
        plddt_values = [r["mean_plddt"] for r in valid if r.get("mean_plddt")]
        if plddt_values:
            print(f"  Mean pLDDT: {sum(plddt_values)/len(plddt_values):.1f}")
            print(f"  pLDDT range: {min(plddt_values):.1f} - {max(plddt_values):.1f}")

        quality_counts = {}
        for r in valid:
            q = r.get("quality", "unknown")
            quality_counts[q] = quality_counts.get(q, 0) + 1
        print(f"  Quality: {quality_counts}")

    if failed:
        print(f"\n  Failed structures:")
        for r in failed:
            print(f"    {r['name']}: {r['error']}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Batch validation of AlphaFold/PDB structures"
    )
    parser.add_argument("--accessions", nargs="+", help="UniProt accessions to retrieve and validate")
    parser.add_argument("--accession-file", help="File with one accession per line")
    parser.add_argument("--pdb-dir", help="Directory of PDB files to validate")
    parser.add_argument("--pdb-files", nargs="+", help="Individual PDB files to validate")
    parser.add_argument("--output-dir", default="batch_results", help="Output directory")
    parser.add_argument("--export-tsv", action="store_true",
                        help="Also export to validation_reports.tsv for Delta Lake")
    args = parser.parse_args()

    # Collect inputs
    accessions = []
    if args.accessions:
        accessions.extend(args.accessions)
    if args.accession_file:
        with open(args.accession_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    accessions.append(line)

    pdb_files = []
    if args.pdb_dir:
        pdb_files.extend(sorted(glob.glob(os.path.join(args.pdb_dir, "*.pdb"))))
    if args.pdb_files:
        pdb_files.extend(args.pdb_files)

    if not accessions and not pdb_files:
        parser.error("Provide --accessions, --accession-file, --pdb-dir, or --pdb-files")

    os.makedirs(args.output_dir, exist_ok=True)

    # Validate
    reports = []
    if accessions:
        reports.extend(batch_validate_accessions(accessions, args.output_dir))
    if pdb_files:
        reports.extend(batch_validate_pdbs(pdb_files, args.output_dir))

    # Write outputs
    write_summary_tsv(reports, os.path.join(args.output_dir, "summary.tsv"))
    write_batch_stats(reports, args.output_dir)

    if args.export_tsv:
        from export_tables import export_validation_report
        for r in reports:
            if "error" not in r:
                acc = r.get("uniprot_accession", r.get("name", "unknown"))
                export_validation_report(
                    {"metrics": r, "model": r.get("model"), "validation_date": r.get("validation_date")},
                    acc, "alphafold", args.output_dir,
                )
        print(f"Exported to validation_reports.tsv")

    print_summary(reports)


if __name__ == "__main__":
    main()
