#!/usr/bin/env python3
"""
Refinement strategy advisor — recommend parameters based on resolution and method.

Uses static resolution-strategy tables (works with no project history) and
optionally scans local completed projects for empirical evidence.

Usage:
  python strategy_advisor.py --resolution 2.5 --method xray
  python strategy_advisor.py --resolution 3.5 --method cryo_em
  python strategy_advisor.py --resolution 1.8 --method xray --project-history /path/to/staging
  python strategy_advisor.py --resolution 2.5 --method xray --json

  # As a library
  from strategy_advisor import recommend_strategy
  rec = recommend_strategy(resolution=2.5, method="xray")
"""

import argparse
import json
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

# Static strategy tables from docs/structural_biology_memory.md
XRAY_STRATEGIES = [
    {
        "resolution_min": 0.0, "resolution_max": 1.5,
        "strategy": "individual_sites+individual_adp",
        "notes": "Anisotropic ADPs if data:param ratio > 3. Hydrogens visible in density.",
        "expected_rfree": (0.12, 0.18),
        "expected_cycles": (3, 6),
    },
    {
        "resolution_min": 1.5, "resolution_max": 2.0,
        "strategy": "individual_sites+individual_adp",
        "notes": "Standard isotropic B-factors.",
        "expected_rfree": (0.18, 0.24),
        "expected_cycles": (4, 8),
    },
    {
        "resolution_min": 2.0, "resolution_max": 3.0,
        "strategy": "individual_sites+individual_adp+tls",
        "notes": "TLS captures domain motion. Use 1 TLS group per chain initially.",
        "expected_rfree": (0.22, 0.28),
        "expected_cycles": (5, 10),
    },
    {
        "resolution_min": 3.0, "resolution_max": 4.0,
        "strategy": "individual_sites+group_adp",
        "notes": "Too few observations for individual ADPs. Use reference model restraints.",
        "expected_rfree": (0.26, 0.34),
        "expected_cycles": (5, 12),
    },
    {
        "resolution_min": 4.0, "resolution_max": 99.0,
        "strategy": "rigid_body",
        "notes": "Jelly-body restraints help. NCS constraints required for complexes.",
        "expected_rfree": (0.30, 0.42),
        "expected_cycles": (3, 8),
    },
]

CRYOEM_STRATEGIES = [
    {
        "resolution_min": 0.0, "resolution_max": 2.5,
        "strategy": "minimization_global+local_grid_search+adp",
        "notes": "Similar to high-res X-ray. Individual B-factors meaningful.",
        "expected_cc": (0.75, 0.90),
        "expected_cycles": (3, 6),
    },
    {
        "resolution_min": 2.5, "resolution_max": 3.5,
        "strategy": "minimization_global+local_grid_search+morphing",
        "notes": "Morphing helps domain fitting. Standard cryo-EM workflow.",
        "expected_cc": (0.65, 0.80),
        "expected_cycles": (4, 8),
    },
    {
        "resolution_min": 3.5, "resolution_max": 5.0,
        "strategy": "minimization_global+morphing+simulated_annealing",
        "notes": "Add NCS constraints for complexes. Simulated annealing escapes local minima.",
        "expected_cc": (0.55, 0.70),
        "expected_cycles": (5, 10),
    },
    {
        "resolution_min": 5.0, "resolution_max": 99.0,
        "strategy": "rigid_body",
        "notes": "Only domain placement is meaningful at this resolution.",
        "expected_cc": (0.40, 0.60),
        "expected_cycles": (2, 5),
    },
]


def recommend_strategy(resolution, method="xray", staging_dir=None):
    """Recommend a refinement strategy based on resolution and method.

    Args:
        resolution: resolution in Angstroms
        method: "xray" or "cryo_em"
        staging_dir: optional path to staging area for historical project data

    Returns dict with:
        strategy, notes, expected_rfree/expected_cc, expected_cycles,
        confidence, historical_evidence
    """
    strategies = XRAY_STRATEGIES if method == "xray" else CRYOEM_STRATEGIES

    # Find matching resolution bin
    match = None
    for s in strategies:
        if s["resolution_min"] <= resolution < s["resolution_max"]:
            match = s
            break

    if match is None:
        match = strategies[-1]  # fallback to lowest resolution

    result = {
        "resolution": resolution,
        "method": method,
        "strategy": match["strategy"],
        "notes": match["notes"],
        "confidence": "static",
        "historical_evidence": [],
    }

    if method == "xray":
        result["expected_rfree_range"] = list(match["expected_rfree"])
    else:
        result["expected_cc_range"] = list(match.get("expected_cc", (0.5, 0.8)))

    result["expected_cycles_range"] = list(match["expected_cycles"])

    # Scan historical projects if staging dir provided
    if staging_dir and os.path.isdir(staging_dir):
        evidence = _scan_project_history(staging_dir, resolution, method)
        if evidence:
            result["historical_evidence"] = evidence
            result["confidence"] = "empirical"

            # If historical data suggests a different strategy, note it
            best_hist = evidence[0]
            if best_hist.get("strategy") and best_hist["strategy"] != match["strategy"]:
                result["notes"] += (
                    f" Historical data suggests '{best_hist['strategy']}' "
                    f"(R-free={best_hist.get('best_rfree', 'N/A')} from {best_hist['project_id']})"
                )

    return result


def _scan_project_history(staging_dir, target_resolution, method,
                           resolution_tolerance=0.5):
    """Scan completed projects to find strategies used at similar resolutions.

    Returns list of evidence dicts sorted by best outcome.
    """
    from refinement_state import ProjectState

    evidence = []

    for entry in os.listdir(staging_dir):
        project_dir = os.path.join(staging_dir, entry)
        if not os.path.isdir(project_dir):
            continue

        notes_path = os.path.join(project_dir, "project_notes.json")
        if not os.path.exists(notes_path):
            continue

        state = ProjectState.load(project_dir)

        # Filter by method and resolution
        if state.method != method:
            continue
        proj_res = state.get("resolution")
        if proj_res is None:
            continue
        if abs(proj_res - target_resolution) > resolution_tolerance:
            continue

        # Extract best metrics
        metrics = state.cycle_metrics
        if not metrics:
            continue

        best_rfree = None
        best_cc = None
        strategy_used = None

        for m in metrics:
            if m.get("r_free") is not None:
                if best_rfree is None or m["r_free"] < best_rfree:
                    best_rfree = m["r_free"]
            if m.get("map_model_cc") is not None:
                if best_cc is None or m["map_model_cc"] > best_cc:
                    best_cc = m["map_model_cc"]
            if m.get("refinement_strategy"):
                strategy_used = m["refinement_strategy"]

        evidence.append({
            "project_id": state.project_id,
            "resolution": proj_res,
            "strategy": strategy_used,
            "best_rfree": best_rfree,
            "best_cc": best_cc,
            "total_cycles": len(metrics),
            "status": state.status,
        })

    # Sort by best outcome
    if method == "xray":
        evidence.sort(key=lambda e: e.get("best_rfree") or 999)
    else:
        evidence.sort(key=lambda e: -(e.get("best_cc") or 0))

    return evidence


def format_recommendation(rec, as_json=False):
    """Format a strategy recommendation for display."""
    if as_json:
        return json.dumps(rec, indent=2)

    lines = [
        "=" * 60,
        f"Strategy Recommendation ({rec['method']}, {rec['resolution']} A)",
        "=" * 60,
        f"  Strategy:  {rec['strategy']}",
        f"  Notes:     {rec['notes']}",
    ]

    if "expected_rfree_range" in rec:
        lo, hi = rec["expected_rfree_range"]
        lines.append(f"  Expected R-free: {lo:.2f} - {hi:.2f}")
    if "expected_cc_range" in rec:
        lo, hi = rec["expected_cc_range"]
        lines.append(f"  Expected CC: {lo:.2f} - {hi:.2f}")

    lo, hi = rec["expected_cycles_range"]
    lines.append(f"  Expected cycles: {lo} - {hi}")
    lines.append(f"  Confidence: {rec['confidence']}")

    if rec["historical_evidence"]:
        lines.append("")
        lines.append("  Historical evidence:")
        for e in rec["historical_evidence"][:5]:
            metric = f"R-free={e['best_rfree']:.3f}" if e.get("best_rfree") else f"CC={e.get('best_cc', '?')}"
            lines.append(
                f"    {e['project_id']}: {e.get('strategy', '?')} -> {metric} "
                f"({e['total_cycles']} cycles, {e['status']})"
            )

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Refinement strategy advisor")
    parser.add_argument("--resolution", type=float, required=True, help="Resolution in Angstroms")
    parser.add_argument("--method", default="xray", choices=["xray", "cryo_em"])
    parser.add_argument("--project-history", help="Staging dir to scan for historical data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    rec = recommend_strategy(args.resolution, args.method, args.project_history)
    print(format_recommendation(rec, as_json=args.json))


if __name__ == "__main__":
    main()
