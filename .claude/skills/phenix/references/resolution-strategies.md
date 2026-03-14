# Resolution-Dependent Refinement Strategies

Choose refinement parameters based on data resolution and method.

## X-ray Crystallography

### Ultra-High Resolution (< 1.5 A)

- **Strategy**: `individual_sites + individual_adp` (anisotropic if data supports it)
- **ADPs**: Anisotropic for well-ordered regions, isotropic for flexible regions
- **Hydrogens**: Riding hydrogens visible in difference map
- **Weight**: Optimize with `optimize_xyz_weight=True`
- **Expected R-free**: < 0.18
- **Notes**: Individual atom positions very well defined; can model alternate conformations

### High Resolution (1.5-2.0 A)

- **Strategy**: `individual_sites + individual_adp`
- **ADPs**: Isotropic B-factors (anisotropic only if data/parameter ratio > 3)
- **Hydrogens**: Riding
- **Weight**: Default or optimize
- **Expected R-free**: 0.18-0.23
- **Notes**: Good density for side chains; most rotamers clear

### Mid Resolution (2.0-3.0 A)

- **Strategy**: `individual_sites + individual_adp + tls`
- **ADPs**: Isotropic with TLS groups (1 group per chain or domain)
- **TLS groups**: Auto-detect or 1 per chain
- **Weight**: Optimize recommended
- **Expected R-free**: 0.22-0.28
- **Notes**: TLS captures domain motion that individual B-factors miss at this resolution

### Low Resolution (3.0-4.0 A)

- **Strategy**: `individual_sites + group_adp` (or `group_sites + group_adp`)
- **ADPs**: Group B-factors (per residue)
- **Reference model**: Use AlphaFold or homolog as restraint
- **NCS**: Apply NCS restraints if multiple copies
- **Jelly-body**: Consider `refinement.pdb_interpretation.c_beta_restraints=True`
- **Expected R-free**: 0.28-0.35
- **Notes**: Individual atom refinement adds too many parameters; use restraints liberally

### Very Low Resolution (> 4.0 A)

- **Strategy**: `rigid_body` then `group_sites + group_adp`
- **ADPs**: Group B-factors
- **NCS**: Strong NCS constraints (not just restraints)
- **Reference model**: Essential — use AlphaFold prediction
- **Expected R-free**: 0.30-0.40
- **Notes**: Effectively fitting rigid bodies into density; model geometry entirely from restraints

## Cryo-EM

### High Resolution Cryo-EM (< 2.5 A)

- **Tool**: `phenix.real_space_refine`
- **Strategy**: `minimization_global + local_grid_search + adp`
- **Macro cycles**: 5
- **Notes**: Treat similarly to high-resolution X-ray; individual coordinates reliable

### Mid Resolution Cryo-EM (2.5-3.5 A)

- **Tool**: `phenix.real_space_refine`
- **Strategy**: `minimization_global + local_grid_search + morphing`
- **Macro cycles**: 5
- **Notes**: Morphing helps fit domains; backbone reliable, some side chains ambiguous

### Low Resolution Cryo-EM (3.5-5.0 A)

- **Tool**: `phenix.real_space_refine`
- **Strategy**: `minimization_global + morphing + simulated_annealing`
- **NCS**: Apply constraints if symmetric complex
- **Reference model**: AlphaFold prediction as reference
- **Macro cycles**: 3-5
- **Notes**: Secondary structure elements visible; side chains from model restraints only

### Very Low Resolution Cryo-EM (> 5.0 A)

- **Tool**: `phenix.real_space_refine`
- **Strategy**: `rigid_body` (individual domains)
- **Notes**: Only domain placement is meaningful; do not refine individual coordinates

## Refinement Progression

Typical refinement follows a staged approach:

```
Cycle 1:  rigid_body                    (place model roughly)
Cycle 2:  individual_sites             (adjust coordinates)
Cycle 3:  individual_sites + adp       (add B-factors)
Cycle 4:  individual_sites + adp + tls (add domain motion)
Cycle 5+: same as 4, manual rebuilding between cycles
```

Skip early stages if the starting model is already well-placed (e.g., after AutoBuild).

## When to Change Strategy

| Symptom | Current Strategy | Try Instead |
|---------|-----------------|-------------|
| R-gap > 0.07 | individual_adp | Add TLS, reduce macro_cycles |
| R-free stuck | xyz + adp | Add simulated_annealing (1 cycle) |
| R-free increasing | any | Revert to previous model, check data |
| Many Rama outliers | xyz | Check manual rebuilding, morphing |
| High clashscore | any | Weight optimization, reduce xyz weight |
| Density shows disorder | individual | Model alternate conformations or truncate |

## Data/Parameter Ratio

Rule of thumb: observations (reflections) / parameters should be > 1.5 for stable refinement.

| Resolution | Typical params per atom | Isotropic OK? | Anisotropic OK? |
|-----------|------------------------|---------------|-----------------|
| < 1.0 A | 9 (aniso) | Yes | Yes |
| 1.0-1.5 A | 4-9 | Yes | Maybe (check ratio) |
| 1.5-3.0 A | 4 (iso) | Yes | No |
| > 3.0 A | 1-2 (group) | Group only | No |
