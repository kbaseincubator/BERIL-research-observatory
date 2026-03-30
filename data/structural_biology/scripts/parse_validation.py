#!/usr/bin/env python3
"""
Parse Phenix validation tool outputs into structured JSON reports.

Supports parsing output from:
  - phenix.validation / phenix.molprobity (combined validation)
  - phenix.refine (refinement log with final statistics)
  - phenix.xtriage (data quality analysis)
  - phenix.ramalyze, phenix.rotalyze, phenix.clashscore (individual tools)

Can run standalone to validate a model, or be imported by other scripts.

Usage:
  # Parse an existing log file
  python parse_validation.py --log validation.log --type validation

  # Run phenix.molprobity and parse the output
  python parse_validation.py --model model.pdb --run

  # Run full validation with experimental data
  python parse_validation.py --model model.pdb --data data.mtz --run

  # Output as JSON
  python parse_validation.py --log refine.log --type refine --json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date


def parse_validation_log(log_text):
    """Parse phenix.validation or phenix.molprobity output.

    Returns dict with validation metrics.
    """
    metrics = {}

    # MolProbity score
    m = re.search(r"MolProbity score\s*[=:]\s*([\d.]+)", log_text)
    if m:
        metrics["molprobity_score"] = float(m.group(1))

    # Clashscore
    m = re.search(r"Clashscore\s*[=:]\s*([\d.]+)", log_text)
    if m:
        metrics["clash_score"] = float(m.group(1))

    # Ramachandran favored
    m = re.search(r"Ramachandran favored\s*[=:]\s*([\d.]+)\s*%", log_text)
    if m:
        metrics["ramachandran_favored"] = float(m.group(1))

    # Ramachandran outliers
    m = re.search(r"Ramachandran outliers\s*[=:]\s*([\d.]+)\s*%", log_text)
    if m:
        metrics["ramachandran_outliers"] = float(m.group(1))

    # Rotamer outliers
    m = re.search(r"Rotamer outliers\s*[=:]\s*([\d.]+)\s*%", log_text)
    if m:
        metrics["rotamer_outliers"] = float(m.group(1))

    # C-beta deviations
    m = re.search(r"C-beta deviations\s*[=:]\s*(\d+)", log_text)
    if m:
        metrics["cbeta_deviations"] = int(m.group(1))

    # R-work and R-free
    m = re.search(r"R-work\s*[=:]\s*([\d.]+)", log_text)
    if m:
        metrics["r_work"] = float(m.group(1))

    m = re.search(r"R-free\s*[=:]\s*([\d.]+)", log_text)
    if m:
        metrics["r_free"] = float(m.group(1))

    # RMS bonds and angles
    m = re.search(r"RMS\(bonds\)\s*[=:]\s*([\d.]+)", log_text)
    if m:
        metrics["rms_bonds"] = float(m.group(1))

    m = re.search(r"RMS\(angles\)\s*[=:]\s*([\d.]+)", log_text)
    if m:
        metrics["rms_angles"] = float(m.group(1))

    return metrics


def parse_refine_log(log_text):
    """Parse phenix.refine output log.

    Returns dict with final refinement metrics and per-cycle history.
    """
    result = {"cycles": [], "final": {}}

    # Parse individual macro cycles
    cycle_pattern = re.compile(
        r"macro_cycle\s+(\d+):\s*\n"
        r"\s*R-work\s*=\s*([\d.]+),\s*R-free\s*=\s*([\d.]+)",
        re.MULTILINE,
    )
    for m in cycle_pattern.finditer(log_text):
        cycle = {
            "cycle": int(m.group(1)),
            "r_work": float(m.group(2)),
            "r_free": float(m.group(3)),
        }
        result["cycles"].append(cycle)

    # Parse final statistics (reuse validation parser)
    # Look for "Final model statistics:" section or "Final R-work" line
    final_section = log_text
    final_marker = log_text.find("Final model statistics:")
    if final_marker >= 0:
        final_section = log_text[final_marker:]

    result["final"] = parse_validation_log(final_section)

    # Parse refinement strategy
    m = re.search(r"Refinement strategy:\s*(.+)", log_text)
    if m:
        result["refinement_strategy"] = m.group(1).strip()

    # Parse TLS groups
    m = re.search(r"Number of TLS groups:\s*(\d+)", log_text)
    if m:
        result["tls_groups"] = int(m.group(1))

    # Parse output model path
    m = re.search(r"Output model:\s*(\S+)", log_text)
    if m:
        result["output_model"] = m.group(1)

    return result


def parse_xtriage_log(log_text):
    """Parse phenix.xtriage output log.

    Returns dict with data quality metrics.
    """
    metrics = {}

    # Resolution
    m = re.search(r"Resolution\s*(?:range\s*)?:\s*[\d.]+ - ([\d.]+)", log_text)
    if m:
        metrics["resolution"] = float(m.group(1))

    # Space group
    m = re.search(r"Space group\s*:\s*(.+)", log_text)
    if m:
        metrics["space_group"] = m.group(1).strip()

    # Unit cell
    m = re.search(
        r"Unit cell\s*:\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)",
        log_text,
    )
    if m:
        metrics["unit_cell"] = [float(m.group(i)) for i in range(1, 7)]

    # Completeness
    m = re.search(r"Completeness\s*:\s*([\d.]+)%", log_text)
    if m:
        metrics["completeness"] = float(m.group(1))

    # Wilson B-factor
    m = re.search(r"Wilson B(?:-factor)?\s*:\s*([\d.]+)", log_text)
    if m:
        metrics["wilson_b"] = float(m.group(1))

    # Twinning
    if re.search(r"No twinning detected", log_text, re.IGNORECASE):
        metrics["twinning"] = False
    elif re.search(r"twinning detected", log_text, re.IGNORECASE):
        metrics["twinning"] = True

    # Number of reflections
    m = re.search(r"Number of reflections:\s*(\d+)", log_text)
    if m:
        metrics["n_reflections"] = int(m.group(1))

    # Matthews coefficient
    m = re.search(r"Matthews coefficient:\s*([\d.]+)", log_text)
    if m:
        metrics["matthews_coefficient"] = float(m.group(1))

    # Solvent content
    m = re.search(r"Solvent content:\s*([\d.]+)%", log_text)
    if m:
        metrics["solvent_content"] = float(m.group(1))

    # Molecules in ASU
    m = re.search(r"(?:Estimated )?[Nn]umber of molecules in ASU:\s*(\d+)", log_text)
    if m:
        metrics["n_molecules_asu"] = int(m.group(1))

    return metrics


def parse_ramalyze_output(text):
    """Parse phenix.ramalyze per-residue output.

    Returns list of outlier residues.
    """
    outliers = []
    for line in text.strip().split("\n"):
        if "OUTLIER" in line:
            parts = line.split()
            if len(parts) >= 4:
                outliers.append({
                    "residue": parts[0],
                    "type": "ramachandran_outlier",
                    "phi": parts[1] if len(parts) > 1 else None,
                    "psi": parts[2] if len(parts) > 2 else None,
                })
    return outliers


def parse_rotalyze_output(text):
    """Parse phenix.rotalyze per-residue output.

    Returns list of outlier residues.
    """
    outliers = []
    for line in text.strip().split("\n"):
        if "OUTLIER" in line:
            parts = line.split()
            if len(parts) >= 2:
                outliers.append({
                    "residue": parts[0],
                    "type": "rotamer_outlier",
                })
    return outliers


def run_phenix_validation(model_path, data_path=None):
    """Run phenix.molprobity and individual validation tools.

    Returns a structured validation report dict.
    """
    report = {
        "model": model_path,
        "data": data_path,
        "validation_date": date.today().isoformat(),
        "metrics": {},
        "outliers": [],
    }

    # Run phenix.molprobity
    cmd = ["phenix.molprobity", model_path]
    if data_path:
        cmd.append(data_path)
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"WARNING: phenix.molprobity exited with code {result.returncode}")
        print(f"  stderr: {result.stderr[:500]}")
    report["metrics"] = parse_validation_log(result.stdout)

    # Run phenix.ramalyze for per-residue Ramachandran
    cmd_rama = ["phenix.ramalyze", model_path]
    print(f"Running: {' '.join(cmd_rama)}")
    result_rama = subprocess.run(cmd_rama, capture_output=True, text=True, timeout=120)
    if result_rama.returncode == 0:
        report["outliers"].extend(parse_ramalyze_output(result_rama.stdout))

    # Run phenix.rotalyze for per-residue rotamers
    cmd_rota = ["phenix.rotalyze", model_path]
    print(f"Running: {' '.join(cmd_rota)}")
    result_rota = subprocess.run(cmd_rota, capture_output=True, text=True, timeout=120)
    if result_rota.returncode == 0:
        report["outliers"].extend(parse_rotalyze_output(result_rota.stdout))

    # Run phenix.clashscore
    cmd_clash = ["phenix.clashscore", model_path]
    print(f"Running: {' '.join(cmd_clash)}")
    result_clash = subprocess.run(cmd_clash, capture_output=True, text=True, timeout=120)
    if result_clash.returncode == 0:
        m = re.search(r"clashscore\s*=\s*([\d.]+)", result_clash.stdout)
        if m:
            report["metrics"]["clash_score"] = float(m.group(1))

    return report


def format_report(report, as_json=False):
    """Format a validation report for display or JSON output."""
    if as_json:
        return json.dumps(report, indent=2)

    lines = []
    lines.append("=" * 60)
    lines.append("Validation Report")
    lines.append("=" * 60)
    lines.append(f"  Model: {report.get('model', 'N/A')}")
    lines.append(f"  Data:  {report.get('data', 'N/A')}")
    lines.append(f"  Date:  {report.get('validation_date', 'N/A')}")
    lines.append("")

    m = report.get("metrics", {})
    if "molprobity_score" in m:
        lines.append(f"  MolProbity score:      {m['molprobity_score']:.2f}")
    if "clash_score" in m:
        lines.append(f"  Clashscore:            {m['clash_score']:.2f}")
    if "ramachandran_favored" in m:
        lines.append(f"  Ramachandran favored:  {m['ramachandran_favored']:.2f}%")
    if "ramachandran_outliers" in m:
        lines.append(f"  Ramachandran outliers: {m['ramachandran_outliers']:.2f}%")
    if "rotamer_outliers" in m:
        lines.append(f"  Rotamer outliers:      {m['rotamer_outliers']:.2f}%")
    if "cbeta_deviations" in m:
        lines.append(f"  C-beta deviations:     {m['cbeta_deviations']}")
    if "r_work" in m:
        lines.append(f"  R-work:                {m['r_work']:.4f}")
    if "r_free" in m:
        lines.append(f"  R-free:                {m['r_free']:.4f}")
    if "rms_bonds" in m:
        lines.append(f"  RMS(bonds):            {m['rms_bonds']:.3f}")
    if "rms_angles" in m:
        lines.append(f"  RMS(angles):           {m['rms_angles']:.3f}")

    outliers = report.get("outliers", [])
    if outliers:
        lines.append("")
        lines.append(f"  Outlier residues ({len(outliers)}):")
        for o in outliers[:20]:
            lines.append(f"    {o['residue']} — {o['type']}")
        if len(outliers) > 20:
            lines.append(f"    ... and {len(outliers) - 20} more")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Parse Phenix validation output or run validation"
    )
    parser.add_argument(
        "--log",
        help="Path to existing Phenix log file to parse",
    )
    parser.add_argument(
        "--type",
        choices=["validation", "refine", "xtriage"],
        default="validation",
        help="Type of log file (default: validation)",
    )
    parser.add_argument(
        "--model",
        help="Path to PDB model file (used with --run)",
    )
    parser.add_argument(
        "--data",
        help="Path to MTZ data file (used with --run)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run phenix.molprobity and parse the output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
    )
    parser.add_argument(
        "--output",
        help="Write report to file instead of stdout",
    )
    args = parser.parse_args()

    if args.run:
        if not args.model:
            parser.error("--model required when using --run")
        report = run_phenix_validation(args.model, args.data)
    elif args.log:
        with open(args.log) as f:
            log_text = f.read()
        if args.type == "refine":
            result = parse_refine_log(log_text)
            report = {
                "model": args.log,
                "data": None,
                "validation_date": date.today().isoformat(),
                "metrics": result["final"],
                "cycles": result.get("cycles", []),
                "refinement_strategy": result.get("refinement_strategy"),
                "outliers": [],
            }
        elif args.type == "xtriage":
            metrics = parse_xtriage_log(log_text)
            report = {
                "model": args.log,
                "data": None,
                "validation_date": date.today().isoformat(),
                "metrics": metrics,
                "outliers": [],
            }
        else:
            metrics = parse_validation_log(log_text)
            report = {
                "model": args.log,
                "data": None,
                "validation_date": date.today().isoformat(),
                "metrics": metrics,
                "outliers": [],
            }
    else:
        parser.error("Provide --log or --run")

    output = format_report(report, as_json=args.json)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
