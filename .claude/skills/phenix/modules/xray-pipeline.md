# X-ray Crystallography Pipeline

Full X-ray structure determination workflow: data assessment, phasing, model building, refinement, and validation.

## Pipeline Overview

```
phenix.xtriage → Phaser MR (with AF model) → AutoBuild → REFINEMENT LOOP → Deposition
                                                          │
                                        phenix.refine → Coot/ChimeraX → phenix.validate → iterate
```

## Step 1: Data Quality Assessment (phenix.xtriage)

**Where**: NERSC interactive (seconds)

```bash
phenix.xtriage data.mtz \
  log=xtriage.log
```

### Parse xtriage Output

Key metrics to extract from `xtriage.log`:

| Metric | What to Check | Action |
|--------|--------------|--------|
| Resolution | High-resolution limit | Report to user; use for refinement strategy |
| Twinning | L-test, H-test | If twinned, flag — refinement needs `twin_law` |
| Ice rings | Systematic absences at ~3.9, 3.7, 3.4 A | Flag if present — may need resolution cutoff |
| Anisotropy | Directional resolution differences | If severe, consider anisotropy correction |
| Space group | Confirmed or ambiguous | If ambiguous, try alternatives in Phaser |
| Completeness | % of reflections observed | Flag if < 90% |
| I/sigma | Signal-to-noise in resolution shells | Determines effective resolution cutoff |

```bash
# Quick resolution check
grep "High resolution" xtriage.log
grep "twin" xtriage.log
grep "ice" xtriage.log
```

**Decision point**: If data quality is poor, inform the user before proceeding. Do NOT continue with unusable data.

## Step 2: Molecular Replacement with AlphaFold (Phaser)

**Where**: NERSC SLURM batch (minutes-hours)

### Retrieve AlphaFold Model

Read [retrieve.md](retrieve.md) to fetch the AlphaFold prediction for the target protein.

### Process AF Model for MR

```bash
# Trim low-confidence regions and split domains
phenix.process_predicted_model \
  model.pdb \
  pae_json_file=pae.json \
  b_factor_column_label=plddt \
  remove_low_confidence_residues=True \
  plddt_cutoff=70
```

### Run Phaser

```bash
phenix.phaser \
  data.mtz \
  model=processed_model.pdb \
  composition.chain=A \
  search.copies=1 \
  search.vrms=0.7
```

**VRMS parameter**: For bacterial proteins with good AF predictions, `vrms=0.7` usually works. For eukaryotic or low-confidence models, try `vrms=1.0`. See [resolution-strategies.md](../references/resolution-strategies.md).

### Assess MR Success

| Metric | Success | Marginal | Failure |
|--------|---------|----------|---------|
| LLG (log-likelihood gain) | > 100 | 50-100 | < 50 |
| TFZ (translation function Z-score) | > 8 | 5-8 | < 5 |

If MR fails with one domain, try:
1. Split into multiple domains (using PAE matrix)
2. Use individual domains as separate search models
3. Try with `vrms=1.0` or `vrms=1.5`
4. Consider experimental phasing (AutoSol) instead

## Step 3: Initial Model Building (AutoBuild)

**Where**: NERSC SLURM batch (hours)

```bash
phenix.autobuild \
  data.mtz \
  model=phaser_solution.pdb \
  seq_file=sequence.fasta \
  nproc=32
```

### SLURM Script for AutoBuild

```bash
#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=08:00:00
#SBATCH --job-name=autobuild_{project_id}

module load phenix

phenix.autobuild \
  data.mtz \
  model=phaser_solution.pdb \
  seq_file=sequence.fasta \
  nproc=32 \
  output_dir=autobuild_output
```

### Assess AutoBuild Output

- Check R-work/R-free from `autobuild_output/overall_best.log`
- Count built residues vs expected (from sequence)
- Flag gaps in model (unbuilt regions)

## Step 4: Refinement Loop

This is iterative and human-in-the-loop. Each cycle:

### 4a. Run phenix.refine

**Where**: NERSC SLURM batch (minutes-hours)

```bash
phenix.refine \
  data.mtz \
  model.pdb \
  strategy={refinement_strategy} \
  main.number_of_macro_cycles=5 \
  output.prefix=refine_cycle_{N} \
  output.serial=1 \
  nproc=8
```

Choose `strategy` based on resolution — read [resolution-strategies.md](../references/resolution-strategies.md):

| Resolution | Strategy |
|-----------|----------|
| First cycle (any) | `rigid_body` |
| < 2.0 A | `individual_sites+individual_adp` |
| 2.0-3.0 A | `individual_sites+individual_adp+tls` |
| 3.0-4.0 A | `group_sites+group_adp` |
| > 4.0 A | `rigid_body` with NCS restraints |

### 4b. Run Validation

Read [validation.md](validation.md) — run `phenix.validate` and parse results.

### 4c. Prepare for Human Inspection

If validation shows issues:

1. Generate Coot navigation script — read [visualization.md](visualization.md)
2. Generate ChimeraX session — read [visualization.md](visualization.md)
3. Present results to user with clear instructions

```
Refinement cycle {N} complete:
  R-work: {r_work:.3f}  R-free: {r_free:.3f}  (gap: {gap:.3f})
  MolProbity: {score:.2f}  Rama fav: {rama_fav:.1f}%  Clash: {clash:.1f}

  {n_outliers} problem residues identified.

  To inspect in Coot:
    coot --script scripts/coot_cycle_{N}_outliers.py

  Please review and save the rebuilt model, then tell me the path.
```

### 4d. Accept Rebuilt Model

When user provides their rebuilt model:

1. Upload to MinIO as `cycles/cycle_{N+1}/model.pdb`
2. Log what the user changed (ask for notes)
3. Run next refinement cycle

### 4e. Convergence Check

After each cycle, check if refinement has converged:

- R-free improvement < 0.001 for 2 consecutive cycles → converged
- R-gap increasing → possible overfitting, stop or change strategy
- MolProbity score plateaued → converged

## Step 5: Final Model

When refinement converges and validation is acceptable:

1. Save final model to `projects/{project_id}/final/model_final.pdb`
2. Generate final validation report
3. Generate publication figures (read [visualization.md](visualization.md))
4. Update Delta Lake tables

## Alternative: Experimental Phasing (when MR fails)

If molecular replacement fails (no suitable search model or LLG too low):

```bash
# SAD/MAD phasing
phenix.autosol \
  data.mtz \
  seq_file=sequence.fasta \
  atom_type=Se \
  sites.n_sites=4 \
  nproc=32
```

This runs HySS (heavy atom search) → Phaser (phasing) → RESOLVE (density modification) → AutoBuild. Typically takes hours. Use SLURM batch.

## Provenance Per Step

Log each step with:
- Tool name and version
- Input files (MinIO paths)
- Parameters used
- Output files (MinIO paths)
- Key metrics
- Decision rationale (why this strategy was chosen)
