# Phenix Troubleshooting

Common issues and solutions when running Phenix tools.

## Installation / Environment

| Problem | Cause | Solution |
|---------|-------|----------|
| `phenix.version: command not found` | Phenix not in PATH | `module load phenix` or `source $PHENIX_ROOT/phenix_env.sh` |
| `ImportError: libfftw3f.so` | Missing shared library | Ensure Phenix env is sourced; check `$PHENIX/lib` |
| `License error` | License expired or missing | Re-register at phenix-online.org; `phenix.show_license` |
| Python version conflict | System Python conflicts with Phenix Python | Always use Phenix's bundled Python; don't mix envs |
| `CCTBX error` | Corrupted installation | Reinstall Phenix or run `phenix.rebuild_sources` |

## phenix.refine

| Problem | Cause | Solution |
|---------|-------|----------|
| R-free much higher than R-work (gap > 0.07) | Overfitting | Reduce number of parameters: use group ADPs, add TLS, optimize weights |
| R-free increasing each cycle | Refinement diverging | Revert to previous model; check data quality with xtriage; lower weight |
| R-free stuck (no improvement) | Wrong strategy or model errors | Try simulated annealing; check for wrong space group; rebuild manually |
| `No reflections found` | MTZ file issues | Check `phenix.mtz.dump data.mtz`; verify column labels |
| `Space group mismatch` | Model and data in different space groups | `phenix.pdbtools model.pdb --space-group="P 21 21 21"` |
| Very high clashscore after refinement | XYZ weight too low | `optimize_xyz_weight=True`; or manually increase geometry weight |
| `Geometry restraints error` | Unknown residue/ligand | Generate restraints with eLBOW; provide ligand CIF file |
| Memory error on large structure | Too many atoms for available RAM | Use SLURM with more memory; reduce `nproc` |

## Phaser (Molecular Replacement)

| Problem | Cause | Solution |
|---------|-------|----------|
| LLG < 50, TFZ < 5 | Poor search model | Trim low-confidence regions; try different VRMS; split domains |
| Multiple solutions with similar LLG | Ambiguous placement | Check each solution in Coot; validate with refine |
| `No solution found` | Model too different from target | Try experimental phasing (AutoSol); use ensemble of models |
| Wrong number of copies | Incorrect ASU contents | Recalculate Matthews coefficient; try different copy numbers |
| Phaser crashes | Insufficient memory | Reduce resolution range; split search into stages |
| Solution in wrong space group | Ambiguous space group | Try alternative space groups from xtriage |

## phenix.real_space_refine (Cryo-EM)

| Problem | Cause | Solution |
|---------|-------|----------|
| Model moves out of density | Map origin issue | Check `phenix.map_box` to center map; verify map format |
| Poor map-model CC | Wrong resolution | Verify resolution with mtriage; try different contour levels |
| Refinement very slow | Map too large | Box the map around the model; reduce step size |
| NCS violations | NCS constraints too tight | Switch from constraints to restraints; check chain alignment |
| Model distorted after refinement | Weight issues | Reduce macro_cycles; add reference model restraints |

## phenix.xtriage

| Problem | Cause | Solution |
|---------|-------|----------|
| Twin detected | Crystal is twinned | Add `twin_law` to refinement; may need to detwin first |
| Ice rings detected | Ice contamination in data | Apply resolution cutoff before/after ice ring positions |
| Anisotropy detected | Anisotropic diffraction | Apply anisotropy correction; report in deposition |
| Pseudotranslation | Non-crystallographic translation | Note in refinement; may affect MR |

## phenix.process_predicted_model

| Problem | Cause | Solution |
|---------|-------|----------|
| No domains found | PAE suggests single domain | Use without splitting; lower pLDDT cutoff |
| Too many domains | Aggressive splitting | Increase `maximum_domains`; use higher confidence cutoff |
| All residues removed | pLDDT cutoff too high | Lower `plddt_cutoff` (try 50 instead of 70) |
| PAE file format error | Wrong PAE JSON format | Check if it's AlphaFold v2/v4 format; ensure `.json` extension |

## AutoBuild

| Problem | Cause | Solution |
|---------|-------|----------|
| Low completeness (< 80% built) | Poor phases or low resolution | More refinement of MR solution first; try different starting model |
| Very slow (> 12 hours) | Large unit cell or high resolution | Reduce `nproc`; split into smaller domains |
| `Map correlation too low` | Bad phases | Recheck MR solution; try experimental phasing |

## Data Format Issues

| Problem | Solution |
|---------|----------|
| Can't read MTZ file | `phenix.mtz.dump file.mtz` to inspect; check if it's actually CIF |
| Can't read MRC map | `phenix.map_box map.mrc` to re-box; check header with EMAN2 |
| PDB vs mmCIF confusion | Phenix reads both; use `phenix.pdb_as_cif` or `phenix.cif_as_pdb` to convert |
| Column label mismatch | `phenix.mtz.dump` to see labels; specify with `label="F(+),SIGF(+)"` |

## SLURM Job Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Job killed (OOM) | Insufficient memory | Increase `--mem` or `--mem-per-cpu`; reduce `nproc` |
| Job timeout | Underestimated runtime | Increase `--time`; check if refinement is converging |
| `module load phenix` fails | Module not installed on compute nodes | Source env directly: `source /path/to/phenix_env.sh` |
| Phenix can't find data files | Path not accessible from compute node | Use absolute paths; ensure $SCRATCH is mounted |

## General Debugging

```bash
# Check Phenix version and installation
phenix.version

# Inspect MTZ file
phenix.mtz.dump data.mtz

# Inspect PDB file
phenix.pdbtools model.pdb --show-summary

# Check space group compatibility
phenix.explore_metric_symmetry data.mtz

# Quick validation
phenix.molprobity model.pdb
```
