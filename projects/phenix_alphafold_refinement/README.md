# AlphaFold-to-Refined Structure: Agent-Driven Phenix Pipeline Demo

## Research Question

Can an AI agent autonomously take an AlphaFold-predicted structure from retrieval through molecular replacement and crystallographic refinement, producing a publication-quality model validated against experimental X-ray data?

## Status

Complete — full pipeline executed, model refined to R-free = 0.244.

## Overview

This project demonstrates the `/phenix` structural biology skill by running the complete AlphaFold-to-refined-structure pipeline on **hen egg-white lysozyme (HEWL)**, the canonical crystallography benchmark protein. Starting from a UniProt accession (P00698), the agent retrieves the AlphaFold prediction, validates it, places it into the crystal lattice via molecular replacement, and refines it against 1.5 A experimental X-ray data (PDB 1AKI).

The pipeline runs entirely locally on a Mac (Apple Silicon) using Phenix 2.0-5936 — no HPC cluster or SLURM required for this scale of problem.

### Key Findings

- AlphaFold model (pLDDT 93.88) placed successfully via Phaser MR with TFZ = 25.1
- Single round of refinement reduced R-free from 0.379 to **0.244**
- Ramachandran favored improved from 91.0% to **98.5%** after fitting to experimental density
- 67 ordered water molecules placed automatically
- Total wall-clock time: ~2 minutes (retrieval through refinement)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, Phenix workflow
- [Report](REPORT.md) — findings, interpretation, metrics comparison
- [Analysis Notebook](notebooks/01_alphafold_to_refined_structure.ipynb) — full reproducible pipeline

## Data Sources

| Source | What | Resolution |
|--------|------|-----------|
| AlphaFold DB (EBI) | Predicted structure for P00698, v6 | n/a (pLDDT 93.88) |
| PDB 1AKI | Experimental X-ray structure + structure factors | 1.50 A |

## Project Structure

```
phenix_alphafold_refinement/
├── README.md                  — This file
├── RESEARCH_PLAN.md           — Hypothesis, approach, workflow
├── REPORT.md                  — Findings and interpretation
├── notebooks/
│   └── 01_alphafold_to_refined_structure.ipynb  — Full pipeline notebook
├── data/
│   ├── AF-P00698-F1-model_v6.pdb               — AlphaFold prediction (raw)
│   ├── AF_lysozyme_processed.pdb                — After process_predicted_model
│   ├── mrage_P212121_1.1.pdb                    — After molecular replacement
│   ├── refine_001.pdb                           — Refined model (cycle 1)
│   ├── 1AKI_rfree.mtz                           — Experimental data with R-free flags
│   └── refine_001.log                           — Refinement log
├── figures/
│   ├── validation_comparison.png                — Before/after validation metrics
│   └── rfactor_convergence.png                  — R-factor improvement per macro-cycle
└── requirements.txt
```

## Reproduction

### Prerequisites

- **Phenix 2.0** — Install from [phenix-online.org](https://phenix-online.org/download) (free for academics)
- **Python 3.9+** with `matplotlib`, `numpy`, `jupyter`
- Internet access for AlphaFold/PDB downloads

### Steps

```bash
# 1. Activate Phenix
source ~/phenix-2.0-5936/phenix_env.sh

# 2. Install notebook dependencies
pip install matplotlib numpy jupyter

# 3. Run the notebook (all steps are self-contained)
cd projects/phenix_alphafold_refinement
jupyter nbconvert --to notebook --execute --inplace notebooks/01_alphafold_to_refined_structure.ipynb

# Expected runtime: ~3 minutes on Apple Silicon Mac
```

### Limitations

- Refinement was limited to 1 cycle (5 macro-cycles) — additional rounds with manual Coot rebuilding would further improve the model
- No TLS refinement was applied (would help with anisotropic displacement)
- The 16 N-terminal residues (signal peptide) were trimmed by `process_predicted_model` — the deposited 1AKI model includes mature protein residues 1-129

## Authors

- Paramvir Dehal (LBNL) — ORCID: [0000-0001-9267-5088](https://orcid.org/0000-0001-9267-5088)
- Claude (Anthropic) — AI co-scientist
