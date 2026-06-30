# Thermodynamic Impact Analysis: OPAM2 pKa to Metabolic Modeling

## Research Question

How do updated pKa predictions from OPAM2 (a graph-convolutional neural network fine-tuned on ModelSEED biochemistry) propagate through the thermodynamic pipeline — from pKa to deltaG via the Legendre transform in dGPredictor — and what is the downstream impact on metabolic model predictions (blocked reactions, reaction directionality, thermodynamic loops, and growth phenotype accuracy)?

## Status

In Progress

## Overview

The ModelSEED Database currently uses Marvin 23.4 (ChemAxon) for pKa values, which feed into the Legendre transform in dGPredictor to compute pH-corrected deltaG values for reactions. These deltaG values constrain reaction directionality and thermodynamic feasibility in genome-scale metabolic models.

This project replaces Marvin pKa values with OPAM2 predictions, recomputes deltaG for all ModelSEED reactions, and evaluates the downstream impact across multiple reference metabolic models spanning Gram-negative, Gram-positive, and Archaea.

## Pipeline

```
OPAM2 pKa predictions
    |
    v
ModelSEEDDatabase compound pKa/pkb columns
    |
    v
dGPredictor Legendre transform (pH correction)
    |
    v
ModelSEEDDatabase reaction deltag/deltagerr columns
    |
    v
ModelSEEDpy FullThermoPkg FBA constraints
    |
    v
Blocked reactions, directionality, loops, phenotype accuracy
```

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [Notebooks](notebooks/)

## Data Sources

- OPAM2: `freiburgermsu/OPAM2` (ModelSEED-finetuned weights)
- ModelSEEDDatabase: `freiburgermsu/ModelSEEDDatabase` (branch `clauded`)
- dGPredictor: `freiburgermsu/dGPredictor`
- ModelSEEDpy: `freiburgermsu/ModelSEEDpy`
- KBUtilLib: `/global_share/KBaseUtilities/KBUtilLib`

## Reproduction

### Prerequisites

- Python 3.10+
- PyTorch, torch-geometric, RDKit
- cobra, modelseedpy, cobrakbase
- KBUtilLib (shared filesystem at `/global_share/KBaseUtilities/KBUtilLib`)
- Access to KBase genomes for model building

### Steps

1. Clone required repos to `/tmp/`:
   ```bash
   gh repo clone freiburgermsu/OPAM2 /tmp/OPAM2
   gh repo clone freiburgermsu/ModelSEEDDatabase /tmp/ModelSEEDDatabase -- -b clauded
   gh repo clone freiburgermsu/dGPredictor /tmp/dGPredictor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run notebooks in order (01 through 08). Notebooks 01-04 handle data pipeline; 05-08 handle evaluation.

### Expected Runtime

- NB01-02 (pKa): ~40 min
- NB03-04 (deltaG): ~25 min
- NB05-08 (evaluation): ~3-5 hours depending on number of models

## Authors

- Andrew Freiburger
