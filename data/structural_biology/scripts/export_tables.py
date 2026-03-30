#!/usr/bin/env python3
"""
Export project data to TSV files for Delta Lake ingestion.

Produces TSV files matching the schema in structural_biology.json:
- structure_projects.tsv
- refinement_cycles.tsv
- validation_reports.tsv
- alphafold_structures.tsv

Usage:
  # Export a completed project
  python export_tables.py project --project-dir /path/to/project --output-dir /path/to/tsv/

  # Export a validation report
  python export_tables.py validation --report validation.json --accession P0A6Y8 --output-dir /path/to/tsv/

  # Export AlphaFold structure metadata
  python export_tables.py alphafold --metadata metadata.tsv --output-dir /path/to/tsv/
"""

import argparse
import csv
import json
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from refinement_state import ProjectState

MINIO_BASE = "s3a://cdm-lake/tenant-general-warehouse/kescience/structural-biology"

# Column definitions matching structural_biology.json schema_sql
STRUCTURE_PROJECTS_COLUMNS = [
    "project_id", "uniprot_accession", "pdb_id", "method",
    "resolution", "space_group", "status", "created_date", "completed_date",
]

REFINEMENT_CYCLES_COLUMNS = [
    "project_id", "cycle_number", "r_work", "r_free", "r_gap", "map_model_cc",
    "molprobity_score", "ramachandran_favored", "ramachandran_outliers",
    "clash_score", "rotamer_outliers", "refinement_strategy", "parameters_json",
    "model_path", "notes", "timestamp",
]

VALIDATION_REPORTS_COLUMNS = [
    "uniprot_accession", "source", "molprobity_score", "ramachandran_favored",
    "ramachandran_outliers", "clash_score", "rotamer_outliers", "cbeta_deviations",
    "report_path", "model_path", "validation_date",
]

ALPHAFOLD_STRUCTURES_COLUMNS = [
    "uniprot_accession", "pdb_path", "cif_path", "pae_path",
    "n_residues", "n_domains", "mean_plddt", "retrieval_date",
]


def _append_tsv(filepath, columns, rows):
    """Append rows to a TSV file, writing header if file doesn't exist."""
    write_header = not os.path.exists(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        if write_header:
            writer.writerow(columns)
        for row in rows:
            writer.writerow([_format_value(row.get(col)) for col in columns])
    return len(rows)


def _format_value(val):
    """Format a value for TSV output."""
    if val is None:
        return ""
    if isinstance(val, float):
        return f"{val:.6g}"
    if isinstance(val, dict):
        return json.dumps(val)
    return str(val)


def export_structure_project(project_dir, output_dir):
    """Export a project to structure_projects.tsv.

    Returns number of rows written.
    """
    state = ProjectState.load(project_dir)

    row = {
        "project_id": state.project_id,
        "uniprot_accession": state.get("uniprot_accession"),
        "pdb_id": state.get("pdb_id"),
        "method": state.method,
        "resolution": state.get("resolution"),
        "space_group": state.get("space_group"),
        "status": state.status,
        "created_date": state.get("created", "")[:10],
        "completed_date": state.get("completed_date"),
    }

    filepath = os.path.join(output_dir, "structure_projects.tsv")
    return _append_tsv(filepath, STRUCTURE_PROJECTS_COLUMNS, [row])


def export_refinement_cycles(project_dir, output_dir):
    """Export all refinement cycles to refinement_cycles.tsv.

    Returns number of rows written.
    """
    state = ProjectState.load(project_dir)
    rows = []

    for m in state.cycle_metrics:
        r_work = m.get("r_work")
        r_free = m.get("r_free")
        r_gap = (r_free - r_work) if r_work is not None and r_free is not None else None

        row = {
            "project_id": state.project_id,
            "cycle_number": m["cycle"],
            "r_work": r_work,
            "r_free": r_free,
            "r_gap": r_gap,
            "map_model_cc": m.get("map_model_cc"),
            "molprobity_score": m.get("molprobity_score"),
            "ramachandran_favored": m.get("ramachandran_favored"),
            "ramachandran_outliers": m.get("ramachandran_outliers"),
            "clash_score": m.get("clash_score"),
            "rotamer_outliers": m.get("rotamer_outliers"),
            "refinement_strategy": m.get("refinement_strategy"),
            "parameters_json": m.get("parameters"),
            "model_path": m.get("model_path",
                                f"{MINIO_BASE}/projects/{state.project_id}/cycles/cycle_{m['cycle']:03d}/model.pdb"),
            "notes": m.get("notes"),
            "timestamp": m.get("timestamp"),
        }
        rows.append(row)

    filepath = os.path.join(output_dir, "refinement_cycles.tsv")
    return _append_tsv(filepath, REFINEMENT_CYCLES_COLUMNS, rows)


def export_validation_report(report, accession, source, output_dir):
    """Export a validation report to validation_reports.tsv.

    Args:
        report: dict with 'metrics' key containing validation metrics
        accession: UniProt accession
        source: one of 'alphafold', 'experimental', 'refined'
        output_dir: output directory

    Returns number of rows written.
    """
    metrics = report.get("metrics", {})

    row = {
        "uniprot_accession": accession,
        "source": source,
        "molprobity_score": metrics.get("molprobity_score"),
        "ramachandran_favored": metrics.get("ramachandran_favored"),
        "ramachandran_outliers": metrics.get("ramachandran_outliers"),
        "clash_score": metrics.get("clash_score"),
        "rotamer_outliers": metrics.get("rotamer_outliers"),
        "cbeta_deviations": metrics.get("cbeta_deviations"),
        "report_path": report.get("report_path"),
        "model_path": report.get("model"),
        "validation_date": report.get("validation_date"),
    }

    filepath = os.path.join(output_dir, "validation_reports.tsv")
    return _append_tsv(filepath, VALIDATION_REPORTS_COLUMNS, [row])


def export_alphafold_structure(metadata, output_dir):
    """Export AlphaFold structure metadata to alphafold_structures.tsv.

    Args:
        metadata: dict matching ALPHAFOLD_STRUCTURES_COLUMNS keys
        output_dir: output directory

    Returns number of rows written.
    """
    filepath = os.path.join(output_dir, "alphafold_structures.tsv")
    return _append_tsv(filepath, ALPHAFOLD_STRUCTURES_COLUMNS, [metadata])


def main():
    parser = argparse.ArgumentParser(
        description="Export structural biology data to TSV for Delta Lake ingestion"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_proj = subparsers.add_parser("project", help="Export project + cycles")
    p_proj.add_argument("--project-dir", required=True)
    p_proj.add_argument("--output-dir", required=True)

    p_val = subparsers.add_parser("validation", help="Export validation report")
    p_val.add_argument("--report", required=True, help="Path to validation JSON")
    p_val.add_argument("--accession", required=True)
    p_val.add_argument("--source", default="experimental",
                       choices=["alphafold", "experimental", "refined"])
    p_val.add_argument("--output-dir", required=True)

    p_af = subparsers.add_parser("alphafold", help="Export AlphaFold metadata")
    p_af.add_argument("--metadata", required=True, help="Path to metadata TSV")
    p_af.add_argument("--output-dir", required=True)

    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    if args.command == "project":
        n1 = export_structure_project(args.project_dir, args.output_dir)
        n2 = export_refinement_cycles(args.project_dir, args.output_dir)
        print(f"Exported {n1} project row, {n2} cycle rows to {args.output_dir}")

    elif args.command == "validation":
        with open(args.report) as f:
            report = json.load(f)
        n = export_validation_report(report, args.accession, args.source, args.output_dir)
        print(f"Exported {n} validation report row to {args.output_dir}")

    elif args.command == "alphafold":
        # Read metadata TSV and re-export (for format consistency)
        import csv as csv_mod
        with open(args.metadata) as f:
            reader = csv_mod.DictReader(f, delimiter="\t")
            for row in reader:
                export_alphafold_structure(row, args.output_dir)
        print(f"Exported AlphaFold metadata to {args.output_dir}")


if __name__ == "__main__":
    main()
