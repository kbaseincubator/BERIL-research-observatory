# Structure Validation (MolProbity)

Run MolProbity validation on protein structures and parse results for decision-making.

## When to Use

- After any refinement cycle
- To assess AlphaFold prediction quality
- Before deposition
- When user asks `/phenix validate <model>`

## Workflow

### Step 1: Run Validation

```bash
# Full MolProbity validation
phenix.validation model.pdb data.mtz \
  output.prefix=validation \
  output.directory=./validation_output

# AlphaFold model (no experimental data)
phenix.validation model.pdb \
  output.prefix=validation \
  output.directory=./validation_output

# Cryo-EM model with map
phenix.validation model.pdb map.mrc \
  output.prefix=validation \
  output.directory=./validation_output
```

### Step 2: Parse Key Metrics

The validation output contains a summary log. Extract these metrics:

```bash
# Parse MolProbity summary from log
grep -A 20 "MolProbity statistics" validation_output/validation.log

# Key metrics to extract:
# - Ramachandran favored (%)
# - Ramachandran outliers (%)
# - Rotamer outliers (%)
# - C-beta deviations
# - Clashscore
# - MolProbity score
# - R-work / R-free (if experimental data provided)
```

### Alternative: phenix.molprobity for Standalone Validation

```bash
phenix.molprobity model.pdb \
  output_prefix=molprobity \
  output_dir=./molprobity_output
```

### Step 3: Identify Problem Residues

```bash
# Ramachandran outliers
phenix.ramalyze model.pdb

# Rotamer outliers
phenix.rotalyze model.pdb

# Clashscore details (per-atom clashes)
phenix.clashscore model.pdb

# C-beta deviations
phenix.cbetadev model.pdb
```

Parse each output to build a list of problem residues:

```python
# Example: parse ramalyze output
# Output format: chain:resseq:resname:phi:psi:classification
# Look for lines containing "OUTLIER"
```

### Step 4: Generate Validation Report

Compile results into a structured JSON report:

```json
{
  "model": "model.pdb",
  "data": "data.mtz",
  "timestamp": "2026-03-14T10:00:00Z",
  "summary": {
    "molprobity_score": 1.45,
    "ramachandran_favored": 97.2,
    "ramachandran_outliers": 0.3,
    "rotamer_outliers": 1.1,
    "clashscore": 4.2,
    "cbeta_deviations": 2,
    "r_work": 0.198,
    "r_free": 0.234
  },
  "outliers": {
    "ramachandran": [
      {"chain": "A", "residue": 45, "name": "LEU", "phi": -120.3, "psi": 60.1}
    ],
    "rotamer": [
      {"chain": "A", "residue": 78, "name": "ARG"}
    ],
    "clashes": [
      {"atom1": "A:45:LEU:CD1", "atom2": "A:48:VAL:CG2", "overlap": 0.8}
    ]
  }
}
```

### Step 5: Assess Quality

Use these thresholds (from SKILL.md):

| Metric | Good | Acceptable | Poor |
|--------|------|-----------|------|
| MolProbity score | < 1.5 | 1.5-2.5 | > 2.5 |
| Ramachandran favored | > 97% | 95-97% | < 95% |
| Ramachandran outliers | < 0.2% | 0.2-0.5% | > 0.5% |
| Clashscore | < 5 | 5-10 | > 10 |
| Rotamer outliers | < 1% | 1-3% | > 3% |
| R-free (X-ray) | < 0.25 | 0.25-0.30 | > 0.30 |
| R-gap | < 0.05 | 0.05-0.07 | > 0.07 |

### Resolution-Dependent Expectations

Validation metrics should be interpreted in context of resolution:

| Resolution (A) | Expected Rama fav | Expected Clash | Expected Rota out |
|----------------|-------------------|----------------|-------------------|
| < 1.5 | > 98% | < 3 | < 0.5% |
| 1.5-2.0 | > 97% | < 5 | < 1% |
| 2.0-3.0 | > 96% | < 8 | < 2% |
| 3.0-4.0 | > 94% | < 12 | < 4% |
| > 4.0 | > 90% | varies | varies |

## Output to User

Present validation results in a clear summary:

```
Validation Report for model.pdb
================================
MolProbity score:     1.45 (GOOD)
Ramachandran favored: 97.2% (GOOD)
Ramachandran outliers: 0.3% (ACCEPTABLE)
Rotamer outliers:     1.1% (ACCEPTABLE)
Clashscore:           4.2 (GOOD)
C-beta deviations:    2
R-work / R-free:      0.198 / 0.234 (GOOD, gap = 0.036)

Problem residues (3 total):
  - A:Leu45 — Ramachandran outlier (phi=-120.3, psi=60.1)
  - A:Arg78 — Rotamer outlier
  - A:Leu45-Val48 — Steric clash (0.8 A overlap)

Recommendation: Model quality is good. Minor issues at Leu45 region
may improve with 1 more refinement cycle or manual adjustment in Coot.
```

## After Validation

- If quality is **good**: proceed to next step (deposition or final model)
- If quality is **acceptable**: recommend 1 more refinement cycle, generate Coot script for outliers
- If quality is **poor**: analyze what went wrong, check refinement parameters, consult [troubleshooting.md](../references/troubleshooting.md)

When generating visualization scripts for problem residues, read [visualization.md](visualization.md).
