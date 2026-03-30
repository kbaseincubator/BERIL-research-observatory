# Phenix Parameter Reference

Common parameter recipes for Phenix tools, formatted as `.eff` parameter file snippets.

## Parameter File Format

Phenix uses `.eff` (PHIL) parameter files. Create them as text files:

```
# my_refine.eff
refinement {
  crystal_symmetry {
    space_group = P 21 21 21
  }
  refine {
    strategy = individual_sites+individual_adp+tls
  }
  main {
    number_of_macro_cycles = 5
  }
}
```

Use with: `phenix.refine data.mtz model.pdb my_refine.eff`

## phenix.refine Parameters

### Refinement Strategies

| Strategy | What It Refines | When to Use |
|----------|----------------|-------------|
| `rigid_body` | Overall position/rotation of chains | First cycle, low-resolution, initial MR placement |
| `individual_sites` | XYZ coordinates per atom | Standard coordinate refinement |
| `individual_adp` | Isotropic B-factors per atom | Standard for < 3.0 A |
| `group_adp` | B-factors per residue/group | Low resolution (> 3.0 A) |
| `tls` | Translation-Libration-Screw groups | Captures domain motion (2.0-3.5 A) |
| `occupancies` | Atom occupancies | Alternate conformations, partial occupancy |

Combine with `+`: `strategy=individual_sites+individual_adp+tls`

### Common Recipes

#### First Refinement After MR

```
refinement.refine.strategy = rigid_body
refinement.main.number_of_macro_cycles = 3
```

#### Standard Mid-Resolution (2.0-3.0 A)

```
refinement.refine.strategy = individual_sites+individual_adp+tls
refinement.main.number_of_macro_cycles = 5
refinement.refine.adp.tls = auto
```

#### High Resolution (< 2.0 A)

```
refinement.refine.strategy = individual_sites+individual_adp
refinement.main.number_of_macro_cycles = 5
```

#### Low Resolution (> 3.5 A)

```
refinement.refine.strategy = individual_sites+group_adp
refinement.main.number_of_macro_cycles = 5
refinement.reference_model.enabled = True
refinement.reference_model.file = reference.pdb
```

#### Weight Optimization

```
refinement.target_weights.optimize_xyz_weight = True
refinement.target_weights.optimize_adp_weight = True
```

### NCS Restraints

```
refinement.ncs.type = torsion
refinement.ncs.find_automatically = True
```

### Simulated Annealing (for stuck refinements)

```
refinement.simulated_annealing.start_temperature = 5000
refinement.main.simulated_annealing = True
refinement.main.number_of_macro_cycles = 1
```

### Riding Hydrogens

```
refinement.pdb_interpretation.use_neutron_distances = False
refinement.hydrogens.refine = riding
```

## phenix.real_space_refine Parameters

### Standard Cryo-EM

```bash
phenix.real_space_refine \
  model.pdb map.mrc \
  resolution=3.0 \
  run=minimization_global+local_grid_search+morphing+simulated_annealing \
  macro_cycles=5
```

### With NCS Constraints

```bash
phenix.real_space_refine \
  model.pdb map.mrc \
  resolution=3.0 \
  run=minimization_global+local_grid_search \
  ncs_constraints=True \
  macro_cycles=5
```

### With Reference Model Restraints

```bash
phenix.real_space_refine \
  model.pdb map.mrc \
  resolution=3.0 \
  run=minimization_global+local_grid_search \
  reference_model.file=reference.pdb \
  macro_cycles=5
```

## Phaser Parameters

### Standard MR with AlphaFold

```bash
phenix.phaser \
  data.mtz \
  model=af_model.pdb \
  composition.chain=A \
  search.copies=1 \
  search.vrms=0.7
```

### Multi-Domain Search

```bash
phenix.phaser \
  data.mtz \
  model=domain1.pdb model=domain2.pdb \
  composition.chain=A \
  search.copies=1 search.copies=1 \
  search.vrms=0.7 search.vrms=0.7
```

### VRMS Guidelines

| Model Source | Recommended VRMS |
|-------------|-----------------|
| AlphaFold (pLDDT > 80, bacterial) | 0.7 |
| AlphaFold (pLDDT > 80, eukaryotic) | 1.0 |
| AlphaFold (pLDDT 60-80) | 1.0-1.5 |
| Homology model (> 40% identity) | 0.7-1.0 |
| Homology model (20-40% identity) | 1.0-1.5 |
| Distant homolog | 1.5-2.0 |

## phenix.process_predicted_model Parameters

```bash
phenix.process_predicted_model \
  model.pdb \
  pae_json_file=pae.json \
  b_factor_column_label=plddt \
  remove_low_confidence_residues=True \
  plddt_cutoff=70 \
  split_model_by_compact_regions=True \
  maximum_domains=5
```

## eLBOW (Ligand Restraints)

```bash
# Generate restraints from SMILES
phenix.elbow --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --output ligand

# Generate restraints from PDB/CIF
phenix.elbow ligand.pdb --output ligand

# With AM1 optimization
phenix.elbow --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --opt --output ligand
```
