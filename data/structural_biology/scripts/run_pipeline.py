#!/usr/bin/env python3
"""
Structural biology pipeline orchestrator.

Manages project directories, SLURM job submission, output parsing, and
provenance logging for Phenix structural biology workflows.

Usage:
  run_pipeline.py retrieve --accession P0A6Y8 --project-id struct_20260314_trx
  run_pipeline.py validate --model model.pdb [--data data.mtz]
  run_pipeline.py xray --data data.mtz --seq seq.fa --project-id struct_20260314_dhfr
  run_pipeline.py cryoem --map map.mrc --seq seq.fa --resolution 3.0 --project-id struct_20260314_ribo
  run_pipeline.py refine --project-id struct_20260314_dhfr [--strategy individual_sites+individual_adp+tls]
  run_pipeline.py process --project-id struct_20260314_dhfr --cycle 3
  run_pipeline.py accept --project-id struct_20260314_dhfr --model rebuilt.pdb
  run_pipeline.py converge --project-id struct_20260314_dhfr
  run_pipeline.py finalize --project-id struct_20260314_dhfr
  run_pipeline.py status --project-id struct_20260314_dhfr
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SLURM_TEMPLATES_DIR = os.path.join(SCRIPTS_DIR, "slurm_templates")
MINIO_BASE = "s3a://cdm-lake/tenant-general-warehouse/kescience/structural-biology"

# Default staging area for projects (local scratch)
DEFAULT_STAGING = os.environ.get(
    "PHENIX_STAGING",
    os.path.join(os.environ.get("SCRATCH", "/tmp"), "phenix_projects"),
)


def ensure_project_dir(project_id, staging=None):
    """Create local project directory structure. Returns project path."""
    staging = staging or DEFAULT_STAGING
    project_dir = os.path.join(staging, project_id)
    for subdir in ["input", "cycles", "scripts", "figures", "final"]:
        os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
    return project_dir


def load_project_state(project_dir):
    """Load project state from project_notes.json."""
    notes_path = os.path.join(project_dir, "project_notes.json")
    if os.path.exists(notes_path):
        with open(notes_path) as f:
            return json.load(f)
    return {
        "project_id": os.path.basename(project_dir),
        "status": "new",
        "current_cycle": 0,
        "steps_completed": [],
        "created": datetime.now().isoformat(),
    }


def save_project_state(project_dir, state):
    """Save project state to project_notes.json."""
    notes_path = os.path.join(project_dir, "project_notes.json")
    with open(notes_path, "w") as f:
        json.dump(state, f, indent=2)


def log_provenance(project_dir, action, tool, parameters=None, metrics=None,
                   input_model=None, output_model=None, notes=None):
    """Append a provenance record to the project's provenance.jsonl."""
    record = {
        "project_id": os.path.basename(project_dir),
        "action": action,
        "tool": tool,
        "timestamp": datetime.now().isoformat(),
    }
    if parameters:
        record["parameters"] = parameters
    if metrics:
        record["metrics"] = metrics
    if input_model:
        record["input_model"] = input_model
    if output_model:
        record["output_model"] = output_model
    if notes:
        record["decision_rationale"] = notes

    prov_path = os.path.join(project_dir, "provenance.jsonl")
    with open(prov_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"  Provenance logged: {action} ({tool})")


def submit_slurm_job(template_name, env_vars, project_dir, dry_run=False):
    """Submit a SLURM job using a template. Returns job ID or None."""
    template_path = os.path.join(SLURM_TEMPLATES_DIR, template_name)
    if not os.path.exists(template_path):
        print(f"ERROR: SLURM template not found: {template_path}")
        return None

    # Build sbatch command with env vars
    env_args = []
    for key, val in env_vars.items():
        env_args.append(f"{key}={val}")

    cmd = ["sbatch"]
    if env_args:
        cmd.extend(["--export", ",".join(env_args)])
    cmd.extend(["--chdir", project_dir, template_path])

    if dry_run:
        print(f"  [DRY RUN] Would submit: {' '.join(cmd)}")
        return "DRY_RUN"

    print(f"  Submitting: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: sbatch failed: {result.stderr.strip()}")
        return None

    # Parse job ID from "Submitted batch job 12345"
    output = result.stdout.strip()
    print(f"  {output}")
    parts = output.split()
    job_id = parts[-1] if parts else None
    return job_id


def check_slurm_job(job_id):
    """Check SLURM job status. Returns status string."""
    result = subprocess.run(
        ["sacct", "-j", str(job_id), "--format=State", "--noheader", "--parsable2"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "UNKNOWN"
    status = result.stdout.strip().split("\n")[0] if result.stdout.strip() else "UNKNOWN"
    return status


def get_latest_cycle(project_dir):
    """Find the latest refinement cycle number."""
    cycles_dir = os.path.join(project_dir, "cycles")
    if not os.path.exists(cycles_dir):
        return 0
    existing = [
        d for d in os.listdir(cycles_dir)
        if d.startswith("cycle_") and os.path.isdir(os.path.join(cycles_dir, d))
    ]
    if not existing:
        return 0
    numbers = []
    for d in existing:
        try:
            numbers.append(int(d.split("_")[1]))
        except (ValueError, IndexError):
            pass
    return max(numbers) if numbers else 0


def upload_to_minio(local_path, minio_path):
    """Upload a file or directory to MinIO."""
    cmd = ["mc", "cp"]
    if os.path.isdir(local_path):
        cmd.append("--recursive")
    cmd.extend([local_path, f"berdl/{minio_path}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: MinIO upload failed: {result.stderr.strip()}")
        return False
    return True


# ─── Subcommands ─────────────────────────────────────────────

def cmd_retrieve(args):
    """Retrieve AlphaFold structure(s)."""
    from retrieve_alphafold import retrieve_structure

    project_dir = None
    if args.project_id:
        project_dir = ensure_project_dir(args.project_id)

    output_dir = args.output_dir or (
        os.path.join(project_dir, "input") if project_dir else "."
    )

    import requests as req
    session = req.Session()

    for acc in args.accession:
        metadata = retrieve_structure(acc, output_dir, session=session)
        if metadata and project_dir:
            log_provenance(
                project_dir,
                action="retrieve_alphafold",
                tool="retrieve_alphafold.py",
                parameters={"accession": acc},
                metrics={"n_residues": metadata["n_residues"], "mean_plddt": metadata["mean_plddt"]},
            )
    print("Retrieval complete.")


def cmd_validate(args):
    """Run validation on a model."""
    from parse_validation import run_phenix_validation, format_report

    report = run_phenix_validation(args.model, args.data)
    print(format_report(report, as_json=args.json))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")

    if args.project_id:
        project_dir = ensure_project_dir(args.project_id)
        log_provenance(
            project_dir,
            action="validation",
            tool="phenix.molprobity",
            input_model=args.model,
            metrics=report.get("metrics", {}),
        )


def cmd_xray(args):
    """Start X-ray structure determination pipeline."""
    project_dir = ensure_project_dir(args.project_id)
    state = load_project_state(project_dir)

    print(f"=== X-ray Pipeline: {args.project_id} ===")
    print(f"Data: {args.data}")
    print(f"Sequence: {args.seq}")
    print(f"Project dir: {project_dir}")
    print()

    # Copy input files
    import shutil
    input_dir = os.path.join(project_dir, "input")
    data_dest = os.path.join(input_dir, os.path.basename(args.data))
    seq_dest = os.path.join(input_dir, os.path.basename(args.seq))
    if not os.path.exists(data_dest):
        shutil.copy2(args.data, data_dest)
    if not os.path.exists(seq_dest):
        shutil.copy2(args.seq, seq_dest)

    state["method"] = "xray"
    state["data_file"] = data_dest
    state["seq_file"] = seq_dest
    state["status"] = "in_progress"

    # Step 1: xtriage (run interactively — fast)
    if "xtriage" not in state["steps_completed"]:
        print("Step 1: Running phenix.xtriage...")
        result = subprocess.run(
            ["phenix.xtriage", data_dest],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            from parse_validation import parse_xtriage_log
            xtriage_metrics = parse_xtriage_log(result.stdout)
            log_provenance(project_dir, "xtriage", "phenix.xtriage", metrics=xtriage_metrics)
            state["xtriage"] = xtriage_metrics
            state["steps_completed"].append("xtriage")
            print(f"  Resolution: {xtriage_metrics.get('resolution', 'N/A')} A")
            print(f"  Space group: {xtriage_metrics.get('space_group', 'N/A')}")
        else:
            print(f"  WARNING: xtriage failed: {result.stderr[:200]}")

    # Step 2: Molecular replacement with Phaser (SLURM)
    if "phaser" not in state["steps_completed"]:
        search_model = args.search_model
        if not search_model:
            print("\nStep 2: Molecular replacement")
            print("  No search model provided. Use --search-model or retrieve AlphaFold structure first.")
            print("  Skipping Phaser for now.")
        else:
            print(f"\nStep 2: Submitting Phaser MR (search model: {search_model})...")
            job_id = submit_slurm_job("phaser.sh", {
                "PHENIX_DATA": data_dest,
                "PHENIX_MODEL": search_model,
                "PHENIX_SEQ": seq_dest,
                "PHENIX_PROJECT_ID": args.project_id,
            }, project_dir, dry_run=args.dry_run)
            if job_id:
                state["phaser_job_id"] = job_id
                log_provenance(project_dir, "molecular_replacement", "phenix.phaser",
                               parameters={"search_model": search_model, "slurm_job": job_id})

    save_project_state(project_dir, state)
    print(f"\nProject state saved. Use 'run_pipeline.py status --project-id {args.project_id}' to check progress.")


def cmd_cryoem(args):
    """Start cryo-EM structure determination pipeline."""
    project_dir = ensure_project_dir(args.project_id)
    state = load_project_state(project_dir)

    print(f"=== Cryo-EM Pipeline: {args.project_id} ===")
    print(f"Map: {args.map}")
    print(f"Sequence: {args.seq}")
    print(f"Resolution: {args.resolution} A")
    print(f"Project dir: {project_dir}")
    print()

    # Copy input files
    import shutil
    input_dir = os.path.join(project_dir, "input")
    map_dest = os.path.join(input_dir, os.path.basename(args.map))
    seq_dest = os.path.join(input_dir, os.path.basename(args.seq))
    if not os.path.exists(map_dest):
        shutil.copy2(args.map, map_dest)
    if not os.path.exists(seq_dest):
        shutil.copy2(args.seq, seq_dest)

    state["method"] = "cryo_em"
    state["map_file"] = map_dest
    state["seq_file"] = seq_dest
    state["resolution"] = args.resolution
    state["status"] = "in_progress"

    # Step 1: map_to_model or predict_and_build (SLURM)
    if args.search_model:
        print("Step 1: Submitting phenix.predict_and_build (AlphaFold-guided)...")
        template = "predict_and_build.sh"
        env_vars = {
            "PHENIX_MODEL": args.search_model,
            "PHENIX_MAP": map_dest,
            "PHENIX_SEQ": seq_dest,
            "PHENIX_RESOLUTION": str(args.resolution),
            "PHENIX_PROJECT_ID": args.project_id,
        }
        tool = "phenix.predict_and_build"
    else:
        print("Step 1: Submitting phenix.map_to_model...")
        template = "map_to_model.sh"
        env_vars = {
            "PHENIX_MAP": map_dest,
            "PHENIX_SEQ": seq_dest,
            "PHENIX_RESOLUTION": str(args.resolution),
            "PHENIX_PROJECT_ID": args.project_id,
        }
        tool = "phenix.map_to_model"

    job_id = submit_slurm_job(template, env_vars, project_dir, dry_run=args.dry_run)
    if job_id:
        state["build_job_id"] = job_id
        log_provenance(project_dir, "model_building", tool,
                       parameters={"resolution": args.resolution, "slurm_job": job_id})

    save_project_state(project_dir, state)
    print(f"\nProject state saved. Use 'run_pipeline.py status --project-id {args.project_id}' to check progress.")


def cmd_refine(args):
    """Submit a refinement cycle."""
    project_dir = ensure_project_dir(args.project_id)
    state = load_project_state(project_dir)
    method = state.get("method", "xray")

    # Determine cycle number
    cycle_num = get_latest_cycle(project_dir) + 1
    cycle_dir = os.path.join(project_dir, "cycles", f"cycle_{cycle_num:03d}")
    os.makedirs(cycle_dir, exist_ok=True)

    # Find input model
    model = args.model
    if not model:
        # Look for previous cycle output or initial model
        if cycle_num > 1:
            prev_cycle = os.path.join(project_dir, "cycles", f"cycle_{cycle_num - 1:03d}")
            candidates = [
                os.path.join(prev_cycle, f) for f in os.listdir(prev_cycle)
                if f.endswith(".pdb") and "refine" in f
            ] if os.path.exists(prev_cycle) else []
            if candidates:
                model = candidates[0]
        if not model:
            print("ERROR: No model found. Provide --model or ensure previous cycle output exists.")
            return

    strategy = args.strategy or "individual_sites+individual_adp"

    print(f"=== Refinement Cycle {cycle_num} ({args.project_id}) ===")
    print(f"Model: {model}")
    print(f"Strategy: {strategy}")

    if method == "xray" or method == "cryo_em" and state.get("data_file"):
        # Reciprocal-space refinement
        template = "refine.sh"
        env_vars = {
            "PHENIX_MODEL": model,
            "PHENIX_DATA": state.get("data_file", args.data or ""),
            "PHENIX_STRATEGY": strategy,
            "PHENIX_CYCLES": str(args.cycles or 5),
            "PHENIX_PROJECT_ID": args.project_id,
        }
    else:
        # Real-space refinement (cryo-EM)
        template = "real_space_refine.sh"
        env_vars = {
            "PHENIX_MODEL": model,
            "PHENIX_MAP": state.get("map_file", args.map or ""),
            "PHENIX_RESOLUTION": str(state.get("resolution", args.resolution or 3.0)),
            "PHENIX_CYCLES": str(args.cycles or 5),
            "PHENIX_PROJECT_ID": args.project_id,
        }

    job_id = submit_slurm_job(template, env_vars, project_dir, dry_run=args.dry_run)
    if job_id:
        state["current_cycle"] = cycle_num
        state[f"cycle_{cycle_num}_job"] = job_id
        log_provenance(
            project_dir,
            action="refinement",
            tool=f"phenix.{'refine' if template == 'refine.sh' else 'real_space_refine'}",
            input_model=model,
            parameters={"strategy": strategy, "cycles": args.cycles or 5, "slurm_job": job_id},
            notes=args.notes,
        )

    save_project_state(project_dir, state)
    print(f"\nCycle {cycle_num} submitted. Check with: run_pipeline.py status --project-id {args.project_id}")


def cmd_process(args):
    """Process SLURM output after refinement finishes."""
    from cycle_manager import process_refinement_output

    staging = args.staging or DEFAULT_STAGING
    project_dir = os.path.join(staging, args.project_id)

    if not os.path.exists(project_dir):
        print(f"Project not found: {project_dir}")
        return

    result = process_refinement_output(project_dir, args.cycle)
    print()
    print(json.dumps(result, indent=2))


def cmd_accept(args):
    """Accept a rebuilt model from the user."""
    from cycle_manager import accept_rebuilt_model

    staging = args.staging or DEFAULT_STAGING
    project_dir = os.path.join(staging, args.project_id)

    if not os.path.exists(project_dir):
        print(f"Project not found: {project_dir}")
        return

    next_cycle = accept_rebuilt_model(project_dir, args.model, args.notes or "")
    print(f"Ready for refinement cycle {next_cycle}")


def cmd_converge(args):
    """Check convergence and recommend next step."""
    from cycle_manager import check_convergence as _check_conv
    from refinement_state import ProjectState

    staging = args.staging or DEFAULT_STAGING
    project_dir = os.path.join(staging, args.project_id)

    if not os.path.exists(project_dir):
        print(f"Project not found: {project_dir}")
        return

    state = ProjectState.load(project_dir)
    converged, reason, recommendation = _check_conv(state)
    print(f"Converged: {converged}")
    print(f"Reason: {reason}")
    print(f"Recommendation: {recommendation}")


def cmd_finalize(args):
    """Finalize a converged project."""
    from cycle_manager import finalize_project

    staging = args.staging or DEFAULT_STAGING
    project_dir = os.path.join(staging, args.project_id)

    if not os.path.exists(project_dir):
        print(f"Project not found: {project_dir}")
        return

    final = finalize_project(project_dir)
    if final:
        print(f"Final model: {final}")


def cmd_status(args):
    """Show project status."""
    staging = args.staging or DEFAULT_STAGING
    project_dir = os.path.join(staging, args.project_id)

    if not os.path.exists(project_dir):
        print(f"Project not found: {project_dir}")
        return

    state = load_project_state(project_dir)

    print(f"=== Project Status: {args.project_id} ===")
    print(f"  Method:          {state.get('method', 'N/A')}")
    print(f"  Status:          {state.get('status', 'N/A')}")
    print(f"  Created:         {state.get('created', 'N/A')}")
    print(f"  Current cycle:   {state.get('current_cycle', 0)}")
    print(f"  Steps completed: {', '.join(state.get('steps_completed', [])) or 'none'}")
    print(f"  Local path:      {project_dir}")

    # Check any pending SLURM jobs
    for key, val in state.items():
        if key.endswith("_job_id") or key.endswith("_job"):
            job_status = check_slurm_job(val)
            print(f"  SLURM {key}: {val} ({job_status})")

    # Show latest cycle metrics from provenance
    prov_path = os.path.join(project_dir, "provenance.jsonl")
    if os.path.exists(prov_path):
        print("\n  Recent actions:")
        with open(prov_path) as f:
            lines = f.readlines()
        for line in lines[-5:]:
            record = json.loads(line)
            ts = record.get("timestamp", "?")[:19]
            action = record.get("action", "?")
            tool = record.get("tool", "?")
            print(f"    [{ts}] {action} ({tool})")
            metrics = record.get("metrics", {})
            if metrics:
                for k, v in list(metrics.items())[:4]:
                    print(f"      {k}: {v}")


def main():
    parser = argparse.ArgumentParser(
        description="Phenix structural biology pipeline orchestrator"
    )
    parser.add_argument("--dry-run", action="store_true", help="Don't submit SLURM jobs")
    parser.add_argument("--staging", help=f"Staging directory (default: {DEFAULT_STAGING})")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # retrieve
    p_ret = subparsers.add_parser("retrieve", help="Retrieve AlphaFold structures")
    p_ret.add_argument("--accession", nargs="+", required=True)
    p_ret.add_argument("--project-id")
    p_ret.add_argument("--output-dir")

    # validate
    p_val = subparsers.add_parser("validate", help="Run validation on a model")
    p_val.add_argument("--model", required=True)
    p_val.add_argument("--data", help="MTZ data file (optional)")
    p_val.add_argument("--project-id")
    p_val.add_argument("--json", action="store_true")
    p_val.add_argument("--output", help="Save report to file")

    # xray
    p_xray = subparsers.add_parser("xray", help="Start X-ray pipeline")
    p_xray.add_argument("--data", required=True, help="MTZ reflection data")
    p_xray.add_argument("--seq", required=True, help="Sequence FASTA")
    p_xray.add_argument("--project-id", required=True)
    p_xray.add_argument("--search-model", help="Search model for MR (PDB)")

    # cryoem
    p_em = subparsers.add_parser("cryoem", help="Start cryo-EM pipeline")
    p_em.add_argument("--map", required=True, help="Map file (MRC)")
    p_em.add_argument("--seq", required=True, help="Sequence FASTA")
    p_em.add_argument("--resolution", type=float, required=True)
    p_em.add_argument("--project-id", required=True)
    p_em.add_argument("--search-model", help="AlphaFold model for guided building")

    # refine
    p_ref = subparsers.add_parser("refine", help="Submit refinement cycle")
    p_ref.add_argument("--project-id", required=True)
    p_ref.add_argument("--model", help="Input model (auto-detected from previous cycle)")
    p_ref.add_argument("--data", help="MTZ data (for X-ray)")
    p_ref.add_argument("--map", help="Map file (for cryo-EM)")
    p_ref.add_argument("--resolution", type=float)
    p_ref.add_argument("--strategy", help="Refinement strategy")
    p_ref.add_argument("--cycles", type=int, help="Number of macro cycles")
    p_ref.add_argument("--notes", help="Notes on what changed this cycle")

    # process (M3)
    p_proc = subparsers.add_parser("process", help="Process refinement output")
    p_proc.add_argument("--project-id", required=True)
    p_proc.add_argument("--cycle", type=int, required=True, help="Cycle number to process")

    # accept (M3)
    p_acc = subparsers.add_parser("accept", help="Accept rebuilt model from user")
    p_acc.add_argument("--project-id", required=True)
    p_acc.add_argument("--model", required=True, help="Path to rebuilt PDB")
    p_acc.add_argument("--notes", help="Notes about what was changed")

    # converge (M3)
    p_conv = subparsers.add_parser("converge", help="Check convergence")
    p_conv.add_argument("--project-id", required=True)

    # finalize (M3)
    p_final = subparsers.add_parser("finalize", help="Finalize converged project")
    p_final.add_argument("--project-id", required=True)

    # status
    p_stat = subparsers.add_parser("status", help="Show project status")
    p_stat.add_argument("--project-id", required=True)

    args = parser.parse_args()

    commands = {
        "retrieve": cmd_retrieve,
        "validate": cmd_validate,
        "xray": cmd_xray,
        "cryoem": cmd_cryoem,
        "refine": cmd_refine,
        "process": cmd_process,
        "accept": cmd_accept,
        "converge": cmd_converge,
        "finalize": cmd_finalize,
        "status": cmd_status,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
