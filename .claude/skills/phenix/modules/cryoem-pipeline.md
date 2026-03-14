# Cryo-EM Pipeline

Structure determination from cryo-EM density maps using Phenix tools and AlphaFold predictions.

## Pipeline Overview

```
phenix.mtriage → process_predicted_model → dock_predicted_model → REFINEMENT LOOP
                                                                   │
                                              phenix.real_space_refine → Coot → validate → iterate
```

Alternative (no AlphaFold model):
```
phenix.mtriage → phenix.map_to_model → REFINEMENT LOOP
```

AI-assisted (PredictAndBuild):
```
phenix.mtriage → PredictAndBuild → REFINEMENT LOOP
```

## Step 1: Map Quality Assessment (phenix.mtriage)

**Where**: NERSC interactive (minutes)

```bash
phenix.mtriage map.mrc \
  resolution=3.0 \
  log=mtriage.log
```

With a model (for map-model metrics):
```bash
phenix.mtriage map.mrc \
  model=model.pdb \
  resolution=3.0
```

### Key Metrics from mtriage

| Metric | What It Means | Good Values |
|--------|--------------|-------------|
| Resolution (d99) | Resolution from map alone | Should match reported resolution |
| Resolution (FSC=0.5) | Resolution at which map self-consistency drops | Primary resolution metric |
| Map-model CC | Correlation between map and model | > 0.6 |
| Map sharpening B | Applied B-factor for sharpening | Negative = sharpened (typical) |

## Step 2: Process AlphaFold Model

**Where**: NERSC interactive (seconds)

If an AlphaFold model is available, process it for use with cryo-EM:

```bash
# Trim low-confidence regions, split into rigid domains
phenix.process_predicted_model \
  model.pdb \
  pae_json_file=pae.json \
  b_factor_column_label=plddt \
  remove_low_confidence_residues=True \
  plddt_cutoff=70 \
  split_model_by_compact_regions=True
```

This produces:
- Trimmed model (low-pLDDT regions removed)
- Domain-split models (if PAE indicates multiple domains)

### pLDDT Cutoff Guidance

| Map Resolution | Recommended pLDDT Cutoff | Rationale |
|---------------|-------------------------|-----------|
| < 3.0 A | 70 | Higher confidence needed for detailed fitting |
| 3.0-4.0 A | 60 | Medium confidence regions may still be useful |
| > 4.0 A | 50 | Even low-confidence backbone can guide fitting |

## Step 3: Dock Model into Map

**Where**: NERSC interactive (minutes)

```bash
# Dock processed domains into the cryo-EM map
phenix.dock_predicted_model \
  map.mrc \
  model=processed_model.pdb \
  resolution=3.0 \
  nproc=8
```

For multi-domain proteins (split by process_predicted_model):
```bash
# Dock each domain separately
for domain in domain_*.pdb; do
  phenix.dock_predicted_model \
    map.mrc \
    model=$domain \
    resolution=3.0
done
```

### Assess Docking Quality

- Check map-model correlation (should be > 0.5 for a successful dock)
- Visual inspection may be needed — generate ChimeraX script (see [visualization.md](visualization.md))

## Step 3 (Alternative): Build Model from Scratch

**Where**: NERSC SLURM batch (hours)

When no AlphaFold model is available:

```bash
phenix.map_to_model \
  map.mrc \
  resolution=3.0 \
  seq_file=sequence.fasta \
  nproc=32
```

### SLURM Script

```bash
#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=24:00:00
#SBATCH --job-name=map_to_model_{project_id}

module load phenix

phenix.map_to_model \
  map.mrc \
  resolution=3.0 \
  seq_file=sequence.fasta \
  nproc=32 \
  output_dir=map_to_model_output
```

## Step 3 (AI-assisted): PredictAndBuild

**Where**: NERSC SLURM batch (hours-days)

PredictAndBuild uses AlphaFold predictions iteratively refined against experimental data:

```bash
phenix.predict_and_build \
  map.mrc \
  seq_file=sequence.fasta \
  resolution=3.0 \
  model=alphafold_model.pdb \
  nproc=32
```

If no pre-downloaded AF model, PredictAndBuild can call the Phenix AlphaFold server — but we can supply pre-downloaded models from BERDL to avoid external dependency.

## Step 4: Real-Space Refinement Loop

### 4a. Run phenix.real_space_refine

**Where**: NERSC SLURM batch (minutes-hours)

```bash
phenix.real_space_refine \
  model.pdb \
  map.mrc \
  resolution=3.0 \
  run=minimization_global+local_grid_search+morphing+simulated_annealing \
  macro_cycles=5 \
  output.prefix=rsr_cycle_{N}
```

### Resolution-Dependent Strategy

| Resolution | Strategy |
|-----------|----------|
| < 3.0 A | `minimization_global+local_grid_search+adp` |
| 3.0-4.0 A | `minimization_global+local_grid_search+morphing` |
| > 4.0 A | `minimization_global+morphing+simulated_annealing` (+ NCS/reference restraints) |

### 4b. Validate

Read [validation.md](validation.md) — run validation, parse metrics.

For cryo-EM, also check map-model correlation:
```bash
phenix.mtriage map.mrc model=rsr_cycle_{N}_model.pdb resolution=3.0
```

### 4c. Human Inspection

Same as X-ray — generate Coot/ChimeraX scripts for outliers, present to user, accept rebuilt model.

For cryo-EM, ChimeraX is often preferred over Coot for map visualization:
```
open map.mrc
open model.pdb
volume #1 step 1 level 0.02
```

### 4d. Convergence

Check convergence via:
- Map-model CC improvement < 0.005 for 2 cycles → converged
- MolProbity score plateaued → converged
- Ramachandran/rotamer outliers stable → converged

## Multi-Chain / Symmetric Complexes

For complexes with multiple chains or symmetry:

```bash
# Apply NCS restraints during refinement
phenix.real_space_refine \
  model.pdb \
  map.mrc \
  resolution=3.0 \
  ncs_constraints=True \
  macro_cycles=5
```

## Key Differences from X-ray

| Aspect | X-ray | Cryo-EM |
|--------|-------|---------|
| Refinement tool | `phenix.refine` | `phenix.real_space_refine` |
| Data format | MTZ (reflections) | MRC (density map) |
| Quality metric | R-free | Map-model CC |
| Resolution metric | d_min from data | FSC from reconstruction |
| B-factors | Refined against data | Often set to fixed value |
| Validation | Standard MolProbity | MolProbity + map correlation |

## Provenance

Log each step with tool, parameters, input/output paths, and metrics. See SKILL.md provenance section.
