---
name: phenix
description: Structural biology workflow orchestrator using the Phenix suite. Use when the user wants to determine, refine, or validate protein structures — including AlphaFold structure retrieval, X-ray crystallography, cryo-EM, MolProbity validation, or visualization script generation.
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Agent
user-invocable: true
---

# Phenix — Structural Biology Agent

Orchestrate structural biology workflows: retrieve AlphaFold predictions, validate structures, solve X-ray and cryo-EM structures, manage refinement loops, and generate visualization scripts.

## Entry Points

| Command | What It Does |
|---------|-------------|
| `/phenix` | Start a new structural biology project (guided workflow) |
| `/phenix retrieve <accession>` | Retrieve AlphaFold structure(s) from EBI |
| `/phenix validate <model>` | Run MolProbity validation on a structure |
| `/phenix xray <data.mtz> <seq.fa>` | Start X-ray structure determination |
| `/phenix cryoem <map.mrc> <seq.fa>` | Start cryo-EM structure determination |
| `/phenix refine` | Run next refinement cycle (within active project) |
| `/phenix inspect` | Generate visualization scripts for current model |
| `/phenix status` | Show project status, current metrics, next recommended step |
| `/phenix history` | Show refinement convergence history |

Parse the user's command to determine which module to read.

## Module Routing

| User Intent | Module |
|-------------|--------|
| Retrieve AlphaFold structures | [retrieve.md](modules/retrieve.md) |
| Validate a structure (MolProbity) | [validation.md](modules/validation.md) |
| X-ray crystallography pipeline | [xray-pipeline.md](modules/xray-pipeline.md) |
| Cryo-EM pipeline | [cryoem-pipeline.md](modules/cryoem-pipeline.md) |
| Generate Coot/PyMOL/ChimeraX scripts | [visualization.md](modules/visualization.md) |
| Review cross-project patterns | [memory.md](modules/memory.md) |

**Read the appropriate module** before proceeding. Each module contains the full workflow, commands, and output parsing for that step.

## References

Read these as needed for parameter details and troubleshooting:

| Reference | When to Read |
|-----------|-------------|
| [phenix-parameters.md](references/phenix-parameters.md) | Setting up `.eff` parameter files for Phenix tools |
| [resolution-strategies.md](references/resolution-strategies.md) | Choosing refinement strategy based on resolution |
| [troubleshooting.md](references/troubleshooting.md) | When a Phenix tool fails or produces unexpected results |

## Preconditions

1. **Phenix installed** on NERSC — install with the helper at `data/structural_biology/scripts/`, file name `install_phenix.sh`, then:
   ```bash
   module load conda
   conda activate phenix
   phenix.version
   ```
2. **KBASE_AUTH_TOKEN** set in `.env` (for BERDL queries and MinIO storage)
3. **MinIO access** configured (for structure storage) — see `/berdl-minio` skill
4. **For SLURM jobs**: Access to Perlmutter compute nodes
5. **Python 3.9+**: Use `module load python` on NERSC (system Python is too old)

## Phenix Environment Setup

Before running any Phenix tool:

```bash
module load conda
conda activate phenix
phenix.version
```

## Pipeline Scripts

The pipeline orchestrator (`run_pipeline.py` under `data/structural_biology/scripts/`) handles
project creation, SLURM job submission, output parsing, and provenance logging:

```bash
module load python
PIPELINE_DIR=data/structural_biology/scripts
PIPELINE="$PIPELINE_DIR/run_pipeline.py"
python3 "$PIPELINE" retrieve --accession P0A6Y8
python3 "$PIPELINE" validate --model model.pdb
python3 "$PIPELINE" xray --data data.mtz --seq seq.fa --project-id struct_YYYYMMDD_name
python3 "$PIPELINE" refine --project-id struct_YYYYMMDD_name
python3 "$PIPELINE" process --project-id struct_YYYYMMDD_name --cycle 3
python3 "$PIPELINE" accept --project-id struct_YYYYMMDD_name --model rebuilt.pdb
python3 "$PIPELINE" converge --project-id struct_YYYYMMDD_name
python3 "$PIPELINE" finalize --project-id struct_YYYYMMDD_name
python3 "$PIPELINE" batch-validate --accessions P0A6Y8 Q9Y6K9 --output-dir results/
python3 "$PIPELINE" advise --resolution 2.5 --method xray
python3 "$PIPELINE" figures --project-id struct_YYYYMMDD_name
python3 "$PIPELINE" dashboard
python3 "$PIPELINE" status --project-id struct_YYYYMMDD_name
```

### Refinement Loop Workflow

1. Submit refinement: `run_pipeline.py refine --project-id ...`
2. After SLURM job finishes: `run_pipeline.py process --project-id ... --cycle N`
3. Process generates Coot/PyMOL/ChimeraX scripts and checks convergence
4. If not converged: user inspects model in Coot, rebuilds, saves
5. Accept rebuilt model: `run_pipeline.py accept --project-id ... --model rebuilt.pdb`
6. Repeat from step 1 until converged
7. Finalize: `run_pipeline.py finalize --project-id ...`

## Project State Management

Each structural biology project is tracked in a project directory on MinIO:

```
s3a://cdm-lake/tenant-general-warehouse/kescience/structural-biology/
├── alphafold-structures/{accession}/     # Retrieved AF structures
│   ├── model.pdb
│   ├── model.cif
│   └── pae.json
└── projects/{project_id}/               # Structure determination projects
    ├── input/                           # Experimental data
    ├── cycles/cycle_{NNN}/              # Refinement cycle outputs
    ├── scripts/                         # Visualization scripts
    ├── figures/                         # Generated figures
    └── final/                           # Final depositable model
```

### Project ID Convention

`struct_{YYYYMMDD}_{short_name}` — e.g., `struct_20260314_ecoli_dhfr`

### Tracking State

The agent tracks project state via:
1. **MinIO directory structure** — what files exist tells us what step we're at
2. **Delta Lake `refinement_cycles`** — queryable history of all refinement iterations
3. **Local project notes** — `project_notes.json` in the project directory

## Compute Strategy

| Step | Where | Runtime |
|------|-------|---------|
| AlphaFold retrieval | NERSC login node | Seconds (HTTP) |
| phenix.xtriage | NERSC interactive | Seconds |
| phenix.validate | NERSC interactive | Seconds-minutes |
| phenix.process_predicted_model | NERSC interactive | Seconds |
| phenix.refine | NERSC SLURM batch | Minutes-hours |
| phenix.real_space_refine | NERSC SLURM batch | Minutes-hours |
| Phaser | NERSC SLURM batch | Minutes-hours |
| AutoBuild | NERSC SLURM batch | Hours |
| PredictAndBuild | NERSC SLURM batch | Hours-days |
| map_to_model | NERSC SLURM batch | Hours |
| Figure generation (headless) | NERSC interactive | Seconds-minutes |

### SLURM Job Template

For compute-intensive Phenix steps:

```bash
#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=04:00:00
#SBATCH --job-name=phenix_{tool}_{project_id}
#SBATCH --output=phenix_%j.out
#SBATCH --error=phenix_%j.err

module load phenix

# Tool-specific command (filled in by agent)
{phenix_command}
```

## Delta Lake Tables

Results are stored in `kescience_structural_biology` — use `berdl_notebook_utils.get_table_schema(database="kescience_structural_biology", table=..., detailed=True, return_json=False)` for the live schema.

| Table | Purpose |
|-------|---------|
| `structure_projects` | One row per structure determination project |
| `refinement_cycles` | Full refinement history with metrics |
| `validation_reports` | Standalone validations (including AlphaFold-only) |
| `alphafold_structures` | Retrieved structure file metadata |

## Provenance

Every agent action is logged as a JSON record in the project's `provenance.jsonl` file:

```json
{
  "project_id": "struct_20260314_ecoli_dhfr",
  "action": "refinement",
  "tool": "phenix.refine",
  "tool_version": "1.21.2",
  "input_model": "s3://...cycles/cycle_003/model.pdb",
  "parameters": {"strategy": "individual_sites+individual_adp+tls"},
  "output_model": "s3://...cycles/cycle_004/model.pdb",
  "metrics": {"r_work": 0.198, "r_free": 0.234, "molprobity_score": 1.45},
  "decision_rationale": "Added TLS refinement because R-gap was >0.05",
  "timestamp": "2026-03-14T10:30:00Z"
}
```

## Instructions for Claude

1. **Parse the user's command** to determine the entry point (retrieve, validate, xray, cryoem, etc.)
2. **Read the appropriate module** for the target workflow
3. **Read [resolution-strategies.md](references/resolution-strategies.md)** before making any refinement parameter decisions
4. **Read [docs/structural_biology_memory.md](../../../docs/structural_biology_memory.md)** for cross-project lessons when starting refinement
5. **Check project state** — what step are we at? What has been tried?
6. **Run automated steps** and parse outputs carefully
7. **For human-in-the-loop steps**: generate visualization scripts, highlight problem regions, and wait for the user
8. **Log provenance** for every action taken
9. **Store results** — upload to MinIO, update Delta Lake tables
10. **Update memory** — if a new pattern or lesson is learned, update `docs/structural_biology_memory.md`

### Decision Thresholds

Use these defaults unless the user specifies otherwise:

| Metric | Good | Acceptable | Poor |
|--------|------|-----------|------|
| R-free (X-ray) | < 0.25 | 0.25-0.30 | > 0.30 |
| R-gap (R-free - R-work) | < 0.05 | 0.05-0.07 | > 0.07 |
| MolProbity score | < 1.5 | 1.5-2.5 | > 2.5 |
| Ramachandran favored | > 97% | 95-97% | < 95% |
| Ramachandran outliers | < 0.2% | 0.2-0.5% | > 0.5% |
| Clashscore | < 5 | 5-10 | > 10 |
| Rotamer outliers | < 1% | 1-3% | > 3% |

### Safety Rules

1. **Never delete experimental data** — only create new files
2. **Always keep the previous cycle's model** — refinement can make things worse
3. **Never skip validation** — always validate after refinement
4. **Confirm with user** before submitting SLURM jobs that will run > 1 hour
5. **Log every action** — provenance is non-negotiable

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to the active project's `projects/<id>/memories/pitfalls.md`.
