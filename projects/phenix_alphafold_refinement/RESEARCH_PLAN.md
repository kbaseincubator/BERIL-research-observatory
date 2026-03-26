# Research Plan: AlphaFold-to-Refined Structure Pipeline

## Research Question

How effectively can an AI-driven pipeline use AlphaFold predictions as starting models for X-ray crystallographic refinement, and what quality improvements does experimental data provide over the prediction alone?

## Hypothesis

- **H0**: Refinement of an AlphaFold model against experimental data does not significantly improve validation metrics beyond the raw prediction.
- **H1**: A single automated refinement cycle against high-resolution X-ray data substantially improves Ramachandran statistics, rotamer quality, and R-factors relative to the AlphaFold prediction — demonstrating that AI-predicted models benefit from experimental refinement.

### Secondary Hypothesis

- **H2**: The `/phenix` agent skill can execute the complete AlphaFold-to-refined-structure pipeline (retrieval, processing, molecular replacement, refinement, validation) without manual intervention, producing results comparable to an experienced crystallographer's first refinement pass.

## Literature Context

AlphaFold2 has transformed structural biology by providing high-confidence predictions for most known protein sequences (Jumper et al., 2021, Nature 596:583-589). However, AlphaFold models differ from experimentally determined structures in important ways:

1. **No experimental density fitting** — AF models are predicted from sequence, not fitted to electron density maps. This means side-chain conformations may not match the actual crystal packing environment.
2. **B-factors are pLDDT scores** — not true atomic displacement parameters. They reflect prediction confidence, not crystallographic thermal motion.
3. **No solvent modeling** — AF models lack ordered water molecules that are integral to protein function and crystal contacts.
4. **Signal peptide artifacts** — AF models for secreted proteins include signal peptide residues that are cleaved in the mature protein used for crystallization.

Phenix provides `process_predicted_model` (Liebschner et al., 2019, Acta Cryst D75:861-877) to convert pLDDT to pseudo-B-factors and trim low-confidence regions, making AF models suitable as molecular replacement search models. Several studies have shown that AF models work well as MR search models even at moderate resolution (McCoy et al., 2022, J Appl Cryst 55:1256-1264).

## Approach

### Target Protein

**Hen egg-white lysozyme (HEWL)** — UniProt P00698

- 129 residues (mature protein), 14.3 kDa
- Canonical crystallography tutorial protein
- AlphaFold pLDDT: 93.88 (94.5% of residues "very high" confidence)
- Extensive PDB coverage — over 100 deposited structures

### Experimental Data

**PDB 1AKI** — Orthorhombic HEWL at 1.5 A resolution

- Space group: P 21 21 21
- Unit cell: 59.06 x 68.45 x 30.52 A
- 16,327 unique reflections
- Structure factors deposited (CIF -> MTZ conversion)

### Workflow

| Step | Tool | Input | Output |
|------|------|-------|--------|
| 1. Retrieve AF model | EBI API (curl) | UniProt P00698 | PDB + PAE JSON |
| 2. Validate raw AF model | phenix.molprobity | AF model PDB | MolProbity report |
| 3. Process AF model | phenix.process_predicted_model | AF model PDB | Trimmed model with pseudo-B-factors |
| 4. Fetch experimental data | RCSB + phenix.cif_as_mtz | PDB 1AKI | MTZ with R-free flags |
| 5. Molecular replacement | phenix.mrage (Phaser) | Processed model + MTZ | Placed model in crystal lattice |
| 6. Refinement | phenix.refine | Placed model + MTZ | Refined model + maps |
| 7. Validate refined model | phenix.molprobity | Refined model PDB | MolProbity report |
| 8. Compare metrics | Python/matplotlib | Both reports | Figures + tables |

### Analysis Plan

#### Notebook 1: Full Pipeline (`01_alphafold_to_refined_structure.ipynb`)
- **Goal**: Execute the complete pipeline in a single reproducible notebook
- **Expected output**: Refined PDB, validation reports, comparison figures

### Performance Considerations

- All steps run locally on Apple Silicon Mac (no SLURM needed for this protein size)
- Expected total runtime: ~3 minutes
- Most time spent in phenix.refine (5 macro-cycles, ~40 seconds)

## Expected Outcomes

- **If H1 supported**: Refinement against experimental data at 1.5 A should produce R-free < 0.25 and substantially improved Ramachandran/rotamer statistics, demonstrating the value of combining AI prediction with experimental data.
- **If H0 not rejected**: Would suggest AF models are already near-optimal for well-folded globular proteins — unlikely given the known differences in side-chain positioning and solvent modeling.
- **Potential confounders**: HEWL is an unusually well-behaved protein. Results may not generalize to larger, more flexible, or multi-domain proteins.

## Validation Strategy

Compare the following metrics between raw AF model and refined model:
1. R-work / R-free (experimental agreement)
2. MolProbity score
3. Ramachandran favored / outliers
4. Rotamer outliers
5. Clashscore
6. RMS(bonds) and RMS(angles)
7. Number of ordered waters placed

## Revision History

- **v1** (2026-03-26): Initial plan — chose HEWL/1AKI as demo system after evaluating E. coli thioredoxin (2TRX lacks deposited structure factors)

## Authors

- Paramvir Dehal (LBNL) — ORCID: 0000-0001-9267-5088
- Claude (Anthropic) — AI co-scientist
