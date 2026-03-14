#!/usr/bin/env python3
"""
Refinement cycle manager — post-refinement workflow, convergence detection,
model acceptance, and project finalization.

Handles the critical loop: refinement → validation → human inspection → next cycle.

Usage:
  # Process SLURM output after refinement finishes
  python cycle_manager.py process --project-dir /path/to/project --cycle 3

  # Accept a rebuilt model from the user
  python cycle_manager.py accept --project-dir /path/to/project --model rebuilt.pdb

  # Check convergence
  python cycle_manager.py converge --project-dir /path/to/project

  # Finalize project
  python cycle_manager.py finalize --project-dir /path/to/project
"""

import argparse
import glob
import json
import os
import shutil
import sys
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from refinement_state import ProjectState
from parse_validation import parse_validation_log, parse_refine_log
from generate_scripts import (
    generate_coot_outlier_script,
    generate_pymol_validation_script,
    generate_chimerax_session,
    generate_rfactor_plot,
)
from run_pipeline import log_provenance


# Convergence thresholds
RFREE_DELTA_THRESHOLD = 0.001   # R-free change per cycle
RGAP_MAX = 0.07                 # Maximum acceptable R-gap
MOLPROBITY_DELTA = 0.05         # MolProbity change threshold
CONSECUTIVE_PLATEAU = 2         # Cycles with no improvement before declaring converged


def find_refinement_output(project_dir, cycle_num):
    """Find the output PDB from a refinement cycle.

    Looks for common Phenix output naming patterns in the cycle directory.
    Returns path to the output model or None.
    """
    cycle_dir = os.path.join(project_dir, "cycles", f"cycle_{cycle_num:03d}")
    if not os.path.exists(cycle_dir):
        return None

    # Common Phenix output patterns
    patterns = [
        os.path.join(cycle_dir, "*_refine_*.pdb"),
        os.path.join(cycle_dir, "*_real_space_refined*.pdb"),
        os.path.join(cycle_dir, "*.pdb"),
    ]

    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]  # Most recent

    # Also check the SLURM output directory
    parent = project_dir
    patterns_parent = [
        os.path.join(parent, "*_refine_*.pdb"),
        os.path.join(parent, "*_real_space_refined*.pdb"),
    ]
    for pattern in patterns_parent:
        matches = sorted(glob.glob(pattern))
        if matches:
            # Move to cycle dir
            dest = os.path.join(cycle_dir, os.path.basename(matches[-1]))
            shutil.copy2(matches[-1], dest)
            return dest

    return None


def find_refinement_log(project_dir, cycle_num):
    """Find the refinement log file for a cycle."""
    cycle_dir = os.path.join(project_dir, "cycles", f"cycle_{cycle_num:03d}")

    patterns = [
        os.path.join(cycle_dir, "*_refine_*.log"),
        os.path.join(cycle_dir, "*.log"),
        os.path.join(project_dir, f"phenix_refine_*.out"),
        os.path.join(project_dir, f"phenix_rsr_*.out"),
    ]

    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]

    return None


def check_convergence(state):
    """Analyze refinement metrics history and determine if converged.

    Args:
        state: ProjectState instance

    Returns:
        (converged: bool, reason: str, recommendation: str)
    """
    metrics = state.cycle_metrics
    if len(metrics) < 2:
        return False, "Too few cycles", "Continue refinement"

    # Check R-free convergence (X-ray)
    rfree_history = [(m["cycle"], m.get("r_free")) for m in metrics if "r_free" in m]
    if len(rfree_history) >= 2:
        recent = rfree_history[-CONSECUTIVE_PLATEAU:]
        deltas = [
            abs(recent[i][1] - recent[i - 1][1])
            for i in range(1, len(recent))
        ]

        if all(d < RFREE_DELTA_THRESHOLD for d in deltas):
            return True, (
                f"R-free plateau: last {len(deltas)} cycles changed by "
                f"{', '.join(f'{d:.4f}' for d in deltas)}"
            ), "Converged — finalize or do manual rebuilding"

        # Check for overfitting (R-gap increasing)
        latest = metrics[-1]
        r_work = latest.get("r_work")
        r_free = latest.get("r_free")
        if r_work and r_free:
            r_gap = r_free - r_work
            if r_gap > RGAP_MAX:
                return False, (
                    f"R-gap = {r_gap:.3f} (threshold {RGAP_MAX})"
                ), "Overfitting detected — reduce parameters or add restraints"

        # Check if R-free is getting worse
        if len(rfree_history) >= 2 and rfree_history[-1][1] > rfree_history[-2][1]:
            return False, (
                f"R-free increased: {rfree_history[-2][1]:.4f} -> {rfree_history[-1][1]:.4f}"
            ), "R-free getting worse — try different strategy or manual rebuilding"

    # Check map-model CC convergence (cryo-EM)
    cc_history = [(m["cycle"], m.get("map_model_cc")) for m in metrics if "map_model_cc" in m]
    if len(cc_history) >= CONSECUTIVE_PLATEAU:
        recent = cc_history[-CONSECUTIVE_PLATEAU:]
        deltas = [
            abs(recent[i][1] - recent[i - 1][1])
            for i in range(1, len(recent))
        ]
        if all(d < 0.005 for d in deltas):
            return True, (
                f"Map-model CC plateau: {recent[-1][1]:.3f}"
            ), "Converged — finalize or do manual rebuilding"

    # Check MolProbity plateau
    mp_history = [(m["cycle"], m.get("molprobity_score")) for m in metrics if "molprobity_score" in m]
    if len(mp_history) >= CONSECUTIVE_PLATEAU:
        recent = mp_history[-CONSECUTIVE_PLATEAU:]
        deltas = [
            abs(recent[i][1] - recent[i - 1][1])
            for i in range(1, len(recent))
        ]
        if all(d < MOLPROBITY_DELTA for d in deltas):
            # MolProbity alone isn't enough — need R-free or CC to also plateau
            pass

    return False, "Still improving", "Continue refinement"


def process_refinement_output(project_dir, cycle_num):
    """Process the output of a refinement SLURM job.

    1. Find output model
    2. Parse refinement log for metrics
    3. Check convergence
    4. Generate visualization scripts
    5. Update project state

    Returns dict with results.
    """
    state = ProjectState.load(project_dir)
    cycle_dir = os.path.join(project_dir, "cycles", f"cycle_{cycle_num:03d}")
    os.makedirs(cycle_dir, exist_ok=True)
    scripts_dir = os.path.join(project_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    result = {"cycle": cycle_num, "status": "processed"}

    # Find output model
    model_path = find_refinement_output(project_dir, cycle_num)
    if not model_path:
        result["status"] = "error"
        result["error"] = "No output model found"
        print(f"ERROR: No refinement output found for cycle {cycle_num}")
        return result

    result["model"] = model_path
    print(f"Found output model: {model_path}")

    # Parse refinement log
    log_path = find_refinement_log(project_dir, cycle_num)
    metrics = {}
    outliers = []

    if log_path:
        print(f"Parsing log: {log_path}")
        with open(log_path) as f:
            log_text = f.read()
        refine_result = parse_refine_log(log_text)
        metrics = refine_result.get("final", {})
    else:
        # Try to parse from validation output
        metrics = parse_validation_log("")  # empty — no log found

    result["metrics"] = metrics

    # Record metrics in state
    state.record_cycle_metrics(
        cycle_num,
        r_work=metrics.get("r_work"),
        r_free=metrics.get("r_free"),
        molprobity_score=metrics.get("molprobity_score"),
        ramachandran_favored=metrics.get("ramachandran_favored"),
        ramachandran_outliers=metrics.get("ramachandran_outliers"),
        clash_score=metrics.get("clash_score"),
        rotamer_outliers=metrics.get("rotamer_outliers"),
        map_model_cc=metrics.get("map_model_cc"),
    )

    # Check convergence
    converged, reason, recommendation = check_convergence(state)
    result["converged"] = converged
    result["convergence_reason"] = reason
    result["recommendation"] = recommendation

    # Generate visualization scripts for outliers
    if outliers or metrics:
        generate_coot_outlier_script(
            outliers, model_path,
            output_path=os.path.join(scripts_dir, f"coot_cycle_{cycle_num:03d}.py"),
        )
        generate_pymol_validation_script(
            outliers, model_path,
            output_path=os.path.join(scripts_dir, f"pymol_cycle_{cycle_num:03d}.pml"),
        )
        generate_chimerax_session(
            model_path, outliers=outliers,
            output_path=os.path.join(scripts_dir, f"chimerax_cycle_{cycle_num:03d}.cxc"),
        )

    # Generate R-factor convergence plot if we have history
    rfactor_data = [
        {"cycle": m["cycle"], "r_work": m["r_work"], "r_free": m["r_free"]}
        for m in state.cycle_metrics
        if m.get("r_work") is not None and m.get("r_free") is not None
    ]
    if len(rfactor_data) >= 2:
        figures_dir = os.path.join(project_dir, "figures")
        os.makedirs(figures_dir, exist_ok=True)
        generate_rfactor_plot(
            rfactor_data,
            output_path=os.path.join(figures_dir, "rfactor_convergence.png"),
        )

    # Update state
    if converged:
        state.transition("converged")
    else:
        state.transition("awaiting_inspection")
    state.save()

    # Log provenance
    log_provenance(
        project_dir,
        action="process_refinement_output",
        tool="cycle_manager",
        input_model=model_path,
        metrics=metrics,
        notes=f"Cycle {cycle_num}: {reason}. {recommendation}",
    )

    return result


def accept_rebuilt_model(project_dir, rebuilt_model_path, notes=""):
    """Accept a rebuilt model from the user and prepare for next cycle.

    Args:
        project_dir: path to project directory
        rebuilt_model_path: path to the user's rebuilt PDB
        notes: user's notes about what they changed

    Returns next cycle number.
    """
    state = ProjectState.load(project_dir)

    if not state.is_waiting_for_human() and state.status != "converged":
        print(f"WARNING: Project is in '{state.status}' state, not awaiting inspection")

    next_cycle = state.current_cycle + 1
    cycle_dir = os.path.join(project_dir, "cycles", f"cycle_{next_cycle:03d}")
    os.makedirs(cycle_dir, exist_ok=True)

    # Copy rebuilt model
    dest = os.path.join(cycle_dir, "model_rebuilt.pdb")
    shutil.copy2(rebuilt_model_path, dest)
    print(f"Copied rebuilt model to {dest}")

    # Transition state
    state.transition("refining")
    state.save()

    # Log provenance
    log_provenance(
        project_dir,
        action="accept_rebuilt_model",
        tool="human",
        input_model=rebuilt_model_path,
        output_model=dest,
        notes=notes or "User-rebuilt model accepted",
    )

    print(f"Ready for refinement cycle {next_cycle}")
    return next_cycle


def finalize_project(project_dir):
    """Finalize a converged project.

    1. Find the best model across all cycles
    2. Copy to final/
    3. Generate final visualization scripts
    4. Update project state

    Returns path to final model.
    """
    state = ProjectState.load(project_dir)
    final_dir = os.path.join(project_dir, "final")
    os.makedirs(final_dir, exist_ok=True)

    # Find best model (lowest R-free or highest CC)
    best_cycle = None
    best_metric = None

    for m in state.cycle_metrics:
        cycle = m["cycle"]
        r_free = m.get("r_free")
        cc = m.get("map_model_cc")

        metric = r_free if r_free is not None else (-cc if cc is not None else None)
        if metric is not None and (best_metric is None or metric < best_metric):
            best_metric = metric
            best_cycle = cycle

    if best_cycle is None:
        best_cycle = state.current_cycle

    # Find the model for the best cycle
    model_path = find_refinement_output(project_dir, best_cycle)
    if not model_path:
        print(f"ERROR: Cannot find model for best cycle {best_cycle}")
        return None

    # Copy to final
    final_model = os.path.join(final_dir, "model_final.pdb")
    shutil.copy2(model_path, final_model)
    print(f"Final model (from cycle {best_cycle}): {final_model}")

    # Generate final scripts
    generate_pymol_validation_script(
        [], final_model,
        output_path=os.path.join(final_dir, "pymol_final.pml"),
    )
    generate_chimerax_session(
        final_model,
        output_path=os.path.join(final_dir, "chimerax_final.cxc"),
    )

    # Update state
    state.transition("complete")
    state.set("completed_date", datetime.now().strftime("%Y-%m-%d"))
    state.set("best_cycle", best_cycle)
    state.set("final_model", final_model)
    state.save()

    # Log provenance
    log_provenance(
        project_dir,
        action="finalize",
        tool="cycle_manager",
        input_model=model_path,
        output_model=final_model,
        notes=f"Finalized from cycle {best_cycle}",
    )

    return final_model


def main():
    parser = argparse.ArgumentParser(description="Refinement cycle manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_proc = subparsers.add_parser("process", help="Process refinement output")
    p_proc.add_argument("--project-dir", required=True)
    p_proc.add_argument("--cycle", type=int, required=True)

    p_acc = subparsers.add_parser("accept", help="Accept rebuilt model")
    p_acc.add_argument("--project-dir", required=True)
    p_acc.add_argument("--model", required=True)
    p_acc.add_argument("--notes", default="")

    p_conv = subparsers.add_parser("converge", help="Check convergence")
    p_conv.add_argument("--project-dir", required=True)

    p_fin = subparsers.add_parser("finalize", help="Finalize project")
    p_fin.add_argument("--project-dir", required=True)

    args = parser.parse_args()

    if args.command == "process":
        result = process_refinement_output(args.project_dir, args.cycle)
        print(json.dumps(result, indent=2))

    elif args.command == "accept":
        next_cycle = accept_rebuilt_model(args.project_dir, args.model, args.notes)
        print(f"Next cycle: {next_cycle}")

    elif args.command == "converge":
        state = ProjectState.load(args.project_dir)
        converged, reason, recommendation = check_convergence(state)
        print(f"Converged: {converged}")
        print(f"Reason: {reason}")
        print(f"Recommendation: {recommendation}")

    elif args.command == "finalize":
        final = finalize_project(args.project_dir)
        if final:
            print(f"Final model: {final}")


if __name__ == "__main__":
    main()
