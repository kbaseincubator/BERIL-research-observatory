#!/usr/bin/env python3
"""
Project dashboard — summarize all structural biology projects.

Scans the staging area for project directories and produces a summary table
with key metrics, identifies stalled projects, and optionally exports to
Delta Lake TSVs.

Usage:
  python project_dashboard.py --staging $SCRATCH/phenix_projects
  python project_dashboard.py --staging $SCRATCH/phenix_projects --json
  python project_dashboard.py --staging $SCRATCH/phenix_projects --export-tsv results/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from refinement_state import ProjectState

STALE_DAYS = 7  # Days before a project is considered stalled


def scan_projects(staging_dir):
    """Scan a staging directory for project directories.

    Returns list of project summary dicts.
    """
    summaries = []

    if not os.path.isdir(staging_dir):
        return summaries

    for entry in sorted(os.listdir(staging_dir)):
        project_dir = os.path.join(staging_dir, entry)
        notes_path = os.path.join(project_dir, "project_notes.json")
        if not os.path.exists(notes_path):
            continue

        state = ProjectState.load(project_dir)
        summary = _summarize_project(state)
        summary["project_dir"] = project_dir
        summaries.append(summary)

    return summaries


def _summarize_project(state):
    """Extract a summary dict from a ProjectState."""
    summary = {
        "project_id": state.project_id,
        "method": state.method or "N/A",
        "resolution": state.get("resolution"),
        "status": state.status,
        "cycle": state.current_cycle,
        "r_work": None,
        "r_free": None,
        "map_model_cc": None,
        "molprobity": None,
        "created": state.get("created", "")[:10],
        "last_updated": state.get("last_updated", "")[:10],
        "stale": False,
        "stale_reason": None,
    }

    # Get latest metrics
    latest = state.get_latest_metrics()
    if latest:
        summary["r_work"] = latest.get("r_work")
        summary["r_free"] = latest.get("r_free")
        summary["map_model_cc"] = latest.get("map_model_cc")
        summary["molprobity"] = latest.get("molprobity_score")

    # Check if stalled
    if state.is_waiting_for_human():
        last_updated = state.get("last_updated", "")
        if last_updated:
            try:
                updated_dt = datetime.fromisoformat(last_updated)
                age = datetime.now() - updated_dt
                if age > timedelta(days=STALE_DAYS):
                    summary["stale"] = True
                    summary["stale_reason"] = f"Awaiting inspection for {age.days} days"
            except ValueError:
                pass

    return summary


def format_table(summaries):
    """Format summaries as an ASCII table."""
    if not summaries:
        return "No projects found."

    # Column widths
    headers = ["Project", "Method", "Res(A)", "Status", "Cycle", "R-free", "CC", "MolP", "Updated"]
    rows = []
    for s in summaries:
        stale_mark = " (!)" if s["stale"] else ""
        rows.append([
            s["project_id"][:30],
            s["method"][:6],
            f"{s['resolution']:.1f}" if s["resolution"] else "-",
            s["status"][:16] + stale_mark,
            str(s["cycle"]),
            f"{s['r_free']:.3f}" if s["r_free"] else "-",
            f"{s['map_model_cc']:.3f}" if s["map_model_cc"] else "-",
            f"{s['molprobity']:.2f}" if s["molprobity"] else "-",
            s["last_updated"] or "-",
        ])

    # Calculate column widths
    widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]

    # Build table
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_line = "|" + "|".join(f" {h:<{w}} " for h, w in zip(headers, widths)) + "|"

    lines = [sep, header_line, sep]
    for row in rows:
        line = "|" + "|".join(f" {v:<{w}} " for v, w in zip(row, widths)) + "|"
        lines.append(line)
    lines.append(sep)

    return "\n".join(lines)


def format_json(summaries):
    """Format summaries as JSON."""
    return json.dumps(summaries, indent=2, default=str)


def print_dashboard(summaries):
    """Print a full dashboard with table and statistics."""
    total = len(summaries)
    by_status = {}
    for s in summaries:
        by_status[s["status"]] = by_status.get(s["status"], 0) + 1

    stale = [s for s in summaries if s["stale"]]

    print("=" * 70)
    print("STRUCTURAL BIOLOGY PROJECT DASHBOARD")
    print("=" * 70)
    print(f"  Total projects: {total}")
    for status, count in sorted(by_status.items()):
        print(f"    {status}: {count}")
    print()

    print(format_table(summaries))

    if stale:
        print(f"\n  STALE PROJECTS ({len(stale)}):")
        for s in stale:
            print(f"    {s['project_id']}: {s['stale_reason']}")

    print()


def export_all_projects(summaries, output_dir):
    """Export all projects to Delta Lake TSVs."""
    from export_tables import export_structure_project, export_refinement_cycles

    os.makedirs(output_dir, exist_ok=True)
    n_projects = 0
    n_cycles = 0

    for s in summaries:
        project_dir = s.get("project_dir")
        if project_dir and os.path.isdir(project_dir):
            n_projects += export_structure_project(project_dir, output_dir)
            n_cycles += export_refinement_cycles(project_dir, output_dir)

    print(f"Exported {n_projects} projects, {n_cycles} cycles to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Structural biology project dashboard")
    parser.add_argument("--staging", required=True, help="Staging directory with projects")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--export-tsv", help="Export all projects to TSV directory")
    args = parser.parse_args()

    summaries = scan_projects(args.staging)

    if args.json:
        print(format_json(summaries))
    else:
        print_dashboard(summaries)

    if args.export_tsv:
        export_all_projects(summaries, args.export_tsv)


if __name__ == "__main__":
    main()
